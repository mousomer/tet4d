# Explorer Topology Phase 8

## Goal

Shrink the legacy explorer bridge so setup and export flows consume one runtime-owned explorer-topology resolver instead of importing edge-rule conversion directly from UI layers.

## Scope

In scope:

1. runtime-owned explorer topology selection resolution
2. runtime-owned legacy-profile preview export helper
3. caller migration in 2D/ND setup and Topology Lab export paths

Out of scope:

1. deleting the bridge entirely
2. changing Normal Game topology behavior
3. changing explorer movement semantics

## Implemented

1. Added `src/tet4d/engine/runtime/topology_explorer_runtime.py` as the runtime-owned resolver/export facade over the legacy bridge and explorer store.
2. Migrated `src/tet4d/ui/pygame/front2d_setup.py` and `src/tet4d/ui/pygame/frontend_nd_setup.py` to that runtime facade.
3. Migrated legacy explorer preview export in `src/tet4d/ui/pygame/launch/topology_lab_menu.py` to the same runtime facade.
4. Removed direct `topology_explorer_bridge` imports from live UI setup/export owners.

## Acceptance

1. Explorer setup/export callers in UI no longer import the bridge directly.
2. The bridge remains available only as a runtime implementation detail while non-advanced explorer setup/export still need compatibility conversion.
3. Explorer runtime behavior is unchanged.
