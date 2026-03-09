from __future__ import annotations

from tet4d.engine.gameplay.topology import (
    default_edge_rules_for_mode,
    normalize_topology_mode,
)
from tet4d.engine.gameplay.topology_designer import TopologyProfileState
from tet4d.engine.runtime.topology_explorer_bridge import (
    explorer_profile_from_legacy_profile,
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


def export_explorer_preview_from_profile_state(
    profile: TopologyProfileState,
    *,
    dims: tuple[int, ...],
    source: str,
) -> tuple[bool, str, str | None]:
    explorer_profile = explorer_profile_from_legacy_profile(profile)
    return export_explorer_topology_preview(
        explorer_profile,
        dims=dims,
        source=source,
    )


__all__ = [
    "resolve_direct_explorer_launch_profile",
    "export_explorer_preview_from_profile_state",
    "export_stored_explorer_topology_preview",
    "load_runtime_explorer_topology_profile",
]
