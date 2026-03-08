# Explorer Topology Phase 6

## Goal
Add engine-owned diagnostics to explorer topology previews without changing movement semantics.

## Implemented
1. `compile_explorer_topology_preview()` now emits derived warning strings.
2. Warnings currently cover disconnected movement graphs, orientation-reversing seam transforms, and cross-axis seam pairings.
3. Topology Lab renders those warnings directly from the preview payload.

## Non-goals
- no legality changes
- no new UI-only validation rules
- no live gameplay routing changes
