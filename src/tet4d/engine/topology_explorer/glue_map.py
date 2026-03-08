from __future__ import annotations

from dataclasses import dataclass

from ..core.model import Coord
from .glue_model import (
    SIDE_NEG,
    SIDE_POS,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    MoveStep,
    coord_in_bounds,
    tangent_axes_for_boundary,
)
from .glue_validate import validate_explorer_topology_profile


def _apply_transform(
    source_values: tuple[int, ...],
    *,
    target_extents: tuple[int, ...],
    transform: BoundaryTransform,
) -> tuple[int, ...]:
    mapped = [0] * len(source_values)
    for source_index, target_index in enumerate(transform.permutation):
        source_value = source_values[source_index]
        if transform.signs[source_index] < 0:
            mapped[target_index] = target_extents[target_index] - 1 - source_value
        else:
            mapped[target_index] = source_value
    return tuple(mapped)


def _boundary_extents(dims: Coord, boundary: BoundaryRef) -> tuple[int, ...]:
    return tuple(dims[axis] for axis in tangent_axes_for_boundary(boundary))


def _active_boundary_lookup(
    profile: ExplorerTopologyProfile,
) -> dict[BoundaryRef, tuple[GluingDescriptor, bool]]:
    lookup: dict[BoundaryRef, tuple[GluingDescriptor, bool]] = {}
    for glue in profile.active_gluings():
        lookup[glue.source] = (glue, True)
        lookup[glue.target] = (glue, False)
    return lookup


def _boundary_for_exit(coord: Coord, step: MoveStep, dims: Coord) -> BoundaryRef | None:
    axis_value = coord[step.axis]
    if step.delta < 0:
        if axis_value != 0:
            return None
        return BoundaryRef(dimension=len(dims), axis=step.axis, side=SIDE_NEG)
    if axis_value != dims[step.axis] - 1:
        return None
    return BoundaryRef(dimension=len(dims), axis=step.axis, side=SIDE_POS)


def _target_inward_step(boundary: BoundaryRef) -> MoveStep:
    return MoveStep(axis=boundary.axis, delta=1 if boundary.side == SIDE_NEG else -1)


@dataclass(frozen=True)
class BoundaryTraversal:
    glue_id: str
    source_boundary: BoundaryRef
    target_boundary: BoundaryRef
    source_coord: Coord
    target_coord: Coord
    exit_step: MoveStep
    entry_step: MoveStep


def map_boundary_exit(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
    step: MoveStep,
) -> BoundaryTraversal | None:
    validate_explorer_topology_profile(profile, dims=tuple(int(value) for value in dims))
    if not coord_in_bounds(coord, dims):
        raise ValueError("coord must be in bounds")
    if step.axis >= len(dims):
        raise ValueError("move axis must exist in the board dimension")
    source_boundary = _boundary_for_exit(coord, step, dims)
    if source_boundary is None:
        return None
    lookup = _active_boundary_lookup(profile)
    binding = lookup.get(source_boundary)
    if binding is None:
        return None
    glue, forward = binding
    target_boundary = glue.target if forward else glue.source
    transform = glue.transform if forward else glue.transform.inverse()

    source_axes = tangent_axes_for_boundary(source_boundary)
    target_axes = tangent_axes_for_boundary(target_boundary)
    source_values = tuple(coord[axis] for axis in source_axes)
    target_extents = _boundary_extents(dims, target_boundary)
    target_values = _apply_transform(
        source_values,
        target_extents=target_extents,
        transform=transform,
    )

    target_coord = [0] * len(dims)
    for axis, value in zip(target_axes, target_values):
        target_coord[axis] = value
    target_coord[target_boundary.axis] = (
        0 if target_boundary.side == SIDE_NEG else dims[target_boundary.axis] - 1
    )

    return BoundaryTraversal(
        glue_id=glue.glue_id,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        source_coord=tuple(coord),
        target_coord=tuple(int(value) for value in target_coord),
        exit_step=step,
        entry_step=_target_inward_step(target_boundary),
    )


def move_cell(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
    step: MoveStep,
) -> Coord | None:
    validate_explorer_topology_profile(profile, dims=tuple(int(value) for value in dims))
    if not coord_in_bounds(coord, dims):
        raise ValueError("coord must be in bounds")
    if step.axis >= len(dims):
        raise ValueError("move axis must exist in the board dimension")
    next_coord = list(coord)
    next_coord[step.axis] += step.delta
    if coord_in_bounds(tuple(next_coord), dims):
        return tuple(next_coord)
    traversal = map_boundary_exit(profile, dims=dims, coord=coord, step=step)
    if traversal is None:
        return None
    return traversal.target_coord
