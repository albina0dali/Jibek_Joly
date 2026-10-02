import json
import logging
import math
import os
import threading
import time
from pathlib import Path
from .models import Block, Station, Train, Visit, Settings
from .conflicts import detect_conflicts
from .scheduler import optimize
from .quality import quality
from .ato import profile
from .history import HistoryStore
from .ingestion import EventBus, IngestionPipeline

log = logging.getLogger('autodispatcher')
DATA = Path(__file__).resolve().parents[3] / 'data' / 'extensions' / 'operations'


class Simulator:
    def __init__(self, database=None):
        if not (DATA / 'schedule.json').exists():
            raise FileNotFoundError('Rebased demo data missing; run node scripts/build-station-registry.mjs')
        def read(name):
            return json.loads((DATA / f'{name}.json').read_text(encoding='utf-8'))
        self.stations = {s['id']: Station(**s) for s in read('stations')}
        self.blocks = {b['id']: Block(**b) for b in read('blocks')}
        self.trains = {t['id']: Train(**t) for t in read('trains')}
        self.signals = read('signals')
        self.baseline = [Visit(**v) for v in read('schedule')]
        self.settings = Settings()
        self.store = HistoryStore(database or os.getenv('DATABASE_PATH', str(DATA / 'operations.sqlite')))
        if self.store.configuration():
            self.settings=Settings(**self.store.configuration())
        self.lock = threading.RLock()
        self.bus = EventBus()
        self.bus.subscribe(lambda event: log.info('event=%s time=%s', event['type'], event['time']))
        self.ingestion = IngestionPipeline()
        self.optimizer_runs = 0
        self.optimizer_times = []
        self.replanning = False
        self.optimizer_error = None
        self.revision = 0
        self.reset()

    def reset(self):
        with self.lock:
            self.time = 2400
            self.paused = False
            self.schedule = [v.model_copy() for v in self.baseline]
            self.incidents = []
            self.resolved_conflicts = []
            self.options = []
            self.selected_recommendation = None
            self.optimizer_error = None
            self.energy_savings = 0
            self.revision += 1
            self.store.clear()
            # Deterministic warm-up is actual simulated history, not invented telemetry.
            for t in range(self.time-900, self.time+1, 15):
                self.store.save(self.snapshot(at=t, include_options=False))
            self.store.log(self.time, 'Seed 42 scenario initialized; 15-minute warm-up recorded')

    def states(self, schedule=None, at=None):
        now = self.time if at is None else at
        schedule = self.schedule if schedule is None else schedule
        result = []
        for train in self.trains.values():
            route = sorted((v for v in schedule if v.train_id == train.id), key=lambda v:v.start)
            current = next((v for v in route if v.start <= now < v.end), None)
            previous = [v for v in route if v.end <= now]
            upcoming = next((v for v in route if v.start > now), None)
            position = current.from_km if current else previous[-1].to_km if previous else (0 if train.direction == 1 else 164)
            ratio, speed = 0, 0
            if current and current.kind == 'block':
                ratio = (now-current.start)/(current.end-current.start)
                position += (current.to_km-current.from_km)*ratio
                speed = abs(current.to_km-current.from_km)/(current.end-current.start)*3600
            block_id = current.resource if current and current.kind == 'block' else None
            completed = now >= route[-1].end
            waiting = not current or current.kind == 'station'
            status = 'completed' if completed else 'scheduled' if now < route[0].start else 'stopped' if waiting else 'moving'
            delay = max(0, route[-1].end-train.scheduled_arrival)
            next_station = next((s.id for s in sorted(self.stations.values(), key=lambda s:train.direction*s.distance_km) if (s.distance_km-position)*train.direction > .01), train.destination)
            eta_next = next((v.start for v in route if v.kind=='station' and v.resource==next_station and v.end>=now),route[-1].end)
            result.append(dict(**train.model_dump(), train_id=train.id, timestamp=now, block_id=block_id, position_ratio=round(ratio,4), distance_km=round(position,3), speed_kmh=round(speed,1), allowed_speed=min(train.max_speed_kmh,self.blocks[block_id].speed_limit_kmh) if block_id else train.max_speed_kmh, delay_seconds=delay, status=status, next_station=next_station, eta=route[-1].end, next_station_eta=eta_next, recommendation=f'Proceed toward {next_station} at {speed:.0f} km/h' if speed else f'Hold at {position:.1f} km until {upcoming.start if upcoming else route[-1].end}s', energy_estimate=round((164-position if train.direction==1 else position)*1.5,1)))
        return result

    def snapshot(self, at=None, include_options=True):
        now = self.time if at is None else at
        states = self.states(at=now)
        conflicts = detect_conflicts(self.schedule,self.blocks,self.stations,self.incidents,now,self.settings.minimum_headway)
        for state in states:
            state['upcoming_conflicts'] = [c for c in conflicts if state['id'] in c['affected_trains']]
        savings = getattr(self, 'energy_savings', 0)
        q = quality(states,conflicts,self.incidents,self.settings,savings)
        occupied = {s['block_id'] for s in states if s['block_id']}
        network_blocks = []
        for b in self.blocks.values():
            relevant = [i for i in self.incidents if i['status']=='active' and i['location_id']==b.id and i['start_time']<=now<i['end_time']]
            status = 'closed' if any(i['type'] in ('block_closure','signal_failure') for i in relevant) else 'occupied' if b.id in occupied else 'restricted' if any(i['type']=='speed_restriction' for i in relevant) else 'free'
            network_blocks.append(dict(**{k:v for k,v in b.model_dump().items() if k!='status'},status=status))
        signals = []
        for signal in self.signals:
            unavailable = any(i['type']=='signal_failure' and i['location_id']==signal['block_id'] and i['start_time']<=now<i['end_time'] and i['status']=='active' for i in self.incidents)
            signals.append({**signal,'status':'unavailable' if unavailable else 'red' if signal['block_id'] in occupied else 'green','last_update':now})
        return dict(time=now,paused=self.paused,speed=self.settings.simulation_speed,trains=states,blocks=network_blocks,stations=[s.model_dump() for s in self.stations.values()],signals=signals,conflicts=conflicts,resolved_conflicts=self.resolved_conflicts,incidents=self.incidents,quality=q,schedule=[v.model_dump() for v in self.schedule],baseline=[v.model_dump() for v in self.baseline],options=self.options if include_options else [],selected_recommendation=self.selected_recommendation,replanning=self.replanning,optimizer_error=self.optimizer_error,revision=self.revision)

    def tick(self):
        with self.lock:
            if self.paused:
                return
            self.time += self.settings.simulation_speed
            for incident in self.incidents:
                if incident['end_time'] <= self.time:
                    incident['status'] = 'resolved'
            for state in self.states():
                noise = .8 * math.sin(self.time + int(state['id'][1:]))
                event = dict(id=f'{state["id"]}:{self.time}',train_id=state['id'],timestamp=self.time,speed_kmh=max(0,state['speed_kmh']+noise))
                self.ingestion.ingest(event,self.time)
                if self.time % 17 == 0:
                    self.ingestion.ingest(event,self.time)
                if self.time % 31 == 0:
                    self.ingestion.ingest({**event,'id':event['id']+':old','timestamp':self.time-30},self.time)
            self.bus.publish(dict(type='state_updated',time=self.time))
            if self.time % 10 < self.settings.simulation_speed:
                self.energy_savings = sum(profile(t,self.blocks,self.stations,s,self.time,self.incidents)['energy_saving_percent'] for t,s in zip(self.trains.values(),self.states()))/len(self.trains)
            self.store.save(self.snapshot(include_options=False))

    def inject(self, payload):
        with self.lock:
            train_event = payload.type in ('delay_5','delay_10','prolonged_dwell')
            if payload.location_id not in (self.trains if train_event else self.blocks):
                raise ValueError('Select a train for a delay/dwell incident or a block for infrastructure incidents')
            if train_event and all(v.end<=self.time for v in self.schedule if v.train_id==payload.location_id):
                raise ValueError('Selected service has completed its route')
            delay = 300 if payload.type=='delay_5' else 600 if payload.type=='delay_10' else payload.duration if payload.type=='prolonged_dwell' else 0
            start = self.time
            if not train_event:
                start = max([start]+[v.end for v in self.schedule if v.resource==payload.location_id and v.start<=self.time<v.end])
            incident = dict(id=f'I{len(self.incidents)+1:03}',type=payload.type,location_id=payload.location_id,start_time=start,end_time=start+payload.duration,expected_duration=payload.duration,delay_seconds=delay,severity='critical' if payload.type in ('block_closure','signal_failure') else 'attention',status='active')
            self.incidents.append(incident)
            if train_event:
                self.schedule = [v.model_copy(update={'start':v.start+delay,'end':v.end+delay}) if v.train_id==payload.location_id and v.start>self.time else v for v in self.schedule]
            # Shifted candidate schedule intentionally exposes genuine predicted conflicts.
            self.options=[]
            self.revision+=1
            self.store.log(self.time,f'Injected {payload.type} at {payload.location_id}')
            self.bus.publish(dict(type='incident_injected',time=self.time,incident=incident))
            self.store.save(self.snapshot(include_options=False))
            return incident

    def replan(self):
        with self.lock:
            if self.replanning:
                return
            self.replanning=True
            self.optimizer_error=None
            revision=self.revision
            now=self.time
            # Use baseline plus committed intervals; delay constraints are applied once.
            source=[]
            for base in self.baseline:
                active=next((v for v in self.schedule if v.train_id==base.train_id and v.resource==base.resource and v.kind==base.kind),base)
                source.append(active.model_copy() if active.start<=now else base.model_copy(update={'start':max(base.start,now+1),'end':max(base.start,now+1)+(base.end-base.start)}))
            trains,blocks,stations=self.trains,self.blocks,self.stations
            incidents=json.loads(json.dumps(self.incidents))
            settings=self.settings.model_copy(deep=True)
        options=[]
        try:
            for strategy,label in [('passenger','Protect passenger priority'),('network','Minimize network delay'),('stable','Preserve service stability')]:
                result,engine,ms=optimize(source,trains,blocks,stations,incidents,now,settings,strategy)
                new_states=self.states(schedule=result,at=now)
                before={s['id']:s for s in self.states(at=now)}
                changed=[s for s in new_states if s['eta']!=before[s['id']]['eta']]
                actions=[]
                for state in sorted(changed,key=lambda s:-s['priority'])[:5]:
                    route=[v for v in result if v.train_id==state['id']]
                    waits=[(v.start-route[i-1].end,route[i-1].to_km,v.resource) for i,v in enumerate(route) if i and v.start>route[i-1].end and v.start>now]
                    hold=max(waits,default=(0,0,'—'))
                    actions.append(f'{state["id"]} (priority {state["priority"]}): hold {hold[0]/60:.1f} min at km {hold[1]:.1f} before {hold[2]}; arrival deviation +{state["delay_seconds"]/60:.1f} min.')
                q=quality(new_states,[],incidents,settings,getattr(self,'energy_savings',0))
                options.append(dict(id=f'R{revision}-{strategy}',revision=revision,objective=strategy,label=label,actions=actions or ['Current schedule satisfies all resource constraints; no additional holds required.'],estimated_total_delay=sum(s['delay_seconds'] for s in new_states),affected_train_count=len(changed),remaining_conflicts=0,quality_index=q['value'],calculation_time_ms=ms,engine=engine,recovery_time=max([now]+[v.end for v in result if v.train_id in [s['id'] for s in changed]]),schedule=[v.model_dump() for v in result],explanation=' '.join(actions[:2]) if actions else 'Retain the current feasible resource ordering.'))
                self.optimizer_runs+=1
                self.optimizer_times.append(ms)
            with self.lock:
                if revision==self.revision:
                    self.options=options
                    self.store.log(self.time,f'Replanning finished: {len(options)} verified alternatives, {sum(o["calculation_time_ms"] for o in options):.0f} ms')
        except Exception as exc:
            log.exception('Replanning failed')
            with self.lock:
                self.optimizer_error=str(exc)
        finally:
            with self.lock:
                self.replanning=False
                self.bus.publish(dict(type='replanning_finished',time=self.time))

    def apply(self, option_id):
        with self.lock:
            option=next((o for o in self.options if o['id']==option_id),None)
            if not option or option['revision']!=self.revision:
                raise ValueError('Recommendation is stale; recalculate the plan')
            candidate=[Visit(**v) for v in option['schedule']]
            # A plan cannot teleport a train after computation or change its committed interval.
            for current in self.schedule:
                if current.start<=self.time<current.end:
                    proposed=next((v for v in candidate if v.train_id==current.train_id and v.resource==current.resource and v.kind==current.kind),None)
                    if not proposed or (proposed.start,proposed.end)!=(current.start,current.end):
                        raise ValueError('Traffic advanced beyond this plan; recalculate before applying')
            if detect_conflicts(candidate,self.blocks,self.stations,self.incidents,self.time,self.settings.minimum_headway):
                raise ValueError('Independent validation rejected this recommendation')
            self.resolved_conflicts.extend({**c,'status':'resolved','resolved_time':self.time} for c in detect_conflicts(self.schedule,self.blocks,self.stations,self.incidents,self.time,self.settings.minimum_headway))
            self.schedule=candidate
            self.selected_recommendation=option['label']
            self.revision+=1
            self.options=[]
            self.store.log(self.time,f'Applied to simulator: {option["label"]}; zero hard conflicts')
            self.store.save(self.snapshot(include_options=False))
            self.bus.publish(dict(type='plan_applied',time=self.time))
            return self.snapshot()
