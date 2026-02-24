# Tetris Family RDS (General)

Status: Active v0.8 (Verified 2026-02-20)  
Author: Omer + Codex  
Date: 2026-02-20  
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Purpose

Define shared requirements for the 2D, 3D, and 4D game modes in this repository.

Mode-specific requirements are defined in:
1. `docs/rds/RDS_2D_TETRIS.md`
2. `docs/rds/RDS_3D_TETRIS.md`
3. `docs/rds/RDS_4D_TETRIS.md`

Cross-cutting requirements are defined in:
1. `docs/rds/RDS_KEYBINDINGS.md`
2. `docs/rds/RDS_MENU_STRUCTURE.md`
3. `docs/rds/RDS_PLAYBOT.md`
4. `docs/rds/RDS_SCORE_ANALYZER.md`
5. `docs/rds/RDS_PACKAGING.md`

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
11. Remove manual slicing controls; keep gameplay independent from view-layer selection concepts.
12. Unify frontend entry into one main menu for 2D/3D/4D.
13. Make settings persistence and display mode transitions reliable (including fullscreen).
14. Add a deterministic automatic playbot framework for 2D/3D/4D with safe execution and performance budgets.
15. Keep menu structure and default settings in external config files (not hardcoded in frontend modules).
16. Define a long-term path for non-euclidean geometry gameplay extensions without breaking deterministic core behavior.
17. Add setup-selectable boundary topology presets:
18. `bounded`,
19. `wrap_all`,
20. `invert_all`.
21. Keep gravity-axis wrapping disabled by default in all presets.
22. Add advanced topology-designer mode (hidden by default) with per-axis/per-edge behavior profiles and deterministic export.
23. Support 4D camera/view hyperplane turns (`xw`/`zw`) as render-only controls (no gameplay-state mutation).
24. Keep view-plane turns keybindable as explicit camera actions, not overloaded with gameplay rotation actions.
25. Ship desktop bundles for macOS/Linux/Windows that include embedded Python runtime (no Python preinstall required for end users).

## 3. Shared Rules and Axis Conventions

1. Axis `0`=`x`(horizontal), axis`1`=`y` (gravity/downward).
2. 3D adds axis `2`=`z`, 4D adds axis`3`=`w`.
3. Gravity acts on axis `y` in all modes.
4. `y < 0` is allowed before lock; locking above top triggers game over.
5. Board storage is sparse (`coord -> cell_id`).

### 3.1 Shared topology preset rules

1. Topology mode must be one of: `bounded`, `wrap_all`, `invert_all`.
2. Topology behavior is engine-level (movement/collision/lock), not render-only.
3. Gravity axis (`y`) does not wrap by default.
4. `wrap_all`: non-gravity axes use modular wrapping at board edges.
5. `invert_all`: crossing a wrapped edge mirrors other wrapped non-gravity axes deterministically.
6. Fixed `(seed, topology mode, input stream)` must produce deterministic replay.
7. In invert topologies, piece mapping must preserve seam traversal continuity for seam-straddling pieces; moves must not fail solely due to per-cell inversion desynchronization.

### 3.2 Advanced topology-designer rules

1. `topology_advanced=0` keeps preset-only behavior (`bounded`/`wrap_all`/`invert_all`).
2. `topology_advanced=1` enables profile-based per-axis/per-edge overrides.
3. Profile source file is `config/topology/designer_presets.json`.
4. Profile output export path defaults to `state/topology/selected_profile.json`.
5. Gravity-axis wrapping remains disabled unless explicitly enabled in engine config.
6. Deterministic replay rule still applies to `(seed, topology mode/profile, input stream)`.

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
9. Rotation overlay rendering must use the same topology-aware mapping path as active-piece rendering in all modes (2D/3D/4D), including exploration mode.

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
14. Help topic contracts are source-controlled:
15. `config/help/topics.json`
16. `config/help/action_map.json`
17. Runtime tuning config files are source-controlled:
18. `config/gameplay/tuning.json`
19. `config/playbot/policy.json`
20. `config/audio/sfx.json`
21. User runtime overrides remain in `state/menu_settings.json`.
22. Canonical maintenance contract rules are defined in:
23. `config/project/canonical_maintenance.json`
24. Contract validation script is:
25. `tools/governance/validate_project_contracts.py`
26. Repository path/constant/secret policy configs are source-controlled:
27. `config/project/io_paths.json`
28. `config/project/constants.json`
29. `config/project/secret_scan.json`
30. Secret scan command is:
31. `python3 tools/governance/scan_secrets.py`
32. Shared safe path/constants loader is:
33. `tetris_nd/project_config.py`
34. Repository hygiene must treat IDE state/log files/temporary local asset packs as non-source:
35. keep them ignored in `.gitignore` and never ship them as runtime contracts.
36. If such files are accidentally committed (or if sensitive data is introduced), cleanup must include history purge across refs before release.
37. Local environment bootstrap script is:
38. `scripts/bootstrap_env.sh`
39. Canonical schema/migration/help/replay/release artifacts are source-controlled:
40. `config/schema/*.schema.json`
41. `config/schema/help_topics.schema.json`
42. `config/schema/help_action_map.schema.json`
43. `docs/migrations/*.md`
44. `tests/replay/manifest.json`
45. `docs/help/HELP_INDEX.md`
46. `assets/help/manifest.json`
47. `docs/RELEASE_CHECKLIST.md`
48. Profiler/benchmark tool outputs must be constrained to paths under the project root.
49. Desktop packaging assets are source-controlled:
50. `packaging/pyinstaller/tet4d.spec`
51. `packaging/scripts/build_macos.sh`
52. `packaging/scripts/build_linux.sh`
53. `packaging/scripts/build_windows.ps1`
54. `.github/workflows/release-packaging.yml`
55. Desktop packaging usage docs are source-controlled:
56. `docs/RELEASE_INSTALLERS.md`
57. Shared font model/factory is source-controlled:
58. `tetris_nd/font_profiles.py`
59. Per-mode font profile values (2D vs ND) must remain explicit and stable.

## 7. Engineering Best Practices

1. Keep gameplay rules in engine modules (`game2d.py`,`game_nd.py`).
2. Keep rendering and camera/view logic in frontend modules.
3. Prefer small helper functions to avoid deeply nested loops and handlers.
4. Share projection/math helpers to avoid 3D/4D behavior drift.
5. Avoid hidden side effects at import-time.
6. Keep deterministic paths stable (seeded RNG, reproducible replay scripts).
7. Remove unreferenced helpers unless they are intentionally exported with explicit justification.

## 8. Testing Instructions

Required checks for behavior changes:

```bash
scripts/bootstrap_env.sh
ruff check .
ruff check . --select C901
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/scan_secrets.py
python3 tools/governance/check_pygame_ce.py
pytest -q
PYTHONPATH=. python3 tools/stability/check_playbot_stability.py --repeats 20 --seed-base 0
python3 tools/benchmarks/bench_playbot.py --assert --record-trend
python3.14 -m compileall -q  front2d.py  tetris_nd  src/tet4d
./scripts/ci_check.sh
```

Expected test categories:
1. Unit tests for board, pieces, and game state transitions.
2. Replay determinism tests for 2D/3D/4D.
3. Smoke tests for key routing and system controls per mode.
4. Scoring matrix tests for 1/2/3/4+ clears across modes.
5. Random/debug piece stress tests for spawn validity and non-premature game-over.
6. Menu/settings/display-mode integration tests (windowed <-> fullscreen).
7. Rotation-animation state machine tests (start, progress, finish, interruption/retrigger).
8. Topology seam regression tests: seam-straddling invert moves (including 4D `w` seam) must remain movable when target cells are otherwise valid.
9. Visual topology parity tests: rotation overlays and active-piece cells must agree under wrap/invert topologies.

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
11. Topology presets are selectable in setup menus and persisted in menu settings.

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
14. Offline playbot policy analysis tool added (`tools/benchmarks/analyze_playbot_policies.py`).
15. Playbot policy defaults retuned (budgets and benchmark thresholds) based on measured trend and benchmark data.
16. Unreferenced helper cleanup pass completed; definition-only helpers were removed from frontend/menu/project-config/score-analyzer modules.
17. Help/menu restructure `M1` contract completed with config-backed topic registry + action mapping and validator/test coverage.
18. Low-risk simplification follow-up completed:
19. menu-config validator helpers were consolidated in `tetris_nd/menu_config.py`,
20. keybinding save/load path/profile resolution was deduplicated in `tetris_nd/keybindings.py`,
21. test-only playbot wrappers were removed from `tetris_nd/playbot/planner_nd.py` (tests now import `planner_nd_core` directly),
22. obsolete `menu_gif_guides.py` shim was removed; menu guide rendering now uses `tetris_nd/menu_control_guides.py` only.
23. Stage-2 simplification follow-up completed:
24. shared list/string validators are now reused across row/action/scope checks in `tetris_nd/menu_config.py`,
25. keybinding profile clone/dimension handling now uses shared helpers/constants in `tetris_nd/keybindings.py`,
26. playbot enum option/index boilerplate was reduced through shared typed helpers in `tetris_nd/playbot/types.py`.
27. keybinding `small` profile now resolves directly to root keybinding files (`keybindings/2d.json`,`3d.json`,`4d.json`), removing legacy dual-write/fallback paths.
28. Stage-3 dead-code cleanup completed:
29. removed unreferenced helper APIs in `tetris_nd/runtime_config.py`, `tetris_nd/topology.py`, and `tetris_nd/topology_designer.py`.
30. menu-config validation now consistently uses shared primitive guards for launcher/settings/setup validation branches.
31. Stage-4 flow/tool simplification completed:
32. duplicated launch orchestration across `2D/3D/4D` now uses one shared launch pipeline in `tetris_nd/launcher_play.py`.
33. playbot benchmark wrapper helpers were removed from `tetris_nd/playbot/types.py`; tools now consume benchmark thresholds/history paths directly from runtime config.
34. Stage-5 runtime-config simplification completed:
35. removed unused runtime-config constants/imports and consolidated repeated dimension-bucket/name-normalization access paths in `tetris_nd/runtime_config.py`.
36. Stage-6 icon-pack integration completed:
37. helper/menu/help action icons now source from external SVG transform assets under `assets/help/icons/transform/svg`, via mapping config `config/help/icon_map.json`.
38. procedural icon rendering remains as deterministic fallback for unmapped/missing assets (for example `soft_drop` / `hard_drop`).
39. Desktop packaging baseline completed with embedded-runtime bundle spec, local OS build scripts, and CI packaging matrix workflow.
40. Font profile unification completed: duplicated frontend `GfxFonts`/`init_fonts` implementations are now routed through shared profile-driven factory in `tetris_nd/font_profiles.py` with preserved 2D/ND profile values.

Remaining follow-up:
1. Closed: policy trend checks and dry-run stability checks are automated in CI + scheduled stability-watch workflow.
2. Closed: help/documentation coverage now includes menu parity, settings IA rules, and control-guide surfaces.
3. Closed: top-level/submenu split policy is enforced by config validation (`settings_category_metrics`+ split rules).
4. Closed: maintainability follow-up executed for keybinding modules (shared display utils + menu model extraction + dead code removal).
5. Closed: local CI runner is hermetic and module-based in `scripts/ci_check.sh` (no global fallback drift).
6. Closed: docs freshness rules now include regex checks for stale pass-count snapshots.
7. Closed: control-helper optimization completed (cached action-icon surfaces + shared dimensional row-builders with parity tests).
8. Closed: simplification batch completed (shared UI utilities, pause/settings row externalization, keybindings view/input split, shared ND launcher helper, shared 2D/ND lookahead helper, and sectioned runtime-config validator).
9. Closed: follow-up simplification pass completed for nested runtime callbacks, gameplay tuning validator split, duplicated 3D/4D grid branch rendering, keybinding defaults/catalog split, score-analyzer feature split, and 2D panel extraction.
10. Closed: optimization-focused pass completed for menu gradient caching and bounded HUD/panel text-surface caching.
11. Closed: remaining decomposition pass completed for 3D frontend runtime/render split and runtime-config validator section split.
12. Closed: further runtime optimization pass completed (shared text-render cache, cached control-helper text, and 4D layer rendering pre-indexing by `w` layer).
13. Closed: security/config hardening batch:
14. CI-enforced repository secret scan policy added (`config/project/secret_scan.json`,`tools/governance/scan_secrets.py`,`scripts/ci_check.sh`),
15. I/O path definitions centralized in `config/project/io_paths.json` with safe `Path` resolution helpers in `tetris_nd/project_config.py`,
16. selected runtime constants (cache/render limits and layout values) externalized to `config/project/constants.json`.
17. Closed: projection-lattice caching pass implemented for static camera/view signatures in 3D/4D projection grid paths.
18. Closed: low-risk LOC-reduction pass executed (pause-menu action dedupe, projected-grid dead-code removal, shared projection cache-key helpers, and score-analyzer validation consolidation).
19. Planned: keep continuous CI/stability watch and revisit optional sub-splits only if module scope grows.
20. Closed: advanced boundary-warping designer baseline implemented:
21. per-axis/per-edge profile overrides via `config/topology/designer_presets.json`,
22. setup-gated by `topology_advanced` toggle and `topology_profile_index`,
23. deterministic profile export provided at `state/topology/selected_profile.json`.
24. Closed: 4D view `xw` / `zw` camera turns are implemented with keybinding + test coverage, preserving deterministic gameplay/replay behavior.
25. Closed: setup-menu render/value dedup extraction (`BKL-P2-007`) completed by routing 3D setup through shared ND setup module (`tetris_nd/frontend_nd.py`) via thin adapter in `tetris_nd/front3d_setup.py`.
26. Closed: help/menu restructure `M2` shared layout-zone renderer is implemented in `tetris_nd/menu_layout.py` and wired in `tetris_nd/help_menu.py`.
27. Closed: help/menu restructure `M3` full key/help synchronization + explicit paging implemented in `tetris_nd/help_menu.py` and `tetris_nd/help_topics.py`.
28. Closed: help contract validation now enforces quick/full lane coverage for action mappings in `tools/governance/validate_project_contracts.py`.
29. Closed: help/menu restructure phase `M4` (launcher/pause parity + compact-window hardening) is implemented with config-enforced parity and compact help layout policy.

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
5. Phase 5: boundary-warping designer for custom topology authoring.

### 11.7 Test requirements (for future implementation)

1. Golden parity tests: `cartesian` profile must match current gameplay results.
2. Property tests: translation/rotation maps are reversible where declared reversible.
3. Clear-rule tests: region clears are deterministic and invariant to iteration order.
4. Replay tests: same input stream yields same final state per geometry profile.
5. Bot dry-run tests: no geometry profile may generate invalid/zero-sized placements.
