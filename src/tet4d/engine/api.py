from __future__ import annotations

import random
from typing import Any

from .core.model import BoardND
from .core.rules.state_queries import (
    board_cells as core_board_cells,
    current_piece_cells as core_current_piece_cells,
    is_game_over as core_is_game_over,
    legal_actions as core_legal_actions,
    legal_actions_2d as core_legal_actions_2d,
)
from .core.step.reducer import step as core_step
from .core.step.reducer import step_2d as core_step_2d
from .core.step.reducer import step_nd as core_step_nd
from .game2d import Action, GameConfig, GameState
from .game_nd import GameConfigND, GameStateND
from .pieces2d import PIECE_SET_2D_CLASSIC, PIECE_SET_2D_DEBUG
from .pieces_nd import (
    PIECE_SET_3D_DEBUG,
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_DEBUG,
    PIECE_SET_4D_STANDARD,
)
from .playbot import PlayBotController
from .playbot.types import (
    BOT_MODE_OPTIONS,
    BOT_PLANNER_ALGORITHM_OPTIONS,
    BOT_PLANNER_PROFILE_OPTIONS,
    BotMode,
    BotPlannerAlgorithm,
    BotPlannerProfile,
    DryRunReport,
    bot_mode_from_index,
    bot_mode_label,
    bot_planner_algorithm_from_index,
    bot_planner_algorithm_label,
    bot_planner_profile_from_index,
    bot_planner_profile_label,
    default_planning_budget_ms,
)
from .core.rng import EngineRNG, coerce_random
from .runtime_config import playbot_benchmark_history_file, playbot_benchmark_p95_thresholds


# Stable aliases for callers that want explicit dimensional naming.
Action2D = Action
GameConfig2D = GameConfig
GameState2D = GameState


def new_game_state_2d(
    config: GameConfig,
    *,
    board: BoardND | None = None,
    rng: random.Random | None = None,
    seed: int | None = None,
) -> GameState:
    rng = coerce_random(rng=rng, seed=seed)
    if board is None:
        board = BoardND((config.width, config.height))
    return GameState(config=config, board=board, rng=rng)


def new_game_state_nd(
    config: GameConfigND,
    *,
    board: BoardND | None = None,
    rng: random.Random | None = None,
    seed: int | None = None,
) -> GameStateND:
    rng = coerce_random(rng=rng, seed=seed)
    if board is None:
        board = BoardND(config.dims)
    return GameStateND(config=config, board=board, rng=rng)


def new_rng(seed: int | float | str | bytes | bytearray | None = None) -> EngineRNG:
    return EngineRNG(seed)


def plan_best_2d_move(
    state: GameState,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> Any:
    from .playbot.planner_2d import plan_best_2d_move as _plan_best_2d_move

    return _plan_best_2d_move(
        state,
        profile=profile,
        budget_ms=budget_ms,
        algorithm=algorithm,
    )


def plan_best_nd_move(
    state: GameStateND,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> Any:
    from .playbot.planner_nd import plan_best_nd_move as _plan_best_nd_move

    return _plan_best_nd_move(
        state,
        profile=profile,
        budget_ms=budget_ms,
        algorithm=algorithm,
    )


def run_dry_run_2d(
    cfg: GameConfig,
    *,
    max_pieces: int = 64,
    seed: int = 1337,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    from .playbot.dry_run import run_dry_run_2d as _run_dry_run_2d

    return _run_dry_run_2d(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=planner_profile,
        planning_budget_ms=planning_budget_ms,
        planner_algorithm=planner_algorithm,
    )


def run_dry_run_nd(
    cfg: GameConfigND,
    *,
    max_pieces: int = 64,
    seed: int = 1337,
    planner_profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    planning_budget_ms: int | None = None,
    planner_algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> DryRunReport:
    from .playbot.dry_run import run_dry_run_nd as _run_dry_run_nd

    return _run_dry_run_nd(
        cfg,
        max_pieces=max_pieces,
        seed=seed,
        planner_profile=planner_profile,
        planning_budget_ms=planning_budget_ms,
        planner_algorithm=planner_algorithm,
    )


def step_2d(state: GameState, action: Action = Action.NONE) -> GameState:
    return core_step_2d(state, action)


def step_nd(state: GameStateND) -> GameStateND:
    return core_step_nd(state)


def step(state: GameState | GameStateND, action: Action | None = None) -> GameState | GameStateND:
    return core_step(state, action)


def legal_actions_2d(_: GameState | None = None) -> tuple[Action, ...]:
    return core_legal_actions_2d(_)


def legal_actions(state: GameState | GameStateND) -> tuple[Action, ...]:
    return core_legal_actions(state)


def board_cells(state: GameState | GameStateND) -> dict[tuple[int, ...], int]:
    return core_board_cells(state)


def current_piece_cells(state: GameState | GameStateND, *, include_above: bool = False) -> tuple[tuple[int, ...], ...]:
    return core_current_piece_cells(state, include_above=include_above)


def is_game_over(state: GameState | GameStateND) -> bool:
    return core_is_game_over(state)


__all__ = [
    "Action",
    "Action2D",
    "BoardND",
    "BOT_MODE_OPTIONS",
    "BOT_PLANNER_ALGORITHM_OPTIONS",
    "BOT_PLANNER_PROFILE_OPTIONS",
    "BotMode",
    "BotPlannerAlgorithm",
    "BotPlannerProfile",
    "DryRunReport",
    "PlayBotController",
    "GameConfig",
    "GameConfig2D",
    "GameConfigND",
    "GameState",
    "GameState2D",
    "GameStateND",
    "EngineRNG",
    "board_cells",
    "bot_mode_from_index",
    "bot_mode_label",
    "bot_planner_algorithm_from_index",
    "bot_planner_algorithm_label",
    "bot_planner_profile_from_index",
    "bot_planner_profile_label",
    "current_piece_cells",
    "default_planning_budget_ms",
    "is_game_over",
    "legal_actions",
    "legal_actions_2d",
    "new_game_state_2d",
    "new_game_state_nd",
    "new_rng",
    "PIECE_SET_2D_CLASSIC",
    "PIECE_SET_2D_DEBUG",
    "PIECE_SET_3D_DEBUG",
    "PIECE_SET_3D_STANDARD",
    "PIECE_SET_4D_DEBUG",
    "PIECE_SET_4D_STANDARD",
    "plan_best_2d_move",
    "plan_best_nd_move",
    "playbot_benchmark_history_file",
    "playbot_benchmark_p95_thresholds",
    "run_dry_run_2d",
    "run_dry_run_nd",
    "step",
    "step_2d",
    "step_nd",
]
