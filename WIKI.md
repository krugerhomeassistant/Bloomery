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
- **AI daily insight**: `GET /api/ai/daily` → cached per user/day in `insightcache`; `?refresh=true` regenerates; falls back to rule text when AI off/errors.
- **AI chat**: `POST /api/ai/chat` → system prompt + JSON context + last 12 messages; history stored; `DELETE` clears.
- **Data**: export JSON (`/api/export`), import (merge; `replace` flag), delete account.

## Registration policy
`BLOOMERY_ALLOW_REGISTRATION=auto` (default): open until first user exists, then closed. `true` for a household instance.

## Tag catalog
Categories (ids are permanent): symptoms, mood, sex, discharge, digestion, activity, pill, other, ovulation_test, pregnancy_test. Flow is a separate field. Defined in `backend/app/catalog.py`, served at `/api/catalog`.

## UI map
Bottom nav: Today · Calendar · Insights · Assistant · Profile. Global LogDay sheet. Theme: Auto/Light/Dark (localStorage). Desktop shows centred phone-width column.

## Safety copy
Every AI prompt and Insights page states estimates ≠ medical advice ≠ contraception. Flags recommend a healthcare professional.
