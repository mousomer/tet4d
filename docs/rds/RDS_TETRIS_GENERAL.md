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

### 3.2a Topology Lab semantic freeze rules

1. The Topology Lab is split into `Editor`, `Sandbox`, and `Play`.
2. `Editor` owns topology construction, boundary gluing, topology preset
   selection, validation, validity status, and launch eligibility.
3. `Sandbox` owns free probe/piece exploration, neighbor inspection, seam
   visibility, and exploratory movement diagnostics.
4. `Play` owns launched gameplay and play-specific legality, including
   gameplay drop and lock behavior.
5. Sandbox/Explorer movement may exceed Play legality on non-trivial `Y`-seam
   topologies; gravity tick, soft drop, and hard drop must not treat a
   `Y`-axis seam traversal as ordinary fall continuation.
6. `Play This Topology` must preserve the exact canonical topology transport
   semantics selected and validated in the lab. No silent fallback or partial
   topology reconstruction is allowed.
7. Wrap / invert / sphere-like selections are transport presets, not visual
   themes, spawn presets, or renderer-only options.

### 3.2b Topology/gameplay golden trace rules

1. Stage 2 topology/gameplay golden traces live under
   `migration/golden_traces/` and are generated by `tools/migration/`.
2. The traces are deterministic, versioned JSON artifacts generated from the
   Python runtime. They record topology transport, probe movement, gameplay
   state, drop/lock results, and launch parity behavior.
3. Unity, Godot, C#, C++, or other engine migration work must replay these
   traces before implementing independent topology transport or gameplay
   drop/lock logic.
4. Trace export must not reinterpret semantics; Python remains authoritative
   until a replacement core passes trace parity.
5. Stage 3 adds locked-cell endgame traces to the same migration replay
   contract.

### 3.2c Endgame golden trace rules

1. Locked-cell endgame traces live under `migration/golden_traces/endgame/` and
   are generated by `tools/migration/export_endgame_trace.py`.
2. Endgame traces are deterministic, versioned JSON artifacts generated from
   the Python headless locked-cell explosion model.
3. The endgame model owns particle state, topology-aware movement, canonical
   boundary handling, velocity transport, and kinetic-energy diagnostics.
4. Pygame rendering, shell artifacts, audio, camera, and UI controls are
   adapters over the model and are not semantic authorities.
5. Unity, Godot, C#, C++, or other engine migration work must replay endgame
   traces before implementing independent endgame simulation.

### 3.2d Migration bundle rules

1. Stage 4 migration bundle output lives under `migration/exported_bundle/` and
   is generated by `tools/migration/export_config_bundle.py`.
2. The bundle packages a manifest, config snapshot, topology/gameplay/endgame
   trace copies and indexes, schema metadata, authority-doc metadata, and a
   generated README for engine replay spikes.
3. The bundle is not authoritative. Config authority remains in `config/`,
   semantic authority remains in the Python runtime under `src/`, trace
   authority remains in `migration/golden_traces/`, and product/governance
   authority remains in the documented RDS/plans/governance files.
4. Bundle JSON must be deterministic, repo-relative, digest-backed, and free of
   timestamps, local absolute paths, memory reprs, and object identities.
5. Unity/Godot replay spikes should consume the bundle as input data before
   implementing independent topology transport, gameplay drop/lock, or endgame
   simulation. Engine scene or inspector defaults must not replace the Python
   and config authorities.

### 3.2e Unity replay spike rules

1. Stage 5 Unity replay lives under `unity/Tet4D.Unity/` and consumes only the
   copied bundle under `Assets/StreamingAssets/tet4d_bundle/` at runtime.
2. Unity may parse traces, extract renderable snapshots, render frame data,
   browse cases, and display diagnostics/config metadata.
3. Unity must not call Python at runtime, read repo-root `migration/exported_bundle/`
   directly, or scrape `src/`, `config/`, `tools/`, `tests/`, or `docs/` at runtime.
4. Unity must not implement gameplay rules, topology transport, score/lock
   logic, or endgame particle simulation semantics in C# for this stage.
5. Inspector, prefab, ScriptableObject, and scene values may control replay
   presentation only. They must not become gameplay, topology, config, or
   endgame semantic authority.

### 3.2f Godot replay spike rules

1. Stage 6 Godot replay lives under `godot/Tet4D.Godot/` and consumes only the
   copied bundle under `res://assets/tet4d_bundle/` at runtime.
2. Godot may parse traces, extract renderable snapshots, render frame data,
   browse cases, animate playback, and display diagnostics/config metadata.
3. The purpose of the Godot spike is product-shell evaluation: menus, settings
   UX, display clarity, diagnostics panels, and replay readability. It is not
   a semantic core port.
4. Godot must not call Python at runtime, read repo-root
   `migration/exported_bundle/` directly, or scrape `src/`, `config/`,
   `tools/`, `tests/`, or `docs/` at runtime.
5. Godot must not implement gameplay rules, topology transport, score/lock
   logic, or endgame particle simulation semantics in GDScript for this stage.
6. Inspector, scene, and project settings may control replay presentation
   only. They must not become gameplay, topology, config, or endgame semantic
   authority.

### 3.2g Godot core-port decision rules

1. Stage 7 accepts Godot as the primary product shell direction, conditional on
   completed manual visual acceptance of the Stage 6/6b replay viewer.
2. The migration reason is UI/product-shell quality: menus, settings,
   diagnostics, controls, replay readability, and future packaging surfaces.
   It is not a claim that Godot owns stronger gameplay semantics or that
   rendering alone justifies the migration.
3. GDScript is the Godot shell language. It may own menus, settings, rendering,
   replay views, camera/layout behavior, input routing, and diagnostics.
4. GDScript must not own the deterministic gameplay, topology, scoring,
   locking, line-clear, spawn, or endgame particle simulation core.
5. The recommended future core language is C++ through Godot GDExtension.
6. C# is an alternative core language only if port speed clearly outweighs
   export, console, and long-term dependency concerns.
7. Python remains the semantic oracle/reference until a replacement core passes
   topology, gameplay, launch-parity, and endgame trace parity.
8. Stage 7 is planning/governance only. It must not add C++, C#, GDExtension,
   gameplay, topology, endgame, trace, config, or runtime implementation.
9. Stage 8 may start with a C++ GDExtension skeleton, build/test scaffolding,
   and a narrow Godot API boundary, but no gameplay port.
10. The Stage 8 skeleton may expose only native integration proof calls:
    version, status, echo, stable text hash, and integer addition.
11. Stage 8 must not expose gameplay stepping, piece movement, rotation, drop,
    lock, topology, endgame simulation, trace parity, Python runtime, C#,
    Steam, or console packaging APIs.
12. Stage 9 may port only the plain bounded 2D behavior needed to match
    `gameplay_plain_2d_short` required trace fields. It may expose only
    parity/smoke APIs through Godot and must not expose live gameplay controls,
    topology, 3D, 4D, endgame, Python runtime, C#, Steam, or console packaging
    APIs.
13. Stage 10 may add canonical snapshot serialization and `state_hash` parity
    for `gameplay_plain_2d_short` only. It must keep the Godot API parity-only
    and must not broaden into live gameplay controls or non-plain-2D semantics.
14. Stage 11 may broaden plain bounded 2D parity with small Python golden
    traces for rotation, hard-drop lock, and line clear. It may expose only
    case-list, case-export, status, and parity-check APIs through Godot and
    must not expose live gameplay controls, topology, 3D, 4D, endgame, Python
    runtime, C#, Steam, or console packaging APIs.
15. Stage 12 may add live plain bounded 2D controls only through a native C++
    session API. Godot may capture input and render returned snapshots, but it
    must not own collision checks, movement legality, rotation resolution,
    lock, line clear, scoring, spawn, or state hashing.
16. Stage 12b may improve the live plain bounded 2D surface with a C++-owned
    deterministic fixed classic sequence and mode-specific Godot HUD/input
    presentation, but it must keep Stage 11 parity fixtures separate and must
    not broaden into 3D, 4D, topology, endgame, Python runtime calls, or
    Godot-owned gameplay legality.
17. Stage 13 may polish only the same live plain bounded 2D slice. Godot may
    own elapsed-time accumulation, held-key repeat detection, HUD labels,
    mode switching, and rendering, but it may only send command strings to the
    native session. C++ remains authoritative for gravity tick results,
    movement/rotation legality, collision, lock, line clear, scoring, piece
    sequence, game-over, current/next piece reporting, and state hashing.
18. Stage 14 is planning/governance only for plain bounded 3D/4D native
    parity. It must preserve the accepted plain 2D C++/Godot boundary and must
    not implement 3D, 4D, topology transport, endgame simulation, live Godot
    3D/4D gameplay, C#, Python runtime calls from Godot, or Godot-side
    gameplay legality.
19. The next native ND parity target is trace-first:
    `gameplay_plain_3d_short` and `gameplay_plain_4d_short`. Python remains
    the oracle until the C++ core matches those traces, including
    per-frame/final `state_hash`.
20. The preferred Stage 15+ strategy is to add a minimal sidecar plain-ND path
    beside the accepted 2D core, then migrate shared helpers only after
    3D/4D trace parity is proven.
21. Stage 15 may implement only native plain-ND trace scaffolding beside the
    accepted 2D core. The allowed Stage 15 commands are the target trace
    commands `move_axis`, `soft_drop`, and `hard_drop`; the allowed Godot API
    surface is parity/list/export/status only. Stage 15 must not expose live
    Godot 3D/4D gameplay, topology transport, endgame simulation, ND rotation
    beyond explicit golden trace coverage, C#, Python runtime calls from
    Godot, or Godot-side gameplay legality.
22. Stage 16 is coverage planning only and documents the next explicit ND
    trace expansion for rotation, clear/scoring, and spawn-blocked game-over in
    `docs/plans/plain_nd_coverage_expansion_plan.md`; it still does not
    authorize live Godot ND gameplay or broad ND rule implementation.
23. Stage 17 may add Python-oracle plain-ND golden traces for rotation,
    plane-clear/scoring, and spawn-blocked game-over. These traces are future
    C++ parity targets only; Stage 17 must not broaden native ND gameplay,
    expose live Godot ND commands, add topology/endgame behavior, or move
    gameplay legality into Godot.
24. Stage 18 may implement native C++ parity only for the explicit plain-ND
    rotation traces `gameplay_plain_3d_rotation_short` and
    `gameplay_plain_4d_rotation_short`. It may expose those cases through the
    existing parity/list/export/status API only and must not add live Godot
    3D/4D gameplay, topology transport, plane-clear/scoring parity,
    spawn-blocked game-over parity, endgame behavior, C#, Python runtime calls
    from Godot, or Godot-side ND legality.
25. Stage 19 may implement native C++ parity only for the explicit plain-ND
    clear/scoring traces `gameplay_plain_3d_plane_clear_short` and
    `gameplay_plain_4d_plane_clear_short`. It may expose those cases through
    the existing parity/list/export/status API only and must not add live Godot
    3D/4D gameplay, topology transport, endgame behavior, C#, Python runtime
    calls from Godot, or Godot-side ND legality.
26. Stage 20 may implement native C++ parity only for the explicit plain-ND
    spawn-blocked game-over traces
    `gameplay_plain_3d_spawn_blocked_game_over` and
    `gameplay_plain_4d_spawn_blocked_game_over`. It may expose those cases
    through the existing parity/list/export/status API only and must not add
    live Godot 3D/4D gameplay, topology transport, endgame behavior, C#,
    Python runtime calls from Godot, or Godot-side ND legality.
27. Stage 21 is planning-only for the live plain ND Godot prototype. It records
    Stage 22 as live plain 3D first and Stage 23 as live plain 4D, defines the
    future native API, command, rendering, W-slice, HUD, and test boundaries,
    and must not add live 3D/4D implementation, topology transport, endgame
    behavior, C#, Python runtime calls from Godot, or Godot-side ND legality.
28. Stage 22 may add live plain 3D only. C++ must own the live 3D session,
    movement, rotation, drop, tick, lock, clear/scoring, spawn/game-over,
    command status, and state hashing. Godot may route input, manage shell
    cadence/pause/mode switching, render returned snapshots, and display
    HUD/hints through the existing mapper/renderer. Stage 22 must not add live
    4D, topology transport, endgame behavior, C#, Python runtime calls from
    Godot, or Godot-side ND legality.
29. Stage 22b may correct Live 3D rendering and rotation readability only.
    Live 3D cells should be solid, readable cuboids with centralized visual
    roles and outlines, and the HUD may show signed rotation-plane feedback
    from returned C++ command/status data. Godot must not apply independent
    gameplay rotation transforms, fake state interpolation, legality checks,
    scoring, lock, spawn, or hash behavior.
30. Stage 22c may further correct Live 3D exterior cell readability only.
    Godot may alter cell face materials, exterior face geometry, outlines,
    lights, and camera defaults so pieces read as opaque external blocks, but
    must not change C++ ND parity behavior or create a separate coordinate
    system.
31. Stage 22d is design-only. The gameboard visual-language authority is
    `docs/plans/gameboard_visual_language_design.md`. It distinguishes the
    addressed convexity/internal-wall issue from the remaining active-piece
    orientation ambiguity and defines the diagrammatic grammar for Live 3D and
    future Live 4D without implementing rendering changes.
32. Stage 22e may implement that diagrammatic Live 3D grammar only through the
    existing mapper/renderer path. Live 3D requires a canonical exterior
    orthographic view, distinguishable X/Y/Z basis, solid external cubes,
    stable axis/near-far/drop landmarks, at least one explicit active-piece
    origin/orientation cue, visible signed rotation-plane feedback, and
    primary-surface score/status/game-over visibility. The Godot shell must
    reserve left case browser, center board, right inspector, top status, and
    bottom playback regions structurally; side-panel clipping is a layout
    regression, not a width/font tuning problem. Snapshot-to-world projection
    must route through one focused presentation/projection owner before
    renderer nodes.
33. Stage 22f must perform manual Live 3D visual acceptance against the Stage
    22d checklist and `docs/plans/godot_live_3d_manual_acceptance.md`.
    Stage 22f manual Live 3D visual acceptance passed after Stage 22g corrections.
    Stage 23 Live Plain 4D Godot Prototype is implemented narrowly. Live 4D
    must inherit the same cell, axis, rotation-plane, HUD, and landmark grammar
    with stable W-slice context.
34. Stage 22g may correct failed Stage 22f visual acceptance observations only.
    Allowed corrections include an above-board canonical Live 3D default/Fit
    View, visible camera preset/view diagnostics, compact readable bundle
    status with detail text, stronger active-vs-locked cell roles, and an
    active-piece origin/orientation marker. Stage 22g must not change C++
    gameplay semantics, rotation math, trace parity, golden traces, accepted
    Live 2D, Replay, or mapper/renderer ownership. Stage 22f manual Live 3D
    visual acceptance passed after Stage 22g corrections. Stage 23 Live Plain
    4D Godot Prototype is implemented narrowly through C++ `PlainNDSession`,
    side-by-side W slices, Q/E W movement, and six direct rotation plane pairs
    without changing topology, endgame, or golden trace authority.
35. Stage 23b may correct Live 4D manual acceptance defects only. Allowed
    corrections include larger/readable W labels, Space hard-drop capture
    before focused UI accept handling, and restrained active-cell brightness
    while preserving active/locked distinction. Stage 23b must not change C++
    gameplay semantics, trace parity, topology, endgame, Python runtime calls,
    Godot-side legality, or the accepted Live 2D/Live 3D/Replay behavior.
    Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
    Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain
    bounded prototype. Stage 24 Live ND polish and hardening is now unblocked.
    Topology and endgame remain deferred.
36. Stage 23c may correct Live 4D view and W-slice readability defects only.
    Allowed corrections include explicit W-slice headers/chips, fitted Live 4D
    entry/reset, Fit View recovery for the full W-slice layout, and limited
    camera adjustment controls that do not overlap gameplay controls. Live 3D
    may continue relying on its fixed canonical exterior view. Live 4D requires
    a canonical fitted default plus safe camera adjustment. Stage 23c must not
    change C++ gameplay semantics, trace parity, topology, endgame, Python
    runtime calls, Godot-side legality, or the accepted Live 2D/Live 3D/Replay
    behavior.
37. Stage 23d may correct Live 4D zoom-control defects only. Allowed
    corrections include changing orthographic camera size for `-`/`=`/`+`,
    robust minus/equal/plus key detection, camera diagnostics that expose size
    and zoom state, pre-UI camera-key capture in Live 4D, and Fit View
    recovery for the canonical fitted W-slice layout. Stage 23d must not
    change C++ gameplay semantics, trace parity, topology, endgame, Python
    runtime calls, Godot-side legality, or the accepted Live 2D/Live 3D/Replay
    behavior.
    Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
    Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain
    bounded prototype. Stage 24 Live ND polish and hardening is now unblocked.
    Topology and endgame remain deferred.
38. Stage 24 may harden live ND shell lifecycle and input focus only. Allowed
    corrections include resuming the selected Live 2D/3D/4D mode when returning
    from Replay without resetting native C++ session state, pausing
    non-selected live modes, clearing live UI focus and repeat state on entry,
    preserving pre-UI Space hard-drop capture, and preserving pre-UI Live 4D
    camera/zoom capture after focus changes and mode switching. Stage 24 must
    not change C++ gameplay semantics, trace parity, topology, endgame, Python
    runtime calls, Godot-side legality, or accepted Live 2D/Live 3D/Replay
    behavior. Manual Stage 24 acceptance is required before Stage 25 topology
    planning.
39. The migrated Godot Live 3D shell should prefer snapping to returned C++
    state plus clear plane feedback over a misleading Godot-side rotation
    tween. A future Godot presentation tween is allowed only if it is derived
    from and cannot contradict returned native state.

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
12. `cellwise_deformation` from unsafe seam crossings must be surfaced explicitly and blocked for rigid-piece gameplay instead of being silently canonicalized into a new local frame. Explorer-mode traversal legality remains cellwise-owned and must continue to allow those non-safe seam traversals.

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
10. Leaderboard entries are recorded only for completed standard-play `game_over` sessions, never for explorer-mode runs or quit/menu/restart exits, and storage keeps the top `10` scores per gameplay dimension.
11. Deterministic replay rule applies to `(seed, topology selection, kick_level, input stream)`.

## 4. Shared UX Requirements

1. Menu/setup screen before starting each mode.
2. In-game panel with score, cleared lines/layers, speed, controls, and game-over state.
3. Toggleable grid/projection-guide modes must exist in all modes.
4. Shared grid mode cycle is `off`, `bottom_boundary`, `edge`, `full`, `helper`, `all_boundaries`.
5. When grid is off, a board shadow/silhouette must still provide spatial context.
6. `bottom_boundary` and `all_boundaries` are render-only active-piece projection-guide modes derived from the current active-piece render state plus stable board presentation; they must not change legality, lock, ghost behavior, board-fit logic, or explorer traversal permission.
7. Layer/line clear feedback should be animated.
8. Setup and pause menus must expose equivalent controls/keybinding editing actions.
9. A unified startup menu must allow choosing 2D/3D/4D and shared settings.
10. Audio controls (master volume, SFX volume, mute) must be available in settings.
11. Fullscreen/windowed toggle must be supported without layout corruption.
12. Piece rotations must use a soft visual animation instead of a single-frame snap.
13. 3D/4D locked-cell transparency must be user-adjustable from settings with default `25%` and allowed range `0%..90%`.
14. Locked-cell transparency must affect locked board cells only (challenge layers + landed pieces); active-piece cells remain opaque.
15. Piece generation must support both fixed-seed deterministic runs and true-random runs with user-configurable setup controls.
16. Terminal game-over presentation must use a dedicated post-terminal phase model `playing -> endgame_shatter -> endgame_relic_field`; the animation must render from a frozen endgame snapshot instead of mutating live gameplay entities.
17. The frozen endgame snapshot must capture locked cells, board dimensions, the render/projection context needed to keep projection/camera stable, deterministic animation seed inputs, and the topology/seam inputs needed by the locked-cell explosion subsystem.
18. Locked-cell endgame motion must be owned by a dedicated seam-aware explosion subsystem that simulates per-cell particles rather than gameplay tetromino objects or live board ownership. That shared explosion state may keep bounded render-only centerline trail history in board coordinates, but trail generation must not mutate gameplay or explosion physics.
19. Connected seams in that subsystem must transport both particle position and particle velocity through the same seam transform; transporting position without transforming velocity is invalid.
20. Locked-cell explosion interaction must be modeled on two independent axes: `boundary_response` (`escape` or `bounce`) and `particle_collisions` (`off` or `on`). Connected seams are not an option toggle and must always transport both particle position and particle velocity when a seam exists; `boundary_response` applies only to non-connected boundaries. Particle-particle collision response must expose a live numeric coefficient-of-restitution control `e in [0, 1]` where `e = 1` is fully elastic and `e = 0` is maximally inelastic along the collision normal. Boundary bounce may remain on its existing separate rule if that boundary behavior is intentionally held elastic.
21. The locked-cell explosion subsystem must land in staged order: standalone simulator first, explorer/topology-playground launch second, and game-end handoff third. The standalone simulator must be directly launchable from the main launcher without entering explorer mode or reaching game over first, while explorer launch remains explorer-owned and must not inherit gameplay-only legality restrictions.
21a. The dedicated standalone/explorer explosion simulator UI may remain distinct from the normal explorer shell, but it must render explosion objects as tet4d cell-like units rather than balls/circles, must provide true `2D` / `3D` / `4D` coverage through existing dimensional scene/render machinery, and must source standalone topology choices from the existing explorer topology preset registry instead of a simulator-local topology list.
21b. In `3D` and `4D`, the simulator must support a true board-native view that reuses the existing gameplay board presentation rather than only topology-playground projection panes. A projection reference view may remain optional, but true board view must be the default simulator path.
21c. The simulator must expose explicit snapshot sources: inherited current state when launched from explorer/gameplay-owned handoff, plus standalone engine-backed `single_cell`, `single_piece`, and `piece_change` sources. `single_piece` must use canonical gameplay piece definitions, and `piece_change` must be documented as a deterministic engine-backed current-piece to next-piece transition snapshot rather than a simulator-local ad hoc shape mix.
21d. The shared explosion simulation state must expose live kinetic-energy diagnostics computed from the active particle velocities using the current simulation dimension only. The simulator UI must display a live compact formula form sourced from shared simulation state rather than a UI-only physics reimplementation: `K = 1/2 Σ (m_i ||v_i||^2)` with live compact numeric `m_i` and `||v_i||` terms derived from the current particle set, formatted as squared speed magnitudes rather than pre-squared numeric totals, factoring out a common mass as `K = 1/2 m [ ... ]` when masses are uniform and otherwise showing compact weighted terms `K = 1/2 [m1*||v1||^2 + m2*||v2||^2 + ...]`. The display may truncate long expansions with `...`, but it must stay live against the current particle state and must not become stale while the real kinetic energy changes. The simulator must expose both a uniform-mass mode and a deterministic seed-backed random-mass mode, with random masses drawn reproducibly from a bounded configurable range for the current particle set. That same shared state must also support a non-mutating movement-diagnostics monitor with `off` / `summary` / `full` modes, using the live mass and elasticity settings to compare substages `before step`, `after free flight`, `after seam transport`, `after boundary resolution`, `after particle collision resolution`, and `after finalize/nudge`, so suspicious heading changes, wrong-stage energy changes, and repeated-contact snagging can be localized without relying on final-frame energy alone.
21e. Simulator text/layout must follow the shared wrapped-row contract: labels, values, helper text, status text, and aggregate energy readouts must wrap within their panel widths, reserve vertical space for wrapped lines, and remain fully visible without overlap or obscuration at supported window sizes.
21f. The standalone/explorer explosion simulator must expose an explicit `Trace` overlay toggle plus a bounded numeric trace-retention control that remains directly text-editable while keeping a numeric backing value. When enabled, the preview must draw clearly visible tapering per-particle centerline trails from capped shared history using the active simulator view, including seam-break handling and post-escape continuation, rather than replacing tet4d cell rendering or mutating the shared simulation semantics. In board-native `3D` / `4D`, those trails must project the same actual particle centers used by the rendered explosion cells; render-only half-cell offsets are invalid, bounce contacts must contribute the true boundary-plane contact point to shared trail history before any post-contact interior stabilization/nudge is applied, and bounce frames must also retain the immediate same-frame post-contact continuation sample so the visible trace does not imply a fake pause at the wall.
21g. The standalone/explorer explosion simulator true-board view must route board presentation through the shared grid-mode system rather than simulator-local toggles. That includes selectable `none` / `edge` / `full` grid presentation plus render-only `bottom_boundary` and `all_boundaries` shadow modes, believable board-vs-cell occlusion in `3D` / `4D`, and visible seam/bounce contact that starts on the actual board boundary rather than outside the box.
21g1. The true seam/bounce boundary, the drawn board box, edge-grid lines, and render-only boundary/shadow guides must all reuse one canonical board-face definition per axis. That canonical boundary is the cell-extent box with board-face planes at `-0.5` and `size - 0.5` in board coordinates, not center-crossing planes at `0` and `size`.
21h. In that simulator path, `grid_mode` and shadow/projection-guide selection must remain independent controls. Grid selection must not silently force shadow selection, shadow selection must not silently force grid selection, and both must stay render-only with no simulation-state side effects.
21i. The explosion simulator `3D` / `4D` true-board preview must reuse the existing ND scene-camera control family already used by gameplay/explorer board views rather than introducing simulator-local orbit semantics, touched simulator rows must keep typed input discipline so categorical values render as selector/dropdown affordances, and the `4D` true-board preview must expose selectable `fade` and `box_size` W-movement animation styles by reusing the existing gameplay-style layer-transition behavior where available.
21j. Explosion defaults persistence must use one shared config-backed authority for both the standalone/explorer simulator and the later game-end explosion handoff. The simulator must expose a real `Save` action that persists only persistent explosion-default fields such as topology/snapshot selection, boundary/collision/mass/elasticity settings, diagnostics preference where treated as user preference, trace/grid/shadow/view preferences, speed preset, sound, seed, and `endgame_live_cell_fraction`; transient runtime state such as live particle positions/velocities, traces, diagnostics logs, focused particle selection, dropdown/hover state, and frame counters must not be serialized. The saved explosion-default model must then seed standalone simulator startup defaults, explorer-triggered simulator defaults where relevant, and the overlapping endgame explosion-controller defaults without maintaining separate simulator-only and endgame-only copies. Endgame settings may provide only endgame-specific preset/speed/chrome inputs and must not override shared saved boundary, collision, mass, diagnostics, trace, grid/shadow, W-movement, speed, sound, seed, or live-fraction defaults.
21k. Endgame must keep using the shared explosion runtime/session builder, but it must no longer release every locked board cell into live simulation by default. Instead, it must deterministically select a readable live subset from available locked cells as `0` when no locked cells exist, otherwise `clamp(round(endgame_live_cell_fraction * available_locked_cells), minimum=1, maximum=available_locked_cells)`; the default saved fraction is `0.12`. Non-selected locked cells must stay out of the live explosion simulation set, while gameplay topology and locked-cell sources remain the runtime handoff inputs. Endgame capture must pass the full selected topology seam rules into the shared survivor runtime so bounded, wrap, and invert topology modes affect survivor motion, including gravity-axis seams when the selected topology defines them; gameplay drop/lock policy may still keep stricter gravity-axis traversal rules and must not be changed by endgame rendering. Native-board endgame moving-cell rendering must consume only that selected live subset; escaping cells must be represented only as capped, deterministic, short-lived shell artifacts plus bounded grid-break overlay marks derived from those artifacts, and must not be reconstructed as board-native particles, full cell/cube render states, or a destructible grid model. The endgame surface may retain a low-alpha cracked-board residue derived from capped grid-break marks and static shell state so survivor particles keep a damaged-board context after rupture. Trace rendering, shadow/projection-guide defaults, and 4D W-movement style defaults must affect the actual endgame render path where applicable.
21k1. The standalone explosion simulator may expose a preview-only staged shell harness for those escaping-cell artifacts, but that harness must remain non-mutating: frozen source cells hold during the charge phase, rupture may render capped short-lived cell/cube proxies derived only from source cells plus selected boundary impacts, those proxies must remain draw-state-only and must never enter the shared controller/runtime particle set, preview timing/time-scale controls affect only that simulator harness, and actual gameplay endgame wiring remains a later stage. Causal shell sequencing and shell-sound trigger data should be modeled as one event chain so later renderer/audio adapters consume one source-to-impact-to-shard-to-residue sentence rather than disconnected phase lists.
22. When leaderboard registration is offered from the post-terminal path, it must open as a compact modal overlay on top of the existing endgame/post-game surface rather than navigating to a dedicated full-screen registration screen; the existing registration form state and submission authority must remain singular, and background gameplay/menu input must stay suppressed while the modal is open.
23. Tutorial overlay panel must be enlarged for readability, present one clear plain-language primary action line plus one optional tip line, and in 3D/4D default to a side-panel-safe lane outside the active board/layers area.
24. Tutorial progression must expose explicit segment order:
25. translations -> piece rotations -> camera rotations (3D/4D) -> camera controls (`toggle_grid`, transparency) -> goals (line/layer/full-board clear).
26. System controls (`help`, `menu`, `restart`, `quit`) are guidance-only in tutorials and must not require dedicated interactive stages.
27. Movement and rotation tutorial stages require repeated successful actions (`4` per direction stage) before progression.
28. The tutorial `toggle_grid` stage must cover the full shared grid-mode cycle, including `bottom_boundary` and `all_boundaries`.
29. Settings keep endgame/explosion controls inside the scrolling `Settings -> Game` page as an `Endgame Effects` section, including `boundary_response` (`escape` / `bounce`), `particle_collisions` (`off` / `on`), locked-cell explosion speed controls, and shatter-speed control, while the same page also owns shared rotation animation mode, kick permissiveness (`kick_level`), and shared piece motion animation durations for rotation and deliberate translation tweens across 2D/3D/4D.
30. Launcher, pause, settings, and keyboard bindings menu structure must derive from one canonical authored config tree in `config/menu/structure.json`, then normalize into the runtime graph consumed by rendering/navigation/input; oversized settings/keybindings pages must use the shared scrolling viewport and scrollbar path instead of clipping rows or defining page-local overflow behavior.
31. Ordinary play launcher/setup surfaces must stay minimal for topology: safe preset selection only, plus launcher routes to `Play Last Custom Topology` and `Topology Playground` for custom topology work.
32. Launcher learning/support IA must keep `Tutorials` first-class while leaving the internal split explicit: `Interactive Tutorials` for guided onboarding, `How to Play` for gameplay explanation, `Controls Reference` for shortcut/action legend, and `Help / FAQ` for broader support/troubleshooting.
33. Launcher configuration IA must keep `Settings -> Keyboard Bindings` as persistent input configuration only; authored wrapper groups may exist in config, but one-item runtime pages must collapse away instead of surviving as visible structure. Controls reference/help content must not be folded into that settings destination.
34. Launcher `Leaderboard` and `Bot` must not be root destinations or `Settings` entries in the visible-shell pass; they belong to play-adjacent flow instead.
35. For topology-playground migration-state questions, `docs/plans/topology_playground_current_authority.md` is the current architecture authority. Older topology-playground manifests and stage plans are historical unless explicitly reactivated.
25. Explorer Topology Lab must use a scene-first graphical explorer shell for 2D/3D/4D, with direct seam selection, engine-backed probe traversal, explorer-only sandbox interaction, and play launch from the current draft topology. Live Explorer launch must enter that same shell directly rather than a separate detached explorer frontend.
25. The Explorer Playground shell must expose an explicit controls/scene pane model, generated pane-aware helper text, mouse-adjustable +/- value controls, and synchronized 2D coordinate-plane projections as the default 3D/4D primary visualization: `3D` uses `xy/xz/yz`, `4D` uses `xy/xz/xw/yz/yw/zw`, all panels share one canonical selected-cell/topology/move-preview/seam-focus state, and hidden coordinates must stay explicit in every panel. Free-camera 3D/4D views may remain optional debug-only helpers, but they must not remain the primary Explorer Playground interface.
26. The Explorer Playground shell must be able to compile and export a parallel experiment pack from the current draft plus the active dimension's preset family, persist that pack under `state/topology/`, and surface a recommended next topology directly in the shell.
27. For the migrated Explorer Playground path, explorer rendering, topology visualization, and explorer-side selection/probe highlighting must consume the engine/runtime-owned `TopologyPlaygroundState`; retained UI-local mirrors may remain only as additive synchronized compatibility projections during migration, not as explorer-path input authority. When a compatibility mirror no longer has an active caller, it must stop re-synchronizing from canonical state rather than lingering as a full shadow copy; `explorer_profile` / `explorer_draft`, seam-selection/highlight state, and probe-state reads/writes must route through canonical selectors/helpers rather than synchronized shell copies. Retired profile/draft shell fields may survive only as fallback storage when canonical state is absent, but the old raw probe trio (`probe_coord`, `probe_trace`, `probe_path`) must not survive as retained fallback storage on the migrated path.
28. For the migrated core gluing workflow, explorer-side boundary picks, seam picks, and linked transform-editor slot selection must update the engine/runtime-owned `TopologyPlaygroundState` selected boundary, selected seam, and normalized gluing draft immediately; one full seam edit must complete without round-tripping to another menu.
29. The diagnostics pane must be clearly labeled as a secondary research/diagnostics surface; core seam authoring remains in the graphical explorer plus linked transform editor/action workspace and must not depend on row-based diagnostics controls. Explorer preset changes plus save/export/experiment/back administrative commands may live there, but duplicate copies must not compete with the action workspace, and read-only seam-context rows must look read-only rather than editable. UI maintenance should keep contextual row ownership isolated in dedicated helpers rather than rebuilding one mixed shell file, shell-facing row values/playability/context formatting should stay on that extracted helper side rather than drifting back into `controls_panel.py`, and any retained Normal Game support must stay narrow rather than reintroducing a generic catch-all helper. Legacy row adjustment may live in `controls_panel.py` if it remains private and does not retake row layout/value presentation or export orchestration ownership.
28. The Explorer Playground primary workspace ribbon must expose `Editor`, `Sandbox`, and `Play` as the only top-level workspace buttons. Editor-tool selection belongs to contextual secondary controls, and the footer movement grid must identify whether it moves the editor probe or the sandbox piece.
29. Invalid explorer topology / board-size pairings must remain attached to the current canonical draft topology across explorer entry, preview, sandbox, and play-launch surfaces; the playground may mark the topology invalid and block incompatible actions, but it must not silently substitute a fallback topology or drop the seam.
30. The Explorer Playground must surface one coherent runtime-derived playability signal for the current topology before launch, explicitly distinguishing validity, cellwise explorer usability, rigid playability, and the reason the current topology is invalid or explorer-only; this signal must be derived from canonical runtime state rather than preset labels or UI-only guesses.
31. The Explorer Playground workspace model must be centered on `editor`, `sandbox`, and `play` both internally and in the visible top-level shell. `Edit` may remain only as an editor-scoped tool name, and legacy inspect naming may remain only as compatibility input at normalization/deserialization boundaries, not as a primary workspace or active visible copy path.
32. Movement targets must be workspace-specific: `editor` moves only the editor probe/selection, `sandbox` moves only the sandbox piece, and `play` moves only the gameplay piece. Editor movement must stay non-mutating even when the active Editor tool is an explicit edit tool, and the editor probe/dot must remain visible in both Probe and Edit.
33. The legacy Inspect dot is the Editor probe/dot. Its movement, rendered position, and trace path must stay consistent before and after seam traversal, and that consistency requirement applies equally in `2D`, `3D`, and `4D`.
33a. The current visible-shell phase does not require the older `3D` / `4D` per-panel movement-preview legends. The accepted reduced guidance is that the probe remains movable and the shell helper exposes the full translation keys for the active dimension.
34. Editor trace visibility must be controlled by an explicit `Trace` contextual control owned by `Editor`, not by a floating/global Explorer exception. Disabling trace must not hide or disable the editor probe/dot itself.
34a. The canonical probe trace visual language is now the connecting trace line itself; intermediate path dots are intentionally removed across dimensions during this phase.
35. Editor must also support an explicit `Probe Neighbors` contextual overlay owned by `Editor`. That overlay must derive from the same canonical seam-aware probe state as probe movement, trace, and edit targeting; it must render adjacent targets as smaller subordinate dots; and toggling it must not hide the main probe dot.
36. Sandbox neighbor-search must be explicit runtime/menu state rather than hidden ND-only behavior; the playground must support sandbox piece experimentation with that overlay both enabled and disabled, while keeping the sandbox piece itself visible/usable in `3D`/`4D` by selecting/framing a visible sandbox cell rather than an abstract stale origin when the overlay is off or the piece has moved. The visible `Neighbors` control is Sandbox-owned contextual UI, not a floating/global Explorer toggle.
37. Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and `4D`.
38. In `3D` and `4D`, projected sandbox piece cells must render as clear piece boxes rather than neighbor-style dots.
39. Neighbor markers must appear as small dots only when the explicit Explorer `neighbor search` control is enabled, and those markers must not replace, hide, or visually masquerade as the sandbox piece.
40. On the live `Play This Topology` path, move acceptance, continued fall eligibility, support/grounded checks, lock decisions, and active-piece rendering inputs must all derive from the same canonical gameplay state rather than retained shell snapshots, panel-owned selection state, or projection-only coordinates.
40a. `2D` keeps its simpler cell/grid layering path; projected-depth board-line occlusion machinery is for projected `3D` / `4D` board-box renderers only.
40b. In projected `3D` / `4D` board-box renderers, board gridlines and box edges must resolve visibility against the active piece per projected fragment based on screen-space overlap plus projected depth, not by one global whole-pass ordering.
40c. When projected board lines cross the active-piece projection, the renderer must split them into under-piece and over-piece fragments before final draw ordering.
41. Play-mode movement classes must remain explicit: deliberate translation, rotation, gravity tick, soft drop, and hard drop must not silently share one generic seam-transport rule.
42. Groundedness and lock in Play must be computed from whether one legal gravity/drop step exists under the Play drop policy; generic adjacency, generic seam existence, and non-drop reachability must not count as fall continuation.
43. Play drop legality may be stricter than deliberate/topological translation: lateral or other non-drop motion may enter legal bottom-layer space through the topology, while gravity/soft-drop/hard-drop may still be forbidden to continue through a non-trivial gravity-axis seam.
44. Explorer Playground helper text/panel selection must be keyed to the canonical workspace model (`editor` / `sandbox` / `play`). Editor helper content may vary by the active Editor tool, but legacy tool labels must not retake the primary top-level role. Workspace-shell copy/layout/helper routing should remain in dedicated shell helpers rather than drifting back into one monolithic menu/orchestration module, and those shell helpers should consume stable scene/value selectors instead of private adjustment helpers from `controls_panel.py`.
45. The Explorer Playground scene shell must keep an explicit right-side helper panel visible outside the explorer viewport. That helper must stay concise for the topology-editor shell: minimal translation keys, minimal rotation keys, and at most one short workspace/tool-context line. It must not become a second menu or status dump.
46. Menu items, workspace controls, and critical actions in the Explorer shell must remain fully visible and readable. Clipped, hidden, or effectively unusable labels are regressions.
47. The frozen visible-shell redesign must keep the default topology-playground surface compact: top bar with title/workspace tabs/validity, left sidebar with active-workspace contextual controls only, larger center workspace, small right helper, and compact bottom strip for status/actions. Verbose diagnostics and internal-facing labels such as `Analysis View`, `Explorer Workspace`, `Workspace Path`, and `Editor Tool` must be removed from the default-primary shell or demoted behind diagnostics surfaces.
48. Direct Topology Playground launch must remain available both through the launcher route and through the unified CLI wrapper: `cli/front.py --topology-playground [2|3|4]`. The older `python -m tet4d.ui.pygame.topology_lab [2|3|4]` entrypoint may remain as a thin compatibility delegate, but it must not carry a second independent launch implementation.

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
6. During any active-piece translation or rotation tween, board presentation must remain stable for the full tween: viewport fit, board anchoring, projection basis, grid geometry, and locked-cell projection must not be recomputed from transient animated piece geometry. Projected-mode renderers must build that frozen presentation once per discrete move/tween start and then reuse it across tween frames.
7. Ordinary translations and safe seam traversals must preserve stable per-cell identity from the gameplay/transport path, and non-safe seam traversals must still interpolate from explicit transport-derived correspondence; render interpolation must not rematch destination cells by sorting, canonicalization, nearest-neighbor pairing, or any other unordered-set heuristic. That classification controls presentation/correspondence only; explorer-mode traversal permission must not be blocked by gameplay-only rigid-play constraints.

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
22. Repo governance and maintenance contract rules are defined in:
23. `config/project/policy_pack.json`
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
34. Local verification and test harnesses may override the runtime state root through `TET4D_STATE_ROOT`; source-tree defaults remain under the project root, while frozen builds must route writable state under a platform user-data root, and resolved override paths must remain under the selected root.
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
46. `migration/golden_traces/**/*.json`
47. `docs/help/HELP_INDEX.md`
48. `config/project/policy/manifests/help_assets_manifest.json`
49. `docs/RELEASE_CHECKLIST.md`
50. Endgame animation tuning authority lives in `config/project/constants.json` under `animation.endgame`; shatter duration, shell lifetime/fade, burst impulse/spin, capture timing, relic-field speed/radius/depth/path-family weights, preset defaults/registry data, field bounds, and collision tuning must not be hardcoded only in Python.
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
5. Explorer preset libraries now keep sphere-like transport presets available alongside quotient presets for 2D/3D/4D, but must classify them honestly: clean quotient families, advanced quotient families, sphere-like / compactified transport heuristics, and experimental transport must remain visibly separate, and labels/descriptions must not present sphere-like heuristics as clean quotient spaces. Legality remains engine-owned in `src/tet4d/engine/topology_explorer/glue_validate.py`, not UI-owned.
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
