# Topology Playability Signaling Pass 1

Status date: 2026-03-12
Status sources of truth:
- [`docs/plans/topology_playground_current_authority.md`](topology_playground_current_authority.md)
- [`docs/plans/unsafe_topology_correctness_fix_pass1.md`](unsafe_topology_correctness_fix_pass1.md)
- supporting context only: [`docs/plans/topology_explorer_functional_audit.md`](topology_explorer_functional_audit.md)
- archived migration audit: [`docs/history/topology_playground/topology_playground_reality_audit.md`](../history/topology_playground/topology_playground_reality_audit.md)

## Scope

This pass stays within the playability-signaling stage.
It does not change core topology semantics, reopen completed migration stages, or broaden into general performance work or UI redesign.

## A. Status model

Canonical status now lives on the runtime-owned `TopologyPlaygroundState.playability_analysis` field.
The UI reads that one analysis object instead of mixing raw preview errors, preset labels, and ad hoc launch messaging.

Statuses surfaced in this pass:

- `validity`
  - `valid`
  - `invalid`
- `explorer_usability`
  - `cellwise_explorable`
  - `not_explorable`
- `rigid_playability`
  - `rigid_playable`
  - `not_rigid_playable`
- `summary`
  - combined user-facing state such as `Valid. Cellwise explorable. Not rigid-playable.`
- reason fields
  - `validity_reason`
  - `explorer_reason`
  - `rigid_reason`

## B. Runtime source

The signal is derived from existing runtime behavior only:

- validity uses the current explorer validation split in `src/tet4d/engine/topology_explorer/glue_validate.py`
  - `validate_topology_structure(...)`
  - `validate_topology_bijection(...)`
- explorer usability follows the current validated preview/probe surface
  - valid topology => cellwise explorer remains available
  - invalid topology => probe/preview remain unavailable for the active dimensions
- rigid playability uses the existing rigid transport semantics already shared by gameplay and sandbox
  - `move_cell(...)`
  - `classify_explorer_piece_move(...)`
  - a validated topology is marked `not_rigid_playable` when the current runtime finds a minimal adjacent-cell rigid transport counterexample (`cellwise_deformation`)
- preview movement counts continue to come from the existing compiled preview payload when available

This pass does not introduce a second playability store.
The shell updates `playability_analysis` during canonical scene refresh from the live canonical profile plus current board dimensions.

## C. User-facing messages

Examples now surfaced in the playground shell:

- `Valid. Cellwise explorable. Rigid-playable.`
- `Valid. Cellwise explorable. Not rigid-playable.`
- `Invalid for current board dimensions.`
- `Why: Rigid transport fails when a two-cell piece partly crosses projective_0 (x- -> x+) during x-.`
- `Play: Explorer stays available, but play uses rigid transport.`
- `Preview unavailable until the topology validates.`

The Analysis View now shows explicit `Topology Status`, `Validity`, `Explorer`, `Rigid Play`, and `Why` rows.
The workspace preview panel also shows the same playability breakdown directly above the existing preview diagnostics and therefore above `Play This Topology`.

## D. Known remaining gaps

- Positive `rigid_playable` status is currently derived from the live adjacent-cell rigid-transport scan rather than exhaustive piece-orientation enumeration across every topology family.
- Legacy compatibility-only non-explorer surfaces do not yet mirror the new playability signal.
- This pass does not change play-launch policy; valid explorer-only / non-rigid topologies are now signaled clearly, but launch still follows the existing runtime rules.
