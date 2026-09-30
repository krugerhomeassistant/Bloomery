# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.3.0

## Current subtask
Proactive insights (done): daily feed on Today + after-log notes.

## Last execution results
- `backend/app/feed.py` + `GET /api/feed`; `PUT /api/logs` returns `note`; AI daily insight receives `heads_up_today`.
- Today shows feed cards (forecast / milestone / recap / tip) with detail sheet; saving a log shows a toast note.
- Tests 15/15. E2E: feed cards, tip sheet, toast OK; PMS-date feed returned bloating / tender breasts / mood swings forecasts.

## Blockers
None.

## Immediate next step
User: `docker compose up -d --build` and try it. Candidates: push notifications (Web Push), AI-written recap, GHCR image for ZimaOS.
