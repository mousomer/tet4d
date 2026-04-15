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
   - includes hidden imports for lazy `tet4d.ai.playbot.*` modules used by
     frozen launcher/setup flows
2. Packaging docs reflect current flow: `docs/RELEASE_INSTALLERS.md`.
3. Local installer build is verified for the target release OS:
   - macOS: `bash packaging/scripts/build_macos.sh` (`.dmg`)
   - Linux: `bash packaging/scripts/build_linux.sh` (`.deb`)
   - Windows: `./packaging/scripts/build_windows.ps1` (`.msi`)
   - each packaging script must pass its packaged runtime
     `--runtime-smoke-check` before emitting the installer artifact
   - Windows packaging fails if the expected `.msi` is missing or if any
     external `*.cab` is emitted under `build/packaging/windows`
   - Windows release artifacts remain a single generated `.msi` without any
     sidecar CAB upload
4. CI workflow is green for the installer matrix and packaged runtime smoke
   checks: `.github/workflows/release-packaging.yml`.
5. The tag-triggered release workflow attached the generated installers to the GitHub release.
