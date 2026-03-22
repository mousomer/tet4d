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
2. Keep `tet4d.engine` reusable as a lower layer; UI, AI, replay, and tools may depend on engine, but engine must not depend back on those upper layers.
3. Keep controls configurable via external JSON files (`keybindings/2d.json`,`3d.json`,`4d.json`).
4. Maintain playable and testable 2D, 3D, and 4D experiences with the same quality bar.
5. Preserve Python 3.14 compatibility while staying runnable on local Python 3.11+.
6. Add a dedicated in-app keybinding edit menu with local save/load workflow.
7. Add random-cell piece sets for 2D, 3D, and 4D as selectable options.
8. Allow lower-dimensional piece sets to be used on higher-dimensional boards through defined embedding rules.
9. Verify and harden scoring behavior with explicit automated scoring tests.
10. Add debug piece sets (simple large rectangular blocks) for 2D/3D/4D validation workflows.
11. Add non-intrusive sound effects with volume controls and mute toggles.
12. Remove manual slicing controls; keep gameplay independent from view-layer selection concepts.
13. Unify frontend entry into one main menu for 2D/3D/4D.
14. Make settings persistence and display mode transitions reliable (including fullscreen).
15. Add a deterministic automatic playbot framework for 2D/3D/4D with safe execution and performance budgets.
16. Keep menu structure and default settings in external config files (not hardcoded in frontend modules).
17. Define a long-term path for non-euclidean geometry gameplay extensions without breaking deterministic core behavior.
18. Add setup-selectable boundary topology presets:
19. `bounded`,
20. `wrap_all`,
21. `invert_all`.
22. Keep gravity-axis wrapping disabled by default in all presets.
23. Add advanced topology-designer mode (hidden by default) with per-axis/per-edge behavior profiles and deterministic export.
24. Support 4D camera/view hyperplane turns (`xw`/`zw`) as render-only controls (no gameplay-state mutation).
25. Keep view-plane turns keybindable as explicit camera actions, not overloaded with gameplay rotation actions.
26. Ship desktop bundles for macOS/Linux/Windows that include embedded Python runtime (no Python preinstall required for end users).
27. Add interactive tutorials for 2D/3D/4D with data-driven lesson packs, deterministic progression, and per-step input gating.
28. 3D/4D mouse tutorial stages must display explicit mouse prompts and require sustained mouse orbit/zoom interaction for at least 2 seconds before completion.
29. Tutorial board dimensions must use explicit per-mode tutorial profiles and must not inherit or clamp against the user's normal gameplay board settings.

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
5. Ordinary play launcher/setup surfaces remain preset-only for the migrated path; custom topology editing and custom-topology launch live in the Explorer Playground / last-custom route.
6. Gravity-axis wrapping remains disabled unless explicitly enabled in engine config.
7. Deterministic replay rule still applies to `(seed, topology mode/profile, input stream)`.

### 3.3 Shared piece-local transform rules

1. Piece-local coordinates are occupied-cell offsets from a deterministic piece origin, not a fixed pivot cell.
2. Piece rotation semantics are owned by `src/tet4d/engine/core/piece_transform.py` and reused by gameplay, AI, tutorials, and rotation animation.
3. A piece rotation is specified as a signed quarter-turn count in the active rotation plane; positive and negative turns are canonical, while raw `CW`/`CCW` wording is legacy-only and must not be the source-of-truth contract.
4. A 90-degree piece rotation must rotate occupied cells around the center of the active bounding box in the active rotation plane.
5. For XY gameplay on the screen, visual angle wording may differ from math-axis intuition because screen `y` increases downward; gameplay, animation, and tests must all follow the same canonical signed-turn helper instead of duplicating `CW`/`CCW` lore.
6. Odd active-plane spans rotate around the center cell.
7. Even active-plane spans rotate around the between-cells axis or plane.
8. Deterministic local re-anchoring after rotation is allowed as long as gameplay, bot planning, tutorials, and animation all consume the same canonical transform math.
9. Explorer-runtime piece transport must classify single-step outcomes as `plain_translation`, `rigid_transform`, or `cellwise_deformation` before mutating active-piece frame state.
10. `plain_translation` must preserve the existing piece-local frame and any rotation metadata exactly; ordinary movement must not rebase the piece origin through generic min-corner normalization.
11. `rigid_transform` outcomes may reframe the piece only through an explicit signed-permutation piece-frame transform that preserves coherent later rotations.
12. `cellwise_deformation` from unsafe seam crossings must be surfaced explicitly and blocked for rigid-piece gameplay instead of being silently canonicalized into a new local frame.

### 3.4 Shared rotation-kick rules

1. Rotation kicks are a post-rotation translation policy and must not change canonical piece-local rotation semantics in `src/tet4d/engine/core/piece_transform.py`.
2. Kick candidate generation must have exactly one canonical engine-core owner; target module path is `src/tet4d/engine/core/rotation_kicks.py`.
3. Kick candidate generation must stay pure and deterministic.
4. Kick acceptance must reuse the same topology-aware legality path as normal placement and existence checks.
5. Kick code must not duplicate bounded/wrap/invert edge math, topology crossing rules, or invert uniqueness handling from `src/tet4d/engine/gameplay/topology.py`.
6. `TopologyPolicy` remains authoritative for whether a rotated or kicked candidate is legal after mapping.
7. Gameplay and AI must consume the same canonical kick resolver; AI may import the engine-owned resolver or engine-owned convenience exports directly, but engine must not import AI.
8. `kick_level` is a gameplay-affecting advanced setting that must be persisted with menu settings and recorded in replay and save metadata.
9. Score multiplier may include a permissiveness factor keyed by configured `kick_level`, while leaderboard ordering remains score-first and is not bucketed by kick level.
10. Deterministic replay rule applies to `(seed, topology selection, kick_level, input stream)`.

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
11. 3D/4D locked-cell transparency must be user-adjustable from settings with default `25%` and allowed range `0%..90%`.
12. Locked-cell transparency must affect locked board cells only (challenge layers + landed pieces); active-piece cells remain opaque.
13. Piece generation must support both fixed-seed deterministic runs and true-random runs with user-configurable setup controls.
14. Tutorial overlay panel must be enlarged for readability, present one clear plain-language primary action line plus one optional tip line, and in 3D/4D default to a side-panel-safe lane outside the active board/layers area.
15. Tutorial progression must expose explicit segment order:
16. translations -> piece rotations -> camera rotations (3D/4D) -> camera controls (`toggle_grid`, transparency) -> goals (line/layer/full-board clear).
17. System controls (`help`, `menu`, `restart`, `quit`) are guidance-only in tutorials and must not require dedicated interactive stages.
18. Movement and rotation tutorial stages require repeated successful actions (`4` per direction stage) before progression.
19. Advanced gameplay settings expose a shared rotation animation mode selector (`cellwise_sliding` vs `rigid_piece_rotation`), kick permissiveness (`kick_level`), and shared piece motion animation durations for rotation and deliberate translation tweens across 2D/3D/4D.
20. Ordinary play launcher/setup surfaces must stay minimal for topology: safe preset selection only, plus launcher routes to `Play Last Custom Topology` and `Open Explorer Playground` for custom topology work.
21. For topology-playground migration-state questions, `docs/plans/topology_playground_current_authority.md` is the current architecture authority. Older topology-playground manifests and stage plans are historical unless explicitly reactivated.
22. Explorer Topology Lab must use a scene-first graphical explorer shell for 2D/3D/4D, with direct seam selection, engine-backed probe traversal, explorer-only sandbox interaction, and play launch from the current draft topology. Live Explorer launch must enter that same shell directly rather than a separate detached explorer frontend.
23. The Explorer Playground shell must expose an explicit controls/scene pane model, generated pane-aware helper text, mouse-adjustable +/- value controls, and synchronized 2D coordinate-plane projections as the default 3D/4D primary visualization: `3D` uses `xy/xz/yz`, `4D` uses `xy/xz/xw/yz/yw/zw`, all panels share one canonical selected-cell/topology/move-preview/seam-focus state, and hidden coordinates must stay explicit in every panel. Free-camera 3D/4D views may remain optional debug-only helpers, but they must not remain the primary Explorer Playground interface.
24. The Explorer Playground shell must be able to compile and export a parallel experiment pack from the current draft plus the active dimension's preset family, persist that pack under `state/topology/`, and surface a recommended next topology directly in the shell.
25. For the migrated Explorer Playground path, explorer rendering, topology visualization, and explorer-side selection/probe highlighting must consume the engine/runtime-owned `TopologyPlaygroundState`; retained UI-local mirrors may remain only as additive synchronized compatibility projections during migration, not as explorer-path input authority.
26. For the migrated core gluing workflow, explorer-side boundary picks, seam picks, and linked transform-editor slot selection must update the engine/runtime-owned `TopologyPlaygroundState` selected boundary, selected seam, and normalized gluing draft immediately; one full seam edit must complete without round-tripping to another menu.
27. The `Analysis View` pane must be clearly labeled as a secondary research/diagnostics surface; core seam authoring remains in the graphical explorer plus linked transform editor/action workspace and must not depend on row-based analysis controls. Explorer preset changes plus save/export/experiment/back administrative commands may live there, but duplicate copies must not compete with the action workspace, and read-only seam-context rows must look read-only rather than editable. UI maintenance should keep contextual row ownership isolated in dedicated helpers rather than rebuilding one mixed shell file, shell-facing row values/playability/context formatting should stay on that extracted helper side rather than drifting back into `controls_panel.py`, and any retained Normal Game row/export support must stay behind a narrowly named transitional legacy-support seam instead of a generic catch-all helper.
28. The Explorer Playground primary workspace ribbon must expose `Editor`, `Sandbox`, and `Play` as the only top-level workspace buttons. Editor-tool selection belongs to contextual secondary controls, and the footer movement grid must identify whether it moves the editor probe or the sandbox piece.
29. Invalid explorer topology / board-size pairings must remain attached to the current canonical draft topology across explorer entry, preview, sandbox, and play-launch surfaces; the playground may mark the topology invalid and block incompatible actions, but it must not silently substitute a fallback topology or drop the seam.
30. The Explorer Playground must surface one coherent runtime-derived playability signal for the current topology before launch, explicitly distinguishing validity, cellwise explorer usability, rigid playability, and the reason the current topology is invalid or explorer-only; this signal must be derived from canonical runtime state rather than preset labels or UI-only guesses.
31. The Explorer Playground workspace model must be centered on `editor`, `sandbox`, and `play` both internally and in the visible top-level shell. `Edit` may remain only as an editor-scoped tool name, and legacy inspect naming may remain only as compatibility input at normalization/deserialization boundaries, not as a primary workspace or active visible copy path.
32. Movement targets must be workspace-specific: `editor` moves only the editor probe/selection, `sandbox` moves only the sandbox piece, and `play` moves only the gameplay piece. Editor movement must stay non-mutating even when the active Editor tool is an explicit edit tool, and the editor probe/dot must remain visible in both Probe and Edit.
33. The legacy Inspect dot is the Editor probe/dot. Its movement, rendered position, and trace path must stay consistent before and after seam traversal, and that consistency requirement applies equally in `2D`, `3D`, and `4D`.
34. Editor trace visibility must be controlled by an explicit `Trace` contextual control owned by `Editor`, not by a floating/global Explorer exception. Disabling trace must not hide or disable the editor probe/dot itself.
35. Sandbox neighbor-search must be explicit runtime/menu state rather than hidden ND-only behavior; the playground must support sandbox piece experimentation with that overlay both enabled and disabled, while keeping the sandbox piece itself visible/usable in `3D`/`4D` by selecting/framing a visible sandbox cell rather than an abstract stale origin when the overlay is off or the piece has moved. The visible `Neighbors` control is Sandbox-owned contextual UI, not a floating/global Explorer toggle.
36. Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and `4D`.
37. In `3D` and `4D`, projected sandbox piece cells must render as clear piece boxes rather than neighbor-style dots.
38. Neighbor markers must appear as small dots only when the explicit Explorer `neighbor search` control is enabled, and those markers must not replace, hide, or visually masquerade as the sandbox piece.
39. On the live `Play This Topology` path, move acceptance, continued fall eligibility, support/grounded checks, lock decisions, and active-piece rendering inputs must all derive from the same canonical gameplay state rather than retained shell snapshots, panel-owned selection state, or projection-only coordinates.
40. Play-mode movement classes must remain explicit: deliberate translation, rotation, gravity tick, soft drop, and hard drop must not silently share one generic seam-transport rule.
41. Groundedness and lock in Play must be computed from whether one legal gravity/drop step exists under the Play drop policy; generic adjacency, generic seam existence, and non-drop reachability must not count as fall continuation.
42. Play drop legality may be stricter than deliberate/topological translation: lateral or other non-drop motion may enter legal bottom-layer space through the topology, while gravity/soft-drop/hard-drop may still be forbidden to continue through a non-trivial gravity-axis seam.
43. Explorer Playground helper text/panel selection must be keyed to the canonical workspace model (`editor` / `sandbox` / `play`). Editor helper content may vary by the active Editor tool, but legacy tool labels must not retake the primary top-level role. Workspace-shell copy/layout/helper routing should remain in dedicated shell helpers rather than drifting back into one monolithic menu/orchestration module, and those shell helpers should consume stable scene/value selectors instead of private adjustment helpers from `controls_panel.py`.
44. The Explorer Playground scene shell must keep an explicit right-side helper panel visible outside the explorer viewport. That helper must stay concise for the topology-editor shell: minimal translation keys, minimal rotation keys, and at most one short workspace/tool-context line. It must not become a second menu or status dump.
45. Menu items, workspace controls, and critical actions in the Explorer shell must remain fully visible and readable. Clipped, hidden, or effectively unusable labels are regressions.

### 4.1 Soft piece-rotation animation requirements

1. The visual transition for a successful rotation should be eased and short (`120-180 ms` target).
2. Gameplay state (collision, lock, scoring) remains discrete and deterministic; animation is presentation-only.
3. In `2D`, rigid rotation presentation must be drawn as rotated cell boxes sharing one angle around the discrete rotation pivot, not a precomposed sprite or a per-cell slide/morph between start and end cells.
4. If a new rotation arrives during an active rotation animation, either:
5. start from the current interpolated pose and retarget cleanly, or
6. queue one pending turn and consume it immediately after the current turn ends.
7. No visible jitter or one-frame reversion to the previous orientation is allowed.
8. The same animation path must be used for manual input and bot-triggered rotations.
9. Headless/dry-run paths must skip visual tween logic entirely.
10. Rotation overlay rendering must use the same topology-aware mapping path as active-piece rendering in all modes (2D/3D/4D), including exploration mode and wrapped/custom-topology play.
11. Any rigid-rotation visual angle must be derived from the discrete signed quarter-turn transform contract, not from an independent CW/CCW sign convention in renderer code.
12. When a rigid `2D` rotating cell box straddles a topology seam, rendering must clip and map the visible fragments so partial geometry appears in each affected destination grid region instead of disappearing or drawing as one unsplit quad.

### 4.2 Deliberate translation animation requirements

1. Successful deliberate piece translations may use a short eased visual tween; gameplay state remains discrete and deterministic.
2. Translation tweening applies only to deliberate move inputs or equivalent bot/explorer single-step moves, not to gravity ticks, soft-drop streaming, or hard drop.
3. Translation tweening must reuse the same active-piece overlay path as rotation tweening so mapped cells stay topology-correct in all modes.
4. Shared settings must expose separate persisted durations for `2D rotation`, `ND rotation` (shared by 3D/4D), and deliberate-translation tweens, stored in integer milliseconds and allowing `0` to disable each tween.
5. When a tweened `2D` translating cell box straddles a topology seam, rendering must clip and map the visible fragments so partial geometry appears in each affected destination grid region rather than snapping to one unsplit destination cell.

## 5. Controls and Keybinding Requirements

1. Keybindings must be loaded from external JSON files.
2. Small and full keyboard profiles are supported.
3. User-defined non-default profiles are supported (create/redefine/save/load).
4. Main/setup and in-game pause menus must provide equivalent profile actions.
5. System actions (`quit`,`menu`,`restart`,`toggle_grid`) are shared and discoverable.
6. 2D must ignore ND-only movement/rotation keys.
7. Keybinding edit flow must support per-action rebind, conflict handling, and local save/load.
8. Keybindings setup must be reachable from unified main menu and in-game pause menu.
9. 3D/4D camera keybindings must include in-game overlay-transparency adjustment actions.
10. Setup menus must expose random-mode controls in 2D/3D/4D; seed control is
    centralized in the shared Settings hub and applies across 2D/3D/4D unless a
    mode-specific exception is explicitly justified.

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
10. Windowed runtime resizes must be persisted as user override display state (`display.windowed_size`) without mutating source-controlled defaults.
11. Settings/keybindings/state writes must be atomic and recover from corrupt files with warning.
12. Menu/default config files are source-controlled:
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
23. `config/project/policy/manifests/canonical_maintenance.json`
24. Contract validation script is:
25. `tools/governance/validate_project_contracts.py`
26. Repository path/constant/secret policy configs are source-controlled:
27. `config/project/io_paths.json`
28. `config/project/constants.json`
29. `config/project/policy/manifests/secret_scan.json`
30. Secret scan command is:
31. `python3 tools/governance/scan_secrets.py`
32. Shared safe path/constants loader is:
33. `src/tet4d/engine/runtime/project_config.py`
34. Local verification and test harnesses may override the runtime state root through `TET4D_STATE_ROOT`, but resolved override paths must remain under the project root.
35. Repository hygiene must treat IDE state/log files/temporary local asset packs as non-source:
36. keep them ignored in `.gitignore` and never ship them as runtime contracts.
37. If such files are accidentally committed (or if sensitive data is introduced), cleanup must include history purge across refs before release.
38. Local environment bootstrap script is:
39. `scripts/bootstrap_env.sh`
40. Canonical schema/migration/help/replay/release artifacts are source-controlled:
41. `config/schema/*.schema.json`
42. `config/schema/help_topics.schema.json`
43. `config/schema/help_action_map.schema.json`
44. `docs/migrations/*.md`
45. `config/project/policy/manifests/replay_manifest.json`
46. `docs/help/HELP_INDEX.md`
47. `config/project/policy/manifests/help_assets_manifest.json`
48. `docs/RELEASE_CHECKLIST.md`
49. Profiler/benchmark tool outputs must be constrained to paths under the project root.
50. Desktop packaging assets are source-controlled:
51. `packaging/pyinstaller/tet4d.spec`
52. `packaging/scripts/build_macos.sh`
53. `packaging/scripts/build_linux.sh`
54. `packaging/scripts/build_windows.ps1`
55. `.github/workflows/release-packaging.yml`
55. Desktop packaging usage docs are source-controlled:
56. `docs/RELEASE_INSTALLERS.md`
57. Tutorial lesson packs are source-controlled:
58. `config/tutorial/lessons.json`
59. Tutorial lesson schema is source-controlled:
60. `config/schema/tutorial_lessons.schema.json`
61. Shared font model/factory is source-controlled:
62. `src/tet4d/ui/pygame/render/font_profiles.py`
63. Per-mode font profile values (2D vs ND) must remain explicit and stable.
64. Generated configuration reference is source-controlled at:
65. `docs/CONFIGURATION_REFERENCE.md`
66. Generated user-settings reference is source-controlled at:
67. `docs/USER_SETTINGS_REFERENCE.md`
68. Config changes under `config/` must regenerate those references via `tools/governance/generate_configuration_reference.py`.

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
python3.14 -m compileall -q front2d.py src/tet4d
./scripts/ci_check.sh
```

Expected test categories:
1. Unit tests for board, pieces, and game state transitions.
2. Replay determinism tests for 2D/3D/4D.
3. Smoke tests for key routing and system controls per mode.
4. Scoring matrix tests for 1/2/3/4+ clears across modes, including layer-size weighting (`sqrt(layer_size/reference)`, floor `1.0`) so larger cleared layers award higher base clear points.
5. Random/debug piece stress tests for spawn validity and non-premature game-over.
6. Menu/settings/display-mode integration tests (windowed <-> fullscreen).
7. Rotation-animation state machine tests (start, progress, finish, interruption/retrigger).
8. Topology seam regression tests: seam-straddling invert moves (including 4D `w` seam) must remain movable when target cells are otherwise valid.
9. Visual topology parity tests: rotation overlays and active-piece cells must agree under wrap/invert topologies.
10. Topology-aware kick acceptance tests must cover bounded, wrap, and invert modes without duplicating topology rules in kick code.

## 9. Acceptance Criteria (Family)

1. All three modes launch and play from menu to game-over without crash.
2. Clear and scoring logic match the mode RDS files.
3. Keybindings remain external and loadable.
4. Test and lint suites pass.
5. Keybindings can be edited in-app and saved/loaded locally by profile.
6. Random-cell piece sets are selectable and playable in each dimension.
7. Lower-dimensional piece sets are selectable and playable on higher-dimensional boards.
8. Scoring behavior is verified by automated tests, matches defined tables, and scales clear rewards by cleared layer size using square-root weighting.
9. Audio can be muted/unmuted and volume-controlled from settings.
10. Fullscreen toggling preserves correct menu and game layout state.
11. Safe topology presets are selectable in ordinary play setup menus and persisted in menu settings; custom topology launch routes through the Explorer Playground / last-custom path.
12. `kick_level` is persisted, participates in score multiplier calculation, and leaves leaderboard ordering unchanged.

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
12. Shared ND runtime loop orchestration extracted for 3D/4D (`src/tet4d/ui/pygame/runtime_ui/loop_runner_nd.py`).
13. Frontend split executed: launcher orchestration/settings and 3D/4D setup/render modules extracted for maintainability.
14. Offline playbot policy analysis tool added (`tools/benchmarks/analyze_playbot_policies.py`).
15. Playbot policy defaults retuned (budgets and benchmark thresholds) based on measured trend and benchmark data.
16. Unreferenced helper cleanup pass completed; definition-only helpers were removed from frontend/menu/project-config/score-analyzer modules.
17. Help/menu restructure `M1` contract completed with config-backed topic registry + action mapping and validator/test coverage.
18. Low-risk simplification follow-up completed:
19. menu-config validator helpers were consolidated in `src/tet4d/engine/runtime/menu_config.py`,
20. keybinding save/load path/profile resolution was deduplicated in `src/tet4d/ui/pygame/keybindings.py`,
21. test-only playbot wrappers were removed from `src/tet4d/ai/playbot/planner_nd.py` (tests now import `planner_nd_core` directly),
22. obsolete `menu_gif_guides.py` shim was removed; control visuals now use action-icon rendering via `src/tet4d/ui/pygame/render/control_icons.py`.
23. Stage-2 simplification follow-up completed:
24. shared list/string validators are now reused across row/action/scope checks in `src/tet4d/engine/runtime/menu_config.py`,
25. keybinding profile clone/dimension handling now uses shared helpers/constants in `src/tet4d/ui/pygame/keybindings.py`,
26. playbot enum option/index boilerplate was reduced through shared typed helpers in `src/tet4d/ai/playbot/types.py`.
27. keybinding `small` profile now resolves directly to root keybinding files (`keybindings/2d.json`,`3d.json`,`4d.json`), removing legacy dual-write/fallback paths.
28. Stage-3 dead-code cleanup completed:
29. removed unreferenced helper APIs in `src/tet4d/engine/runtime/runtime_config.py`, `src/tet4d/engine/gameplay/topology.py`, and `src/tet4d/engine/gameplay/topology_designer.py`.
30. menu-config validation now consistently uses shared primitive guards for launcher/settings/setup validation branches.
31. Stage-4 flow/tool simplification completed:
32. duplicated launch orchestration across `2D/3D/4D` now uses one shared launch pipeline in `src/tet4d/ui/pygame/launch/launcher_play.py`.
33. playbot benchmark wrapper helpers were removed from `src/tet4d/ai/playbot/types.py`; tools now consume benchmark thresholds/history paths directly from runtime config.
34. Stage-5 runtime-config simplification completed:
35. removed unused runtime-config constants/imports and consolidated repeated dimension-bucket/name-normalization access paths in `src/tet4d/engine/runtime/runtime_config.py`.
36. Stage-6 icon-pack integration completed:
37. helper/menu/help action icons now source from external SVG transform assets under `assets/help/icons/transform/svg`, via mapping config `config/help/icon_map.json`.
38. procedural icon rendering remains as deterministic fallback for unmapped/missing assets (for example `soft_drop` / `hard_drop`).
39. Desktop packaging baseline completed with embedded-runtime bundle spec, local OS build scripts, and CI packaging matrix workflow.
40. Font profile unification completed: duplicated frontend `GfxFonts`/`init_fonts` implementations are now routed through shared profile-driven factory in `src/tet4d/ui/pygame/render/font_profiles.py` with preserved 2D/ND profile values.

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
14. CI-enforced repository secret scan policy added (`config/project/policy/manifests/secret_scan.json`,`tools/governance/scan_secrets.py`,`scripts/ci_check.sh`),
15. I/O path definitions centralized in `config/project/io_paths.json` with safe `Path` resolution helpers in `src/tet4d/engine/runtime/project_config.py`,
16. selected runtime constants (cache/render limits and layout values) externalized to `config/project/constants.json`.
17. Closed: projection-lattice caching pass implemented for static camera/view signatures in 3D/4D projection grid paths.
18. Closed: low-risk LOC-reduction pass executed (pause-menu action dedupe, projected-grid dead-code removal, shared projection cache-key helpers, and score-analyzer validation consolidation).
19. Planned: keep continuous CI/stability watch and revisit optional sub-splits only if module scope grows.
20. Closed: advanced boundary-warping designer baseline implemented:
21. per-axis/per-edge profile overrides via `config/topology/designer_presets.json`,
22. custom topology editing/launch now lives in the Explorer Playground / last-custom path while ordinary setup remains preset-only,
23. deterministic profile export provided at `state/topology/selected_profile.json`.
24. Closed: 4D view `xw` / `zw` camera turns are implemented with keybinding + test coverage, preserving deterministic gameplay/replay behavior.
25. Closed: setup-menu render/value dedup extraction (`BKL-P2-007`) completed by routing 3D setup through the shared ND setup module (`src/tet4d/ui/pygame/frontend_nd_setup.py`) with ND state creation and gameplay/input routing owned separately by `frontend_nd_state.py` and `frontend_nd_input.py`.
26. Closed: help/menu restructure `M2` shared layout-zone renderer is implemented in `src/tet4d/engine/ui_logic/menu_layout.py` and wired in `src/tet4d/ui/pygame/runtime_ui/help_menu.py`.
27. Closed: help/menu restructure `M3` full key/help synchronization + explicit paging implemented in `src/tet4d/ui/pygame/runtime_ui/help_menu.py` and `src/tet4d/engine/runtime/help_topics.py`.
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

### 11.6.1 Current engine staging note

1. A new exploratory kernel now exists under `src/tet4d/engine/topology_explorer/` for general boundary gluings, signed-permutation transforms, boundary-crossing movement, and movement-graph compilation.
2. Live Explorer gameplay/runtime for 2D, 3D, and 4D now routes through that gluing engine; Normal Game remains on the legacy bounded/wrap/invert topology path.
3. Runtime-owned explorer profile storage and preview export now exist under `src/tet4d/engine/runtime/topology_explorer_store.py`, `src/tet4d/engine/runtime/topology_explorer_bridge.py`, and `src/tet4d/engine/runtime/topology_explorer_preview.py`.
4. Explorer 2D, Explorer 3D, and Explorer 4D Topology Lab now edit general gluing profiles directly through those runtime owners and use the graphical explorer scene as the primary spatial frontend, with boundary-card selection, tangent transform controls, basis-arrow overlays, and engine-backed probe traversal supporting live seam editing inside that scene-first shell.
5. Explorer preset libraries now include explicitly marked unsafe `Projective` / `Sphere` families for 2D/3D/4D; legality remains engine-owned in `src/tet4d/engine/topology_explorer/glue_validate.py`, not UI-owned.
6. The legacy bridge remains only for non-advanced explorer setup/export compatibility and future deletion once those paths stop depending on legacy edge-rule conversion.
7. A canonical engine/runtime playground-state contract now exists under `src/tet4d/engine/runtime/topology_playground_state.py`; later UI migration stages consume that state, while retained UI-local state paths remain additive compatibility debt until the consumer switch is complete.
8. The migrated Explorer Playground shell now surfaces a canonical playability analysis from that runtime state, explicitly showing validity, explorer usability, rigid playability, and launch context before `Play This Topology`.
9. Stage-1 workspace freeze now treats `editor` / `sandbox` / `play` as the canonical internal workspace identifiers, keeps `Edit` as the remaining editor-scoped tool label, limits legacy inspect naming to compatibility input handling only, and exposes sandbox neighbor-search plus workspace helper scaffolding explicitly in the migrated shell.
10. Live-path regression coverage now pins the broader non-trivial `Y`-seam Play contract on the direct play-launch runtime: sphere-like and projective-style cases now check drop legality, sideways bottom-layer entry, and hard-drop parity on the real gameplay path rather than helper-only geometry probes.
11. Current topology-playground migration authority lives in `docs/plans/topology_playground_current_authority.md`; older topology-playground manifests and stage plans are historical background only.

### 11.7 Test requirements (for future implementation)

1. Golden parity tests: `cartesian` profile must match current gameplay results.
2. Property tests: translation/rotation maps are reversible where declared reversible.
3. Clear-rule tests: region clears are deterministic and invariant to iteration order.
4. Replay tests: same input stream yields same final state per geometry profile.
5. Bot dry-run tests: no geometry profile may generate invalid/zero-sized placements.
