# Godot Release Export

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
- Development-configured only: Linux and Windows Godot GDExtension artifact
  names. Neither has a current export preset or Stage 54G runtime verdict.
- Legacy retained path: Python/PyInstaller `.dmg`, `.deb`, and `.msi` builders
  under `packaging/scripts/` and `packaging/pyinstaller/`.

Do not report legacy installer CI or static GDExtension declarations as current
Godot runtime release evidence.

## Current release workflow

`.github/workflows/release-packaging.yml` builds the macOS Godot ZIP from the
exact pinned editor and template. A matching tag may publish that ZIP to its
GitHub release. The workflow does not publish retained Python installers.
