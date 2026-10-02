# Required dependency graph

## Frontend

React 19, react-dom 19, react-router-dom 7, lucide-react 0.468; build: TypeScript5.7, Vite6, @vitejs/plugin-react4. package-lock.json сохраняет реально разрешённые версии. Rollup override @rollup/wasm-node4.59 — часть текущей Windows-сборки. Playwright — tooling, не runtime. Никаких chart SDK/map API: графики, топология и вагоны — inline SVG.

```text
reference main → Dispatch → PageTitle, Diagram, Badge → clock/label/i18n
               → History → PageTitle, Network, Diagram, TrainDrawer
                         → request/download → HTTP + bearer
               → YardBrain → YardSchematic, CompareMetric, useResource
                           → Panel/Badge, clock/label, request, i18n
all pages → PageProps/Snapshot types, session, host select/act/notify
host → useLive, TrainDrawer, LanguageSwitcher
```

Shared required code в source/shared_required_only/frontend/src. Из mixed files извлечены только нужные declarations; SpeedChart, TrainTable, остальные pages и resource modules отсутствуют. TypeScript paths + Vite aliases обеспечивают пакетам React/icons resolution для page files вне frontend root. При переносе в монорепо заменить этот resolution на механизм команды.

Optional CSS: style.css + resource-style.css со снятыми selectors исключительно отсутствующих страниц; media breakpoints 1600/1300/1050/700. Оба нужны только для воспроизведения reference appearance. IBM Plex Sans/Mono via Google Fonts @import; Arial/monospace fallback. Никаких локальных изображений или sprite assets.

## Backend

FastAPI, uvicorn[standard], pydantic2, OR-Tools9, reportlab4; SQLite3 и json — Python stdlib. pytest/httpx — проверки. Полные bounds и lock frontend в package manifests.

```text
main → api → Simulator → models, scheduler, conflicts, quality,
                      → HistoryStore(SQLite), ato.profile, ingestion(EventBus)
                      → data stations/blocks/trains/schedule/signals
          → reports → reportlab, csv
          → ResourcePlanning(yard only) → yard → OR-Tools CP-SAT
                                     → data.resource_scenarios.yard
```

ATO/ingestion сохранены **без переноса их страниц**: tick использует их для energy QI и обработки simulator events. generate_demo_data сохранён для восстановления отсутствующего schedule; по умолчанию использовать сохранённые data, не регенерировать во время интеграции. Timetable/speed_limits/incident templates/metadata сохранены как связанные dataset artifacts, хотя Simulator напрямую читает только пять файлов. Resource generator для fleet/maintenance не нужен runtime Yard и не скопирован.

Один backend процесс держит mutable schedule/options/yard results и sessions в памяти. Multi worker FastAPI без внешнего shared state нарушит согласованность. SQLite доступ сериализуется sim.lock; reset получает resources.lock перед sim.lock. Асинхронные solver вызовы вынесены в thread.

Дизайн можно менять. Контракты данных, scheduler/validator, временные единицы, solver constraints и совместный lifecycle менять нельзя незаметно.
