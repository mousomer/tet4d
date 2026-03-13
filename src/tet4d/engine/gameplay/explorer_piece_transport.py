from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from itertools import permutations, product
from typing import Iterable, Literal, Sequence

from tet4d.engine.core.model import Coord
from tet4d.engine.topology_explorer.transport_resolver import (
    CELLWISE_DEFORMATION,
    PLAIN_TRANSLATION,
    RIGID_TRANSFORM,
    ExplorerTransportFrameTransform,
)

ExplorerPieceMoveKind = Literal[
    "plain_translation",
    "rigid_transform",
    "cellwise_deformation",
]
ExplorerPieceFrameTransform = ExplorerTransportFrameTransform


def _coerce_coords(coords: Iterable[Sequence[int]]) -> tuple[Coord, ...]:
    return tuple(tuple(int(value) for value in coord) for coord in coords)


def _sub_coords(left: Coord, right: Coord) -> Coord:
    return tuple(left[axis] - right[axis] for axis in range(len(left)))


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
