# Topology Playground Debt Register

Role: ledger
Status: active
Source of truth: this file for active topology-playground follow-up debt
Supersedes: ad hoc transitional-debt sections previously embedded in authority notes
Last updated: 2026-03-29

## Purpose

Track active transitional debt for the topology-playground path without mixing
that debt into the architecture authority or the visible-shell spec.

This file does not define accepted architecture.
That belongs in `topology_playground_current_authority.md`.

This file does not define the visible shell contract.
That belongs in `topology_playground_shell_redesign_spec.md`.

## Open debt

| Debt | Primary location | Status | Exit condition |
| --- | --- | --- | --- |
| Compatibility-only shell projections remain in the migrated path | `src/tet4d/ui/pygame/topology_lab/scene_state.py` | active | all live readers move to canonical selectors or true caches only |
| Remaining shell-owned cache classification is still concentrated and easy to misread | `scene_state.py`, `workspace_shell.py`, related shell helpers | active | cache/projection boundaries are explicit and narrow |
| `controls_panel.py` remains too large and mixed-responsibility | `src/tet4d/ui/pygame/topology_lab/controls_panel.py` | active | shell-preserving simplification narrows ownership without changing the frozen shell |
| `scene_state.py` still carries compatibility and projection debt | `src/tet4d/ui/pygame/topology_lab/scene_state.py` | deferred | live shell consumes narrower canonical seams |
| Some dimension-specific probe/camera behavior still relies on older helper layers | topology-lab scene/helper modules | active | all probe/camera behavior routes through stable canonical seams |
| Unsafe-topology cross-surface drift still exists in some paths | sandbox / gameplay / preview integration | active | sandbox, preview, and gameplay contracts agree on supported vs unsupported cases |
| Play drop-policy coverage remains incomplete for some topology families | gameplay tests | active | focused regressions pin remaining non-trivial families |
| Historical docs may still mention removed legacy paths | docs layer | active | stale references are removed or moved to history |

## Deferred decomposition rule

The following work is explicitly deferred unless it preserves the already-
settled visible shell contract:

- deeper `controls_panel.py` simplification that changes the frozen shell
- deeper `scene_state.py` simplification that changes the frozen shell
- any cache/routing simplification that would reopen authority boundaries
- broad cleanup motivated only by module size rather than by a specific stable
  seam

## Classification rules

Use these rules when touching retained shell state:

- canonical runtime selectors own explorer-path input truth
- synchronized compatibility projections are not truth sources
- true shell-owned caches must be named and treated as caches
- fallback storage must not silently regain authority
- any new shell field must be classified immediately as:
  - canonical truth,
  - true cache,
  - compatibility projection,
  - fallback storage

## Immediate follow-up priorities

- keep canonical runtime state as the only explorer-path input authority
- keep retained caches/projections from drifting back into truth ownership
- simplify `controls_panel.py` while preserving the frozen shell contract
- simplify `scene_state.py` while preserving the frozen shell contract
- remove stale legacy-path references from active docs

## Exit condition for this ledger

This ledger can be retired or sharply reduced when:

- compatibility-only shell projections are gone or trivial,
- cache/projection boundaries are narrow and explicit,
- `controls_panel.py` and `scene_state.py` no longer carry ambiguous ownership
  debt,
- unsafe-topology cross-surface behavior is pinned,
- historical doc drift is cleaned up.
