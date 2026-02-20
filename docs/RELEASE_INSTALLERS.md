# Desktop Installer Packaging

This document defines how to build local desktop bundles that do not require a preinstalled Python runtime.

## 1. Packaging model

1. Packager: `PyInstaller` (`onedir`).
2. Entry point: `front.py` (unified launcher).
3. Bundled runtime content:
   - `assets/`
   - `config/`
   - `keybindings/`
   - `docs/help/`
4. Build spec:
   - `packaging/pyinstaller/tet4d.spec`

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

## 3. Output artifacts

All scripts write artifacts to:

- `artifacts/installers/`

Current outputs:

1. `tet4d-macos.tar.gz`
2. `tet4d-linux.tar.gz`
3. `tet4d-windows.zip`

## 4. CI packaging workflow

Workflow:

- `.github/workflows/release-packaging.yml`

Triggers:

1. manual dispatch,
2. tag push matching `v*`.

## 5. Follow-up release hardening

1. Add code-signing and notarization automation for macOS.
2. Add Authenticode signing + MSI workflow for Windows.
3. Add AppImage packaging/signing flow for Linux releases.
