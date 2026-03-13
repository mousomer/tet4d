from __future__ import annotations

from collections.abc import Iterable, Sequence

from tet4d.engine.core.piece_transform import rotate_blocks_2d
from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    validate_candidate_piece_placement,
)
from tet4d.engine.gameplay.explorer_movement_policy import (
    CELLWISE_FREE,
    ExplorerMovementPolicy,
    explorer_movement_policy_from_rigid_play_enabled,
    normalize_explorer_movement_policy,
)
from tet4d.engine.gameplay.explorer_piece_transport import CELLWISE_DEFORMATION
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.transport_resolver import (
    BLOCKED_MOVE,
    ExplorerTransportFrameTransform,
    ExplorerTransportResolver,
)


def _apply_frame_transform(
    piece: ActivePiece2D,
    frame_transform: ExplorerTransportFrameTransform,
) -> ActivePiece2D:
    if frame_transform.is_identity_linear():
        return piece.moved(
            frame_transform.translation[0], frame_transform.translation[1]
        )
    current_blocks = rotate_blocks_2d(piece.shape.blocks, piece.rotation)
    transformed_blocks = [
        frame_transform.apply_linear(block) for block in current_blocks
    ]
    shape = PieceShape2D(
        piece.shape.name,
        list(transformed_blocks),
        piece.shape.color_id,
    )
    return ActivePiece2D(
        shape=shape,
        pos=frame_transform.apply_absolute(piece.pos),
        rotation=0,
    )


def _piece_from_exact_cells(
    piece: ActivePiece2D,
    moved_cells: Sequence[Sequence[int]],
) -> ActivePiece2D:
    cells = tuple((int(coord[0]), int(coord[1])) for coord in moved_cells)
    origin = cells[0]
    shape = PieceShape2D(
        piece.shape.name,
        [(cell[0] - origin[0], cell[1] - origin[1]) for cell in cells],
        piece.shape.color_id,
    )
    return ActivePiece2D(shape=shape, pos=origin, rotation=0)


def _resolved_movement_policy(
    *,
    movement_policy: ExplorerMovementPolicy | None,
    rigid_play_enabled: bool | None,
) -> ExplorerMovementPolicy:
    if movement_policy is not None:
        return normalize_explorer_movement_policy(movement_policy)
    return explorer_movement_policy_from_rigid_play_enabled(rigid_play_enabled)


def move_piece_via_explorer_glue_2d(
    piece: ActivePiece2D,
    *,
    transport: ExplorerTransportResolver,
    dx: int,
    dy: int,
    movement_policy: ExplorerMovementPolicy | None = None,
    rigid_play_enabled: bool | None = True,
) -> ActivePiece2D | None:
    if (dx, dy) not in {(-1, 0), (1, 0), (0, -1), (0, 1)}:
        return None
    axis = 0 if dx != 0 else 1
    delta = dx if dx != 0 else dy
    step = MoveStep(axis=axis, delta=delta)
    policy = _resolved_movement_policy(
        movement_policy=movement_policy,
        rigid_play_enabled=rigid_play_enabled,
    )
    step_result = transport.resolve_piece_step(piece.cells(), step)
    if step_result.kind == BLOCKED_MOVE:
        return None
    if policy == CELLWISE_FREE:
        assert step_result.moved_cells is not None
        use_exact_cells = step_result.kind == CELLWISE_DEFORMATION or any(
            cell_step.traversal is not None for cell_step in step_result.cell_steps
        )
        if use_exact_cells:
            return _piece_from_exact_cells(piece, step_result.moved_cells)
        assert step_result.frame_transform is not None
        return _apply_frame_transform(piece, step_result.frame_transform)
    if step_result.kind == CELLWISE_DEFORMATION and not step_result.rigidly_coherent:
        return None
    if step_result.frame_transform is None:
        assert step_result.moved_cells is not None
        return _piece_from_exact_cells(piece, step_result.moved_cells)
    return _apply_frame_transform(piece, step_result.frame_transform)


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
    ignore_cells: Iterable[Sequence[int]] = (),
) -> bool:
    return validate_candidate_piece_placement(
        build_candidate_piece_placement(
            piece, piece_cells_in_bounds_2d(piece, dims=dims)
        ),
        board_cells,
        ignore_cells=ignore_cells,
    )


__all__ = [
    "can_piece_exist_explorer_2d",
    "move_piece_via_explorer_glue_2d",
    "piece_cells_in_bounds_2d",
]
