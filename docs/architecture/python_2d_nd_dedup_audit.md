# Stage 45 Python 2D/ND Dedup Audit

Status: continued major pass implemented
Date: 2026-07-11

## Authority and constraints

Python remains the semantic authority for gameplay, topology, replay, and
parity behavior. This audit follows `docs/ARCHITECTURE_CONTRACT.md`,
`docs/architecture/authority_map.md`, and the active Tetris RDS documents. It
does not change gameplay rules, topology rules, replay schemas, Godot, native
C++, or authority ownership.

## Duplication seams reviewed

| Seam | Current state | Stage 45 decision |
| --- | --- | --- |
| Placement legality and atomic piece commit | Stage 45A centralized candidate validation and conditional commit in `engine/core/rules/piece_placement.py` | Keep the pure owner; expose each game state's dimensional legality adapter as `piece_pose_legal` so the public facade and planners do not reconstruct or privately access legality |
| Movement and topology transport | Ordinary translations already commit through the shared placement transaction, but explorer movement also owns seam transport, gravity-seam rejection, ND frame composition, and dimensional piece APIs | Keep existing placement reuse; defer further movement unification because the remaining parallel code is topology- and frame-sensitive |
| Rotation resolution and commit | Both states used the shared kick resolver but repeated resolve-then-commit orchestration | Add `resolve_and_commit_rotated_piece` beside the existing pure kick resolver; retain dimensional rotation and movement adapters |
| Hard drop and lock/respawn lifecycle | Both states already route through `engine/core/rules/lifecycle.py` | Keep unchanged and retain focused lifecycle coverage |
| Lock, clear, score, and analysis flow | Both states called `apply_lock_flow` but repeated mapped-cell rejection, above-gravity game-over handling, state accounting, and analysis assignment | Centralize current-piece lock mutation in `apply_current_piece_lock_flow`; retain dimensional mapping and board dimensions in each state |
| Spawn validity and installation | 2D and ND repeated legality, game-over, and current-piece installation; ND additionally resets its transported piece frame | Centralize the shared install transaction in `install_spawn_candidate`, with an ND pre-install callback; retain dimensional spawn geometry and bag rules |
| Spawn geometry and bag filtering | Piece types, bag retry/fallback policy, and spawn coordinate construction remain dimension-specific | Defer; combining these rules would obscure meaningful behavior differences |
| Playbot planning | 2D and ND use different candidate generation and evaluation strategies; ND candidate enumeration called private `_can_exist` | Route ND planning through the public gameplay legality owner; defer planner algorithm and simulation unification |
| Frontend legality access | Pygame tutorial and ND input paths use the public engine legality API | Keep the public boundary and extend its regression check to playbot code |

## Completed slices

Stage 45A centralized mapped piece-pose legality and atomic
validate-then-commit behavior in `engine/core/rules/piece_placement.py`.

The continued pass centralizes spawn installation/game-over handling, rotation
resolve-and-commit behavior, and current-piece lock/clear/score/analysis state
mutation. The public gameplay legality facade and ND planner now route through
the game states' public dimensional legality adapters.

Regression coverage pins shared helper contracts, collision rejection, atomic
failure, successful rotation commit, illegal rotation non-mutation, spawn
game-over behavior, lock accounting, public-boundary use, and
2D/embedded-ND translation, rotation, hard-drop, spawn, lock, clear, and score
equivalence.

## Explicitly deferred

- Explorer/topology-aware movement orchestration, including seam transport,
  gravity-seam rejection, and ND piece-frame composition.
- Dimension-specific spawn coordinate construction, bag generation, retry, and
  fallback rules.
- 2D and ND planner candidate generation, simulation, heuristics, and search
  policy.
- Full 2D/ND game-state or game-loop unification.

These paths remain separate because their current differences carry documented
dimensional or topology semantics. They should not be combined without a
narrower audit and behavior-first regression coverage.

## Result

Several high-value state-transition seams now have one Python owner without
merging game loops or changing public gameplay behavior. No bug correction or
intentional semantic change is included. Python remains the reference and
semantic authority.
