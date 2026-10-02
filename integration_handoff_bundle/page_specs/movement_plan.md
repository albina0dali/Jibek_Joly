# PAGE PURPOSE

`/dispatch`, Dispatch in original frontend/src/pages.tsx:25. Compare original timetable, committed simulated movement and proposed schedules. No separate KPI-card strip or timetable table on this page. No geographic map here; the time–distance SVG is the main planning display. QI is in shared header; proposed QI exists in Option payload but not rendered in inspector.

# USER FLOW

Enter authenticated host → choose service type and time range → click trajectory or inspect dropdown → generate alternatives → choose preview → inspect changed ETA/explanation → Apply to simulator → preview clears and actual schedule updates. Open service details uses host drawer. Simulation pause/resume in header affects live state; it does not select preview.

# VISIBLE BLOCKS (top to bottom)

1. Eyebrow PLANNING / TIME–DISTANCE; H1 Dispatch plan (RU План движения), description about original timetable/committed movement/resource ordering; Generate alternatives button at right. Button text/busy Calculating… is raw English in current source.
2. Filters tabs: all, express, passenger, freight, delayed, conflict ing. Plan preview dropdown: Applied schedule + state.options labels in returned order. Diagram time range:30min(1800),1hour(3600 default),2hours(7200).
3. Two-column hierarchy: left Train diagram panel with subtitle distance increases southbound and Applied plan/Preview badge; right Plan inspector, Selected service, all-train dropdown, selected service ID/type, six definition rows: Service priority; Original ETA; Recommended ETA; Delay impact; Upcoming conflicts; Affected services. Open service details button. If preview selected, callout with option.label, option.explanation and Apply to simulator.
4. Validator note: block exclusivity/direction/headway/platform capacity/active restrictions; optimizer_error alert if present.
5. Host train drawer when requested, independent of preview selection. Shared live/clock/QI/language controls as described in ROUTES_AND_NAVIGATION.

# INTERACTIONS

| Control | Exact effect |
|---|---|
| Generate alternatives | disabled only while state.replanning; POST /api/replan; returns options[] then host GET /api/state; no schedule apply |
| Filter tab | local filter; graph trains only; does not restrict inspector dropdown or options |
| delayed | train.delay_seconds>0, not >=60 |
| conflict ing | train.upcoming_conflicts.length>0; derived from applied state, not preview |
| Preview dropdown | sets local preview ID; chooses option.schedule; no POST/no state mutation; empty → applied |
| Time range | local range seconds; does not reset graph zoom/pan |
| Pan earlier/later | local pan -/+300 seconds |
| Zoom in/out | ×/÷1.5, clamp1..4 |
| Click trajectory | set local selected ID, highlight and inspector; no drawer yet |
| Hover trajectory | caption ID/type/arrival+delay from applied train state; leave restores instructional caption |
| Inspect train dropdown | selected ID; all16 options, even when graph filtered |
| Open details | host select(selected) → drawer current live Snapshot |
| Apply | POST /api/replan/{option.id}/apply; on success clear preview, toast; failures keep preview, host toast |
| Drawer close | explicit X or backdrop click; inside click stops propagation; source has no Escape handler/focus trap |

Default selected=state.trains[0].id, filter=all, range3600, preview='', zoom1, pan0. Local state resets on route unmount. Selected train may be hidden by a graph filter, but inspector stays selected. Preview ID no longer present silently falls back to applied schedule; no explicit stale-preview alert until apply.

# INPUT DATA

Full Snapshot via shared GET/WS; stations/blocks/trains/schedule/signals source data; dynamically injected incidents/conflicts/options; PageProps host callbacks. Display names from i18n; station rows in Diagram use ID + chainage, not translated names. Original baseline is retained separate from schedule. All16 train routes use S1→S8 or reverse, with intermediate visits.

# COMPUTED VALUES / CHART DETAILS

Graph viewBox1080×490; plot x95..1020, y50..420. `start=state.time-600+pan`, `end=start+range/zoom`; `x=95+(t-start)/(end-start)*925`, `y=50+km/164*370`. Nine evenly spaced vertical time ticks and all station horizontal lines. polyline concatenates both endpoints of every visit; equal-distance station visits create horizontal time-axis dwells.

Per visible train: dashed original baseline; future recommendation from preview or schedule where end>now; actual committed parts where start<=now (current visit clipped to now and train.distance_km); transparent wide hit target; marker at(now,current distance). Current-time dashed line and NOW label. Other trains opacity0.22 when selected. Colour semantics: any upcoming conflict first, then delay>=300, delay>=60, then express/passenger/freight. Future selected train emphasized. Colours are replace able; meanings must remain distinguish able.

Conflict markers come from **current state.conflicts** even in preview; position midpoint of block or station.distance_km, x at conflict.start_time; native SVG title=description. Thus preview is candidate schedule overlay, not complete recomputed snapshot. Graph hover uses current train ETA/delay, not preview ETA.

Inspector Original ETA=last baseline visit.end; Recommended ETA=last preview or applied visit.end. Delay impact=current applied train.delay_seconds/60, Upcoming conflicts=current train list, Affected services=option.affected_train_count or0. Preserve/document the mixed applied-vs-preview semantics; do not silently claim all numbers describe proposed plan. No Before/After tabs on this page; comparison is graph layers + ETA fields/preview dropdown.

Drawer: train ID,status,type,service_number; priority, translated origin/destination, current block or holding point, position,current/allowed speed, projected delay,next station ID+ETA,final arrival, energy proxy, current recommendation, each upcoming conflict or empty note. Energy proxy=remaining corridor distance×1.5 arbitrary units. Drawer displays live schedule even with preview open.

# OUTPUT

Verified alternatives with distinct objectives, a select able overlay and applied live schedule. Scheduler formulas, limitations and apply validation in API_CONTRACT. Algorithms produce results from data; screenshots are observations, not replacement constants.

# SOURCE FILES / REQUIRED DEPENDENCIES

Bundle Dispatch.tsx, shared Diagram/TrainDrawer/Badge/PageTitle, clock/label/i18n/types, host state/act/select/notify. Backend api replan/apply, simulator, scheduler, conflicts, models, quality, history; ato/ingestion needed by tick/Quality. See provenance for source lines. Optional CSS `.dispatch-filters`, `.plan-layout`, `.diagram`, `.chart-toolbar`, `.callout`, `.drawer`.

# ACCEPTANCE CHECKLIST

Six tabs, three ranges, preview/applied distinct; pan/zoom bounds; graph selection+hover; original/actual/proposed layers; conflicts; correct inspector source semantics; all drawer fields; real generate/apply with stale/occupied checks; busy/errors; no schedule change on preview; shared QI/history update after apply.
