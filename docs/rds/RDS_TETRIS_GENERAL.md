# Tetris Family RDS (General)

Status: Active v0.6 (Verified 2026-02-18)  
Author: Omer + Codex  
Date: 2026-02-18  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Purpose

Define shared requirements for the 2D, 3D, and 4D game modes in this repository.

Mode-specific requirements are defined in:
1. `docs/rds/RDS_2D_TETRIS.md`
2. `docs/rds/RDS_3D_TETRIS.md`
3. `docs/rds/RDS_4D_TETRIS.md` Keybinding-specific requirements are defined in:
1. `docs/rds/RDS_KEYBINDINGS.md` Menu-structure and settings-flow requirements are defined in:
1. `docs/rds/RDS_MENU_STRUCTURE.md` Automatic playbot requirements are defined in:
1. `docs/rds/RDS_PLAYBOT.md` Score-analyzer (board health + placement quality) requirements are defined in:
1. `docs/rds/RDS_SCORE_ANALYZER.md`

## 2. Current Project Intentions

1. Keep one shared deterministic gameplay core with mode-specific frontends.
2. Keep controls configurable via external JSON files (`keybindings/2d.json`,`3d.json`,`4d.json`).
3. Maintain playable and testable 2D, 3D, and 4D experiences with the same quality bar.
4. Preserve Python 3.14 compatibility while staying runnable on local Python 3.11+.
5. Add a dedicated in-app keybinding edit menu with local save/load workflow.
6. Add random-cell piece sets for 2D, 3D, and 4D as selectable options.
7. Allow lower-dimensional piece sets to be used on higher-dimensional boards through defined embedding rules.
8. Verify and harden scoring behavior with explicit automated scoring tests.
9. Add debug piece sets (simple large rectangular blocks) for 2D/3D/4D validation workflows.
10. Add non-intrusive sound effects with volume controls and mute toggles.
11. Clarify slicing semantics and decouple slicing from rotation concerns.
12. Unify frontend entry into one main menu for 2D/3D/4D.
13. Make settings persistence and display mode transitions reliable (including fullscreen).
14. Add a deterministic automatic playbot framework for 2D/3D/4D with safe execution and performance budgets.
15. Keep menu structure and default settings in external config files (not hardcoded in frontend modules).
16. Define a long-term path for non-euclidean geometry gameplay extensions without breaking deterministic core behavior.

## 3. Shared Rules and Axis Conventions

1. Axis `0`=`x`(horizontal), axis`1`=`y` (gravity/downward).
2. 3D adds axis `2`=`z`, 4D adds axis`3`=`w`.
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
7. A unified startup menu must allow choosing 2D/3D/4D and shared settings.
8. Audio controls (master volume, SFX volume, mute) must be available in settings.
9. Fullscreen/windowed toggle must be supported without layout corruption.
10. Piece rotations must use a soft visual animation instead of a single-frame snap.

### 4.1 Soft piece-rotation animation requirements

1. The visual transition for a successful rotation should be eased and short (`120-180 ms` target).
2. Gameplay state (collision, lock, scoring) remains discrete and deterministic; animation is presentation-only.
3. If a new rotation arrives during an active rotation animation, either:
4. start from the current interpolated pose and retarget cleanly, or
5. queue one pending turn and consume it immediately after the current turn ends.
6. No visible jitter or one-frame reversion to the previous orientation is allowed.
7. The same animation path must be used for manual input and bot-triggered rotations.
8. Headless/dry-run paths must skip visual tween logic entirely.

## 5. Controls and Keybinding Requirements

1. Keybindings must be loaded from external JSON files.
2. Small and full keyboard profiles are supported.
3. User-defined non-default profiles are supported (create/redefine/save/load).
4. Main/setup and in-game pause menus must provide equivalent profile actions.
5. System actions (`quit`,`menu`,`restart`,`toggle_grid`) are shared and discoverable.
6. 2D must ignore ND-only movement/rotation keys.
7. Keybinding edit flow must support per-action rebind, conflict handling, and local save/load.
8. Keybindings setup must be reachable from unified main menu and in-game pause menu.

## 6. Technical Requirements

1. Dependency package is `pygame-ce`; imports remain`import pygame`.
2. Main scripts:
3. `front2d.py`
4. `front3d.py`
5. `front4d.py`
6. Game loops must be frame-rate independent for gravity.
7. Piece set registration must include metadata (`id`,`dimension`,`cell_count`,`generator`,`is_embedded`).
8. Embedding helpers must convert lower-dimensional piece offsets into target board dimensions deterministically.
9. Display mode changes (windowed/fullscreen) must run through a shared display-state manager.
10. Settings/keybindings/state writes must be atomic and recover from corrupt files with warning.
11. Menu/default config files are source-controlled:
12. `config/menu/structure.json`
13. `config/menu/defaults.json`
14. Runtime tuning config files are source-controlled:
15. `config/gameplay/tuning.json`
16. `config/playbot/policy.json`
17. `config/audio/sfx.json`
18. User runtime overrides remain in `state/menu_settings.json`.
19. Canonical maintenance contract rules are defined in:
20. `config/project/canonical_maintenance.json`
21. Contract validation script is:
22. `tools/validate_project_contracts.py`
23. Canonical schema/migration/help/replay/release artifacts are source-controlled:
24. `config/schema/*.schema.json`
25. `docs/migrations/*.md`
26. `tests/replay/manifest.json`
27. `docs/help/HELP_INDEX.md`
28. `assets/help/manifest.json`
29. `docs/RELEASE_CHECKLIST.md`

## 7. Engineering Best Practices

1. Keep gameplay rules in engine modules (`game2d.py`,`game_nd.py`).
2. Keep rendering and camera/view logic in frontend modules.
3. Prefer small helper functions to avoid deeply nested loops and handlers.
4. Share projection/math helpers to avoid 3D/4D behavior drift.
5. Avoid hidden side effects at import-time.
6. Keep deterministic paths stable (seeded RNG, reproducible replay scripts).

## 8. Testing Instructions

Required checks for behavior changes:

```bash
ruff check .
ruff check . --select C901
python3 tools/validate_project_contracts.py
python3 tools/check_pygame_ce.py
pytest -q
PYTHONPATH=. python3 tools/check_playbot_stability.py --repeats 20 --seed-base 0
python3 tools/bench_playbot.py --assert --record-trend
python3.14 -m compileall -q  front2d.py  tetris_nd
./scripts/ci_check.sh
```Expected test categories:
1. Unit tests for board, pieces, and game state transitions.
2. Replay determinism tests for 2D/3D/4D.
3. Smoke tests for key routing and system controls per mode.
4. Scoring matrix tests for 1/2/3/4+ clears across modes.
5. Random/debug piece stress tests for spawn validity and non-premature game-over.
6. Menu/settings/display-mode integration tests (windowed <-> fullscreen).
7. Rotation-animation state machine tests (start, progress, finish, interruption/retrigger).

## 9. Acceptance Criteria (Family)

1. All three modes launch and play from menu to game-over without crash.
2. Clear and scoring logic match the mode RDS files.
3. Keybindings remain external and loadable.
4. Test and lint suites pass.
5. Keybindings can be edited in-app and saved/loaded locally by profile.
6. Random-cell piece sets are selectable and playable in each dimension.
7. Lower-dimensional piece sets are selectable and playable on higher-dimensional boards.
8. Scoring behavior is verified by automated tests and matches defined tables.
9. Audio can be muted/unmuted and volume-controlled from settings.
10. Fullscreen toggling preserves correct menu and game layout state.

## 10. Backlog Status

Completed in current implementation:
1. Board-size-aware playbot budget scaling for large boards.
2. CI benchmark trend tracking via JSONL history output.
3. ND planner split (`planner_nd.py`+`planner_nd_search.py`) to reduce orchestration complexity.
4. Deterministic long-run score snapshot tests across assist combinations.
5. User-facing shipped-feature map documentation (`docs/FEATURE_MAP.md`).
6. Explicit adaptive fallback policy (candidate caps + lookahead throttle + deadline safety).
7. Configured `AUTO` algorithm policy tuning (`HEURISTIC`vs`GREEDY_LAYER`) via runtime policy weights.
8. Optional deeper lookahead profile (`ULTRA`) for 2D/3D.
9. Benchmark thresholds and policy defaults externalized in `config/playbot/policy.json`.
10. Keybindings UX parity delivered across launcher/pause, with category docs sourced from `config/menu/structure.json`.
11. 4D helper-grid guidance propagated across all rendered `w` layer boards.
12. Shared ND runtime loop orchestration extracted for 3D/4D (`tetris_nd/loop_runner_nd.py`).
13. Frontend split executed: launcher orchestration/settings and 3D/4D setup/render modules extracted for maintainability.
14. Offline playbot policy analysis tool added (`tools/analyze_playbot_policies.py`).
15. Playbot policy defaults retuned (budgets and benchmark thresholds) based on measured trend and benchmark data.

Remaining follow-up:
1. Closed: policy trend checks and dry-run stability checks are automated in CI + scheduled stability-watch workflow.
2. Closed: help/documentation coverage now includes menu parity, settings IA rules, and control-guide surfaces.
3. Closed: top-level/submenu split policy is enforced by config validation (`settings_category_metrics`+ split rules).
4. Closed: maintainability follow-up executed for keybinding modules (shared display utils + menu model extraction + dead code removal).

## 11. Long-Term Goal: Non-Euclidean Geometry Extensions

### 11.1 Goal

Add optional geometry profiles where board adjacency is not strict cartesian grid topology, while preserving:
1. deterministic simulation,
2. reproducible replay,
3. stable scoring/clear rules per geometry profile.

### 11.2 Scope and design boundaries

1. Keep current euclidean grids as the default profile.
2. Add geometry as a pluggable engine-layer concept, not a frontend-only effect.
3. Treat rendering projection and gameplay topology as separate concerns.

### 11.3 Engine design plan

1. Introduce `GeometryProfile` interface (engine-level):
2. `neighbors(coord) -> iterable[coord]`
3. `translate(coord, axis_like, step) -> coord | invalid`
4. `rotation_map(piece_cells, transform_id) -> transformed_cells`
5. `clear_regions(cells, gravity_descriptor) -> cleared_region_ids`
6. Back existing euclidean behavior with a `CartesianGeometryProfile`.

### 11.4 Data model plan

1. Add geometry metadata to config:
2. `geometry.id`(example:`cartesian`,`torus_3d`,`wrapped_4d`)
3. `geometry.params` (profile-specific numeric settings)
4. Geometry profile definitions live in external config files under `config/geometry/`.

### 11.5 Determinism and replay requirements

1. Replay must store geometry profile id + params snapshot.
2. RNG state progression must remain identical for identical `(seed, geometry profile, input stream)`.
3. Dry-run and bot simulation must run on the same geometry profile API as gameplay.

### 11.6 Rollout phases

1. Phase 1: engine abstraction only with `cartesian` parity (no behavior change).
2. Phase 2: add one bounded non-euclidean profile (example: wrapped edges / torus) behind config flag.
3. Phase 3: add geometry-aware score-analyzer features and bot heuristics.
4. Phase 4: expose geometry selection in setup menus and help documentation.

### 11.7 Test requirements (for future implementation)

1. Golden parity tests: `cartesian` profile must match current gameplay results.
2. Property tests: translation/rotation maps are reversible where declared reversible.
3. Clear-rule tests: region clears are deterministic and invariant to iteration order.
4. Replay tests: same input stream yields same final state per geometry profile.
5. Bot dry-run tests: no geometry profile may generate invalid/zero-sized placements.
