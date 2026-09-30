# ACTIVE CONTEXT

**Date:** 2026-09-30 · **Version:** 0.2.0

## Current subtask
In-app AI configuration (done). User tested v0.1 locally via Docker Desktop and liked it.

## Last execution results
- AI provider/key/model now set in Profile → AI assistant (admin = first account); stored in `setting` table; env still works as default.
- Tests 12/12. E2E via Playwright: real Anthropic endpoint returned clean "401: API key is invalid." for a bogus key; custom provider Test → Save → chat OK.
- Fixed: key no longer carried across provider switch.

## Blockers
None.

## Immediate next step
User: `docker compose up -d --build`, Profile → AI assistant → Claude + key → Test → Save. Then build/save/load image to ZimaOS (README).
