# AGENTS.md

"6 Majors Travel" marathon-travel booking site: static HTML + one stdlib Python server. No framework, no deps, no tests, no README.

## Run
- `python server.py` serves the site and API at http://localhost:8000 (`PORT` env overrides). `bookings.db` (SQLite) is auto-created on startup and is gitignored — delete it to reset bookings.

## Layout
- `*.html` — hand-written static pages; assets referenced relative as `assets/...`.
- `server.py` — extends `http.server.SimpleHTTPRequestHandler`; serves static files and adds the booking/admin API: POST `/book`, `/admin/login`, `/admin/delete`; GET `/admin`, `/admin/logout`.
- Admin pages are generated inline by `_page()` in `server.py` (duplicates the header/nav/footer markup). Keep nav edits in sync across all HTML files and `_page()`.

## Gotchas
- CSS is cache-busted via `style.css?v=20` — when editing `style.css`, bump the `v=` value in every HTML file and in `server.py` `_page()`. `index.html` currently omits `?v=` (the only page that does).
- Admin password is hardcoded in `server.py` (`ADMIN_PASSWORD`); auth is a raw substring match on the cookie, no sessions.
- No test suite — verify manually: run the server, then exercise endpoints with curl/`Invoke-WebRequest` (`/book`, `/admin`, `/admin/login`).
- Commit convention here is short one-liners ("mi cambio").
