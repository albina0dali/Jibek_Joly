import time
from collections import defaultdict
from .models import Visit
from .conflicts import detect_conflicts


def resource_key(v, blocks):
    return (v.resource, v.direction if v.resource in blocks and blocks[v.resource].track_type == 'double' else 0)


def duration(v, incidents, blocks):
    value = v.end - v.start
    for incident in incidents:
        if incident['status'] == 'active' and incident['type'] == 'speed_restriction' and v.resource == incident['location_id'] and v.end > incident['start_time'] and v.start < incident['end_time']:
            value = max(value, int(blocks[v.resource].distance_km / 40 * 3600))
    return value


def closure_windows(incidents):
    return [(i['location_id'], i['start_time'], i['end_time']) for i in incidents if i['status'] == 'active' and i['type'] in ('block_closure', 'signal_failure')]


def release_delay(train_id, incidents):
    return sum(i['delay_seconds'] for i in incidents if i['status'] == 'active' and i['location_id'] == train_id)


def heuristic(schedule, trains, blocks, stations, incidents, now, settings, strategy):
    reservations = defaultdict(list)
    output = []
    routes = defaultdict(list)
    for v in schedule:
        routes[v.train_id].append(v)
        if v.start <= now:
            output.append(v.model_copy())
            reservations[resource_key(v, blocks)].append((v.start, v.end + (settings.minimum_headway if v.kind == 'block' else 0), v.lane))
    if strategy == 'passenger':
        order = sorted(trains.values(), key=lambda t: (-t.priority, t.scheduled_departure, t.id))
    elif strategy == 'network':
        order = sorted(trains.values(), key=lambda t: (max(now, next((v.start for v in routes[t.id] if v.start > now), 10**9)), t.id))
    else:
        order = sorted(trains.values(), key=lambda t: (release_delay(t.id, incidents) > 0, t.scheduled_departure, t.id))
    windows = closure_windows(incidents)
    for train in order:
        previous = max([now] + [v.end for v in routes[train.id] if v.start <= now]) + release_delay(train.id, incidents)
        for v in routes[train.id]:
            if v.start <= now:
                continue
            length = duration(v, incidents, blocks)
            earliest = max(v.start, previous)
            key = resource_key(v, blocks)
            capacity = stations[v.resource].platform_count if v.kind == 'station' else 1
            padding = settings.minimum_headway if v.kind == 'block' else 0
            candidates = []
            for lane in range(capacity):
                start = earliest
                while True:
                    overlaps = [(a, b) for a, b, l in reservations[key] if l == lane and start < b and start + length + padding > a]
                    overlaps += [(a, b) for r, a, b in windows if r == v.resource and start < b and start + length > a]
                    if not overlaps:
                        break
                    start = max(b for _, b in overlaps)
                candidates.append((start, lane))
            start, lane = min(candidates)
            new = v.model_copy(update={'start': start, 'end': start + length, 'lane': lane})
            output.append(new)
            reservations[key].append((start, new.end + padding, lane))
            previous = new.end
    return sorted(output, key=lambda v: (v.train_id, v.start))


def cp_schedule(schedule, trains, blocks, stations, incidents, now, settings, strategy):
    from ortools.sat.python import cp_model
    model = cp_model.CpModel()
    resources = defaultdict(list)
    routes = defaultdict(list)
    variables = {}
    warm_start = heuristic(schedule, trains, blocks, stations, incidents, now, settings, strategy)
    hint = {(v.train_id, v.resource, v.kind): v for v in warm_start}
    horizon = max(v.end for v in warm_start) + 3600
    terms = []
    for index, v in enumerate(schedule):
        fixed = v.start <= now
        length = v.end - v.start if fixed else duration(v, incidents, blocks)
        start = model.new_int_var(v.start if fixed else max(now, v.start), v.start if fixed else horizon, f's{index}')
        end = model.new_int_var(0, horizon + 3600, f'e{index}')
        model.add(end == start + length)
        padding = settings.minimum_headway if v.kind == 'block' else 0
        interval = model.new_interval_var(start, length + padding, end + padding, f'i{index}')
        resources[resource_key(v, blocks)].append(interval)
        variables[index] = (start, end)
        suggested = hint[(v.train_id, v.resource, v.kind)]
        model.add_hint(start, suggested.start)
        model.add_hint(end, suggested.end)
        routes[v.train_id].append(index)
    for resource, intervals in resources.items():
        if resource[0] in stations:
            model.add_cumulative(intervals, [1] * len(intervals), stations[resource[0]].platform_count)
        else:
            model.add_no_overlap(intervals)
    for r, a, b in closure_windows(incidents):
        for key in list(resources):
            if key[0] == r:
                interval = model.new_interval_var(a, b - a, b, f'closure{r}{a}{key[1]}')
                model.add_no_overlap(resources[key] + [interval])
    for train_id, indices in routes.items():
        previous = None
        future = [i for i in indices if schedule[i].start > now]
        for index in indices:
            start, end = variables[index]
            if previous is not None:
                model.add(start >= variables[previous][1])
            if future and index == future[0]:
                bound = max(now, schedule[previous].end if previous is not None else now) + release_delay(train_id, incidents)
                model.add(start >= bound)
            previous = index
        if future:
            last = future[-1]
            delay = model.new_int_var(0, horizon, f'delay{train_id}')
            model.add(delay >= variables[last][1] - schedule[last].end)
            weights = settings.objective_weights
            priority = trains[train_id].priority if strategy == 'passenger' else 1
            multiplier = weights['delay'] + weights['priority'] * priority + weights['deviation']
            if strategy == 'stable':
                disturbed = model.new_bool_var(f'disturbed{train_id}')
                model.add(delay > 0).only_enforce_if(disturbed)
                model.add(delay == 0).only_enforce_if(disturbed.Not())
                terms.append(disturbed * 20000)
            terms.append(delay * max(1, int(10 * multiplier)))
            for a, b in zip(indices, indices[1:]):
                if b in future:
                    hold = model.new_bool_var(f'hold{a}')
                    model.add(variables[b][0] > variables[a][1]).only_enforce_if(hold)
                    model.add(variables[b][0] == variables[a][1]).only_enforce_if(hold.Not())
                    terms.append(hold * int(weights['stops'] * 60))
    model.minimize(sum(terms))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = settings.max_optimizer_runtime / 3
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 42
    status = solver.solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError('CP-SAT did not find a feasible plan within budget')
    return [v.model_copy(update={'start': solver.value(variables[i][0]), 'end': solver.value(variables[i][1])}) for i, v in enumerate(schedule)]


def optimize(schedule, trains, blocks, stations, incidents, now, settings, strategy):
    start = time.perf_counter()
    engine = 'CP-SAT'
    candidates = [heuristic(schedule, trains, blocks, stations, incidents, now, settings, order) for order in ('passenger', 'network', 'stable')]
    candidates = [p for p in candidates if not detect_conflicts(p, blocks, stations, incidents, now, settings.minimum_headway)]
    def score(plan):
        routes = defaultdict(list)
        for visit in plan:
            routes[visit.train_id].append(visit)
        cost = 0
        w = settings.objective_weights
        for train_id, route in routes.items():
            route.sort(key=lambda v:v.start)
            delay = max(0,route[-1].end-trains[train_id].scheduled_arrival)
            weight = w['delay'] + w['priority'] * (trains[train_id].priority if strategy=='passenger' else 1) + w['deviation']
            cost += delay * max(1,int(10*weight))
            if strategy=='stable' and delay:
                cost += 20000
            cost += sum(b.start>a.end for a,b in zip(route,route[1:]) if b.start>now) * int(w['stops']*60)
        return cost
    try:
        result = cp_schedule(schedule, trains, blocks, stations, incidents, now, settings, strategy)
        if detect_conflicts(result, blocks, stations, incidents, now, settings.minimum_headway):
            raise RuntimeError('Independent validator rejected CP-SAT output')
        if candidates and score(min(candidates,key=score)) < score(result):
            result=min(candidates,key=score)
            engine='validated heuristic (better incumbent)'
    except (ImportError, RuntimeError) as exc:
        engine = 'deterministic fallback'
        result = min(candidates,key=score) if candidates else heuristic(schedule, trains, blocks, stations, incidents, now, settings, strategy)
    conflicts = detect_conflicts(result, blocks, stations, incidents, now, settings.minimum_headway)
    if conflicts:
        raise ValueError('No conflict-free recommendation is feasible with committed occupations')
    return result, engine, round((time.perf_counter() - start) * 1000, 1)
