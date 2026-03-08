from __future__ import annotations

from dataclasses import dataclass

from ..core.model import Coord


AXIS_NAMES = ("x", "y", "z", "w")
SIDE_NEG = "-"
SIDE_POS = "+"
_SIDE_SET = frozenset((SIDE_NEG, SIDE_POS))


def normalize_dimension(dimension: int) -> int:
    value = int(dimension)
    if value < 2 or value > len(AXIS_NAMES):
        raise ValueError("dimension must be between 2 and 4")
    return value


def axis_name(axis: int) -> str:
    index = int(axis)
    if not (0 <= index < len(AXIS_NAMES)):
        raise ValueError("invalid axis index")
    return AXIS_NAMES[index]


def normalize_side(side: str) -> str:
    normalized = str(side).strip()
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
        axis = int(self.axis)
        if not (0 <= axis < dimension):
            raise ValueError("boundary axis must exist in the given dimension")
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
        permutation = tuple(int(value) for value in self.permutation)
        signs = tuple(int(value) for value in self.signs)
        if len(permutation) == 0:
            raise ValueError("boundary transform must have at least one tangent axis")
        if len(permutation) != len(signs):
            raise ValueError("permutation and signs must have the same length")
        expected = tuple(range(len(permutation)))
        if tuple(sorted(permutation)) != expected:
            raise ValueError("permutation must be a complete index permutation")
        if any(value not in (-1, 1) for value in signs):
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
        glue_id = str(self.glue_id).strip()
        if not glue_id:
            raise ValueError("glue_id must be non-empty")
        if self.source.dimension != self.target.dimension:
            raise ValueError("source and target boundaries must share a dimension")
        if self.source == self.target:
            raise ValueError("source and target boundaries must be distinct")
        if self.transform.tangent_dimension != self.source.dimension - 1:
            raise ValueError("transform tangent dimension must match boundary tangent rank")
        object.__setattr__(self, "glue_id", glue_id)
        object.__setattr__(self, "enabled", bool(self.enabled))


@dataclass(frozen=True)
class ExplorerTopologyProfile:
    dimension: int
    gluings: tuple[GluingDescriptor, ...]

    def __post_init__(self) -> None:
        dimension = normalize_dimension(self.dimension)
        gluings = tuple(self.gluings)
        for glue in gluings:
            if glue.source.dimension != dimension or glue.target.dimension != dimension:
                raise ValueError("all boundaries in a profile must match profile dimension")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "gluings", gluings)

    def active_gluings(self) -> tuple[GluingDescriptor, ...]:
        return tuple(glue for glue in self.gluings if glue.enabled)


@dataclass(frozen=True)
class MoveStep:
    axis: int
    delta: int

    def __post_init__(self) -> None:
        axis = int(self.axis)
        delta = int(self.delta)
        if axis < 0:
            raise ValueError("move axis must be non-negative")
        if delta not in (-1, 1):
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
