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
2. `docs/rds/RDS_PACKAGING.md` and `docs/RELEASE_INSTALLERS.md` match each
   supported product family and its precise evidence level.
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
7. The Windows Designer ZIP contains only its EXE, PCK, and release DLL, and
   `packaging/godot/validate_windows_package.py` passes.
8. `packaging/godot/validate_android_export.py` passes, and where an APK was
   built, `packaging/godot/validate_android_package.py` passes and the APK is
   signed.
9. `packaging/godot/validate_ipados_project.py` passes against the exported
   Xcode project with explicit `--artifact-mode configuration` or
   `--artifact-mode release`. Configuration mode must have the deliberately
   reduced descriptor and no native framework; release mode must have the
   complete iOS descriptor and release xcframework. The generated export
   method must be `development` in both modes.
10. No keystore, certificate, provisioning profile, or other signing secret is
    committed on any platform.
11. Run `python tools/release/release_metadata.py validate-tag --tag <tag>` and
    confirm the normalized tag exactly matches `pyproject.toml`; do not publish
    a historical or proposed version label that disagrees with project truth.
12. Confirm the unified workflow checked out one exact source SHA in all seven
    package jobs and generated `tet4d-release-<version>-manifest.json` only
    after every package passed.
13. Verify the manifest names all three Python installers and all four Godot
    Designer artifacts, records their SHA-256 values, and describes iPadOS as
    an unsigned simulator-compiled Xcode project without device acceptance.

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

## Platform and product-family truth

1. Report macOS as the accepted Godot professional-core release target.
2. Report Windows x86-64 as a structurally validated portable Designer
   candidate, including whether native CI and direct clean-machine launch ran.
3. For Windows, run `packaging/godot/build_windows.sh`, inspect the three-file
   ZIP, and complete `docs/plans/design_evaluation_laboratory_acceptance.md`
   before any runtime-support claim.
3a. For Android, run `packaging/godot/build_android.sh`, and report whether the
    APK itself was built or only the export configuration was validated. State
    the evidence level exactly: automated InputMap tests, emulator keyboard
    testing, and real physical Android keyboard testing are three different
    claims and the weaker may not be reported as the stronger.
3b. For iPadOS, run `packaging/godot/build_ipados.sh`, and report the build
    result, the signing status, and whether evidence came from the simulator or
    a physical iPad. Simulator keyboard input is not physical-iPad keyboard
    acceptance.
3c. Rebuild every platform artifact after any shared Design Laboratory change,
    and record a SHA-256 for each produced artifact with its exact class.
    An iPad configuration-export checksum is not a release checksum. A Windows
    ZIP SHA identifies the exact timestamp-bearing ZIP; do not call that ZIP
    bit-reproducible unless its metadata is normalized.
4. Report Linux Godot support as development-configured and not
   runtime-verified for this release.
5. For Python/PyInstaller, run the existing `.dmg`, `.deb`, and `.msi`
   builders on real macOS, Linux, and Windows runners from one integrated SHA.
   Record version and SHA-256, install or mount, launch the installed app from
   outside the checkout with isolated user state, and uninstall where
   applicable. Report unproven platforms as pending and do not add the family
   to the unified release workflow until all three pass.
6. Report ad-hoc signing and absent notarization; do not imply public
   Gatekeeper-ready distribution.
7. Do not create or upload a tagged release unless the tag/project-version
   invariant passes. A manual dispatch proves packaging and manifest assembly
   without publishing a release.
