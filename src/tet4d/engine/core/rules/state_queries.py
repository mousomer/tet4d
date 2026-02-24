from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...game2d import Action, GameState
    from ...game_nd import GameStateND


def legal_actions_2d(_: "GameState | None" = None) -> tuple["Action", ...]:
    from ...game2d import Action

    return tuple(Action)


def legal_actions(state: "GameState | GameStateND") -> tuple["Action", ...]:
    from ...game2d import GameState

    if isinstance(state, GameState):
        return legal_actions_2d(state)
    return ()


def board_cells(state: "GameState | GameStateND") -> dict[tuple[int, ...], int]:
    return dict(state.board.cells)


def current_piece_cells(
    state: "GameState | GameStateND",
    *,
    include_above: bool = False,
) -> tuple[tuple[int, ...], ...]:
    cells = state.current_piece_cells_mapped(include_above=include_above)
    return tuple(tuple(cell) for cell in cells)


def is_game_over(state: "GameState | GameStateND") -> bool:
    return bool(state.game_over)


__all__ = [
    "board_cells",
    "current_piece_cells",
    "is_game_over",
    "legal_actions",
    "legal_actions_2d",
]

