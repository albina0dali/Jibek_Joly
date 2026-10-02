# PAGE PURPOSE

`/yard`, YardBrain in original resource-pages.tsx. Group120wagons into destination-consistent consists, reserve formation tracks and shunters, compare baseline vs calculated plan. Separate static synthetic scenario, not an event-driven physical marshalling simulation. No manual wagon edits, filtering dropdowns, cargo compatibility exclusions, fleet assignment page, main-corridor train creation or wagon lifecycle status fields exist here.

# USER FLOW

Mount loads YardState → inspect baseline12consists and inventory → optimize2s → compare metrics/before-after plans → select consist from table/SVG or select wagon to find its consist → move projected-time slider → inspect constraints/cargo/deadline → apply resource plan → applied badge/button disabled. Route remount preserves backend result/applied, resets local frame6000,modeafter,selection.

# VISIBLE BLOCKS

1. RESOURCE INTELLIGENCE / WAGONS, H1 Yard Brain (RU Вагоны и составы), description; Optimize wagon formation. While busy spinner + Solving resource constraints…; errors inline role=alert.
2. SIMULATED / DERIVED badge and seed42 synthetic provenance. Empty/loading until GET resolves.
3. Four side-by-side metrics: Formed trains(trains), Wagon waiting(wagon-hours), Late wagon time(min), Mean train fill(%). Before→after arrow when result exists, before muted; lower preferred except fill. UI numbers one decimal, solver waiting metrics2 decimals internally.
4. Left-upper Aksai formation yard panel: track/shunter reservation subtitle, Before optimization/After optimization tabs; inline four-track SVG; Projected yard state slider+clock.
5. Left-lower Formation and departure sequence table. Subtitle120wagons·Ntrains. Columns Consist,Destination,Wagons,Track/shunter,Formation(start–end HH:mm),Departure(HH:mm),Length/mass(m/t). All plan rows, no page/filter. Selected row highlighting.
6. Right-upper Consist inspector: selected ID/destination; wagon count,length vs assigned-track/train limit,mass vs global train limit,shunter,departure HH:mm:ss; wagon IDs with native title cargo/mass/deadline; same-destination explanation.
7. Right-lower Algorithm and measurable effect: description bin packing + interval scheduling; when result, slotsfreed,wagon hours saved2decimals, engine,time_ms, proof note120 assigned once/zero overlaps; Apply resource plan or Applied to resource simulator(disabled). Before solve explanatory text only.
8. Full-width Wagon inventory: all120 buttons showingID,destination,mass; cargo-styled classes; title destination,cargo,arrival→deadline. Click selects its consist, not wagon detail modal.

# INTERACTIONS / LOCAL STATE

`mode='after'` initially but fallback baseline until result. Before tab always enabled; After disabled when no result. Mode affects SVG/table/inspector/inventory mapping only: KPI comparison always shows result if present even on Before tab. Solver call **does not reset mode**; if user chose Before earlier, it stays Before after newsolve. selected=null → plan[0]; unknown/stale selected ID also falls back plan[0]. Selected consist can be absent from current timeline; inspector/table still show its full plan.

Calculate POST `/api/resources/yard/optimize` body `{train_id:'F103',runtime_seconds:2}`; train_id is shared-hook legacy and ignored foryard. Set busy/error; response fullstate; failures keep prior data/result and showalert. GET onmount/session change only, no WS/poll foryard. Repeatedmount can issue twice under StrictMode, harmlessGET. Appliedmanager results reset backend but a mountedYard does not subscribe toreset; freshGET or remount needed.

SVG active consist defined `formation_start<=frame<departure`, so it stays visible during clearance after assembly. Track ready when `frame>=available_time`; otherwise Existing occupation until. SVG initial frame6000(09:40), slider minreference2400 max=max(reference+7200,all departures). onChange onlyframe. Clicking active SVG consist or Enter selectsID. Each wagon is a generic rectangle; no per wagon click/title there. Header text **hardcoded S7 / Aksai Yard**, junction geometry exactly four tracks; future dataset remap must update this explicitly. No geospatial coords or train animation timer.

Table click selects consist. Inventory click finds current mode plan containing wagon, sets selected ID. Hover browser-native title shows cargo/deadline; not custom pop over. Apply POST{plan_id,option_id:undefined omitted}; manager verifiesversion and validates after plan; sets applied field+audit action. UI disables busy/current applied; no traffic timetable mutation. Newsolve cancreate another plan; no production reservation persistence/dispatch integration.

# INPUT DATA: EXACT FIELDS

`data/resource_scenarios.json` has seed42,provenance,yard (other original sections excluded from bundle).

Wagon: `id`W001..W120, `destination`S3/S4/S5/S8, `cargo`grain/containers/ore, `priority`1..3, `length_m`15..24, `mass_t`45..85, `arrival_time`seconds2400..4440, `deadline`arrival+50/70/95min. No origin,type/status/loading/readiness boolean. Cargo affects inventory colour/title; solver groups by destination, uses priority onlytardinesscost. Does not enforcehazmat/cargo compatibility rules.

Yard: `station_id = S7`, `reference_time = 2400`, 120 wagons, 4 tracks, 2 shunters; `max_train_length_m = 620`, `max_train_mass_t = 1800`, `formation_setup_minutes = 8`, `formation_minutes_per_wagon = 1`, `departure_clearance_minutes = 4`.

Tracks: YT1 620 m ready at 2400; YT2 520 m ready at 3120; YT3 720 m ready at 3480; YT4 450 m ready at 4500. Each track has `max_mass_t = 2000`. Shunters: SH01 ready at 2400; SH02 ready at 3120. `available_time` encodes prior occupation, not an explicit list of occupation intervals.

Consist output: idYT-xx,destination,wagon_ids[],length_m,mass_t,length_limit_m,track_id,shunter_id,formation_start,formation_end,departure. CP candidate IDs tied to candidate slot index can have gaps; don'tassume sequential IDs. No explicit consist status; projectedformation/clearance/absent derived from frame. Full response has baseline/baseline_metrics/result/applied/version, notanindependent persisted consists.json dataset.

# GROUPING / FORMATION / OPTIMIZATION

Baseline: sort wagons by arrival and ID, group by destination, split into batches of 10. Sort batches by maximum arrival time and destination. Choose the earliest feasible track/shunter pair using `max(latest wagon arrival, track readiness, shunter readiness)`; break ties by track ID, then shunter ID. Total length and mass must fit both the assigned track and global train limit. Assembly ends at `start + (8 + wagon_count) × 60`; departure is four minutes later. Reserve the track until departure and the shunter until assembly ends. Update readiness for the next batch. With 30 wagons per destination this produces 12 trains.

Compare feasible batching candidates with batch sizes 8/10/12/15/20 and retain the smallest independently computed objective. CP-SAT builds `ceil(destination wagon count / 8)` candidate slots per destination (four here). Each wagon must be assigned once. Used slots must be nonempty; all assigned wagons and resources must be ready. Length and mass must satisfy both global and assigned-track limits. Optional track `[start, departure]` and shunter `[start, assembly_end]` intervals have NoOverlap constraints. Each used train gets exactly one track and one shunter. Baseline supplies solver hints.

CP variables use minutes relative to 2400, with floor conversion for arrivals, deadlines and readiness; the current data is aligned to minutes. Start horizon is 360 minutes, assembly end 400, departure 410. These bounds belong to this synthetic scenario. Deadlines are soft cost penalties, not hard latest-departure constraints.

Objective: `1400 × number_of_trains + Σwagons(floor((departure-arrival)/60) + 4 × priority × max(0,floor((departure-deadline)/60)))`.

CP uses a two-second limit, one worker and seed 42. Choose a feasible/optimal CP candidate only if its independently measured objective is no worse than the best batching plan; otherwise retain deterministic batching. Engine identifies the chosen method. The captured improvement from 12 to 8 trains does not certify a global optimum; a batching fallback can win. No LLM supplies these results.

Independent validation checks nonempty groups with one destination, exact length/mass sums and limits, arrival/readiness, minimum assembly duration and departure clearance, every wagon assigned exactly once, and no track or shunter overlaps. It uses Python assertions. Applying validates again and checks the plan version. Reset increments the version and clears result/applied state. Planning state is in memory; audit actions are in SQLite.

# COMPUTED VALUES

`train_count = len(plan)`; `wagon_count = sum(member_count)`.

`wagon_hours = Σ max(0, departure-arrival)/3600`, rounded to two decimals.

`late_wagon_minutes = Σ max(0, departure-deadline)/60`, rounded to one decimal. This metric is unweighted; the objective separately applies priority.

`mean_fill_percent = mean(length_m/length_limit_m × 100)`, rounded to one decimal. It measures length fill against assigned track/global length limit, not mass fill.

`slots_freed = before.train_count - after.train_count`; `wagon_hours_saved = round(before.wagon_hours - after.wagon_hours, 2)`. These logical departure slots are not independently allocated corridor paths.

Seed 42 baseline: 12 trains, 120.48 wagon-hours, 997.0 late wagon-minutes, 33.3% length fill. Captured result: 8 trains, 114.48 wagon-hours, 692.0 late wagon-minutes, 53.7% fill; 4 slots and 6.00 wagon-hours saved. `data/captured/yard_optimized.json` contains the exact observed plan. Runtime and CP incumbent can vary across hardware. Do not replace the algorithm with these example values.

# OUTPUT / SOURCE FILES / REQUIRED DEPENDENCIES

Verified resource assignment plan,baselinevsresultmetrics,per consist composition/reservations,select able projected yard view and persistent until reset applymark. Source YardBrain.tsx(includes useResource/CalculateButton/CompareMetric/YardSchematic),resource-types,sharedPanel/Badge/PageTitle/services/i18n. Backend yard.py originalfullalgorithm; yard-onlyresourcesadapter+api;datafile. Sidebar station display isn'tdynamicallylookeduphere; retain original station data separatelyforfutureremap.

# ACCEPTANCE CHECKLIST

120uniqueIDs/allfields;4tracks/2shunters/readiness/limits;baseline12;real optimization and engine;computed before after formulas;mode affects plan but not KPI;alltablecolumns;selection table/SVG/Enter/inventory;timeline bounds/active half open interval;native cargo/deadlinetitles;applied flag/log/stale validation;does not create corridor trains;noinventedwagonfilters/status fields.
