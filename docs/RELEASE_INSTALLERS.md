# Godot Release Exports

Tet4D's current professional-core release path is the Godot 4.7.2 macOS
Universal app. The earlier Python/PyInstaller installers are retained as a
legacy path and are not the Stage 54G product artifact.

## Build the current release candidate

Requirements:

1. macOS 13 or newer;
2. the exact Godot 4.7.2 stable editor pinned by
   `config/project/policy_pack.json`;
3. the matching official Godot 4.7.2 export templates;
4. the pinned `native/third_party/godot-cpp` submodule; and
5. the repository development environment with SCons 4.10.1.

From the repository root:

```bash
git submodule update --init --recursive
GODOT_BIN=/path/to/Godot packaging/godot/build_macos.sh
```

The script performs these release-boundary checks:

- exact Godot build identifier;
- universal release GDExtension build for macOS 13+;
- Godot release export through the checked-in `macOS Universal` preset;
- required executable, `Info.plist`, and packaged release framework;
- bundle identifier and version consistency;
- packaged `x86_64` plus `arm64` native slices;
- deep strict code-signature validation; and
- ZIP creation that preserves the macOS app-bundle structure; and
- two isolated clean-user launches of a copied app outside the checkout via
  `packaging/godot/smoke_macos.sh`.

Outputs are ignored local artifacts:

```text
artifacts/godot/macos/Tet4D.app
artifacts/godot/macos/Tet4D-0.7.5-macos-universal.zip
```

The versioned filename follows `pyproject.toml`; do not edit the export-preset
version independently.

## Build the Windows Design Laboratory candidate

Requirements are the exact pinned Godot 4.7.2 editor and matching export
templates, the pinned godot-cpp submodule, SCons 4.10.1, and either a native
Windows C++ toolchain or MinGW-w64 on macOS/Linux. From the repository root:

```bash
GODOT_BIN=/path/to/Godot \
GODOT_TEMPLATE_ROOT=/path/to/Godot-4.7.2-templates \
packaging/godot/build_windows.sh
```

The script cross-builds the release GDExtension, exports from a disposable
project copy, and validates the exact portable payload, PE binaries, version,
required laboratory resources, exclusions, and path sanitation. Its ignored
output is:

```text
artifacts/godot/windows/Tet4D-Designer-0.7.5-windows-x86_64.zip
```

Extract that ZIP to any user-writable directory and launch
`Tet4D Designer.exe`. This is an equivalent portable distributable, not an
MSI: extraction installs it, deleting that extracted directory uninstalls it,
and it creates no Start Menu entry, desktop shortcut, or registry uninstaller.
Profiles, evaluations, captures, and proposal exports are written to the
platform application-data directory through Godot `user://`, not the extracted
application directory. The package embeds no Python runtime or Godot editor.

Local cross-build and validation do not establish Windows runtime acceptance.
The Windows workflow builds natively, runs the focused laboratory suite,
validates the package, and performs a bounded headless start; a direct clean
Windows-machine review remains an explicit Stage 54F-5 acceptance item.

## Smoke and manual acceptance

The build already runs the two-user headless outside-tree smoke. For manual
acceptance, copy or extract the app outside the repository, use an isolated
application data directory, and launch the actual executable under
`Tet4D.app/Contents/MacOS/Tet4D`. Verify startup, native extension load, setup,
2D/3D/4D play, Hold, NEXT, Ghost, quit, and relaunch. The final Stage 54G
verdict requires independent human acceptance of the exported app.

The app is ad-hoc signed for local distribution testing. It is not notarized;
macOS may block a downloaded archive from an unknown source. Developer-ID
signing and notarization are post-gate distribution work unless separately
authorized and provisioned.

## Platform support boundary

- Current supported release: macOS 13+, Universal 2, Godot app/ZIP.
- Current packaged design candidate: Windows x86-64 portable Godot
  Design-Laboratory ZIP; clean-machine runtime acceptance pending.
- Development-configured only: Linux Godot GDExtension artifact names.
- Legacy retained path: Python/PyInstaller `.dmg`, `.deb`, and `.msi` builders
  under `packaging/scripts/` and `packaging/pyinstaller/`.

Do not report legacy installer CI or static GDExtension declarations as current
Godot runtime release evidence.

## Current release workflow

`.github/workflows/release-packaging.yml` builds the macOS Godot ZIP and the
separately named Windows Designer ZIP from exact pinned editors and templates.
A matching tag may publish both to its GitHub release after both jobs pass.
The workflow does not publish retained Python installers.
