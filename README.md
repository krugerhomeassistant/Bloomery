# 🌸 Bloomery

Private, self-hosted period & cycle tracker with predictions, pattern insights and an optional AI assistant.
Mobile-first installable PWA; one Docker container; your data never leaves your server (unless you pick a cloud LLM).

## Quick start

```bash
cp .env.example .env
docker compose up -d --build
# open http://<host>:8420  → first account created becomes the only one (BLOOMERY_ALLOW_REGISTRATION=auto)
```

On a phone: open the URL → browser menu → **Add to Home Screen**.

### Enable local AI (Ollama)

```bash
# .env
BLOOMERY_AI_PROVIDER=ollama
BLOOMERY_AI_MODEL=llama3.2:3b

docker compose --profile ai up -d
docker compose exec ollama ollama pull llama3.2:3b
docker compose restart bloomery
```

Cloud alternatives: `BLOOMERY_AI_PROVIDER=openai` (any OpenAI-compatible API) or `anthropic`, plus `BLOOMERY_AI_API_KEY`.

## Features

- **Today**: cycle ring with period/fertile arcs, "Period in N days" / "Ovulation in N days" / "Late by N", week strip, daily insight cards
- **Calendar**: logged, predicted, fertile and ovulation days; edit-mode period marking
- **Daily log**: flow, 10 categories (symptoms, mood, sex, discharge, digestion, activity, pill, tests…), BBT, weight, water, sleep, notes
- **Predictions**: recency-weighted cycle length, learned period length, BBT thermal-shift ovulation detection, learned luteal length
- **Insights**: averages, regularity, cycle history bars, phase-linked symptom patterns, BBT & weight charts, health-check flags
- **AI**: daily personalised insight + chat grounded in your data (Ollama / OpenAI-compatible / Anthropic)
- Multi-user, argon2 passwords, JSON export/import, account deletion, dark mode

> Predictions are estimates, not medical advice and not a contraceptive method.

## Development

```bash
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/uvicorn app.main:app --reload            # :8000
.venv/bin/python -m pytest -q
cd frontend && npm install && npm run dev           # :5173, proxies /api
python scripts/seed_demo.py http://localhost:8000   # demo/demodemo
```

API docs: `/api/docs`. See `WIKI.md`, `ARCHITECTURE.md`, `PLAN.md`.

## Backups

Everything lives in `./data` (`bloomery.db` SQLite + `secret.key`). Copy the folder while the container is stopped, or use in-app export.
