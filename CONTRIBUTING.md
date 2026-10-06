# Contributing

Thanks for helping! Issues and pull requests are welcome. Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Develop

```bash
# backend (Python 3.13)
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt pytest
BLOOMERY_DATA_DIR=./data uvicorn app.main:app --reload --port 8000
# frontend (Node 24), proxies /api to :8000
cd frontend && npm ci && npm run dev
# demo data
python scripts/seed_demo.py http://localhost:8000
```

## Checks (same as CI)

```bash
pip install ruff && ruff check . && ruff format --check .
python -m pytest backend/tests
cd frontend && npm run build
# Home Assistant integration (Python 3.13)
pip install pytest-homeassistant-custom-component mypy
python -m pytest -c tests_ha/pytest.ini tests_ha --cov=custom_components.bloomery --cov-fail-under=95
mypy custom_components/bloomery
```

## Releasing (maintainers)

1. Note changes under `## [Unreleased]` in `CHANGELOG.md` as you go.
2. `python scripts/bump.py X.Y.Z` (updates backend, integration and frontend versions and the changelog).
3. `git commit -am "Release vX.Y.Z" && git push`

When a version that has no release yet reaches `main`, CI runs every check, publishes `ghcr.io/krugerhomeassistant/bloomery:X.Y.Z` (+ `X.Y`), then creates the `vX.Y.Z` tag and GitHub release with notes and `bloomery.zip`, which HACS offers as an update.
