# Researched Guidelines And Current Issues

Status: Active  
Last verified: 2026-02-18

## 1. Guidelines used

1. Xbox Accessibility Guideline 112: consistent navigation and complete keyboard/controller support.
2. Xbox Accessibility Guideline 114: clear hierarchy, labeling, and predictable transitions.
3. WCAG 2.2: readable contrast, visible focus, and consistent help placement.
4. Nielsen heuristics: consistency, visibility of system status, recognition over recall, and error prevention.

## 2. How they are applied in this project

1. Unified menu IA with stable top-level categories (`Play`, `Settings`, `Keybindings`, `Bot Options`, `Help`).
2. Keyboard-first flows with consistent action semantics (`Enter` confirm, `Esc` back/cancel, arrow navigation).
3. Settings and keybindings are externalized to JSON and profile-scoped (no hardcoded-only paths).
4. Reset actions require confirmation; autosave is silent and status-visible.
5. Help and control guides are intended to be available from launcher, pause menu, and in-game helper surfaces.
6. Helper panel ordering prioritizes immediate gameplay controls over diagnostics.

## 3. Current issues (open backlog)

1. No active open gaps (verified 2026-02-18).
2. Continuous checks are automated in:
3. `/Users/omer/workspace/test-code/tet4d/.github/workflows/ci.yml`
4. `/Users/omer/workspace/test-code/tet4d/.github/workflows/stability-watch.yml`
5. Canonical synchronization source:
6. `/Users/omer/workspace/test-code/tet4d/docs/BACKLOG.md`

## 4. Current quality snapshot

1. `ruff check . --select C901`: pass.
2. `python3 tools/validate_project_contracts.py`: pass.
3. `pytest -q`: pass (`126 passed`).
