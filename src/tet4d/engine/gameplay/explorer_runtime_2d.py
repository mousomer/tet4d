from __future__ import annotations

from tet4d.engine.core.piece_transform import rotate_blocks_2d
from tet4d.engine.gameplay.explorer_piece_transport import (
    CELLWISE_DEFORMATION,
    PLAIN_TRANSLATION,
    ExplorerPieceMoveOutcome,
    classify_explorer_piece_move,
)
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, MoveStep, move_cell


def _apply_transport_outcome(
    piece: ActivePiece2D,
    outcome: ExplorerPieceMoveOutcome,
) -> ActivePiece2D:
    transform = outcome.frame_transform
    if transform is None:
        raise ValueError("rigid transport outcome requires a frame transform")
    if outcome.kind == PLAIN_TRANSLATION:
        return piece.moved(transform.translation[0], transform.translation[1])
    current_blocks = rotate_blocks_2d(piece.shape.blocks, piece.rotation)
    transformed_blocks = [transform.apply_linear(block) for block in current_blocks]
    shape = PieceShape2D(
        piece.shape.name,
        list(transformed_blocks),
        piece.shape.color_id,
    )
    return ActivePiece2D(
        shape=shape,
        pos=transform.apply_absolute(piece.pos),
        rotation=0,
    )


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
    source_cells = tuple(piece.cells())
    axis = 0 if dx != 0 else 1
    delta = dx if dx != 0 else dy
    step = MoveStep(axis=axis, delta=delta)
    moved_cells: list[tuple[int, int]] = []
    for cell in source_cells:
        mapped = move_cell(profile, dims=dims, coord=cell, step=step)
        if mapped is None:
            return None
        moved_cells.append((mapped[0], mapped[1]))
    if len(moved_cells) != len(set(moved_cells)):
        return None
    outcome = classify_explorer_piece_move(source_cells, tuple(moved_cells))
    if outcome.kind == CELLWISE_DEFORMATION:
        return None
    return _apply_transport_outcome(piece, outcome)


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
