from __future__ import annotations

from dataclasses import dataclass

from tet4d.engine.core.piece_transform import rotate_blocks_2d, rotate_blocks_nd
from tet4d.engine.gameplay.pieces2d import (
    PIECE_SET_2D_CLASSIC,
    get_piece_bag_2d,
    piece_set_2d_label,
)
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    get_piece_shapes_nd,
    piece_set_label,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, movement_steps_for_dimension
from tet4d.engine.topology_explorer.glue_model import coord_in_bounds
from tet4d.engine.topology_explorer.glue_map import move_cell

from .scene_state import TopologyLabState, ensure_sandbox_state


@dataclass(frozen=True)
class SandboxShape:
    set_id: str
    label: str
    name: str
    blocks: tuple[tuple[int, ...], ...]


def _shape_catalog(dimension: int) -> tuple[SandboxShape, ...]:
    if dimension == 2:
        return tuple(
            SandboxShape(
                set_id=PIECE_SET_2D_CLASSIC,
                label=piece_set_2d_label(PIECE_SET_2D_CLASSIC),
                name=shape.name,
                blocks=tuple(tuple(int(v) for v in block) for block in shape.blocks),
            )
            for shape in get_piece_bag_2d(PIECE_SET_2D_CLASSIC)
        )
    piece_set_id = PIECE_SET_3D_STANDARD if dimension == 3 else PIECE_SET_4D_STANDARD
    return tuple(
        SandboxShape(
            set_id=piece_set_id,
            label=piece_set_label(piece_set_id),
            name=shape.name,
            blocks=tuple(tuple(int(v) for v in block) for block in shape.blocks),
        )
        for shape in get_piece_shapes_nd(dimension, piece_set_id=piece_set_id)
    )


def sandbox_shapes_for_state(state: TopologyLabState) -> tuple[SandboxShape, ...]:
    return _shape_catalog(state.dimension)


def _fit_origin_for_blocks(
    blocks: tuple[tuple[int, ...], ...], dims: tuple[int, ...]
) -> tuple[int, ...]:
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


def ensure_piece_sandbox(state: TopologyLabState) -> None:
    ensure_sandbox_state(state)
    sandbox = state.sandbox
    assert sandbox is not None
    shapes = sandbox_shapes_for_state(state)
    sandbox.piece_index = max(0, min(sandbox.piece_index, len(shapes) - 1))
    dims = explorer_topology_preview_dims(state.dimension)
    blocks = shapes[sandbox.piece_index].blocks
    fitted_origin = _fit_origin_for_blocks(blocks, dims)
    if sandbox.origin is None or not coord_in_bounds(sandbox.origin, dims):
        sandbox.origin = fitted_origin
        return
    cells = tuple(
        tuple(sandbox.origin[index] + block[index] for index in range(state.dimension))
        for block in blocks
    )
    if any(not coord_in_bounds(cell, dims) for cell in cells):
        sandbox.origin = fitted_origin


def sandbox_shape(state: TopologyLabState) -> SandboxShape:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    return sandbox_shapes_for_state(state)[state.sandbox.piece_index]


def _rotated_blocks(state: TopologyLabState) -> tuple[tuple[int, ...], ...]:
    shape = sandbox_shape(state)
    assert state.sandbox is not None
    if state.dimension == 2:
        return tuple(tuple(int(v) for v in block) for block in rotate_blocks_2d(shape.blocks, state.sandbox.rotation_steps))
    assert state.sandbox.rotation_plane is not None
    axis_a, axis_b = state.sandbox.rotation_plane
    return tuple(
        tuple(int(v) for v in block)
        for block in rotate_blocks_nd(shape.blocks, axis_a=axis_a, axis_b=axis_b, steps_cw=state.sandbox.rotation_steps)
    )


def sandbox_cells(state: TopologyLabState) -> tuple[tuple[int, ...], ...]:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None and state.sandbox.origin is not None
    blocks = _rotated_blocks(state)
    return tuple(
        tuple(state.sandbox.origin[index] + block[index] for index in range(state.dimension))
        for block in blocks
    )


def sandbox_validity(state: TopologyLabState, profile: ExplorerTopologyProfile) -> tuple[bool, str]:
    del profile
    dims = explorer_topology_preview_dims(state.dimension)
    cells = sandbox_cells(state)
    if len(set(cells)) != len(cells):
        return False, "sandbox piece collapses onto itself"
    for cell in cells:
        if not coord_in_bounds(cell, dims):
            return False, "sandbox rotation leaves preview bounds"
    return True, ""


def move_sandbox_piece(state: TopologyLabState, profile: ExplorerTopologyProfile, step_label: str) -> tuple[bool, str]:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    cells = sandbox_cells(state)
    step = next((item for item in movement_steps_for_dimension(profile.dimension) if item.label == step_label), None)
    if step is None:
        return False, f"unknown sandbox step {step_label}"
    moved: list[tuple[int, ...]] = []
    dims = explorer_topology_preview_dims(state.dimension)
    for cell in cells:
        target = move_cell(profile, dims=dims, coord=cell, step=step)
        if target is None:
            state.sandbox.invalid_message = f"{step_label} blocked for sandbox piece"
            return False, state.sandbox.invalid_message
        moved.append(target)
    if len(set(moved)) != len(moved):
        state.sandbox.invalid_message = "sandbox movement collapses cells"
        return False, state.sandbox.invalid_message
    deltas = {tuple(moved[index][axis] - cells[index][axis] for axis in range(state.dimension)) for index in range(len(cells))}
    if len(deltas) != 1:
        state.sandbox.invalid_message = "sandbox piece cannot remain rigid across seam crossing"
        return False, state.sandbox.invalid_message
    origin_delta = next(iter(deltas))
    assert state.sandbox.origin is not None
    state.sandbox.origin = tuple(state.sandbox.origin[index] + origin_delta[index] for index in range(state.dimension))
    state.sandbox.trace.append(f"{step_label}: {list(cells[0])} -> {list(moved[0])}")
    state.sandbox.trace = state.sandbox.trace[-8:]
    state.sandbox.invalid_message = ""
    return True, "sandbox moved"


def rotate_sandbox_piece(state: TopologyLabState, profile: ExplorerTopologyProfile) -> tuple[bool, str]:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    state.sandbox.rotation_steps = (state.sandbox.rotation_steps + 1) % 4
    valid, message = sandbox_validity(state, profile)
    if valid:
        state.sandbox.invalid_message = ""
        state.sandbox.trace.append("rotate cw")
        state.sandbox.trace = state.sandbox.trace[-8:]
        return True, "sandbox rotated"
    state.sandbox.rotation_steps = (state.sandbox.rotation_steps - 1) % 4
    state.sandbox.invalid_message = message
    return False, message


def cycle_sandbox_piece(state: TopologyLabState, step: int) -> None:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    shapes = sandbox_shapes_for_state(state)
    state.sandbox.piece_index = (state.sandbox.piece_index + step) % len(shapes)
    state.sandbox.rotation_steps = 0
    state.sandbox.trace = []
    state.sandbox.invalid_message = ""
    dims = explorer_topology_preview_dims(state.dimension)
    state.sandbox.origin = _fit_origin_for_blocks(sandbox_shape(state).blocks, dims)


def reset_sandbox_piece(state: TopologyLabState) -> None:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    dims = explorer_topology_preview_dims(state.dimension)
    state.sandbox.rotation_steps = 0
    state.sandbox.origin = _fit_origin_for_blocks(sandbox_shape(state).blocks, dims)
    state.sandbox.trace = []
    state.sandbox.invalid_message = ""


def sandbox_lines(state: TopologyLabState, profile: ExplorerTopologyProfile) -> list[str]:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    shape = sandbox_shape(state)
    valid, message = sandbox_validity(state, profile)
    lines = [
        f"Sandbox piece: {shape.name}",
        f"Set: {shape.label}",
        f"Origin: {list(state.sandbox.origin or ())}",
        f"Cells: {len(sandbox_cells(state))}",
        "Status: valid" if valid else f"Status: invalid ({message})",
    ]
    if state.sandbox.show_trace and state.sandbox.trace:
        lines.append("Trace")
        lines.extend(f"  {item}" for item in state.sandbox.trace[-4:])
    return lines


__all__ = [
    "cycle_sandbox_piece",
    "ensure_piece_sandbox",
    "move_sandbox_piece",
    "reset_sandbox_piece",
    "rotate_sandbox_piece",
    "sandbox_cells",
    "sandbox_lines",
    "sandbox_shape",
    "sandbox_validity",
]
