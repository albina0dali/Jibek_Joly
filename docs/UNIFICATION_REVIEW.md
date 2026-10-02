# Final unification review

The existing shell, Worker/D1 architecture, local startup, core six-train simulation and three React extension pages are preserved. No commit, push or deployment is included.

Nine visible station identities form one vocabulary. The operational dataset uses eight, omitting the intermediate Ақкөл stop while retaining both endpoints and the Алматы-1 simulated formation hub. See [station mapping](STATION_MAPPING.md). All joins are rebased in the data; names are not just frontend substitutions. The 164 km scale is **Synthetic operational corridor distance**, not real geography. The original handoff remains unchanged (112 checksums).

All user-facing network scores use [one movement model](MOVEMENT_INDEX.md), with weights 30/20/20/20/10. Paused incident/recovery calculation: 91.1 → 74.0 → 91.1. The internal legacy score remains for compatibility. Core and extension retain different train populations and simulation states, so their live index values need not coincide.

`#plan` is «Диспетчерская» (six policy alternatives); `#movement-plan` is «План движения» (sixteen services and resource scheduling). `#history` is «Записи поездок» (full core journeys); `#history-reports` is «История и отчёты» (recent operational replay and live exports). All routes remain available. Yard shows Алматы-1 and SIMULATED YARD OPERATIONS; 120 wagons, four tracks and two shunters are retained.

Files changed for this pass:

- Data and identities: all JSON files in `data/extensions/operations/`, `web/station-registry.json`, `web/corridor-engine.js`, `scripts/build-station-registry.mjs`, `scripts/rebase-extension.mjs`.
- Shared index and UI: `web/movement-index-model.json`, `web/movement-index.js`, `web/quality.js`, `web/planning.js`, `web/app.js`, `web/advanced-ui.js`, `web/locales/ru.json`, `web/locales/kk.json`.
- Extension presentation: `web/extension/host.tsx`, `Dispatch.tsx`, `YardBrain.tsx`, `shared/components.tsx`, `shared/i18n.tsx`, `shared/locales/catalog.json`, `web/extension.css`.
- Service and reports: `server/index.js`, `server/extension-proxy.js`, `server/extension-paths.js`, `server/extension/app/quality.py`, `simulator.py`, `reports.py`.
- Validation and documentation: `tests/extension-adapters.test.mjs`, `tests/movement-index-vectors.json`, `tests/test_extension.py`, `tests/extension-browser.mjs`, `README.md`, `docs/STATION_MAPPING.md`, `docs/MOVEMENT_INDEX.md`, this review and the integration file manifest.

Validation: build, syntax check, 20 JavaScript tests plus Worker/D1/API/SSE suite, six Python tests, and Playwright. Browser coverage includes all 13 routes in RU/KK and dark/light, shared computed styles, station names, readable translations, incident/recovery, Preview/Apply, Replay, CSV/PDF and yard constraints. All three extension pages are checked at 390 px. Screenshots and exported reports are in `.jol-local/review/`.

## Exact local demo steps

1. Run `npm start`, then open `http://localhost:8787/#map`. Inspect the nine-station corridor and initial calculated index (about 90.7). Open «Аналитика» and «Диспетчерская» to compare the same index factors and existing forecast functionality.
2. Open «План движения», click «Сбросить демо». Reset pauses the operational simulation at 08:40. Baseline index is about 91.1; station names run Көкшетау → Алматы-2. The diagram and factor table show the synthetic 164 km scale and actual model inputs.
3. Click «Демо-сбой: F103 +10 мин». Index drops to about 74.0; delay and resource conflict markers appear. Wait for calculation to finish.
4. Click «Рассчитать варианты» if needed, wait until complete, then choose an alternative in «Просмотр плана». Inspect trajectories and F103 in the service selector. Preview leaves LIVE unchanged. Click «Применить в симуляторе» in the inspector; the calculated index returns to about 91.1 and conflicts clear.
5. Open «История и отчёты»: choose «Последние 15 мин», move the scrubber, inspect a train, start/pause replay, then «Вернуться в эфир». Export CSV/PDF. Exports always contain current LIVE traffic, even while replay is selected; both contain the canonical station vocabulary and current movement index.
6. Open «Вагоны и составы»: inspect the Алматы-1 simulated yard, 120 wagons, four tracks and two shunters. Click «Оптимизировать формирование», compare «До/после», inspect inventory and the timeline, then apply the resource plan. The feasible example reduces 12 consists to eight and wagon waiting from 120.48 to 114.48 wagon-hours. Traffic schedule remains unchanged.
7. Toggle RU/KZ and dark/light in the common header. Open «Записи поездок» to confirm full core journey history remains distinct from operational replay. Check the three extension pages at a narrow mobile width.

Keep the simulation paused for reproducible index comparisons. If time advances, live values are recalculated and can differ.
