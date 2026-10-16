#!/usr/bin/env sh
# Same gates as CI (lint, format, backend tests, i18n + build). Install as a hook: ln -sf ../../scripts/check.sh .git/hooks/pre-push
set -e
cd "$(dirname "$0")/.."
ruff check . && ruff format --check .
(cd backend && python -m pytest -q)
(cd frontend && npm run i18n && npm run build)
