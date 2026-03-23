# Explorer Topology Phase 9

## Goal

Finish the conceptual unification between Explorer Mode and Topology Lab by
introducing one explorer-playground launch contract and routing both entry paths
through the same shell.

## Scope

In scope:

1. one shared launch contract for explorer/topology playground entry
2. one shared builder for shell launch state
3. Explorer Mode and Topology Lab both opening the same shell owner
4. play-preview config assembly moved behind the playground shell owner

Out of scope:

1. deleting the legacy explorer bridge entirely
2. changing Normal Game topology behavior
3. visual 3D/4D picking polish

## Implemented

1. Added `src/tet4d/ui/pygame/topology_lab/app.py` as the canonical owner for
   `ExplorerPlaygroundLaunch`, the shared launch builder, and direct
   play-preview config assembly.
2. Rewired `src/tet4d/ui/pygame/front2d_game.py`,
   `src/tet4d/ui/pygame/front3d_game.py`, and
   `src/tet4d/ui/pygame/front4d_game.py` so Explorer Mode now constructs the
   same launch contract before entering `run_explorer_playground(...)`.
3. Rewired `cli/front.py` Topology Lab action to build the same launch contract
   and call the same shell API, differing only by entry source/gameplay mode.
4. Replaced direct setup-module play-preview config assembly inside
   `src/tet4d/ui/pygame/launch/topology_lab_menu.py` with the playground-owned
   config builder.

## Acceptance

1. Explorer Mode and Topology Lab both route through the same shell owner.
2. Entry points differ by launch context rather than by separate shell setup
   logic.
3. Play-preview config assembly is owned once by the playground shell layer.
4. Explorer topology semantics remain engine-owned; this phase changes launch
   ownership only.

## Follow-up

Phase 10 completed the remaining setup-side split: Explorer setup menus no
longer expose topology-editor rows, and Explorer launch now resolves the stored
explorer gluing profile by default instead of depending on the old setup toggle.
