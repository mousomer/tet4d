# RDS Files And Codex Instructions

This document is section `3` of the unified documentation layout.

## RDS index

All requirement/design specs are in:
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_TETRIS_GENERAL.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_KEYBINDINGS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_PLAYBOT.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_SCORE_ANALYZER.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_2D_TETRIS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_3D_TETRIS.md`
- `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_4D_TETRIS.md`

Read order:
1. General RDS
2. Keybindings RDS
3. Menu structure RDS
4. Playbot + score-analyzer RDS
5. Mode-specific RDS
6. This Codex instructions page

## Codex contributor workflow

1. Read the relevant RDS files before editing gameplay logic.
2. Keep keybindings external; do not hardcode mode keys in frontends.
3. Preserve deterministic behavior where seeds are used.
4. When refactoring frontends, keep behavior parity with existing tests.
5. Prefer small, composable helpers over large event/render functions.

## Coding best practices

1. Keep game rules in engine modules (`game2d.py`, `game_nd.py`) and keep rendering thin.
2. Reuse shared projection/menu/input helpers to avoid 3D/4D drift.
3. Avoid side effects during import (especially in keybinding/config modules).
4. Keep files ASCII unless there is a strong reason otherwise.
5. Name helper functions by intent (`_advance_gravity`, `_tick_clear_animation`, etc.).
6. Keep complexity in check; run `ruff --select C901` on changes.

## Testing instructions

Run after every gameplay or input change:

```bash
ruff check /Users/omer/workspace/test-code/tet4d
ruff check /Users/omer/workspace/test-code/tet4d --select C901
pytest -q
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

Minimum required coverage for gameplay-affecting changes:
1. Unit tests for engine correctness (move/rotate/lock/clear/scoring).
2. Replay determinism tests.
3. Per-mode smoke tests for key routing and system controls.
4. If controls changed, verify JSON keybinding load/save behavior.

## Done criteria for gameplay changes

1. RDS intent remains accurate or is updated in the same change.
2. Existing tests pass and new behavior has targeted tests.
3. No new C901 failures.
4. Usage docs remain valid (`README.md`, docs links, run commands).

## Simplification and Technical Debt Tracking (2026-02-18)

Authoritative open/deferred items are tracked in:
1. `/Users/omer/workspace/test-code/tet4d/docs/BACKLOG.md`

### Active open items (synced from `/Users/omer/workspace/test-code/tet4d/docs/BACKLOG.md`)

1. `[P3]` Keep one source of truth for simplification debt: keep this file and `/Users/omer/workspace/test-code/tet4d/docs/BACKLOG.md` aligned as code evolves.
2. `[P3]` Periodic retuning cadence: rerun planner analysis against trend history after major algorithm/piece-set changes.

### Current complexity hotspots (`ruff --select C901`)

1. None currently open in backlog (latest local `ruff check --select C901` is green).

### Recent simplification baseline (already completed)

1. Shared menu-state dispatcher pattern extracted and reused.
2. Shared camera pose animator extracted.
3. Shared ND movement dispatch pipeline extracted.
4. Branching piece-set selector replaced with registry maps.
5. App boot/display/audio persistence glue consolidated.

### Verification requirements for simplification PRs

1. No behavior changes without tests.
2. Add or update targeted tests before extraction/refactor.
3. Keep deterministic replay tests green.
4. Run:
5. `ruff check /Users/omer/workspace/test-code/tet4d`
6. `ruff check /Users/omer/workspace/test-code/tet4d --select C901`
7. `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3.11 -m pytest -q`
8. `python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front.py /Users/omer/workspace/test-code/tet4d/tetris_nd`
