from __future__ import annotations

from tet4d.engine.core.model import BoardND, Coord
from tet4d.engine.core.piece_transform import normalize_blocks_nd
from tet4d.engine.gameplay.pieces_nd import ActivePieceND
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, MoveStep, move_cell


def _rebuild_piece_from_cells(
    piece: ActivePieceND,
    cells: tuple[Coord, ...],
) -> ActivePieceND:
    mins = tuple(min(cell[axis] for cell in cells) for axis in range(len(cells[0])))
    rel_blocks = normalize_blocks_nd(cells)
    return ActivePieceND(shape=piece.shape, pos=mins, rel_blocks=rel_blocks)


def move_piece_via_explorer_glue(
    piece: ActivePieceND,
    *,
    dims: Coord,
    profile: ExplorerTopologyProfile,
    axis: int,
    delta: int,
) -> ActivePieceND | None:
    step = MoveStep(axis=int(axis), delta=int(delta))
    moved_cells: list[Coord] = []
    for cell in piece.cells():
        mapped = move_cell(profile, dims=dims, coord=cell, step=step)
        if mapped is None:
            return None
        moved_cells.append(mapped)
    if len(moved_cells) != len({tuple(cell) for cell in moved_cells}):
        return None
    return _rebuild_piece_from_cells(piece, tuple(moved_cells))


def piece_cells_in_bounds(
    piece: ActivePieceND,
    *,
    dims: Coord,
) -> tuple[Coord, ...] | None:
    cells = tuple(piece.cells())
    if any(
        coord[axis] < 0 or coord[axis] >= dims[axis]
        for coord in cells
        for axis in range(len(dims))
    ):
        return None
    return cells


def can_piece_exist_explorer(
    board: BoardND,
    piece: ActivePieceND,
    *,
    dims: Coord,
) -> bool:
    cells = piece_cells_in_bounds(piece, dims=dims)
    if cells is None:
        return False
    return all(coord not in board.cells for coord in cells)


__all__ = [
    "can_piece_exist_explorer",
    "move_piece_via_explorer_glue",
    "piece_cells_in_bounds",
]
