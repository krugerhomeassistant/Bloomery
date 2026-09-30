# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.1.0

## Current subtask
ZimaOS deployment support + memory sizing for a 0.5–1 GB free-RAM home server.

## Last execution results
- Added `backend/entrypoint.sh` (chown bind mount → drop to uid 10001); tested with root-owned mount: OK.
- Added `docker-compose.zimaos.yml` (image-only, /DATA/AppData/bloomery, mem_limit 256m, x-casaos metadata).
- Measured: 60 MiB idle, 72 MiB after 600 concurrent requests under 256 MiB cap; image 274 MB.
- README: ZimaOS section (build on PC → docker save/scp/load → dashboard Import).
- 11/11 tests pass.

## Blockers
None. Ollama not viable on user's server (RAM) → cloud AI or none.

## Immediate next step
User deploys on ZimaOS. Then: GHCR multi-arch image (removes manual build), reminders, Alembic.
