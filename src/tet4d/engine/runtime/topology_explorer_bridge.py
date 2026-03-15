from __future__ import annotations

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_INVERT, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
)
from tet4d.engine.topology_explorer import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    export_explorer_topology_preview,
)


def explorer_profile_from_legacy_profile(
    profile: TopologyProfileState,
) -> ExplorerTopologyProfile:
    if profile.gameplay_mode != GAMEPLAY_MODE_EXPLORER:
        raise ValueError("legacy bridge supports Explorer Mode profiles only")

    gluings: list[GluingDescriptor] = []
    tangent_dimension = profile.dimension - 1
    permutation = tuple(range(tangent_dimension))

    for axis, axis_rule in enumerate(profile.edge_rules):
        neg, pos = axis_rule
        if neg == EDGE_BOUNDED and pos == EDGE_BOUNDED:
            continue
        if neg != pos:
            raise ValueError(
                f"{AXIS_NAMES[axis]} boundaries use asymmetric edge rules and cannot be represented as one explorer gluing"
            )
        if neg not in {EDGE_WRAP, EDGE_INVERT}:
            raise ValueError(
                f"{AXIS_NAMES[axis]} boundaries use unsupported edge behavior {neg!r}"
            )
        signs = tuple(1 if neg == EDGE_WRAP else -1 for _ in range(tangent_dimension))
        gluings.append(
            GluingDescriptor(
                glue_id=f"legacy_{AXIS_NAMES[axis]}_{neg}",
                source=BoundaryRef(profile.dimension, axis, "-"),
                target=BoundaryRef(profile.dimension, axis, "+"),
                transform=BoundaryTransform(permutation=permutation, signs=signs),
            )
        )

    return ExplorerTopologyProfile(dimension=profile.dimension, gluings=tuple(gluings))


def explorer_profile_from_edge_rules(
    *,
    dimension: int,
    topology_mode: str,
    edge_rules: tuple[tuple[str, str], ...],
) -> ExplorerTopologyProfile:
    return explorer_profile_from_legacy_profile(
        TopologyProfileState(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=int(dimension),
            topology_mode=str(topology_mode),
            edge_rules=tuple((str(neg), str(pos)) for neg, pos in edge_rules),
        )
    )


def export_explorer_preview_from_legacy_profile(
    profile: TopologyProfileState,
    *,
    dims: tuple[int, ...],
    source: str,
) -> tuple[bool, str, str | None]:
    return export_explorer_topology_preview(
        explorer_profile_from_legacy_profile(profile),
        dims=dims,
        source=source,
    )


__all__ = [
    "explorer_profile_from_edge_rules",
    "explorer_profile_from_legacy_profile",
    "export_explorer_preview_from_legacy_profile",
]
