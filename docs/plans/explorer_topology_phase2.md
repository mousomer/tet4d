# Explorer Topology Phase 2

## Goal

Add runtime-owned explorer topology profile storage and preview export on top of the new engine-owned gluing kernel without switching live gameplay topology semantics yet.

## Canonical owners

1. `src/tet4d/engine/topology_explorer/`
   - pure gluing model, validation, mapping, and movement graph
2. `src/tet4d/engine/runtime/topology_explorer_store.py`
   - explorer-only JSON profile storage
3. `src/tet4d/engine/runtime/topology_explorer_bridge.py`
   - legacy explorer edge-rule to gluing-profile bridge for the representable subset
4. `src/tet4d/engine/runtime/topology_explorer_preview.py`
   - compiled preview/export payloads

## Non-goals

1. No live gameplay switch to the general gluing engine yet.
2. No full topology-lab GUI rewrite yet.
3. No Normal Game topology semantic changes.

## Acceptance

1. Explorer general-gluing profiles have one runtime-owned save/load path.
2. Explorer preview export is runtime-owned and compiled from the general gluing kernel.
3. The current topology lab can export an explorer gluing preview only when the current legacy explorer profile is representable as a true paired-boundary gluing.
4. Asymmetric legacy edge rules are rejected for the new preview path with an explicit message, not silently misrepresented.
