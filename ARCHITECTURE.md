# ARCHITECTURE

## Topology
```
Browser/PWA ──HTTP──▶ bloomery container :8000 (host :8420)
                        ├─ FastAPI  /api/*          (session-cookie auth)
                        ├─ static SPA /*            (Vite build, SW precache)
                        ├─ SQLite  /data/bloomery.db (WAL)
                        └─ httpx ──▶ LLM: ollama:11434/v1 | OpenAI-compat | api.anthropic.com
```
Single image, multi-stage: `node:24-alpine` (build SPA) → `python:3.13-slim` (runtime). `entrypoint.sh` starts as root, chowns `$BLOOMERY_DATA_DIR`, drops to uid 10001 via `setpriv`. 1 uvicorn worker, access log off. Footprint: ~60 MiB RAM idle, image 274 MB.

Deploy targets: `docker-compose.yml` (generic, builds locally, optional Ollama profile) · `docker-compose.zimaos.yml` (prebuilt image, `/DATA/AppData/bloomery`, `mem_limit: 256m`, `x-casaos` metadata).

## Stack (pinned 2026-09-30)
| Layer | Tech |
|---|---|
| Backend | Python 3.13, FastAPI 0.142.1, uvicorn 0.54, SQLModel 0.0.47 (SQLAlchemy 2), pydantic-settings 2.15, argon2-cffi 25.1, httpx 0.28, itsdangerous 2.2 |
| Frontend | React 19.3, Vite 8.3 (rolldown), TypeScript 5.9, Tailwind 4.3 (`@tailwindcss/vite`), react-router-dom 7.18, date-fns 4.4, lucide-react 1.49, vite-plugin-pwa 1.3, @fontsource-variable/nunito (self-hosted font, no Google calls) |
| AI | Raw HTTP, no SDKs. OpenAI `/chat/completions` schema (Ollama/LM Studio/OpenRouter/vLLM) + Anthropic `/v1/messages` (`anthropic-version: 2023-06-01`) |

## Backend modules (`backend/app/`)
| File | Role |
|---|---|
| `config.py` | `Settings` (env `BLOOMERY_*`), secret auto-gen, provider defaults |
| `db.py` | engine, WAL + FK pragmas, `create_all` |
| `models.py` | `User`, `DayLog`, `ChatMessage`, `InsightCache` |
| `cycles.py` | **pure** cycle engine (`Engine`), thermal-shift detection, symptom patterns |
| `catalog.py` | tag catalog (single source of truth, served to UI) |
| `ai.py` | provider abstraction, context builder, prompts, rule fallback |
| `deps.py` | auth deps, `today` param, `build_engine` |
| `routers/auth.py` | register/login/logout/me/password/status |
| `routers/tracking.py` | profile, logs, period edit/start/end, cycle overview/calendar, insights, export/import, delete account |
| `routers/assistant.py` | AI status/daily/chat |
| `main.py` | app factory, SessionMiddleware, SPA fallback |

## DB schema (SQLite)
- **user**: id, username (unique, lowercased), password_hash (argon2id), display_name, created_at, onboarded, cycle_length=28, period_length=5, luteal_length=14, goal(track|conceive|avoid), birth_year?, temp_unit(C|F), weight_unit(kg|lb)
- **daylog**: id, user_id→user (CASCADE), day (DATE), UNIQUE(user_id, day), flow(null|spotting|light|medium|heavy), tags JSON `{category:[ids]}`, temperature °C, weight kg, water_ml, sleep_hours, notes, updated_at
- **chatmessage**: id, user_id, role(user|assistant), content, created_at
- **setting**: key (PK), value — server-wide; `ai_provider|ai_base_url|ai_model|ai_api_key` (plaintext; DB file is the trust boundary)
- **insightcache**: id, user_id, day, content — UNIQUE(user_id, day)

Migrations: none yet (`create_all` only). Adding columns requires Alembic or manual `ALTER TABLE` → see PLAN backlog.

## Env keys (no secrets committed)
`BLOOMERY_PORT, BLOOMERY_DATA_DIR(/data), BLOOMERY_STATIC_DIR(/app/static), BLOOMERY_SECRET_KEY, BLOOMERY_ALLOW_REGISTRATION(auto|true|false), BLOOMERY_SECURE_COOKIES, BLOOMERY_SESSION_MAX_AGE_DAYS, BLOOMERY_AI_PROVIDER(none|ollama|openai|anthropic), BLOOMERY_AI_BASE_URL, BLOOMERY_AI_MODEL, BLOOMERY_AI_API_KEY, BLOOMERY_AI_TIMEOUT`

## Invariants
1. Dates are **client-local calendar dates**; every cycle endpoint takes `?today=YYYY-MM-DD` (frontend always sends it). Server never uses UTC "now" for cycle math.
2. Units stored canonical: temperature °C, weight kg. Conversion only in UI.
3. `cycles.py` is side-effect free; all prediction logic lives there and is unit-tested.
4. Spotting never starts/extends a period; only light/medium/heavy = bleeding.
5. A DayLog with no data is deleted, not stored empty.
6. Tag ids validated against `catalog.VALID`; renaming an id orphans old data → only add, never rename.
9. AI config precedence: env `BLOOMERY_AI_*` < `setting` table < per-call override (Test button). Changing provider never reuses the previous provider's url/model/key. Admin = lowest user id. API key never returned (only `has_key` + last 4).
7. LLM receives only a compact JSON summary (≤60 days logs + stats); never credentials/usernames.
8. `/api/*` never falls through to SPA (404 instead).

## Frontend (`frontend/src/`)
`api.ts` (fetch wrapper + types) · `state.tsx` (AppProvider: user, catalog, data `version` bump, log-sheet date, theme; `useFetch`) · `App.tsx` (auth gate → onboarding → router + bottom nav + global `LogDay` sheet) · `components/ui.tsx` (Sheet, Chip, Stepper, LineChart, Logo) · `components/CycleRing.tsx` · `pages/*`.
Design tokens in `index.css` `@theme` (pink-500 #FF4A7D primary, teal-400/500 fertile, canvas/card/ink/muted/line, `.dark` overrides). Custom classes via Tailwind v4 `@utility` (card, btn, btn-primary, btn-ghost, input).
