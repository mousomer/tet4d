from __future__ import annotations

import random

from .core.model import Action, BoardND
from .core.piece_transform import (
    block_axis_bounds,
    canonicalize_blocks_2d,
    canonicalize_blocks_nd,
    enumerate_orientations_nd,
    rotate_blocks_2d,
    rotate_blocks_nd,
    rotate_point_2d,
    rotate_point_nd,
    rotation_planes_nd,
)
from .core.rng import EngineRNG, coerce_random
from .core.rules.state_queries import (
    board_cells as core_board_cells,
    current_piece_cells as core_current_piece_cells,
    is_game_over as core_is_game_over,
)
from .core.step.reducer import step_2d as core_step_2d
from .core.step.reducer import step_nd as core_step_nd
from .gameplay.game2d import GameConfig, GameState
from .gameplay.game_nd import GameConfigND, GameStateND
from .tutorial.api import (
    tutorial_board_dims_runtime,
    tutorial_lesson_ids_runtime,
    tutorial_lessons_payload_runtime,
    tutorial_plan_payload_runtime,
)

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


def board_cells(state: GameState | GameStateND) -> dict[tuple[int, ...], int]:
    return core_board_cells(state)


def current_piece_cells(
    state: GameState | GameStateND, *, include_above: bool = False
) -> tuple[tuple[int, ...], ...]:
    return core_current_piece_cells(state, include_above=include_above)


def is_game_over(state: GameState | GameStateND) -> bool:
    return core_is_game_over(state)


__all__ = [
    "Action",
    "Action2D",
    "BoardND",
    "EngineRNG",
    "GameConfig",
    "GameConfig2D",
    "GameConfigND",
    "GameState",
    "GameState2D",
    "GameStateND",
    "block_axis_bounds",
    "board_cells",
    "canonicalize_blocks_2d",
    "canonicalize_blocks_nd",
    "current_piece_cells",
    "enumerate_orientations_nd",
    "is_game_over",
    "new_game_state_2d",
    "new_game_state_nd",
    "new_rng",
    "rotate_blocks_2d",
    "rotate_blocks_nd",
    "rotate_point_2d",
    "rotate_point_nd",
    "rotation_planes_nd",
    "step",
    "step_2d",
    "step_nd",
    "tutorial_board_dims_runtime",
    "tutorial_lesson_ids_runtime",
    "tutorial_lessons_payload_runtime",
    "tutorial_plan_payload_runtime",
]
