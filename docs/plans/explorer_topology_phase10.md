# Explorer Topology Phase 10

## Goal

Finish the setup-side unification so Explorer Mode no longer uses the pre-launch
setup menu as a topology editor.

## Scope

In scope:

1. hide topology-editor rows from outer Explorer setup menus
2. resolve stored explorer gluing profiles for Explorer launch regardless of the
   old advanced-toggle state
3. route explorer setup export through the stored explorer profile path

Out of scope:

1. deleting the legacy bridge entirely
2. changing Normal Game topology behavior
3. richer 3D/4D scene polish

## Implemented

1. Updated `src/tet4d/engine/runtime/menu_config.py` so Explorer setup fields now
   hide `topology_mode`, `topology_advanced`, and `topology_profile_index`.
2. Updated `src/tet4d/ui/pygame/front2d_setup.py` and
   `src/tet4d/ui/pygame/frontend_nd_setup.py` so Explorer launch always resolves
   the stored gluing profile through `resolve_explorer_topology_runtime_profile(...)`
   with runtime-owned explorer semantics.
3. Updated Explorer setup export in both setup owners so Explorer export always
   emits the stored explorer-topology preview, independent of the old advanced
   toggle.

## Acceptance

1. Outer Explorer setup menus no longer act as topology editors.
2. Explorer launch resolves the stored explorer gluing profile by default.
3. The remaining legacy bridge is reduced to compatibility-only export/preview
   responsibilities, not live Explorer launch setup.
