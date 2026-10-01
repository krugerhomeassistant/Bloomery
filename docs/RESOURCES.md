# RESOURCES

## Key paths
| What | Path |
|---|---|
| Cycle engine | `backend/app/cycles.py` |
| Tag catalog | `backend/app/catalog.py` |
| AI provider + prompts | `backend/app/ai.py` |
| API routers | `backend/app/routers/{auth,tracking,assistant}.py` |
| Settings/env | `backend/app/config.py`, `.env.example` |
| Tests | `backend/tests/` |
| Theme tokens | `frontend/src/index.css` |
| API client/types | `frontend/src/api.ts` |
| Global state | `frontend/src/state.tsx` |
| Screens | `frontend/src/pages/*.tsx` |
| Cycle ring | `frontend/src/components/CycleRing.tsx` |
| PWA config | `frontend/vite.config.ts` |
| Demo seeder | `scripts/seed_demo.py` (user demo / demodemo) |
| Data (runtime) | `./data/bloomery.db`, `./data/secret.key` |

- `docs/home-assistant.md` integration guide · `CHANGELOG.md` · `CONTRIBUTING.md` · `SECURITY.md` · `.github/workflows/ci.yml` (CI + release) · `.github/workflows/validate.yml` (hassfest + HACS)
- `custom_components/bloomery/` HA integration · `tests_ha/` its tests · `hacs.json` HACS metadata

## Endpoints (all under `/api`, docs at `/api/docs`)
`GET health` · `GET catalog` · auth: `GET status, POST register, POST login, POST logout, GET me, POST password` · `PUT profile` · `GET logs?start&end`, `GET|PUT logs/{day}` · `PUT period`, `POST period/start`, `POST period/end` · `GET cycle/overview`, `GET cycle/calendar?start&end` · `GET insights` · `GET export`, `POST import`, `DELETE account` · `GET ai/status`, `GET ai/daily[?refresh=true]`, `GET|POST|DELETE ai/chat`. Cycle endpoints accept `?today=`.

## External docs
- HA quality scale rules https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/ · HACS action https://www.hacs.xyz/docs/publish/action/ · HACS default inclusion https://hacs.xyz/docs/publish/include/ · Keep a Changelog https://keepachangelog.com/en/1.1.0/
- HA DataUpdateCoordinator https://developers.home-assistant.io/docs/integration_fetching_data/ · HACS publish https://hacs.xyz/docs/publish/integration/ · local brand images (2026.3+) https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api/
- FastAPI https://fastapi.tiangolo.com · SQLModel https://sqlmodel.tiangolo.com
- Vite https://vite.dev · Tailwind v4 https://tailwindcss.com/docs · vite-plugin-pwa https://vite-pwa-org.netlify.app
- React Router https://reactrouter.com · date-fns https://date-fns.org · lucide https://lucide.dev
- Ollama OpenAI compat https://github.com/ollama/ollama/blob/main/docs/openai.md · models https://ollama.com/library
- Anthropic Messages API https://platform.claude.com/docs/en/api/overview · versioning https://platform.claude.com/docs/en/api/versioning
- Flo UI references: https://screensdesign.com/showcase/flo-period-pregnancy-tracker , https://dribbble.com/tags/period-tracker-app
- Clinical context: ACOG — menstruation as a vital sign (normal cycle 21–35 d, bleeding ≤7 d)

## Local
- Host folder: `E:\Projects\Personal\Bloomery`
- Default URL: http://localhost:8420
