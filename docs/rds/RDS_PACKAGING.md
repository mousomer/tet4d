# Desktop Packaging RDS

Status: Active v0.5 (Stage 54G accepted; Stage 54F-5 Windows, Android tablet,
and iPadOS Design Laboratory candidates. Scope now covers desktop and tablet
distribution; the document title is a governed identity token and is retained.)
Author: Omer + Codex
Date: 2026-08-30
Scope: current Godot product exports plus the active Python/PyInstaller product
family.

## 1. Purpose

Define the release paths that distribute the accepted Godot 2D/3D/4D product
and the active Python product without a repository checkout or developer-only
build tree. Product-family names and evidence remain explicit: a Python bundle
embeds its own runtime and must never masquerade as the Godot professional-core
artifact, while neither family may claim a platform it did not build and test.

## 2. Current supported release path

The Stage 54G release candidate is:

- product: `Tet4D`;
- version authority: `pyproject.toml` (`0.7.5` for this candidate);
- engine: the exact Godot 4.7.2 stable build pinned in
  `config/project/policy_pack.json`;
- platform: macOS 13 or newer;
- architecture: Universal 2 (`x86_64` and `arm64`);
- package: an ad-hoc-signed `.app` bundle and a ZIP containing that bundle;
- bundle identifier: `io.github.mousomer.tet4d`;
- entry point: `res://scenes/trace_replay.tscn`; and
- persistent data root: the platform application-data directory named `Tet4D`,
  containing `shell_settings.json` and `game_setup.json`.

The accepted macOS product remains unchanged. Stage 54F-5 additionally
defines a structurally validated Windows x86-64 portable Design Laboratory
candidate named `Tet4D Designer`. It uses the same Godot product shell and
entry point, adds the deterministic design-evaluation workflow, and contains
no Python runtime or editor. The current Windows deliverable is a ZIP with
`Tet4DDesigner.exe`, `Tet4DDesigner.pck`, and
`libtet4d_core.windows.template_release.x86_64.dll`. Extracting the ZIP is the
installation operation and deleting the extracted directory is uninstallation;
it intentionally creates no Start Menu item, desktop shortcut, or registry
uninstaller.

The Windows artifact has passed local cross-build, PE/resource/package
validation, and the laboratory's local Godot tests on macOS. Direct launch on
a clean Windows machine remains pending and must not be inferred from those
results. The Windows CI job performs the native Windows build, focused
laboratory suite, package validation, and a bounded launch of the packaged
executable when the workflow is run.

The exact locally validated ZIP selected for clean-machine evaluation is stored
outside Git as an Actions artifact, release asset, or canonical candidate
asset. Reproducible build outputs remain ignored under `artifacts/godot/`; a
new candidate must update its checksum record and pass the repository validator
before publication. Asset availability does not promote Windows runtime
acceptance.

The same Design Laboratory additionally ships to two tablet targets, both
intended for landscape use with a physical keyboard rather than as touch-first
games:

- **Android tablet.** An arm64 APK supporting only large and extra-large
  screens, built from the prebuilt Godot export template with no Gradle build
  entering the repository. Because Godot `user://` is application private on
  Android, nomination additionally writes a portable archive and offers it to
  the system document picker.
- **iPadOS.** A Godot-generated Xcode project for the iPad device family, built
  and signed through Xcode. `UIFileSharingEnabled` and
  `LSSupportsOpeningDocumentsInPlace` expose the Documents directory in the
  Files app so a nominated bundle is retrievable from the device.

Both are configuration-validated on any host through the exported resource pack
or Xcode project. Neither artifact may be reported as device-accepted, and
automated InputMap tests, emulator or simulator testing, and real physical
keyboard testing must be reported as the three distinct claims they are.

The exported product must contain the release GDExtension framework, scenes,
scripts, theme resources, fonts, configuration registries, help assets, and
copied replay bundle required by the product. It must exclude the Godot test
tree, editor state, developer user data, source-tree build products, and
machine-local paths.

The current canonical files are:

1. `godot/Tet4D.Godot/export_presets.cfg`;
2. `packaging/godot/build_macos.sh`;
3. `packaging/godot/smoke_macos.sh`;
4. `packaging/godot/build_windows.sh`;
5. `packaging/godot/validate_windows_package.py`;
6. `scripts/build_godot_tet4d_core.sh`;
7. `godot/Tet4D.Godot/addons/tet4d_core/tet4d_core.gdextension`;
8. `.github/workflows/release-packaging.yml`; and
9. `release-candidates/windows/README.md`; and
10. `docs/RELEASE_INSTALLERS.md` and `docs/RELEASE_CHECKLIST.md`.

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

## 4. Windows design-laboratory boundary

1. Windows release builds use `template_release`, `arch=x86_64`, the exact
   Godot 4.7.2 editor/templates, and a MinGW cross-toolchain on non-Windows
   builders.
2. The checked-in `Windows x86_64` preset exports a separate PCK and selects
   `libtet4d_core.windows.template_release.x86_64.dll` through the checked-in
   GDExtension descriptor.
3. The validator checks the exact three-file payload, PE executables, version
   metadata, required laboratory resources, absence of source/test/editor
   payloads, and absence of repository/user path leakage.
4. Mutable profiles, evaluations, captures, and proposal exports remain under
   Godot's writable `user://design_lab` root, never beside the executable.
5. Linux remains development-configured only. Windows is a packaged
   Design-Laboratory candidate, not a clean-machine runtime-accepted target
   until the recorded Windows acceptance is complete.
6. Only a validator-approved, checksum-recorded Windows ZIP may be published
   from ignored build output to Actions, release, or canonical candidate asset
   storage for remote testing; generated archives never enter Git history.

## 4a. Tablet design-laboratory boundary

1. Android release builds use the pinned 4.7.2 Android export templates, the
   prebuilt template rather than a Gradle build, `arm64-v8a` only, and large and
   extra-large screen support only. Automated release export copies the
   credential-free canonical preset into the disposable project, generates an
   ephemeral test key, and injects that key into all three release-signing
   fields of the staged copy only.
2. iPadOS builds use the pinned 4.7.2 iOS export template, the iPad device
   family, landscape orientation, and integer
   `application/export_method_release=1` (Development). Godot 4.7's mobile
   renderer requires an A12 device or newer.
3. `display/window/handheld/orientation` is an integer enum. A string value is
   silently ignored by the engine and falls back to a single pinned landscape
   orientation, so the validators assert the numeric value.
4. Both validators check application or bundle identity, screen or device
   targeting, orientation, packed laboratory resources, absence of test and
   Python payloads, and absence of repository path leakage.
5. No keystore, certificate, provisioning profile, password, or other signing
   secret is committed. Android test release signing exists only in disposable
   build state; the iPadOS team identifier is a placeholder overridden by
   `TET4D_IOS_TEAM_ID`.
6. Mutable profiles, evaluations, captures, and proposal exports remain under
   Godot's writable `user://design_lab` root on every platform. Only the
   transport that externalises a finished bundle differs by platform.
7. Neither tablet target is a clean-device runtime-accepted target until the
   recorded acceptance in
   `docs/plans/design_evaluation_laboratory_acceptance.md` is complete.
8. iPad configuration exports and release exports are distinct artifact
   classes. Configuration mode may carry the deliberately reduced descriptor
   only when explicitly validated as configuration evidence. Release mode must
   carry both iOS library declarations and the release native xcframework.

## 5. Active Python installer path

The following path owns the active Python/pygame packaged product family:

- `packaging/pyinstaller/tet4d.spec`;
- `packaging/scripts/build_macos.sh`;
- `packaging/scripts/build_linux.sh`;
- `packaging/scripts/build_windows.ps1`; and
- `.dmg`, `.deb`, and `.msi` outputs described by prior changelog entries.

This path embeds Python and launches `front.py`. It is distinct from the Stage
54G Godot professional-core release path and is not required to close that
gate. Before it enters the unified release workflow, every existing builder
must run from clean integrated source on its real operating system, produce the
version from `pyproject.toml`, and pass package installation plus an
outside-checkout `--runtime-smoke-check` followed by uninstallation where the
platform has an installer.

Proof status at 2026-08-31:

- macOS arm64: the existing builder produced
  `tet4d-0.7.5-macos-arm64.dmg` from integrated master
  `d542d682ab9f66a6e8ca95b888232b90524ef266`; the mounted app ran from the
  runner temporary directory with isolated user state and no checkout
  dependency. SHA-256:
  `3cbd29ec0a9d139b4687c41ad8e55c9a0f628ec52d9a21f9e7cbad896466c91d`.
  The embedded PyInstaller Mach-O is ad-hoc signed; the outer app bundle and
  shell launcher are unsigned, and the package is not notarized.
- Linux amd64: Actions run 33392862609 built
  `tet4d_0.7.5_amd64.deb` at integrated master `d542d682`, verified its package
  version and architecture, installed it, launched `/usr/bin/tet4d` from the
  runner temporary directory with isolated user state, and purged it. SHA-256:
  `5090caaef6328e3ff7c8d87945c96defc39760b0a1655bc4701e9ecf099b11c2`.
- Windows x64: after the proof harness was corrected to wait for the installed
  GUI-subsystem process, Actions run 33392862609 built and installed
  `tet4d-0.7.5-windows-x64.msi`, verified the installed version, executable and
  shortcuts, launched it from the runner temporary directory with isolated
  user state, uninstalled it, and verified files, shortcuts, and registration
  were removed. SHA-256:
  `abd25b01129810cdbe4433b17d8921b651b5a520aac67cf954f22c5f855e4f91`.

Run 33392862609 therefore satisfies the three-platform Python proof gate at
source `d542d682ab9f66a6e8ca95b888232b90524ef266`. Release orchestration may now
admit the Python family, provided it preserves these checks and binds both
product families to one source SHA and project version.

The proven checks are folded into `.github/workflows/release-packaging.yml` and
the temporary proof-only workflow is removed. The unified workflow retains the
real-platform install, outside-checkout runtime, and removal checks; gives all
seven product-family artifacts explicit names; rejects tag/project-version
disagreement before builds; and generates a checksum/source-SHA manifest only
after all package jobs pass. Its iPadOS manifest entry must remain explicit
that the output is unsigned, simulator-compiled Xcode-project evidence without
physical-device acceptance.

The first integrated unified dispatch, Actions run 33397993043 at exact master
`4fdb8bfa4e5730426789453df71ea198e70d475f`, is diagnostic rather than release
proof. It exposed two clean-run orchestration dependencies: direct headless
Design Laboratory tests resolved `PresentationProfile` through absent generated
global-class metadata on Android and iPadOS, and Windows passed 7-Zip an output
switch that PowerShell split into an invalid short `-o` argument. Both must be
corrected and the full seven-artifact workflow rerun from a new integrated
master SHA before the unified gate is accepted.

PR #79 corrected both dependencies; its complete exact-head CI matrix was green
before squash merge as `38551bb2f87d4f2866f33f99a7143cf156c75da6`.
Integrated dispatch 33401278911 confirms that the cache-free tablet semantic
test and Windows template extraction now pass their corrected boundaries, but
is still diagnostic: YAML folded each tablet build command into a shell token
with a leading space after an explicit continuation, so Android and iPadOS
could not locate their checked-in build scripts. Tablet build invocations must
be expressed as unambiguous shell blocks, and a fresh seven-artifact dispatch
from the resulting integrated master SHA remains required.

The same dispatch also completed the Windows native release build and export,
then correctly rejected the ZIP for containing the runner checkout marker.
The direct Godot test had populated the source project's ignored `.godot`
state, and the Windows disposable export copied that generated cache. Android
and iPadOS share the same source-copy pattern after the same test. Every
disposable platform export must therefore remove copied `.godot` state before
import/export; the macOS builder's existing exclusion remains the reference
boundary. This is packaging isolation, not a relaxation of host-path
validation.

After PR #80 made the tablet commands executable and isolated all disposable
project copies, integrated dispatch 33416903976 reached Android native
compilation. The configuration and staged release-signing validators passed,
then pinned `godot-cpp` required NDK `28.1.13356709` while the workflow had
selected the runner's newest preinstalled NDK. Android release packaging must
install and assert the exact NDK version required by the pinned native binding;
runner image inventory is not release authority.

The same dispatch compiled the iPadOS arm64 device archive successfully, then
correctly stopped because the declared release payload is an XCFramework and
the builder had not assembled one. The release builder must compile both the
arm64 device archive and the universal simulator archive with the pinned native
binding, combine exactly those archives with `xcodebuild -create-xcframework`,
and stage the resulting `libtet4d_core.ios.template_release.xcframework` before
Godot export. A single device archive is not the declared iPadOS GDExtension and
must not be renamed or accepted as one.

The Windows lane also completed native compilation and export. Its strict
validator then found the runner checkout marker in regenerated `.godot` cache
files packed into the PCK. Removing copied cache before import remains required,
and every canonical Designer export preset must additionally exclude both
`tests/*` and `.godot/*` so cache recreated by Godot cannot become product
payload. Host-path validation remains strict; this invariant removes the
development-only input rather than weakening the check.

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
   Disposable Windows, Android, iPadOS, and macOS project copies exclude the
   source checkout's generated `.godot` editor state before import/export.
6. A representative packaged 2D/3D/4D session, including Hold, NEXT, and
   Ghost, passes final manual release-candidate review.
7. Normal startup emits no release-blocking resource, parser, persistence, or
   GDExtension warning/error.
8. The current release workflow uploads the accepted Godot macOS ZIP, the
   separately named Windows Designer ZIP, the Android tablet APK, and the
   iPadOS Xcode project.
9. The Windows candidate passes exact three-file structural validation and its
   native CI job runs the focused laboratory suite plus bounded packaged start.
10. The Android and iPadOS candidates pass their configuration and artifact
    validators, and the recorded evidence names the exact level at which it was
    obtained.
    Their workflow steps invoke the checked-in build scripts directly with the
    resolved editor and template-root environment, without YAML folding or
    shell-continuation ambiguity.
11. Linux Godot, direct clean-machine Windows Godot acceptance, tablet device
    acceptance, signing/notarization, and each Python installer are reported
    with their exact verification limits.
12. Python packages use the project version, build on their real platform,
    install or mount successfully, launch from outside the checkout with
    isolated user state, and uninstall cleanly where applicable before they are
    admitted to the unified release workflow.
