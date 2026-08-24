# Desktop Packaging RDS

Status: Active v0.3 (Stage 54G candidate)
Author: Omer + Codex
Date: 2026-08-24
Scope: current Godot professional-core export plus retained legacy Python packaging.

## 1. Purpose

Define the release path that distributes the accepted Godot 2D/3D/4D product
without a repository checkout, Python runtime, or developer-only native build
tree. Keep the earlier Python/PyInstaller installers identifiable as a retained
legacy product path rather than allowing them to masquerade as the current
professional-core release.

## 2. Current supported release path

The Stage 54G release candidate is:

- product: `Tet4D`;
- version authority: `pyproject.toml` (`0.7.5` for this candidate);
- engine: the exact Godot 4.7.1 stable build pinned in
  `config/project/policy_pack.json`;
- platform: macOS 13 or newer;
- architecture: Universal 2 (`x86_64` and `arm64`);
- package: an ad-hoc-signed `.app` bundle and a ZIP containing that bundle;
- bundle identifier: `io.github.mousomer.tet4d`;
- entry point: `res://scenes/trace_replay.tscn`; and
- persistent data root: the platform application-data directory named `Tet4D`,
  containing `shell_settings.json` and `game_setup.json`.

The exported product must contain the release GDExtension framework, scenes,
scripts, theme resources, fonts, configuration registries, help assets, and
copied replay bundle required by the product. It must exclude the Godot test
tree, editor state, developer user data, source-tree build products, and
machine-local paths.

The current canonical files are:

1. `godot/Tet4D.Godot/export_presets.cfg`;
2. `packaging/godot/build_macos.sh`;
3. `packaging/godot/smoke_macos.sh`;
4. `scripts/build_godot_tet4d_core.sh`;
5. `godot/Tet4D.Godot/addons/tet4d_core/tet4d_core.gdextension`;
6. `.github/workflows/release-packaging.yml`; and
7. `docs/RELEASE_INSTALLERS.md` and `docs/RELEASE_CHECKLIST.md`.

## 3. Native release boundary

1. macOS release builds use `template_release`, `arch=universal`, and an
   explicit `macos_deployment_target=13.0`.
2. The exported app must select
   `libtet4d_core.macos.template_release.framework` through the checked-in
   GDExtension descriptor.
3. Both the source release framework and packaged framework must contain
   `x86_64` and `arm64` slices.
4. The app must load the GDExtension without an absolute path or current
   working-directory dependency.
5. Debug artifacts remain development-only and are not valid release evidence.

## 4. Other Godot platform declarations

The GDExtension descriptor names Linux and Windows debug/release artifact
locations so those platforms can be developed and verified incrementally.
There is no checked-in Godot export preset, current Godot installer, or Stage
54G runtime acceptance for Linux or Windows. They are therefore
development-configured targets, not supported professional-core release
targets. Static descriptor or CI evidence must not be reported as runtime
success.

## 5. Legacy Python installer path

The following path is retained for the earlier Python/pygame product and its
historical releases:

- `packaging/pyinstaller/tet4d.spec`;
- `packaging/scripts/build_macos.sh`;
- `packaging/scripts/build_linux.sh`;
- `packaging/scripts/build_windows.ps1`; and
- `.dmg`, `.deb`, and `.msi` outputs described by prior changelog entries.

This path embeds Python and launches `front.py`. It is not the Stage 54G Godot
professional-core release path, is not required to close that gate, and must
not be attached by the current Godot release workflow. Repairs to retained
legacy packaging require a separate task.

## 6. Acceptance criteria

1. The exact pinned editor and matching official export template are used.
2. `packaging/godot/build_macos.sh` creates the `.app` and ZIP from a clean
   release GDExtension build and calls `packaging/godot/smoke_macos.sh` for
   two isolated outside-tree launches.
3. Bundle name, identifier, version, minimum OS, executable, signature, and
   universal architectures are validated from the artifact.
4. The app contains the required native framework and runtime resources.
5. The exported app launches outside the repository with isolated clean user
   data and no current-working-directory dependency.
6. A representative packaged 2D/3D/4D session, including Hold, NEXT, and
   Ghost, passes final manual release-candidate review.
7. Normal startup emits no release-blocking resource, parser, persistence, or
   GDExtension warning/error.
8. The current release workflow uploads only the Godot macOS ZIP for this
   supported path.
9. Linux, Windows, signing/notarization, and legacy Python installers are
   reported with their exact verification limits.
