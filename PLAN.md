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
- [ ] Publish multi-arch image to GHCR so ZimaOS can pull directly (removes manual build)

## Phase 4 — In-app AI settings (v0.2.0)
- [x] `setting` table (new table → no migration needed on existing DBs)
- [x] `ai.config()` precedence env < DB < override; provider presets (anthropic/openai/openrouter/ollama/custom)
- [x] Admin-only `GET/PUT /api/ai/config`, `POST /api/ai/config/test`; key never returned
- [x] Profile → AI assistant sheet (provider, key, model w/ suggestions, advanced base URL, Test, Save); Assistant "Set up AI" CTA
- [x] Tests 12/12; E2E: real Anthropic 401 surfaced cleanly, custom provider test+save+chat OK
- [ ] User: rebuild (`docker compose up -d --build`), add Claude key, then build image for ZimaOS

## Backlog (next)
- [ ] Alembic migrations (needed before first schema change)
- [ ] Reminders/notifications (Web Push via VAPID; period due, pill, BBT)
- [ ] App lock PIN / passkey (WebAuthn)
- [ ] Import from Flo / Clue / Apple Health CSV exports
- [ ] Pregnancy mode (weeks, due date) & perimenopause mode
- [ ] Partner read-only sharing link
- [ ] Streaming AI responses (SSE)
- [ ] Symptom predictions ("cramps likely in 2 days") from patterns
- [ ] Localisation (i18n)
- [ ] Encrypted-at-rest DB (SQLCipher) option
- [ ] CI: GitHub Actions build + test + publish image to GHCR
