# Оперативная карта / Операциялық карта

The existing `#map` navigation entry and page title are Operations Map. There is no separate route or navigation entry for 2D. The application currently exposes RU and KK, with these localized mode names:

| Locale | Section | 3D mode | 2D mode |
|---|---|---|---|
| RU | Оперативная карта | 3D Обзор сети | 2D Диспетчерская схема |
| KK | Операциялық карта | 3D Желі көрінісі | 2D Диспетчерлік схема |

`web/dispatcher-scheme.js` renders the world supplied by the existing map page. It does not own a simulator, timer, network dataset or index calculation. The same `live()` world feeds both the existing Three.js view and the SVG view. Switching view preserves the clock, commands, selected train, station identities, positions, delays and Movement Index. Mode choice survives language/theme changes and navigation in the current page session; a fresh application load defaults to 3D.

The nine canonical station identities are unchanged. The existing core simulation has six trains, and the operational extension still uses its separate eight-station subset and sixteen trains as documented by the completed unification. The shared Movement Index specification and its 91.1 → 74.0 → 91.1 incident/recovery scenario are unchanged.

The scheme displays primary/reserve track occupancy, direction-specific signals from `signalState`, train direction and delay, and canonical station names. Train and block selection use the existing dispatcher controls. Clicking a station opens the existing arrivals dialog. Clicking a signal uses the same `action(..., 'signal', ...)` path as the existing 3D and signal board. Replay disallows signal commands. “Follow camera” returns to 3D and follows the selected train. The SVG is schematic, not geographical; mobile scrolling stays within its panel.

The existing Three.js renderer, camera controls and simulation logic are preserved. User-facing navigation, section heading, breadcrumbs, browser title, and links returning to the map use the new section name. Mode labels and descriptions live in `web/locales/ru.json` and `kk.json`; there is no application English locale to update.

For review, start `npm start`, open `http://localhost:8787/#map`, then switch between the two mode buttons. Select trains, stations, blocks and signals in 2D; pause motion and compare the train table and index before/after switching. Toggle RU/KZ and the theme. Run `npm run test:map` for these checks and `npm run test:browser` for the existing all-page regression suite.

The operations-center presentation in `web/operations-ui.css` adds a compact calculated KPI strip, grouped navigation, semantic status colors and smaller alert summaries. Source/connection status identifies local Core computation, SSE telemetry or Python polling. The short run identifier is the actual Core trip UUID; Python pages show the actual schedule revision. This UI layer does not merge the two simulators. Python last-received time appears in the connection tooltip, and a failed poll displays the stale-state/reconnect message. See `docs/CASE_ACCEPTANCE_AUDIT.md` for the acceptance gaps, including the absence of a single cross-model incident/Apply/map flow.
