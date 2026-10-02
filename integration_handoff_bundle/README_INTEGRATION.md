# Jibek Joly: integration handoff, только три страницы

Этот пакет описывает **реальный текущий код отдельного проекта**, не проект будущего командного сайта. Переносить только `/dispatch`, `/history`, `/yard`. Исходный проект не изменён подготовкой пакета. Сборка, исходные IDs, данные и формулы сохранены. Все железнодорожные данные вымышленные; epoch исходного сценария 2026-10-01 08:00 UTC+05. Дата аудита: 2026-10-02, Asia/Qyzylorda.

**Personal project station count: 8.** Поездов 16; не путать эти количества.

## Порядок чтения

1. `INTEGRATION_MANIFEST.json`, `ROUTES_AND_NAVIGATION.md`, `DEPENDENCIES.md`.
2. Три `page_specs/*.md` — блоки, состояния, каждое действие и вычисления.
3. `DATA_INVENTORY.md`, `data/DATA_INVENTORY.json`, `STATIONS_PERSONAL.md`.
4. `QUALITY_INDEX_SPEC.md`, `API_CONTRACT.md`, `SOURCE_PROVENANCE.md`.
5. `reference_screenshots/*.png` и соседние `.visible.json` — фактические русские подписи и состояния исходного UI. Фикстуры `data/captured/` — записанные расчёты, не подставлять их как hardcoded результаты.
6. `VALIDATION.md` и машинные отчёты проверок.

## MUST PRESERVE

Содержимое и иерархию блоков, фильтры, таблицы и поля, исходный/действующий/предлагаемый графики, выбор поезда и drawer, preview отдельно от apply, историю снимков, replay без изменения текущей симуляции, реальные CSV/PDF, формулы QI и yard, ограничения ресурсов, поля/ID/единицы datasets, асинхронные ошибки и проверки актуальности. RU/KK/EN и сохранение языка тоже входят в существующую функциональность.

## CAN BE REPLACED BY TEAM DESIGN

Цвета, background, borders, typography, radius, shadows, общие карточки и внешний вид навигации. CSS в пакете — **опциональная визуальная справка**, не требование дизайна. Можно переписать SVG/компоненты в дизайн-системе команды, сохранив смысл осей, слои графиков, данные и взаимодействия. Полный layout другого сайта сюда не придумывался.

## Самостоятельный запуск reference host

Python 3.12; Node 22+ (аудит проведён на Node 24). В двух терминалах из bundle:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r source/shared_required_only/backend/requirements.txt
Set-Location source/shared_required_only/backend
..\..\..\..\.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

```powershell
Set-Location source/shared_required_only/frontend
npm ci
npm run dev
```

Открыть http://localhost:5175/dispatch. Dispatcher / `dispatch-demo`, Admin / `admin-demo`. Навигация reference host содержит ровно три ссылки. `npm run build` создаёт production static files; production hosting требует SPA fallback и proxy `/api`, `/ws` к backend. `vite preview` сам не заменяет production reverse proxy.

Backend читает **bundle/data**, а не исходный проект. DATABASE_PATH можно направить в отдельный SQLite; иначе создаётся `data/operations.sqlite`. Node_modules, venv, dist, runtime SQLite в перенос не входят. При запуске создаётся новая 15-минутная история; сохранённые конфигурации SQLite переживают reset, но история и actions очищаются. Не копировать личные токены/сессии.

## Что адаптировано для переносимости

Бизнес-тела Dispatch, History, YardBrain, графиков/drawer извлечены AST без переписывания. Imports перенаправлены в общий обязательный слой; добавлен host только для трёх routes. Backend расчётов и отчётов сохранён; путь данных направлен в bundle/data. ResourcePlanning оставлен только для yard; fleet/maintenance страницы, алгоритмы и datasets не включены. Подробная карта оригинал → bundle в `source/*_PROVENANCE.json`.

## Критичные ограничения текущего кода

- Это прямой линейный вымышленный коридор 164 км; не географическая карта. Константы 164 есть в графиках, симуляторе и energy profile; будущая смена сети требует согласованного изменения всех мест.
- История сохраняет traffic snapshots, не снимки ресурсного yard. Replay не восстанавливает вагоны. Применение yard только помечает ресурсный план и пишет audit action; основной график поездов не меняется.
- Экспорт во время replay всё равно выгружает **текущий живой** state. В CSV/PDF нет полного yard inventory, составов или всех исторических снимков.
- Некоторые подписи/динамические пояснения Dispatch и документы CSV/PDF остаются на английском: это факт исходного кода, не требование нового дизайна. Например Generate alternatives и текст preview callout не пропущены через перевод.
- Числа времени — секунды после 08:00, без Unix timestamp и rollover суток. Не использовать часы хоста вместо scenario time.
- Снимки доступного часа хранятся в SQLite, действия — последние 100 в API; исходный reset и startup стирают history/actions. Сохранение конфигурации не равно сохранению состояния симуляции.
- Нельзя запускать Python с `-O`: yard.validate использует assert. В source сохранён исходный механизм.

Следующему Codex следует интегрировать page contracts и business services в командный shell, затем проверить чек-листы трёх page_specs и reference screenshots. Станции здесь не переименованы, не сокращены и не подогнаны под командный dataset.
