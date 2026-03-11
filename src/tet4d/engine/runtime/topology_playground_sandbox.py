from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.core.model import Coord
from tet4d.engine.core.piece_transform import rotate_blocks_2d, rotate_blocks_nd
from tet4d.engine.gameplay.api import piece_set_options_for_dimension_gameplay
from tet4d.engine.gameplay.pieces2d import (
    PIECE_SET_2D_OPTIONS,
    get_piece_bag_2d,
    piece_set_2d_label,
)
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    get_piece_shapes_nd,
    piece_set_label,
)
from tet4d.engine.runtime.topology_playground_state import (
    TRANSPORT_OWNER_EXPLORER,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState,
)
from tet4d.engine.topology_explorer import movement_steps_for_dimension
from tet4d.engine.topology_explorer.glue_model import MoveStep, coord_in_bounds
from tet4d.engine.topology_explorer.glue_map import map_boundary_exit, move_cell


@dataclass(frozen=True)
class SandboxShape:
    set_id: str
    label: str
    name: str
    blocks: tuple[Coord, ...]


def _selected_piece_set_id(state: TopologyPlaygroundState) -> str:
    index = int(state.launch_settings.piece_set_index)
    if state.dimension == 2:
        options = tuple(PIECE_SET_2D_OPTIONS)
    elif state.dimension == 3:
        options = tuple(piece_set_options_for_dimension_gameplay(3))
    else:
        options = tuple(piece_set_options_for_dimension_gameplay(4))
    if not options:
        return PIECE_SET_3D_STANDARD if state.dimension == 3 else PIECE_SET_4D_STANDARD
    return options[max(0, min(len(options) - 1, index))]


def sandbox_shapes_for_state(
    state: TopologyPlaygroundState,
) -> tuple[SandboxShape, ...]:
    piece_set_id = _selected_piece_set_id(state)
    if state.dimension == 2:
        return tuple(
            SandboxShape(
                set_id=piece_set_id,
                label=piece_set_2d_label(piece_set_id),
                name=shape.name,
                blocks=tuple(
                    tuple(int(value) for value in block) for block in shape.blocks
                ),
            )
            for shape in get_piece_bag_2d(piece_set_id)
        )
    return tuple(
        SandboxShape(
            set_id=piece_set_id,
            label=piece_set_label(piece_set_id),
            name=shape.name,
            blocks=tuple(tuple(int(value) for value in block) for block in shape.blocks),
        )
        for shape in get_piece_shapes_nd(state.dimension, piece_set_id=piece_set_id)
    )


def _fit_origin_for_blocks(blocks: tuple[Coord, ...], dims: Coord) -> Coord:
    fitted: list[int] = []
    for axis, size in enumerate(dims):
        min_block = min(block[axis] for block in blocks)
        max_block = max(block[axis] for block in blocks)
        min_origin = -min_block
        max_origin = size - 1 - max_block
        if min_origin > max_origin:
            fitted.append(min_origin)
            continue
        center = max(0, size // 2)
        fitted.append(max(min_origin, min(max_origin, center)))
    return tuple(fitted)


def _trace_tuple(values: object) -> tuple[str, ...]:
    return tuple(str(entry) for entry in values or ())


def _set_trace(
    sandbox: TopologyPlaygroundSandboxPieceState,
    *entries: str,
    limit: int,
) -> None:
    history = list(_trace_tuple(sandbox.trace))
    history.extend(str(entry) for entry in entries)
    sandbox.trace = tuple(history[-limit:])


def _set_seam_crossings(
    sandbox: TopologyPlaygroundSandboxPieceState,
    entries: tuple[str, ...],
    *,
    limit: int,
) -> None:
    sandbox.seam_crossings = tuple(str(entry) for entry in entries[-limit:])


def ensure_piece_sandbox_state(state: TopologyPlaygroundState) -> None:
    sandbox = state.sandbox_piece_state
    sandbox.trace = _trace_tuple(sandbox.trace)
    sandbox.seam_crossings = _trace_tuple(sandbox.seam_crossings)
    sandbox.invalid_message = str(sandbox.invalid_message)
    shapes = sandbox_shapes_for_state(state)
    if not shapes:
        raise ValueError('sandbox piece catalog is empty')
    sandbox.piece_index = max(0, min(int(sandbox.piece_index), len(shapes) - 1))
    sandbox.enabled = True
    base_blocks = shapes[sandbox.piece_index].blocks
    if sandbox.local_blocks is None:
        sandbox.local_blocks = base_blocks
    blocks = tuple(tuple(int(value) for value in block) for block in sandbox.local_blocks)
    fitted_origin = _fit_origin_for_blocks(blocks, state.axis_sizes)
    if sandbox.origin is None or not coord_in_bounds(sandbox.origin, state.axis_sizes):
        sandbox.origin = fitted_origin
        return
    cells = tuple(
        tuple(
            sandbox.origin[axis] + block[axis] for axis in range(state.dimension)
        )
        for block in blocks
    )
    if any(not coord_in_bounds(cell, state.axis_sizes) for cell in cells):
        sandbox.origin = fitted_origin


def sandbox_shape(state: TopologyPlaygroundState) -> SandboxShape:
    ensure_piece_sandbox_state(state)
    return sandbox_shapes_for_state(state)[state.sandbox_piece_state.piece_index]


def spawn_sandbox_piece(state: TopologyPlaygroundState) -> None:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    shape = sandbox_shape(state)
    sandbox.enabled = True
    sandbox.local_blocks = shape.blocks
    sandbox.origin = _fit_origin_for_blocks(shape.blocks, state.axis_sizes)
    sandbox.trace = ()
    sandbox.seam_crossings = ()
    sandbox.invalid_message = ''


def sandbox_cells(state: TopologyPlaygroundState) -> tuple[Coord, ...]:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    assert sandbox.origin is not None
    blocks = tuple(tuple(int(value) for value in block) for block in sandbox.local_blocks or ())
    return tuple(
        tuple(sandbox.origin[axis] + block[axis] for axis in range(state.dimension))
        for block in blocks
    )


def rotate_blocks_for_action(
    dimension: int,
    blocks: tuple[Coord, ...],
    *,
    action: str,
) -> tuple[Coord, ...] | None:
    if action == 'rotate_xy_pos':
        return tuple(
            tuple(int(value) for value in block)
            for block in rotate_blocks_2d(blocks, 1)
        )
    if action == 'rotate_xy_neg':
        return tuple(
            tuple(int(value) for value in block)
            for block in rotate_blocks_2d(blocks, -1)
        )
    plane_map = {
        'rotate_xy_pos': (0, 1, 1),
        'rotate_xy_neg': (0, 1, -1),
        'rotate_xz_pos': (0, 2, 1),
        'rotate_xz_neg': (0, 2, -1),
        'rotate_yz_pos': (1, 2, 1),
        'rotate_yz_neg': (1, 2, -1),
        'rotate_xw_pos': (0, 3, 1),
        'rotate_xw_neg': (0, 3, -1),
        'rotate_yw_pos': (1, 3, 1),
        'rotate_yw_neg': (1, 3, -1),
        'rotate_zw_pos': (2, 3, 1),
        'rotate_zw_neg': (2, 3, -1),
    }
    spec = plane_map.get(action)
    if spec is None:
        return None
    axis_a, axis_b, steps = spec
    if int(dimension) <= max(axis_a, axis_b):
        return None
    return tuple(
        tuple(int(value) for value in block)
        for block in rotate_blocks_nd(
            blocks,
            axis_a=axis_a,
            axis_b=axis_b,
            steps_cw=steps,
        )
    )


def sandbox_validity(state: TopologyPlaygroundState) -> tuple[bool, str]:
    cells = sandbox_cells(state)
    if len(set(cells)) != len(cells):
        return False, 'sandbox piece collapses onto itself'
    for cell in cells:
        if not coord_in_bounds(cell, state.axis_sizes):
            return False, 'sandbox rotation leaves preview bounds'
    return True, ''


def rotate_sandbox_piece_action(
    state: TopologyPlaygroundState,
    action: str,
) -> tuple[bool, str]:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    current_blocks = tuple(
        tuple(int(value) for value in block) for block in sandbox.local_blocks or ()
    )
    rotated = rotate_blocks_for_action(state.dimension, current_blocks, action=action)
    if rotated is None:
        return False, f'unsupported sandbox rotation {action}'
    previous = sandbox.local_blocks
    sandbox.local_blocks = rotated
    valid, message = sandbox_validity(state)
    if valid:
        sandbox.invalid_message = ''
        _set_trace(sandbox, action, limit=8)
        return True, 'sandbox rotated'
    sandbox.local_blocks = previous
    sandbox.invalid_message = message
    return False, message


def _move_target_for_transport(
    state: TopologyPlaygroundState,
    coord: Coord,
    *,
    step: MoveStep,
) -> tuple[Coord | None, str | None]:
    if state.transport_policy.owner == TRANSPORT_OWNER_EXPLORER:
        traversal = map_boundary_exit(
            state.explorer_profile,
            dims=state.axis_sizes,
            coord=coord,
            step=step,
        )
        target = move_cell(
            state.explorer_profile,
            dims=state.axis_sizes,
            coord=coord,
            step=step,
        )
        crossing = None
        if traversal is not None:
            crossing = (
                f'{traversal.glue_id}: {traversal.source_boundary.label} -> '
                f'{traversal.target_boundary.label}'
            )
        return target, crossing
    candidate = list(coord)
    candidate[step.axis] += step.delta
    target = state.transport_policy.base_policy.map_coord(
        tuple(candidate),
        allow_above_gravity=state.transport_policy.allow_above_gravity,
    )
    return target, None


def move_sandbox_piece(
    state: TopologyPlaygroundState,
    step_label: str,
) -> tuple[bool, str]:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    cells = sandbox_cells(state)
    step = next(
        (
            item
            for item in movement_steps_for_dimension(state.dimension)
            if item.label == step_label
        ),
        None,
    )
    if step is None:
        return False, f'unknown sandbox step {step_label}'
    moved: list[Coord] = []
    seam_crossings: list[str] = []
    for cell in cells:
        target, seam_crossing = _move_target_for_transport(
            state,
            cell,
            step=step,
        )
        if target is None:
            sandbox.invalid_message = f'{step_label} blocked for sandbox piece'
            return False, sandbox.invalid_message
        moved.append(target)
        if seam_crossing is not None:
            seam_crossings.append(seam_crossing)
    if len(set(moved)) != len(moved):
        sandbox.invalid_message = 'sandbox movement collapses cells'
        return False, sandbox.invalid_message
    deltas = {
        tuple(
            moved[index][axis] - cells[index][axis] for axis in range(state.dimension)
        )
        for index in range(len(cells))
    }
    if len(deltas) != 1:
        sandbox.invalid_message = 'sandbox piece cannot remain rigid across seam crossing'
        return False, sandbox.invalid_message
    origin_delta = next(iter(deltas))
    assert sandbox.origin is not None
    sandbox.origin = tuple(
        sandbox.origin[axis] + origin_delta[axis] for axis in range(state.dimension)
    )
    sandbox.invalid_message = ''
    _set_trace(
        sandbox,
        f'{step_label}: {list(cells[0])} -> {list(moved[0])}',
        limit=8,
    )
    _set_seam_crossings(sandbox, tuple(seam_crossings), limit=4)
    return True, 'sandbox moved'


def rotate_sandbox_piece(state: TopologyPlaygroundState) -> tuple[bool, str]:
    return rotate_sandbox_piece_action(state, 'rotate_xy_pos')


def cycle_sandbox_piece(state: TopologyPlaygroundState, step: int) -> None:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    shapes = sandbox_shapes_for_state(state)
    sandbox.enabled = True
    sandbox.piece_index = (sandbox.piece_index + int(step)) % len(shapes)
    shape = sandbox_shape(state)
    sandbox.local_blocks = shape.blocks
    sandbox.origin = _fit_origin_for_blocks(shape.blocks, state.axis_sizes)
    sandbox.trace = ()
    sandbox.seam_crossings = ()
    sandbox.invalid_message = ''


def reset_sandbox_piece(state: TopologyPlaygroundState) -> None:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    sandbox.enabled = True
    shape = sandbox_shape(state)
    sandbox.local_blocks = shape.blocks
    sandbox.origin = _fit_origin_for_blocks(shape.blocks, state.axis_sizes)
    sandbox.trace = ()
    sandbox.seam_crossings = ()
    sandbox.invalid_message = ''


def sandbox_lines(state: TopologyPlaygroundState) -> list[str]:
    ensure_piece_sandbox_state(state)
    sandbox = state.sandbox_piece_state
    shape = sandbox_shape(state)
    valid, message = sandbox_validity(state)
    lines = [
        f'Sandbox piece: {shape.name}',
        f'Set: {shape.label}',
        f'Origin: {list(sandbox.origin or ())}',
        f'Cells: {len(sandbox_cells(state))}',
        'Status: valid' if valid else f'Status: invalid ({message})',
    ]
    seam_crossings = _trace_tuple(sandbox.seam_crossings)
    if seam_crossings:
        lines.append('Seam crossings')
        lines.extend(f'  {entry}' for entry in seam_crossings)
    trace = _trace_tuple(sandbox.trace)
    if sandbox.show_trace and trace:
        lines.append('Trace')
        lines.extend(f'  {entry}' for entry in trace[-4:])
    return lines


__all__ = [
    'SandboxShape',
    'cycle_sandbox_piece',
    'ensure_piece_sandbox_state',
    'move_sandbox_piece',
    'reset_sandbox_piece',
    'rotate_blocks_for_action',
    'rotate_sandbox_piece',
    'rotate_sandbox_piece_action',
    'sandbox_cells',
    'sandbox_lines',
    'sandbox_shape',
    'sandbox_shapes_for_state',
    'sandbox_validity',
    'spawn_sandbox_piece',
]
