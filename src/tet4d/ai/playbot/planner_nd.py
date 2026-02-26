from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine import api as engine_api
from tet4d.ai.playbot.types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    PlanStats,
    clamp_planning_budget_ms,
    default_planning_budget_ms,
)

GameStateND = engine_api.GameStateND
ActivePieceND = engine_api.ActivePieceND
plan_best_nd_with_budget = engine_api.plan_best_nd_with_budget


@dataclass(frozen=True)
class BotPlanND:
    final_piece: ActivePieceND
    stats: PlanStats


def plan_best_nd_move(
    state: GameStateND,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> BotPlanND | None:
    if state.current_piece is None:
        return None

    dims = state.config.dims
    ndim = state.config.ndim
    planning_budget_ms = budget_ms
    if planning_budget_ms is None:
        planning_budget_ms = default_planning_budget_ms(ndim, profile, dims=dims)
    planning_budget_ms = clamp_planning_budget_ms(
        ndim,
        planning_budget_ms,
        dims=dims,
    )

    search_plan = plan_best_nd_with_budget(
        state,
        profile=profile,
        planning_budget_ms=planning_budget_ms,
        algorithm=algorithm,
    )
    if search_plan is None:
        return None
    return BotPlanND(
        final_piece=search_plan.final_piece,
        stats=search_plan.stats,
    )
