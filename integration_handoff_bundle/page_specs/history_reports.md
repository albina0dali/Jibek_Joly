# PAGE PURPOSE

`/history`, History in frontend/src/pages.tsx. Replay recorded traffic snapshots and view audit actions; download actual live CSV/PDF. This is not just a visual timeline. No calendar/date picker, report range dropdown, audit text filter or separate history table exists in current code.

# USER FLOW

Enter → LIVE current topology/diagram/QI → choose last5/10/15min or drag scrubber → recorded snapshot fetched → play/pause replay → inspect historical train → return live. ExportCSV/PDF requests current live state regardless of replay. Route unmount discards local replay state; backend history remains.

# VISIBLE BLOCKS

1. Eyebrow AUDIT / HISTORY & REPORTS, H1 History & reports, descriptive text; Export CSV and Export PDF buttons.
2. Replay toolbar: LIVE/REPLAY badge; Last5min/10min/15min tabs (15 default); Play replay/Pause replay; range scrubber; displayed scenario clock; Return to live.
3. Status row Recorded QI, Incidents, Conflicts from replay||state; snapshot count from full retained backend index (not filtered to selected window).
4. Current network / Recorded network state panel: same compact inline SVG topology and native titles as Network. All stations,14 blocks, train markers, siding marks, signals and occupancy legend. Subtitle positions/incident/quality restored from one snapshot.
5. Recorded train diagram: same Diagram SVG/pan/zoom/hover/selection and original/applied layers from replay||state. No preview dropdown or type tabs here.
6. Operational action log, newest-first up to100 rows time+translated description. Log always latest global index.actions, even in replay and regardless of selected range.
7. Historical drawer owned inside History; live Network selection opens host live drawer. Diagram selection creates History drawer even in live mode.

# INTERACTIONS

| Control / update | Actual behaviour |
|---|---|
| Mount/index refresh | GET /api/history on session change and floor(state.time/5) change; paused time freezes refresh, not an independent polling timer |
| Last5/10/15min | range=300/600/900; setAt=max(first retained snapshot time,state.time-range); starts replay but does not stop an already playing timer |
| Scrubber | lower=max(first snapshot time,state.time-range), max=live state.time, value=at??live.time; onChange stops playback, sets integer target time |
| Fetch replay | GET /api/history?at=N returns newest stored time<=N; race/unmount guarded by active flag; errors notify, previous replay can remain |
| Play | toggles playing; if live starts at lower; timer increments at by15sec each500ms (~30 simulated seconds/real second) |
| Replay reaches now | playing=false; at=state.time but stays REPLAY, not LIVE until Return to live |
| Return to live | playing=false, at=null; useEffect clears replay; historySelected is not automatically cleared |
| Network train click | if replay present opens snapshot-owned drawer; otherwise calls host select with live state |
| Diagram train click | setHistorySelected; highlight + local drawer. Historical selection can persist across replay snapshots |
| Export | authenticated GET /api/reports/{csv|pdf}, Blob URL, download autodispatcher.ext, revoke after1s; errors toast. No query for at/range |
| Drawer | same fields as Dispatch, values from captured historical snapshot; close X/backdrop. No Escape-specific handler |

Range slider target and returned snapshot.time can differ (nearest earlier). Display clock uses replay.time, not requested at. Until network fetch completes, topology/status may briefly show old/live snapshot while REPLAY badge already changes. If request fails, there is no dedicated replay error panel. Preserve the actual asynchronous behaviour or explicitly agree a correction during integration.

# INPUT DATA / HISTORY FORMAT

HistoryStore SQLite tables:

```sql
snapshots(time INTEGER PRIMARY KEY, payload TEXT NOT NULL)
actions(id INTEGER PRIMARY KEY, time INTEGER, description TEXT)
configuration(id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)
```

Snapshot payload is full traffic Snapshot; stored options=[] because saves use include_options=False. Includes complete schedules, baseline,positions,blocks,signals,incidents,QI,current/resolved conflicts,revision. Yard data/results are absent. `get(at)` query time<=at ORDER BY time DESC LIMIT1. index returns ascending time/QI from SQLite JSON. `save` insert-or-replace; deletes snapshots older than now-3600. actions API newest first LIMIT100; actions table itself is not pruned. All access via sim.lock.

Startup/reset: self.time2400(08:40), clear snapshots/actions; save61 actual synthetic warm-up snapshots at1500..2400 step15 (08:25..08:40), initial audit action. Live tick each1real second advances1/2/5sim seconds; save every tick unless paused. Paused replan itself logs action but does not save snapshot; inject/apply save immediately, replacing any snapshot at same time. Settings change logs without snapshot. Yard solve/apply log without snapshot, and can be missed by paused History index until remount/time changes.

Actions: initial seed warm-up; injected incident; replanning finished(count/time); applied dispatch(label/zero conflicts); admin configuration change; synthetic resource optimization and apply. EventBus state_updated does not create per-tick action rows; tick saves snapshots. Historical incident resolved status is stored on tick. Global actions may include other original resource modules when connected to full original host; the portable host only has yard.

# COMPUTED VALUES / TIME

Same topology formulas as original Network: x=62+distance_km/164×956, viewBox1080×330; active trains excludes scheduled/completed; y arranged by direction/index. Statuses from same snapshot, signals direction+1 displayed; double-track second line; siding marks for available stations. Native titles provide block/type/status/speed and train speed/delay. Diagram rules in movement_plan.md. QI here is **stored value**, not recomputed on client.

Clock formatting adds8 to floor(seconds/3600), minutes/seconds from remainder, no timezone/date conversion. Scenario epoch metadata says2026-10-01T08:00+05. No historical calendar UI. PDF timezone text Asia/Qyzylorda; no host current-date substitution.

# CSV: REAL CONTENT

Header `category,id,status_or_score,delay_seconds_or_weight,detail`. Live rows for all16 trains(status,delay seconds,position/speed detail); all incidents(status,delay seconds,type/location); active/predicted plus resolved conflicts(status,predicted_delay,description); five quality components(score,weight,contribution+reason). No action-log rows, yard wagons/consists, historical snapshots or selected replay/window. Units depend on category; don't map this mixed schema to one metric blindly. Python csv writer uses standard delimiter/quoting; response text/csv. Labels/schema are English; no BOM or locale selector.

# PDF: REAL CONTENT

ReportLab A4, margins36/32; title Autodispatcher Demo Report; fictional advisory warning, oldest retained history time→live current time and Asia/Qyzylorda; current QI/category; total projected delay,hard-conflict count,selected recommendation; all-train table(id,type,state,delaymin,final arrival), repeatRows1; five-component quality breakdown; incident list; latest12 actions reversed to chronological order; disclaimer. `escape` handles user-visible text. Document default fonts/schemas stay English regardless of UI language. PDF is generated bytes, not browser print and not screenshot. No dedicated yard report or historical-map rendering. `data/captured/autodispatcher.csv/pdf` were downloaded while replay was selected to verify live export semantics.

# OUTPUT / SOURCE FILES / REQUIRED DEPENDENCIES

Historical network+diagram+drawer from same captured snapshot; global audit log; actualCSV/PDF. Source History.tsx, shared Network/Diagram/TrainDrawer, request/download/clock/i18n; backend history/store/reports/simulator/quality and scheduler (applied plans), reportlab. Reference screenshots: default/replay/snapshot drawer; captured history index and 62 payloads (61 warm-up plus any live ticks).

# ACCEPTANCE CHECKLIST

All three ranges, scrubber-nearest-earlier, replay15sec/500ms, pause, return live, historical vs live drawers, recorded QI/incidents/conflicts, raw latest-first actions/global scope, hour retention and reset, downloads with correct category fields, PDF alltrain/quality/action content; export live during replay; yard actions visible after index refresh, no claim yard snapshots replay.
