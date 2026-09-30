# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.6.0

## Current subtask
Shipped AI cycle recap + Apple Health import. Deployment: ZimaOS, Tailscale-only (no extra hardening).

## Last execution results
- `/api/ai/recap` (cached per completed cycle) + RecapSheet; Apple Health streaming import (`appleHealth.ts` + `importers._apple`).
- Tests 21/21. E2E OK (synthetic export, fake LLM).

## Blockers
None. Real-provider AI, notifications, and real Apple/Clue exports still untested by user.

## Immediate next step
User updates container and tests. Remaining backlog: app lock (PIN), pregnancy/perimenopause modes, partner sharing, i18n, Alembic before first schema change.
