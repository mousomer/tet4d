from __future__ import annotations

from .glue_model import (
    SIDE_NEG,
    SIDE_POS,
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    normalize_dimension,
)


def _identity_transform(tangent_dimension: int) -> BoundaryTransform:
    return BoundaryTransform(
        permutation=tuple(range(tangent_dimension)),
        signs=tuple(1 for _ in range(tangent_dimension)),
    )


def _single_flip_transform(tangent_dimension: int, flip_index: int) -> BoundaryTransform:
    signs = [1] * tangent_dimension
    signs[int(flip_index)] = -1
    return BoundaryTransform(
        permutation=tuple(range(tangent_dimension)),
        signs=tuple(signs),
    )


def pair_boundaries(
    *,
    dimension: int,
    source_axis: int,
    source_side: str,
    target_axis: int,
    target_side: str,
    glue_id: str,
    transform: BoundaryTransform,
) -> GluingDescriptor:
    return GluingDescriptor(
        glue_id=glue_id,
        source=BoundaryRef(dimension=dimension, axis=source_axis, side=source_side),
        target=BoundaryRef(dimension=dimension, axis=target_axis, side=target_side),
        transform=transform,
    )


def axis_wrap_profile(
    *,
    dimension: int,
    wrapped_axes: tuple[int, ...],
) -> ExplorerTopologyProfile:
    normalized_dimension = normalize_dimension(dimension)
    tangent_dimension = normalized_dimension - 1
    gluings = [
        pair_boundaries(
            dimension=normalized_dimension,
            source_axis=axis,
            source_side=SIDE_NEG,
            target_axis=axis,
            target_side=SIDE_POS,
            glue_id=f"wrap_{axis}",
            transform=_identity_transform(tangent_dimension),
        )
        for axis in wrapped_axes
    ]
    return ExplorerTopologyProfile(dimension=normalized_dimension, gluings=tuple(gluings))


def torus_profile_2d() -> ExplorerTopologyProfile:
    return axis_wrap_profile(dimension=2, wrapped_axes=(0, 1))


def cylinder_profile_2d() -> ExplorerTopologyProfile:
    return axis_wrap_profile(dimension=2, wrapped_axes=(0,))


def mobius_strip_profile_2d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=2,
        gluings=(
            pair_boundaries(
                dimension=2,
                source_axis=0,
                source_side=SIDE_NEG,
                target_axis=0,
                target_side=SIDE_POS,
                glue_id="mobius_x",
                transform=_single_flip_transform(1, 0),
            ),
        ),
    )


def klein_bottle_profile_2d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=2,
        gluings=(
            pair_boundaries(
                dimension=2,
                source_axis=0,
                source_side=SIDE_NEG,
                target_axis=0,
                target_side=SIDE_POS,
                glue_id="klein_x",
                transform=_identity_transform(1),
            ),
            pair_boundaries(
                dimension=2,
                source_axis=1,
                source_side=SIDE_NEG,
                target_axis=1,
                target_side=SIDE_POS,
                glue_id="klein_y",
                transform=_single_flip_transform(1, 0),
            ),
        ),
    )
