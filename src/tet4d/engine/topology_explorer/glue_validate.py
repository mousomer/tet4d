from __future__ import annotations

from .glue_model import (
    BoundaryRef,
    ExplorerTopologyProfile,
    GluingDescriptor,
    normalize_dimension,
    tangent_axes_for_boundary,
)


def _boundary_extents(dims: tuple[int, ...], boundary: BoundaryRef) -> tuple[int, ...]:
    tangent_axes = tangent_axes_for_boundary(boundary)
    return tuple(int(dims[axis]) for axis in tangent_axes)


def _validate_dims(dims: tuple[int, ...], dimension: int) -> tuple[int, ...]:
    if len(dims) != dimension:
        raise ValueError("dims length must match profile dimension")
    normalized = tuple(int(size) for size in dims)
    if any(size <= 0 for size in normalized):
        raise ValueError("all dimension sizes must be positive")
    return normalized


def _validate_boundary_ownership(gluings: tuple[GluingDescriptor, ...]) -> None:
    seen: set[BoundaryRef] = set()
    for glue in gluings:
        if glue.source in seen:
            raise ValueError(f"boundary {glue.source.label} is already owned by another gluing")
        if glue.target in seen:
            raise ValueError(f"boundary {glue.target.label} is already owned by another gluing")
        seen.add(glue.source)
        seen.add(glue.target)


def _validate_extent_compatibility(
    dims: tuple[int, ...],
    glue: GluingDescriptor,
) -> None:
    source_extents = _boundary_extents(dims, glue.source)
    target_extents = _boundary_extents(dims, glue.target)
    for source_index, target_index in enumerate(glue.transform.permutation):
        if source_extents[source_index] != target_extents[target_index]:
            raise ValueError(
                "gluing transform is not bijective for the board dimensions"
            )


def validate_explorer_topology_profile(
    profile: ExplorerTopologyProfile,
    *,
    dims: tuple[int, ...],
) -> ExplorerTopologyProfile:
    dimension = normalize_dimension(profile.dimension)
    normalized_dims = _validate_dims(dims, dimension)
    active_gluings = profile.active_gluings()
    _validate_boundary_ownership(active_gluings)
    for glue in active_gluings:
        _validate_extent_compatibility(normalized_dims, glue)
    return profile
