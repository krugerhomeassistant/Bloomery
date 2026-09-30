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
- [ ] Setting `mode:<uid>` = {mode: cycle|pregnancy|perimenopause, lmp}
- [ ] Pregnancy: week/day, due date (LMP+280), weekly cards, trimester tips, predictions hidden, suggest after positive test
- [ ] Perimenopause: wider uncertainty, gentler flags, days-since-period, 12-month note; new symptoms
- [ ] Profile "Life stage" switch; AI context includes mode

## Backlog (next)
- [ ] Alembic migrations (needed before first schema change)
- [x] Reminders/notifications — done via ntfy/Gotify/HA/Discord (Web Push still possible later for HTTPS installs)
- [x] App lock PIN (passkey/WebAuthn still open; needs HTTPS)
- [x] Import from Flo / Clue / CSV (Apple Health still open)
- [ ] Pregnancy mode (weeks, due date) & perimenopause mode
- [x] Partner read-only sharing link
- [x] Streaming AI responses
- [ ] Symptom predictions ("cramps likely in 2 days") from patterns
- [ ] Localisation (i18n)
- [ ] Encrypted-at-rest DB (SQLCipher) option
- [ ] CI: GitHub Actions build + test + publish image to GHCR
