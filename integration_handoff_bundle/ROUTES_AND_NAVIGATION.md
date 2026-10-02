# Routes, entry points, host contract

Исходный entry: frontend/index.html → frontend/src/main.tsx → React StrictMode/createRoot → BrowserRouter → App. Исходный проект имеет 11 страниц; переносить **только** следующие три.

| Route | Component original | Navigation RU / KK / EN | Bundle entry |
|---|---|---|---|
| /dispatch | pages.tsx: Dispatch | План движения / Қозғалыс жоспары / Dispatch Plan | source/movement_plan/Dispatch.tsx |
| /history | pages.tsx: History | История и отчёты / Тарих және есептер / History & Reports | source/history_reports/History.tsx |
| /yard | resource-pages.tsx: YardBrain | Вагоны и составы / Вагондар мен құрамдар / Yard Brain | source/wagons_consists/YardBrain.tsx |

Фактические H1 и nav подписи могут различаться регистром; точные тексты из catalog/resources и *.visible.json. Исходные `/`, `/traffic`, `/incidents`, `/advisory`, `/analytics`, `/locomotives`, `/maintenance`, `/settings` **не перенесены**. Root и неизвестный маршрут reference host редиректят /dispatch. Это adapter, не смена маршрутов исходного проекта.

## Shared host behaviour

Sidebar исходника: JIBEK JOLY, Railway operations, corridor Arqa — Dala / Sector 01 · 164 km, navigation, synthetic warning, account name/role, sign out. Верхняя панель: connection LIVE/CONNECTING/RECONNECTING/OFFLINE, scenario time, UTC+05, RU/ҚАЗ/EN, count active trains (excluding scheduled/completed), count active incidents, QI with one decimal, pause/resume ×speed. Footer: synthetic seed42, WebSocket 1Hz и browser render latency (это UI processing, не network RTT). Изменение внешнего вида shell допустимо.

Login — сервисный экран, не четвёртая переносимая business page. Сессия `{token,username,role,expires}` в sessionStorage['session']; reload сохраняет session в этой вкладке. Logout удаляет ключ. Язык localStorage['jibek-joly.language'] = ru/kk/en; default ru, подписка useSyncExternalStore, html.lang меняется без reload. Browser globals делают i18n client-only; для SSR нужен host adapter.

## PageProps contract (shared page-contract.ts)

`{ state: Snapshot, session: Session, select(id), act(path, body?): Promise<boolean>, notify(message) }`.

`useLive`: GET /api/state + authenticated WS /ws/live. Token отправляется первым WS frame `{token}`, не query string. Snapshot приходит каждую секунду даже при paused. Offline/watchdog (>4s silence) → reconnect exponential 500×2^attempt ms, max15s; после >4 попыток OFFLINE; online возвращает reconnect. Unmount закрывает socket/listeners/timers.

`act`: POST, если ответ содержит trains — напрямую setState; иначе GET /api/state. Ошибка → toast и false. Поведение Generate alternatives зависит от этого: /api/replan отвечает options[], host затем получает state. Drawer Dispatch живёт в host с selected train ID; Historical drawer живёт внутри History и использует replay snapshot. Toast закрывается по click или через7s.

Разделение данных: dispatch apply обновляет schedule/revision/history; History показывает это через общий поток. Yard использует отдельный GET/POST resource contract; только actions log связывает его с History. Resource GET выполняется при mount/session change, не каждую секунду. Выход/вход на Yard сбрасывает локальные mode/selection/frame, но manager result/applied сохраняются до backend reset/restart.
