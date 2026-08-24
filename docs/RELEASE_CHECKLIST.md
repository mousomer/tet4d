# Release Checklist

## Code and tests

1. Run focused policy-routed Godot, native, deterministic, conformance, and
   integration checks.
2. Run `./scripts/check_keybinding_contract.sh`.
3. Run `./scripts/check_git_sanitation_repo.sh`.
4. Run `GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh`.
5. Run `CODEX_MODE=1 ./scripts/verify.sh`.

## Documentation and RDS sync

1. `README.md` and `godot/Tet4D.Godot/README.md` identify Godot as the current
   bounded 2D/3D/4D professional-core product shell.
2. `docs/rds/RDS_PACKAGING.md` and `docs/RELEASE_INSTALLERS.md` match the
   supported target and legacy-path disposition.
3. `docs/BACKLOG.md`, the professional programme, task contract, and
   `CURRENT_STATE.md` distinguish automatically verified, human accepted, and
   deferred release state.
4. `docs/CHANGELOG.md` records release-path changes.
5. Replay, settings, or setup migration docs change only if their payload
   contracts changed.

## Artifacts and config

1. `pyproject.toml`, `project.godot`, and `export_presets.cfg` agree on product
   version and name.
2. The preset uses `io.github.mousomer.tet4d`, macOS 13 minimums, Universal 2,
   release mode, and excludes the test tree.
3. The release framework and packaged framework both contain `x86_64` and
   `arm64` slices.
4. The app contains its executable, release GDExtension, PCK/resources, theme,
   fonts, assets, and required metadata.
5. The app excludes user data, editor state, source-tree dependencies,
   temporary evidence, and machine-local paths.
6. `codesign --verify --deep --strict` passes for the app.

## Current-platform package

1. Run `GODOT_BIN=/path/to/Godot packaging/godot/build_macos.sh`.
2. Confirm its integrated `packaging/godot/smoke_macos.sh` two-user
   outside-tree smoke passes.
3. Inspect the produced app and ZIP.
4. Extract/copy the candidate outside the repository for real-window review.
5. Launch twice with separate clean user-data roots.
6. Exercise persisted valid and malformed settings/setup values.
7. Confirm preferences persist while transient view and live session state,
   including Hold, do not.
8. Complete the exported 2D/3D/4D, Hold/NEXT/Ghost, replay, setup, Settings,
   focus/modal, resize, accessibility, warning, and performance matrix.
9. Record independent human acceptance before declaring Stage 54G complete.

## Platform and legacy truth

1. Report macOS as the only current Godot professional-core release target.
2. Report Linux and Windows Godot support as development-configured and not
   runtime-verified for this release.
3. Report Python/PyInstaller `.dmg`, `.deb`, and `.msi` builders as retained
   legacy packaging, not current release evidence.
4. Report ad-hoc signing and absent notarization; do not imply public
   Gatekeeper-ready distribution.
