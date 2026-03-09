# Explorer Topology Phase 7

Status: implemented
Date: 2026-03-09

## Objective

Finish the explorer topology lab as a scene-first playground where the graphical
explorer scene is the primary interaction surface for design, inspection, probe
traversal, sandboxing, and direct play launch.

## Scope

In scope:

1. explicit scene-state ownership for active tool, hover/selection, probe state, and sandbox state
2. canonical tool model:
   - navigate
   - inspect_boundary
   - create_gluing
   - edit_transform
   - probe
   - piece_sandbox
   - play_preview
3. direct scene-first editing in Explorer 2D/3D/4D
4. clickable seam/basis arrows that select active gluings
5. live transform editing with immediate preview rebuild
6. probe traversal through the engine-owned gluing runtime, with visible path trace and seam highlighting
7. explorer-only piece sandbox inside the same explorer shell
8. direct play launch from the current in-memory draft topology without requiring save

Out of scope:

1. richer true 3D face-picking geometry beyond the current card/shell scene
2. richer 4D shell grouping beyond the current hybrid hyperface shell
3. deletion of the legacy explorer bridge

## Canonical owners

Engine:

- `src/tet4d/engine/runtime/topology_explorer_preview.py`
- `src/tet4d/engine/runtime/topology_explorer_store.py`
- `src/tet4d/engine/runtime/topology_explorer_bridge.py`
- `src/tet4d/engine/gameplay/explorer_runtime_2d.py`
- `src/tet4d/engine/gameplay/explorer_runtime_nd.py`

UI:

- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/explorer_tools.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/scene2d.py`
- `src/tet4d/ui/pygame/topology_lab/scene3d.py`
- `src/tet4d/ui/pygame/topology_lab/scene4d.py`
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`
- `src/tet4d/ui/pygame/topology_lab/preview.py`
- `src/tet4d/ui/pygame/topology_lab/arrow_overlay.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`

## Delivered behavior

1. Explorer Topology Lab for 2D/3D/4D uses the graphical explorer scene as the primary workspace.
2. Boundaries are selectable directly from the scene.
3. Existing seam arrows are clickable and switch the lab to transform-edit mode for that gluing.
4. Transform changes update the draft gluing profile, preview payload, diagnostics, and arrow overlays immediately.
5. Probe traversal is engine-backed and now records both message trace and coordinate path; traversed seams highlight in the scene.
6. Piece sandbox uses the explorer gluing engine and surfaces rigid-coherence failures explicitly instead of silently repairing seam-crossing motion.
7. `Play` launches Explorer 2D/3D/4D from the current in-memory draft topology without requiring save.
8. Returning from play preview restores the same lab draft.

## Acceptance

1. Scene-first editing is the default interaction model for Explorer 2D/3D/4D.
2. Side panels support the scene; they are not the primary editor.
3. Probe moves, sandbox transport, warnings, and seam arrows all come from engine-owned explorer topology logic.
4. Normal Game topology lab behavior is unchanged.
5. Explorer topology remains separate from Normal Game topology.

## Verification

- focused topology-lab, explorer-preview, and sandbox pytest slices
- `CODEX_MODE=1 ./scripts/verify.sh`
- `CODEX_MODE=1 ./scripts/ci_check.sh`
