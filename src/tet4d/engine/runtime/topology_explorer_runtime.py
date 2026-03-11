from __future__ import annotations

from tet4d.engine.gameplay.topology import (
    default_edge_rules_for_mode,
    normalize_topology_mode,
)
from tet4d.engine.runtime.topology_explorer_experiments import (
    compile_parallel_explorer_experiments,
    export_parallel_explorer_experiments,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    export_explorer_topology_preview,
    preview_dims_for_dimension,
)
from tet4d.engine.runtime.topology_explorer_store import load_explorer_topology_profile
from tet4d.engine.topology_explorer import ExplorerTopologyProfile


def resolve_direct_explorer_launch_profile(
    *,
    dimension: int,
    gravity_axis: int,
    topology_mode: str,
    explorer_topology_profile_override: ExplorerTopologyProfile | None = None,
) -> tuple[str, tuple[tuple[str, str], ...], ExplorerTopologyProfile]:
    resolved_mode = normalize_topology_mode(topology_mode)
    topology_edge_rules = default_edge_rules_for_mode(
        int(dimension),
        int(gravity_axis),
        mode=resolved_mode,
    )
    explorer_profile = (
        explorer_topology_profile_override
        if explorer_topology_profile_override is not None
        else load_runtime_explorer_topology_profile(dimension)
    )
    return resolved_mode, topology_edge_rules, explorer_profile


def load_runtime_explorer_topology_profile(dimension: int) -> ExplorerTopologyProfile:
    return load_explorer_topology_profile(dimension)


def export_stored_explorer_topology_preview(
    dimension: int,
    *,
    source: str = "stored_profile",
) -> tuple[bool, str, str | None]:
    return export_explorer_topology_preview(
        load_runtime_explorer_topology_profile(dimension),
        dims=preview_dims_for_dimension(dimension),
        source=source,
    )


def compile_runtime_explorer_experiments(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "explorer_playground",
) -> dict[str, object]:
    return compile_parallel_explorer_experiments(
        profile,
        dims=dims,
        source=source,
    )


def export_runtime_explorer_experiments(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
    source: str = "explorer_playground",
) -> tuple[bool, str, str | None]:
    return export_parallel_explorer_experiments(
        profile,
        dims=dims,
        source=source,
    )


__all__ = [
    "resolve_direct_explorer_launch_profile",
    "export_stored_explorer_topology_preview",
    "compile_runtime_explorer_experiments",
    "export_runtime_explorer_experiments",
    "load_runtime_explorer_topology_profile",
]
