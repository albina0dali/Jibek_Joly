# Data inventory

All source railway datasets are synthetic seed42. No official KTZ dataset, coordinates, live railway telemetry or external feed. No existing source data deleted/changed.

| File | Original count | Fields | Usage |
|---|---|---|---|
| blocks.json | 14 | id, from_station, to_station, start_km, end_km, distance_km, track_type, direction ality, speed_limit_kmh, capacity, status | 14 directional resource blocks/topology/conflicts/energy limits |
| incidents.json | 2 | type, location_id, duration | 2 example incident templates, not automatic runtime incidents |
| metadata.json | 5 | seed, fictional, simulation_start, timezone, epoch | seed,fictional flag,epoch/timezone/start; scenario provenance |
| resource_scenarios.json | 5 | seed, provenance, yard, fleet, maintenance | yard120wagons/4tracks/2shunters; subset seed/provenance/yard only |
| schedule.json | 336 | train_id, resource, kind, start, end, from_km, to_km, direction, lane | 336 original feasible Visit intervals; Simulator baseline/schedule |
| signals.json | 28 | id, block_id, direction, status, last_update | 28 signal descriptors; live red/green/unavailable derived |
| speed_limits.json | 14 | block_id, speed_limit_kmh | 14 related reference limits; runtime reads blocks.speed_limit_kmh |
| stations.json | 8 | id, name, distance_km, platform_count, siding_available | all station axes/topology/names, model and capacity |
| timetable.json | 112 | train_id, station_id, scheduled_arrival, scheduled_departure, minimum_dwell_seconds | 112 station visit timetable entries, related reference artifact; not separately loaded by Simulator |
| trains.json | 16 | id, service_number, type, priority, origin, destination, length_m, max_speed_kmh, scheduled_departure, scheduled_arrival, planned_stops, direction | 16 services priorities/types/origins/destinations/stops/scheduled times |

## Dynamic entities and sources

- Main route sequences: derived from schedule.json grouped train_id and sorted start; no routes.json. Planned timetable rows are distinct from interpolated movement.
- Movements: Simulator.states interpolation plus snapshot time; no external movements feed.
- Incidents and conflicts: injected/derived in memory, copied into SQLite snapshot; templates file does not initialize active incidents.
- History/events: HistoryStore runtime SQLite; captured62initial snapshots (61 warm-up + any live ticks) and indexes/actions in data/captured. Simulator EventBus events are not all SQL audit rows.
- Reports: generated current Snapshot, quality components, history index andlast12actions; examples captured actual CSV/PDF, not cannedresponse.
- Yard consists: algorithm output in result.before/after, not static consists dataset. Yard shunters are independent resource IDs SH01/SH02; not main locomotive fleet L01..L08.
- Quality inputs: same Snapshot trains(delay priority/status/speed),conflicts,settings weights,mean ATO energy saving; formula spec separate.
- Config: source Settings defaults + SQLite configuration persisted viaAPI; no frontend language affects numeric formula.

Original resource_scenarios.json also has8fleetlocomotives/12jobs and3sensorhistories/3maintenancepoints, **not consumed by these three pages**, excludedfromportabledataandalgorithms; originalfileunmodified. Its originalSHA256 in inventory enables provenance; existing original data remain available if future scope explicitly expands.

## Units and joins

IDs case-sensitive; stationsS1..S8,blocksB01..B14,trainsE/P/F IDs,wagonsW001..W120,tracksYT1..YT4,consistsYT-xx,shuntersSH01/SH02. Join Visits.resource to Station or Block basedkind; trains origin/destination/planned_stop IDs; timetable.station_id; signal.block_id; yardstation_id/destinations. Alltimes secondsrelative08:00, distanceskm,lengthsm,massesmetrictons,speedkm/h,delay seconds except UI min. Source metadata epoch frozen; noUTCtimestampformatimplicitlyinferred.

Schema details: source models.py/types.ts/resource-types.ts and data/captured fullresponses. No wagon status,consist status,lat/lon,train locomotive_id,production railway location mapping. Coordinates must remain null until real input exists.
