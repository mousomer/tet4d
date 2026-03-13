# Topology Playground Ownership Audit

Last updated: 2026-03-13  
Scope: Explorer Playground ownership and mode-boundary cleanup after the semantics-correctness pass.

## State Buckets

- Canonical persistent topology state owner: `src/tet4d/engine/runtime/topology_playground_state.py`
  - dimensions, draft topology / seam definitions, preset metadata, playability analysis, launch settings
- Inspector transient state owner: `src/tet4d/engine/runtime/topology_playground_state.py` (`probe_state`) plus `src/tet4d/ui/pygame/topology_lab/controls_panel.py` / `scene_state.py` bridge helpers
  - selected cell, probe trace/path/frame, highlighted seam for local traversal inspection
- Sandbox transient state owner: `src/tet4d/engine/runtime/topology_playground_sandbox.py` (`sandbox_piece_state`) plus `src/tet4d/ui/pygame/topology_lab/state_ownership.py`
  - current piece pose/trace plus sandbox-only projection focus / slice anchor / overlay state
- Shared derived cache owner: `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
  - preview payload, basis arrows, boundary snapshot, experiment batch, render/cache signature

## Audit Matrix

| Surface / control | Mode | Owner module | Canonical state touched | Transient state touched | Visible | Wired | Tested | Legacy | Keep / Demote / Remove | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Projection cell click | Inspector | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` | `probe_state` via `scene_state.py` | inspector probe coord/path/frame | yes | yes | yes | no | Keep | Left click updates inspector probe selection and slice anchor. |
| Projection cell click | Sandbox | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` + `src/tet4d/ui/pygame/topology_lab/state_ownership.py` | none | sandbox focus coord/path/frame | yes | yes | yes | no | Keep | No longer overwrites inspector probe state. |
| Boundary pills / seam picks | Editor | `src/tet4d/ui/pygame/topology_lab/boundary_picker.py` | selected boundary/gluing draft through canonical playground bridge | pending source, hovered boundary/glue | yes | yes | yes | no | Keep | Canonical seam selection remains editor-owned even when inspected elsewhere. |
| Transform editor permutation/sign controls | Editor | `src/tet4d/ui/pygame/topology_lab/transform_editor.py` | gluing draft in canonical topology config | none beyond editor selection context | yes | yes | yes | no | Keep | Primary live seam-edit surface. |
| Analysis view preset / board / rigid-play rows | Editor / Play | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | axis sizes, preset metadata, launch settings, playability analysis | selected row only | yes | yes | yes | mixed | Keep | Canonical persistent settings stay here; no inspector/sandbox transient ownership. |
| Probe footer movement grid | Inspector | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` | none | inspector probe coord/frame | yes | yes | yes | no | Keep | Uses inspector-local traversal options only. |
| Sandbox footer movement grid | Sandbox | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` + `src/tet4d/ui/pygame/topology_lab/state_ownership.py` | none | sandbox focus coord/frame | yes | yes | yes | no | Keep | Footer labels and step options no longer borrow inspector state. |
| Sandbox piece controls (spawn / move / rotate / reset / trace) | Sandbox | `src/tet4d/engine/runtime/topology_playground_sandbox.py` via `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py` | `sandbox_piece_state` in canonical playground runtime | sandbox trace / seam crossings / local blocks | yes | yes | yes | no | Keep | Piece semantics remain engine-owned; UI adapter is intentionally thin. |
| Workspace preview / playability panel | Play | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` + `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | playability analysis, preset metadata, launch settings | inspector or sandbox lines depending on active tool | yes | yes | yes | no | Keep | Play summary stays canonical; active-mode line section is transient and mode-specific. |
| Scene overlays (probe path / sandbox focus marker) | Inspector / Sandbox | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` | none | inspector probe path or sandbox focus path | yes | yes | yes | no | Keep | Active mode now chooses the overlay source explicitly. |
| Action bar `Play This Topology` | Play | `src/tet4d/ui/pygame/topology_lab/play_launch.py` + `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical topology config, launch settings, playability analysis | play preview request flag | yes | yes | yes | no | Keep | Launch sync boundary remains explicit and canonical. |
| Save / Export / Experiments / Back rows | Editor / Advanced | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical topology draft / preview export payload | experiment batch cache | yes | yes | yes | partial | Keep | Secondary analysis actions; not primary explorer interaction. |
| Legacy normal-mode rows / resolved-profile export | Legacy compatibility | `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py` | legacy topology profile only | none | yes | yes | yes | yes | Demote | Explicitly isolated compatibility surface; should not compete with live explorer flow. |

## Conclusions

- Inspector and sandbox now have separate transient selection/overlay ownership on the live explorer path.
- Canonical topology, launch, and playability data remain engine/runtime-owned and survive tool switches.
- Legacy normal-mode controls remain intentionally isolated in `legacy_panel_support.py` and are no longer part of the primary explorer ownership path.
