# WIKI — Bloomery

## Purpose
Self-hosted, Docker-based menstrual cycle tracker modelled on the look & feel of Flo (soft pink UI, cycle circle, chip-based daily logging, insight cards) but private: all data in a local SQLite file, optional local LLM.

## Glossary
| Term | Meaning |
|---|---|
| Period | Run of bleeding days (light/medium/heavy); gaps ≤2 days merged |
| Cycle | Period start → day before next period start |
| Cycle day (CD) | 1-based day within cycle |
| Segment | Engine object for one cycle (actual or predicted): start, length, period_end, ovulation, fertile window |
| Fertile window | ovulation−5 … ovulation+1 (clamped after period end) |
| Luteal phase | ovulation → next period; default 14 d, learned from BBT |
| BBT | Basal body temperature (°C stored) |
| Thermal shift | "3 over 6" rule: 3 consecutive temps > max of prior 6, one ≥ +0.2 °C → ovulation = day before first high temp |
| Phase | menstrual · follicular · fertile · ovulation · luteal |
| Chance | pregnancy chance label: high (ov−2…ov), medium (ov−5…ov−3, ov+1), low otherwise |
| Flag | rule-based health-check message (short/long cycles, variability >9 d, period >7 d, ≥7 d late) |

## Prediction rules (`backend/app/cycles.py`)
- Valid cycle lengths: 15–90 d. Predicted cycle = linear-recency-weighted mean of last 6; with <3 cycles blended with profile default (weight 2).
- Predicted period length = same blend over completed periods, clamped 1–12.
- Uncertainty = ceil(pstdev(last 6 cycles)) clamped 1–7 (2 if <2 cycles).
- Regularity (≥3 cycles): spread ≤7 regular · ≤9 somewhat irregular · else irregular.
- Current cycle length = max(predicted, days elapsed+1) → late cycles push future predictions.
- Status states: `empty`, `period` ("Period · Day N"), `fertile` ("Ovulation in N"), `cycle` ("Period in N"), `due` (expected today), `late` ("Period late by N").
- 12 future segments are generated for the calendar.

## Workflows
- **Onboarding**: goal → last period start (or unknown) → period length → cycle length → birth year → `PUT /api/profile` + `POST /api/period/start`.
- **Log period (Today)**: confirm sheet → `POST /api/period/start {day}` fills predicted_period days as `medium` (Flo behaviour); trim via calendar edit or `POST /api/period/end`.
- **Calendar edit**: toggle days → `PUT /api/period {add, remove}` (diff vs current). Editable up to today+14.
- **Daily log**: global sheet (`openLog(date)`), day arrows, search filters chips, "none"/"fine" options are exclusive → `PUT /api/logs/{day}`; empty log deletes row.
- **Insights**: `GET /api/insights` → stats, flags, symptom patterns (tag ≥3 logs and ≥60% in one phase), BBT (current cycle), weight (180 d).
- **Daily feed** (`GET /api/feed`, `app/feed.py`, rule-based, no AI): milestones (period day 1, fertile window start, ovulation, period in 1–3 d, late) · recap (first 4 days of a cycle: last cycle length vs avg, period length, top 3 tags) · forecasts (tag from symptoms/mood/digestion/discharge logged within ±1 day of today's position — aligned to cycle start OR to next period, best wins — in ≥2 past cycles and ≥50% of cycles with logs; skipped if already logged today; max 3; includes a symptom tip) · phase tip (rotates daily by date). Forecast titles are passed to the AI daily insight as `heads_up_today`.
- **After-log note**: `PUT /api/logs/{day}` returns `note` for newly added tags only — "X during your period matches your usual pattern" (from symptom patterns) or a symptom tip; UI shows it as a toast (≥10 s, scales with length, explicit close) and the latest note is stored in `setting` `lognote:<uid>` {day,text} and returned as the first `/api/feed` card (kind `note`, 💬 "About today's log") for that day only.
- **AI daily insight**: `GET /api/ai/daily` → cached per user/day in `insightcache`; `?refresh=true` regenerates; falls back to rule text when AI off/errors.
- **AI chat**: `POST /api/ai/chat` → system prompt + JSON context + last 12 messages; history stored; `DELETE` clears. `POST /api/ai/chat/stream` = same but streams plain-text chunks (provider SSE parsed server-side); saved to history when the stream ends; `<think>` blocks hidden client-side and stripped before saving.
- **AI setup (in-app)**: Profile → AI assistant sheet → `GET/PUT /api/ai/config`, `POST /api/ai/config/test` (admin only). Providers: anthropic (Haiku 4.5 default), openai (gpt-5-mini; uses `max_completion_tokens`, no temperature), openrouter (`openrouter/auto`), ollama, custom. Blank model/URL = provider default; blank key = keep saved key (same provider only).
- **Notifications** (`app/notify.py`, `routers/notifications.py`): per-user config in `setting` key `notify:<uid>` (JSON: url, time HH:MM, tz from browser, kinds ⊂ milestone/forecast/recap/tip/pill, last-sent date). Background task (`lifespan`) ticks every 60 s; sends once per local day after `time`; marks sent before sending (no retry storms). Payload by URL: host contains `ntfy` → JSON publish to root `{topic,title,message,tags}`; `discord` → `{content}`; else `{title,message,priority:5}` (Gotify, HA webhook, generic). `GET/PUT /api/notifications`, `POST /api/notifications/test`.
- **AI cycle recap** (`GET /api/ai/recap?start=`): per-cycle context (`ai.recap_context`: cycle stats, averages, recent lengths, per-day logs w/ cycle day + phase + BBT) + `RECAP_PROMPT` (3–5 bullets + "For next cycle:"). Completed cycles cached in `setting` key `recap:<uid>:<start>`; `?refresh=true` rewrites. Rules fallback = `feed.cycle_summary`. UI: Insights → Cycle history row → RecapSheet; Today recap card opens it too.
- **Apple Health import**: browser streams `export.xml` (`frontend/src/appleHealth.ts`, TextDecoderStream, regex over complete `<Record>` tags up to last `<`), keeps 22 cycle types, POSTs `{format:"apple_health", records:[[type,date,value,unit]]}`. Server `importers._apple` maps flow (value suffix Light/Medium/Heavy/Unspecified; works for `MenstrualFlow*` and iOS 18 `VaginalBleeding*`), IntermenstrualBleeding→spotting, BBT (degF→°C), CervicalMucusQuality→discharge, Ovulation/Pregnancy tests, 16 symptoms (severity NotPresent skipped). Merge: flow never overwrites bleeding; tags union; temperature only if empty. `.zip` rejected with "unzip first".
- **Import from other apps** (`app/importers.py`, `POST /api/import/other {content}`): auto-detects Flo JSON (`operationalData.cycles[].period_start_date/_end_date` → medium), Clue `.cluedata` (`data[].day` + `period`), CSV (date + period/flow/bleeding[.value] words or 0–3, or start/end). Periods only; never overwrites existing bleeding days; ambiguous `dd/mm` vs `mm/dd` tries day-first.
- **Security**: per-IP login throttle (10 fails/15 min → 429; in-memory; per-IP only so strangers can't lock the owner out); security headers middleware; `/api/*` `Cache-Control: no-store`.
- **Life stages** (`cycles.py` Profile.mode/lmp, `deps.life_stage`, `PUT /api/life-stage`): `cycle` (default), `pregnancy` (LMP = chosen date or last logged period; due = LMP+280; `overview.pregnancy` {week, day, due, days_left, trimester, size}; predictions/phases/flags off; feed = baby size, countdown, trimester tip), `perimenopause` (±≥5 d uncertainty; "Days since period"; flags: no period ≥60 d, 12 months = menopause marker, bleeding after → doctor). Logging a positive pregnancy test suggests pregnancy mode. Cycle history is untouched when switching.
- **App lock** (`routers/auth.py`, `components/LockScreen.tsx`): optional 4-digit PIN, `/api/auth/me` returns `pin_set`. Lock overlay shows only when the device was away longer than its "Ask for PIN after" choice (1 min–4 h, default 15; `lockAfter`/`lastActive` in localStorage, `state.tsx` helpers); fresh password login is unlocked. Setting/removing needs the account password. 10 wrong PINs (in-memory counter) end the session → password login. Client-side overlay: guards a phone left unlocked, not a stolen session cookie.
- **Releases**: semver; `CHANGELOG.md` `[Unreleased]` → `python scripts/bump.py X.Y.Z` (backend `app/__init__.py`, integration manifest, frontend package files, changelog) → commit, push to main. CI `version` job sees a version without a release (or a pushed `vX.Y.Z` tag), verifies all versions agree, pushes `ghcr.io/…/bloomery:X.Y.Z` + `X.Y`, creates tag + GitHub release (notes from changelog, `bloomery.zip` for HACS).
- **Home Assistant calendars**: integration has Periods (#FF4A7D), Fertile windows (#3CC4BB), Ovulation (#7C5CE0) calendar entities from feed `events`; colours changeable per calendar (HA 2026.2+). ICS `?type=` gives one feed per kind for other calendar apps. HACS store icon is a HACS bug (hacs/integration#5223); HA itself shows the bundled icon.
- **Home Assistant integration** (`custom_components/bloomery`): installed via HACS custom repository; config flow takes the feed URL (`…/api/ha/<token>`), polls it with `tz=<HA time zone>` every 15 min + 00:00:10. Entities: status, cycle_day, phase (enum), days_until_period, next_period, ovulation, pregnancy_chance, life_stage, pregnancy_week, due_date, cycle_length/period_length (diagnostic); binary period, fertile_window. Entry unique id = `<host>_<user_id>` so a regenerated token is handled with *Reconfigure*. Tests: `tests_ha/` (Python 3.13, `pytest -c tests_ha/pytest.ini tests_ha`).
- **Home Assistant / calendar** (`routers/share.py`): token kind `ha` (`ha:<token>`, `haof:<uid>`). `GET /api/ha/{token}?tz=<IANA>` flat JSON (state, cycle_day, phase, in_period, fertile, days_until_period, next_period, ovulation…); `GET /api/ha/{token}/calendar.ics` all-day events (Period / Predicted period / Fertile window / Ovulation, last 60 days + predictions). Profile generates the HA `rest:` YAML. HA token can't open the partner page and vice versa.
- **Partner sharing** (`routers/share.py`): owner `GET/POST/DELETE /api/tokens/share` (POST regenerates → old link 404s); public `GET /api/share/{token}` returns name, status, current cycle, next period, phase tip for partner, 35 days of cycle markers only (period/predicted/fertile/ovulation). Tokens in `setting` (`share:<token>`→uid, `shareof:<uid>`→token). Frontend: `main.tsx` renders `SharePage` for `/share/*` without the auth gate. Copy button only in secure contexts (clipboard API needs HTTPS); link text is `select-all`.
- **Learned vs default settings**: Profile shows defaults plus "using N" when the engine's learned value differs (`/api/cycle/overview` predicted_cycle_length / predicted_period_length / luteal_length).
- **Data**: export JSON (`/api/export`), import (merge; `replace` flag), delete account.

## Registration policy
`BLOOMERY_ALLOW_REGISTRATION=auto` (default): open until first user exists, then closed. `true` for a household instance.

## Tag catalog
Categories (ids are permanent): symptoms, mood, sex, discharge, digestion, activity, pill, other, ovulation_test, pregnancy_test. Flow is a separate field. Defined in `backend/app/catalog.py`, served at `/api/catalog`.

## UI map
Bottom nav: Today · Calendar · Insights · Assistant · Profile. Global LogDay sheet. Theme: Auto/Light/Dark (localStorage). Desktop shows centred phone-width column.

## Safety copy
Every AI prompt and Insights page states estimates ≠ medical advice ≠ contraception. Flags recommend a healthcare professional.
