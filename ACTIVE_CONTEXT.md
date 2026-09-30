# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.1.0 (MVP complete)

## Current subtask
Delivered v0.1.0 to `E:\Projects\Personal\Bloomery`. Awaiting user run on host + reference-image feedback for visual tuning.

## Last execution results
- Backend: 11/11 pytest passing (engine, API flow, AI provider mocks).
- Frontend: `tsc` clean, Vite build OK (~107 kB gz JS).
- Docker image built & ran healthy; demo seeded; screenshots verified Today (fertile, light+dark), Log sheet, Calendar (+edit), Insights, Assistant (off + fake-LLM chat), insight sheet.

## Blockers
None. (Sandbox-only CA workaround documented in LESSONS #2.)

## Immediate next step
1. User: `cp .env.example .env && docker compose up -d --build` → http://localhost:8420.
2. Optionally enable Ollama (README).
3. Pick next backlog item from PLAN (suggest: reminders, Alembic, Flo data import).
