from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

from ..model import Coord

_PieceT = TypeVar("_PieceT")


def _normalize_coord(coord: Sequence[int]) -> Coord:
    return tuple(int(value) for value in coord)


def _normalize_coords(coords: Iterable[Sequence[int]]) -> tuple[Coord, ...]:
    return tuple(_normalize_coord(coord) for coord in coords)


@dataclass(frozen=True)
class CandidatePiecePlacement(Generic[_PieceT]):
    piece: _PieceT
    cells: tuple[Coord, ...]

    def __post_init__(self) -> None:
        cells = _normalize_coords(self.cells)
        if not cells:
            raise ValueError("candidate placement requires at least one cell")
        dimension = len(cells[0])
        if any(len(coord) != dimension for coord in cells):
            raise ValueError("candidate placement cells must share a dimension")
        object.__setattr__(self, "cells", cells)


def build_candidate_piece_placement(
    piece: _PieceT,
    cells: Iterable[Sequence[int]] | None,
) -> CandidatePiecePlacement[_PieceT] | None:
    if cells is None:
        return None
    return CandidatePiecePlacement(piece=piece, cells=tuple(cells))


def _occupied_coords(
    board_cells: Mapping[Sequence[int], object] | Iterable[Sequence[int]],
) -> set[Coord]:
    if isinstance(board_cells, Mapping):
        return {_normalize_coord(coord) for coord in board_cells.keys()}
    return {_normalize_coord(coord) for coord in board_cells}


def validate_candidate_piece_placement(
    candidate: CandidatePiecePlacement[object] | None,
    board_cells: Mapping[Sequence[int], object] | Iterable[Sequence[int]],
    *,
    ignore_cells: Iterable[Sequence[int]] = (),
    coord_validator: Callable[[Coord], bool] | None = None,
) -> bool:
    if candidate is None:
        return False
    if len(set(candidate.cells)) != len(candidate.cells):
        return False
    if coord_validator is not None and any(
        not coord_validator(coord) for coord in candidate.cells
    ):
        return False
    occupied = _occupied_coords(board_cells)
    ignored = {_normalize_coord(coord) for coord in ignore_cells}
    return all(coord not in occupied or coord in ignored for coord in candidate.cells)


def commit_piece_placement(
    state: object,
    candidate: CandidatePiecePlacement[object],
    *,
    attribute: str = "current_piece",
) -> None:
    setattr(state, attribute, candidate.piece)


__all__ = [
    "CandidatePiecePlacement",
    "build_candidate_piece_placement",
    "commit_piece_placement",
    "validate_candidate_piece_placement",
]
