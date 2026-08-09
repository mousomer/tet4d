# Task Contract — Stage 54E-2b Renderer Composition

## Objective

Migrate applicable Live-4D renderer consumers from `G_D(p) + anchor_i` to the
accepted `B -> G_D -> L -> anchor_i` composition without changing gameplay or
input semantics.

## Current Authority

- `docs/architecture/4d_presentation_interaction_architecture.md`: accepted
  Stage 54E-1 transform, ownership, and staged-delivery contract.
- Stage 54E-2a implementation at `cb7d5e600f58d01f9c25fb705471ab543ab045d9`:
  reviewed-green state/decomposition evidence.
- `docs/architecture/game_safe_4d_slice_basis.md`: exact signed `B` contract.
- `docs/architecture/ghost_piece.md`: authoritative Ghost destination and
  presentation-only identity.
- `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`: subsystem ownership boundaries.
- `docs/plans/professional_godot_game_programme.md`, `CURRENT_STATE.md`, and
  `docs/BACKLOG.md`: Stage 54E sequencing and explicit deferrals.
- `config/project/policy_pack.json`, `docs/WORKFLOW_CODEX.md`, and
  `godot/AGENTS.md`: routing and verification governance.

Python semantic authority does not apply to the new presentation transform.
Native gameplay remains authoritative for canonical cells and Ghost landing.

## Allowed Systems and Paths

- Godot rendering and presentation under
  `godot/Tet4D.Godot/scripts/{rendering,presentation}/`.
- Minimum app-to-renderer presentation-state wiring in
  `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd`.
- Focused Godot renderer/presentation tests.
- Stage 54E architecture, programme, backlog, handoff, and authority evidence.

## Required Changes

- Apply one shared `SliceLocalOrientation` to locked, active, and Ghost cells.
- Apply the same orientation to grid, floor/lattice, slice frame/wireframe,
  active frame, and applicable geometry-attached markers.
- Keep slice identity labels readable and attached without rotating anchors.
- Derive per-slice and collection world AABBs from oriented local corners and
  use those bounds as camera-fit inputs.
- Preserve exact `B`, affine centred `G_D`, anchor-only layout, continuous yaw,
  representative pitch, signed-basis, asymmetric-dimension, and W=1 behavior.

## Forbidden Changes

- Input rerouting, including mouse/keyboard yaw or pitch ownership.
- `CameraRig` orientation ownership, control-frame resolver semantics, roll
  binding removal, pitch-domain policy, or fitted-camera Forward proof.
- Camera/GUI preset redesign or lifecycle/reset reconciliation.
- Canonical gameplay, Ghost landing, native C++, Python, snapshot/hash/replay,
  RNG, score, queue, topology, or persistence semantics.
- Stage 54E-2c, 54E-2d, 54E-3, 54E-4, or 54E-5 implementation.

## Acceptance Criteria

1. Live-4D render composition is exactly `world = L(G_D(p)) + anchor_i`.
2. One continuous yaw/pitch `L` is applied once and identically to every slice.
3. Locked, active, Ghost, grid, frame, and geometry-attached markers align.
4. Yaw/pitch do not change anchors, row/column assignment, order, membership,
   exact `B`, canonical source cells, or deterministic identity.
5. Layout changes may move anchors but cannot change oriented local deltas.
6. Oriented corner-derived bounds contain every rendered local board corner
   for identity, non-quarter yaw, pitch, asymmetric dimensions, and multiple
   slices; camera fit consumes those bounds.
7. Slice labels remain associated with the correct signed semantic slice and
   are not rotated as local physical geometry.
8. Identity `L` preserves current 2D, 3D, and Live-4D presentation.
9. Focused, resolver-required, sanitation, full repository, and manual visual
   verification are green.
10. Status is `IMPLEMENTED / REVIEW PENDING`; Stage 54E-2c remains blocked.

## Automated Verification

- Policy-backed resolver requirements: `documentation`, `godot`,
  `deterministic`, and `human_visual`; full repository gate required.
- Focused renderer/presentation Godot tests.
- `GODOT_BIN=... ./scripts/verify_godot_4_7.sh`.
- Governance/documentation validators and generated-document checks.
- Git sanitation and `git diff --check`.
- `CODEX_MODE=1 ./scripts/verify.sh`.

## Manual Verification

Inspect a real rendered Live-4D scene at identity and at representative
nonzero continuous yaw/pitch. Confirm uniform per-slice orientation, fixed
anchors/order, cell/Ghost/grid/frame alignment, correct labels, no clipping,
and complete collection framing. Do not assess final control correspondence.

## Documentation Updates

Update only concrete implementation/status evidence in `CURRENT_STATE.md`,
`docs/BACKLOG.md`, `docs/architecture/4d_presentation_interaction_architecture.md`,
`docs/plans/professional_godot_game_programme.md`, `docs/ARCHITECTURE_CONTRACT.md`,
and `docs/architecture/authority_map.md` where the resulting diff establishes
new renderer ownership evidence.

## Explicit Deferrals

- Stage 54E-2c: interaction, resolver, `CameraRig`, roll, pitch policy, presets,
  and fitted-camera semantic Forward verification.
- Stage 54E-2d: lifecycle, reset/new-game/mode-switch, and final contract
  reconciliation.
- Stages 54E-3/4/5 and later integrated visual acceptance.
