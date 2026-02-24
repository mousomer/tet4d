from __future__ import annotations

from typing import Any


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


__all__ = [
    "board_cells",
    "current_piece_cells",
    "is_game_over",
]
