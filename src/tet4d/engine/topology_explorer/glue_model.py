from __future__ import annotations

from dataclasses import dataclass

from tet4d.generated.topology_contract_v1 import (
    AXIS_NAMES,
    MAXIMUM_RANK,
    MINIMUM_RANK,
    VALID_BOUNDARY_SIDES,
    VALID_MOVEMENT_DELTAS,
    VALID_TRANSFORM_SIGNS,
)

from ..core.model import Coord
from .domain_validation import (
    require_bounded_integral,
    require_exact_bool,
    require_instance,
    require_instance_sequence,
    require_integral,
    require_integral_sequence,
    require_non_negative_integral,
    require_string,
)

SIDE_NEG, SIDE_POS = VALID_BOUNDARY_SIDES
_SIDE_SET = frozenset(VALID_BOUNDARY_SIDES)


def normalize_dimension(dimension: int) -> int:
    return require_bounded_integral(
        dimension,
        "dimension",
        minimum=MINIMUM_RANK,
        maximum=MAXIMUM_RANK,
    )


def axis_name(axis: int) -> str:
    index = require_bounded_integral(
        axis,
        "axis",
        minimum=0,
        maximum=len(AXIS_NAMES) - 1,
    )
    return AXIS_NAMES[index]


def normalize_side(side: str) -> str:
    normalized = require_string(side, "side").strip()
    if normalized not in _SIDE_SET:
        raise ValueError("side must be '-' or '+'")
    return normalized


@dataclass(frozen=True)
class BoundaryRef:
    dimension: int
    axis: int
    side: str

    def __post_init__(self) -> None:
        dimension = normalize_dimension(self.dimension)
        axis = require_bounded_integral(
            self.axis,
            "boundary.axis",
            minimum=0,
            maximum=dimension - 1,
        )
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "side", normalize_side(self.side))

    @property
    def label(self) -> str:
        return boundary_label(self)


def boundary_label(boundary: BoundaryRef) -> str:
    return f"{axis_name(boundary.axis)}{boundary.side}"


def tangent_axes_for_boundary(boundary: BoundaryRef) -> tuple[int, ...]:
    return tuple(axis for axis in range(boundary.dimension) if axis != boundary.axis)


@dataclass(frozen=True)
class BoundaryTransform:
    permutation: tuple[int, ...]
    signs: tuple[int, ...]

    def __post_init__(self) -> None:
        permutation = require_integral_sequence(
            self.permutation,
            "boundary_transform.permutation",
        )
        signs = require_integral_sequence(
            self.signs,
            "boundary_transform.signs",
        )
        if len(permutation) == 0:
            raise ValueError("boundary transform must have at least one tangent axis")
        if len(permutation) != len(signs):
            raise ValueError("permutation and signs must have the same length")
        expected = tuple(range(len(permutation)))
        if tuple(sorted(permutation)) != expected:
            raise ValueError("permutation must be a complete index permutation")
        if any(value not in VALID_TRANSFORM_SIGNS for value in signs):
            raise ValueError("signs must contain only -1 or +1")
        object.__setattr__(self, "permutation", permutation)
        object.__setattr__(self, "signs", signs)

    @property
    def tangent_dimension(self) -> int:
        return len(self.permutation)

    def inverse(self) -> BoundaryTransform:
        inverse_permutation = [0] * len(self.permutation)
        inverse_signs = [1] * len(self.permutation)
        for source_index, target_index in enumerate(self.permutation):
            inverse_permutation[target_index] = source_index
            inverse_signs[target_index] = self.signs[source_index]
        return BoundaryTransform(
            permutation=tuple(inverse_permutation),
            signs=tuple(inverse_signs),
        )


@dataclass(frozen=True)
class GluingDescriptor:
    glue_id: str
    source: BoundaryRef
    target: BoundaryRef
    transform: BoundaryTransform
    enabled: bool = True

    def __post_init__(self) -> None:
        glue_id = require_string(self.glue_id, "gluing.glue_id").strip()
        if not glue_id:
            raise ValueError("glue_id must be non-empty")
        source = require_instance(self.source, "gluing.source", BoundaryRef)
        target = require_instance(self.target, "gluing.target", BoundaryRef)
        transform = require_instance(
            self.transform,
            "gluing.transform",
            BoundaryTransform,
        )
        if source.dimension != target.dimension:
            raise ValueError("source and target boundaries must share a dimension")
        if source == target:
            raise ValueError("source and target boundaries must be distinct")
        if transform.tangent_dimension != source.dimension - 1:
            raise ValueError(
                "transform tangent dimension must match boundary tangent rank"
            )
        object.__setattr__(self, "glue_id", glue_id)
        object.__setattr__(
            self,
            "enabled",
            require_exact_bool(self.enabled, "gluing.enabled"),
        )


@dataclass(frozen=True)
class ExplorerTopologyProfile:
    dimension: int
    gluings: tuple[GluingDescriptor, ...]

    def __post_init__(self) -> None:
        dimension = normalize_dimension(self.dimension)
        gluings = require_instance_sequence(
            self.gluings,
            "profile.gluings",
            GluingDescriptor,
        )
        for glue in gluings:
            if glue.source.dimension != dimension or glue.target.dimension != dimension:
                raise ValueError(
                    "all boundaries in a profile must match profile dimension"
                )
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "gluings", gluings)

    def active_gluings(self) -> tuple[GluingDescriptor, ...]:
        return tuple(glue for glue in self.gluings if glue.enabled)


@dataclass(frozen=True)
class MoveStep:
    axis: int
    delta: int

    def __post_init__(self) -> None:
        axis = require_non_negative_integral(self.axis, "move.axis")
        delta = require_integral(self.delta, "move.delta")
        if delta not in VALID_MOVEMENT_DELTAS:
            raise ValueError("move delta must be -1 or +1")
        object.__setattr__(self, "axis", axis)
        object.__setattr__(self, "delta", delta)

    @property
    def label(self) -> str:
        return f"{axis_name(self.axis)}{'+' if self.delta > 0 else '-'}"


def movement_steps_for_dimension(dimension: int) -> tuple[MoveStep, ...]:
    normalized = normalize_dimension(dimension)
    steps: list[MoveStep] = []
    for axis in range(normalized):
        steps.append(MoveStep(axis=axis, delta=-1))
        steps.append(MoveStep(axis=axis, delta=1))
    return tuple(steps)


def coord_in_bounds(coord: Coord, dims: Coord) -> bool:
    return len(coord) == len(dims) and all(
        0 <= value < dims[axis] for axis, value in enumerate(coord)
    )
