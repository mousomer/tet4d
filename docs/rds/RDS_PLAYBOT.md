# Automatic Playbot RDS (2D / 3D / 4D)

Status: Active v1.1 (Verified 2026-02-18)
Author: Omer + Codex
Date: 2026-02-18
Target Runtime: Python 3.11-3.14 + `pygame-ce`

## 1. Purpose

Define one playbot architecture that supports:
1. 2D Tetris (`x,y`),
2. 3D Tetris (`x,y,z`),
3. 4D Tetris (`x,y,z,w`).

The bot must stay deterministic under fixed seed, avoid illegal transitions, and remain usable in real-time gameplay.

## 2. Scope and Non-goals

In scope:
1. Shared planning/execution pipeline for 2D/3D/4D.
2. Runtime integration with current frontends and HUD.
3. Dry-run mode for logic verification without graphics.
4. Test requirements and acceptance criteria.

Out of scope (current release):
1. Reinforcement learning.
2. Networked model downloads.
3. Human-like randomized key timing.

## 3. Operating Modes

1. `OFF`: human-only gameplay.
2. `ASSIST`: bot computes best landing and shows preview/stats; player controls movement.
3. `AUTO`: bot controls movement, rotation, and descent.
4. `STEP`: debug mode; one bot action per step request.

Default mode: `OFF`.

## 4. Current Architecture

### 4.1 Implemented modules

1. `tetris_nd/playbot/types.py`
2. `tetris_nd/playbot/planner_2d.py`
3. `tetris_nd/playbot/planner_nd_core.py`
4. `tetris_nd/playbot/planner_nd.py`
5. `tetris_nd/playbot/planner_nd_search.py`
5. `tetris_nd/playbot/controller.py`
6. `tetris_nd/playbot/dry_run.py`
7. `tetris_nd/playbot/__init__.py`

### 4.2 Core data contracts

1. `BotPlan2D`and`BotPlanND` carry:
2. `final_piece` (the selected settled placement),
3. `stats` (`PlanStats`: candidate count, expected clears, heuristic score, planning ms).
4. `PlayBotController` owns runtime mode, timing, assist preview, and per-piece execution state.
5. `DryRunReport` records pass/fail, reason, dropped piece count, clear count, and game-over state.

### 4.3 State handling rules

1. Planners do not mutate live game state.
2. Candidate scoring uses copied board-cell maps and simulated lock/clear outcomes.
3. Controller executes only via game-state safety methods (`try_move*`,`try_rotate`, lock/spawn).
4. ND orientation enumeration is cached (`lru_cache`) in planner scope.

## 5. Planning Strategy

### 5.1 Shared pipeline (current)

1. Enumerate orientation variants.
2. Enumerate lateral placements for each orientation.
3. Fast-drop each valid candidate to settled position.
4. Simulate lock + plane clear on copied board state.
5. Score result and select best candidate.
6. Return target settled piece (`final_piece`) to controller.

### 5.2 2D planner (`planner_2d.py`)

1. Exhaustive over unique 2D rotations and legal `x` placements.
2. Drop along `y` until collision.
3. Score features:
4. clear reward,
5. aggregate height penalty,
6. hole penalty,
7. bumpiness penalty,
8. max-height penalty,
9. game-over penalty.
10. Profile-based lookahead is available:
11. `FAST`: depth-1 (no followup),
12. `BALANCED/DEEP`: depth-2 with bounded top-candidate followup.
13. `ULTRA`: optional deeper lookahead profile for larger 2D boards.

### 5.3 3D planner (ND path in `planner_nd.py`)

1. Uses ND orientation BFS with 3D planes (`xy`,`xz`,`yz`).
2. Enumerates legal lateral coordinates (`x`,`z`) then drops along gravity axis.
3. Uses heuristic scoring from ND height/holes/roughness/max-height features.
4. Profile-based lookahead is available in 3D:
5. `FAST`: depth-1,
6. `BALANCED/DEEP`: depth-2 with bounded followup.
7. `ULTRA`: deeper candidate breadth/depth profile for slower/high-quality planning.
7. Alternative planner algorithms are supported:
8. `AUTO`(default),`HEURISTIC`,`GREEDY_LAYER`.

### 5.4 4D planner (ND path in `planner_nd.py`)

1. Uses ND orientation BFS with all 4D planes (`xy`,`xz`,`xw`,`yz`,`yw`,`zw`) under orientation/depth caps.
2. Enumerates legal lateral coordinates (`x`,`z`,`w`) then drops along gravity axis.
3. Uses greedy 4D priority key:
4. non-game-over outcomes,
5. cleared layers,
6. layer-completion concentration,
7. lower hole count.
8. This prioritizes finishing layers before secondary shape quality.
9. Alternative planner algorithms are supported:
10. `AUTO`(default),`HEURISTIC`,`GREEDY_LAYER`.

### 5.5 Performance strategy (current)

1. Orientation caching for repeated piece-shape exploration.
2. Column-level precomputation for fast drop settling.
3. Explicit per-plan time budget is enforced (`budget_ms`) with best-so-far fallback under timeout.
4. 4D uses greedy comparison to reduce scoring overhead versus deep heuristic search.
5. Planner profiles (`FAST/BALANCED/DEEP/ULTRA`) tune lookahead depth and candidate breadth.
6. Board-size-aware default planning budgets are loaded from `config/playbot/policy.json`.
7. Adaptive fallback is explicit and config-driven:
8. candidate caps by dimension and budget,
9. lookahead throttling when budget is tight,
10. deadline safety window before timeout.
11. Benchmark thresholds and trend-history output path are config-driven.

## 6. Action Synthesis and Execution

1. Planner outputs target placement (`final_piece`), not raw key events.
2. Controller derives incremental runtime actions each tick:
3. rotation step toward target orientation,
4. lateral step toward target position,
5. soft drop while visible,
6. optional hard drop after configurable soft-drop threshold.
7. Default hard-drop threshold after visible soft drops: `4`.
8. Rotations wait until the active piece is fully visible.
9. Bot behavior is independent from keyboard-binding files.
10. Auto-mode step interval scales from speed level and gravity interval.
11. In `ASSIST`, controller updates preview only and does not move the piece.

## 7. UX Integration

1. Unified menu exposes bot mode, bot speed, planner algorithm, planner profile, and planning budget.
2. Runtime controls include mode cycle and one-step trigger.
3. HUD status lines include mode, speed, planner algorithm/profile/budget, candidate count, expected clears, and plan time.
4. User camera/view controls remain active in bot-controlled gameplay.

## 8. Determinism and Safety

1. Fixed seed + same starting state => deterministic plans.
2. Planner rejects invalid placements via existence/collision checks.
3. Controller fails safe:
4. failed planned action falls back to safe descent/lock flow,
5. stale plan state is replaced on piece-token change,
6. no direct unsafe board mutation from controller.

## 9. Testing Requirements (Current Mapping)

Unit and integration coverage is currently concentrated in:
1. `tetris_nd/tests/test_playbot.py`
2. `tetris_nd/tests/test_gameplay_replay.py`
3. `tetris_nd/tests/test_score_snapshots.py`
4. `tetris_nd/tests/test_game2d.py`
5. `tetris_nd/tests/test_game_nd.py` Required checks:
1. bot places pieces without invalid transitions (2D/ND),
2. assist/auto behavior remains deterministic on replay scripts,
3. dry-run reports successful clears for debug piece sets,
4. 4D greedy key prioritizes layer completion,
5. hard-drop-after-soft-drop threshold behavior works,
6. manual controls and keybinding-dependent gameplay remain unaffected.
7. repeated dry-run stability check passes across seed sweep (`tools/stability/check_playbot_stability.py`).

## 10. Dry-run Requirements

1. Dry run must operate without graphics and without pygame event loop.
2. Dry run must support both 2D and ND configs.
3. Dry run pass criteria:
4. no early game-over,
5. target number of pieces dropped,
6. at least one clear observed.

## 11. Shared ND Design Rules (3D + 4D)

1. `planner_nd_core.py` is the single source of truth for ND candidate generation and scoring primitives.
2. `planner_nd.py` remains a thin orchestration layer (budgeting, lookahead, algorithm selection).
3. Dimension-specific branching should remain configuration-based (`ndim`/ plane set), not duplicated planners.
4. New ND heuristics should be added once and reused by both 3D and 4D paths.
5. Controller ND execution path should remain shared across 3D and 4D.

## 12. Operational Cadence

1. Periodic policy tuning is automated by scheduled workflow:
2. `.github/workflows/stability-watch.yml`
3. Offline analysis tooling remains available at `tools/benchmarks/analyze_playbot_policies.py` for cross-policy comparison across seeds and board sizes.
4. Stability watch script (`tools/stability/check_playbot_stability.py`) uses an extended 4D dry-run horizon (`max_pieces=40`) to reduce false negatives in broad seed sweeps.

## 13. Anti-duplication Guardrails

1. Avoid introducing separate 3D/4D planner files unless required by measured performance.
2. If behavior differs across 3D/4D, prefer branching by config flags in shared ND helpers.
3. Keep controller orchestration shared; avoid per-frontend bot logic forks.

## 14. Acceptance Criteria

1. Bot works in 2D/3D/4D from one controller framework.
2. No illegal moves are applied during bot operation.
3. Deterministic replay tests stay green.
4. Dry-run checks validate playable setups and clear behavior.
5. Existing gameplay and controls remain functional with bot enabled.
