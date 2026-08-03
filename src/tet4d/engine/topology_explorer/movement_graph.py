from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Any

from ..core.model import Coord
from .contract_validation import (
    require_json_array,
    require_json_int_sequence,
    require_json_object,
    require_json_string,
)
from .domain_validation import require_integral_sequence
from .glue_map import BoundaryTraversal
from .glue_model import (
    BoundaryRef,
    ExplorerTopologyProfile,
    MoveStep,
    movement_steps_for_dimension,
)
from .glue_validate import validate_explorer_topology_profile
from .transport_resolver import build_explorer_transport_resolver

MOVEMENT_GRAPH_ALGORITHM_VERSION = 1


@dataclass(frozen=True)
class MovementEdge:
    step: MoveStep
    target: Coord
    traversal: BoundaryTraversal | None


def _normalized_dims(dims: Coord) -> Coord:
    return require_integral_sequence(dims, "movement graph dimensions")


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
    *,
    dims: Coord,
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for coord, edges in rows:
        payload.append(
            {
                "coord": list(coord),
                "edges": [
                    {
                        "step": edge.step.label,
                        "target": list(edge.target),
                        "traversal": (
                            None
                            if edge.traversal is None
                            else {
                                "glue_id": edge.traversal.glue_id,
                                "source_boundary": {
                                    "axis": edge.traversal.source_boundary.axis,
                                    "side": edge.traversal.source_boundary.side,
                                },
                                "target_boundary": {
                                    "axis": edge.traversal.target_boundary.axis,
                                    "side": edge.traversal.target_boundary.side,
                                },
                                "source_coord": list(edge.traversal.source_coord),
                                "target_coord": list(edge.traversal.target_coord),
                                "entry_step": edge.traversal.entry_step.label,
                            }
                        ),
                    }
                    for edge in edges
                ],
            }
        )
    if deserialize_movement_graph_rows(payload, dims=dims) is None:
        raise ValueError("movement graph rows do not satisfy the strict cache format")
    return payload


def _deserialize_boundary_ref(
    payload: object,
    *,
    dimension: int,
) -> BoundaryRef:
    boundary = require_json_object(payload, "cache.boundary")
    if set(boundary) != {"axis", "side"}:
        raise ValueError("cache boundary fields must be exactly axis and side")
    axis = require_json_int_sequence(
        [boundary["axis"]],
        "cache.boundary.axis",
        minimum=0,
        maximum=dimension - 1,
    )[0]
    return BoundaryRef(
        dimension=dimension,
        axis=axis,
        side=require_json_string(boundary["side"], "cache.boundary.side"),
    )


def _deserialize_coord(payload: object, *, dims: Coord, path: str) -> Coord:
    coord = require_json_int_sequence(payload, path)
    if len(coord) != len(dims):
        raise ValueError(f"{path} rank must match cache dimensions")
    if any(value < 0 or value >= dims[axis] for axis, value in enumerate(coord)):
        raise ValueError(f"{path} must be within cache dimensions")
    return coord


def _require_exact_fields(
    payload: dict[str, object],
    expected: set[str],
    *,
    path: str,
) -> None:
    if set(payload) != expected:
        raise ValueError(f"{path} fields must be exactly {', '.join(sorted(expected))}")


def _deserialize_movement_edge(
    payload: object,
    *,
    dims: Coord,
    source_coord: Coord,
    step_by_label: dict[str, MoveStep],
) -> MovementEdge:
    edge_payload = require_json_object(payload, "cache.edge")
    _require_exact_fields(
        edge_payload,
        {"step", "target", "traversal"},
        path="cache.edge",
    )
    step_label = require_json_string(edge_payload["step"], "cache.edge.step")
    step = step_by_label.get(step_label)
    if step is None:
        raise ValueError(f"cache.edge.step is unsupported: {step_label!r}")
    target = _deserialize_coord(
        edge_payload["target"],
        dims=dims,
        path="cache.edge.target",
    )
    traversal_payload = edge_payload["traversal"]
    if traversal_payload is None:
        expected_target = list(source_coord)
        expected_target[step.axis] += step.delta
        if tuple(expected_target) != target:
            raise ValueError("non-traversal cache edge must be one unit movement")
        return MovementEdge(step=step, target=target, traversal=None)
    traversal_obj = require_json_object(traversal_payload, "cache.edge.traversal")
    _require_exact_fields(
        traversal_obj,
        {
            "glue_id",
            "source_boundary",
            "target_boundary",
            "source_coord",
            "target_coord",
            "entry_step",
        },
        path="cache.edge.traversal",
    )
    source_boundary = _deserialize_boundary_ref(
        traversal_obj["source_boundary"],
        dimension=len(dims),
    )
    target_boundary = _deserialize_boundary_ref(
        traversal_obj["target_boundary"],
        dimension=len(dims),
    )
    entry_step_label = require_json_string(
        traversal_obj["entry_step"],
        "cache.edge.traversal.entry_step",
    )
    entry_step = step_by_label.get(entry_step_label)
    if entry_step is None:
        raise ValueError("cache traversal entry step is unsupported")
    traversal_source = _deserialize_coord(
        traversal_obj["source_coord"],
        dims=dims,
        path="cache.edge.traversal.source_coord",
    )
    traversal_target = _deserialize_coord(
        traversal_obj["target_coord"],
        dims=dims,
        path="cache.edge.traversal.target_coord",
    )
    expected_source_boundary = _boundary_ref_for_exit(
        dims,
        coord=source_coord,
        step=step,
    )
    if expected_source_boundary != source_boundary:
        raise ValueError("cache traversal source boundary does not match its exit")
    if traversal_source != source_coord or traversal_target != target:
        raise ValueError("cache traversal coordinates must match their edge")
    expected_entry_delta = 1 if target_boundary.side == "-" else -1
    if entry_step != MoveStep(axis=target_boundary.axis, delta=expected_entry_delta):
        raise ValueError("cache traversal entry step must point inward")
    expected_target_axis_value = (
        0 if target_boundary.side == "-" else dims[target_boundary.axis] - 1
    )
    if target[target_boundary.axis] != expected_target_axis_value:
        raise ValueError("cache traversal target must lie on its target boundary")
    glue_id = require_json_string(
        traversal_obj["glue_id"],
        "cache.edge.traversal.glue_id",
    ).strip()
    if not glue_id:
        raise ValueError("cache traversal glue_id must be non-empty")
    traversal = BoundaryTraversal(
        glue_id=glue_id,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        source_coord=traversal_source,
        target_coord=traversal_target,
        exit_step=step,
        entry_step=entry_step,
    )
    return MovementEdge(
        step=step,
        target=target,
        traversal=traversal,
    )


def deserialize_movement_graph_rows(
    payload: object,
    *,
    dims: Coord,
) -> tuple[tuple[Coord, tuple[MovementEdge, ...]], ...] | None:
    try:
        normalized_dims = require_integral_sequence(dims, "cache dims")
        if len(normalized_dims) < 2 or any(value <= 0 for value in normalized_dims):
            raise ValueError("cache dimensions must be positive and have rank >= 2")
        rows_payload = require_json_array(payload, "cache.graph_rows")
        steps = movement_steps_for_dimension(len(normalized_dims))
        step_by_label = {step.label: step for step in steps}
        rows: list[tuple[Coord, tuple[MovementEdge, ...]]] = []
        seen_coords: set[Coord] = set()
        for row_index, row_raw in enumerate(rows_payload):
            row_path = f"cache.graph_rows[{row_index}]"
            row_payload = require_json_object(row_raw, row_path)
            _require_exact_fields(row_payload, {"coord", "edges"}, path=row_path)
            coord = _deserialize_coord(
                row_payload["coord"],
                dims=normalized_dims,
                path=f"{row_path}.coord",
            )
            if coord in seen_coords:
                raise ValueError("cache graph coordinates must be unique")
            seen_coords.add(coord)
            edges_payload = require_json_array(
                row_payload["edges"], f"{row_path}.edges"
            )
            edges = tuple(
                _deserialize_movement_edge(
                    edge_payload,
                    dims=normalized_dims,
                    source_coord=coord,
                    step_by_label=step_by_label,
                )
                for edge_payload in edges_payload
            )
            edge_steps = tuple(edge.step for edge in edges)
            if len(set(edge_steps)) != len(edge_steps):
                raise ValueError("cache graph contains duplicate moves for one cell")
            if edge_steps != tuple(step for step in steps if step in edge_steps):
                raise ValueError("cache graph movement edges must use canonical order")
            for step in steps:
                neighbor = list(coord)
                neighbor[step.axis] += step.delta
                if (
                    0 <= neighbor[step.axis] < normalized_dims[step.axis]
                    and step not in edge_steps
                ):
                    raise ValueError("cache graph omits an in-bounds movement edge")
            rows.append((coord, edges))
        expected_coords = tuple(product(*(range(size) for size in normalized_dims)))
        if tuple(coord for coord, _ in rows) != expected_coords:
            raise ValueError(
                "cache graph must contain every board coordinate exactly once"
            )
        return tuple(rows)
    except (KeyError, TypeError, ValueError):
        return None


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
    return movement_graph_from_rows(
        _build_movement_graph_rows(profile, normalized_dims)
    )
