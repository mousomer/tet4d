from __future__ import annotations

from collections.abc import Iterable, Sequence

from tet4d.engine.core.model import BoardND, Coord
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
from tet4d.engine.gameplay.pieces_nd import ActivePieceND
from tet4d.engine.topology_explorer import MoveStep
from tet4d.engine.topology_explorer.transport_resolver import (
    BLOCKED_MOVE,
    ExplorerTransportFrameTransform,
    ExplorerTransportResolver,
)


def _apply_frame_transform(
    piece: ActivePieceND,
    frame_transform: ExplorerTransportFrameTransform,
) -> ActivePieceND:
    if frame_transform.is_identity_linear():
        return piece.moved(frame_transform.translation)
    rel_blocks = tuple(
        frame_transform.apply_linear(block) for block in piece.rel_blocks
    )
    return ActivePieceND(
        shape=piece.shape,
        pos=frame_transform.apply_absolute(piece.pos),
        rel_blocks=rel_blocks,
    )


def _piece_from_exact_cells(
    piece: ActivePieceND,
    moved_cells: Sequence[Sequence[int]],
) -> ActivePieceND:
    cells = tuple(tuple(int(value) for value in coord) for coord in moved_cells)
    origin = cells[0]
    rel_blocks = tuple(
        tuple(cell[index] - origin[index] for index in range(len(origin)))
        for cell in cells
    )
    return ActivePieceND(shape=piece.shape, pos=origin, rel_blocks=rel_blocks)


def _resolved_movement_policy(
    *,
    movement_policy: ExplorerMovementPolicy | None,
    rigid_play_enabled: bool | None,
) -> ExplorerMovementPolicy:
    if movement_policy is not None:
        return normalize_explorer_movement_policy(movement_policy)
    return explorer_movement_policy_from_rigid_play_enabled(rigid_play_enabled)


def move_piece_via_explorer_glue(
    piece: ActivePieceND,
    *,
    transport: ExplorerTransportResolver,
    axis: int,
    delta: int,
    movement_policy: ExplorerMovementPolicy | None = None,
    rigid_play_enabled: bool | None = True,
) -> ActivePieceND | None:
    step = MoveStep(axis=int(axis), delta=int(delta))
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
    ignore_cells: Iterable[Sequence[int]] = (),
) -> bool:
    return validate_candidate_piece_placement(
        build_candidate_piece_placement(piece, piece_cells_in_bounds(piece, dims=dims)),
        board.cells,
        ignore_cells=ignore_cells,
    )


__all__ = [
    "can_piece_exist_explorer",
    "move_piece_via_explorer_glue",
    "piece_cells_in_bounds",
]
