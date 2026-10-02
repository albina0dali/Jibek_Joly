"""Reproducible fictional corridor. Run: python generate_demo_data.py --seed 42."""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.models import Block, Station, Train, Visit, Settings
from app.scheduler import heuristic


def generate(seed=42, output=None):
    rng = random.Random(seed)
    output = Path(output or Path(__file__).resolve().parents[4] / 'data')
    output.mkdir(parents=True, exist_ok=True)
    names = ['Arqa Junction', 'Sarybel', 'Kumyr', 'Terek', 'Bastau', 'Zhalyn', 'Aksai Yard', 'Dala Terminal']
    distances = [0, 18, 43, 61, 89, 112, 138, 164]
    stations = [Station(id=f'S{i+1}', name=name, distance_km=distances[i], platform_count=3 if i in (1, 3, 6) else 2, siding_available=i in (1, 3, 6)) for i, name in enumerate(names)]
    blocks = []
    for i in range(7):
        midpoint = (distances[i] + distances[i+1]) / 2
        for j, (a, b) in enumerate(((distances[i], midpoint), (midpoint, distances[i+1]))):
            double = i in (0, 2, 5, 6)
            blocks.append(Block(id=f'B{2*i+j+1:02}', from_station=f'S{i+1}', to_station=f'S{i+2}', start_km=a, end_km=b, distance_km=b-a, track_type='double' if double else 'single', speed_limit_kmh=[120, 100, 130, 90, 110, 100, 120][i], capacity=2 if double else 1))
    trains, schedule = [], []
    for i in range(16):
        kind = ['express', 'passenger', 'freight', 'passenger', 'freight'][i % 5]
        priority = {'express': 3, 'passenger': 2, 'freight': 1}[kind]
        prefix = {'express': 'E', 'passenger': 'P', 'freight': 'F'}[kind]
        direction = 1 if i % 2 == 0 else -1
        departure = i * 150 + rng.randint(0, 35)
        train = Train(id=f'{prefix}{101+i}', service_number=f'{prefix}-{701+i}', type=kind, priority=priority, origin='S1' if direction == 1 else 'S8', destination='S8' if direction == 1 else 'S1', length_m=rng.randint(480, 850) if kind == 'freight' else rng.randint(180, 300), max_speed_kmh={'express': 140, 'passenger': 120, 'freight': rng.choice([75, 80, 85])}[kind], scheduled_departure=departure, direction=direction, planned_stops=[s.id for s in stations[1:-1] if kind != 'express' or s.siding_available])
        clock = departure
        for block in blocks if direction == 1 else list(reversed(blocks)):
            travel = round(block.distance_km / (min(train.max_speed_kmh, block.speed_limit_kmh) * .85) * 3600)
            a, b = (block.start_km, block.end_km) if direction == 1 else (block.end_km, block.start_km)
            schedule.append(Visit(train_id=train.id, resource=block.id, kind='block', start=clock, end=clock+travel, from_km=a, to_km=b, direction=direction))
            clock += travel
            station = next((s for s in stations if s.distance_km == b), None)
            if station:
                dwell = rng.randint(80, 140) if station.id in train.planned_stops else 25
                schedule.append(Visit(train_id=train.id, resource=station.id, kind='station', start=clock, end=clock+dwell, from_km=b, to_km=b, direction=direction))
                clock += dwell
        trains.append(train)
    resolved = heuristic(schedule, {t.id:t for t in trains}, {b.id:b for b in blocks}, {s.id:s for s in stations}, [], -1, Settings(), 'network')
    timetable = []
    for train in trains:
        route = [v for v in resolved if v.train_id == train.id]
        train.scheduled_arrival = route[-1].end
        train.scheduled_departure = route[0].start
        timetable.extend(dict(train_id=v.train_id, station_id=v.resource, scheduled_arrival=v.start, scheduled_departure=v.end, minimum_dwell_seconds=v.end-v.start) for v in route if v.kind == 'station')
    data = {'stations': [s.model_dump() for s in stations], 'blocks': [b.model_dump() for b in blocks], 'trains': [t.model_dump() for t in trains], 'timetable': timetable, 'schedule': [v.model_dump() for v in resolved], 'signals': [dict(id=f'SIG-{b.id}-{d}', block_id=b.id, direction=d, status='green', last_update=0) for b in blocks for d in (-1, 1)], 'speed_limits': [dict(block_id=b.id, speed_limit_kmh=b.speed_limit_kmh) for b in blocks], 'incidents': [dict(type='delay_10', location_id='P104', duration=600), dict(type='block_closure', location_id='B07', duration=600)], 'metadata': dict(seed=seed, fictional=True, simulation_start=2400, timezone='Asia/Qyzylorda', epoch='2026-10-01T08:00:00+05:00')}
    for name, value in data.items():
        (output / f'{name}.json').write_text(json.dumps(value, indent=2), encoding='utf-8')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()
    generate(args.seed, args.output)
    print(f'Generated fictional railway dataset (seed {args.seed}).')
