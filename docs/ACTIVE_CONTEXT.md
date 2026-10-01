# ACTIVE CONTEXT

**Date:** 2026-10-01 · **Version:** 1.2.0

## Current subtask
v1.2.0: per-type colour calendars, Platinum-rules HA integration, professional repo tooling and tag-driven releases.

## Last execution results
- Backend 26/26, HA 13/13 with 100% coverage, mypy strict clean, ruff clean, frontend build OK, live feed checked with the integration client.

## Blockers
- GitHub repo has no topics → HACS action fails `topics` until the user adds them (needs their login).

## Immediate next step
Push main, confirm CI, tag v1.2.0 → release + bloomery.zip; user updates via HACS. Optional: HACS default-store PR.
