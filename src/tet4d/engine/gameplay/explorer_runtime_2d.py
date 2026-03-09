from __future__ import annotations

from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, MoveStep, move_cell


def _rebuild_piece_from_cells(
    piece: ActivePiece2D,
    cells: tuple[tuple[int, int], ...],
) -> ActivePiece2D:
    min_x = min(cell[0] for cell in cells)
    min_y = min(cell[1] for cell in cells)
    rel_blocks = tuple(sorted((x - min_x, y - min_y) for x, y in cells))
    shape = PieceShape2D(piece.shape.name, list(rel_blocks), piece.shape.color_id)
    return ActivePiece2D(shape=shape, pos=(min_x, min_y), rotation=0)


def move_piece_via_explorer_glue_2d(
    piece: ActivePiece2D,
    *,
    dims: tuple[int, int],
    profile: ExplorerTopologyProfile,
    dx: int,
    dy: int,
) -> ActivePiece2D | None:
    if (dx, dy) not in {(-1, 0), (1, 0), (0, -1), (0, 1)}:
        return None
    axis = 0 if dx != 0 else 1
    delta = dx if dx != 0 else dy
    step = MoveStep(axis=axis, delta=delta)
    moved_cells: list[tuple[int, int]] = []
    for cell in piece.cells():
        mapped = move_cell(profile, dims=dims, coord=cell, step=step)
        if mapped is None:
            return None
        moved_cells.append((mapped[0], mapped[1]))
    if len(moved_cells) != len(set(moved_cells)):
        return None
    return _rebuild_piece_from_cells(piece, tuple(moved_cells))


def piece_cells_in_bounds_2d(
    piece: ActivePiece2D,
    *,
    dims: tuple[int, int],
) -> tuple[tuple[int, int], ...] | None:
    cells = tuple(piece.cells())
    if any(x < 0 or x >= dims[0] or y < 0 or y >= dims[1] for x, y in cells):
        return None
    return cells


def can_piece_exist_explorer_2d(
    board_cells: dict[tuple[int, int], int],
    piece: ActivePiece2D,
    *,
    dims: tuple[int, int],
) -> bool:
    cells = piece_cells_in_bounds_2d(piece, dims=dims)
    if cells is None:
        return False
    return all(coord not in board_cells for coord in cells)


__all__ = [
    "can_piece_exist_explorer_2d",
    "move_piece_via_explorer_glue_2d",
    "piece_cells_in_bounds_2d",
]
