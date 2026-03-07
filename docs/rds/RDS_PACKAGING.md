# Desktop Packaging RDS

Status: Active v0.2 (Verified 2026-03-06)
Author: Omer + Codex
Date: 2026-03-06
Scope: Desktop packaging and installer pipeline for macOS, Linux, and Windows.

## 1. Purpose

Define packaging requirements so users can install and run `tet4d` locally without a preinstalled Python runtime.

## 2. Requirements

1. Packaging must produce desktop installers with embedded Python runtime payloads.
2. Packaging entrypoint must be the unified launcher (`front.py`).
3. Bundles must include required runtime data directories:
4. `assets/`,
5. `config/`,
6. `keybindings/`,
7. `docs/help/`.
8. Packaging output must be produced on each target OS:
9. macOS x64,
10. macOS arm64,
11. Linux AMD64,
12. Windows x64.
13. Installer formats must be:
14. `.dmg` for macOS,
15. `.deb` for Linux,
16. `.msi` for Windows.
17. Packaging scripts must be source-controlled and runnable locally.
18. CI must provide a packaging workflow that uploads per-OS artifacts.
19. Tag-triggered packaging must publish installer assets to the matching GitHub release.
20. Packaging changes must update:
21. `README.md`,
22. `docs/RELEASE_INSTALLERS.md`,
23. `docs/RELEASE_CHECKLIST.md`,
24. `docs/BACKLOG.md`,
25. `docs/CHANGELOG.md`.

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

1. Local packaging scripts produce `.dmg`, `.deb`, and `.msi` artifacts on their target OS.
2. CI packaging workflow uploads installer artifacts for each matrix OS.
3. Tag-triggered packaging publishes installers to the matching GitHub release.
4. Core runtime/lint/test gates continue to pass after packaging changes.
