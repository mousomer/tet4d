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


def neighbors_for_cell(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    validate_explorer_topology_profile(
        profile, dims=tuple(int(value) for value in dims)
    )
    edges: list[MovementEdge] = []
    for step in movement_steps_for_dimension(len(dims)):
        target = move_cell(profile, dims=dims, coord=coord, step=step)
        if target is None:
            continue
        traversal = map_boundary_exit(profile, dims=dims, coord=coord, step=step)
        edges.append(
            MovementEdge(
                step=step,
                target=target,
                traversal=traversal,
            )
        )
    return tuple(edges)


def build_movement_graph(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
) -> dict[Coord, tuple[MovementEdge, ...]]:
    validate_explorer_topology_profile(
        profile, dims=tuple(int(value) for value in dims)
    )
    graph: dict[Coord, tuple[MovementEdge, ...]] = {}
    for coord_values in product(*(range(size) for size in dims)):
        coord = tuple(int(value) for value in coord_values)
        graph[coord] = neighbors_for_cell(profile, dims=dims, coord=coord)
    return graph
