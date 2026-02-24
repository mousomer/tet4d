from __future__ import annotations

from typing import Any

from ..model.game2d_types import ActivePiece2DLike, GameState2DLike


def board_cells(state: Any) -> dict[tuple[int, ...], int]:
    return dict(state.board.cells)


def current_piece_cells(
    state: Any,
    *,
    include_above: bool = False,
) -> tuple[tuple[int, ...], ...]:
    cells = state.current_piece_cells_mapped(include_above=include_above)
    return tuple(tuple(cell) for cell in cells)


def is_game_over(state: Any) -> bool:
    return bool(state.game_over)


def can_piece_exist_2d(state: GameState2DLike, piece: ActivePiece2DLike) -> bool:
    mapped_cells = state._mapped_piece_cells(piece)
    if mapped_cells is None:
        return False
    for x, y in mapped_cells:
        if y < 0:
            continue
        if (x, y) in state.board.cells:
            return False
    return True


__all__ = [
    "board_cells",
    "can_piece_exist_2d",
    "current_piece_cells",
    "is_game_over",
]
