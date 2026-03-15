# Topology Playground Startup Optimization Pass 1

Status date: 2026-03-11
Scope: R3 startup/load optimization pass 1 only.
Source audits:
- [`docs/plans/topology_playground_reality_audit.md`](docs/plans/topology_playground_reality_audit.md)
- [`docs/plans/topology_playground_startup_audit.md`](docs/plans/topology_playground_startup_audit.md)

## Short Plan

1. Bypass startup-only compatibility work when Explorer launch already provides an explicit topology profile.
2. Stop launch validation and default probe placement from compiling extra movement graphs.
3. Remove redundant per-cell validation inside the one remaining startup graph build.

## Acceptance Criteria

- Tie every change to the ranked hotspots in the startup audit.
- Reduce at least one meaningful pre-first-frame hotspot by bypassing or removing unnecessary startup work.
- Keep first-frame-critical work separate from deferred/manual work.
- Avoid unrelated migration or feature churn.
- Capture a before/after startup trace for the optimized path.
- List the remaining hotspots for a later pass.

## What Changed

1. Hotspot: launch validation was compiling a full explorer preview before startup even reached the shell.
   Change: `src/tet4d/ui/pygame/topology_lab/app.py` now validates launch profiles with `validate_explorer_topology_profile(...)` instead of `compile_explorer_topology_preview(...)`.

2. Hotspot: `_initial_topology_lab_state(...)` loaded and refreshed the stored explorer profile before replacing it with the explicit launch profile.
   Change: `src/tet4d/ui/pygame/launch/topology_lab_menu.py` now takes a direct explicit-profile startup path that hydrates canonical state, scene camera/orbit, preview, and probe state without detouring through `load_runtime_explorer_topology_profile(...)`.

3. Hotspot: `recommended_explorer_probe_coord(...)` rebuilt the movement graph even though the initial probe only needs a validated center coordinate.
   Change: `src/tet4d/engine/runtime/topology_explorer_preview.py` now validates dims/profile and returns the centered probe coordinate directly.

4. Hotspot: `build_movement_graph(...)` revalidated the same profile inside every `neighbors_for_cell(...)` call.
   Change: `src/tet4d/engine/topology_explorer/movement_graph.py` now validates once per graph build and reuses that validated path for cell expansion.

No startup instrumentation changes were required. Existing measurements from `scripts/profile_topology_playground_startup.py` were enough to compare before/after on the same audited route.

## Measured Startup Delta

Measured on 2026-03-11 with `scripts/profile_topology_playground_startup.py` using the same representative launch profiles called out by the startup audit.

| Dimension | First frame before | First frame after | Delta | Startup movement-graph builds before -> after |
| --- | ---: | ---: | ---: | --- |
| 2D | `137.5 ms` | `64.6 ms` | `-72.9 ms` (`-53%`) | `4 -> 1` |
| 3D | `555.5 ms` | `215.9 ms` | `-339.6 ms` (`-61%`) | `4 -> 1` |
| 4D | `6890.3 ms` | `2326.1 ms` | `-4564.2 ms` (`-66%`) | `4 -> 1` |

Additional observed reductions from the same trace:

- Launch validation dropped from `28.8 / 195.3 / 2311.4 ms` to about `0.024 / 0.026 / 0.026 ms` for `2D / 3D / 4D`.
- Startup validation calls dropped from `604 / 1948 / 14404` to `1 / 1 / 1`.
- Stored explorer-profile startup load disappeared from the explicit explorer launch path.

## Remaining Follow-Up Hotspots

1. The remaining first-frame bottleneck is the one required preview compile in `_refresh_explorer_scene_state(...)`, especially for `4D` (`~2309 ms` after this pass).
2. If repeated same-signature scene refreshes still show up later, add a dedicated cached preview/graph artifact path keyed by `(profile, dims)`.
3. Keep playability analysis lazy. Manual experiment-pack generation is still very heavy in `4D` (`~6865 ms` here), but it remains off the startup path.
4. `_bind_controls_panel_compat(...)` and retained shell mirrors still exist, but after this pass they are no longer dominant startup costs on the audited explorer route.

## RDS Check

Compared against `docs/rds/RDS_TETRIS_GENERAL.md` items 21-26. No RDS update was required because this pass changes startup cost, not the user-facing shell contract.
