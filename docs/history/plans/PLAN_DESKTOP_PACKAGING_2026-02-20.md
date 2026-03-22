# Plan Report: Desktop Packaging Without System Python (2026-02-20)

Status: Planned + Executed (baseline packaging scaffold)  
Related backlog item: `BKL-P2-018`  
Related RDS files: `docs/rds/RDS_TETRIS_GENERAL.md`, `docs/rds/RDS_PACKAGING.md`

## 1. Objective

1. Allow users to run/install `tet4d` on macOS, Linux, and Windows without preinstalled Python.
2. Keep one canonical packaging path and avoid per-platform drift.
3. Keep packaging reproducible in CI and local developer environments.

## 2. RDS Comparison (Before Changes)

1. Existing general RDS requires Python runtime compatibility and `pygame-ce`, but did not define desktop installer/bundled-runtime deliverables.
2. Existing release checklist had no desktop packaging verification stage.
3. Existing docs described source checkout + venv usage only.

## 3. Packaging Decisions

1. Build artifact type: bundled desktop app with embedded Python runtime (PyInstaller `onedir`).
2. Packaging entrypoint: `front.py` (unified launcher).
3. Bundled runtime data: `assets/`, `config/`, `keybindings/`, and `docs/help/`.
4. CI packaging: matrix job per OS (`macOS`, `Linux`, `Windows`) with uploaded installer artifacts.
5. Local scripts: one build script per OS under `packaging/scripts/`.

## 4. Scope and Non-Goals

1. In scope:
2. baseline cross-platform frozen runtime packaging,
3. local build scripts,
4. CI workflow,
5. packaging documentation and release checklist integration.
6. Out of scope for this batch:
7. code signing and notarization credential automation,
8. MSI/WiX and DMG branding customization,
9. auto-update infrastructure.

## 5. Implementation Plan

1. Add packaging spec:
2. `packaging/pyinstaller/tet4d.spec`.
3. Add build scripts:
4. `packaging/scripts/build_macos.sh`,
5. `packaging/scripts/build_linux.sh`,
6. `packaging/scripts/build_windows.ps1`.
7. Add CI workflow:
8. `.github/workflows/release-packaging.yml`.
9. Add docs:
10. `docs/RELEASE_INSTALLERS.md`,
11. update `README.md`, `docs/PROJECT_STRUCTURE.md`, `docs/README.md`, `docs/RDS_AND_CODEX.md`, `docs/RELEASE_CHECKLIST.md`.
12. Add packaging RDS:
13. `docs/rds/RDS_PACKAGING.md`.
14. Update canonical maintenance contract and backlog/changelog.

## 6. Acceptance Criteria

1. Local scripts build frozen desktop bundles on each OS.
2. CI workflow produces OS-specific uploaded artifacts.
3. RDS/docs/backlog/changelog are synchronized.
4. Local gates remain green:
5. `ruff check .`,
6. `pytest -q`,
7. `python3 tools/validate_project_contracts.py`,
8. `./scripts/ci_check.sh`.
