# Explorer Topology Phase 3

Status: Active implementation batch

## Objective

Add a real 3D Explorer Topology Lab MVP that edits general explorer gluings directly instead of editing only legacy per-edge rules.

## Canonical owners

1. `src/tet4d/engine/topology_explorer/` owns gluing semantics, transforms, validation, and graph mapping.
2. `src/tet4d/engine/runtime/topology_explorer_store.py` owns explorer gluing persistence.
3. `src/tet4d/engine/runtime/topology_explorer_preview.py` owns explorer preview compilation/export.
4. `src/tet4d/ui/pygame/launch/topology_lab_menu.py` owns the lab entrypoint/orchestration.
5. `src/tet4d/ui/pygame/topology_lab/` owns UI-only draft/editing helpers.

## Scope

In scope:

- 3D explorer-only direct gluing editor rows
- source/target boundary selection
- tangent permutation selection
- tangent sign-flip toggles
- explorer preset loading
- direct save/load through the explorer runtime store
- live graph/adjacency preview summary inside the lab
- preview export through the explorer preview runtime owner

Out of scope:

- 4D direct gluing editor
- mouse-based exploded-cube picking
- switching live explorer gameplay to the new gluing engine
- deleting the legacy bridge for non-direct paths

## Acceptance

1. Explorer 3D uses direct gluing rows instead of legacy edge-rule rows.
2. Saving Explorer 3D lab state writes `ExplorerTopologyProfile` through runtime storage.
3. Exporting Explorer 3D lab state writes the general explorer preview directly, not via the legacy bridge.
4. Normal Game and 4D explorer remain behaviorally unchanged in this phase.
5. Focused tests and full `verify.sh` / `ci_check.sh` stay green.
