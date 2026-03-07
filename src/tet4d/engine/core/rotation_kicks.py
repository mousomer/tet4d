from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar


Coord = tuple[int, ...]
PlaneOffset = tuple[int, int]
_DEFAULT_KICK_LEVEL = "off"
_T = TypeVar("_T")


def normalize_kick_level_name(
    value: object,
    *,
    allowed_levels: Sequence[str] | None = None,
    default: str = _DEFAULT_KICK_LEVEL,
) -> str:
    fallback = str(default).strip().lower() or _DEFAULT_KICK_LEVEL
    if not isinstance(value, str) or not value.strip():
        return fallback
    normalized = value.strip().lower()
    if allowed_levels is not None and normalized not in allowed_levels:
        return fallback
    return normalized


def project_plane_offset(
    *,
    ndim: int,
    axis_a: int,
    axis_b: int,
    plane_offset: Sequence[int],
) -> Coord:
    if ndim < 2:
        raise ValueError("ndim must be >= 2")
    if not (0 <= axis_a < ndim) or not (0 <= axis_b < ndim):
        raise ValueError("rotation axes out of bounds")
    if axis_a == axis_b:
        raise ValueError("rotation axes must be distinct")
    if len(plane_offset) != 2:
        raise ValueError("plane_offset must contain exactly two integers")
    offset_a = int(plane_offset[0])
    offset_b = int(plane_offset[1])
    vector = [0] * ndim
    vector[axis_a] = offset_a
    vector[axis_b] = offset_b
    return tuple(vector)


def kick_candidate_vectors(
    *,
    ndim: int,
    axis_a: int,
    axis_b: int,
    gravity_axis: int,
    plane_offsets: Sequence[PlaneOffset],
) -> tuple[Coord, ...]:
    if not (0 <= gravity_axis < ndim):
        raise ValueError("gravity_axis out of bounds")
    candidates: list[Coord] = []
    seen: set[Coord] = set()
    for plane_offset in plane_offsets:
        vector = project_plane_offset(
            ndim=ndim,
            axis_a=axis_a,
            axis_b=axis_b,
            plane_offset=plane_offset,
        )
        if vector[gravity_axis] > 0:
            continue
        if all(component == 0 for component in vector):
            continue
        if vector in seen:
            continue
        seen.add(vector)
        candidates.append(vector)
    return tuple(candidates)


def resolve_kicked_candidate(
    rotated_piece: _T,
    *,
    candidate_vectors: Sequence[Sequence[int]],
    move_piece: Callable[[_T, Sequence[int]], _T],
    can_place: Callable[[_T], bool],
) -> _T | None:
    if can_place(rotated_piece):
        return rotated_piece
    for vector in candidate_vectors:
        candidate = move_piece(rotated_piece, vector)
        if can_place(candidate):
            return candidate
    return None


def resolve_kicked_piece_2d(
    rotated_piece: _T,
    *,
    candidate_vectors: Sequence[Sequence[int]],
    move_piece: Callable[[_T, int, int], _T],
    can_place: Callable[[_T], bool],
) -> _T | None:
    def _move(piece: _T, vector: Sequence[int]) -> _T:
        if len(vector) != 2:
            raise ValueError("2D kick vectors must have length 2")
        return move_piece(piece, int(vector[0]), int(vector[1]))

    return resolve_kicked_candidate(
        rotated_piece,
        candidate_vectors=candidate_vectors,
        move_piece=_move,
        can_place=can_place,
    )


def resolve_kicked_piece_nd(
    rotated_piece: _T,
    *,
    candidate_vectors: Sequence[Sequence[int]],
    move_piece: Callable[[_T, Sequence[int]], _T],
    can_place: Callable[[_T], bool],
) -> _T | None:
    return resolve_kicked_candidate(
        rotated_piece,
        candidate_vectors=candidate_vectors,
        move_piece=move_piece,
        can_place=can_place,
    )


def resolve_rotated_piece(
    rotated_piece: _T,
    *,
    ndim: int,
    axis_a: int,
    axis_b: int,
    gravity_axis: int,
    kick_level: str,
    plane_offsets_for_level: Callable[[str], Sequence[PlaneOffset]],
    move_piece: Callable[[_T, Sequence[int]], _T],
    can_place: Callable[[_T], bool],
) -> _T | None:
    plane_offsets = tuple(plane_offsets_for_level(kick_level))
    if not plane_offsets:
        return rotated_piece if can_place(rotated_piece) else None
    return resolve_kicked_candidate(
        rotated_piece,
        candidate_vectors=kick_candidate_vectors(
            ndim=ndim,
            axis_a=axis_a,
            axis_b=axis_b,
            gravity_axis=gravity_axis,
            plane_offsets=plane_offsets,
        ),
        move_piece=move_piece,
        can_place=can_place,
    )


__all__ = [
    "PlaneOffset",
    "kick_candidate_vectors",
    "normalize_kick_level_name",
    "project_plane_offset",
    "resolve_kicked_candidate",
    "resolve_kicked_piece_2d",
    "resolve_kicked_piece_nd",
    "resolve_rotated_piece",
]
