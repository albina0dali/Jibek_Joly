# Проверка handoff bundle

Аудит выполнен 2026-10-02, Asia/Qyzylorda. Подготовка не меняла исходный application code, dataset, станции или дизайн. Все новые материалы находятся внутри `integration_handoff_bundle/`.

- Отдельный backend пакета запущен и отвечает на REST/WS.
- Отдельный frontend установлен из package-lock и проходит TypeScript + Vite production build без CSS warnings.
- Открыты три страницы исходного frontend в браузере, выполнены основные действия и сохранены **13 скриншотов**: default, фильтры/zoom, preview/apply, live/replay, drawers, yard before/after, выбор и projected timeline, применение плана.
- Скачаны реальные CSV/PDF во время replay.
- В браузере проверены три маршрута portable frontend и отсутствие лишних business links; JavaScript page errors отсутствуют.
- Программно проверены station/block/train/yard joins, оригинальные копии и декларации, авторизация HTTP/WS, история и nearest-earlier lookup, yard constraints/metrics/apply, dispatch generate/apply/stale validation, CSV/PDF и reset.

Машинные результаты: `VALIDATION_BROWSER.json`, `VALIDATION_BACKEND.json`. Значения QI: `QUALITY_OBSERVATIONS.json`. Файлы и SHA256: `CHECKSUMS.json`. Проверка целостности: `python tooling/check_integrity.py .` из bundle. Архив рядом с каталогом содержит те же файлы, без node_modules, venv, dist, SQLite и кешей.

## Воспроизведение проверки

```powershell
# После установки backend requirements, из bundle:
python tooling/verify_bundle.py .

Set-Location source/shared_required_only/frontend
npm ci
npm run build
```

`tooling/capture_reference.mjs` используется при наличии исходного проекта, Playwright и трёх запущенных серверов: оригинальный frontend5173, backend пакета8001 и portable frontend5175. Он перенаправляет только capture context в изолированный backend; не использовать его как production feature.

## Чек-лист будущего интегратора

Сверить три `page_specs` по всем blocks/actions, сохранять split между live и preview/replay, не заменить реальные exports заглушками, не перенести yard apply в traffic без отдельной согласованной модели. Сохранить IDs/единицы/epoch и формулы QI/yard. Проверить snapshot shape, Bearer/WS auth, один общий state service и revision/committed-interval gates. Командный дизайн свободно заменяет reference presentation.
