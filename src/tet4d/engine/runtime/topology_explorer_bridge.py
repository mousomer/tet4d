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


__all__ = ["explorer_profile_from_legacy_profile"]
