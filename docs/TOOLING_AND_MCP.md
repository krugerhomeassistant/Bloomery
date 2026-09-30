# TOOLING & MCP

## Runtime tools
| Tool | Use | Why |
|---|---|---|
| Docker + Compose | build/run single image; `ai` profile adds Ollama | one-command self-hosting |
| Ollama (`ollama/ollama:latest`) | local LLM, OpenAI-compatible `/v1` | privacy: data never leaves host |
| uvicorn | ASGI server, `--proxy-headers` | behind reverse proxy |

## Dev tools
| Tool | Command |
|---|---|
| pytest | `cd backend && .venv/bin/python -m pytest -q` |
| tsc | `cd frontend && npx tsc --noEmit` |
| Vite dev | `npm run dev` (proxy `/api` → :8000) |
| Playwright (Chromium) | visual QA screenshots at 390×844 (script pattern in LESSONS #4 / ACTIVE_CONTEXT) |
| `pytest-homeassistant-custom-component` | HA test harness for `tests_ha/` (Python 3.13 venv) | real HA core in tests |
| hassfest (GH action) | validates the HA integration manifest/translations in CI | official HA validator |
| `scripts/seed_demo.py` | demo data (7 cycles, symptoms, BBT) |
| fake LLM | tiny `http.server` returning `/chat/completions` JSON to test AI path without a model |

## Claude session tooling used
- WebSearch/WebFetch: Flo UI research, Ollama models, Anthropic API version
- npm/pip registries: version verification
- Remote device bridge: deliver files to `E:\Projects\Personal\Bloomery`
- No MCP servers required by the app itself.

## Candidate integrations (not yet added)
- Alembic (migrations) · pywebpush (reminders) · GitHub Actions + GHCR (CI images) · Renovate (dep updates)
