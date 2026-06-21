# Python Oracle Boundary Audit

## Purpose

This Stage 23 audit separates gameplay semantic authority from incidental
Python implementation history.

Python gameplay semantics and golden traces remain the current oracle. Python
UI history, pygame scaffolding, obsolete helpers, duplicated utilities, and
temporary migration harness layout are not automatically authoritative.

Use this rule before porting Python material into Godot or C++:

```text
If changing it would make the game a different game, it is oracle material.
If changing it only makes the product cleaner, it is not oracle material.
```

This document is an anti-porting-junk audit. It helps future migration stages
avoid reproducing old Python UI, pygame, helper-panel, config, or migration
scaffolding when those surfaces do not define gameplay semantics.

## Classification Definitions

| Category | Meaning | Porting rule |
| --- | --- | --- |
| Semantic oracle | Actual game rules/behaviour | Preserve until parity proves replacement |
| Useful implementation | Current working implementation, not sacred | Reuse or replace pragmatically |
| Historical scaffolding | Exists because pygame/project evolved messily | Do not port unless needed |
| Dead weight / do-not-port | Legacy, duplicated, misleading, obsolete, or temporary | Delete, quarantine, or explicitly mark do-not-port |

Additional audit labels used below:

| Category | Meaning | Porting rule |
| --- | --- | --- |
| Mixed | Contains both semantic material and replaceable scaffolding | Preserve semantic behavior; redesign incidental structure |
| Unknown / requires later audit | Not enough evidence from this pass | Do not port blindly |

## Semantic Oracle Criteria

A Python surface is semantic-oracle material if changing it would alter:

- topology rules
- board coordinate meaning
- legal movement
- rotation semantics
- dimensional movement semantics
- drop/collision/lock behaviour
- clearing behaviour
- piece lifecycle
- fixture/golden trace meaning
- trace output that reflects real gameplay state

## Non-Oracle Criteria

A Python surface is probably not semantic authority if changing it only affects:

- pygame layout
- menu structure
- panel arrangement
- helper-panel wording
- legacy names
- rendering style
- camera/view presentation
- duplicated utility plumbing
- temporary migration harness location
- generated maintenance-document layout
- old config surfaces no longer used as authority

## Surface Inventory

This inventory is based on the repository tree present during Stage 23. Literal
paths `src/tet4d/core/`, `src/tet4d/topology/`, and `src/tet4d/game/` were not
found; their current equivalents are under `src/tet4d/engine/core/`,
`src/tet4d/engine/topology_explorer/`, and `src/tet4d/engine/gameplay/`.

| Surface | Classification | Notes |
| --- | --- | --- |
| `src/tet4d/` | Mixed | Package root containing semantic engine code, replay helpers, shared coordinate helpers, AI/playbot logic, and pygame UI history. |
| `src/tet4d/core/` | No matching path found | Omitted as a literal path; current core surfaces live under `src/tet4d/engine/core/`. |
| `src/tet4d/topology/` | No matching path found | Omitted as a literal path; current topology surfaces live under gameplay/topology-explorer packages. |
| `src/tet4d/game/` | No matching path found | Omitted as a literal path; current game surfaces live under `src/tet4d/engine/gameplay/`. |
| `src/tet4d/engine/core/model/` | Semantic oracle | Board and game-state value objects define coordinate/state meaning used by rules and tests. |
| `src/tet4d/engine/core/rules/` | Semantic oracle | Board rules, gravity, lifecycle, locking, placement, scoring, and state queries are direct game-rule surfaces. |
| `src/tet4d/engine/core/step/reducer.py` | Semantic oracle | Reduces commands into gameplay state transitions. |
| `src/tet4d/engine/core/piece_transform.py` | Semantic oracle | Piece transform behavior affects rotation/placement semantics. |
| `src/tet4d/engine/core/rotation_kicks.py` | Semantic oracle | Rotation-kick behavior affects legal rotation outcomes. |
| `src/tet4d/engine/core/rng/engine_rng.py` | Mixed | Deterministic gameplay RNG behavior can be oracle material; implementation shape is replaceable if outputs stay equivalent. |
| `src/tet4d/engine/gameplay/` | Mixed | Contains central gameplay/topology semantics plus mode adapters and some runtime glue. |
| `src/tet4d/engine/gameplay/game2d.py` | Semantic oracle | Owns current 2D gameplay loop behavior. |
| `src/tet4d/engine/gameplay/game_nd.py` | Semantic oracle | Owns current 3D/4D plain-ND gameplay behavior. |
| `src/tet4d/engine/gameplay/pieces2d.py`, `pieces_nd.py`, `pieces_shared.py` | Semantic oracle | Piece shapes, dimensional coordinates, and lifecycle expectations affect legal gameplay. |
| `src/tet4d/engine/gameplay/lock_flow.py` | Semantic oracle | Lock/drop policy is explicitly oracle material. |
| `src/tet4d/engine/gameplay/play_move_intents.py` | Semantic oracle | Movement intent mapping affects legal movement semantics. |
| `src/tet4d/engine/gameplay/topology.py` | Semantic oracle | Topology behavior and labels affect movement and trace meaning. |
| `src/tet4d/engine/gameplay/topology_designer.py` | Mixed | Topology construction and validation are semantic; designer workflow shape is replaceable. |
| `src/tet4d/engine/gameplay/explorer_movement_policy.py`, `explorer_piece_transport.py`, `explorer_runtime_2d.py`, `explorer_runtime_nd.py` | Mixed | Sandbox-vs-Play movement and transport behavior are semantic; explorer runtime wiring is replaceable. |
| `src/tet4d/engine/gameplay/challenge_mode.py`, `exploration_mode.py` | Mixed | Mode rules may be semantic where they change gameplay eligibility or state transitions; presentation and menu flow are replaceable. |
| `src/tet4d/engine/gameplay/leveling.py`, `scoring_bonus.py`, `speed_curve.py` | Semantic oracle | Scoring, leveling, and speed defaults affect current gameplay behavior. |
| `src/tet4d/engine/gameplay/rotation_anim.py` | Useful implementation | Animation timing is presentation unless tests prove it drives semantic state. |
| `src/tet4d/engine/topology_explorer/` | Mixed | Glue maps, movement graphs, presets, and transport resolution influence topology authority; editor/explorer organization is not sacred. |
| `src/tet4d/shared/nd_coords.py` | Semantic oracle | Coordinate normalization and dimensional labels affect board and trace meaning. |
| `src/tet4d/replay/format.py` | Mixed | Replay schema/format fields tied to real gameplay state are oracle material; serializer organization is replaceable. |
| `src/tet4d/ai/` | Useful implementation | Playbot/planner code is useful for automation and tests, but is not automatically gameplay authority unless it encodes fixture expectations. |
| `src/tet4d/ui/` | Historical scaffolding | UI package location is not semantic authority by itself. |
| `src/tet4d/ui/pygame/` | Mixed | Some pygame live shells call semantic Python gameplay, but pygame rendering, panels, menus, layout, and shell flow are not automatically authoritative. |
| `src/tet4d/ui/pygame/front2d_game.py`, `front3d_game.py`, `front4d_game.py` | Mixed | Any delegated gameplay calls or golden-trace-aligned state handling must be preserved; pygame loop/presentation structure should not be ported blindly. |
| `src/tet4d/ui/pygame/front2d_*`, `front3d_render.py`, `front4d_render.py`, `frontend_nd_*` | Historical scaffolding | Pygame setup, input loop, and render organization are product-shell history unless they encode gameplay results. |
| `src/tet4d/ui/pygame/menu/` | Historical scaffolding | Menu runner, keybinding menu, setup menu, and numeric input are UI history, not gameplay semantics. |
| `src/tet4d/ui/pygame/launch/` | Historical scaffolding | Launcher/menu routing is replaceable shell behavior. |
| `src/tet4d/ui/pygame/render/` | Historical scaffolding | Panel, icon, text, grid, projection-guide, and cell-render helpers define pygame presentation, not game rules. |
| `src/tet4d/ui/pygame/runtime_ui/` | Historical scaffolding | Pause/help/tutorial/app loop panels are pygame shell history. |
| `src/tet4d/ui/pygame/input/` | Useful implementation | Input dispatch and camera controls are useful references for product expectations; they are not semantic movement rules unless they map directly into gameplay commands. |
| `src/tet4d/ui/pygame/topology_lab/` | Mixed | Editor/Sandbox/Play distinctions and launch eligibility are semantic per current topology authority; controls panels, layout, camera, preview, and workspace shell are replaceable. |
| `src/tet4d/ui/pygame/locked_cell_explosion/` | Mixed | Headless model/simulation/topology surfaces feed endgame golden traces; launcher, surface, render, board view, preview, and audio are presentation/scaffolding. |
| `tools/migration/` | Mixed | Exporters, trace schema helpers, comparison harnesses, and parity harnesses preserve oracle evidence; their current directory layout is temporary migration organization. |
| `tools/migration/export_topology_trace.py`, `export_gameplay_trace.py`, `export_endgame_trace.py`, `trace_cases.py`, `trace_schema.py`, `compare_trace.py`, `compare_cpp_gameplay_trace.py` | Semantic oracle / useful implementation | They define and verify current migration evidence; harness code can be reorganized only if trace meaning and comparisons remain equivalent. |
| `tools/parity/first_subsystem_parity_pilot.py`, `trace_metadata_identity_digest_parity.py`, `topology_identifier_normalization_parity.py`, `trace_schema_version_normalization_parity.py` | Useful implementation | Maintained parity/evidence harnesses are authoritative for their documented evidence boundaries, but not gameplay authority or permanent package layout. |
| `tools/migration/export_config_bundle.py`, `sync_godot_bundle.py`, `sync_unity_bundle.py`, `compare_config_bundle.py` | Useful implementation | Bundle and sync tooling is migration support; exported copies are not sources of truth. |
| `tests/fixtures/` | Mixed | Present fixture area contains parity fixtures; fixture semantics are authoritative where docs identify them as evidence. |
| `tests/fixtures/parity/` | Semantic oracle | Committed parity fixtures encode current semantic/evidence expectations for the maintained parity slices. |
| `tests/unit/` | Mixed | Tests encode current behavioral expectations. Gameplay/topology/migration tests are oracle evidence; UI/layout tests are product-shell expectations. |
| `migration/golden_traces/` | Semantic oracle | Checked-in topology, gameplay, and endgame traces are Python-authoritative migration oracle evidence. |
| `config/` | Mixed | Gameplay, topology, schema, project policy, and defaults can be authoritative; obsolete UI/config surfaces are not automatically semantic. |
| `config/gameplay/` | Semantic oracle | Piece sets, tuning, and scoring defaults affect gameplay behavior. |
| `config/topology/` | Semantic oracle | Topology designer presets affect topology construction expectations. |
| `config/schema/` | Mixed | Schemas are authoritative for data contracts; schema file organization is replaceable. |
| `config/project/` | Mixed | `policy_pack.json` and policy-backed constants are governance/config authority; generated or maintenance input structure is not gameplay authority. |
| `config/menu/`, `config/help/`, `config/keybindings/`, `config/tutorial/`, `config/ui/`, `config/audio/`, `config/playbot/` | Useful implementation / historical scaffolding | These are product and tooling inputs. They should inform Godot UX only when product requirements still need them; they do not define gameplay rules. |
| `docs/architecture/` | Mixed | Authority, parity, and transfer docs define migration governance; they do not replace Python gameplay semantics. |
| `docs/plans/` | Mixed | Active plans define scoped work and evidence boundaries; older plan history is not automatically porting authority. |

## Likely Semantic Oracle Surfaces

- `src/tet4d/engine/core/model/`, `src/tet4d/engine/core/rules/`, and
  `src/tet4d/engine/core/step/`: these define board state, coordinate/state
  queries, gravity, locking, placement, scoring, lifecycle, and command
  reduction. Changing them can change the game.
- `src/tet4d/engine/gameplay/game2d.py`, `game_nd.py`, piece modules,
  `lock_flow.py`, `play_move_intents.py`, and topology modules: these own the
  current legal movement, dimensional movement, rotation, drop/collision/lock,
  clearing, scoring, and piece lifecycle behavior.
- `src/tet4d/engine/topology_explorer/` transport and glue modules: these
  define current topology movement graphs, gluing, validation, presets, and
  transport resolution used by topology migration evidence.
- `src/tet4d/shared/nd_coords.py`: dimensional coordinate meaning is a semantic
  dependency for gameplay and traces.
- `src/tet4d/replay/format.py` and trace schema helpers under
  `tools/migration/`: trace fields that reflect real gameplay state are part of
  replay and parity evidence.
- `migration/golden_traces/`: these are the checked-in Python-authoritative
  topology, gameplay, and endgame traces.
- `tests/fixtures/parity/`: these fixtures encode maintained parity-slice
  expectations for trace metadata identity/digest, topology identifier
  normalization, and trace schema/version normalization.
- Gameplay/topology/endgame unit tests under `tests/unit/`: tests covering
  board rules, pieces, topology, movement, locking, clearing, trace export,
  and parity harnesses are semantic evidence.
- `config/gameplay/` and `config/topology/`: current gameplay and topology
  defaults can define deterministic behavior and fixture meaning.

## Likely Replaceable / Do-Not-Port Surfaces

- `src/tet4d/ui/pygame/menu/` and `src/tet4d/ui/pygame/launch/`: menu runners,
  setup menus, launch routing, and keybinding-menu presentation are pygame
  shell history. Godot should implement product-appropriate UI rather than
  reproduce this structure.
- `src/tet4d/ui/pygame/render/`, `front3d_render.py`, `front4d_render.py`, and
  projection/camera helpers: pygame display assumptions, panel drawing,
  camera/view presentation, text caching, icons, and projection guides are not
  game-rule authority.
- `src/tet4d/ui/pygame/runtime_ui/`: pause/help/tutorial overlays and draggable
  panels are shell scaffolding unless a product requirement explicitly carries
  them forward.
- Helper-panel wording and layout in topology-lab controls files: the semantic
  boundary is Editor/Sandbox/Play behavior and launch eligibility, not the old
  controls-panel decomposition.
- `tools/migration/` package layout: the maintained harnesses and evidence
  matter, but their location under `tools/migration/` is an active route
  decision, not gameplay semantics.
- Exported bundle copies under migration outputs: copied config and trace
  bundles are disposable artifacts, not source authority.
- Menu/help/keybinding/tutorial/UI/audio config surfaces: these can inform
  product UX where still useful, but they should not be treated as gameplay
  semantics.
- Historical names that survived by accident: names may help trace old
  behavior, but future Godot/C++ ports should classify the behavior before
  preserving a name.

No file is approved for deletion or quarantine by this audit. "Dead weight /
do-not-port" is a porting classification, not a cleanup authorization.

## Porting Guidance

Before porting a Python surface to Godot/C++, classify it.

- If semantic oracle: preserve behaviour until parity proves replacement.
- If useful implementation: reuse only if it reduces risk.
- If historical scaffolding: avoid porting unless there is an explicit product
  reason.
- If dead weight: do not port; delete/quarantine in a separate approved cleanup
  stage.

When a surface is mixed, split the decision: preserve the semantic behavior and
replace the incidental Python structure.

## Impact on Next Stages

This audit supports the next planned stages:

```text
24. Parity tooling/package review and tools/parity decision
25. Move parity harnesses from tools/migration/ to tools/parity/
26. Select first structural-but-safe parity slice
27. Implement first structural-but-safe parity slice
28. Authority-transfer readiness review
```

The recommended next structural-but-safe parity candidate remains:

```text
trace envelope validation
```

Allowed future scope for that candidate:

- top-level trace object shape
- required metadata keys
- schema/version field presence
- identity/digest field presence
- fixture envelope structure
- exact validation result comparison

Forbidden future scope:

- trace events
- board snapshots
- piece positions
- topology traversal
- movement
- gameplay semantics
- rendering/view/camera
- authority transfer

## Explicit Non-Transfer Statement

This audit does not transfer authority from Python to Godot or C++.
This audit does not approve deletion of semantic Python code.
This audit does not authorize gameplay, topology, trace-event, movement,
rendering, or Godot implementation changes.
