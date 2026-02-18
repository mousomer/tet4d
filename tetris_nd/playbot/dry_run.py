from __future__ import annotations

import random

from ..board import BoardND
from ..challenge_mode import apply_challenge_prefill_2d, apply_challenge_prefill_nd
from ..game2d import GameConfig, GameState
from ..game_nd import GameConfigND, GameStateND
from ..runtime_config import playbot_dry_run_defaults
from .planner_2d import plan_best_2d_move
from .planner_nd import plan_best_nd_move
from .types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    DryRunReport,
    default_planning_budget_ms,
)


DEFAULT_DRY_RUN_PIECES, DEFAULT_DRY_RUN_SEED = playbot_dry_run_defaults()


def run_dry_run_2d(
    cfg: GameConfig,
    *,
    max_pieces: int = DEFAULT_DRY_RUN_PIECES,
    seed: int = DEFAULT_DRY_RUN_SEED,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    state = GameState(
        config=cfg,
        board=BoardND((cfg.width, cfg.height)),
        rng=random.Random(seed),
    )
    apply_challenge_prefill_2d(state, layers=cfg.challenge_layers)
    clears_observed = 0
    pieces_dropped = 0
    budget = (
        planning_budget_ms
        if planning_budget_ms is not None
        else default_planning_budget_ms(2, planner_profile, dims=(cfg.width, cfg.height))
    )

    for _ in range(max(1, max_pieces)):
        if state.game_over:
            break
        before_clears = state.lines_cleared
        plan = plan_best_2d_move(
            state,
            profile=planner_profile,
            budget_ms=budget,
            algorithm=planner_algorithm,
        )
        if plan is None:
            break
        state.current_piece = plan.final_piece
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        pieces_dropped += 1
        if state.lines_cleared > before_clears:
            clears_observed += 1

    passed = (not state.game_over) and pieces_dropped >= max(1, max_pieces) and clears_observed > 0
    if passed:
        reason = f"dry run ok: dropped={pieces_dropped}, clears={clears_observed}"
    elif state.game_over:
        reason = f"dry run failed: game over after {pieces_dropped} pieces, clears={clears_observed}"
    elif clears_observed <= 0:
        reason = f"dry run failed: no clears in {pieces_dropped} pieces"
    else:
        reason = f"dry run failed: dropped {pieces_dropped}/{max_pieces}"

    return DryRunReport(
        passed=passed,
        reason=reason,
        pieces_dropped=pieces_dropped,
        clears_observed=clears_observed,
        game_over=state.game_over,
    )


def run_dry_run_nd(
    cfg: GameConfigND,
    *,
    max_pieces: int = DEFAULT_DRY_RUN_PIECES,
    seed: int = DEFAULT_DRY_RUN_SEED,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    state = GameStateND(
        config=cfg,
        board=BoardND(cfg.dims),
        rng=random.Random(seed),
    )
    apply_challenge_prefill_nd(state, layers=cfg.challenge_layers)
    clears_observed = 0
    pieces_dropped = 0
    budget = (
        planning_budget_ms
        if planning_budget_ms is not None
        else default_planning_budget_ms(cfg.ndim, planner_profile, dims=cfg.dims)
    )

    for _ in range(max(1, max_pieces)):
        if state.game_over:
            break
        before_clears = state.lines_cleared
        plan = plan_best_nd_move(
            state,
            profile=planner_profile,
            budget_ms=budget,
            algorithm=planner_algorithm,
        )
        if plan is None:
            break
        state.current_piece = plan.final_piece
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
        pieces_dropped += 1
        if state.lines_cleared > before_clears:
            clears_observed += 1

    passed = (not state.game_over) and pieces_dropped >= max(1, max_pieces) and clears_observed > 0
    if passed:
        reason = f"dry run ok: dropped={pieces_dropped}, clears={clears_observed}"
    elif state.game_over:
        reason = f"dry run failed: game over after {pieces_dropped} pieces, clears={clears_observed}"
    elif clears_observed <= 0:
        reason = f"dry run failed: no clears in {pieces_dropped} pieces"
    else:
        reason = f"dry run failed: dropped {pieces_dropped}/{max_pieces}"

    return DryRunReport(
        passed=passed,
        reason=reason,
        pieces_dropped=pieces_dropped,
        clears_observed=clears_observed,
        game_over=state.game_over,
    )
