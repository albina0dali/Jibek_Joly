# ORIGINAL CASE COMPLIANCE TABLE

Дата аудита: 2026-10-02. Оценка по условиям, переданным пользователем; независимый официальный документ и оценка жюри не предоставлены. Таблица ниже зафиксирована **до redesign**. Все данные демонстрационные, подключения к КТЖ нет.

| Requirement | Status | Evidence | Remaining gap |
|---|---|---|---|
| Realtime: поезда, сигналы, стрелки, расписание | 🟡 ЧАСТИЧНО | `server/index.js`: `/api/stream`, telemetry 1 Hz; `web/advanced-ui.js`: обработчик EventSource/reconnect; Python state polling 1 s в `web/extension/host.tsx` | Карта по умолчанию использует локальную симуляцию; SSE handler не имел доступной кнопки в UI (выявлено browser acceptance). Python использует polling, а не SSE. Last update/connection недостаточно заметны |
| Autodispatching | ✅ ВЫПОЛНЕНО в пределах demo | `server/extension/app/scheduler.py`, `conflicts.py`, `api.py`: ресурсные интервалы, приоритеты, три альтернативы, CP-SAT/validated heuristic, независимая проверка Apply; `web/planning.js`: шесть core policies | Нет гарантии глобального оптимума или промышленного управления обгонами. Оптимизируется конечное расписание 16 demo trains |
| Автоведение | 🟡 ЧАСТИЧНО | `web/eco-ui.js`, `journey.js`, `server/eco-api.js`, Python `ato.py`: current/recommended/limit/ETA, профиль, влияние плана | Консультативная модель, мгновенная скорость, энергия — proxy. Неверное название раздела |
| Единый Movement Index | ✅ ВЫПОЛНЕНО | `web/movement-index-model.json`, `movement-index.js`, Python `quality.py`; JS/Python vectors; F103 91.1 → 74.0 → 91.1 | Одинаковая формула, разные входные состояния двух симуляторов; это не один глобальный runtime |
| Incident → alternatives → Preview → Apply → recovery | ✅ ВЫПОЛНЕНО внутри Python model | `tests/test_extension.py`, `tests/extension-browser.mjs`: Preview не меняет schedule; Apply меняет revision/schedule и индекс | Incident core map не становится incident Python model |
| 3D/2D shared state, станции и occupancy | ✅ ВЫПОЛНЕНО | `web/app.js`, `dispatcher-scheme.js`, `tests/operations-map.mjs`: девять станций, шесть поездов, общий world/time/selection/actions | Геометрия учебная, расстояния не географические |
| Map + train graph + Preview/Replay одного end-to-end state | 🟡 ЧАСТИЧНО | Core map/Диспетчерская используют core world; Python graph/history используют Python snapshots | Python Preview/Replay не отображается на core 3D/2D map. Объединение runtime потребует отдельной архитектурной работы |
| Replay read-only, scrub, return Live | ✅ ВЫПОЛНЕНО | `web/journey.js`, `extension/History.tsx`, Python `history.py`; Python/browser проверка неизменности live | Экспорт из Python Replay всегда LIVE; это указано в UI |
| CSV/PDF download | 🟡 ЧАСТИЧНО до polish | `reports.py`, `History.tsx`, Python/browser tests: реальные непустые CSV/PDF, canonical IDs, компоненты индекса; PDF содержит время и итог | CSV не содержал отдельных строк итогового индекса и времени. Yard не экспортируется; snapshot export Replay отсутствует |
| Worker/D1/Python/OR-Tools/storage/API/health | ✅ ВЫПОЛНЕНО для локального прототипа | `server/index.js`, `extension-proxy.js`, `extension/main.py`, OpenAPI, D1 и SQLite, README | Production deployment, HA и масштабирование не подтверждены |
| UI <500 ms, replan ≤5 s | ⚫ НЕВОЗМОЖНО ПОДТВЕРДИТЬ | Код содержит paint cadence, SSE latency samples и ограничение solver runtime | NOT MEASURED для всей цепочки; solver budget не является гарантией end-to-end latency |
| Burst/load behavior | ⚫ НЕВОЗМОЖНО ПОДТВЕРДИТЬ | Есть replan lock/revision checks и ошибки 503 | NOT MEASURED; промышленного load test нет |
| Полное demo map incident → Python Apply → same map recovery | 🟡 ЧАСТИЧНО | Внутримодельные сценарии воспроизводимы UI без правки кода/данных | Требуется отдельный incident F103 в Плане движения; нельзя выдавать его за продолжение core map incident |
| A. UI / UX | 🟡 ЧАСТИЧНО | RU/KK, темы, SVG/3D, клавиатурные controls; BEFORE screenshots | Длинные страницы, крупный gauge, не сгруппирован sidebar, слабая плотность и источник данных |
| B. Dispatch / Advisory / Realtime | 🟡 ЧАСТИЧНО | Рабочие модели и проверки выше | Нет единого runtime всех страниц и полевой валидации |
| C. Backend Architecture | ✅ ВЫПОЛНЕНО для demo | Разделены Worker/Python/yard; реальные storage и proxy | Scalability/production readiness не измерены |
| D. Demo / Engineering Culture | 🟡 ЧАСТИЧНО | README, commands, JS/Python/browser suites, воспроизводимые данные | Один бесшовный end-to-end runtime и performance evidence отсутствуют |

## Неизменяемые границы redesign

Сохраняются datasets, canonical station mapping, пять факторов и веса, движок движения, Preview/Apply, read-only Replay, изоляция yard, API. Названия, визуальная иерархия, статус соединения, компактность и источник данных исправляются в UI. Отсутствующий единый runtime нельзя исправить косметическим переименованием.

## UI audit BEFORE

Снимки: `.jol-local/ui-review/before/`, 1920×1080, 1366×768, 390×844, все 13 маршрутов. Крупные отступы и карточки, длинный sidebar без групп, круговой gauge 174px, высокий transport/source, длинный неограниченный inventory, крупные alert areas. На laptop действия и canvas конкурируют за первый экран. Статус local/SSE/Python и время получения данных должны быть явными.
