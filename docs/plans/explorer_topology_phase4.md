# Explorer Topology Phase 4

Status: Active implementation batch

## Objective

Extend the direct explorer gluing editor across the remaining explorer dimensions so Explorer Mode no longer uses the legacy per-edge topology editor path in 2D, 3D, or 4D.

## Canonical owners

1. `src/tet4d/engine/topology_explorer/` owns 2D/3D/4D explorer gluing semantics, transforms, validation, and graph mapping.
2. `src/tet4d/engine/runtime/topology_explorer_store.py` owns persisted 2D/3D/4D explorer gluing profiles.
3. `src/tet4d/engine/runtime/topology_explorer_preview.py` owns 2D/3D/4D explorer preview compilation/export.
4. `src/tet4d/ui/pygame/launch/topology_lab_menu.py` owns the direct explorer lab orchestration for 2D, 3D, and 4D.
5. `src/tet4d/ui/pygame/topology_lab/` owns UI-only draft/editing helpers shared by 2D, 3D, and 4D.

## Scope

In scope:

- direct 2D and 4D explorer gluing editor rows
- 2D and 4D boundary selection
- tangent permutation/sign editing for 2D and 4D
- 2D/4D explorer preset loading, including unsafe projective/sphere families across all explorer dimensions
- direct 2D/4D save/load through the explorer runtime store
- live 2D/4D graph/adjacency preview summary inside the lab
- 2D/4D preview export through the explorer preview runtime owner

Out of scope:

- mouse-based 4D hyperface picking
- switching live explorer gameplay to the new gluing engine
- deleting the legacy bridge for non-explorer or bridge-only runtime paths

## Acceptance

1. Explorer 2D and Explorer 4D use direct gluing rows instead of legacy edge-rule rows.
2. Saving Explorer 2D/4D lab state writes `ExplorerTopologyProfile` through runtime storage.
3. Exporting Explorer 2D/4D lab state writes the general explorer preview directly, not via the legacy bridge.
4. Normal Game behavior is unchanged in this phase.
5. Unsafe projective/sphere presets are engine-owned, visibly marked in the lab, and validate under the explorer gluing engine for 2D/3D/4D preview dims.
6. Focused tests and full `verify.sh` / `ci_check.sh` stay green.
