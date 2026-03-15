# Topology Playground Ownership Audit

Last updated: 2026-03-14  
Scope: Explorer Playground ownership and mode/action cleanup after the semantics-correctness pass.

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
| Boundary pills / seam picks | Edit | `src/tet4d/ui/pygame/topology_lab/boundary_picker.py` | selected boundary/gluing draft through canonical playground bridge | pending source, hovered boundary/glue | yes | yes | yes | no | Keep | Seam creation/edit remains edit-owned; non-edit modes only retain read-only seam context. |
| Transform editor permutation/sign controls | Edit | `src/tet4d/ui/pygame/topology_lab/transform_editor.py` | gluing draft in canonical topology config | none beyond editor selection context | yes | yes | yes | no | Keep | Interactive only in `Edit`; passive display outside that mode. |
| Analysis view preset / board / rigid-play rows | Editor / Play | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | axis sizes, preset metadata, launch settings, playability analysis | selected row only | yes | yes | yes | mixed | Keep | Canonical persistent settings stay here; no inspector/sandbox transient ownership. |
| Inspect footer movement grid | Inspect | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` | none | inspector probe coord/frame | yes | yes | yes | no | Keep | Uses inspector-local traversal options only. |
| Sandbox footer movement grid | Sandbox | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` + `src/tet4d/ui/pygame/topology_lab/state_ownership.py` | none | sandbox focus coord/frame | yes | yes | yes | no | Keep | Footer labels and step options no longer borrow inspector state. |
| Sandbox piece controls (spawn / move / rotate / reset / trace) | Sandbox | `src/tet4d/engine/runtime/topology_playground_sandbox.py` via `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py` | `sandbox_piece_state` in canonical playground runtime | sandbox trace / seam crossings / local blocks | yes | yes | yes | no | Keep | Piece semantics remain engine-owned; UI adapter is intentionally thin. |
| Workspace preview / playability panel | Play | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` + `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | playability analysis, preset metadata, launch settings | inspect or sandbox lines depending on active mode | yes | yes | yes | no | Keep | Play summary stays canonical; transient line sections now match the active mode explicitly. |
| Scene overlays (probe path / sandbox focus marker) | Inspector / Sandbox | `src/tet4d/ui/pygame/launch/topology_lab_menu.py` | none | inspector probe path or sandbox focus path | yes | yes | yes | no | Keep | Active mode now chooses the overlay source explicitly. |
| Action bar `Apply` / `Remove` | Edit | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical topology draft / seam selection | none | yes | yes | yes | no | Keep | Seam mutation lives only in `Edit`. |
| Action bar `Reset Inspect` | Inspect | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | `probe_state` | inspector probe coord/path/frame | yes | yes | yes | no | Keep | Inspect reset remains read-only/cellwise and does not mutate seams or launch. |
| Action bar sandbox piece controls | Sandbox | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | `sandbox_piece_state` | sandbox trace / focus | yes | yes | yes | no | Keep | Piece experimentation stays sandbox-owned. |
| Action bar `Play This Topology` | Play | `src/tet4d/ui/pygame/topology_lab/play_launch.py` + `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical topology config, launch settings, playability analysis | play preview request flag | yes | yes | yes | no | Keep | Launch stays explicit and canonical, with no duplicate launch action in other modes. |
| Save / Export / Experiments / Back rows | Editor / Advanced | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical topology draft / preview export payload | experiment batch cache | yes | yes | yes | partial | Keep | Secondary analysis actions; not primary explorer interaction. |
| Legacy normal-mode rows / resolved-profile export | Legacy compatibility | `src/tet4d/ui/pygame/topology_lab/legacy_panel_support.py` | legacy topology profile only | none | yes | yes | yes | yes | Demote | Explicitly isolated compatibility surface; should not compete with live explorer flow. |
| Probe-unavailable fallback handling | Compatibility debt | `src/tet4d/ui/pygame/topology_lab/scene_state.py` | canonical `probe_state` | none on migrated explorer path | no | no | yes | removed | Remove | Explorer probe state now stays canonical even when preview validation fails; no retained shell fallback path remains on the migrated explorer route. |
| Dirty shell-field relaunch sync | Compatibility debt | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | canonical `TopologyPlaygroundState` only | none on migrated explorer path | no | no | yes | removed | Remove | Play launch no longer rebuilds explorer runtime state from drifted shell snapshots. |

## Conclusions

- The live explorer path now presents four canonical user-facing modes: `Edit`, `Inspect`, `Sandbox`, and `Play`.
- Inspector and sandbox continue to have separate transient selection/overlay ownership on the live explorer path.
- Action-bar ownership is now unambiguous: seam mutation belongs only to `Edit`, inspect reset belongs only to `Inspect`, piece experimentation belongs only to `Sandbox`, and launch belongs only to `Play`.
- Canonical topology, inspect, sandbox, launch, and playability data remain engine/runtime-owned and survive mode switches.
- Retained shell snapshots no longer backstop probe-unavailable fallback or stale play-launch resync on the migrated explorer path.
- Legacy normal-mode controls remain intentionally isolated in `legacy_panel_support.py` and are no longer part of the primary explorer ownership path.
