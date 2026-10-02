"""Wagon grouping + track and shunting locomotive scheduling with CP-SAT."""
import math
import time
from collections import defaultdict
from ortools.sat.python import cp_model


def metrics(plan,wagons):
    lookup={w['id']:w for w in wagons}
    waiting=sum(max(0,t['departure']-lookup[w]['arrival_time'])/3600 for t in plan for w in t['wagon_ids'])
    tardiness=sum(max(0,t['departure']-lookup[w]['deadline'])/60 for t in plan for w in t['wagon_ids'])
    return dict(train_count=len(plan),wagon_hours=round(waiting,2),late_wagon_minutes=round(tardiness,1),wagon_count=sum(len(t['wagon_ids']) for t in plan),mean_fill_percent=round(sum(t['length_m']/t['length_limit_m']*100 for t in plan)/max(1,len(plan)),1))


def baseline(data,batch_size=10):
    groups=defaultdict(list)
    for wagon in sorted(data['wagons'],key=lambda w:(w['arrival_time'],w['id'])):
        groups[wagon['destination']].append(wagon)
    track_ready={t['id']:t['available_time'] for t in data['tracks']}
    loco_ready={l['id']:l['available_time'] for l in data['shunters']}
    batches=[]
    for destination,wagons in groups.items():
        for i in range(0,len(wagons),batch_size):
            batches.append((destination,wagons[i:i+batch_size]))
    batches.sort(key=lambda b:(max(w['arrival_time'] for w in b[1]),b[0]))
    plan=[]
    for destination,wagons in batches:
        length=sum(w['length_m'] for w in wagons)
        mass=sum(w['mass_t'] for w in wagons)
        compatible=[t for t in data['tracks'] if length<=min(t['length_m'],data['max_train_length_m']) and mass<=min(t['max_mass_t'],data['max_train_mass_t'])]
        choices=[(max(max(w['arrival_time'] for w in wagons),track_ready[t['id']],loco_ready[l['id']]),t,l) for t in compatible for l in data['shunters']]
        if not choices:
            raise ValueError('A wagon batch cannot fit any usable formation track')
        start,track,loco=min(choices,key=lambda c:(c[0],c[1]['id'],c[2]['id']))
        end=start+(data['formation_setup_minutes']+len(wagons)*data['formation_minutes_per_wagon'])*60
        depart=end+data['departure_clearance_minutes']*60
        track_ready[track['id']]=depart
        loco_ready[loco['id']]=end
        plan.append(dict(id=f'YT-{len(plan)+1:02}',destination=destination,wagon_ids=[w['id'] for w in wagons],length_m=length,mass_t=mass,length_limit_m=min(track['length_m'],data['max_train_length_m']),track_id=track['id'],shunter_id=loco['id'],formation_start=start,formation_end=end,departure=depart))
    return plan


def validate(plan,data):
    wagons={w['id']:w for w in data['wagons']}
    tracks={t['id']:t for t in data['tracks']}
    shunters={l['id']:l for l in data['shunters']}
    assigned=[]
    for train in plan:
        ws=[wagons[w] for w in train['wagon_ids']]
        track=tracks[train['track_id']]
        loco=shunters[train['shunter_id']]
        assert ws and all(w['destination']==train['destination'] for w in ws),'Mixed destinations'
        assert sum(w['length_m'] for w in ws)==train['length_m']<=min(track['length_m'],data['max_train_length_m']),'Length exceeded'
        assert sum(w['mass_t'] for w in ws)==train['mass_t']<=min(track['max_mass_t'],data['max_train_mass_t']),'Mass exceeded'
        assert train['formation_start']>=max([track['available_time'],loco['available_time']]+[w['arrival_time'] for w in ws]),'Formation before resources/arrivals'
        assert train['formation_end']-train['formation_start']>=(data['formation_setup_minutes']+len(ws)*data['formation_minutes_per_wagon'])*60
        assert train['departure']>=train['formation_end']+data['departure_clearance_minutes']*60
        assigned+=train['wagon_ids']
    assert sorted(assigned)==sorted(wagons),'Every wagon must be assigned once'
    for i,a in enumerate(plan):
        for b in plan[i+1:]:
            if a['track_id']==b['track_id']:
                assert a['departure']<=b['formation_start'] or b['departure']<=a['formation_start'],'Track overlap'
            if a['shunter_id']==b['shunter_id']:
                assert a['formation_end']<=b['formation_start'] or b['formation_end']<=a['formation_start'],'Shunter overlap'
    return True


def objective(plan,data):
    lookup={w['id']:w for w in data['wagons']}
    return len(plan)*1400+sum((t['departure']-lookup[w]['arrival_time'])//60+4*lookup[w]['priority']*max(0,(t['departure']-lookup[w]['deadline'])//60) for t in plan for w in t['wagon_ids'])


def solve(data,runtime=2):
    started=time.perf_counter()
    before=baseline(data)
    best=min((baseline(data,n) for n in (8,10,12,15,20)),key=lambda p:objective(p,data))
    model=cp_model.CpModel()
    grouped=defaultdict(list)
    for w in data['wagons']:
        grouped[w['destination']].append(w)
    reference=data['reference_time']
    slots=[]
    assignment={}
    terms=[]
    track_intervals=defaultdict(list)
    loco_intervals=defaultdict(list)
    # Each destination has enough candidate trains to reproduce the baseline.
    for dest,ws in sorted(grouped.items()):
        for n in range(math.ceil(len(ws)/8)):
            k=len(slots)
            used=model.new_bool_var(f'used{k}')
            start=model.new_int_var(0,360,f'start{k}')
            end=model.new_int_var(0,400,f'end{k}')
            dep=model.new_int_var(0,410,f'dep{k}')
            count=model.new_int_var(0,len(ws),f'count{k}')
            members=[]
            for w in ws:
                x=model.new_bool_var(f'{w["id"]}-{k}')
                assignment[(w['id'],k)]=x
                members.append(x)
                arrival=(w['arrival_time']-reference)//60
                model.add(start>=arrival).only_enforce_if(x)
                wait=model.new_int_var(0,410,f'wait{w["id"]}-{k}')
                model.add(wait==dep-arrival).only_enforce_if(x)
                model.add(wait==0).only_enforce_if(x.Not())
                late=model.new_int_var(0,410,f'late{w["id"]}-{k}')
                model.add(late>=dep-(w['deadline']-reference)//60).only_enforce_if(x)
                model.add(late==0).only_enforce_if(x.Not())
                terms += [wait,late*4*w['priority']]
            model.add(count==sum(members))
            model.add(count>=1).only_enforce_if(used)
            model.add(count==0).only_enforce_if(used.Not())
            model.add(end==start+data['formation_setup_minutes']+count*data['formation_minutes_per_wagon']).only_enforce_if(used)
            model.add(dep==end+data['departure_clearance_minutes']).only_enforce_if(used)
            model.add(start==0).only_enforce_if(used.Not())
            model.add(end==0).only_enforce_if(used.Not())
            model.add(dep==0).only_enforce_if(used.Not())
            lengths=sum(w['length_m']*assignment[(w['id'],k)] for w in ws)
            masses=sum(w['mass_t']*assignment[(w['id'],k)] for w in ws)
            model.add(lengths<=data['max_train_length_m'])
            model.add(masses<=data['max_train_mass_t'])
            track_choices=[]
            for track in data['tracks']:
                choice=model.new_bool_var(f'track{track["id"]}-{k}')
                track_choices.append(choice)
                model.add(lengths<=track['length_m']).only_enforce_if(choice)
                model.add(masses<=track['max_mass_t']).only_enforce_if(choice)
                model.add(start>=(track['available_time']-reference)//60).only_enforce_if(choice)
                duration=model.new_int_var(0,410,f'track_duration{track["id"]}-{k}')
                model.add(duration==dep-start)
                track_intervals[track['id']].append(model.new_optional_interval_var(start,duration,dep,choice,f'ti{track["id"]}-{k}'))
            model.add(sum(track_choices)==used)
            loco_choices=[]
            for loco in data['shunters']:
                choice=model.new_bool_var(f'loco{loco["id"]}-{k}')
                loco_choices.append(choice)
                model.add(start>=(loco['available_time']-reference)//60).only_enforce_if(choice)
                duration=model.new_int_var(0,400,f'loco_duration{loco["id"]}-{k}')
                model.add(duration==end-start)
                loco_intervals[loco['id']].append(model.new_optional_interval_var(start,duration,end,choice,f'li{loco["id"]}-{k}'))
            model.add(sum(loco_choices)==used)
            slots.append(dict(destination=dest,used=used,start=start,end=end,dep=dep,tracks=track_choices,locos=loco_choices))
            terms.append(used*1400)
    for w in data['wagons']:
        model.add(sum(x for (wid,_),x in assignment.items() if wid==w['id'])==1)
    for intervals in list(track_intervals.values())+list(loco_intervals.values()):
        model.add_no_overlap(intervals)
    # Seed a complete feasible grouping/resource schedule, with stable slot IDs.
    hint_groups=defaultdict(list)
    for train in before:
        hint_groups[train['destination']].append(train)
    destination_index=defaultdict(int)
    for k,slot in enumerate(slots):
        dest=slot['destination']
        n=destination_index[dest]
        destination_index[dest]+=1
        train=hint_groups[dest][n] if n<len(hint_groups[dest]) else None
        model.add_hint(slot['used'],int(train is not None))
        for key,field in [('start','formation_start'),('end','formation_end'),('dep','departure')]:
            model.add_hint(slot[key],(train[field]-reference)//60 if train else 0)
        for (wid,index),x in assignment.items():
            if index==k:
                model.add_hint(x,int(train is not None and wid in train['wagon_ids']))
        for i,x in enumerate(slot['tracks']):
            model.add_hint(x,int(train is not None and data['tracks'][i]['id']==train['track_id']))
        for i,x in enumerate(slot['locos']):
            model.add_hint(x,int(train is not None and data['shunters'][i]['id']==train['shunter_id']))
    model.minimize(sum(terms))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=runtime
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=42
    status=solver.solve(model)
    engine='deterministic feasible batching'
    if status in (cp_model.FEASIBLE,cp_model.OPTIMAL):
        candidate=[]
        for k,slot in enumerate(slots):
            if not solver.value(slot['used']):
                continue
            ws=[w for w in data['wagons'] if (w['id'],k) in assignment and solver.value(assignment[(w['id'],k)])]
            track=next(t for i,t in enumerate(data['tracks']) if solver.value(slot['tracks'][i]))
            loco=next(l for i,l in enumerate(data['shunters']) if solver.value(slot['locos'][i]))
            candidate.append(dict(id=f'YT-{k+1:02}',destination=slot['destination'],wagon_ids=[w['id'] for w in ws],length_m=sum(w['length_m'] for w in ws),mass_t=sum(w['mass_t'] for w in ws),length_limit_m=min(track['length_m'],data['max_train_length_m']),track_id=track['id'],shunter_id=loco['id'],formation_start=reference+60*solver.value(slot['start']),formation_end=reference+60*solver.value(slot['end']),departure=reference+60*solver.value(slot['dep'])))
        validate(candidate,data)
        if objective(candidate,data)<=objective(best,data):
            best=candidate
            engine='CP-SAT optimal' if status==cp_model.OPTIMAL else 'CP-SAT feasible'
    validate(before,data)
    validate(best,data)
    bm,am=metrics(before,data['wagons']),metrics(best,data['wagons'])
    return dict(before=before,after=sorted(best,key=lambda t:t['formation_start']),before_metrics=bm,after_metrics=am,slots_freed=bm['train_count']-am['train_count'],wagon_hours_saved=round(bm['wagon_hours']-am['wagon_hours'],2),objective_before=objective(before,data),objective_after=objective(best,data),calculation_time_ms=round((time.perf_counter()-started)*1000,1),engine=engine,constraints_verified=True,objective_formula='wagon waiting minutes + 4 × priority-weighted tardiness + 1400 × formed trains',proof=dict(wagons_assigned=len(data['wagons']),resource_overlaps=0,length_violations=0,mass_violations=0))
