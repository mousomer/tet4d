from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

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


def _single_flip_transform(
    tangent_dimension: int, flip_index: int
) -> BoundaryTransform:
    signs = [1] * tangent_dimension
    signs[int(flip_index)] = -1
    return BoundaryTransform(
        permutation=tuple(range(tangent_dimension)),
        signs=tuple(signs),
    )


def _full_flip_transform(tangent_dimension: int) -> BoundaryTransform:
    return BoundaryTransform(
        permutation=tuple(range(tangent_dimension)),
        signs=tuple(-1 for _ in range(tangent_dimension)),
    )


def _reverse_flip_transform(tangent_dimension: int) -> BoundaryTransform:
    return BoundaryTransform(
        permutation=tuple(reversed(range(tangent_dimension))),
        signs=tuple(-1 for _ in range(tangent_dimension)),
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
    return ExplorerTopologyProfile(
        dimension=normalized_dimension, gluings=tuple(gluings)
    )


def _opposite_projective_profile(dimension: int) -> ExplorerTopologyProfile:
    normalized_dimension = normalize_dimension(dimension)
    tangent_dimension = normalized_dimension - 1
    gluings = tuple(
        pair_boundaries(
            dimension=normalized_dimension,
            source_axis=axis,
            source_side=SIDE_NEG,
            target_axis=axis,
            target_side=SIDE_POS,
            glue_id=f"projective_{axis}",
            transform=_full_flip_transform(tangent_dimension),
        )
        for axis in range(normalized_dimension)
    )
    return ExplorerTopologyProfile(dimension=normalized_dimension, gluings=gluings)


def _sphere_like_pairs(dimension: int) -> tuple[tuple[int, str, int, str], ...]:
    normalized_dimension = normalize_dimension(dimension)
    if normalized_dimension == 2:
        return ((0, SIDE_NEG, 1, SIDE_NEG), (0, SIDE_POS, 1, SIDE_POS))
    if normalized_dimension == 3:
        return (
            (0, SIDE_NEG, 1, SIDE_NEG),
            (0, SIDE_POS, 1, SIDE_POS),
            (2, SIDE_NEG, 2, SIDE_POS),
        )
    if normalized_dimension == 4:
        return (
            (0, SIDE_NEG, 1, SIDE_NEG),
            (0, SIDE_POS, 1, SIDE_POS),
            (2, SIDE_NEG, 3, SIDE_NEG),
            (2, SIDE_POS, 3, SIDE_POS),
        )
    raise ValueError("sphere-like presets are only supported for 2D, 3D, and 4D")


def _sphere_like_profile(dimension: int) -> ExplorerTopologyProfile:
    normalized_dimension = normalize_dimension(dimension)
    tangent_dimension = normalized_dimension - 1
    gluings = tuple(
        pair_boundaries(
            dimension=normalized_dimension,
            source_axis=source_axis,
            source_side=source_side,
            target_axis=target_axis,
            target_side=target_side,
            glue_id=f"sphere_{index:02d}",
            transform=_reverse_flip_transform(tangent_dimension),
        )
        for index, (source_axis, source_side, target_axis, target_side) in enumerate(
            _sphere_like_pairs(normalized_dimension), start=1
        )
    )
    return ExplorerTopologyProfile(dimension=normalized_dimension, gluings=gluings)


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


def projective_plane_profile_2d() -> ExplorerTopologyProfile:
    return _opposite_projective_profile(2)


def sphere_profile_2d() -> ExplorerTopologyProfile:
    return _sphere_like_profile(2)


ExplorerTopologyPresetGroup = Literal[
    "quotient_core",
    "quotient_advanced",
    "sphere_like",
    "experimental",
]
ExplorerTopologyMathematicalStatus = Literal[
    "quotient_clean",
    "quotient_advanced",
    "transport_heuristic",
    "experimental",
]
ExplorerTopologyRecommendation = Literal[
    "explorer",
    "gameplay",
    "both",
]
_PRESET_GROUP_LABELS: dict[ExplorerTopologyPresetGroup, str] = {
    "quotient_core": "Core Quotient Topologies",
    "quotient_advanced": "Advanced Quotient Topologies",
    "sphere_like": "Sphere-Like / Compactified Transport",
    "experimental": "Experimental Transport",
}


@dataclass(frozen=True)
class ExplorerTopologyPreset:
    preset_id: str
    label: str
    description: str
    profile: ExplorerTopologyProfile
    group: ExplorerTopologyPresetGroup = "quotient_core"
    mathematical_status: ExplorerTopologyMathematicalStatus = "quotient_clean"
    recommended_for: ExplorerTopologyRecommendation = "both"
    gravity_safe: bool = True
    unsafe: bool = False


@dataclass(frozen=True)
class ExplorerTopologyPresetSection:
    group: ExplorerTopologyPresetGroup
    label: str
    presets: tuple[ExplorerTopologyPreset, ...]


def full_wrap_profile_3d() -> ExplorerTopologyProfile:
    return axis_wrap_profile(dimension=3, wrapped_axes=(0, 1, 2))


def twisted_y_profile_3d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=3,
        gluings=(
            pair_boundaries(
                dimension=3,
                source_axis=1,
                source_side=SIDE_NEG,
                target_axis=1,
                target_side=SIDE_POS,
                glue_id="twist_y",
                transform=BoundaryTransform(permutation=(0, 1), signs=(-1, 1)),
            ),
        ),
    )


def swapped_xz_profile_3d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=3,
        gluings=(
            pair_boundaries(
                dimension=3,
                source_axis=0,
                source_side=SIDE_NEG,
                target_axis=2,
                target_side=SIDE_POS,
                glue_id="xz_swap",
                transform=BoundaryTransform(permutation=(1, 0), signs=(1, 1)),
            ),
        ),
    )


def projective_space_profile_3d() -> ExplorerTopologyProfile:
    return _opposite_projective_profile(3)


def sphere_profile_3d() -> ExplorerTopologyProfile:
    return _sphere_like_profile(3)


def full_wrap_profile_4d() -> ExplorerTopologyProfile:
    return axis_wrap_profile(dimension=4, wrapped_axes=(0, 1, 2, 3))


def twisted_y_profile_4d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=4,
        gluings=(
            pair_boundaries(
                dimension=4,
                source_axis=1,
                source_side=SIDE_NEG,
                target_axis=1,
                target_side=SIDE_POS,
                glue_id="twist_y_4d",
                transform=BoundaryTransform(permutation=(0, 1, 2), signs=(-1, 1, 1)),
            ),
        ),
    )


def swap_xw_profile_4d() -> ExplorerTopologyProfile:
    return ExplorerTopologyProfile(
        dimension=4,
        gluings=(
            pair_boundaries(
                dimension=4,
                source_axis=0,
                source_side=SIDE_NEG,
                target_axis=3,
                target_side=SIDE_POS,
                glue_id="swap_xw_4d",
                transform=BoundaryTransform(permutation=(2, 0, 1), signs=(1, -1, 1)),
            ),
        ),
    )


def projective_space_profile_4d() -> ExplorerTopologyProfile:
    return _opposite_projective_profile(4)


def sphere_profile_4d() -> ExplorerTopologyProfile:
    return _sphere_like_profile(4)


def preset_group_label(group: ExplorerTopologyPresetGroup) -> str:
    return _PRESET_GROUP_LABELS[group]


def preset_display_label(
    preset: ExplorerTopologyPreset,
    *,
    include_group: bool = False,
    include_unsafe: bool = True,
) -> str:
    label = str(preset.label)
    if include_group:
        label = f"{preset_group_label(preset.group)}: {label}"
    if include_unsafe and preset.unsafe:
        label += " [unsafe]"
    return label


def explorer_preset_sections_for_dimension(
    dimension: int,
) -> tuple[ExplorerTopologyPresetSection, ...]:
    normalized_dimension = normalize_dimension(dimension)
    empty = ExplorerTopologyPreset(
        preset_id=f"empty_{normalized_dimension}d",
        label="Empty",
        description="Start with no explorer gluings.",
        profile=ExplorerTopologyProfile(dimension=normalized_dimension, gluings=()),
        group="quotient_core",
        mathematical_status="quotient_clean",
        recommended_for="both",
        gravity_safe=True,
    )
    if normalized_dimension == 2:
        return (
            ExplorerTopologyPresetSection(
                group="quotient_core",
                label=preset_group_label("quotient_core"),
                presets=(
                    empty,
                    ExplorerTopologyPreset(
                        preset_id="cylinder_2d",
                        label="Cylinder",
                        description="Wrap x while leaving y bounded.",
                        profile=cylinder_profile_2d(),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="both",
                        gravity_safe=True,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="torus_2d",
                        label="Torus",
                        description="Wrap x and y with identity transforms.",
                        profile=torus_profile_2d(),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="quotient_advanced",
                label=preset_group_label("quotient_advanced"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="mobius_2d",
                        label="Mobius Strip",
                        description="Wrap x with a tangent flip.",
                        profile=mobius_strip_profile_2d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="both",
                        gravity_safe=True,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="klein_2d",
                        label="Klein Bottle",
                        description="Combine x wrap with a flipped y seam.",
                        profile=klein_bottle_profile_2d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="projective_2d",
                        label="Projective Plane",
                        description="RP^2-like quotient with full tangent flips on both wrapped axes.",
                        profile=projective_plane_profile_2d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="sphere_like",
                label=preset_group_label("sphere_like"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="sphere_2d",
                        label="Sphere-Like Transport",
                        description="Heuristic adjacent-boundary compactification; exploratory and not piece-safe.",
                        profile=sphere_profile_2d(),
                        group="sphere_like",
                        mathematical_status="transport_heuristic",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
        )
    if normalized_dimension == 3:
        return (
            ExplorerTopologyPresetSection(
                group="quotient_core",
                label=preset_group_label("quotient_core"),
                presets=(
                    empty,
                    ExplorerTopologyPreset(
                        preset_id="wrap_x_3d",
                        label="Wrap X",
                        description="Connect x- to x+ with no twist.",
                        profile=axis_wrap_profile(dimension=3, wrapped_axes=(0,)),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="both",
                        gravity_safe=True,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="full_wrap_3d",
                        label="3-Torus",
                        description="Wrap every 3D axis with identity transforms to form a 3-torus.",
                        profile=full_wrap_profile_3d(),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="quotient_advanced",
                label=preset_group_label("quotient_advanced"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="twist_y_3d",
                        label="Twist Y",
                        description="Wrap y with a single tangent flip.",
                        profile=twisted_y_profile_3d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="projective_3d",
                        label="Projective Space",
                        description="RP^3-like quotient with full tangent flips on every wrapped axis.",
                        profile=projective_space_profile_3d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="sphere_like",
                label=preset_group_label("sphere_like"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="sphere_3d",
                        label="Sphere-Like Transport",
                        description="Heuristic adjacent-face compactification; exploratory and not piece-safe.",
                        profile=sphere_profile_3d(),
                        group="sphere_like",
                        mathematical_status="transport_heuristic",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="experimental",
                label=preset_group_label("experimental"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="swap_xz_3d",
                        label="Swap X- to Z+",
                        description="Pair x- with z+ using a tangent-axis swap.",
                        profile=swapped_xz_profile_3d(),
                        group="experimental",
                        mathematical_status="experimental",
                        recommended_for="explorer",
                        gravity_safe=True,
                    ),
                ),
            ),
        )
    if normalized_dimension == 4:
        return (
            ExplorerTopologyPresetSection(
                group="quotient_core",
                label=preset_group_label("quotient_core"),
                presets=(
                    empty,
                    ExplorerTopologyPreset(
                        preset_id="wrap_x_4d",
                        label="Wrap X",
                        description="Connect x- to x+ with no twist.",
                        profile=axis_wrap_profile(dimension=4, wrapped_axes=(0,)),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="both",
                        gravity_safe=True,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="full_wrap_4d",
                        label="4-Torus",
                        description="Wrap every 4D axis with identity transforms to form a 4-torus.",
                        profile=full_wrap_profile_4d(),
                        group="quotient_core",
                        mathematical_status="quotient_clean",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="quotient_advanced",
                label=preset_group_label("quotient_advanced"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="twist_y_4d",
                        label="Twist Y",
                        description="Wrap y with one tangent-axis flip in 4D.",
                        profile=twisted_y_profile_4d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                    ),
                    ExplorerTopologyPreset(
                        preset_id="projective_4d",
                        label="Projective Space",
                        description="RP^4-like quotient with full tangent flips on every wrapped axis.",
                        profile=projective_space_profile_4d(),
                        group="quotient_advanced",
                        mathematical_status="quotient_advanced",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="sphere_like",
                label=preset_group_label("sphere_like"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="sphere_4d",
                        label="Sphere-Like Transport",
                        description="Heuristic adjacent-hyperface compactification; exploratory and not piece-safe.",
                        profile=sphere_profile_4d(),
                        group="sphere_like",
                        mathematical_status="transport_heuristic",
                        recommended_for="explorer",
                        gravity_safe=False,
                        unsafe=True,
                    ),
                ),
            ),
            ExplorerTopologyPresetSection(
                group="experimental",
                label=preset_group_label("experimental"),
                presets=(
                    ExplorerTopologyPreset(
                        preset_id="swap_xw_4d",
                        label="Swap X- to W+",
                        description="Pair x- with w+ using a 3-axis signed permutation.",
                        profile=swap_xw_profile_4d(),
                        group="experimental",
                        mathematical_status="experimental",
                        recommended_for="explorer",
                        gravity_safe=True,
                    ),
                ),
            ),
        )
    return (
        ExplorerTopologyPresetSection(
            group="quotient_core",
            label=preset_group_label("quotient_core"),
            presets=(empty,),
        ),
    )


def explorer_presets_for_dimension(
    dimension: int,
) -> tuple[ExplorerTopologyPreset, ...]:
    return tuple(
        preset
        for section in explorer_preset_sections_for_dimension(dimension)
        for preset in section.presets
    )


__all__ = [
    "ExplorerTopologyPreset",
    "ExplorerTopologyPresetSection",
    "axis_wrap_profile",
    "cylinder_profile_2d",
    "explorer_preset_sections_for_dimension",
    "explorer_presets_for_dimension",
    "full_wrap_profile_3d",
    "full_wrap_profile_4d",
    "klein_bottle_profile_2d",
    "mobius_strip_profile_2d",
    "pair_boundaries",
    "preset_display_label",
    "preset_group_label",
    "projective_plane_profile_2d",
    "projective_space_profile_3d",
    "projective_space_profile_4d",
    "sphere_profile_2d",
    "sphere_profile_3d",
    "sphere_profile_4d",
    "swap_xw_profile_4d",
    "swapped_xz_profile_3d",
    "torus_profile_2d",
    "twisted_y_profile_3d",
    "twisted_y_profile_4d",
]
