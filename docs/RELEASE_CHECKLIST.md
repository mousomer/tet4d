# Release Checklist

## Code and tests

1. `ruff check .`
2. `ruff check . --select C901`
3. `python3 tools/governance/validate_project_contracts.py`
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
2. `config/project/policy/manifests/replay_manifest.json` updated if replay protocol changes.
3. `config/project/policy/manifests/help_assets_manifest.json` updated for help asset changes.
4. Migration docs updated if payload structure changes:
   - `docs/migrations/menu_settings.md`
   - `docs/migrations/save_state.md`

## Desktop packaging

1. Packaging spec is up to date: `packaging/pyinstaller/tet4d.spec`.
2. Packaging docs reflect current flow: `docs/RELEASE_INSTALLERS.md`.
3. Local package build is verified for the target release OS:
   - macOS: `bash packaging/scripts/build_macos.sh`
   - Linux: `bash packaging/scripts/build_linux.sh`
   - Windows: `./packaging/scripts/build_windows.ps1`
4. CI workflow exists and is green for package matrix: `.github/workflows/release-packaging.yml`.
