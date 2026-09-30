<div align="center">

<img src="docs/assets/hero.jpg" alt="Bloomery — your cycle, your server, your data" width="100%">

# 🌸 Bloomery

**A beautiful, private, self-hosted period & cycle tracker — with smart predictions, daily insights and an optional AI assistant.**

[![CI](https://github.com/krugerhomeassistant/Bloomery/actions/workflows/ci.yml/badge.svg)](https://github.com/krugerhomeassistant/Bloomery/actions/workflows/ci.yml)
[![Docker image](https://img.shields.io/badge/ghcr.io-bloomery-FF4A7D?logo=docker&logoColor=white)](https://github.com/krugerhomeassistant/Bloomery/pkgs/container/bloomery)
![Platforms](https://img.shields.io/badge/arch-amd64%20%7C%20arm64-22ADA5)
![RAM](https://img.shields.io/badge/RAM-~60%20MB-7C5CE0)
![Python](https://img.shields.io/badge/FastAPI-Python%203.13-3776AB?logo=python&logoColor=white)
![React](https://img.shields.io/badge/React%2019-PWA-61DAFB?logo=react&logoColor=black)

[Features](#-features) · [Screenshots](#-screenshots) · [Install](#-install-in-60-seconds) · [ZimaOS](#-zimaos--casaos) · [AI](#-ai-assistant) · [Privacy](#-privacy) · [How it works](#-how-predictions-work) · [Roadmap](#-roadmap)

</div>

---

Period apps know some of the most personal data about you, and most of them live on someone else's servers. **Bloomery** gives you the polished experience of a modern cycle tracker, but it runs on **your** hardware: a NAS, a Raspberry Pi, a home server or a $5 VPS. One container, one SQLite file, no telemetry, no ads, no accounts anywhere but your own.

## ✨ Features

<table>
<tr>
<td width="50%" valign="top">

### 🌷 Today at a glance
A big, colour-coded **cycle ring** that tells you what matters right now: *Period · Day 2*, *Ovulation in 3 days*, *Period in 12 days* or *Late by 2 days*, with your chance of pregnancy and a week strip on top.

### 📅 Calendar
Logged periods, **predicted periods**, fertile window and ovulation day across 13 months. Tap **Edit period** to tick days on and off.

### 📝 One-tap logging
Flow plus **10 categories** of chips: symptoms, mood, sex & libido, discharge, digestion, activity, pill, ovulation and pregnancy tests. Also basal temperature, weight, water, sleep and notes, all searchable.

</td>
<td width="50%" valign="top">

### 🔮 Predictions that learn
Recency-weighted cycle length, learned period length, **BBT thermal-shift ovulation detection** and a learned luteal phase. Late cycles push predictions forward automatically.

### 💡 Daily feed
- **Heads-ups** from *your own* history: *"You might notice tender breasts today (4 of your last 5 cycles)"*
- Milestones: period started, fertile window opens, period due, late
- **Last-cycle recap** and rotating phase tips
- A helpful note every time you log

### 📊 Insights
Averages, regularity, cycle history, **symptom ↔ phase patterns**, temperature and weight charts, plus gentle health-check flags.

</td>
</tr>
<tr>
<td valign="top">

### ✨ AI assistant *(optional)*
A daily personalised insight, plus a chat that already knows your cycle history. Connect **Claude, OpenAI, OpenRouter, Ollama** or any OpenAI-compatible server, **right from the app**.

</td>
<td valign="top">

### 🏠 Built for self-hosting
Multi-arch Docker image · ~60 MB RAM · installable **PWA** · dark mode · multi-user · argon2 passwords · JSON export/import · one-tap account deletion.

</td>
</tr>
</table>

## 📸 Screenshots

<div align="center">

| Today | Daily feed | Log your day | After logging |
|:---:|:---:|:---:|:---:|
| <img src="docs/screenshots/today-light.png" width="200"> | <img src="docs/screenshots/feed-light.png" width="200"> | <img src="docs/screenshots/log-light.png" width="200"> | <img src="docs/screenshots/note-light.png" width="200"> |
| **Calendar** | **Insights** | **Body patterns** | **AI assistant** |
| <img src="docs/screenshots/calendar-light.png" width="200"> | <img src="docs/screenshots/insights-light.png" width="200"> | <img src="docs/screenshots/patterns-light.png" width="200"> | <img src="docs/screenshots/assistant-light.png" width="200"> |

<details>
<summary><b>🌙 Dark mode</b></summary>
<br>

| Today | Calendar | Insights | AI setup |
|:---:|:---:|:---:|:---:|
| <img src="docs/screenshots/today-dark.png" width="200"> | <img src="docs/screenshots/calendar-dark.png" width="200"> | <img src="docs/screenshots/insights-dark.png" width="200"> | <img src="docs/screenshots/ai-settings-dark.png" width="200"> |

</details>
</div>

## 🚀 Install in 60 seconds

**Docker (one line):**

```bash
docker run -d --name bloomery -p 8420:8000 -v bloomery-data:/data --restart unless-stopped \
  ghcr.io/krugerhomeassistant/bloomery:latest
```

**Or Docker Compose:**

```bash
git clone https://github.com/krugerhomeassistant/Bloomery.git && cd Bloomery
docker compose up -d            # pulls the prebuilt image (use --build to build from source)
```

Open **http://your-server:8420**. The first account you create becomes the owner, and sign-ups close automatically after that.

📱 **On your phone:** open the URL, then use your browser menu → **Add to Home Screen**. It launches full-screen, like a native app.

## 🧊 ZimaOS / CasaOS

1. Dashboard → **App Store** → **+** → **Install a customized app** → **Import**
2. Paste [`docker-compose.zimaos.yml`](docker-compose.zimaos.yml) → **Install**
3. Open `http://<zima-ip>:8420`

Data lives in `/DATA/AppData/bloomery`. The app is capped at 256 MB RAM (it uses ~60 MB), so it happily runs next to everything else on small boxes.

## 🤖 AI assistant

Everything works without AI. Turning it on adds a **personalised daily insight** and a **chat** that answers questions like *"why am I so tired before my period?"* using your own logs.

Set it up in the app: **Profile → AI assistant → pick a provider → paste key → Test → Save.**

| Provider | Default model | Notes |
|---|---|---|
| **Claude (Anthropic)** | `claude-haiku-4-5` | Fast and inexpensive; Sonnet/Opus for richer answers |
| **OpenAI** | `gpt-5-mini` | |
| **OpenRouter** | `openrouter/auto` | One key, hundreds of models |
| **Ollama** | `llama3.2:3b` | 100% local. Needs ~3–4 GB free RAM (`docker compose --profile ai up -d`) |
| **Custom** | — | Any OpenAI-compatible server: LM Studio, vLLM, LiteLLM… |

Only the owner account can change AI settings. The API key is stored in your database and **never sent back to the browser**.

## 🔒 Privacy

- **Your data never leaves your server** unless you enable a cloud AI provider. Even then, only a compact summary of your recent cycle (no username, no password) is sent, and only when you use an AI feature.
- No analytics, no trackers, no external fonts or CDNs; everything is bundled.
- Passwords hashed with **argon2id**; signed, HTTP-only session cookies.
- **Export** everything as JSON at any time, or **delete** your account and all data in one tap.

## 🧠 How predictions work

<details>
<summary>Open the maths</summary>

- **Periods** are runs of bleeding days (spotting never starts a period); gaps of up to 2 days are merged.
- **Next cycle length** is a recency-weighted average of your last 6 cycles (15–90 days), blended with your configured default until 3 cycles exist.
- **Ovulation** uses the *3-over-6* basal temperature rule when you log BBT; otherwise *next period − luteal length*. Your luteal length is learned from BBT-confirmed cycles.
- **Fertile window** is ovulation −5 to +1 days (sperm survival plus egg lifespan).
- **Heads-ups:** a symptom is forecast when you logged it within ±1 day of today's position (aligned to cycle start *or* to your next period) in ≥2 past cycles and ≥50% of them.
- **Health flags:** cycles outside 21–35 days, variation >9 days, periods >7 days, or 7+ days late.

</details>

> ⚠️ **Bloomery is not a medical device and not a method of contraception.** Predictions are estimates. Talk to a healthcare professional about anything that worries you.

## 🏗️ Architecture

```mermaid
flowchart LR
  P["📱 Browser / PWA<br/>React 19 · Tailwind 4"] -- HTTPS --> A
  subgraph C["🐳 bloomery container (~60 MB)"]
    A["FastAPI"] --> E["Cycle engine<br/>predictions · feed"]
    A --> D[("SQLite<br/>/data/bloomery.db")]
  end
  A -. optional .-> L["🤖 LLM<br/>Claude · OpenAI · Ollama"]
```

| Layer | Tech |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 4, React Router 7, PWA (Workbox) |
| Backend | Python 3.13, FastAPI, SQLModel/SQLite (WAL), httpx |
| Image | Multi-stage, non-root, healthcheck, `linux/amd64` + `linux/arm64` |

Deeper docs: [Architecture](docs/ARCHITECTURE.md) · [Wiki](docs/WIKI.md) · [Plan](docs/PLAN.md) · API reference at `/api/docs` on your instance.

## ⚙️ Configuration

All optional. Set in `.env` or the container environment ([full list](.env.example)).

| Variable | Default | Purpose |
|---|---|---|
| `BLOOMERY_PORT` | `8420` | Host port (compose) |
| `BLOOMERY_ALLOW_REGISTRATION` | `auto` | `auto` = open until the first account · `true` · `false` |
| `BLOOMERY_SECURE_COOKIES` | `false` | Set `true` behind HTTPS |
| `BLOOMERY_SECRET_KEY` | auto-generated | Session signing key (stored in `/data/secret.key`) |
| `BLOOMERY_AI_*` | — | Optional AI defaults; the in-app settings override them |

**Backups:** copy the `/data` volume (`bloomery.db` + `secret.key`), or use in-app **Export**.

## 🛠️ Development

```bash
# backend
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest
.venv/bin/uvicorn app.main:app --reload          # http://localhost:8000
.venv/bin/python -m pytest -q

# frontend (proxies /api to :8000)
cd frontend && npm install && npm run dev         # http://localhost:5173

# demo data: user demo / demodemo
python scripts/seed_demo.py http://localhost:8000
```

## 🗺️ Roadmap

- [x] Predictions, calendar, logging, insights
- [x] AI assistant with in-app provider setup
- [x] Daily feed: heads-ups, milestones, recaps
- [x] Multi-arch image on GHCR
- [ ] Push notifications (period due, pill reminders)
- [ ] App lock (PIN / passkey)
- [ ] Import from Flo, Clue and Apple Health
- [ ] Pregnancy and perimenopause modes
- [ ] Partner sharing (read-only)
- [ ] Translations

Ideas and bug reports are welcome. [Open an issue](https://github.com/krugerhomeassistant/Bloomery/issues).

<div align="center">
<br>
<sub>Made with 🌸 for people who'd rather keep their cycle to themselves.</sub>
</div>
