from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations, product
from typing import Iterable, Literal, Sequence

from tet4d.engine.core.model import Coord

PLAIN_TRANSLATION = "plain_translation"
RIGID_TRANSFORM = "rigid_transform"
CELLWISE_DEFORMATION = "cellwise_deformation"

ExplorerPieceMoveKind = Literal[
    "plain_translation",
    "rigid_transform",
    "cellwise_deformation",
]


def _coerce_coords(coords: Iterable[Sequence[int]]) -> tuple[Coord, ...]:
    return tuple(tuple(int(value) for value in coord) for coord in coords)


def _sub_coords(left: Coord, right: Coord) -> Coord:
    return tuple(left[axis] - right[axis] for axis in range(len(left)))


@dataclass(frozen=True)
class ExplorerPieceFrameTransform:
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
class ExplorerPieceMoveOutcome:
    kind: ExplorerPieceMoveKind
    moved_cells: tuple[Coord, ...]
    frame_transform: ExplorerPieceFrameTransform | None = None

    def __post_init__(self) -> None:
        moved_cells = _coerce_coords(self.moved_cells)
        if not moved_cells:
            raise ValueError("moved_cells must be non-empty")
        dimension = len(moved_cells[0])
        if any(len(coord) != dimension for coord in moved_cells):
            raise ValueError("all moved_cells must share a dimension")
        if self.kind == CELLWISE_DEFORMATION:
            if self.frame_transform is not None:
                raise ValueError(
                    "cellwise deformation must not carry a frame transform"
                )
        elif self.frame_transform is None:
            raise ValueError("rigid move outcomes require a frame transform")
        object.__setattr__(self, "moved_cells", moved_cells)


@lru_cache(maxsize=8)
def _signed_permutations(
    dimension: int,
) -> tuple[tuple[tuple[int, ...], tuple[int, ...]], ...]:
    perms = tuple(permutations(range(dimension)))
    sign_options = tuple(product((-1, 1), repeat=dimension))
    return tuple(
        (
            tuple(int(value) for value in permutation),
            tuple(int(value) for value in signs),
        )
        for permutation in perms
        for signs in sign_options
    )


def classify_explorer_piece_move(
    source_cells: Iterable[Sequence[int]],
    moved_cells: Iterable[Sequence[int]],
) -> ExplorerPieceMoveOutcome:
    source = _coerce_coords(source_cells)
    moved = _coerce_coords(moved_cells)
    if not source or not moved:
        raise ValueError("source_cells and moved_cells must be non-empty")
    if len(source) != len(moved):
        raise ValueError("source_cells and moved_cells must have the same size")
    dimension = len(source[0])
    if any(len(coord) != dimension for coord in source + moved):
        raise ValueError("all coords must share a dimension")

    translation = _sub_coords(moved[0], source[0])
    if all(
        _sub_coords(moved[index], source[index]) == translation
        for index in range(len(source))
    ):
        return ExplorerPieceMoveOutcome(
            kind=PLAIN_TRANSLATION,
            moved_cells=moved,
            frame_transform=ExplorerPieceFrameTransform(
                permutation=tuple(range(dimension)),
                signs=tuple(1 for _ in range(dimension)),
                translation=translation,
            ),
        )

    for permutation, signs in _signed_permutations(dimension):
        linear = ExplorerPieceFrameTransform(
            permutation=permutation,
            signs=signs,
            translation=tuple(0 for _ in range(dimension)),
        )
        if linear.is_identity_linear():
            continue
        translation = _sub_coords(moved[0], linear.apply_linear(source[0]))
        transform = ExplorerPieceFrameTransform(
            permutation=permutation,
            signs=signs,
            translation=translation,
        )
        if all(
            transform.apply_absolute(source[index]) == moved[index]
            for index in range(len(source))
        ):
            return ExplorerPieceMoveOutcome(
                kind=RIGID_TRANSFORM,
                moved_cells=moved,
                frame_transform=transform,
            )

    return ExplorerPieceMoveOutcome(
        kind=CELLWISE_DEFORMATION,
        moved_cells=moved,
    )


__all__ = [
    "CELLWISE_DEFORMATION",
    "PLAIN_TRANSLATION",
    "RIGID_TRANSFORM",
    "ExplorerPieceFrameTransform",
    "ExplorerPieceMoveKind",
    "ExplorerPieceMoveOutcome",
    "classify_explorer_piece_move",
]
