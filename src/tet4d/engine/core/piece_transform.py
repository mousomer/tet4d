from __future__ import annotations

from collections import deque
from functools import lru_cache
from typing import Iterable, Sequence, TypeAlias

Coord2D: TypeAlias = tuple[int, int]
CoordND: TypeAlias = tuple[int, ...]
Blocks2D: TypeAlias = tuple[Coord2D, ...]
BlocksND: TypeAlias = tuple[CoordND, ...]

_QUARTER_TURNS = 4
_MAX_3D_ORIENTATION_DEPTH = 7
_MAX_4D_ORIENTATION_DEPTH = 6
_MAX_3D_ORIENTATION_COUNT = 96
_MAX_4D_ORIENTATION_COUNT = 180


def _validate_ndim(ndim: int) -> None:
    if ndim < 2:
        raise ValueError("ndim must be >= 2")


def _coerce_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = tuple(tuple(int(value) for value in block) for block in blocks)
    if not coords:
        return tuple()
    ndim = len(coords[0])
    for coord in coords:
        if len(coord) != ndim:
            raise ValueError("inconsistent coordinate dimensions")
    return coords


def _coerce_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_nd(blocks)
    for coord in coords:
        if len(coord) != 2:
            raise ValueError("2D blocks must contain exactly two coordinates")
    return tuple((coord[0], coord[1]) for coord in coords)


@lru_cache(maxsize=8192)
def _block_axis_bounds_cached(blocks: BlocksND) -> tuple[CoordND, CoordND]:
    first = blocks[0]
    mins = [int(value) for value in first]
    maxs = [int(value) for value in first]
    for coord in blocks[1:]:
        for axis, value in enumerate(coord):
            if value < mins[axis]:
                mins[axis] = int(value)
            elif value > maxs[axis]:
                maxs[axis] = int(value)
    return tuple(mins), tuple(maxs)


def block_axis_bounds(blocks: Iterable[Sequence[int]]) -> tuple[CoordND, CoordND]:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    return _block_axis_bounds_cached(coords)


@lru_cache(maxsize=8192)
def _canonicalize_blocks_nd_cached(blocks: BlocksND) -> BlocksND:
    return tuple(sorted(blocks))


def canonicalize_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        return tuple()
    return _canonicalize_blocks_nd_cached(coords)


def canonicalize_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    if not coords:
        return tuple()
    return tuple((coord[0], coord[1]) for coord in _canonicalize_blocks_nd_cached(coords))


def _axis_center_map(coords: BlocksND, *, axes: Iterable[int]) -> dict[int, int]:
    mins, maxs = _block_axis_bounds_cached(coords)
    ndim = len(coords[0])
    centers: dict[int, int] = {}
    for axis in axes:
        if not (0 <= axis < ndim):
            raise ValueError("normalization axis out of bounds")
        centers[axis] = (mins[axis] + maxs[axis]) // 2
    return centers


def _normalize_axes_preserve_order(
    coords: BlocksND,
    *,
    axes: Iterable[int],
) -> BlocksND:
    centers = _axis_center_map(coords, axes=axes)
    ndim = len(coords[0])
    return tuple(
        tuple(
            coord[axis] - centers[axis] if axis in centers else coord[axis]
            for axis in range(ndim)
        )
        for coord in coords
    )


def _normalize_axes_2d_preserve_order(
    coords: Blocks2D,
    *,
    axes: Iterable[int],
) -> Blocks2D:
    normalized = _normalize_axes_preserve_order(coords, axes=axes)
    return tuple((coord[0], coord[1]) for coord in normalized)


def normalize_blocks_2d(blocks: Iterable[Sequence[int]]) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    return canonicalize_blocks_2d(
        _normalize_axes_2d_preserve_order(coords, axes=(0, 1))
    )


def normalize_blocks_nd(blocks: Iterable[Sequence[int]]) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        raise ValueError("piece must contain at least one block")
    ndim = len(coords[0])
    _validate_ndim(ndim)
    return canonicalize_blocks_nd(_normalize_axes_preserve_order(coords, axes=range(ndim)))


def rotate_point_2d(x: int, y: int, steps_cw: int) -> Coord2D:
    steps = steps_cw % _QUARTER_TURNS
    if steps == 0:
        return x, y
    if steps == 1:
        return y, -x
    if steps == 2:
        return -x, -y
    return -y, x


@lru_cache(maxsize=4096)
def _rotate_blocks_2d_cached(blocks: Blocks2D, steps_cw: int) -> Blocks2D:
    steps = steps_cw % _QUARTER_TURNS
    if not blocks or steps == 0:
        return blocks

    rotated = blocks
    for _ in range(steps):
        (min_x, min_y), (max_x, _max_y) = _block_axis_bounds_cached(rotated)
        span_x = max_x - min_x + 1
        raw: list[Coord2D] = []
        raw_min_x = 0
        raw_max_x = 0
        raw_min_y = 0
        raw_max_y = 0
        for idx, (x, y) in enumerate(rotated):
            next_coord = (
                min_x + (y - min_y),
                min_y + (span_x - 1 - (x - min_x)),
            )
            raw.append(next_coord)
            if idx == 0:
                raw_min_x = raw_max_x = next_coord[0]
                raw_min_y = raw_max_y = next_coord[1]
                continue
            raw_min_x = min(raw_min_x, next_coord[0])
            raw_max_x = max(raw_max_x, next_coord[0])
            raw_min_y = min(raw_min_y, next_coord[1])
            raw_max_y = max(raw_max_y, next_coord[1])
        center_x = (raw_min_x + raw_max_x) // 2
        center_y = (raw_min_y + raw_max_y) // 2
        rotated = tuple((x - center_x, y - center_y) for x, y in raw)
    return rotated


def rotate_blocks_2d(blocks: Iterable[Sequence[int]], steps_cw: int) -> Blocks2D:
    coords = _coerce_blocks_2d(blocks)
    return _rotate_blocks_2d_cached(coords, steps_cw % _QUARTER_TURNS)


def rotate_point_nd(
    point: Sequence[int],
    axis_a: int,
    axis_b: int,
    steps_cw: int,
) -> CoordND:
    ndim = len(point)
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")

    steps = steps_cw % _QUARTER_TURNS
    coords = [int(value) for value in point]
    a_val = coords[axis_a]
    b_val = coords[axis_b]

    if steps == 0:
        return tuple(coords)
    if steps == 1:
        coords[axis_a] = b_val
        coords[axis_b] = -a_val
        return tuple(coords)
    if steps == 2:
        coords[axis_a] = -a_val
        coords[axis_b] = -b_val
        return tuple(coords)

    coords[axis_a] = -b_val
    coords[axis_b] = a_val
    return tuple(coords)


@lru_cache(maxsize=8192)
def _rotate_blocks_nd_cached(
    blocks: BlocksND,
    axis_a: int,
    axis_b: int,
    steps_cw: int,
) -> BlocksND:
    steps = steps_cw % _QUARTER_TURNS
    if not blocks or steps == 0:
        return blocks

    ndim = len(blocks[0])
    rotated = blocks
    for _ in range(steps):
        mins, maxs = _block_axis_bounds_cached(rotated)
        min_a = mins[axis_a]
        min_b = mins[axis_b]
        span_a = maxs[axis_a] - min_a + 1
        raw: list[CoordND] = []
        raw_min_a = 0
        raw_max_a = 0
        raw_min_b = 0
        raw_max_b = 0
        for idx, coord in enumerate(rotated):
            next_a = min_a + (coord[axis_b] - min_b)
            next_b = min_b + (span_a - 1 - (coord[axis_a] - min_a))
            next_coord = tuple(
                next_a
                if axis == axis_a
                else next_b
                if axis == axis_b
                else coord[axis]
                for axis in range(ndim)
            )
            raw.append(next_coord)
            if idx == 0:
                raw_min_a = raw_max_a = next_a
                raw_min_b = raw_max_b = next_b
                continue
            raw_min_a = min(raw_min_a, next_a)
            raw_max_a = max(raw_max_a, next_a)
            raw_min_b = min(raw_min_b, next_b)
            raw_max_b = max(raw_max_b, next_b)
        center_a = (raw_min_a + raw_max_a) // 2
        center_b = (raw_min_b + raw_max_b) // 2
        rotated = tuple(
            tuple(
                value - center_a
                if axis == axis_a
                else value - center_b
                if axis == axis_b
                else value
                for axis, value in enumerate(coord)
            )
            for coord in raw
        )
    return rotated


def rotate_blocks_nd(
    blocks: Iterable[Sequence[int]],
    axis_a: int,
    axis_b: int,
    steps_cw: int,
) -> BlocksND:
    coords = _coerce_blocks_nd(blocks)
    if not coords:
        return tuple()
    ndim = len(coords[0])
    _validate_ndim(ndim)
    if axis_a == axis_b:
        raise ValueError("rotation axes must be different")
    if not (0 <= axis_a < ndim and 0 <= axis_b < ndim):
        raise ValueError("rotation axis out of bounds")
    return _rotate_blocks_nd_cached(coords, axis_a, axis_b, steps_cw % _QUARTER_TURNS)


@lru_cache(maxsize=32)
def rotation_planes_nd(ndim: int, gravity_axis: int) -> tuple[tuple[int, int], ...]:
    if ndim == 3:
        extra = [axis for axis in range(ndim) if axis != 0 and axis != gravity_axis]
        z_axis = extra[0] if extra else 2
        return (
            (0, gravity_axis),
            (0, z_axis),
            (gravity_axis, z_axis),
        )
    pairs: list[tuple[int, int]] = []
    for axis_a in range(ndim):
        for axis_b in range(axis_a + 1, ndim):
            pairs.append((axis_a, axis_b))
    return tuple(pairs)


@lru_cache(maxsize=512)
def enumerate_orientations_nd(
    start_blocks: BlocksND,
    ndim: int,
    gravity_axis: int,
) -> tuple[BlocksND, ...]:
    planes = rotation_planes_nd(ndim, gravity_axis)
    max_depth = _MAX_3D_ORIENTATION_DEPTH if ndim == 3 else _MAX_4D_ORIENTATION_DEPTH
    max_orientations = (
        _MAX_3D_ORIENTATION_COUNT if ndim == 3 else _MAX_4D_ORIENTATION_COUNT
    )

    queue: deque[tuple[BlocksND, int]] = deque([(start_blocks, 0)])
    seen: set[BlocksND] = {start_blocks}
    ordered: list[BlocksND] = [start_blocks]

    while queue and len(seen) < max_orientations:
        blocks, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for axis_a, axis_b in planes:
            for step in (1, -1):
                rotated = canonicalize_blocks_nd(
                    rotate_blocks_nd(
                        blocks,
                        axis_a=axis_a,
                        axis_b=axis_b,
                        steps_cw=step,
                    )
                )
                if rotated in seen:
                    continue
                seen.add(rotated)
                ordered.append(rotated)
                queue.append((rotated, depth + 1))
                if len(seen) >= max_orientations:
                    break
            if len(seen) >= max_orientations:
                break
    return tuple(ordered)


__all__ = [
    "Blocks2D",
    "BlocksND",
    "Coord2D",
    "CoordND",
    "block_axis_bounds",
    "canonicalize_blocks_2d",
    "canonicalize_blocks_nd",
    "enumerate_orientations_nd",
    "normalize_blocks_2d",
    "normalize_blocks_nd",
    "rotate_blocks_2d",
    "rotate_blocks_nd",
    "rotate_point_2d",
    "rotate_point_nd",
    "rotation_planes_nd",
]