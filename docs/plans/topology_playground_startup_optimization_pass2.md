# Topology Playground Startup Optimization Pass 2

Status date: 2026-03-11
Scope: R4 preview compile caching / refresh dedup only.
Current topology-playground authority:
- [`docs/plans/topology_playground_current_authority.md`](docs/plans/topology_playground_current_authority.md)
Historical/source audits:
- [`docs/plans/topology_playground_reality_audit.md`](topology_playground_reality_audit.md)
- [`docs/plans/topology_playground_startup_audit.md`](docs/plans/topology_playground_startup_audit.md)
- [`docs/plans/topology_playground_startup_optimization_pass1.md`](docs/plans/topology_playground_startup_optimization_pass1.md)

## Short Plan

1. Define the minimal preview signature for the migrated Explorer Playground refresh path.
2. Cache compiled preview artifacts for repeated same-signature refreshes.
3. Invalidate only on real topology/profile/dimension changes and capture measured refresh evidence.

## Acceptance Criteria

- `_refresh_explorer_scene_state(...)` no longer recompiles unchanged preview artifacts for repeated same-signature refreshes on the migrated path.
- Cache invalidation follows effective topology/profile/dimension inputs rather than generic UI churn.
- Repeated `4D` refreshes are measurably cheaper.
- Correctness stays intact when the preview signature changes.
- The cache scope, invalidation rules, and remaining hotspots are documented.

## What Changed

1. Added `ExplorerPreviewCompileSignature` and `ExplorerPreviewCompileArtifacts` to the scene-state owner so the migrated shell can keep one explicit cached preview entry separate from live mutable UI state.
2. `_refresh_explorer_scene_state(...)` now computes the effective preview signature, reuses cached preview payloads and cached validation errors when that signature matches, and only drops `experiment_batch` when the preview signature actually changes.
3. Added focused regressions in `tests/unit/engine/test_topology_lab_menu.py` covering repeated same-signature refresh reuse, same-signature speed changes, and board-size invalidation.
4. Extended `scripts/profile_topology_playground_startup.py` with a `repeat_refresh` trace section so the repeated-refresh cost can be measured directly.

## Cached Signature And Artifacts

- Signature cached: the effective `ExplorerTopologyProfile` plus normalized board dims / axis sizes for the migrated explorer state. Tool, pane, piece set, and speed are intentionally excluded because they do not affect compiled preview output.
- Artifacts cached: the `compile_explorer_topology_preview(...)` payload used by the scene (`movement_graph` summary, warnings, sample traversals, and `basis_arrows`) plus the same-signature `ValueError` text when compilation fails.
- Invalidation rules: the single-entry cache is replaced when the profile or dims change, and cleared when the migrated explorer path is left or the explorer profile becomes unavailable. Same-signature refreshes reuse the cached entry.

## Measured Refresh Dedup

Measured on 2026-03-11 with `scripts/profile_topology_playground_startup.py --dimensions 4`.

- Startup still pays for one required migrated-path preview compile: `1718.9 ms` in this run, with one `build_movement_graph(...)` call for the `full_wrap_4d` signature.
- Repeated same-signature refreshes on that warmed `4D` state took `0.061 ms` and `0.030 ms`.
- The profiler recorded `0` movement-graph builds and `0` validation calls during the repeated-refresh phase.

## Remaining Hotspots

1. The first preview compile after a real `(profile, dims)` change is still expensive in `4D`; this pass only removes repeated same-signature rebuilds.
2. Explicit preview export still recompiles on demand outside this refresh cache, which is acceptable for this stage because export is not on the migrated refresh path.
3. Manual experiment-pack generation remains uncached and heavy in `4D` (`5223.4 ms` in this run), though it stays off the first-frame path.
4. Compatibility binding through `_bind_controls_panel_compat(...)` still exists on the migrated path, but it is now negligible compared with the one required preview compile.

## RDS Check

Compared against `docs/rds/RDS_TETRIS_GENERAL.md` items 22-26. No RDS update was required because this pass changes refresh cost and cache ownership details, not the Explorer Playground contract.
