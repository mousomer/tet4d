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
    axis_name,
    boundary_label,
)
from tet4d.engine.topology_explorer.movement_graph import build_movement_graph


def preview_dims_for_dimension(dimension: int) -> tuple[int, ...]:
    return configured_preview_dims(dimension)


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
    graph = build_movement_graph(profile, dims=dims)
    degree_histogram = Counter(len(edges) for edges in graph.values())
    traversal_count = sum(
        1 for edges in graph.values() for edge in edges if edge.traversal is not None
    )
    component_count = _component_count(graph)
    return {
        "version": 1,
        "source": str(source),
        "dimension": profile.dimension,
        "dims": [int(value) for value in dims],
        "glue_count": len(profile.gluings),
        "gluings": _glue_payload(profile),
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


def export_explorer_topology_preview(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "stored_profile",
    root_dir: Path | None = None,
) -> tuple[bool, str, Path | None]:
    payload = compile_explorer_topology_preview(profile, dims=dims, source=source)
    destination = explorer_topology_preview_file_default_path(root_dir=root_dir)
    try:
        write_json_object(destination, payload)
    except OSError as exc:
        return False, f"Failed exporting explorer topology preview: {exc}", None
    return True, f"Exported explorer topology preview to {destination}", destination


__all__ = [
    "compile_explorer_topology_preview",
    "export_explorer_topology_preview",
    "preview_dims_for_dimension",
]
