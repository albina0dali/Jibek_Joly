# Unified demo network

Nine canonical team stations; the extension uses eight in corridor order. Ақкөл remains in the team model; the operational model collapses this intermediate stop to preserve both endpoints and the Алматы-1 formation hub. This is an explicit synthetic-demo rebase.

| Old ID | Reference name | Canonical ID | Unified name | Synthetic km |
|---|---|---|---|---|
| S1 | Arqa Junction | team-station-0 | Көкшетау | 0 |
| S2 | Sarybel | team-station-1 | Бурабай | 18 |
| S3 | Kumyr | team-station-3 | Астана | 43 |
| S4 | Terek | team-station-4 | Қарағанды | 61 |
| S5 | Bastau | team-station-5 | Мойынты | 89 |
| S6 | Zhalyn | team-station-6 | Шу | 112 |
| S7 | Aksai Yard | team-station-7 | Алматы-1 | 138 |
| S8 | Dala Terminal | team-station-8 | Алматы-2 | 164 |

**Synthetic operational corridor distance**: 164 km. Chainage, times, capacities and yard equipment are normalized simulation inputs, not real geography or station properties. Geographic coordinates remain null; team x/z are scene positions. Алматы-1 hosts SIMULATED YARD OPERATIONS only.

Run `node scripts/build-station-registry.mjs` to reproduce the registry and rebased dataset from the untouched handoff. All station joins in trains, blocks, schedule, timetable and resource scenarios use canonical IDs, including API state, history, planning and reports. Train/block/signal IDs and 16 trains, 120 wagons, four tracks and two shunters are preserved. S1–S8 remain only in provenance and raw handoff.
