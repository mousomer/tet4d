from __future__ import annotations

from dataclasses import dataclass
from itertools import permutations

from tet4d.engine.topology_explorer import (
    AXIS_NAMES,
    BoundaryRef,
    BoundaryTransform,
    boundary_label,
    tangent_axes_for_boundary,
)


@dataclass(frozen=True)
class ExplorerGlueDraft:
    slot_index: int
    source_index: int
    target_index: int
    permutation_index: int
    signs: tuple[int, ...]


def boundaries_for_dimension(dimension: int) -> tuple[BoundaryRef, ...]:
    return tuple(
        BoundaryRef(dimension=dimension, axis=axis, side=side)
        for axis in range(dimension)
        for side in ("-", "+")
    )


def permutation_options_for_dimension(dimension: int) -> tuple[tuple[int, ...], ...]:
    tangent_dimension = int(dimension) - 1
    return tuple(tuple(option) for option in permutations(range(tangent_dimension)))


def default_draft_for_dimension(dimension: int) -> ExplorerGlueDraft:
    tangent_dimension = int(dimension) - 1
    return ExplorerGlueDraft(
        slot_index=0,
        source_index=0,
        target_index=1,
        permutation_index=0,
        signs=tuple(1 for _ in range(tangent_dimension)),
    )


def transform_preview_label(
    source: BoundaryRef,
    target: BoundaryRef,
    transform: BoundaryTransform,
) -> str:
    source_axes = tangent_axes_for_boundary(source)
    target_axes = tangent_axes_for_boundary(target)
    mapped: list[str] = []
    for source_index, target_index in enumerate(transform.permutation):
        label = AXIS_NAMES[target_axes[target_index]]
        if transform.signs[source_index] < 0:
            label = f"-{label}"
        mapped.append(label)
    source_text = ",".join(AXIS_NAMES[axis] for axis in source_axes)
    target_text = ",".join(mapped)
    return f"{boundary_label(source)}: {source_text} -> {boundary_label(target)}: {target_text}"


__all__ = [
    "ExplorerGlueDraft",
    "boundaries_for_dimension",
    "default_draft_for_dimension",
    "permutation_options_for_dimension",
    "transform_preview_label",
]
