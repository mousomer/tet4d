# Stage 45A Python 2D/ND Dedup Audit

Status: implemented first safe slice
Date: 2026-07-10

## Authority and constraints

Python remains the semantic authority for gameplay, topology, replay, and
parity behavior. This audit follows `docs/ARCHITECTURE_CONTRACT.md`,
`docs/architecture/authority_map.md`, and the active Tetris RDS documents. It
does not change gameplay rules, topology rules, replay schemas, Godot, native
C++, or authority ownership.

## Duplication seams reviewed

| Seam | Current state | Stage 45A decision |
| --- | --- | --- |
| Placement legality and atomic piece commit | `game2d.py` and `game_nd.py` repeated candidate construction, occupancy validation, self-overlap handling, and commit sequencing; the public gameplay facade repeated candidate construction and validation | Centralize the pure legality and conditional-commit operations in `engine/core/rules/piece_placement.py` |
| Hard drop and lock/respawn lifecycle | Both game states already route through `engine/core/rules/lifecycle.py` | Keep unchanged |
| Lock, clear, score, and analysis flow | Both game states already route through `engine/gameplay/lock_flow.py`; dimensional board clearing remains below that shared orchestration | Keep unchanged |
| Rotation resolution | Both game states already route through `engine/core/rotation_kicks.py`, with dimensional adapters for piece rotation | Keep unchanged |
| Spawn geometry and bag filtering | Parallel structure remains, but 2D and ND piece types, bag fallback rules, and spawn coordinate construction differ | Defer; not safe to combine in the first slice |
| Movement and topology transport | Similar orchestration wraps dimension-specific piece APIs and explorer frame transport | Defer; topology-sensitive and outside the safe first slice |
| Playbot planning | 2D has a separate planner; ND has core/search planners and one private `_can_exist` call | Defer to a planner-focused hardening stage |
| Frontend legality access | Pygame tutorial and ND input paths use the public engine legality API; no UI `_can_exist` calls were found | Keep the public-boundary regression check |

## First safe slice

`piece_placement_is_legal` now owns mapped-pose candidate construction and
validation. `commit_piece_if_legal` owns the validate-then-commit transaction.
The 2D and ND game states retain only their dimensional mapping and current-cell
adapter responsibilities. The public legality facade and the 2D state query use
the same canonical pure rule.

Regression coverage pins dimension-independent legality, collision rejection,
atomic non-mutation on failure, successful commit, 2D/embedded-ND public
translation and rotation equivalence, existing hard-drop behavior, replay
behavior, and lifecycle behavior.

## Result

The first slice removes duplicated placement-rule orchestration without
unifying game loops or changing public APIs. No bug correction or intentional
semantic change is included.
