from __future__ import annotations

import random

from .board import BoardND
from .game2d import Action, GameConfig, GameState
from .game_nd import GameConfigND, GameStateND


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
    if rng is None:
        rng = random.Random(seed)
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
    if rng is None:
        rng = random.Random(seed)
    if board is None:
        board = BoardND(config.dims)
    return GameStateND(config=config, board=board, rng=rng)


def step_2d(state: GameState, action: Action = Action.NONE) -> GameState:
    state.step(action)
    return state


def step_nd(state: GameStateND) -> GameStateND:
    state.step()
    return state


def step(state: GameState | GameStateND, action: Action | None = None) -> GameState | GameStateND:
    if isinstance(state, GameState):
        step_2d(state, Action.NONE if action is None else action)
        return state
    if action is not None:
        raise TypeError("ND engine step does not accept a 2D Action")
    step_nd(state)
    return state


def legal_actions_2d(_: GameState | None = None) -> tuple[Action, ...]:
    return tuple(Action)


def legal_actions(state: GameState | GameStateND) -> tuple[Action, ...]:
    if isinstance(state, GameState):
        return legal_actions_2d(state)
    return ()


def board_cells(state: GameState | GameStateND) -> dict[tuple[int, ...], int]:
    return dict(state.board.cells)


def current_piece_cells(state: GameState | GameStateND, *, include_above: bool = False) -> tuple[tuple[int, ...], ...]:
    cells = state.current_piece_cells_mapped(include_above=include_above)
    return tuple(tuple(cell) for cell in cells)


def is_game_over(state: GameState | GameStateND) -> bool:
    return bool(state.game_over)


__all__ = [
    "Action",
    "Action2D",
    "BoardND",
    "GameConfig",
    "GameConfig2D",
    "GameConfigND",
    "GameState",
    "GameState2D",
    "GameStateND",
    "board_cells",
    "current_piece_cells",
    "is_game_over",
    "legal_actions",
    "legal_actions_2d",
    "new_game_state_2d",
    "new_game_state_nd",
    "step",
    "step_2d",
    "step_nd",
]
