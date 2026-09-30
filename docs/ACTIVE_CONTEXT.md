# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.5.0

## Current subtask
User runs Bloomery on ZimaOS, reachable only via Tailscale (private tailnet, not public internet) → no further hardening needed; v0.5.0 throttle/headers kept as harmless defaults. Shipped v0.5.0: security hardening + Flo/Clue/CSV import.

## Last execution results
- Per-IP login throttle, security headers, `no-store` on API; importer (`app/importers.py`) + `POST /api/import/other`; Profile import auto-routes.
- Tests 19/19; importer self-check passes.

## Blockers
None. AI + notifications not yet tested by user on a real provider.

## Immediate next step
User: update container, test AI (Claude key) + ntfy. Candidates next: app lock (PIN), AI-written recap, Apple Health import, Alembic before first schema change.
