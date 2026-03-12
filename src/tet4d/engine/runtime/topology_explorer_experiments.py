from __future__ import annotations

from pathlib import Path

from tet4d.engine.runtime.project_config import (
    explorer_topology_experiments_file_default_path,
)
from tet4d.engine.runtime.settings_schema import write_json_object
from tet4d.engine.runtime.topology_explorer_preview import (
    compile_explorer_topology_preview,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension

_CONNECTED_COMPONENT_SCORE = 120
_DISCONNECTED_COMPONENT_PENALTY = 40
_MAX_TRAVERSAL_SCORE = 240
_GLUE_SCORE = 10
_MAX_GLUE_SCORE = 40
_WARNING_PENALTY = 20
_UNSAFE_PENALTY = 8


def _experiment_summary(
    preview: dict[str, object],
    *,
    unsafe: bool,
) -> dict[str, object]:
    graph = preview.get("movement_graph", {})
    if not isinstance(graph, dict):
        graph = {}
    glue_count = int(preview.get("glue_count", 0))
    component_count = int(graph.get("component_count", 0))
    boundary_traversal_count = int(graph.get("boundary_traversal_count", 0))
    directed_edge_count = int(graph.get("directed_edge_count", 0))
    warnings = tuple(str(item) for item in preview.get("warnings", ()))
    warning_count = len(warnings)
    recommendation_score = (
        (_CONNECTED_COMPONENT_SCORE if component_count == 1 else 0)
        - max(0, component_count - 1) * _DISCONNECTED_COMPONENT_PENALTY
        + min(boundary_traversal_count, _MAX_TRAVERSAL_SCORE)
        + min(glue_count * _GLUE_SCORE, _MAX_GLUE_SCORE)
        - warning_count * _WARNING_PENALTY
        - (_UNSAFE_PENALTY if unsafe else 0)
    )
    return {
        "glue_count": glue_count,
        "component_count": component_count,
        "boundary_traversal_count": boundary_traversal_count,
        "directed_edge_count": directed_edge_count,
        "warning_count": warning_count,
        "warnings": list(warnings),
        "recommendation_score": recommendation_score,
    }


def _experiment_entry(
    *,
    experiment_id: str,
    label: str,
    description: str,
    origin: str,
    profile: ExplorerTopologyProfile,
    dims: tuple[int, ...],
    source: str,
    unsafe: bool,
    is_current: bool,
) -> dict[str, object]:
    entry: dict[str, object] = {
        "id": experiment_id,
        "label": label,
        "description": description,
        "origin": origin,
        "unsafe": unsafe,
        "is_current": is_current,
    }
    try:
        preview = compile_explorer_topology_preview(profile, dims=dims, source=source)
    except ValueError as exc:
        entry["valid"] = False
        entry["error"] = str(exc)
        return entry
    entry["valid"] = True
    entry["preview"] = preview
    entry["summary"] = _experiment_summary(preview, unsafe=unsafe)
    return entry


def _experiment_candidates(
    current_profile: ExplorerTopologyProfile,
) -> tuple[dict[str, object], ...]:
    experiments = [
        {
            "experiment_id": "current_draft",
            "label": "Current Draft",
            "description": "Current in-memory Explorer Playground topology.",
            "origin": "current_draft",
            "profile": current_profile,
            "unsafe": False,
            "is_current": True,
        }
    ]
    seen_profiles = {current_profile}
    for preset in explorer_presets_for_dimension(current_profile.dimension):
        if preset.profile in seen_profiles:
            continue
        seen_profiles.add(preset.profile)
        experiments.append(
            {
                "experiment_id": f"preset_{preset.preset_id}",
                "label": preset.label,
                "description": preset.description,
                "origin": f"preset:{preset.preset_id}",
                "profile": preset.profile,
                "unsafe": bool(preset.unsafe),
                "is_current": False,
            }
        )
    return tuple(experiments)


def _recommendation_reason(experiment: dict[str, object]) -> str:
    summary = experiment.get("summary", {})
    if not isinstance(summary, dict):
        return "No preview summary available."
    component_count = int(summary.get("component_count", 0))
    traversal_count = int(summary.get("boundary_traversal_count", 0))
    warning_count = int(summary.get("warning_count", 0))
    parts = [
        f"{component_count} component{'s' if component_count != 1 else ''}",
        f"{traversal_count} boundary traversals",
    ]
    if warning_count == 0:
        parts.append("no warnings")
    else:
        parts.append(f"{warning_count} warning{'s' if warning_count != 1 else ''}")
    if bool(experiment.get("unsafe", False)):
        parts.append("unsafe preset")
    return ", ".join(parts)


def _recommendation_key(experiment: dict[str, object]) -> tuple[int, int, int, int]:
    summary = experiment.get("summary", {})
    if not isinstance(summary, dict):
        return (-10_000, -10_000, -10_000, -10_000)
    return (
        int(summary.get("recommendation_score", -10_000)),
        int(summary.get("boundary_traversal_count", -10_000)),
        -int(summary.get("warning_count", 10_000)),
        -int(bool(experiment.get("unsafe", False))),
    )


def compile_parallel_explorer_experiments(
    current_profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "explorer_playground",
) -> dict[str, object]:
    entries = [
        _experiment_entry(
            experiment_id=str(candidate["experiment_id"]),
            label=str(candidate["label"]),
            description=str(candidate["description"]),
            origin=str(candidate["origin"]),
            profile=candidate["profile"],
            dims=dims,
            source=source,
            unsafe=bool(candidate["unsafe"]),
            is_current=bool(candidate["is_current"]),
        )
        for candidate in _experiment_candidates(current_profile)
    ]
    valid_entries = [entry for entry in entries if bool(entry.get("valid", False))]
    recommended = None
    non_current_valid = [
        entry for entry in valid_entries if not bool(entry.get("is_current", False))
    ]
    best_entry = max(
        non_current_valid or valid_entries,
        key=_recommendation_key,
        default=None,
    )
    if best_entry is not None:
        recommended = {
            "experiment_id": best_entry["id"],
            "label": best_entry["label"],
            "origin": best_entry["origin"],
            "reason": _recommendation_reason(best_entry),
        }
    return {
        "version": 1,
        "source": str(source),
        "dimension": current_profile.dimension,
        "dims": [int(value) for value in dims],
        "experiment_count": len(entries),
        "valid_experiment_count": len(valid_entries),
        "invalid_experiment_count": len(entries) - len(valid_entries),
        "experiments": entries,
        "recommendation": recommended,
    }


def export_parallel_explorer_experiments(
    current_profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "explorer_playground",
    root_dir: Path | None = None,
) -> tuple[bool, str, Path | None]:
    payload = compile_parallel_explorer_experiments(
        current_profile,
        dims=dims,
        source=source,
    )
    destination = explorer_topology_experiments_file_default_path(root_dir=root_dir)
    try:
        write_json_object(destination, payload)
    except OSError as exc:
        return False, f"Failed exporting explorer experiment pack: {exc}", None
    return True, f"Exported explorer experiment pack to {destination}", destination


__all__ = [
    "compile_parallel_explorer_experiments",
    "export_parallel_explorer_experiments",
]
