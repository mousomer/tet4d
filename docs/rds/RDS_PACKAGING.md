# Desktop Packaging RDS

Status: Active v0.1 (Verified 2026-02-20)  
Author: Omer + Codex  
Date: 2026-02-20  
Scope: Desktop packaging and installer pipeline for macOS, Linux, and Windows.

## 1. Purpose

Define packaging requirements so users can run/install `tet4d` locally without a preinstalled Python runtime.

## 2. Requirements

1. Packaging must produce desktop bundles with embedded Python runtime.
2. Packaging entrypoint must be the unified launcher (`front.py`).
3. Bundles must include required runtime data directories:
4. `assets/`,
5. `config/`,
6. `keybindings/`,
7. `docs/help/`.
8. Packaging output must be produced on each target OS:
9. macOS,
10. Linux,
11. Windows.
12. Packaging scripts must be source-controlled and runnable locally.
13. CI must provide a packaging workflow that uploads per-OS artifacts.
14. Packaging changes must update:
15. `README.md`,
16. `docs/RELEASE_INSTALLERS.md`,
17. `docs/RELEASE_CHECKLIST.md`,
18. `docs/BACKLOG.md`,
19. `docs/CHANGELOG.md`.

## 3. Canonical files

1. Spec:
2. `packaging/pyinstaller/tet4d.spec`
3. Local build scripts:
4. `packaging/scripts/build_macos.sh`
5. `packaging/scripts/build_linux.sh`
6. `packaging/scripts/build_windows.ps1`
7. CI workflow:
8. `.github/workflows/release-packaging.yml`
9. Usage and release docs:
10. `docs/RELEASE_INSTALLERS.md`
11. `docs/RELEASE_CHECKLIST.md`

## 4. Acceptance criteria

1. Local packaging scripts run successfully on their target OS.
2. CI packaging workflow uploads artifacts for each matrix OS.
3. Core runtime/lint/test gates continue to pass after packaging changes.
