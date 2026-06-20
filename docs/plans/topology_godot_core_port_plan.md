# Topology Godot Core Port Plan

Role: Stage 25 topology port planning authority
Status: planning-only; topology implementation deferred
Last updated: 2026-06-17

Stage 25 adds no topology gameplay, no topology transport implementation in
C++, no Godot topology editor UI, no live wrap/invert/sphere gameplay, no
endgame, no C#, no Python runtime calls from Godot, and no Godot-side gameplay
legality. It records the topology migration plan after the accepted plain
bounded Live ND baseline.

## 1. Decision Summary

Topology porting will be staged after the accepted plain bounded Live 2D,
Live 3D, Live 4D, and Replay Godot shell baseline. Python remains the topology
oracle until native trace parity passes against the checked-in topology and
topology-aware gameplay traces.

Use `docs/architecture/authority_map.md` and
`docs/governance/godot_cpp_policy.md` as the routing overlay for future
Godot/C++ topology migration work. They do not authorize topology
implementation ahead of this plan's staged parity gates.

C++ will own topology transport, topology-aware gameplay legality, drop/lock
policy, collision, launch-derived status, snapshots, and `state_hash` once a
native topology stage is authorized. Godot will own the topology product shell:
mode selection, editor widgets, input dispatch, render presentation, camera,
HUD, diagnostics, and replay/inspection surfaces.

The accepted plain bounded Live 2D/3D/4D modes must remain preserved. The first
implementation stage after this plan must be trace/parity-driven, not UI-first.
Topology implementation remains deferred until Stage 26 or later, and endgame
remains deferred.

## 2. Current Accepted Baseline

Stage 22f accepted Live 3D visual readability after Stage 22g corrections.
Stage 23 accepted the narrow Live Plain 4D Godot prototype after Stage
23b/23c/23d corrections. Stage 24 accepted Live ND shell lifecycle and input
hardening.

The stable Godot baseline is Live 2D, Live 3D, Live 4D, and Replay as plain
bounded product-shell modes. C++ owns plain bounded gameplay semantics through
`Plain2DSession` and `PlainNDSession`; Godot owns input routing, presentation,
HUD, camera, layout, replay browsing, and rendering through the existing
mapper/renderer path. Python remains the oracle/reference and is not a Godot
runtime dependency.

## 3. Topology Problem Statement

Plain bounded ND gameplay is not enough for tet4d's core identity. The next
semantic frontier is topology: wrap, invert, sphere-like transport, seam and
gluing behavior, Sandbox-vs-Play semantics, launch validation, and
topology-aware gameplay.

The problem splits into separate surfaces:

- topology transport: coordinate movement, seam crossings, frame transforms,
  and neighbor lookup;
- topology construction/editing: Explorer profile, boundary gluing, preset
  selection, validation, and launch eligibility;
- topology-aware gameplay: movement, rotation placement, soft drop, gravity,
  hard drop, lock, clear/scoring, spawn, game-over, and state hashing under a
  topology profile;
- topology visualization: seam, neighbor, probe, launch, and diagnostic
  overlays;
- topology presets: bounded, wrap, invert, sphere-like, and later custom
  Explorer profiles;
- topology launch: preserving the exact validated Editor/Sandbox profile into
  Play without fallback or reconstruction.

## 4. Python Authority And Oracle Traces

Current Python topology authority lives primarily in:

- `src/tet4d/engine/topology_explorer/glue_model.py`
- `src/tet4d/engine/topology_explorer/glue_map.py`
- `src/tet4d/engine/topology_explorer/transport_resolver.py`
- `src/tet4d/engine/topology_explorer/presets.py`
- `src/tet4d/engine/topology_explorer/glue_validate.py`
- `src/tet4d/engine/gameplay/topology.py`
- `src/tet4d/engine/gameplay/explorer_runtime_nd.py`
- `src/tet4d/engine/gameplay/play_move_intents.py`
- `src/tet4d/engine/runtime/topology_playability_signal.py`
- `src/tet4d/engine/runtime/topology_playground_launch.py`
- `src/tet4d/engine/runtime/topology_playground_sandbox.py`
- `src/tet4d/engine/runtime/topology_playground_state.py`

The trace generators are:

- `tools/migration/export_topology_trace.py`
- `tools/migration/export_gameplay_trace.py`
- `tools/migration/trace_cases.py`
- `tools/migration/trace_schema.py`

Checked-in topology traces under `migration/golden_traces/topology/` cover
plain, wrap, invert, and sphere-like transport in 2D/3D/4D; the
Sandbox-vs-Play Y-axis seam distinction; false-lock regression coverage; and
repeatable playability diagnostics. Checked-in gameplay traces under
`migration/golden_traces/gameplay/` cover wrap 2D/3D/4D, invert, sphere-like
transport, Y-axis drop policy, and `Play This Topology` launch parity in
addition to the plain bounded cases.

The exported bundle indexes these traces under
`migration/exported_bundle/manifest.json` and
`migration/exported_bundle/traces/`. Topology-relevant metadata includes
`topology_id`, `topology_preset`, `trace_type`, `dimension`, `frame_count`,
`final_state_hash`, settings `explorer_profile_digest`,
`explorer_rigid_play_enabled`, `topology_mode`, `wrap_gravity_axis`,
`launch_parity`, and frame-level `topology_event` payloads.

The existing traces are sufficient to plan the first native transport model
and likely sufficient for a narrow first transport parity scaffold, but Stage
26 must audit the comparison contract before implementation starts. Native
topology must not invent semantics that are not validated against Python
traces.

Before any second parity slice is added to support this plan, it must satisfy
`docs/architecture/parity_pilot_audit_and_promotion_gates.md`. That gate is
process-only and does not transfer authority.

## 5. Proposed Staging

Stage 26 - Topology Trace Contract Audit / Expansion:

- confirm the exact required fields for native topology transport parity;
- verify whether existing topology/gameplay traces are sufficient for the
  first C++ transport slice;
- add or refine Python oracle traces only if gaps are found;
- do not implement native topology unless the trace contract is proven
  sufficient.

Stage 27 - Native Topology Transport Model Parity:

- add a C++ topology graph/transport model;
- compare native transport output against Python topology transport traces;
- keep Godot topology UI and live topology gameplay out of scope.

Stage 28 - Native Topology-Aware Gameplay Parity:

- apply topology transport to movement, drop, lock, collision, spawn, and
  state hashing;
- preserve the Sandbox-vs-Play semantic distinction;
- match topology-aware gameplay traces and hashes;
- expose only replay/parity surfaces, not product UI expansion.

Stage 29 - Godot Topology Replay / Diagnostic Viewer:

- visualize topology traces, seam crossings, neighbor lookup, and diagnostics;
- keep overlays presentational;
- do not add editable topology UI.

Stage 30 - Godot Topology Lab Product Shell:

- plan or implement the Godot topology editor/sandbox/play shell only after
  native trace parity is trusted.

This sequence is intentionally trace-first and must not jump to UI-first live
topology.

## 6. Minimal First Topology Scope

The first semantic slice should be topology transport and neighbor lookup only:

- deterministic fixture topology;
- movement across seams;
- directed seam metadata;
- frame and piece-frame transform metadata;
- no full editor UI;
- no endgame;
- no arbitrary custom topology authoring in Godot;
- no scoring changes beyond existing Python trace fixtures.

Candidate first topologies are simple wrap first, then simple invert, then one
sphere-like preset only if Stage 26 confirms stable trace coverage and
comparison requirements. Do not start with all topology presets at once.

## 7. Native C++ Architecture Plan

Add topology beside the existing plain bounded model until parity proves the
shape is stable. Do not destructively refactor `PlainNDSession`.

Potential planning-level types:

```text
TopologyND
  dimension
  board_shape
  coordinate domain
  seam rules
  directed boundary lookup
  neighbor transport table
  preset metadata
  validation status

TopologyTransport
  resolve_neighbor(coord, axis, delta)
  returns:
    valid / invalid
    target_coord
    transform / orientation metadata
    seam_crossed
    topology_event / debug metadata

TopologyGameStateND
  composes the current plain-ND state shape
  uses topology-aware transport for moves and drops
  preserves snapshot/status/hash conventions
```

The minimal native topology model should mirror Python's data model:
dimension, board shape, boundary refs, gluing descriptors, boundary transforms,
directed seams, single-cell step results, and piece-step classification as
`blocked`, `plain_translation`, `rigid_transform`, or
`cellwise_deformation`.

## 8. C++ Authority Boundary

C++ owns:

- topology transport;
- neighbor legality;
- movement across seams;
- topology-aware drop and lock;
- topology-aware collision;
- topology-aware game-over;
- topology-aware `state_hash`;
- status and snapshot truth.

Godot owns:

- mode selection;
- UI;
- input dispatch;
- visual presentation;
- camera;
- HUD;
- editor widgets when later authorized.

Godot must not compute topology legality, seam transport, topology collision,
launch eligibility, or topology gameplay state. Godot must not mutate topology
gameplay state.

## 9. Godot Product-Shell Plan

Future Godot topology surfaces may include:

- Topology Lab entry;
- topology preset browser;
- seam and neighbor diagnostics;
- Sandbox topology probe;
- `Play This Topology` launch;
- `Explore This Topology` entry;
- topology-aware HUD labels;
- topology replay diagnostics.

Stage 25 implements none of those surfaces. Existing Live 2D, Live 3D,
Live 4D, and Replay modes remain separate, accepted, and plain bounded.

## 10. Renderer / Visual Plan

Topology visualization should reuse the existing rendering architecture:

- `TraceCoordinateMapper`
- `TraceSceneRenderer`
- `CellRenderer`
- `GridRenderer`

Topology overlays should be added later as presentation overlays. Seam
indicators, neighbor arrows, probe paths, and launch diagnostics are visual
diagnostics, not gameplay logic. Topology visualization must not require a new
coordinate system unless a later stage explicitly justifies it against trace
and rendering evidence. Topology visuals must preserve the Stage 22/23
diagrammatic gameboard grammar.

## 11. Trace And Hash Requirements

Native topology trace export must match Python required fields. Where Python
provides frame/final `state_hash`, native output must match. Topology metadata
must be compared explicitly, including:

- `topology_id`;
- profile/gluing metadata;
- transport kind;
- source/target coordinates;
- traversed seam ids and boundary labels;
- frame transforms and piece-frame transforms;
- active cells;
- locked cells;
- game state and drop/lock status;
- launch parity metadata.

Diff output must identify transport, active-cell, locked-cell, game-state, and
topology metadata mismatches. If existing comparison tools are insufficient,
Stage 26 must strengthen comparison tooling before native implementation.

## 12. Risk Register

- Risk: topology implementation corrupts accepted plain bounded modes.
  Mitigation: use a sidecar topology model, keep `PlainNDSession` untouched,
  and retain plain 2D/3D/4D regression gates.
- Risk: UI-first topology creates fake semantics in Godot. Mitigation:
  require trace-first C++ parity before product UI.
- Risk: topology transport is underspecified. Mitigation: audit and expand
  Python traces before C++ port work.
- Risk: custom topology editor scope becomes too broad. Mitigation: start
  with fixed, preset, trace-covered topologies.
- Risk: visualization becomes misleading. Mitigation: use the existing
  diagrammatic visual grammar and explicit diagnostics.
- Risk: endgame work leaks in. Mitigation: keep endgame explicitly deferred.

## 13. Stage 26 Recommendation

Next task:

```text
Stage 26 - Topology Trace Contract Audit / Expansion
```

Purpose:

- inspect existing topology golden traces;
- decide whether native topology transport can start immediately;
- add or refine Python oracle traces if gaps exist;
- strengthen comparison tooling if topology metadata diffs are insufficient;
- avoid native topology implementation unless the trace contract is already
  sufficient.

Stage 26 may rename itself to `Native Topology Transport Parity Scaffold` only
if its opening audit proves the trace contract is strong enough. The default
recommendation remains audit/expansion first.
