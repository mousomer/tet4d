# Unsafe Topology Correctness Audit

Status date: 2026-03-12
Status source of truth:
- [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
- [`docs/plans/topology_explorer_functional_audit.md`](docs/plans/topology_explorer_functional_audit.md)
Historical migration audit:
- [`docs/plans/topology_playground_reality_audit.md`](topology_playground_reality_audit.md)
Completed UI-cleanup context only:
- [`docs/plans/topology_explorer_menu_audit.md`](docs/plans/topology_explorer_menu_audit.md)
- [`docs/plans/topology_explorer_menu_cleanup_pass1.md`](docs/plans/topology_explorer_menu_cleanup_pass1.md)

## Scope

This stage is diagnostic only.

It does not reopen completed migration stages, and it does not broaden into:

- general performance optimization
- broad UI redesign
- unrelated topology-engine refactors

## Goal

Explain why unsafe / quotient topologies currently feel inconsistent across:

- preview / probe
- explorer shell behavior
- sandbox
- direct play launch

## Plan And Acceptance Criteria

Acceptance criteria for this audit:

1. Trace the actual state and transport path used by preview, explorer, sandbox,
   and play launch.
2. Reproduce the known unsafe-topology failures in direct engine/runtime checks.
3. Separate true state-handoff bugs from piece-transport semantic mismatch.
4. Record stage-safe next actions without re-implementing prior migration work.

## Sources Checked

- [`CURRENT_STATE.md`](CURRENT_STATE.md)
- [`docs/BACKLOG.md`](docs/BACKLOG.md)
- [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md)
- [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py)
- [`src/tet4d/engine/runtime/topology_playground_sandbox.py`](src/tet4d/engine/runtime/topology_playground_sandbox.py)
- [`src/tet4d/engine/runtime/topology_playground_state.py`](src/tet4d/engine/runtime/topology_playground_state.py)
- [`src/tet4d/engine/runtime/topology_explorer_preview.py`](src/tet4d/engine/runtime/topology_explorer_preview.py)
- [`src/tet4d/engine/topology_explorer/glue_map.py`](src/tet4d/engine/topology_explorer/glue_map.py)
- [`src/tet4d/engine/topology_explorer/glue_validate.py`](src/tet4d/engine/topology_explorer/glue_validate.py)
- [`src/tet4d/engine/topology_explorer/presets.py`](src/tet4d/engine/topology_explorer/presets.py)
- [`src/tet4d/engine/gameplay/explorer_piece_transport.py`](src/tet4d/engine/gameplay/explorer_piece_transport.py)
- [`src/tet4d/engine/gameplay/explorer_runtime_2d.py`](src/tet4d/engine/gameplay/explorer_runtime_2d.py)
- [`src/tet4d/engine/gameplay/explorer_runtime_nd.py`](src/tet4d/engine/gameplay/explorer_runtime_nd.py)
- [`src/tet4d/ui/pygame/topology_lab/scene_state.py`](src/tet4d/ui/pygame/topology_lab/scene_state.py)
- [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py)
- [`src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`](src/tet4d/ui/pygame/topology_lab/piece_sandbox.py)
- [`src/tet4d/ui/pygame/topology_lab/play_launch.py`](src/tet4d/ui/pygame/topology_lab/play_launch.py)
- [`tests/unit/engine/test_explorer_piece_transport.py`](tests/unit/engine/test_explorer_piece_transport.py)
- [`tests/unit/engine/test_topology_playground_launch.py`](tests/unit/engine/test_topology_playground_launch.py)
- [`tests/unit/engine/test_topology_playground_sandbox.py`](tests/unit/engine/test_topology_playground_sandbox.py)
- [`tests/unit/engine/test_topology_explorer_preview.py`](tests/unit/engine/test_topology_explorer_preview.py)

## Reproduction Basis

The reproductions below used direct engine/runtime checks rather than UI-click
automation.

Checked preset families and representative cases:

- `Mobius Strip` 2D
- `Projective` 2D / 3D / 4D
- `Sphere` 2D / 3D / 4D
- cross-axis non-unsafe comparison cases (`swap_xz_3d`, `swap_xw_4d`)

Board sizes used:

- equality-valid baseline: `(4, ..., 4)`
- non-bijective failure baseline: `(5, 4)`, `(4, 5, 6)`, `(4, 5, 6, 7)`

## Surface Contract Reality

| surface | current owner | what it really models today | important consequence |
| --- | --- | --- | --- |
| Preview / Probe | [`src/tet4d/engine/runtime/topology_explorer_preview.py`](src/tet4d/engine/runtime/topology_explorer_preview.py) + [`src/tet4d/engine/topology_explorer/glue_map.py`](src/tet4d/engine/topology_explorer/glue_map.py) | point-cell connectivity only | A valid boundary crossing for one cell does not imply a rigid piece can follow it. |
| Sandbox | [`src/tet4d/engine/runtime/topology_playground_sandbox.py`](src/tet4d/engine/runtime/topology_playground_sandbox.py) | per-cell explorer transport plus a translation-only rigidity check | Sandbox rejects rigid seam transforms that gameplay already supports. |
| Play | [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py) + [`src/tet4d/engine/gameplay/explorer_runtime_2d.py`](src/tet4d/engine/gameplay/explorer_runtime_2d.py) + [`src/tet4d/engine/gameplay/explorer_runtime_nd.py`](src/tet4d/engine/gameplay/explorer_runtime_nd.py) | rigid-piece transport | Gameplay allows `plain_translation` and `rigid_transform`, but blocks `cellwise_deformation`. |
| Launch handoff | [`src/tet4d/ui/pygame/topology_lab/play_launch.py`](src/tet4d/ui/pygame/topology_lab/play_launch.py) + [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py) | canonical-state pass-through | On the migrated path, play launch is not re-deriving a different explorer profile from legacy rows. |

## Findings

### 1. The main cross-surface inconsistency is semantic, not a stale launch conversion.

I did not reproduce a separate migrated-path bug where `Play This Topology`
launches with a different explorer gluing profile than the playground holds.

What the code does now:

- [`src/tet4d/ui/pygame/topology_lab/controls_panel.py`](src/tet4d/ui/pygame/topology_lab/controls_panel.py)
  launches play from canonical `TopologyPlaygroundState`.
- [`src/tet4d/engine/runtime/topology_playground_launch.py`](src/tet4d/engine/runtime/topology_playground_launch.py)
  passes the current `explorer_topology_profile` straight into `GameConfig` /
  `GameConfigND`.
- Existing launch tests already pin that direct handoff in
  [`tests/unit/engine/test_topology_playground_launch.py`](tests/unit/engine/test_topology_playground_launch.py).

The larger mismatch is that preview/probe show point connectivity, while play
applies rigid-piece transport rules.

### 2. Preview / probe can legitimately say "yes" when play must say "no".

Representative reproduction on `Projective` 2D / 3D / 4D:

- one cell crossing `x-` is valid in preview/probe
- a 2-cell segment aligned along the movement axis becomes
  `cellwise_deformation`
- gameplay blocks that move
- sandbox also blocks it

This is not a stale-state bug. It is the current product contract gap between:

- point-particle topology preview
- rigid-piece gameplay transport

That gap is especially visible on unsafe quotient families, so the playground
feels like it promised connectivity that play does not honor.

### 3. Sandbox is stricter than gameplay and is currently the clearest correctness bug.

Representative reproductions:

- `Mobius Strip` 2D tangent-aligned segment across `x`
- `Projective` 2D / 3D / 4D tangent-aligned segment across `x`
- `Sphere` 2D / 3D / 4D tangent-aligned segment across the first cross-axis seam
- `swap_xw_4d`

For those cases:

- [`src/tet4d/engine/gameplay/explorer_piece_transport.py`](src/tet4d/engine/gameplay/explorer_piece_transport.py)
  classifies the move as `rigid_transform`
- gameplay accepts the move
- sandbox rejects the same move with
  `sandbox piece cannot remain rigid across seam crossing`

Why:

- gameplay uses `classify_explorer_piece_move(...)`
- sandbox only accepts the move when every cell shares the same translation delta
- that means sandbox allows `plain_translation` only and rejects
  `rigid_transform`

This directly violates the intended distinction in
[`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md):

- `rigid_transform` is allowed
- `cellwise_deformation` is what must be blocked

No RDS change is needed here. The code is drifting from the existing RDS.

### 4. Unsafe preset usability failure splits into two different classes.

There are two separate failure categories today:

1. Preview-valid but piece-unsafe.
   - Example: `Projective`
   - Point traversal compiles and probes correctly.
   - Some piece orientations cross as `rigid_transform`.
   - Other piece orientations cross as `cellwise_deformation` and are blocked in play.

2. Preview-invalid for current board dimensions.
   - Example: `Sphere` on non-bijective sizes such as `(5, 4)`,
     `(4, 5, 6)`, `(4, 5, 6, 7)`
   - Preview compile fails with
     `gluing transform is not bijective for the board dimensions`
   - Probe falls back to `Probe unavailable: ...`
   - Play is blocked behind `scene_preview_error`

So "unsafe topologies are unusable" is real, but it is not one bug. It is a
mix of:

- preview-valid / piece-unsafe topology
- preview-invalid / dimension-incompatible topology

### 5. Projective presets are not the same problem as sphere presets.

Direct checks on equal board sizes did not reproduce a separate point-cell
connectivity failure for `Projective` 2D / 3D / 4D:

- preview compiled
- probe crossed the seam as expected
- sandbox dot-piece crossed the seam as expected
- launched gameplay uses the same explorer profile

The "projective is clearly wrong" symptom is more plausibly explained by
multi-cell rigid-piece behavior:

- some piece orientations are rigid and should be allowed
- sandbox blocks even those rigid cases
- other piece orientations truly deform and must be blocked in play

In other words, the current product does not clearly tell the player whether
they are looking at:

- point connectivity
- rigid-piece-safe connectivity
- or an invalid preset/dimension pairing

## Concrete Reproductions

| case | preview / probe | sandbox | play | diagnosis |
| --- | --- | --- | --- | --- |
| `Mobius Strip` / `Projective` tangent-aligned 2-cell seam crossing | valid | blocked | allowed | sandbox parity bug: `rigid_transform` rejected as if it were non-rigid |
| `Sphere` tangent-aligned 2-cell seam crossing on valid equal dims | valid | blocked | allowed | same sandbox parity bug |
| `Projective` movement-axis-aligned 2-cell seam crossing | valid for single cells | blocked | blocked | true point-vs-rigid-piece contract gap (`cellwise_deformation`) |
| `Sphere` on non-bijective dims | preview compile error | probe unavailable | play blocked before launch | dimension compatibility failure, not launch drift |
| `swap_xz_3d` plain-translation cross-axis case | valid | allowed | allowed | this is the parity baseline that still works |

## RDS Comparison

Checked against:

- shared piece-local transform rules in
  [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md)
- Explorer Playground product rules in
  [`docs/rds/RDS_TETRIS_GENERAL.md`](docs/rds/RDS_TETRIS_GENERAL.md)

Result:

- no RDS update is required for this audit
- current sandbox behavior is below the existing RDS bar because it blocks
  `rigid_transform` instead of only blocking `cellwise_deformation`

## Stage-Safe Next Actions

1. Make sandbox and gameplay share the same transport classifier so both allow
   `rigid_transform` and both block only `cellwise_deformation`.
2. Add explicit cross-surface regression coverage for:
   - point-valid + rigid-transform-allowed
   - point-valid + cellwise-deformation-blocked
   - preview-invalid unsafe preset / dimension pairs
3. Expose a separate explorer/playability signal for rigid-piece safety so the
   preview does not read like a playability promise.
4. Preflight unsafe preset families against current board dimensions before the
   shell lands in `Probe unavailable` / play-blocked state.

## Short Conclusion

The blocking unsafe-topology problem is real, but it is more specific than
"Play This Topology uses different state" or "the migration did not land."

The migrated play-launch path is still using canonical playground state. The
actual drift is:

1. preview / probe are point-connectivity surfaces
2. gameplay is a rigid-piece transport surface
3. sandbox is currently stricter than gameplay and rejects rigid seam
   transforms outright

That sandbox/play mismatch is the clearest correctness bug. The other major gap
is that unsafe previews do not distinguish point connectivity from rigid-piece
playability, so quotient examples can look defined in the playground and still
be blocked or partially blocked once a real piece is involved.
