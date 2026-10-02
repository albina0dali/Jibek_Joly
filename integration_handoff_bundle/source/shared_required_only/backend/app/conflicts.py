from collections import defaultdict
from .models import Visit


def detect_conflicts(schedule: list[Visit], blocks: dict, stations: dict, incidents: list[dict], now: int, headway: int = 60) -> list[dict]:
    result = []

    def add(kind, location, trains, start, end, description):
        if end <= now:
            return
        key = f'{kind}:{location}:{":".join(sorted(trains))}:{start}'
        result.append(dict(id=key, type=kind, severity='critical' if start <= now else 'attention', location=location,
                           start_time=start, affected_trains=sorted(trains), description=description,
                           predicted_delay=max(30, end - max(start, now)), status='active' if start <= now else 'predicted'))

    grouped = defaultdict(list)
    for visit in schedule:
        grouped[visit.resource].append(visit)
    for resource, visits in grouped.items():
        visits.sort(key=lambda v: v.start)
        if resource in stations:
            # Sweep interval boundaries; capacity is an aggregate property, not pairwise.
            boundaries = sorted({v.start for v in visits} | {v.end for v in visits})
            for t, end in zip(boundaries, boundaries[1:]):
                occupants = [v for v in visits if v.start <= t < v.end]
                if len(occupants) > stations[resource].platform_count:
                    kind = 'platform_capacity' if stations[resource].siding_available else 'crossing_overtake'
                    add(kind, resource, [v.train_id for v in occupants], t, end, f'{len(occupants)} trains require {stations[resource].platform_count} platforms at {stations[resource].name}.')
            continue
        block = blocks[resource]
        for i, a in enumerate(visits):
            for b in visits[i + 1:]:
                if b.start >= a.end + headway:
                    break
                if a.train_id == b.train_id or (block.track_type == 'double' and a.direction != b.direction):
                    continue
                if b.start < a.end:
                    kind = 'opposing_direction' if a.direction != b.direction else 'exclusive_occupancy'
                    add(kind, resource, [a.train_id, b.train_id], b.start, min(a.end, b.end), f'{a.train_id} and {b.train_id} have incompatible occupation of {resource}.')
                else:
                    add('headway', resource, [a.train_id, b.train_id], b.start, a.end + headway, f'{b.train_id} enters {resource} before the {headway}s clearance after {a.train_id}.')
    for incident in incidents:
        if incident['status'] != 'active' or incident['type'] not in ('block_closure', 'signal_failure'):
            continue
        for v in grouped.get(incident['location_id'], []):
            start, end = max(v.start, incident['start_time']), min(v.end, incident['end_time'])
            if start < end:
                add('closed_block' if incident['type'] == 'block_closure' else 'signal_unavailable', v.resource, [v.train_id], start, end, f'{v.train_id} requires {v.resource} during {incident["type"].replace("_", " ")}.')
    return result
