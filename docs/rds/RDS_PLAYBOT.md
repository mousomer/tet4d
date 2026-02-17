# Automatic Playbot RDS (2D / 3D / 4D)

Status: Proposed v0.1  
Author: Omer + Codex  
Date: 2026-02-16  
Target Runtime: Python 3.14 + `pygame-ce`

## 1. Purpose

Define a single automatic playbot architecture that supports:
1. 2D Tetris (`x,y`),
2. 3D Tetris (`x,y,z`),
3. 4D Tetris (`x,y,z,w`).

The bot must be deterministic under fixed seed, safe (no illegal actions), and fast enough to run in real time in-game.

## 2. Scope and Non-goals

In scope:
1. Bot planning/evaluation/execution pipeline.
2. Shared interfaces and per-dimension strategy variants.
3. Runtime integration into current frontends and menus.
4. Test plan and acceptance criteria.

Out of scope (initial milestone):
1. Reinforcement learning training pipeline.
2. Online model downloads or network dependencies.
3. Human-like key timing simulation.

## 3. Operating Modes

1. `OFF`: human-only gameplay.
2. `ASSIST`: bot suggests target placement (ghost/preview + HUD stats), player executes.
3. `AUTO`: bot controls active piece fully while the user can still control camera/view.
4. `STEP`: debug mode, one bot action per key press (for verification).

Default mode: `OFF`.

## 4. Architecture

## 4.1 Modules

1. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/types.py`
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/state_clone.py`
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/nd_context.py`
4. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/orientation_cache.py`
5. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/candidate_gen_nd.py`
6. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/simulate_nd.py`
7. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/eval_features_nd.py`
8. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/search_nd.py`
9. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/profiles.py`
10. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/planner_2d.py`
11. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/planner_nd.py`
12. `/Users/omer/workspace/test-code/tet4d/tetris_nd/playbot/controller.py`

## 4.2 Core interfaces

1. `BotPlan`: action queue + target placement + score breakdown.
2. `Planner`: `plan(state, cfg, budget_ms) -> BotPlan`.
3. `Evaluator`: `score(board_after_lock, metadata) -> float`.
4. `Controller`: executes plan at configured action rate and requests replans when needed.

## 4.3 State handling rules

1. Planning never mutates live game state.
2. Planner uses cloned state snapshots only.
3. Clone must include:
4. board cells,
5. current piece position/orientation,
6. next bag,
7. score/lines metadata needed for lookahead heuristics.

## 5. Planning Strategy

## 5.1 Shared pipeline

1. Enumerate candidate landing placements for current piece.
2. Simulate lock + clear result for each candidate.
3. Score resulting board with dimension-specific heuristic weights.
4. Optionally perform limited next-piece lookahead (depth 2).
5. Choose highest score, synthesize executable action queue.
6. Validate queue feasibility against current live state before execution.

## 5.2 2D planner

1. Exhaustive search over:
2. unique 2D rotations,
3. all valid `x` placements,
4. hard-drop landing per placement.
5. Use depth-2 lookahead by default (`current + expected next`).
6. Heuristic features:
7. clear reward,
8. aggregate column height penalty,
9. hole count penalty,
10. bumpiness penalty,
11. well depth penalty.

## 5.3 3D planner

1. Use shared ND candidate generator and search engine with 3D context.
2. Enumerate unique 3D orientations via ND rotation-group BFS (`xy`, `xz`, `yz`).
3. Enumerate lateral coordinates (`x,z`) for each orientation and drop along `y`.
4. Use beam search for depth-2 (configurable beam width).
5. Heuristic features:
6. clear reward,
7. cavity count penalty (enclosed empty cells),
8. surface roughness penalty on top height field over `x,z`,
9. floating-cell penalty (support deficit),
10. max height penalty.

## 5.4 4D planner

1. Use the same shared ND candidate generator and search engine with 4D context.
2. Enumerate orientation states with bounded BFS over 6 rotation planes:
3. `xy`, `xz`, `xw`, `yz`, `yw`, `zw`.
4. Enumerate lateral coordinates (`x,z,w`) for each orientation and drop along `y`.
5. Use beam search depth-1 by default; optional stochastic rollouts for tie-break.
6. Heuristic features:
7. clear reward,
8. hyper-cavity penalty,
9. roughness penalty over `x,z,w` top hyper-surface,
10. isolated-pocket penalty,
11. max height and height variance penalties.

## 5.5 Performance budgets

1. 2D: target < `8 ms` per plan on default board.
2. 3D: target < `25 ms` per plan on default board.
3. 4D: target < `45 ms` per plan on default board.
4. If budget exceeded:
5. reduce lookahead depth first,
6. then reduce beam width,
7. then fallback to greedy depth-1.

## 6. Action Synthesis and Execution

1. Planner emits abstract actions (not raw key events), e.g.:
2. `move_axis(axis, delta)`,
3. `rotate_plane(axis_a, axis_b, steps)`,
4. `soft_drop`.
5. Controller maps abstract actions directly to game-state methods (`try_move_axis`, `try_rotate`, `soft-drop via gravity-axis move`).
6. Bot logic must not depend on current keyboard bindings.
7. Runtime bot movement must avoid instant hard-drop in visible gameplay; descent should be animated cell-by-cell.
8. Auto-mode action interval must match game gravity interval derived from speed level.
9. In bot-controlled descent modes, gravity updates should not double-advance piece descent.
10. Replan triggers:
11. piece lock/spawn,
12. user manual override action,
13. action failure on stale plan.

## 7. UX and Menu Integration

1. Add "Playbot" section in unified menu:
2. mode (`OFF/ASSIST/AUTO/STEP`),
3. strategy profile (`Safe/Balanced/Aggressive`),
4. action rate,
5. planning budget.
6. In-game HUD additions:
7. bot mode,
8. last plan score,
9. candidate count,
10. planning time (ms).
11. Add non-intrusive toggle hotkey for runtime bot on/off.

## 8. Determinism and Safety

1. Given identical seed and starting state, bot decisions must be reproducible.
2. Planner must reject illegal placements (out of bounds/collision).
3. Controller must fail safe:
4. on invalid queued action, cancel plan and replan,
5. never crash the main game loop.

## 9. Testing Requirements

1. Unit tests:
2. candidate generator validity by dimension,
3. orientation enumeration uniqueness,
4. evaluator feature calculations.
5. Integration tests:
6. bot actions never produce invalid state transitions,
7. bot can survive at least `N` drops on default boards (per dimension),
8. deterministic replay with bot enabled.
9. Regression tests:
10. enabling bot does not break manual controls,
11. keybinding changes do not affect bot behavior.

Suggested test files:
1. `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_playbot_2d.py`
2. `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_playbot_nd.py`
3. `/Users/omer/workspace/test-code/tet4d/tetris_nd/tests/test_playbot_replay.py`

## 10. Phased Rollout

1. Phase 1: 2D exhaustive planner + AUTO mode + tests.
2. Phase 2: 3D beam planner + ASSIST overlay + tests.
3. Phase 3: 4D constrained beam planner + performance tuning.
4. Phase 4: profile tuning and UX polish.

## 11. Shared ND Plan (3D + 4D)

Goal: maximize logic sharing so 3D and 4D differ only by configuration and weight profiles.

### 11.1 Shared components (single implementation)

1. ND context builder:
2. `ndim`, `gravity_axis`, rotation planes, lateral axes, board dims.
3. Orientation enumeration:
4. rotation-BFS + canonical block normalization + dedup hash.
5. Candidate generation:
6. lateral translation sweep + gravity drop landing simulation.
7. State simulator:
8. immutable apply-move/rotate/drop/lock transitions on cloned state.
9. Feature extraction:
10. clears, max height, aggregate height, roughness, cavities, hole depth, isolation.
11. Search:
12. beam search + depth control + tie-break rules + budget cutoffs.
13. Plan synthesis:
14. orientation delta + translation path + drop action.

### 11.2 Dimension-specific adapters (thin wrappers)

1. 3D adapter defines:
2. rotation planes (`xy`, `xz`, `yz`),
3. default depth (`2`),
4. beam width and feature weights.
5. 4D adapter defines:
6. rotation planes (`xy`, `xz`, `xw`, `yz`, `yw`, `zw`),
7. default depth (`1`),
8. stricter orientation/beam caps and feature weights.
9. No duplicated candidate/search/simulation code in adapters.

### 11.3 Shared cache strategy

1. Orientation cache key:
2. `(ndim, piece_shape_signature, allowed_rotation_planes)`.
3. Candidate cache key:
4. `(board_signature, piece_orientation_signature, lateral_bounds)`.
5. Cache lifetime: current piece lifetime only (invalidate on lock/spawn).
6. Deterministic ordering must be preserved when iterating cache results.

## 12. 3D Bot Implementation Plan

1. Implement ND context + orientation cache + candidate generator.
2. Implement generic beam search engine and generic ND feature extractor.
3. Add `Planner3D` wrapper that only provides strategy profile and budgets.
4. Integrate into 3D loop (`AUTO`, `ASSIST`, `STEP` support).
5. Add tests:
6. orientation uniqueness on 3D shapes,
7. no illegal candidate placements,
8. deterministic plan choice on fixed seed,
9. latency budget check on default 3D board.

Exit criteria:
1. 3D planner uses shared ND core only.
2. No duplicated search or candidate code in 3D wrapper.
3. Existing 3D gameplay tests remain green.

## 13. 4D Bot Implementation Plan

1. Reuse ND core without forking search/candidate modules.
2. Add 4D-specific caps:
3. max orientation states,
4. max beam width,
5. greedy fallback when budget exhausted.
6. Add `Planner4D` wrapper with 4D profile weights and limits.
7. Integrate into 4D loop with same controller and HUD fields as 3D.
8. Add tests:
9. orientation bounds and determinism,
10. no illegal candidate placements,
11. no action deadlock,
12. latency budget check on default 4D board.

Exit criteria:
1. 4D wrapper is configuration-only over shared ND core.
2. `9/0` rotation reliability remains unaffected in manual mode.
3. Existing 4D gameplay and replay tests remain green.

## 14. Anti-duplication Guardrails

1. `planner_nd.py` is the only ND planner implementation file.
2. 3D/4D wrappers may configure, not re-implement, candidate/search/eval logic.
3. Any new heuristic must be added to shared `eval_features_nd.py` first.
4. Any new search policy must be added to shared `search_nd.py` first.
5. CI check: reject duplicated functions with same name/signature across 3D/4D wrappers.
6. Code review rule: if a change touches both 3D and 4D planner behavior, require shared-core diff unless strongly justified.

## 15. Acceptance Criteria

1. Bot works in 2D/3D/4D with one shared controller framework.
2. No illegal moves are applied.
3. Planning latency stays within budgets on default board sizes.
4. Bot behavior is deterministic under fixed seed.
5. Existing gameplay tests stay green; new playbot tests pass.
