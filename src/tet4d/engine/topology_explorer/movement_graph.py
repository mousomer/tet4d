from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from ..core.model import Coord
from .glue_map import BoundaryTraversal, map_boundary_exit, move_cell
from .glue_model import ExplorerTopologyProfile, MoveStep, movement_steps_for_dimension
from .glue_validate import validate_explorer_topology_profile


@dataclass(frozen=True)
class MovementEdge:
    step: MoveStep
    target: Coord
    traversal: BoundaryTraversal | None


def _normalized_dims(dims: Coord) -> Coord:
    return tuple(int(value) for value in dims)


def _neighbors_for_validated_cell(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    normalized_dims = _normalized_dims(dims)
    normalized_coord = tuple(int(value) for value in coord)
    edges: list[MovementEdge] = []
    for step in movement_steps_for_dimension(profile.dimension):
        target = move_cell(profile, dims=normalized_dims, coord=normalized_coord, step=step)
        if target is None:
            continue
        traversal = map_boundary_exit(
            profile,
            dims=normalized_dims,
            coord=normalized_coord,
            step=step,
        )
        edges.append(
            MovementEdge(
                step=step,
                target=target,
                traversal=traversal,
            )
        )
    return tuple(edges)


def neighbors_for_cell(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    normalized_dims = _normalized_dims(dims)
    validate_explorer_topology_profile(profile, dims=normalized_dims)
    return _neighbors_for_validated_cell(profile, dims=normalized_dims, coord=coord)


def build_movement_graph(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
) -> dict[Coord, tuple[MovementEdge, ...]]:
    normalized_dims = _normalized_dims(dims)
    validate_explorer_topology_profile(profile, dims=normalized_dims)
    graph: dict[Coord, tuple[MovementEdge, ...]] = {}
    for coord_values in product(*(range(size) for size in normalized_dims)):
        coord = tuple(int(value) for value in coord_values)
        graph[coord] = _neighbors_for_validated_cell(
            profile,
            dims=normalized_dims,
            coord=coord,
        )
    return graph
