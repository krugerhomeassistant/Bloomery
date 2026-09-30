# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.4.0

## Current subtask
Notifications (ntfy/Gotify/HA/Discord) + MIT license — done. User installing on ZimaOS.

## Last execution results
- `app/notify.py` scheduler + `/api/notifications` (GET/PUT/test); Profile → Notifications sheet.
- E2E: Send test posted `{"title":"💊 Pill reminder (+1 more)", ...}` to local webhook; settings persisted with browser tz.
- Tests 17/17. MIT LICENSE added.

## Blockers
- GHCR package still private → ZimaOS pull fails ("5 mirror methods"). User must set package visibility Public.

## Immediate next step
Confirm anonymous GHCR pull works; then candidates: Flo/Clue import, app lock (PIN), AI-written recap, Alembic before any schema change.
