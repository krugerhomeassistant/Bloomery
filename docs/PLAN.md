# PLAN

## Phase 0 — Research & design
- [x] Research Flo UI patterns (cycle circle, week strip, insight cards, chip logging, calendar legend)
- [x] Verify latest package versions (npm/pip registries, 2026-09-30)
- [x] Choose stack: FastAPI + SQLite + React/Vite/Tailwind PWA, single container, optional Ollama

## Phase 1 — Backend (v0.1.0)
- [x] config/db/models
- [x] cycle engine (`cycles.py`): periods, weighted prediction, BBT ovulation, fertile window, status, calendar, stats, flags, patterns
- [x] tag catalog
- [x] auth (argon2, session cookie, registration policy)
- [x] tracking API (profile, logs, period edit/start/end, overview, calendar, insights, export/import, delete)
- [x] AI provider abstraction (ollama/openai/anthropic) + daily insight cache + chat
- [x] tests: 11 passing (`backend/tests`)

## Phase 2 — Frontend (v0.1.0)
- [x] Tailwind v4 theme tokens + dark mode
- [x] Auth, Onboarding (5 steps)
- [x] Today (week strip, CycleRing, insight cards, flags, current cycle)
- [x] Calendar (13 months, legend, day panel, edit mode)
- [x] LogDay sheet (flow drops, 10 categories, search, measurements, notes)
- [x] Insights (tiles, history bars, patterns, BBT/weight charts)
- [x] Assistant chat (+ disabled state)
- [x] Profile (cycle settings, goal, units, theme, AI status, export/import, password, logout, delete)
- [x] PWA manifest + icons + SW

## Phase 3 — Packaging & verification
- [x] Multi-stage Dockerfile, non-root, healthcheck
- [x] docker-compose with `ai` profile (Ollama)
- [x] E2E in container: seed demo, Playwright screenshots of all screens, fake OpenAI server → chat/insight verified
- [x] Copy project to `E:\Projects\Personal\Bloomery`
- [x] Privilege-dropping entrypoint (root-owned bind mounts)
- [x] ZimaOS compose (`docker-compose.zimaos.yml`, /DATA/AppData, 256 MiB cap) + README guide
- [x] Memory profile: ~60 MiB idle, ~72 MiB under load
- [ ] User: deploy on ZimaOS and log in
- [x] Publish multi-arch image to GHCR so ZimaOS can pull directly (`.github/workflows/ci.yml`)

## Phase 4 — In-app AI settings (v0.2.0)
- [x] `setting` table (new table → no migration needed on existing DBs)
- [x] `ai.config()` precedence env < DB < override; provider presets (anthropic/openai/openrouter/ollama/custom)
- [x] Admin-only `GET/PUT /api/ai/config`, `POST /api/ai/config/test`; key never returned
- [x] Profile → AI assistant sheet (provider, key, model w/ suggestions, advanced base URL, Test, Save); Assistant "Set up AI" CTA
- [x] Tests 12/12; E2E: real Anthropic 401 surfaced cleanly, custom provider test+save+chat OK
- [ ] User: rebuild (`docker compose up -d --build`), add Claude key, then build image for ZimaOS

## Phase 5 — Daily feed & proactive insights (v0.3.0)
- [x] `app/feed.py`: forecasts, milestones, recap, phase tips, after-log note
- [x] `GET /api/feed`; `note` on `PUT /api/logs`; forecasts in AI context
- [x] Today: feed cards + detail sheet ("Log how you feel"); global toast for log notes
- [x] Tests 15/15 (`test_feed.py`); E2E cards/sheet/toast verified
- [ ] Optional: AI-written recap/notes (currently rules; cheap to add via ai.complete)
- [ ] Push notifications for milestones (needs Web Push; see backlog)

## Phase 6 — Public repo (github.com/krugerhomeassistant/Bloomery)
- [x] Landing README: hero image, badges, feature grid, screenshots (light/dark), install, ZimaOS, AI table, privacy, maths, mermaid architecture, config, roadmap
- [x] `docs/screenshots/*` (Playwright, demo data, fake LLM) + `docs/assets/hero.jpg`
- [x] Living docs moved to `docs/`
- [x] CI: pytest + frontend build on PR/push; multi-arch (amd64/arm64) image → `ghcr.io/krugerhomeassistant/bloomery` (`latest`, semver, sha)
- [x] compose files default to GHCR image; `.env` optional
- [x] Pushed `main`; first CI run green (tests + amd64/arm64 image to GHCR)
- [ ] After first CI run: make GHCR package public (Package settings → Change visibility)
- [ ] Choose a license (user decision)

## Phase 7 — Notifications & license (v0.4.0)
- [x] MIT LICENSE + README badge/section
- [x] ntfy / Gotify / Home Assistant / Discord notifications, daily at user time + tz; kinds incl. pill reminder
- [x] Profile → Notifications sheet (URL help, time, kinds, Send test)
- [x] Tests 17/17 (`test_notify.py`: validation, ntfy/discord/gotify payloads, once-per-day scheduling)
- [ ] User: make GHCR package public (anonymous pull was still 401 on 2026-09-30)

## Phase 8 — Internet-ready + migration (v0.5.0)
- [x] Login throttling (per IP), security headers, no-store API caching
- [x] Import Flo / Clue / CSV period history (`importers.py` + self-check; UI auto-routes by file)
- [x] Tests 19/19
- [x] Deployment context: owner's instance is Tailscale-only → no further hardening planned
- [ ] Verify Clue format against a real `.cluedata` (format inferred from community converters)

## Phase 9 — AI recap + Apple Health (v0.6.0)
- [x] `/api/ai/recap` + RecapSheet (Insights history + Today recap card), cached per completed cycle
- [x] Apple Health: client-side streaming extraction + server mapping/merge
- [x] Tests 21/21; E2E: 4.7 MB synthetic export → 63 days (35 period), 6 cycles, BBT °F→°C; recap sheet via fake LLM
- [ ] Verify against a real iPhone export (value strings inferred from HealthKit enums)

## Phase 10 — Partner sharing + learned settings (v0.7.0)
- [x] Share link create/regenerate/revoke; public partner page (ring, tip, 5-week calendar); privacy test asserts no symptoms/moods/sex/notes leak
- [x] Profile cycle settings show learned values ("using …")
- [x] Tests 22/22; E2E partner page in anonymous browser context

## Phase 11 — Home Assistant + streaming AI (v0.8.0)
- [x] Generic tokens `/api/tokens/{share|ha}`; HA JSON `/api/ha/{token}?tz=`; ICS `/api/ha/{token}/calendar.ics`
- [x] Profile section: generated `rest:` YAML (parsed OK with PyYAML) + ICS URL, new/revoke
- [x] `ai.stream()` (Anthropic SSE + OpenAI deltas) → `POST /api/ai/chat/stream` (text/plain chunks, history saved at end, `<think>` stripped)
- [x] Assistant reads body via `TextDecoderStream`, updates bubble live
- [x] Tests 24/24; E2E: partial reply visible mid-stream (fake SSE LLM), final saved clean

## Phase 12 — App lock (v0.9.0)
- [x] 4-digit PIN argon2-hashed in Setting `pin:<uid>`; `PUT /api/auth/pin` (needs account password; `pin:null` removes); `POST /api/auth/pin/verify` (5 wrong → session cleared)
- [x] `LockScreen` overlay on app open + after 60 s hidden; Profile "App lock (PIN)" sheet
- [x] Account deletion now also removes per-user Setting rows (notes, tokens, PIN, recaps)
- [x] Tests 25/25; E2E set PIN → reload locked → wrong PIN "4 tries left" → correct unlocks

## Phase 13 — Life stages (v1.0.0)
- [x] Setting `mode:<uid>` = {mode: cycle|pregnancy|perimenopause, lmp}; `PUT /api/life-stage`; `/api/auth/me` returns mode+lmp
- [x] Pregnancy: `Engine.pregnancy()` week/day, due (LMP+280), trimester, baby size; purple ring = progress/280; no predicted segments, no phases from LMP on, no flags; feed = size/countdown/trimester tip; partner page tip
- [x] Positive pregnancy test log note suggests pregnancy mode
- [x] Perimenopause: variability ≥5, "Days since period" instead of late, cycle-length flags replaced by 60-day gap + 12-month marker; symptoms night sweats, brain fog, joint pain, palpitations
- [x] Profile "Life stage" switch + LMP date; AI system prompt + context include life stage; daily AI cache cleared on change
- [x] Tests 26/26; E2E pregnancy (13w 0d, due Apr 7, clean week strip) + perimenopause + back to cycle

## Phase 14 — HA integration + gentler lock (v1.1.0)
- [x] `custom_components/bloomery` (HACS custom repo, `hacs.json` at root): config flow (paste feed URL, validates, unique id = host+user id), reconfigure for new tokens, coordinator 15 min + midnight refresh, 12 sensors + 2 binary sensors, `icons.json`, `translations/en.json`, `brand/` icons (HA 2026.3+)
- [x] HA JSON adds user_id, name, version, mode, pregnancy_week, due_date; `VERSION` moved to `app/__init__.py`
- [x] Profile HA section: integration steps + URL (YAML removed); calendar ICS kept
- [x] `tests_ha/` with pytest-homeassistant-custom-component (HA 2026.2): flow errors, entities, abort, reconfigure; CI job with hassfest
- [x] App lock: only after N min away (per-device choice 1 min–4 h, default 15, `lastActive` in localStorage, survives app close); 10 wrong PINs before sign-out

## Phase 15 — Calendars, Platinum integration, releases (v1.2.0)
- [x] Feed JSON `events` + ICS `?type=period|fertile|ovulation`
- [x] Integration: Periods / Fertile windows / Ovulation calendars with `initial_color`; modules api/coordinator/entity; reauth; diagnostics (redacted); exception translations; PARALLEL_UPDATES; pregnancy entities disabled by default; `quality_scale.yaml` (platinum, self-assessed)
- [x] `tests_ha`: 13 tests, 100% coverage; mypy --strict clean
- [x] `docs/home-assistant.md` (install, params, entities, data update, examples, use cases, limitations, troubleshooting, removal)
- [x] Tooling: ruff lint+format (pyproject.toml), Dependabot, CHANGELOG (Keep a Changelog), `scripts/bump.py`, SECURITY/CONTRIBUTING, issue + PR templates, version in Profile footer
- [x] CI: lint → backend → HA tests/coverage/mypy → image → tag-driven GitHub release (`bloomery.zip` for HACS `zip_release`); `validate.yml` = hassfest + HACS action (daily)
- [x] CI creates tag + release when main has an unreleased version (tag push blocked from this sandbox)
- [ ] User: add GitHub repo topics (HACS check)
- [x] Dependabot majors reviewed: TypeScript 7 + Python 3.14 merged (v1.2.1); tests on 3.14.7, cp314 wheels for amd64+arm64 verified
- [ ] Merge Node 26 PR (#1) once Node 26 is LTS (~2026-10-28); build already verified on v26.10.0
- [ ] Optional: submit to HACS default store (needs release + passing HACS action)

## Phase 16 — Backups (v1.3.0)
- [x] `app/backup.py`: sqlite3 backup API snapshot → gzip → optional AES-256-GCM (Argon2id 32 MiB); `/data/backups`, retention, unique names, 3 pre-restore safety copies
- [x] Restore: validate (magic, gzip, SQLite header, integrity_check, core tables) → safety copy → dispose engine → sqlite backup API into the live file → init_db
- [x] Google Drive (web OAuth, `drive.file`): connect/callback with session state + origin, folder find-or-create (fresh-install recovery), multipart upload, prune, download/restore, revoke on disconnect
- [x] Scheduler task in lifespan (daily at local time, once per day); owner-only API `/api/backups/*`; `is_owner` on `/api/auth/me`
- [x] UI: Profile → Backups & restore sheet (status, run, schedule, keep, passphrase, Google setup guide with redirect URI, cloud + local lists, restore confirm with passphrase)
- [x] Tests 32/32 (fake Drive via httpx.MockTransport, encrypted restore, tick, owner-only); E2E backup → encrypt → restore → Google return path
- [ ] Next: HACS default-store PR (user), insights charts (v1.5), translations (v1.6)

## Phase 17 — Face ID unlock + push notifications (v1.4.0)
- [x] `routers/passkeys.py` (py_webauthn 3.0.1): platform authenticator, UV required, RP = Origin host, per-user list in Setting `passkeys:<uid>`, sign-count update, per-address keys; `/me.passkeys`
- [x] `push.py`: VAPID key in Setting `vapid` (py-vapid), aes128gcm via http-ece, send with httpx (no requests/aiohttp), drop 404/410 subs; contact = subscribing HTTPS host
- [x] notify: `deliver()` = URL + push; test endpoint works with device only; `/api/notifications/push` GET/POST/DELETE
- [x] Frontend: `webauthn.ts` helpers, LockScreen Face ID key, Passkeys in App lock sheet, NotifySettings "This device", `public/push-sw.js` via workbox importScripts
- [x] Tests 34/34 (soft authenticator with real ECDSA incl. wrong origin/replay/unknown device; push payload decrypted as a browser would, 410 cleanup); E2E Chromium virtual authenticator register → lock → unlock

## Phase 18 — Insights charts (v1.5.0)
- [x] `cycles.symptom_heatmap`: top 6 tags × cycle day (21–35), share of cycles that reached the day; avg period days + ovulation day for the phase strip; in `/api/insights` as `heatmap`
- [x] `components/InsightCharts.tsx`: CycleTrend (dots + thin line, dashed avg, typical band; tap/hover detail) and SymptomMap (single-hue sequential grid, tap detail line, legend, aria-labels)
- [x] Tests 35/35; screenshots light + dark

## Phase 19 — Doctor's report (v1.6.0)
- [x] `app/report.py` + `GET /api/report?months=&notes=`: window cycles (heavy/spotting days, top tags), summary (avg/min/max/SD), flags, symptom counts/patterns/heatmap (window-only via `since`), BBT, pill, positive tests, optional notes; sex/activity excluded
- [x] `pages/Report.tsx` at `/report` + print CSS (forced light, no nav, A4, cards don't split); entry button on Insights
- [x] Tests 36/36; PDF printed with Chromium and checked
- [x] CODE_OF_CONDUCT.md (Contributor Covenant 2.1, official text; reports via GitHub private reporting)
- [ ] Next: v1.7 HA/Siri logging, v1.8 birth control, v1.9 wearable temperature, v2.0 Afrikaans

## Phase 20 — Logging from Home Assistant & Siri (v1.7.0)
- [x] Token kind `api` (write-only key), `routers/quick.py`: Bearer auth, `/catalog`, `/period-start`, `/log` (merge tags by id/label/cat:id, flow, temp °C/°F, note append, day/tz); account delete removes `api:` tokens
- [x] Integration: options flow (API key, validated), `services.py` actions registered in `async_setup` (`log_period_start`, `log`, response data), services.yaml + translations + icons; quality scale action rules now done
- [x] UI: Profile → Shortcuts & automations (key create/show/copy/rotate/off, Siri Shortcut + HA + curl guides)
- [x] Tests: backend 37/37 (key can't reach other endpoints), HA 18/18 at 100%; E2E key → curl → log

## Phase 21 — Birth control (v1.8.0)
- [x] `app/contraception.py` pure status() per method (pill types, ring 3+1 wk, patch 3×1 wk + 1 off, injection 13 wk, IUD monthly string check + replacement, implant replacement); Setting `bc:<uid>`
- [x] `GET/PUT /api/contraception`; Today feed card (kind contraception); notify "pill" kind = birth control reminders on action days (legacy daily pill text when no method set)
- [x] `Profile.hormonal` → no fertile/ovulation kinds/phases/chance/status, calendars & HA events skip them, ring hides fertile arc, partner page too; AI context flag
- [x] Tests 40/40 (all schedules incl. boundaries, hidden fertility, endpoint + notification); E2E pill setup → Today

## Backlog (next)
- [ ] Alembic migrations (needed before first schema change)
- [x] Reminders/notifications — done via ntfy/Gotify/HA/Discord (Web Push still possible later for HTTPS installs)
- [x] App lock PIN (passkey/WebAuthn still open; needs HTTPS)
- [x] Import from Flo / Clue / CSV (Apple Health still open)
- [x] Pregnancy mode (weeks, due date) & perimenopause mode
- [x] Partner read-only sharing link
- [x] Streaming AI responses
- [x] Symptom predictions (feed forecasts / heads-ups, v0.3)
- [ ] Localisation (i18n)
- [ ] Encrypted-at-rest DB (SQLCipher) option
- [x] CI: GitHub Actions build + test + publish image to GHCR
