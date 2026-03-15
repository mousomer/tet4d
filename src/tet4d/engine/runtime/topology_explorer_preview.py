from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

from tet4d.engine.runtime.project_config import (
    explorer_topology_preview_dims as configured_preview_dims,
    explorer_topology_preview_file_default_path,
)
from tet4d.engine.runtime.settings_schema import write_json_object
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
    MoveStep,
    axis_name,
    boundary_label,
    movement_steps_for_dimension,
    tangent_axes_for_boundary,
    validate_explorer_topology_profile,
)
from tet4d.engine.topology_explorer.movement_graph import build_movement_graph
from tet4d.engine.topology_explorer.transport_resolver import (
    CellStepResult,
    build_explorer_transport_resolver,
)
from tet4d.engine.runtime.topology_explorer_audit import record_active_interaction_phase


def preview_dims_for_dimension(dimension: int) -> tuple[int, ...]:
    return configured_preview_dims(dimension)


def recommended_explorer_probe_coord(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
) -> tuple[int, ...]:
    normalized_dims = tuple(int(value) for value in dims)
    validate_explorer_topology_profile(profile, dims=normalized_dims)
    return tuple(max(0, size // 2) for size in normalized_dims)


def _identity_probe_frame(dimension: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(range(dimension)), tuple(1 for _ in range(dimension))


def _normalize_probe_frame(
    dimension: int,
    *,
    permutation: tuple[int, ...] | None,
    signs: tuple[int, ...] | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    default_permutation, default_signs = _identity_probe_frame(dimension)
    normalized_permutation = (
        default_permutation
        if permutation is None
        else tuple(int(value) for value in permutation)
    )
    normalized_signs = (
        default_signs if signs is None else tuple(int(value) for value in signs)
    )
    if len(normalized_permutation) != dimension:
        normalized_permutation = default_permutation
    if len(normalized_signs) != dimension:
        normalized_signs = default_signs
    if tuple(sorted(normalized_permutation)) != tuple(range(dimension)):
        normalized_permutation = default_permutation
    if any(value not in (-1, 1) for value in normalized_signs):
        normalized_signs = default_signs
    return normalized_permutation, normalized_signs


def _step_in_probe_frame(
    step: MoveStep,
    *,
    permutation: tuple[int, ...],
    signs: tuple[int, ...],
) -> MoveStep:
    axis = int(step.axis)
    return MoveStep(
        axis=int(permutation[axis]),
        delta=int(step.delta) * int(signs[axis]),
    )


def _compose_probe_frame(
    *,
    dimension: int,
    permutation: tuple[int, ...],
    signs: tuple[int, ...],
    frame_transform,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if frame_transform is None or frame_transform.is_identity_linear():
        return permutation, signs
    composed_permutation = [0] * dimension
    composed_signs = [1] * dimension
    for source_axis, intermediate_axis in enumerate(permutation):
        target_axis = int(frame_transform.permutation[intermediate_axis])
        composed_permutation[source_axis] = target_axis
        composed_signs[source_axis] = (
            int(signs[source_axis])
            * int(frame_transform.signs[intermediate_axis])
        )
    return tuple(composed_permutation), tuple(composed_signs)


def _probe_frame_payload(
    permutation: tuple[int, ...],
    signs: tuple[int, ...],
) -> dict[str, object]:
    return {
        'frame_permutation': list(permutation),
        'frame_signs': list(signs),
    }


def _traversal_payload(step_result: CellStepResult) -> dict[str, object] | None:
    traversal = step_result.traversal
    if traversal is None:
        return None
    return {
        "glue_id": traversal.glue_id,
        "source_boundary": boundary_label(traversal.source_boundary),
        "target_boundary": boundary_label(traversal.target_boundary),
    }


def explorer_probe_options(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    coord: tuple[int, ...],
    frame_permutation: tuple[int, ...] | None = None,
    frame_signs: tuple[int, ...] | None = None,
) -> list[dict[str, object]]:
    resolver = build_explorer_transport_resolver(profile, dims)
    normalized_permutation, normalized_signs = _normalize_probe_frame(
        profile.dimension,
        permutation=frame_permutation,
        signs=frame_signs,
    )
    options: list[dict[str, object]] = []
    for step in movement_steps_for_dimension(profile.dimension):
        world_step = _step_in_probe_frame(
            step,
            permutation=normalized_permutation,
            signs=normalized_signs,
        )
        step_result = resolver.resolve_cell_step(coord, world_step)
        options.append(
            {
                "step": step.label,
                "blocked": step_result.target is None,
                "target": None
                if step_result.target is None
                else list(step_result.target),
                "traversal": _traversal_payload(step_result),
            }
        )
    return options


def advance_explorer_probe(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    coord: tuple[int, ...],
    step_label: str,
    frame_permutation: tuple[int, ...] | None = None,
    frame_signs: tuple[int, ...] | None = None,
) -> tuple[tuple[int, ...], dict[str, object]]:
    normalized_permutation, normalized_signs = _normalize_probe_frame(
        profile.dimension,
        permutation=frame_permutation,
        signs=frame_signs,
    )
    step = next(
        (
            item
            for item in movement_steps_for_dimension(profile.dimension)
            if item.label == step_label
        ),
        None,
    )
    if step is None:
        raise ValueError(f"unknown probe step: {step_label}")

    world_step = _step_in_probe_frame(
        step,
        permutation=normalized_permutation,
        signs=normalized_signs,
    )
    step_result = build_explorer_transport_resolver(profile, dims).resolve_cell_step(
        coord,
        world_step,
    )
    next_permutation, next_signs = _compose_probe_frame(
        dimension=profile.dimension,
        permutation=normalized_permutation,
        signs=normalized_signs,
        frame_transform=step_result.frame_transform,
    )
    if step_result.target is None:
        return coord, {
            "step": step_label,
            "blocked": True,
            "message": f"{step_label} blocked at {list(coord)}",
            "traversal": None,
            **_probe_frame_payload(next_permutation, next_signs),
        }
    if step_result.traversal is None:
        return step_result.target, {
            "step": step_label,
            "blocked": False,
            "message": f"{step_label}: {list(coord)} -> {list(step_result.target)}",
            "traversal": None,
            **_probe_frame_payload(next_permutation, next_signs),
        }
    traversal = step_result.traversal
    return step_result.target, {
        "step": step_label,
        "blocked": False,
        "message": (
            f"{step_label}: {boundary_label(traversal.source_boundary)} -> "
            f"{boundary_label(traversal.target_boundary)} to {list(step_result.target)}"
        ),
        "traversal": _traversal_payload(step_result),
        **_probe_frame_payload(next_permutation, next_signs),
    }


def _glue_payload(profile: ExplorerTopologyProfile) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for glue in profile.gluings:
        rows.append(
            {
                "id": glue.glue_id,
                "enabled": glue.enabled,
                "source": boundary_label(glue.source),
                "target": boundary_label(glue.target),
                "permutation": list(glue.transform.permutation),
                "signs": list(glue.transform.signs),
            }
        )
    return rows


def _signed_axis_label(axis: int, sign: int) -> str:
    prefix = "+" if int(sign) > 0 else "-"
    return f"{prefix}{axis_name(axis)}"


def _basis_arrow_payload(profile: ExplorerTopologyProfile) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for glue in profile.gluings:
        source_axes = tangent_axes_for_boundary(glue.source)
        target_axes = tangent_axes_for_boundary(glue.target)
        source_basis = [_signed_axis_label(axis, 1) for axis in source_axes]
        target_basis: list[str] = []
        for source_index, target_index in enumerate(glue.transform.permutation):
            target_basis.append(
                _signed_axis_label(
                    target_axes[target_index],
                    glue.transform.signs[source_index],
                )
            )
        rows.append(
            {
                "id": glue.glue_id,
                "crossing": (
                    f"{boundary_label(glue.source)} -> {boundary_label(glue.target)}"
                ),
                "source_boundary": boundary_label(glue.source),
                "target_boundary": boundary_label(glue.target),
                "source_basis": source_basis,
                "target_basis": target_basis,
                "basis_pairs": [
                    {"from": source_basis[index], "to": target_basis[index]}
                    for index in range(len(source_basis))
                ],
            }
        )
    return rows


def _component_count(graph: dict[tuple[int, ...], tuple[object, ...]]) -> int:
    remaining = set(graph)
    components = 0
    while remaining:
        components += 1
        start = remaining.pop()
        queue = deque([start])
        while queue:
            node = queue.popleft()
            for edge in graph.get(node, ()):
                target = edge.target
                if target in remaining:
                    remaining.remove(target)
                    queue.append(target)
    return components


def _preview_warnings(
    profile: ExplorerTopologyProfile,
    *,
    component_count: int,
) -> list[str]:
    warnings: list[str] = []
    if component_count > 1:
        warnings.append(
            f"Movement graph has {component_count} disconnected components."
        )
    if any(any(sign < 0 for sign in glue.transform.signs) for glue in profile.gluings):
        warnings.append("Contains orientation-reversing seam transforms.")
    if any(glue.source.axis != glue.target.axis for glue in profile.gluings):
        warnings.append("Contains cross-axis seam pairings.")
    return warnings


def _sample_traversals(
    graph: dict[tuple[int, ...], tuple[object, ...]],
    *,
    limit: int = 8,
) -> list[dict[str, object]]:
    samples: list[dict[str, object]] = []
    for coord, edges in graph.items():
        for edge in edges:
            traversal = edge.traversal
            if traversal is None:
                continue
            samples.append(
                {
                    "from": list(coord),
                    "to": list(edge.target),
                    "step": traversal.exit_step.label,
                    "source_boundary": boundary_label(traversal.source_boundary),
                    "target_boundary": boundary_label(traversal.target_boundary),
                }
            )
            if len(samples) >= limit:
                return samples
    return samples


def compile_explorer_topology_preview(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "stored_profile",
) -> dict[str, object]:
    with record_active_interaction_phase(
        "preview_compile",
        dimension=profile.dimension,
        dims=tuple(int(value) for value in dims),
        glue_count=len(profile.gluings),
        source=source,
    ):
        graph = build_movement_graph(profile, dims=dims)
        degree_histogram = Counter(len(edges) for edges in graph.values())
        traversal_count = sum(
            1
            for edges in graph.values()
            for edge in edges
            if edge.traversal is not None
        )
        component_count = _component_count(graph)
        return {
            "version": 1,
            "source": str(source),
            "dimension": profile.dimension,
            "dims": [int(value) for value in dims],
            "glue_count": len(profile.gluings),
            "gluings": _glue_payload(profile),
            "basis_arrows": _basis_arrow_payload(profile),
            "movement_graph": {
                "cell_count": len(graph),
                "directed_edge_count": sum(len(edges) for edges in graph.values()),
                "boundary_traversal_count": traversal_count,
                "component_count": component_count,
                "degree_histogram": {
                    str(key): count for key, count in sorted(degree_histogram.items())
                },
                "origin": [0 for _ in dims],
            },
            "sample_boundary_traversals": _sample_traversals(graph),
            "warnings": _preview_warnings(profile, component_count=component_count),
            "axes": [axis_name(index) for index in range(profile.dimension)],
        }


def _preview_payload_for_export(
    payload: dict[str, object],
    *,
    source: str,
) -> dict[str, object]:
    export_payload = dict(payload)
    export_payload["source"] = str(source)
    return export_payload


def export_explorer_topology_preview(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "stored_profile",
    root_dir: Path | None = None,
    preview_payload: dict[str, object] | None = None,
) -> tuple[bool, str, Path | None]:
    payload = (
        _preview_payload_for_export(preview_payload, source=source)
        if preview_payload is not None
        else compile_explorer_topology_preview(profile, dims=dims, source=source)
    )
    destination = explorer_topology_preview_file_default_path(root_dir=root_dir)
    try:
        write_json_object(destination, payload)
    except OSError as exc:
        return False, f"Failed exporting explorer topology preview: {exc}", None
    return True, f"Exported explorer topology preview to {destination}", destination


__all__ = [
    "advance_explorer_probe",
    "compile_explorer_topology_preview",
    "explorer_probe_options",
    "recommended_explorer_probe_coord",
    "export_explorer_topology_preview",
    "preview_dims_for_dimension",
]
