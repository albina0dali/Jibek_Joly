def quality(states, conflicts, incidents, settings, energy_savings=0):
    active = [s for s in states if s['status'] != 'completed']
    weighted_delay = sum(s['delay_seconds'] * s['priority'] for s in active) / max(1, sum(s['priority'] for s in active))
    average_delay = sum(s['delay_seconds'] for s in active) / max(1, len(active))
    moving = sum(s['speed_kmh'] > 0 for s in active)
    utilization = moving / max(1, len(active))
    scores = dict(schedule=max(0, 100-weighted_delay/30), capacity=max(0, 100-abs(.7-utilization)*45-len(conflicts)*2), energy=min(100, 75+energy_savings), conflict=max(0,100-12*len(conflicts)), arrival=max(0,100-average_delay/40))
    reasons = dict(schedule=f'Priority-weighted delay {weighted_delay/60:.1f} min', capacity=f'{moving}/{len(active)} services moving; target utilization 70%', energy=f'Mean advisory energy saving {energy_savings:.1f}% over full-power baseline', conflict=f'{len(conflicts)} unresolved resource conflicts', arrival=f'Mean projected arrival deviation {average_delay/60:.1f} min')
    components = [dict(name=k, score=round(v,1), weight=settings.quality_weights[k], contribution=round(v*settings.quality_weights[k]/100,2), reason=reasons[k]) for k,v in scores.items()]
    value = round(sum(v*settings.quality_weights[k]/100 for k,v in scores.items()), 1)
    factors = [dict(label=f'{s["train_id"]} · projected +{s["delay_seconds"]/60:.1f} min', impact=round(s['delay_seconds']/30,1)) for s in sorted(active,key=lambda x:-x['delay_seconds']) if s['delay_seconds'] > 0][:3]
    factors += [dict(label=f'{i["location_id"]} · {i["type"].replace("_"," ")}', impact=12) for i in incidents if i['status'] == 'active']
    return dict(value=value, category='NORMAL' if value>=settings.normal_threshold else 'ATTENTION' if value>=settings.attention_threshold else 'CRITICAL', components=components, factors=factors, formula='Q = Σ(component score × weight / 100)')
