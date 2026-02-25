from __future__ import annotations

import random
from typing import Iterable, Sequence

from .pieces2d import DEFAULT_RANDOM_CELL_COUNT_2D, get_piece_bag_2d
from .pieces_nd import (
    DEFAULT_RANDOM_CELL_COUNT_3D,
    DEFAULT_RANDOM_CELL_COUNT_4D,
    get_piece_shapes_nd,
)


def _max_radius(blocks: Iterable[Sequence[int]]) -> int:
    radius = 0
    for block in blocks:
        radius = max(radius, max(abs(int(v)) for v in block))
    return radius


def _span_by_axis(blocks: Iterable[Sequence[int]], ndim: int) -> list[int]:
    mins = [10**9] * ndim
    maxs = [-(10**9)] * ndim
    count = 0
    for block in blocks:
        count += 1
        for axis in range(ndim):
            value = int(block[axis])
            mins[axis] = min(mins[axis], value)
            maxs[axis] = max(maxs[axis], value)
    if count == 0:
        return [1] * ndim
    return [maxs[axis] - mins[axis] + 1 for axis in range(ndim)]


def _minimum_uniform_axis_size(
    all_blocks: Iterable[Sequence[int]],
    *,
    ndim: int,
) -> int:
    blocks = list(all_blocks)
    if not blocks:
        return 8
    spans = _span_by_axis(blocks, ndim)
    radius = _max_radius(blocks)
    span_limit = max(spans)
    return max(8, span_limit + 2, (2 * radius) + 3)


def minimal_exploration_dims_2d(
    piece_set_id: str,
    *,
    random_cell_count: int = DEFAULT_RANDOM_CELL_COUNT_2D,
) -> tuple[int, int]:
    shapes = get_piece_bag_2d(
        piece_set_id,
        rng=random.Random(0),
        random_cell_count=random_cell_count,
    )
    axis = _minimum_uniform_axis_size(
        (block for shape in shapes for block in shape.blocks),
        ndim=2,
    )
    return axis, axis


def _default_random_count_for_ndim(ndim: int) -> int:
    if ndim <= 3:
        return DEFAULT_RANDOM_CELL_COUNT_3D
    return DEFAULT_RANDOM_CELL_COUNT_4D


def minimal_exploration_dims_nd(
    ndim: int,
    piece_set_id: str,
    *,
    random_cell_count: int | None = None,
) -> tuple[int, ...]:
    count = (
        _default_random_count_for_ndim(ndim)
        if random_cell_count is None
        else random_cell_count
    )
    shapes = get_piece_shapes_nd(
        ndim,
        piece_set_id=piece_set_id,
        random_cell_count=count,
        rng=random.Random(0),
    )
    axis = _minimum_uniform_axis_size(
        (block for shape in shapes for block in shape.blocks),
        ndim=ndim,
    )
    return tuple(axis for _ in range(ndim))
