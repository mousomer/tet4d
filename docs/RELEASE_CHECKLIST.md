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
   `packaging/godot/validate_windows_package.py` passes. The production MSVC
   native build explicitly uses `debug_symbols=no` and trims the repository
   root from runtime `__FILE__` diagnostics; no PDB, native debug record, or
   checkout-bound runtime source path is part of the release payload.
8. `packaging/godot/validate_android_export.py` passes, and where an APK was
   built, `packaging/godot/validate_android_package.py` passes and the APK is
   signed. The APK contains Godot 4.7.2's `assets/assets.sparsepck` metadata and
   individually stored required project assets; it is not required to contain
   a conventional `.pck` member.
9. `packaging/godot/validate_ipados_project.py` passes against the exported
   Xcode project with explicit `--artifact-mode configuration` or
   `--artifact-mode release`. Configuration mode must have the deliberately
   reduced descriptor and no native framework; release mode must have the
   complete iOS descriptor and release xcframework at Godot's canonical
   `Tet4DDesigner/dylibs/addons/tet4d_core/bin/` path. The generated export
   method must be `development` in both modes. Release validation must inspect
   the contained binaries, require an `arm64` device slice and `x86_64`
   simulator slice, and reject missing godot-cpp implementation symbols or
   XCFramework metadata that disagrees with the archive architectures.
10. No keystore, certificate, provisioning profile, or other signing secret is
    committed on any platform.
11. Reconcile `pyproject.toml`, `project.godot`, all live macOS/Windows/Android/
    iPadOS export version fields, and the Android version code before a 0.9.0
    candidate. The Godot engine remains the pinned 4.7.2 release.
12. Dispatch `release-packaging.yml` manually with one exact lowercase
    40-character `source_sha`. Its `release_scope` defaults to `current_all`,
    which selects the full registered matrix; an operator may explicitly select
    a validated submatrix with a comma-separated `consumer_id` list. Confirm
    every selected package job checked out that SHA and every unselected package
    job was intentionally skipped.
13. Validate the generated `tet4d.release-manifest.v2`: its canonical scope,
    consumer/product/platform identity, filenames, byte counts, SHA-256 values,
    version, and source SHA must exactly describe the selected package bytes.
    It must reject missing selected packages and any extra unselected registered
    package. The transitional Designer Android artifact and transitional
    Designer iPadOS artifact remain technical evidence only; neither promotes
    Designer support or substitutes for a Godot game package.
14. Confirm the candidate creates or verifies `v<version>` at that exact source
    SHA and creates a **draft** release only. It must not repoint a tag, clobber
    an asset, publish automatically, or combine bytes from a different run.
15. Dispatch `publish-release.yml` manually only after draft inspection. It
    must build and upload nothing; it must download the existing draft assets,
    validate the exact tag/source relationship, manifest checksums and byte
    counts, and the complete asset set before changing the draft to published.

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

1. Report macOS as the implemented Godot game release target; do not rename
   its game-identity ZIP as Designer evidence.
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
    The current Designer-identity artifact is transitional and does not satisfy
    either Designer target support or Godot game/Android implementation.
3b. For iPadOS, run `packaging/godot/build_ipados.sh`, and report the build
    result, the signing status, and whether evidence came from the `x86_64`
    simulator or a physical iPad. Confirm the final self-contained archives
    preserve the `arm64` device and `x86_64` simulator contract and that the
    unsigned simulator build reaches the final link. Simulator compilation or
    keyboard input is not physical-iPad keyboard acceptance.
    The current Designer-identity project is the `legacy_designer_ipados`
    transitional artifact; its successful technical repair does not implement
    the required Godot game/iPadOS target.
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
7. Do not publish unless the manual candidate and separate publication gates
   both prove the exact tag/source/manifest asset identity. Candidate assembly
   creates a draft only; draft inspection precedes publication.
