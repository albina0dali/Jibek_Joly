import math


def profile(train, blocks, stations, state, now, incidents=None):
    """Distance-domain acceleration/braking envelope; transparent energy proxy."""
    origin = 0 if train.direction == 1 else 164
    destination = 164 if train.direction == 1 else 0
    position = state['distance_km']
    remaining = abs(destination - position)
    stop_distances = sorted(abs(s.distance_km - position) for s in stations.values() if s.id in train.planned_stops + [train.destination] and (s.distance_km - position) * train.direction > .01)
    count = max(2, math.ceil(remaining * 4) + 1)
    distances = [min(remaining, i * remaining / (count - 1)) for i in range(count)]
    limits = []
    for d in distances:
        km = position + train.direction * d
        block = next((b for b in blocks.values() if b.start_km <= km <= b.end_km), None)
        limits.append(min(train.max_speed_kmh, block.speed_limit_kmh if block else train.max_speed_kmh))
    # Insert exact station positions so braking envelopes reach zero at every stop.
    distances = sorted(set(distances + stop_distances))
    limits = []
    for d in distances:
        km = position + train.direction * d
        block = next((b for b in blocks.values() if b.start_km <= km <= b.end_km), None)
        limit = min(train.max_speed_kmh, block.speed_limit_kmh if block else train.max_speed_kmh)
        if block and any(i['type']=='speed_restriction' and i['location_id']==block.id and i['status']=='active' and i['start_time']<=now<i['end_time'] for i in (incidents or [])):
            limit=min(limit,40)
        limits.append(limit)
    def envelope(factor):
        speeds = [l * factor for l in limits]
        speeds[0] = min(state['speed_kmh'], limits[0])
        for i, d in enumerate(distances):
            if any(abs(d-s) < .00001 for s in stop_distances):
                speeds[i] = 0
        for i in range(1, len(speeds)):
            speeds[i] = min(speeds[i], math.sqrt((speeds[i-1]/3.6)**2 + 2 * .45 * (distances[i]-distances[i-1])*1000)*3.6)
        for i in range(len(speeds)-2, -1, -1):
            speeds[i] = min(speeds[i], math.sqrt((speeds[i+1]/3.6)**2 + 2 * .6 * (distances[i+1]-distances[i])*1000)*3.6)
        return speeds
    def travel_seconds(speeds):
        return sum((distances[i]-distances[i-1])*3600/max(.5, (speeds[i]+speeds[i-1])/2) for i in range(1, len(speeds))) + 100 * max(0, len(stop_distances)-1)
    baseline = envelope(1)
    target = max(now + travel_seconds(baseline), state['eta'])
    low, high = .65, 1.0
    for _ in range(20):
        mid = (low + high)/2
        if now + travel_seconds(envelope(mid)) > target:
            low = mid
        else:
            high = mid
    recommended = envelope(high)
    def energy(speeds):
        traction = sum(max(0, speeds[i]**2-speeds[i-1]**2)*.002 for i in range(1, len(speeds)))
        drag = sum((distances[i]-distances[i-1]) * (1 + (speeds[i]/100)**2) for i in range(1, len(speeds)))
        return traction + drag
    base_energy, recommended_energy = energy(baseline), energy(recommended)
    points = []
    for i, d in enumerate(distances):
        delta = recommended[i] - recommended[max(0, i-1)]
        next_stop = next((s for s in stop_distances if s >= d), remaining)
        phase = 'STOP' if recommended[i] < 1 else 'BRAKE' if delta < -1 else 'TRACTION' if delta > 1 else 'COAST' if 0 < next_stop-d < 3 else 'CRUISE'
        points.append(dict(distance_km=round(d, 3), route_km=round(position+train.direction*d, 3), speed_limit=limits[i], baseline=round(baseline[i], 2), recommended=round(recommended[i], 2), phase=phase, actual=state['speed_kmh'] if i == 0 else None))
    return dict(train_id=train.id, points=points, stops=stop_distances, acceleration_mps2=.45, braking_mps2=.6, target_arrival=round(target), recommended_arrival=round(now+travel_seconds(recommended)), baseline_energy=round(base_energy, 2), energy_estimate=round(recommended_energy, 2), energy_saving_percent=round(100*(1-recommended_energy/max(1,base_energy)), 1), schedule_deviation=round(now+travel_seconds(recommended)-state['eta']), energy_formula='Σ positive Δ(v²) × 0.002 + Σ distance × (1 + (v/100)²)', estimate_label='Simulation estimate · arbitrary energy units')
