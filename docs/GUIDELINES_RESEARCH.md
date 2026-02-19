# Researched Guidelines And Current Issues

Status: Active  
Last verified: 2026-02-19

## 1. Guidelines used

1. Xbox Accessibility Guideline 112: consistent navigation and complete keyboard/controller support.
2. Xbox Accessibility Guideline 114: clear hierarchy, labeling, and predictable transitions.
3. WCAG 2.2: readable contrast, visible focus, and consistent help placement.
4. Nielsen heuristics: consistency, visibility of system status, recognition over recall, and error prevention.

## 2. How they are applied in this project

1. Unified menu IA with stable top-level categories (`Play`,`Settings`,`Keybindings`,`Bot Options`,`Help`).
2. Keyboard-first flows with consistent action semantics (`Enter`confirm,`Esc` back/cancel, arrow navigation).
3. Settings and keybindings are externalized to JSON and profile-scoped (no hardcoded-only paths).
4. Reset actions require confirmation; autosave is silent and status-visible.
5. Help and control guides are intended to be available from launcher, pause menu, and in-game helper surfaces.
6. Helper panel ordering prioritizes immediate gameplay controls over diagnostics.

## 3. Current issues (open backlog)

1. No blocking implementation gaps are currently open; active items are continuous watch tasks.
2. Complexity guardrails are enforced in local + CI checks (`ruff --select C901` in `scripts/ci_check.sh`).
3. Docs freshness is enforced via canonical contract regex rules in `config/project/canonical_maintenance.json`.
4. Local toolchain bootstrap is standardized in `scripts/bootstrap_env.sh`.
5. Continuous checks are automated in:
6. `.github/workflows/ci.yml`
7. `.github/workflows/stability-watch.yml`
8. Canonical synchronization source:
9. `docs/BACKLOG.md`

## 4. Current quality snapshot

1. `ruff check . --select C901`: pass.
2. `python3 tools/validate_project_contracts.py`: pass.
3. `pytest -q`: pass.
