# Desktop Installer Packaging

This document defines how to build release installers that do not require a preinstalled Python runtime.

## 1. Packaging model

1. Payload builder: `PyInstaller` (`onedir`).
2. Entry point: `front.py` (unified launcher).
3. Bundled runtime content:
   - `assets/`
   - `config/`
   - `keybindings/`
   - `docs/help/`
4. Installer outputs:
   - Windows: `.msi`
   - macOS: `.dmg` containing `tet4d.app`
   - Linux: `.deb`
5. Build spec:
   - `packaging/pyinstaller/tet4d.spec`
6. Frozen bundles must include hidden imports for lazy `tet4d.ai.playbot.*`
   package exports, especially the dry-run/setup helpers used by launcher and
   ND setup menus.

## 2. Local build commands

### macOS

```bash
bash packaging/scripts/build_macos.sh
```

### Linux

```bash
bash packaging/scripts/build_linux.sh
```

### Windows (PowerShell)

```powershell
./packaging/scripts/build_windows.ps1
```

Requirements:

1. `.NET SDK 6+` must be available on `PATH` because the script installs `WiX 6` as a local tool.
2. The script keeps WiX under `build/packaging/windows/.dotnet-tools` and uses `DOTNET_CLI_HOME` under `build/packaging/windows/.dotnet-cli-home` when not already set.
3. The Windows WiX build keeps `<MediaTemplate EmbedCab="yes" />`, builds into a temporary output directory under `build/packaging/windows/out`, and only moves the validated MSI into `artifacts/installers` after post-build checks pass.
4. Before each Windows build, the script removes stale `*.msi` and `*.cab` files from `artifacts/installers` and the packaging build tree under `build/packaging/windows`.
5. The Windows packaging script now fails hard if the expected MSI is missing or if any external `*.cab` is emitted anywhere under `build/packaging/windows`; shipping a sidecar `cab1.cab` is explicitly not allowed.

## 3. Output artifacts

All scripts write artifacts to:

- `artifacts/installers/`

Current outputs:

1. `tet4d-<version>-macos-x64.dmg`
2. `tet4d-<version>-macos-arm64.dmg`
3. `tet4d-<version>-windows-x64.msi`
4. `tet4d_<version>_amd64.deb`

## 4. CI packaging workflow

Workflow:

- `.github/workflows/release-packaging.yml`

Triggers:

1. manual dispatch,
2. tag push matching `v*`.

Current CI package targets:

1. Linux AMD64 (`ubuntu-latest`)
2. Windows x64 (`windows-latest`)
3. macOS x64 (`macos-15-intel`)
4. macOS ARM64 (`macos-latest`)

Artifact upload policy:

1. Windows uploads only `artifacts/installers/*.msi`
2. Linux uploads only `artifacts/installers/*.deb`
3. macOS uploads only `artifacts/installers/*.dmg`

Tag pushes also publish the generated installers to the matching GitHub release.

## 5. Follow-up release hardening

1. Add macOS code signing and notarization automation.
2. Add Windows Authenticode signing for MSI outputs.
3. Add Linux package signing and additional distro formats if needed.
