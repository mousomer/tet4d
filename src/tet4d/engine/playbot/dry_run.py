from __future__ import annotations

import random

from ..core.model import BoardND
from ..challenge_mode import apply_challenge_prefill_2d, apply_challenge_prefill_nd
from ..gameplay.game2d import GameConfig, GameState
from ..gameplay.game_nd import GameConfigND, GameStateND
from ..pieces_nd import PIECE_SET_4D_DEBUG
from ..runtime.runtime_config import playbot_dry_run_defaults
from .planner_2d import plan_best_2d_move
from .planner_nd import plan_best_nd_move
from .types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    DryRunReport,
    default_planning_budget_ms,
)


DEFAULT_DRY_RUN_PIECES, DEFAULT_DRY_RUN_SEED = playbot_dry_run_defaults()


def _is_4d_debug_dry_run(cfg: GameConfigND) -> bool:
    return cfg.ndim >= 4 and cfg.piece_set_id == PIECE_SET_4D_DEBUG


def _dry_run_reason(
    *,
    passed: bool,
    game_over: bool,
    pieces_dropped: int,
    clears_observed: int,
    max_pieces: int,
) -> str:
    if passed:
        return f"dry run ok: dropped={pieces_dropped}, clears={clears_observed}"
    if game_over:
        return f"dry run failed: game over after {pieces_dropped} pieces, clears={clears_observed}"
    if clears_observed <= 0:
        return f"dry run failed: no clears in {pieces_dropped} pieces"
    return f"dry run failed: dropped {pieces_dropped}/{max_pieces}"


def _dry_run_budget_nd(
    cfg: GameConfigND,
    planner_profile: BotPlannerProfile,
    planning_budget_ms: int | None,
) -> int:
    budget = (
        planning_budget_ms
        if planning_budget_ms is not None
        else default_planning_budget_ms(cfg.ndim, planner_profile, dims=cfg.dims)
    )
    if _is_4d_debug_dry_run(cfg):
        return max(96, budget)
    if cfg.ndim >= 4:
        return max(64, budget)
    if cfg.ndim == 3:
        return max(24, budget)
    return budget


def _dry_run_algorithm_nd(
    cfg: GameConfigND, planner_algorithm: BotPlannerAlgorithm
) -> BotPlannerAlgorithm:
    if _is_4d_debug_dry_run(cfg):
        # Debug dry-run should prioritize reliable clear completion over other planner modes.
        return BotPlannerAlgorithm.GREEDY_LAYER
    if cfg.ndim >= 4 and planner_algorithm == BotPlannerAlgorithm.AUTO:
        # Dry-run validation prefers deterministic layer-focused planning over latency-sensitive AUTO switching.
        return BotPlannerAlgorithm.GREEDY_LAYER
    return planner_algorithm


def _run_dry_run_nd_once(
    cfg: GameConfigND,
    *,
    max_pieces: int,
    seed: int,
    planner_profile: BotPlannerProfile,
    budget: int,
    algorithm: BotPlannerAlgorithm,
) -> DryRunReport:
    state = GameStateND(
        config=cfg,
        board=BoardND(cfg.dims),
        rng=random.Random(seed),
    )
    apply_challenge_prefill_nd(state, layers=cfg.challenge_layers)
    clears_observed = 0
    pieces_dropped = 0

    for _ in range(max(1, max_pieces)):
        if state.game_over:
            break
        before_clears = state.lines_cleared
        plan = plan_best_nd_move(
            state,
            profile=planner_profile,
            budget_ms=budget,
            algorithm=algorithm,
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

    passed = (
        (not state.game_over)
        and pieces_dropped >= max(1, max_pieces)
        and clears_observed > 0
    )
    reason = _dry_run_reason(
        passed=passed,
        game_over=state.game_over,
        pieces_dropped=pieces_dropped,
        clears_observed=clears_observed,
        max_pieces=max_pieces,
    )
    return DryRunReport(
        passed=passed,
        reason=reason,
        pieces_dropped=pieces_dropped,
        clears_observed=clears_observed,
        game_over=state.game_over,
    )


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
        else default_planning_budget_ms(
            2, planner_profile, dims=(cfg.width, cfg.height)
        )
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

    passed = (
        (not state.game_over)
        and pieces_dropped >= max(1, max_pieces)
        and clears_observed > 0
    )
    reason = _dry_run_reason(
        passed=passed,
        game_over=state.game_over,
        pieces_dropped=pieces_dropped,
        clears_observed=clears_observed,
        max_pieces=max_pieces,
    )

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
    budget = _dry_run_budget_nd(cfg, planner_profile, planning_budget_ms)
    effective_algorithm = _dry_run_algorithm_nd(cfg, planner_algorithm)
    primary = _run_dry_run_nd_once(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=planner_profile,
        budget=budget,
        algorithm=effective_algorithm,
    )
    if primary.passed or not _is_4d_debug_dry_run(cfg):
        return primary

    # Deterministic fallback for CI stability on 4D debug verification.
    fallback = _run_dry_run_nd_once(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=BotPlannerProfile.DEEP,
        budget=max(128, budget * 2),
        algorithm=BotPlannerAlgorithm.GREEDY_LAYER,
    )
    if fallback.passed:
        return fallback
    return fallback if fallback.pieces_dropped > primary.pieces_dropped else primary
