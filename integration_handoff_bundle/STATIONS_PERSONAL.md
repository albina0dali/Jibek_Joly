# Station inventory

Personal project station count: 8

Original names and IDs unchanged. Coordinates absent; distance_km is corridor chainage. Route Arqa — Dala, fictional164km linear corridor. Not16 stations:16 is train count.

| Order | Original ID | Original display name | km | Platforms | Siding | Page dependencies |
|---|---|---|---|---|---|---|
| 1 | S1 | Arqa Junction | 0 | 2 | False | movement-plan, history-reports |
| 2 | S2 | Sarybel | 18 | 3 | True | movement-plan, history-reports |
| 3 | S3 | Kumyr | 43 | 2 | False | movement-plan, history-reports, wagons-consists |
| 4 | S4 | Terek | 61 | 3 | True | movement-plan, history-reports, wagons-consists |
| 5 | S5 | Bastau | 89 | 2 | False | movement-plan, history-reports, wagons-consists |
| 6 | S6 | Zhalyn | 112 | 2 | False | movement-plan, history-reports |
| 7 | S7 | Aksai Yard | 138 | 3 | True | movement-plan, history-reports, wagons-consists |
| 8 | S8 | Dala Terminal | 164 | 2 | False | movement-plan, history-reports, wagons-consists |

Machine inventory data/stations_personal.json preserves original station fields plus original_id/display_name/order/route/nullcoordinates/usage. Original stations.json also copied verbatim. All eight in traffic diagrams/history; S7 yard itself and S3/S4/S5/S8 wagon destinations directly needed by Yard. S1/S2/S6 are not yard destinations. Blocks refer original station endpoints (two blocks per station pair); no separate routes.json exists: routes derive from schedule visits and train direction/planned_stops.
