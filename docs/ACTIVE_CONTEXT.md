# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 1.1.0

## Current subtask
v1.1.0: HA YAML replaced by HACS custom integration (`custom_components/bloomery`); ICS calendar kept; app lock relaxed (default 15 min away, per-device choice, 10 tries).

## Last execution results
- Backend 26/26, HA integration test 1/1 (HA 2026.2). E2E: no lock after login/reload; lock after simulated 16 min away; Profile HA section OK.

## Blockers
None. User to install integration via HACS and confirm.

## Immediate next step
Wait for feedback. Backlog: symptom predictions, i18n, Alembic, passkeys (HTTPS), SQLCipher.
