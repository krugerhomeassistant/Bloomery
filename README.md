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

### Enable AI (in the app)

Profile → **AI assistant** → pick Claude / OpenAI / OpenRouter / Ollama / any OpenAI-compatible server → paste API key → **Test** → **Save**.
Only the first account (server owner) can change it. Keys are stored in `data/bloomery.db` and never sent back to the browser.
`.env` `BLOOMERY_AI_*` values still work as defaults; in-app settings override them.

### Local AI (Ollama)

```bash
# .env
BLOOMERY_AI_PROVIDER=ollama
BLOOMERY_AI_MODEL=llama3.2:3b

docker compose --profile ai up -d
docker compose exec ollama ollama pull llama3.2:3b
docker compose restart bloomery
```

Cloud alternatives: `BLOOMERY_AI_PROVIDER=openai` (any OpenAI-compatible API) or `anthropic`, plus `BLOOMERY_AI_API_KEY`.

## ZimaOS

ZimaOS "Install a customized app → Import" can't build images, so get the image onto the box first.

**Option A — build on your PC (recommended for low-RAM servers; the build step needs ~1 GB):**
```powershell
# Windows, Docker Desktop, in the project folder
docker build -t bloomery:latest .
docker save bloomery:latest -o bloomery.tar
scp bloomery.tar root@<zima-ip>:/DATA/
ssh root@<zima-ip> "docker load -i /DATA/bloomery.tar && rm /DATA/bloomery.tar"
```
(ZimaOS: Settings → General → Developer mode → enable SSH.)

**Option B — build on ZimaOS:** copy the folder to `/DATA/AppData/bloomery-src`, SSH in, `cd` there, `docker build -t bloomery:latest .`

Then in the ZimaOS dashboard: App Store → **+** → *Install a customized app* → **Import** → paste `docker-compose.zimaos.yml` → Install. Open `http://<zima-ip>:8420`. Data lives in `/DATA/AppData/bloomery`.

### Resource usage (measured)
~60 MiB RAM idle, ~72 MiB after 600 concurrent API requests; image 274 MB; ~0% CPU idle. The ZimaOS compose caps it at 256 MiB.
Local AI (Ollama) needs ≥3–4 GB RAM for a 3B model — on small servers use `BLOOMERY_AI_PROVIDER=anthropic` or `openai` (cloud; cycle summaries leave the box) or `none`.

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
