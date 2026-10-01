## What & why

## Checklist
- [ ] `ruff check . && ruff format --check .`
- [ ] Backend tests pass (`python -m pytest backend/tests`)
- [ ] Integration changes: `pytest -c tests_ha/pytest.ini tests_ha --cov=custom_components.bloomery` ≥ 95% and `mypy custom_components/bloomery`
- [ ] User-facing change noted under `[Unreleased]` in `CHANGELOG.md`
