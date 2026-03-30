# Explorer Topology Phase 5

## Goal
Route live ND Explorer gameplay through the general gluing engine while leaving Normal Game and 2D gameplay semantics unchanged.

## Scope
- `src/tet4d/engine/gameplay/game_nd.py`
- `src/tet4d/engine/gameplay/explorer_runtime_nd.py`
- `src/tet4d/ui/pygame/frontend_nd_input.py`
- `src/tet4d/ui/pygame/frontend_nd_setup.py`
- focused regression tests for config, live movement, and predictive input

## Implemented
1. `GameConfigND` now accepts `explorer_topology_profile`.
2. Live ND explorer movement/collision/hard-drop routing uses the explorer gluing engine when that profile is present.
3. ND predictive input checks now use the same explorer movement path for move actions.
4. Explorer advanced setup loads stored explorer gluing profiles; non-advanced explorer setup bridges resolved explorer edge rules into the gluing model.
5. Explorer advanced topology export now emits explorer movement previews instead of legacy edge-rule exports.

## Non-goals
- no Normal Game topology changes
- no 2D live explorer gameplay migration in this phase
- no 3D/4D lab UX redesign beyond the existing direct gluing editor

## Acceptance
- Live ND explorer movement wraps through glued boundaries.
- ND input prediction agrees with live movement for explorer wraps.
- Normal Game remains on the legacy topology path.
- `verify.sh` and `ci_check.sh` stay green.
