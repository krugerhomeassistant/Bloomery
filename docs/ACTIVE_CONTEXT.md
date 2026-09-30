# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.3.0

## Current subtask
Publish to https://github.com/krugerhomeassistant/Bloomery with a flashy README + CI/GHCR.

## Last execution results
- README rewritten (hero, badges, screenshots, install, ZimaOS, AI, privacy, maths, architecture, roadmap).
- 20 screenshots (light+dark) in `docs/screenshots`, hero in `docs/assets/hero.jpg` (~1.3 MB total).
- `.github/workflows/ci.yml`: tests + build; multi-arch image to GHCR on push to main/tags.
- Living docs moved to `docs/`. Compose files use `ghcr.io/krugerhomeassistant/bloomery:latest`.

## Blockers
- Claude GitHub app has no access to `krugerhomeassistant/Bloomery` (user adjusting installation).

## Immediate next step
Retry `add_repo`, push `main`, watch CI, then user makes GHCR package public and picks a license.
