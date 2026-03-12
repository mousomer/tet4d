from __future__ import annotations

from tet4d.engine.core.model import BoardND, Coord
from tet4d.engine.gameplay.explorer_piece_transport import (
    CELLWISE_DEFORMATION,
    PLAIN_TRANSLATION,
    ExplorerPieceMoveOutcome,
    classify_explorer_piece_move,
)
from tet4d.engine.gameplay.pieces_nd import ActivePieceND
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, MoveStep, move_cell


def _apply_transport_outcome(
    piece: ActivePieceND,
    outcome: ExplorerPieceMoveOutcome,
) -> ActivePieceND:
    transform = outcome.frame_transform
    if transform is None:
        raise ValueError("rigid transport outcome requires a frame transform")
    if outcome.kind == PLAIN_TRANSLATION:
        return piece.moved(transform.translation)
    rel_blocks = tuple(transform.apply_linear(block) for block in piece.rel_blocks)
    return ActivePieceND(
        shape=piece.shape,
        pos=transform.apply_absolute(piece.pos),
        rel_blocks=rel_blocks,
    )


def move_piece_via_explorer_glue(
    piece: ActivePieceND,
    *,
    dims: Coord,
    profile: ExplorerTopologyProfile,
    axis: int,
    delta: int,
) -> ActivePieceND | None:
    source_cells = tuple(piece.cells())
    step = MoveStep(axis=int(axis), delta=int(delta))
    moved_cells: list[Coord] = []
    for cell in source_cells:
        mapped = move_cell(profile, dims=dims, coord=cell, step=step)
        if mapped is None:
            return None
        moved_cells.append(mapped)
    if len(moved_cells) != len({tuple(cell) for cell in moved_cells}):
        return None
    outcome = classify_explorer_piece_move(source_cells, tuple(moved_cells))
    if outcome.kind == CELLWISE_DEFORMATION:
        return None
    return _apply_transport_outcome(piece, outcome)


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
