from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from itertools import product
from typing import Iterable, Literal, Sequence

from ..core.model import Coord
from .glue_map import (
    BoundaryTraversal,
    _apply_transform,
    _boundary_extents,
    _boundary_for_exit,
    _target_inward_step,
)
from .glue_model import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    MoveStep,
    coord_in_bounds,
    tangent_axes_for_boundary,
)
from .glue_validate import validate_explorer_topology_profile

BLOCKED_MOVE = "blocked"
PLAIN_TRANSLATION = "plain_translation"
RIGID_TRANSFORM = "rigid_transform"
CELLWISE_DEFORMATION = "cellwise_deformation"

ExplorerTransportMoveKind = Literal[
    "blocked",
    "plain_translation",
    "rigid_transform",
    "cellwise_deformation",
]


@dataclass(frozen=True)
class ExplorerTransportFrameTransform:
    permutation: tuple[int, ...]
    signs: tuple[int, ...]
    translation: Coord

    def __post_init__(self) -> None:
        permutation = tuple(int(value) for value in self.permutation)
        signs = tuple(int(value) for value in self.signs)
        translation = tuple(int(value) for value in self.translation)
        dimension = len(permutation)
        if dimension == 0:
            raise ValueError("frame transform requires at least one axis")
        if tuple(sorted(permutation)) != tuple(range(dimension)):
            raise ValueError("frame transform permutation must cover each axis once")
        if len(signs) != dimension or any(value not in (-1, 1) for value in signs):
            raise ValueError("frame transform signs must contain only -1 or +1")
        if len(translation) != dimension:
            raise ValueError("frame transform translation must match dimension")
        object.__setattr__(self, "permutation", permutation)
        object.__setattr__(self, "signs", signs)
        object.__setattr__(self, "translation", translation)

    def is_identity_linear(self) -> bool:
        return self.permutation == tuple(
            range(len(self.permutation))
        ) and self.signs == tuple(1 for _ in self.permutation)

    def apply_linear(self, coord: Sequence[int]) -> Coord:
        values = tuple(int(value) for value in coord)
        if len(values) != len(self.permutation):
            raise ValueError("coord dimension must match frame transform")
        mapped = [0] * len(values)
        for source_axis, target_axis in enumerate(self.permutation):
            mapped[target_axis] = self.signs[source_axis] * values[source_axis]
        return tuple(mapped)

    def apply_absolute(self, coord: Sequence[int]) -> Coord:
        mapped = self.apply_linear(coord)
        return tuple(
            mapped[axis] + self.translation[axis] for axis in range(len(mapped))
        )


@dataclass(frozen=True)
class DirectedBoundarySeam:
    glue_id: str
    source_boundary: BoundaryRef
    target_boundary: BoundaryRef
    exit_step: MoveStep
    entry_step: MoveStep
    seam_transform: BoundaryTransform
    frame_transform: ExplorerTransportFrameTransform
    piece_frame_transform: ExplorerTransportFrameTransform
    boundary_coord_map: tuple[tuple[Coord, Coord], ...]
    _target_lookup: dict[Coord, Coord] = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        mapping = tuple(
            (
                tuple(int(value) for value in source_coord),
                tuple(int(value) for value in target_coord),
            )
            for source_coord, target_coord in self.boundary_coord_map
        )
        if not mapping:
            raise ValueError("directed seam requires at least one boundary coordinate")
        dimension = self.source_boundary.dimension
        if self.target_boundary.dimension != dimension:
            raise ValueError("directed seam boundaries must share a dimension")
        if len(self.frame_transform.translation) != dimension:
            raise ValueError("directed seam frame transform dimension mismatch")
        if len(self.piece_frame_transform.translation) != dimension:
            raise ValueError("directed seam piece-frame transform dimension mismatch")
        lookup: dict[Coord, Coord] = {}
        for source_coord, target_coord in mapping:
            if len(source_coord) != dimension or len(target_coord) != dimension:
                raise ValueError("directed seam coord map must match seam dimension")
            if source_coord in lookup:
                raise ValueError(
                    "directed seam boundary map contains duplicate source coords"
                )
            lookup[source_coord] = target_coord
        object.__setattr__(self, "boundary_coord_map", mapping)
        object.__setattr__(self, "_target_lookup", lookup)

    def target_for_source_coord(self, coord: Sequence[int]) -> Coord:
        normalized = tuple(int(value) for value in coord)
        try:
            return self._target_lookup[normalized]
        except KeyError as exc:
            raise ValueError(
                "directed seam is missing a mapping for the requested boundary coord"
            ) from exc


@dataclass(frozen=True)
class CellStepResult:
    source: Coord
    step: MoveStep
    target: Coord | None
    traversal: BoundaryTraversal | None
    frame_transform: ExplorerTransportFrameTransform | None
    piece_frame_transform: ExplorerTransportFrameTransform | None

    @property
    def blocked(self) -> bool:
        return self.target is None


@dataclass(frozen=True)
class PieceStepResult:
    step: MoveStep
    source_cells: tuple[Coord, ...]
    kind: ExplorerTransportMoveKind
    moved_cells: tuple[Coord, ...] | None = None
    frame_transform: ExplorerTransportFrameTransform | None = None
    cell_steps: tuple[CellStepResult, ...] = ()
    rigidly_coherent: bool = False

    def __post_init__(self) -> None:
        source_cells = tuple(
            tuple(int(value) for value in coord) for coord in self.source_cells
        )
        cell_steps = tuple(self.cell_steps)
        moved_cells = (
            None
            if self.moved_cells is None
            else tuple(
                tuple(int(value) for value in coord) for coord in self.moved_cells
            )
        )
        if not source_cells:
            raise ValueError("source_cells must be non-empty")
        if any(len(coord) != len(source_cells[0]) for coord in source_cells):
            raise ValueError("all source_cells must share a dimension")
        if moved_cells is not None and any(
            len(coord) != len(source_cells[0]) for coord in moved_cells
        ):
            raise ValueError("all moved_cells must share the source dimension")
        if len(cell_steps) != len(source_cells):
            raise ValueError("piece-step cell_steps must match source_cells")
        if self.kind == BLOCKED_MOVE:
            if moved_cells is not None or self.frame_transform is not None:
                raise ValueError(
                    "blocked piece transport must not include moved cells or a frame transform"
                )
            rigidly_coherent = False
        elif self.kind == CELLWISE_DEFORMATION:
            if moved_cells is None or self.frame_transform is not None:
                raise ValueError(
                    "cellwise deformation requires moved cells and no frame transform"
                )
            rigidly_coherent = bool(self.rigidly_coherent)
        else:
            if moved_cells is None or self.frame_transform is None:
                raise ValueError(
                    "rigid or translated piece transport requires moved cells and a frame transform"
                )
            rigidly_coherent = True
        object.__setattr__(self, "source_cells", source_cells)
        object.__setattr__(self, "moved_cells", moved_cells)
        object.__setattr__(self, "cell_steps", cell_steps)
        object.__setattr__(self, "rigidly_coherent", rigidly_coherent)


def _identity_frame_transform(
    dimension: int,
    *,
    translation: Sequence[int],
) -> ExplorerTransportFrameTransform:
    return ExplorerTransportFrameTransform(
        permutation=tuple(range(dimension)),
        signs=tuple(1 for _ in range(dimension)),
        translation=tuple(int(value) for value in translation),
    )


def _translation_for_step(dimension: int, step: MoveStep) -> Coord:
    values = [0] * int(dimension)
    values[int(step.axis)] = int(step.delta)
    return tuple(values)


def _lift_boundary_transform(
    *,
    dimension: int,
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    seam_transform: BoundaryTransform,
    normal_sign: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    permutation = [0] * int(dimension)
    signs = [1] * int(dimension)

    source_axes = tangent_axes_for_boundary(source_boundary)
    target_axes = tangent_axes_for_boundary(target_boundary)
    for source_index, target_index in enumerate(seam_transform.permutation):
        source_axis = source_axes[source_index]
        target_axis = target_axes[target_index]
        permutation[source_axis] = target_axis
        signs[source_axis] = seam_transform.signs[source_index]

    permutation[source_boundary.axis] = target_boundary.axis
    signs[source_boundary.axis] = int(normal_sign)
    return tuple(permutation), tuple(signs)


def _piece_frame_normal_sign(
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
) -> int:
    exit_step = _exit_step_for_boundary(source_boundary)
    entry_step = _target_inward_step(target_boundary)
    return 1 if int(exit_step.delta) == int(entry_step.delta) else -1


def _linear_signature(
    frame_transform: ExplorerTransportFrameTransform,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return frame_transform.permutation, frame_transform.signs


def _coerce_cells(cells: Iterable[Sequence[int]]) -> tuple[Coord, ...]:
    return tuple(tuple(int(value) for value in coord) for coord in cells)


def _boundary_fixed_value(dims: Coord, boundary: BoundaryRef) -> int:
    return 0 if boundary.side == "-" else int(dims[boundary.axis]) - 1


def _exit_step_for_boundary(boundary: BoundaryRef) -> MoveStep:
    return MoveStep(axis=boundary.axis, delta=-1 if boundary.side == "-" else 1)


def _iter_boundary_coords(dims: Coord, boundary: BoundaryRef) -> tuple[Coord, ...]:
    tangent_axes = tangent_axes_for_boundary(boundary)
    tangent_ranges = [range(int(dims[axis])) for axis in tangent_axes]
    fixed_value = _boundary_fixed_value(dims, boundary)
    coords: list[Coord] = []
    for tangent_values in product(*tangent_ranges):
        coord = [0] * len(dims)
        for axis, value in zip(tangent_axes, tangent_values):
            coord[axis] = int(value)
        coord[boundary.axis] = fixed_value
        coords.append(tuple(coord))
    return tuple(coords)


def _target_coord_for_source_coord(
    source_coord: Coord,
    *,
    dims: Coord,
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    seam_transform: BoundaryTransform,
) -> Coord:
    source_axes = tangent_axes_for_boundary(source_boundary)
    target_axes = tangent_axes_for_boundary(target_boundary)
    source_values = tuple(int(source_coord[axis]) for axis in source_axes)
    target_values = _apply_transform(
        source_values,
        target_extents=_boundary_extents(dims, target_boundary),
        transform=seam_transform,
    )
    target_coord = [0] * len(dims)
    for axis, value in zip(target_axes, target_values):
        target_coord[axis] = int(value)
    target_coord[target_boundary.axis] = _boundary_fixed_value(dims, target_boundary)
    return tuple(target_coord)


def _frame_transform_for_boundary_mapping(
    *,
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    seam_transform: BoundaryTransform,
    boundary_coord_map: tuple[tuple[Coord, Coord], ...],
    normal_sign: int,
) -> ExplorerTransportFrameTransform:
    dimension = source_boundary.dimension
    permutation, signs = _lift_boundary_transform(
        dimension=dimension,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        seam_transform=seam_transform,
        normal_sign=normal_sign,
    )
    linear = ExplorerTransportFrameTransform(
        permutation=permutation,
        signs=signs,
        translation=tuple(0 for _ in range(dimension)),
    )
    sample_source, sample_target = boundary_coord_map[0]
    translation = tuple(
        sample_target[axis] - linear.apply_linear(sample_source)[axis]
        for axis in range(dimension)
    )
    frame_transform = ExplorerTransportFrameTransform(
        permutation=permutation,
        signs=signs,
        translation=translation,
    )
    for source_coord, target_coord in boundary_coord_map:
        if frame_transform.apply_absolute(source_coord) != target_coord:
            raise ValueError(
                "directed seam frame transform is not coherent across the boundary"
            )
    return frame_transform


def _materialize_directed_boundary_seam(
    glue: GluingDescriptor,
    *,
    dims: Coord,
    forward: bool,
) -> DirectedBoundarySeam:
    source_boundary = glue.source if forward else glue.target
    target_boundary = glue.target if forward else glue.source
    seam_transform = glue.transform if forward else glue.transform.inverse()
    boundary_coord_map = tuple(
        (
            source_coord,
            _target_coord_for_source_coord(
                source_coord,
                dims=dims,
                source_boundary=source_boundary,
                target_boundary=target_boundary,
                seam_transform=seam_transform,
            ),
        )
        for source_coord in _iter_boundary_coords(dims, source_boundary)
    )
    return DirectedBoundarySeam(
        glue_id=glue.glue_id,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        exit_step=_exit_step_for_boundary(source_boundary),
        entry_step=_target_inward_step(target_boundary),
        seam_transform=seam_transform,
        frame_transform=_frame_transform_for_boundary_mapping(
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            seam_transform=seam_transform,
            boundary_coord_map=boundary_coord_map,
            normal_sign=-1,
        ),
        piece_frame_transform=_frame_transform_for_boundary_mapping(
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            seam_transform=seam_transform,
            boundary_coord_map=boundary_coord_map,
            normal_sign=_piece_frame_normal_sign(source_boundary, target_boundary),
        ),
        boundary_coord_map=boundary_coord_map,
        _target_lookup={},
    )


def _build_directed_seam_family(
    profile: ExplorerTopologyProfile,
    *,
    dims: Coord,
) -> tuple[tuple[DirectedBoundarySeam, ...], dict[BoundaryRef, DirectedBoundarySeam]]:
    seams: list[DirectedBoundarySeam] = []
    seam_lookup: dict[BoundaryRef, DirectedBoundarySeam] = {}
    for glue in profile.active_gluings():
        for forward in (True, False):
            seam = _materialize_directed_boundary_seam(glue, dims=dims, forward=forward)
            existing = seam_lookup.get(seam.source_boundary)
            if existing is not None:
                raise ValueError(
                    "multiple directed seams were materialized for boundary "
                    f"{seam.source_boundary.label}: {existing.glue_id} and {seam.glue_id}"
                )
            seam_lookup[seam.source_boundary] = seam
            seams.append(seam)
    _validate_inverse_seam_family(tuple(seams), seam_lookup)
    return tuple(seams), seam_lookup


def _validate_inverse_seam_family(
    seams: tuple[DirectedBoundarySeam, ...],
    seam_lookup: dict[BoundaryRef, DirectedBoundarySeam],
) -> None:
    for seam in seams:
        inverse = seam_lookup.get(seam.target_boundary)
        if inverse is None:
            raise ValueError(
                "directed seam family is missing the reverse crossing for "
                f"{seam.source_boundary.label} -> {seam.target_boundary.label}"
            )
        if inverse.target_boundary != seam.source_boundary:
            raise ValueError(
                "directed seam reverse crossing does not return to the source boundary"
            )
        if inverse.seam_transform != seam.seam_transform.inverse():
            raise ValueError(
                "directed seam reverse crossing does not use the inverse transform"
            )
        for source_coord, target_coord in seam.boundary_coord_map:
            if inverse.target_for_source_coord(target_coord) != source_coord:
                raise ValueError(
                    "directed seam reverse crossing does not restore the source coord"
                )
            if inverse.frame_transform.apply_absolute(target_coord) != source_coord:
                raise ValueError(
                    "directed seam reverse frame transform does not restore the source coord"
                )


@dataclass(frozen=True)
class ExplorerTransportResolver:
    profile: ExplorerTopologyProfile
    dims: Coord
    directed_seams: tuple[DirectedBoundarySeam, ...]
    _seam_lookup: dict[BoundaryRef, DirectedBoundarySeam] = field(
        repr=False, compare=False
    )

    def seam_for_boundary(
        self,
        boundary: BoundaryRef,
    ) -> DirectedBoundarySeam | None:
        return self._seam_lookup.get(boundary)

    def resolve_cell_step(self, coord: Sequence[int], step: MoveStep) -> CellStepResult:
        normalized_coord = tuple(int(value) for value in coord)
        if not coord_in_bounds(normalized_coord, self.dims):
            raise ValueError("coord must be in bounds")
        if not (0 <= int(step.axis) < len(self.dims)):
            raise ValueError("move axis must exist in the board dimension")

        next_coord = list(normalized_coord)
        next_coord[int(step.axis)] += int(step.delta)
        translated = tuple(int(value) for value in next_coord)
        if coord_in_bounds(translated, self.dims):
            return CellStepResult(
                source=normalized_coord,
                step=step,
                target=translated,
                traversal=None,
                frame_transform=_identity_frame_transform(
                    len(self.dims),
                    translation=_translation_for_step(len(self.dims), step),
                ),
                piece_frame_transform=_identity_frame_transform(
                    len(self.dims),
                    translation=_translation_for_step(len(self.dims), step),
                ),
            )

        source_boundary = _boundary_for_exit(normalized_coord, step, self.dims)
        if source_boundary is None:
            return CellStepResult(
                source=normalized_coord,
                step=step,
                target=None,
                traversal=None,
                frame_transform=None,
                piece_frame_transform=None,
            )

        seam = self._seam_lookup.get(source_boundary)
        if seam is None:
            return CellStepResult(
                source=normalized_coord,
                step=step,
                target=None,
                traversal=None,
                frame_transform=None,
                piece_frame_transform=None,
            )

        target_coord = seam.target_for_source_coord(normalized_coord)
        traversal = BoundaryTraversal(
            glue_id=seam.glue_id,
            source_boundary=seam.source_boundary,
            target_boundary=seam.target_boundary,
            source_coord=normalized_coord,
            target_coord=target_coord,
            exit_step=step,
            entry_step=seam.entry_step,
        )
        return CellStepResult(
            source=normalized_coord,
            step=step,
            target=target_coord,
            traversal=traversal,
            frame_transform=seam.frame_transform,
            piece_frame_transform=seam.piece_frame_transform,
        )

    def resolve_piece_step(
        self,
        cells: Iterable[Sequence[int]],
        step: MoveStep,
    ) -> PieceStepResult:
        source_cells = _coerce_cells(cells)
        if not source_cells:
            raise ValueError("cells must be non-empty")
        if any(len(coord) != len(self.dims) for coord in source_cells):
            raise ValueError("cell dimension must match resolver dims")

        cell_steps = tuple(
            self.resolve_cell_step(coord, step) for coord in source_cells
        )
        if any(result.blocked for result in cell_steps):
            return PieceStepResult(
                step=step,
                source_cells=source_cells,
                kind=BLOCKED_MOVE,
                cell_steps=cell_steps,
            )

        moved_cells = tuple(
            result.target for result in cell_steps if result.target is not None
        )
        if len(moved_cells) != len(set(moved_cells)):
            return PieceStepResult(
                step=step,
                source_cells=source_cells,
                kind=CELLWISE_DEFORMATION,
                moved_cells=moved_cells,
                cell_steps=cell_steps,
            )

        piece_frame_transform = cell_steps[0].piece_frame_transform
        if piece_frame_transform is None:
            raise ValueError(
                "non-blocked cell transport requires a piece-frame transform"
            )
        if all(
            result.piece_frame_transform == piece_frame_transform
            for result in cell_steps
        ):
            transformed_cells = tuple(
                piece_frame_transform.apply_absolute(coord) for coord in source_cells
            )
            if transformed_cells == moved_cells:
                kind = (
                    PLAIN_TRANSLATION
                    if piece_frame_transform.is_identity_linear()
                    else RIGID_TRANSFORM
                )
                return PieceStepResult(
                    step=step,
                    source_cells=source_cells,
                    kind=kind,
                    moved_cells=moved_cells,
                    frame_transform=piece_frame_transform,
                    cell_steps=cell_steps,
                )

        rigidly_coherent = all(
            result.piece_frame_transform is not None
            and _linear_signature(result.piece_frame_transform)
            == _linear_signature(piece_frame_transform)
            for result in cell_steps
        )
        return PieceStepResult(
            step=step,
            source_cells=source_cells,
            kind=CELLWISE_DEFORMATION,
            moved_cells=moved_cells,
            cell_steps=cell_steps,
            rigidly_coherent=rigidly_coherent,
        )


@lru_cache(maxsize=32)
def build_explorer_transport_resolver(
    profile: ExplorerTopologyProfile,
    dims: Sequence[int],
) -> ExplorerTransportResolver:
    normalized_dims = tuple(int(value) for value in dims)
    validated_profile = validate_explorer_topology_profile(
        profile,
        dims=normalized_dims,
    )
    directed_seams, seam_lookup = _build_directed_seam_family(
        validated_profile,
        dims=normalized_dims,
    )
    return ExplorerTransportResolver(
        profile=validated_profile,
        dims=normalized_dims,
        directed_seams=directed_seams,
        _seam_lookup=seam_lookup,
    )


__all__ = [
    "BLOCKED_MOVE",
    "CELLWISE_DEFORMATION",
    "DirectedBoundarySeam",
    "PLAIN_TRANSLATION",
    "RIGID_TRANSFORM",
    "CellStepResult",
    "ExplorerTransportFrameTransform",
    "ExplorerTransportMoveKind",
    "ExplorerTransportResolver",
    "PieceStepResult",
    "build_explorer_transport_resolver",
]
