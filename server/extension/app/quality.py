import json
import math
from pathlib import Path

MODEL = json.loads((Path(__file__).resolve().parents[3] / 'web' / 'movement-index-model.json').read_text(encoding='utf-8'))


def calculate_movement_index(weighted_delay, average_delay, utilization, conflicts, energy_savings):
    clamp = lambda n: max(0, min(100, n))
    scores = dict(schedule=clamp(100-weighted_delay/MODEL['delay_divisor_seconds']), capacity=clamp(100-abs(MODEL['target_utilization']-utilization)*MODEL['utilization_penalty']-conflicts*MODEL['capacity_conflict_penalty']), energy=clamp(MODEL['energy_base']+clamp(energy_savings)*MODEL['energy_saving_coefficient']), conflict=clamp(100-MODEL['conflict_penalty']*conflicts), arrival=clamp(100-average_delay/MODEL['arrival_divisor_seconds']))
    # Same positive half-up rule as JavaScript Math.round, including .05 ties.
    return scores, math.floor(sum(v*MODEL['weights'][k]/100 for k,v in scores.items())*10+.5)/10


def quality(states, conflicts, incidents, settings, energy_savings=0):
    active = [s for s in states if s['status'] != 'completed']
    weighted_delay = sum(s['delay_seconds'] * s['priority'] for s in active) / max(1, sum(s['priority'] for s in active))
    average_delay = sum(s['delay_seconds'] for s in active) / max(1, len(active))
    moving = sum(s['speed_kmh'] > 0 for s in active)
    utilization = moving / max(1, len(active))
    scores, value = calculate_movement_index(weighted_delay, average_delay, utilization if active else .7, len(conflicts), energy_savings)
    reasons = dict(schedule=f'Priority-weighted delay {weighted_delay/60:.1f} min', capacity=f'{moving}/{len(active)} services moving; target utilization 70%', energy=f'Mean advisory energy saving {energy_savings:.1f}% over full-power baseline', conflict=f'{len(conflicts)} unresolved resource conflicts', arrival=f'Mean projected arrival deviation {average_delay/60:.1f} min')
    reasons['energy'] += '; advisory proxy score = 70 + 0.05 × saving%, not measured traction efficiency'
    components = [dict(name=k, score=round(v,1), weight=MODEL['weights'][k], contribution=round(v*MODEL['weights'][k]/100,2), reason=reasons[k]) for k,v in scores.items()]
    factors = [dict(label=f'{s["train_id"]} · projected +{s["delay_seconds"]/60:.1f} min', impact=round(s['delay_seconds']/30,1)) for s in sorted(active,key=lambda x:-x['delay_seconds']) if s['delay_seconds'] > 0][:3]
    factors += [dict(label=f'{i["location_id"]} · {i["type"].replace("_"," ")}', impact=12) for i in incidents if i['status'] == 'active']
    return dict(value=value, category='NORMAL' if value>=MODEL['normal_threshold'] else 'ATTENTION' if value>=MODEL['attention_threshold'] else 'CRITICAL', components=components, factors=factors, formula='I = Σ(component score × weight / 100)', model=MODEL['version'])
