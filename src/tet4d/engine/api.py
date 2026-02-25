from __future__ import annotations

import random
from typing import Any

from .core.model import (
    Action,
    BoardND,
    GameConfig2DCoreView,
    GameConfigNDCoreView,
    GameState2DCoreView,
    GameStateNDCoreView,
)
from .core.rules.state_queries import (
    board_cells as core_board_cells,
    current_piece_cells as core_current_piece_cells,
    is_game_over as core_is_game_over,
)
from .core.step.reducer import step_2d as core_step_2d
from .core.step.reducer import step_nd as core_step_nd
from .gameplay.game2d import GameConfig, GameState
from .gameplay.game_nd import GameConfigND, GameStateND
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
from .runtime_config import (
    playbot_benchmark_history_file,
    playbot_benchmark_p95_thresholds,
)
from .runtime.project_config import project_constant_int as _project_constant_int


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


def simulate_lock_board(
    state: GameStateND, piece: Any
) -> tuple[dict[tuple[int, ...], int], int, bool]:
    from .playbot.planner_nd_core import simulate_lock_board as _simulate_lock_board

    return _simulate_lock_board(state, piece)


def greedy_key_4d(
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    cleared: int,
    game_over: bool,
) -> tuple[int, int, int, int]:
    from .playbot.planner_nd_core import greedy_key_4d as _greedy_key_4d

    return _greedy_key_4d(
        cells,
        dims=dims,
        gravity_axis=gravity_axis,
        cleared=cleared,
        game_over=game_over,
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


def step(
    state: GameState | GameStateND, action: Action | None = None
) -> GameState | GameStateND:
    if isinstance(state, GameState):
        return core_step_2d(state, Action.NONE if action is None else action)
    if action is not None:
        raise TypeError("ND engine step does not accept a 2D Action")
    return core_step_nd(state)


def legal_actions_2d(_: GameState | None = None) -> tuple[Action, ...]:
    del _
    return tuple(Action)


def legal_actions(state: GameState | GameStateND) -> tuple[Action, ...]:
    if isinstance(state, GameState):
        return legal_actions_2d(state)
    return ()


def board_cells(state: GameState | GameStateND) -> dict[tuple[int, ...], int]:
    return core_board_cells(state)


def current_piece_cells(
    state: GameState | GameStateND, *, include_above: bool = False
) -> tuple[tuple[int, ...], ...]:
    return core_current_piece_cells(state, include_above=include_above)


def is_game_over(state: GameState | GameStateND) -> bool:
    return core_is_game_over(state)


def config_view_2d(config: GameConfig) -> GameConfig2DCoreView:
    return config.to_core_view()


def state_view_2d(state: GameState) -> GameState2DCoreView:
    return state.to_core_view()


def config_view_nd(config: GameConfigND) -> GameConfigNDCoreView:
    return config.to_core_view()


def state_view_nd(state: GameStateND) -> GameStateNDCoreView:
    return state.to_core_view()


def project_constant_int(
    path: tuple[str, ...],
    default: int,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    return _project_constant_int(
        path,
        default,
        min_value=min_value,
        max_value=max_value,
    )


def project_root_path():
    from .runtime.project_config import project_root_path as _project_root_path

    return _project_root_path()


def run_front3d_ui() -> None:
    from .front3d_game import run as _run_front3d

    _run_front3d()


def run_front4d_ui() -> None:
    from .front4d_game import run as _run_front4d

    _run_front4d()


def profile_4d_new_layer_view_3d(*, xw_deg: float = 0.0, zw_deg: float = 0.0) -> Any:
    from .front4d_game import LayerView3D as _LayerView3D

    return _LayerView3D(xw_deg=xw_deg, zw_deg=zw_deg)


def profile_4d_draw_game_frame(*args: Any, **kwargs: Any) -> Any:
    from .front4d_render import draw_game_frame as _draw_game_frame

    return _draw_game_frame(*args, **kwargs)


def profile_4d_create_initial_state(cfg: GameConfigND) -> GameStateND:
    from .frontend_nd import create_initial_state as _create_initial_state

    return _create_initial_state(cfg)


def profile_4d_init_fonts() -> Any:
    from .frontend_nd import init_fonts as _init_fonts

    return _init_fonts()


def profile_4d_grid_mode_full() -> Any:
    from .view_modes import GridMode as _GridMode

    return _GridMode.FULL


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
    "config_view_2d",
    "config_view_nd",
    "default_planning_budget_ms",
    "greedy_key_4d",
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
    "profile_4d_create_initial_state",
    "profile_4d_draw_game_frame",
    "profile_4d_grid_mode_full",
    "profile_4d_init_fonts",
    "profile_4d_new_layer_view_3d",
    "run_dry_run_2d",
    "run_dry_run_nd",
    "run_front3d_ui",
    "run_front4d_ui",
    "simulate_lock_board",
    "state_view_2d",
    "state_view_nd",
    "step",
    "step_2d",
    "step_nd",
]
