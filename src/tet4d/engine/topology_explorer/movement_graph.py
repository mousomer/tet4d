from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Any

from ..core.model import Coord
from .glue_map import BoundaryTraversal
from .glue_model import (
    BoundaryRef,
    ExplorerTopologyProfile,
    MoveStep,
    movement_steps_for_dimension,
)
from .glue_validate import validate_explorer_topology_profile
from .transport_resolver import build_explorer_transport_resolver


@dataclass(frozen=True)
class MovementEdge:
    step: MoveStep
    target: Coord
    traversal: BoundaryTraversal | None


def _normalized_dims(dims: Coord) -> Coord:
    return tuple(int(value) for value in dims)


def _neighbors_for_validated_cell(
    resolver,
    *,
    steps: tuple[MoveStep, ...],
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    normalized_coord = tuple(int(value) for value in coord)
    edges: list[MovementEdge] = []
    for step in steps:
        step_result = resolver.resolve_cell_step(normalized_coord, step)
        if step_result.target is None:
            continue
        edges.append(
            MovementEdge(
                step=step,
                target=step_result.target,
                traversal=step_result.traversal,
            )
        )
    return tuple(edges)


def _boundary_ref_for_exit(
    dims: Coord,
    *,
    coord: Coord,
    step: MoveStep,
) -> BoundaryRef | None:
    axis = int(step.axis)
    delta = int(step.delta)
    axis_value = int(coord[axis])
    if delta < 0:
        if axis_value != 0:
            return None
        return BoundaryRef(dimension=len(dims), axis=axis, side="-")
    if axis_value != int(dims[axis]) - 1:
        return None
    return BoundaryRef(dimension=len(dims), axis=axis, side="+")


def _graph_edges_for_cell(
    resolver,
    *,
    dims: Coord,
    steps: tuple[MoveStep, ...],
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    edges: list[MovementEdge] = []
    for step in steps:
        axis = int(step.axis)
        delta = int(step.delta)
        next_axis_value = int(coord[axis]) + delta
        if 0 <= next_axis_value < int(dims[axis]):
            target = list(coord)
            target[axis] = next_axis_value
            edges.append(
                MovementEdge(
                    step=step,
                    target=tuple(int(value) for value in target),
                    traversal=None,
                )
            )
            continue
        boundary = _boundary_ref_for_exit(dims, coord=coord, step=step)
        if boundary is None:
            continue
        seam = resolver.seam_for_boundary(boundary)
        if seam is None:
            continue
        target_coord = seam.target_for_source_coord(coord)
        edges.append(
            MovementEdge(
                step=step,
                target=target_coord,
                traversal=BoundaryTraversal(
                    glue_id=seam.glue_id,
                    source_boundary=seam.source_boundary,
                    target_boundary=seam.target_boundary,
                    source_coord=coord,
                    target_coord=target_coord,
                    exit_step=step,
                    entry_step=seam.entry_step,
                ),
            )
        )
    return tuple(edges)


@lru_cache(maxsize=32)
def _build_movement_graph_rows(
    profile: ExplorerTopologyProfile,
    dims: Coord,
) -> tuple[tuple[Coord, tuple[MovementEdge, ...]], ...]:
    validated_profile = validate_explorer_topology_profile(
        profile,
        dims=dims,
    )
    resolver = build_explorer_transport_resolver(validated_profile, dims)
    steps = tuple(movement_steps_for_dimension(validated_profile.dimension))
    rows: list[tuple[Coord, tuple[MovementEdge, ...]]] = []
    for coord_values in product(*(range(size) for size in dims)):
        coord = tuple(int(value) for value in coord_values)
        rows.append(
            (
                coord,
                _graph_edges_for_cell(
                    resolver,
                    dims=dims,
                    steps=steps,
                    coord=coord,
                ),
            )
        )
    return tuple(rows)


def movement_graph_rows(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
) -> tuple[tuple[Coord, tuple[MovementEdge, ...]], ...]:
    return _build_movement_graph_rows(profile, _normalized_dims(dims))


def movement_graph_from_rows(
    rows: tuple[tuple[Coord, tuple[MovementEdge, ...]], ...],
) -> dict[Coord, tuple[MovementEdge, ...]]:
    return dict(rows)


def serialize_movement_graph_rows(
    rows: tuple[tuple[Coord, tuple[MovementEdge, ...]], ...],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for coord, edges in rows:
        payload.append(
            {
                "coord": [int(value) for value in coord],
                "edges": [
                    {
                        "step": edge.step.label,
                        "target": [int(value) for value in edge.target],
                        "traversal": (
                            None
                            if edge.traversal is None
                            else {
                                "glue_id": edge.traversal.glue_id,
                                "source_boundary": {
                                    "axis": int(edge.traversal.source_boundary.axis),
                                    "side": str(edge.traversal.source_boundary.side),
                                },
                                "target_boundary": {
                                    "axis": int(edge.traversal.target_boundary.axis),
                                    "side": str(edge.traversal.target_boundary.side),
                                },
                                "source_coord": [
                                    int(value)
                                    for value in edge.traversal.source_coord
                                ],
                                "target_coord": [
                                    int(value)
                                    for value in edge.traversal.target_coord
                                ],
                                "entry_step": edge.traversal.entry_step.label,
                            }
                        ),
                    }
                    for edge in edges
                ],
            }
        )
    return payload


def _deserialize_boundary_ref(
    payload: object,
    *,
    dimension: int,
) -> BoundaryRef | None:
    if not isinstance(payload, dict):
        return None
    try:
        return BoundaryRef(
            dimension=int(dimension),
            axis=int(payload["axis"]),
            side=str(payload["side"]),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _deserialize_movement_edge(
    payload: object,
    *,
    dimension: int,
    step_by_label: dict[str, MoveStep],
) -> MovementEdge | None:
    if not isinstance(payload, dict):
        return None
    step = step_by_label.get(str(payload.get("step", "")))
    if step is None:
        return None
    try:
        target = tuple(int(value) for value in payload.get("target", ()))
    except (TypeError, ValueError):
        return None
    traversal_payload = payload.get("traversal")
    if traversal_payload is None:
        return MovementEdge(step=step, target=target, traversal=None)
    if not isinstance(traversal_payload, dict):
        return None
    source_boundary = _deserialize_boundary_ref(
        traversal_payload.get("source_boundary"),
        dimension=dimension,
    )
    target_boundary = _deserialize_boundary_ref(
        traversal_payload.get("target_boundary"),
        dimension=dimension,
    )
    entry_step = step_by_label.get(str(traversal_payload.get("entry_step", "")))
    if source_boundary is None or target_boundary is None or entry_step is None:
        return None
    try:
        traversal = BoundaryTraversal(
            glue_id=str(traversal_payload["glue_id"]),
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            source_coord=tuple(
                int(value) for value in traversal_payload.get("source_coord", ())
            ),
            target_coord=tuple(
                int(value) for value in traversal_payload.get("target_coord", ())
            ),
            exit_step=step,
            entry_step=entry_step,
        )
    except (KeyError, TypeError, ValueError):
        return None
    return MovementEdge(
        step=step,
        target=target,
        traversal=traversal,
    )


def deserialize_movement_graph_rows(
    payload: object,
    *,
    dimension: int,
) -> tuple[tuple[Coord, tuple[MovementEdge, ...]], ...] | None:
    if not isinstance(payload, list):
        return None
    step_by_label = {
        step.label: step for step in movement_steps_for_dimension(int(dimension))
    }
    rows: list[tuple[Coord, tuple[MovementEdge, ...]]] = []
    for row_payload in payload:
        if not isinstance(row_payload, dict):
            return None
        try:
            coord = tuple(int(value) for value in row_payload.get("coord", ()))
        except (TypeError, ValueError):
            return None
        edges_payload = row_payload.get("edges", ())
        if not isinstance(edges_payload, list):
            return None
        edges: list[MovementEdge] = []
        for edge_payload in edges_payload:
            edge = _deserialize_movement_edge(
                edge_payload,
                dimension=int(dimension),
                step_by_label=step_by_label,
            )
            if edge is None:
                return None
            edges.append(edge)
        rows.append((coord, tuple(edges)))
    return tuple(rows)


def neighbors_for_cell(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
    coord: Coord,
) -> tuple[MovementEdge, ...]:
    normalized_dims = _normalized_dims(dims)
    validated_profile = validate_explorer_topology_profile(
        profile,
        dims=normalized_dims,
    )
    resolver = build_explorer_transport_resolver(validated_profile, normalized_dims)
    return _neighbors_for_validated_cell(
        resolver,
        steps=tuple(movement_steps_for_dimension(validated_profile.dimension)),
        coord=coord,
    )


def build_movement_graph(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
) -> dict[Coord, tuple[MovementEdge, ...]]:
    normalized_dims = _normalized_dims(dims)
    return movement_graph_from_rows(_build_movement_graph_rows(profile, normalized_dims))
