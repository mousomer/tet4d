# Release Checklist

## Code and tests

1. `ruff check .`
2. `ruff check . --select C901`
3. `python3 tools/validate_project_contracts.py`
4. `pytest -q`
5. `scripts/ci_check.sh`

## Documentation and RDS sync

1. `README.md` reflects current behavior.
2. `docs/FEATURE_MAP.md` updated for shipped features.
3. `docs/BACKLOG.md` updated for open/closed items.
4. `docs/rds/` updated for requirement changes.
5. `docs/CHANGELOG.md` has release notes.

## Artifacts and config

1. `config/schema/*.schema.json` validated as strict JSON.
2. `tests/replay/manifest.json` updated if replay protocol changes.
3. `assets/help/manifest.json` updated for help asset changes.
4. Migration docs updated if payload structure changes:
   - `docs/migrations/menu_settings.md`
- `docs/migrations/save_state.md`
