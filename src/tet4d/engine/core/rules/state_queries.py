from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from ..model.game2d_types import ActivePiece2DLike, GameState2DLike
from .piece_placement import piece_placement_is_legal


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


def can_piece_exist_2d(
    state: GameState2DLike,
    piece: ActivePiece2DLike,
    *,
    ignore_cells: Iterable[Sequence[int]] = (),
) -> bool:
    return piece_placement_is_legal(
        piece,
        state.mapped_piece_cells_for_piece(piece, include_above=True),
        state.board.cells,
        ignore_cells=ignore_cells,
    )


__all__ = [
    "board_cells",
    "can_piece_exist_2d",
    "current_piece_cells",
    "is_game_over",
]
