# 1. ORIGINAL CASE COMPLIANCE

Аудит: 2026-10-02. Основание — переданные пользователем условия, а не независимо полученный официальный документ. [Таблица до redesign](CASE_ACCEPTANCE_AUDIT.md). Статусы ниже относятся к **локальному демонстрационному прототипу**.

| Requirement | Status | Evidence | Remaining gap |
|---|---|---|---|
| Realtime trains/signals/switches/timetable | ✅ ВЫПОЛНЕНО для simulated data | Worker telemetry envelope → SSE → world → paint; доступная кнопка на «Данные и API»; `tests/server.mjs`, `tests/operations-ui-review.mjs` | Default map — local model; Python — polling 1 s; реальные КТЖ источники отсутствуют |
| Reconnect / connection / last update / clock | ✅ ВЫПОЛНЕНО | Прерывание state fetch и SSE → статус reconnect → восстановление; Python timestamp в tooltip, clock из state | Last update не является доказательством latency SLA |
| Dispatch conflicts / feasible alternatives / priorities / occupancy / validation | ✅ ВЫПОЛНЕНО в demo scope | Python CP-SAT + independently validated fallback, три альтернативы; Core шесть policies; JS/Python/browser suites | Конечное demo расписание; нет доказательства глобального оптимума и промышленной поддержки обгонов |
| Автоведение | ✅ ВЫПОЛНЕНО как advisory prototype | `eco-ui.js`, `journey.js`, `eco-api.js`, `ato.py`: speed/profile/limits/ETA/proxy, связь с модельными ограничениями | Не управление локомотивом; мгновенное изменение скорости, некалиброванная энергия |
| Shared Movement Index | ✅ ВЫПОЛНЕНО | Общая спецификация и five-factor weights 30/20/20/20/10; vectors; F103 91.1 → 74.0 → 91.1 | Две популяции поездов дают разные значения одной формулы |
| Incident → analysis → alternatives → Preview → Apply → recovery | ✅ ВЫПОЛНЕНО внутри Python model | UI incident F103, автоматический расчёт, Preview unchanged schedule, Apply changed revision/schedule, calculated recovery | Core incident не передаётся в Python |
| 3D ↔ 2D same world, 9 stations, occupancy, selection/time | ✅ ВЫПОЛНЕНО | `tests/operations-map.mjs`, nine canonical identities / six Core trains | Учебная геометрия и расстояния |
| One state for map + Python graph + Preview/Replay | 🟡 ЧАСТИЧНО | Core map/Диспетчерская и Python graph/history работают по отдельности | Python Preview/Replay не отображается в Core map; это не исправлено косметикой |
| Snapshot Replay / scrub / return Live / read-only | ✅ ВЫПОЛНЕНО | Реальные history snapshots; browser checks live isolation; event log фильтруется по периоду и моменту Replay | LIVE KPI намеренно остаётся отдельно от recorded index |
| CSV/PDF downloaded, IDs/index/time | ✅ ВЫПОЛНЕНО для LIVE | Реальные downloads: 16 train rows, 8 station rows; CSV summary index/time; PDF bytes/IDs/index/font checked | Replay export использует LIVE; yard отсутствует в отчётах |
| Worker/D1/Python/OR-Tools/storage/OpenAPI/health | ✅ ВЫПОЛНЕНО для demo | Actual Worker/D1/API tests; SQLite history; health 200; module separation | Production deployment / HA / scaling не подтверждены |
| UI <500 ms / end-to-end replan ≤5 s | ⚫ НЕВОЗМОЖНО ПОДТВЕРДИТЬ | SSE test: три пакета за ~2.06 s (1 Hz); solver runtime budget существует | **NOT MEASURED** для end-to-end targets; cadence/budget не SLA |
| Burst/load behavior | ⚫ НЕВОЗМОЖНО ПОДТВЕРДИТЬ | Locks/revision validation/error states существуют | **NOT MEASURED**, stress/load benchmark отсутствует |
| Full single map incident → Python Apply → same map recovery demo | 🟡 ЧАСТИЧНО | Два UI-flow работают без редактирования данных или кода | Требуется отдельный F103 incident в Python model |
| A. UI / UX | ✅ ВЫПОЛНЕНО в prototype scope | Compact UI, hierarchy, semantic alerts, focus styles, 13 pages / 2 locales / 2 themes / 3 widths, before/after evidence | Нет формальной WCAG-сертификации; 3D labels могут перекрываться |
| B. Dispatch / Advisory / Realtime | 🟡 ЧАСТИЧНО | Проверенные вычисления и simulated telemetry | Нет общего cross-model runtime и field validation |
| C. Backend Architecture | ✅ ВЫПОЛНЕНО для demo | Модульность, storage, independent checks, yard isolation | Scalability и production hardening не доказаны |
| D. Demo / Engineering Culture | 🟡 ЧАСТИЧНО | README, reproducible dataset, tests, logs, exports, audit evidence | Сквозной single-state demo и performance benchmark отсутствуют |

# 2. WHAT WAS ALREADY COMPLETE

Canonical registry: девять станций, Python subset восемь. Единая формула индекса; реальные модели движения, ограничения ресурсов, альтернативы и independent validation; working Preview/Apply/Replay/export. Worker/D1 и Python/SQLite, CP-SAT/validated fallback. Изоляция yard. RU/KK и темы. Они сохранены.

# 3. WHAT WAS PARTIAL

Realtime chain имел SSE endpoint и handler, но без доступной кнопки подключения. Не хватало видимых connection/source metadata. Сквозная карта → Python план → карта не имела общего runtime. Advisory и энергия — модельные, а не физически валидированные. UX имел большой gauge, длинные панели, sidebar без групп.

# 4. WHAT WAS MISSING

Отдельные строки общего индекса и времени в CSV; доступный UI control для SSE; фильтрация action log по выбранному Replay period. Нет данных КТЖ, подтверждённых latency/load результатов, production deployment или единого состояния между моделями. Последние пункты требуют отдельной работы и не заявлены выполненными.

# 5. WHAT I FIXED

Название «Автоведение» и KK «Жылдамдық профилі»; grouped nav; compact shell, KPI strip, numeric index/status, incident severity/location/approaching count/reserve availability; source/connection/UUID или revision; last update tooltip; stale state/retry. SSE controls используют существующие handlers/API. Preview выделен синим; показаны calculated option effects, повторный Apply блокируется при busy. Исторические события ограничены периодом; исправлено отображение нулевого времени. Inventory ограничен внутренним scroll и фильтром назначения. CSV содержит индекс и simulation timestamp. Сценарии показывают сравнение delay/queue/delayed trains/index/conflicts/forecast restriction clearance.

# 6. UI/UX PROBLEMS FOUND

На 1366×768 карта начиналась около y=622; крупные KPI/source/transport отодвигали основной workspace. Sidebar скрывал нижние routes за scroll, отсутствовала группировка. Gauge 174px занимал лишнее место. Крупные красные summary areas выглядели как ошибка системы. Инвентарь 120 вагонов удлинял страницу. План Диспетчерской начинался графиком, заголовок и расчёт находились ниже. В light theme инструкция canvas имела размытую тень, muted text/background contrast составлял ~4.43:1.

# 7. DESIGN SYSTEM CHANGES

Переопределения в одном `web/operations-ui.css`: 8/16px основной ритм, 24px H1, 12–13px основной dense UI, 10–11px metadata, 4px corner radius, компактные таблицы и panels. Teal normal/success; blue selection/planned/Preview; amber attention; red critical; gray history/secondary. Статусы дублируются текстом. Убраны gradient hero и glowing status dot; gauge отображается компактным числом. Light muted/body-background contrast после исправления ~5.20:1; это проверка пары токенов, не всей доступности. Сохранены focus-visible и reduced-motion handling.

# 8. NAVIGATION CHANGES

13 маршрутов сохранены. Операции: карта, Диспетчерская, План движения, Сценарии, Управлять движением. Интеллект/анализ: Автоведение, Вагоны и составы, Аналитика, Причины задержек. История: История и отчёты, Записи поездок. Система: Данные и API, Как это работает. Отдельного пункта 2D нет. RU/KK переключаются общей настройкой; английского раздела приложения нет.

# 9. PAGE CHANGES

- **Оперативная карта:** KPI, действия и режимы 3D/2D выше; canvas около y=423 на laptop в light view. Renderer/engine не изменены. Alerts содержат реальное число поездов на подходе, а не выдуманный affected count.
- **Сценарии:** compact incident; before/managed comparison metrics над двумя views. Clearance — прогноз окончания ограничения, а не обещание восстановления индекса.
- **Диспетчерская:** section title и кнопка пересчёта перенесены перед графиками; фактическая поездограмма, forecast policies, validation и Apply сохранены.
- **План движения:** dense split graph/inspector; blue Preview vs applied; actual impact metrics, blocked busy Apply, demo incident/reset остаются доступны.
- **Автоведение:** правильное название и subtitle; speed/advice/limit/ETA/energy proxy сохранены, typography и source controls компактнее.
- **История и отчёты:** период/Replay/return Live и export note явны; журнал фильтруется; bounded event scroll; реальный CSV summary index/time.
- **Вагоны и составы:** компактные before/after metrics, layout, inspector; 120 wagon buttons сохранены, search + destination filter + bounded scroll. Yard Apply остаётся изолированным.
- **Аналитика:** общий calculated KPI strip, compact numeric factor summary, dense charts/tables. Значения punctuality/delay/capacity/energy не подменены.

# 10. FILES CHANGED

Именно в этой работе, без перечисления предыдущей унификации:

1. `README.md`
2. `package.json`
3. `web/app.js`
4. `web/advanced-ui.js`
5. `web/index.html`
6. `web/operations-ui.css` — новый
7. `web/locales/ru.json`
8. `web/locales/kk.json`
9. `web/extension/host.tsx`
10. `web/extension/Dispatch.tsx`
11. `web/extension/History.tsx`
12. `web/extension/YardBrain.tsx`
13. `web/extension/shared/i18n.tsx`
14. `server/extension/app/reports.py`
15. `tests/extension-browser.mjs`
16. `tests/operations-ui-review.mjs` — новый
17. `docs/CASE_ACCEPTANCE_AUDIT.md` — новый
18. `docs/FINAL_UI_UX_REVIEW.md` — новый
19. `docs/OPERATIONS_MAP.md`
20. `docs/INTEGRATION_FILES.json`

Generated artifacts: `web/vendor/extension.bundle.js`, `server/assets.generated.json`, `dist/`. Local review scripts, screenshots, JSON evidence, reports, runtime SQLite и Python caches находятся в ignored directories. Случайно регенерированный tripId `web/demo-trip.json` восстановлен; исходные данные не изменены. Коммиты/push не выполнялись.

# 11. TEST RESULTS

| Command | Result |
|---|---|
| `npm run build` (также сборка внутри последнего `npm start`) | PASS |
| `npm run check` | PASS |
| `npm test` | PASS: 20 JavaScript tests + Worker/D1/API/storage/SSE/OpenAPI |
| `npm run test:extension` | PASS: 6 Python tests; 91.1 → 74.0 → 91.1; yard 12 → 8 |
| `npm run test:map` | PASS: names, canonical stations, shared state, signal/selection/theme/mobile |
| `npm run test:browser` | PASS: actual Preview/Apply/Replay/downloads/yard; all 13 routes, RU/KK, light/dark; no JS/HTTP errors |
| `npm run test:ui` | PASS: Core index reduction, Python fetch reconnect, SSE stream reconnect, health 200, 16 laptop screenshots |
| `node .jol-local/ui-review/capture.mjs before/after` | PASS: 39 captures each; no document overflow or JS errors |
| `py -3.12 .jol-local/ui-review/verify-protected.py` | PASS: pre-redesign SHA-256 for datasets and protected model files |
| `py -3.12 integration_handoff_bundle/tooling/check_integrity.py integration_handoff_bundle` | PASS: 112 preserved files |

Browser nav test был уточнён с prefix `#history` до exact route, чтобы не выбирать `#history-reports` после группировки; assertions сохранены, CSV assertions усилены. Проверки styles ожидают active route и видимый H1; Yard Apply ожидает подтверждение API, а не только временный busy/disabled state кнопки. Временные ошибки selector/недоступной SSE-кнопки и гонки ожиданий устранены; финальные проверки повторены и прошли.

# 12. DEMO READINESS

**Внутримодельные demo — готовы**, без правки кода или данных: map → 3D/2D → core incident → actual degradation; отдельно План движения → Reset → Pause → F103 incident → automatic alternatives → Preview → Generate при необходимости → Apply → calculated recovery → History Replay → CSV/PDF → Yard Optimize/Apply → return map с сохранённой Core-моделью. Автоведение показывает Core advisory; это не рекомендации для F103. **Единый single-incident cross-model flow не готов.**

# 13. SAFE TO CLAIM

Демонстрационный railway operations prototype с canonical station vocabulary; одна спецификация индекса; actual scheduling/validation, simulated realtime, advice and energy proxy, read-only Replay, real reports and isolated yard optimization. Подтверждённые screenshots и тесты RU/KK/themes/widths. SSE 1 Hz измерен тестом telemetry cadence.

# 14. DO NOT CLAIM

Подключение к КТЖ, промышленная эксплуатация, локомотивное управление, физически точная экономия топлива, proven global optimum/network-wide dispatching, единый runtime всех страниц, cross-model map recovery, UI latency SLA <500ms, guaranteed replanning ≤5s, production scalability или WCAG certification.

# 15. REMAINING LIMITATIONS

Core 9 stations/6 trains и Python 8/16 — отдельные states. Synthetic distances не являются географическими. CSV/PDF Replay экспортируют LIVE; yard inventory не экспортируется. Python single-worker demo lifecycle отличается от D1. Replan budget и UI cadence не performance guarantee. 3D station/train labels могут перекрываться; 2D является более читаемым operational view. Forecast clearance и end-of-affected-trains time не measured recovery SLA. Имитация стрелок — reserve-route state, а не аппаратная interlocking модель. SSE-поток в текущем UI доступен для просмотра; production authentication/control integration отдельно не выполнена.

# 16. BEFORE/AFTER SCREENSHOTS

- `.jol-local/ui-review/before/`: 39 viewport PNG, все 13 страниц × 1920×1080 / 1366×768 / 390×844.
- `.jol-local/ui-review/after/`: matching 39 PNG плюс четыре key pages × RU/KK × dark/light на 1366×768, `map-incident-2d-1366.png`, `scenario-impact-1366.png`.
- Сопоставление: `map-1366.png`, `scenario-1366.png`, `movement-plan-1366.png`, `wagons-consists-1366.png` в before/after.
- `.jol-local/review/`: `movement-applied.png`, `history-replay.png`, `yard-applied.png`, реальные `report.csv`, `report.pdf`.
- Evidence JSON: `before/checks.json`, `after/checks.json`, `ui-checks.json`, `protected-checks.json`, `.jol-local/review/browser-results.json`.
