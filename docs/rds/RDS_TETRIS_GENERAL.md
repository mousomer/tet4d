# Tetris Family RDS (General)

Status: Active v0.4  
Author: Omer + Codex  
Date: 2026-02-12  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Purpose

Define shared requirements for the 2D, 3D, and 4D game modes in this repository.

Mode-specific requirements are defined in:
1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_2D_TETRIS.md`
2. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_3D_TETRIS.md`
3. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_4D_TETRIS.md`

Keybinding-specific requirements are defined in:
1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_KEYBINDINGS.md`

Menu-structure and settings-flow requirements are defined in:
1. `/Users/omer/workspace/test-code/tet4d/docs/rds/RDS_MENU_STRUCTURE.md`

## 2. Current Project Intentions

1. Keep one shared deterministic gameplay core with mode-specific frontends.
2. Keep controls configurable via external JSON files (`keybindings/2d.json`, `3d.json`, `4d.json`).
3. Maintain playable and testable 2D, 3D, and 4D experiences with the same quality bar.
4. Preserve Python 3.14 compatibility while staying runnable on local Python 3.11+.
5. Add a dedicated in-app keybinding edit menu with local save/load workflow.
6. Add random-cell piece sets for 2D, 3D, and 4D as selectable options.
7. Allow lower-dimensional piece sets to be used on higher-dimensional boards through defined embedding rules.

## 3. Shared Rules and Axis Conventions

1. Axis `0` = `x` (horizontal), axis `1` = `y` (gravity/downward).
2. 3D adds axis `2` = `z`, 4D adds axis `3` = `w`.
3. Gravity acts on axis `y` in all modes.
4. `y < 0` is allowed before lock; locking above top triggers game over.
5. Board storage is sparse (`coord -> cell_id`).

## 4. Shared UX Requirements

1. Menu/setup screen before starting each mode.
2. In-game panel with score, cleared lines/layers, speed, controls, and game-over state.
3. Toggleable grid in all modes.
4. When grid is off, a board shadow/silhouette must still provide spatial context.
5. Layer/line clear feedback should be animated.
6. Setup and pause menus must expose equivalent controls/keybinding editing actions.

## 5. Controls and Keybinding Requirements

1. Keybindings must be loaded from external JSON files.
2. Small and full keyboard profiles are supported.
3. User-defined non-default profiles are supported (create/redefine/save/load).
4. Main/setup and in-game pause menus must provide equivalent profile actions.
5. System actions (`quit`, `menu`, `restart`, `toggle_grid`) are shared and discoverable.
6. 2D must ignore ND-only movement/rotation keys.
7. Keybinding edit flow must support per-action rebind, conflict handling, and local save/load.

## 6. Technical Requirements

1. Dependency package is `pygame-ce`; imports remain `import pygame`.
2. Main scripts:
3. `front2d.py`
4. `front3d.py`
5. `front4d.py`
6. Game loops must be frame-rate independent for gravity.
7. Piece set registration must include metadata (`id`, `dimension`, `cell_count`, `generator`, `is_embedded`).
8. Embedding helpers must convert lower-dimensional piece offsets into target board dimensions deterministically.

## 7. Engineering Best Practices

1. Keep gameplay rules in engine modules (`game2d.py`, `game_nd.py`).
2. Keep rendering and camera/view logic in frontend modules.
3. Prefer small helper functions to avoid deeply nested loops and handlers.
4. Share projection/math helpers to avoid 3D/4D behavior drift.
5. Avoid hidden side effects at import-time.
6. Keep deterministic paths stable (seeded RNG, reproducible replay scripts).

## 8. Testing Instructions

Required checks for behavior changes:

```bash
ruff check /Users/omer/workspace/test-code/tet4d
ruff check /Users/omer/workspace/test-code/tet4d --select C901
pytest -q
python3.14 -m compileall -q /Users/omer/workspace/test-code/tet4d/front2d.py /Users/omer/workspace/test-code/tet4d/tetris_nd
```

Expected test categories:
1. Unit tests for board, pieces, and game state transitions.
2. Replay determinism tests for 2D/3D/4D.
3. Smoke tests for key routing and system controls per mode.

## 9. Acceptance Criteria (Family)

1. All three modes launch and play from menu to game-over without crash.
2. Clear and scoring logic match the mode RDS files.
3. Keybindings remain external and loadable.
4. Test and lint suites pass.
5. Keybindings can be edited in-app and saved/loaded locally by profile.
6. Random-cell piece sets are selectable and playable in each dimension.
7. Lower-dimensional piece sets are selectable and playable on higher-dimensional boards.

## 10. Implementation Plan (Next Milestone)

### 10.1 Keyboard bindings edit menu (with local save/load)

1. Add a shared keybinding-editor model used by setup and pause menus.
2. Implement action-group navigation (`game`, `camera`, `slice`, `system`) and per-action capture mode.
3. Implement conflict flow (`replace`, `swap`, `cancel`) before committing a binding.
4. Persist bindings locally under profile files in `keybindings/profiles/<profile>/<dimension>.json`.
5. Add explicit `Load`, `Save`, `Save As`, and `Reset To Defaults` actions with status messages.

### 10.2 Random-cell piece sets (2D/3D/4D)

1. Add random piece generators per dimension with configurable cell count and deterministic seed support.
2. Enforce validity constraints (connected cells, no duplicate coordinates, normalized offsets).
3. Register these sets in setup menus as named options per mode.
4. Add tests for generator invariants and replay determinism under fixed seeds.

### 10.3 Lower-dimensional piece sets on higher-dimensional boards

1. Add piece-set adapters for 2D->3D, 2D->4D, and 3D->4D embedding.
2. Define default embedding planes/hyperplanes and expose selection where relevant.
3. Ensure embedded pieces fully support target-dimension movement/rotation after spawn.
4. Add tests for spawn validity, collision behavior, and clear/scoring parity.
