# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.3.0

## Current subtask
Repo published: https://github.com/krugerhomeassistant/Bloomery

## Last execution results
- `main` pushed; CI run 36705705457 green: tests + multi-arch image `ghcr.io/krugerhomeassistant/bloomery:latest`.
- Anonymous pull returns 403 → GHCR package is private (GitHub default).
- Local folder synced (docs moved to `docs/`); `.github/workflows/ci.yml` could not be written to the device (protected path) → user gets it via `git pull`.

## Blockers
- User: make GHCR package public; choose a license.

## Immediate next step
User: package → Settings → Change visibility → Public. Then ZimaOS import of `docker-compose.zimaos.yml` works without building.
