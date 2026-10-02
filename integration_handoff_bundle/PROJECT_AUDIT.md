# Аудит исходного проекта

Корень приложения: `autodispatcher/`, внутри workspace `Sweet/`. Исходный проект имеет Python/FastAPI backend и React/TypeScript frontend. Entry points: `backend/main.py`, `frontend/index.html` → `frontend/src/main.tsx`. Проверены исходные функции, а не только названия файлов.

## Исходные frontend-модули

| Модуль | Роль и решение для handoff |
|---|---|
| main.tsx | Routing, login, shell, session, live state, общий drawer. Сохранён адаптер с тремя маршрутами. |
| pages.tsx | Смешанный файл восьми страниц. Извлечены только Dispatch, History, PageTitle и PageProps. |
| resource-pages.tsx | Три ресурсных страницы и helpers. Извлечены только YardBrain и его helpers/SVG. |
| components.tsx | Общие SVG и UI. Нужны trainColor, Badge, Panel, Network, Diagram, TrainDrawer; TrainTable и SpeedChart исключены. |
| hooks.ts | useLive: GET/WS, reconnect, watchdog. Сохранён. |
| services.ts | clock, minutes, label, request, download. Сохранён. |
| i18n.tsx | RU/KK/EN, localStorage, подписки и динамические переводы. Сохранён. |
| types.ts | Извлечены типы Snapshot и входящих в него сущностей; Advisory/Configuration не нужны странице. |
| resource-types.ts | Извлечены только типы yard и общего результата. |
| locales/catalog.json, resources.json | Сохранены словари переводов: это данные подписей, не перенос других страниц. |
| locales/extracted.json, resource-keys.json | Служебные списки проверки локализации; не runtime, исключены. |
| style.css, resource-style.css | Reference styling; сохранены нужные/global правила, исключены правила только других страниц. |

Сборочные скрипты `frontend/scripts/localize.mjs` и `check-locales.mjs`, тесты исходного проекта, Docker/nginx и документация не импортируются страницами. Вместо их бездумного копирования добавлены отдельные проверочные tools пакета.

## Backend-модули

`api`, `models`, `simulator`, `scheduler`, `conflicts`, `quality`, `history`, `reports`, `yard` — прямые обязательные зависимости. `ato` и `ingestion` — транзитивные зависимости Simulator.tick; нужны даже без страниц advisory/analytics. `resources` ограничен yard. `fleet` и `maintenance` исключены. `generate_demo_data` нужен для fallback отсутствующего schedule и воспроизводимости baseline; сохранён. Для yard сохранён точный dataset, регенерация при запуске не нужна.

## Данные и assets

Все JSON в исходном `backend/data` проверены по структуре, полям и ссылкам. История не является готовым JSON dataset: она создаётся в SQLite. Runtime SQLite исходного пользователя не копировался. Снимки и скачанные отчёты получены из изолированной копии backend. Никаких lat/lon, географического map provider или local bitmap assets в трёх страницах нет.

## Browser evidence

Открыты именно страницы исходного frontend на 5173. HTTP и WebSocket перенаправлены в изолированный backend 8001 с сохранёнными данными; исходная действующая симуляция на 8000 не сбрасывалась и не изменялась. Выполнены основные действия и сохранены 13 скриншотов. Затем открыт отдельный frontend пакета на 5175 и проверены все три маршрута и ровно три ссылки навигации.

CSS/навигация исходного shell на reference screenshots — справка. Другие ссылки на этих изображениях не означают, что другие страницы входят в bundle.
