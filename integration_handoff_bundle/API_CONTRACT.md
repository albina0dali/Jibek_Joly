# API contract, фактическое поведение

REST same-origin `/api`, Bearer token. Login public; прочие business endpoints 401 без session, срок24h. Errors `{detail:string|validationErrors}`; services.request преобразует detail в Error, UI toast/alert. Все схемы моделей доступны в `source/shared_required_only/backend/app/models.py`, frontend interfaces/types; полные examples в data/captured.

| Method / path | Input | Output / mutation |
|---|---|---|
| POST /api/auth/login | username,password | token,username,role,expires; in-memory session |
| GET /api/state | — | Snapshot (time,paused,speed,trains,stations,blocks,signals,baseline,schedule,incidents,conflicts,resolved_conflicts,quality,options,revision,replanning,optimizer_error,selected_recommendation) |
| WS /ws/live | first frame {token} within5s | same Snapshot every1s; invalid auth close4401 |
| POST /api/replan | no body | 3 Option[], source scenario unchanged; host fetches state afterward; solver error409 |
| POST /api/replan/{id}/apply | no body | Snapshot; validate revision/current occupation/conflicts; change schedule,revision, actions,stored snapshot; stale409 |
| GET /api/history | no query | {snapshots:[{time,quality}],actions:[{time,description}]} |
| GET /api/history?at=N | integer scenario seconds | latest stored Snapshot with time<=N, 404 if none |
| GET /api/reports/csv,pdf | no replay/range query | live snapshot export bytes, attachment autodispatcher.csv/pdf |
| GET /api/resources/yard | — | {module,seed,provenance,data,baseline,baseline_metrics,result,applied,version} |
| POST /api/resources/yard/optimize | {train_id:'F103',runtime_seconds:2} | full YardState; train_id ignored for yard; runtime constrained0.1..3, UI fixed2; errors409 |
| POST /api/resources/yard/apply | {plan_id,option_id?} | full YardState; option_id unused for yard; verifies result/current version and all yard constraints; sets applied + log, no traffic mutation |
| POST /api/simulation/{pause,resume,reset,1,2,5} | — | Snapshot; reset clears yard version/results and traffic history |
| POST /api/incidents | {type,location_id,duration:60..1800} | incident, future schedule shift/closure + background replan; fixture/host support, no incident page copied |
| GET /api/quality | — | Quality |
| GET/PUT /api/settings | Settings / admin for PUT | persisted configuration, changed revision, cleared options, action; reference host has no settings page |

Option fields: id,revision,objective,label,actions[],explanation,estimated_total_delay(seconds),affected_train_count,remaining_conflicts,quality_index,calculation_time_ms,engine,recovery_time(seconds),schedule:Visit[]. Frontend type does not list revision, but backend apply relies on it. Source ID `R{revision}-{passenger|network|stable}`. Yard plan ID `yard-{version}-{len(last100actions)}`; do not treat this as globally unique or production booking ID.

Visit `{train_id,resource,kind:block|station,start,end,from_km,to_km,direction,lane}`. lane serialized by backend, omitted from frontend Visit type. Resource IDs must resolve in stations or blocks. Time intervals half-open [start,end). Train.upcoming_conflicts derives from independently detected conflicts in current applied candidate; preview does not recompute Train fields.

## Dispatch algorithm / movement

Simulator.states sorts visits by start per train. In occupied block, fraction=(now-start)/(end-start), position=from_km+(to_km-from_km)×fraction, speed=abs(to-from)/(end-start)×3600; station/gap speed0. Display speed1 decimal, position3. Delay=max(0,final_visit.end-scheduled_arrival). Status completed after last end; scheduled before first start; stopped in station/gap, moving in block. Recommendation is simple movement/hold text, not LLM output.

Scheduler retains committed visits start<=now, sequences each route, excludes overlapping same-direction double-track or any single-track occupation, adds block headway default60s, station cumulative capacity, closures/signal failures, speed restriction duration at40km/h. Active train delay constraints summed once from baseline+committed source.

Three strategies: passenger (priority multiplier), network (unit multiplier), stable (adds20000 for delayed service). Selection cost per train: max(0,arrival-scheduled_arrival)×max(1,int(10×(delay Weight+priority Weight×strategy Priority+deviation Weight))) + future gaps×int(stops Weight×60), plus stable penalty. Defaults weights1,3,1,1. CP model measures end shift relative to source last visit; incumbent selection measures scheduled_arrival: preserve this source distinction. CP budget settings.max_optimizer_runtime/3 per strategy (default2/3s), seed42, worker1. Valid heuristic incumbents can replace CP; engine records fallback/better incumbent. No global-optimal guarantee for entire UI pipeline.

Independent validator: same single-track exclusive intervals; double-track opposite directions coexist; headway; aggregate platform capacity via interval sweep; active closure/signal intervals. Only conflicts with end>now retained. start<=now → active/critical, future → predicted/attention; predicted_delay=max(30,end-max(start,now)). Duplicate/symmetric events use deterministic IDs.

Apply checks not only revision: occupied intervals at **apply time** must preserve exact start/end, then independent no-conflict validation. Simulation advancement can in validate a calculated option without changed revision. Preserve errors/recalculate flow.
