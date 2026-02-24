from __future__ import annotations

from functools import reduce
import operator
from typing import Dict, List

from ..model.types import Coord


def full_levels(dims: Coord, cells: Dict[Coord, int], gravity_axis: int) -> List[int]:
    n_dims = len(dims)
    if not (0 <= gravity_axis < n_dims):
        raise ValueError("Invalid gravity_axis")

    if not cells:
        return []

    axis_size = dims[gravity_axis]
    other_dims = [dims[i] for i in range(n_dims) if i != gravity_axis]
    max_per_level = reduce(operator.mul, other_dims, 1) if other_dims else 1
    if max_per_level <= 0:
        return []

    level_counts = [0] * axis_size
    for coord in cells.keys():
        level_counts[coord[gravity_axis]] += 1

    return [level for level, count in enumerate(level_counts) if count == max_per_level]


def clear_planes(
    dims: Coord,
    cells: Dict[Coord, int],
    gravity_axis: int,
) -> tuple[int, Dict[Coord, int], List[int], List[tuple[Coord, int]]]:
    n_dims = len(dims)
    if not (0 <= gravity_axis < n_dims):
        raise ValueError("Invalid gravity_axis")

    if not cells:
        return 0, {}, [], []

    axis_size = dims[gravity_axis]
    levels = full_levels(dims, cells, gravity_axis)
    if not levels:
        return 0, dict(cells), [], []

    levels = sorted(set(levels))
    full_set = set(levels)
    cleared_cells = [
        (coord, cell_id)
        for coord, cell_id in cells.items()
        if coord[gravity_axis] in full_set
    ]

    shift = [0] * axis_size
    for g_val in range(axis_size):
        shift[g_val] = sum(1 for lvl in levels if lvl > g_val)

    new_cells: Dict[Coord, int] = {}
    for coord, cell_id in cells.items():
        g_val = coord[gravity_axis]
        if g_val in full_set:
            continue
        new_g = g_val + shift[g_val]
        if new_g >= axis_size:
            continue
        new_coord = list(coord)
        new_coord[gravity_axis] = new_g
        new_cells[tuple(new_coord)] = cell_id

    return len(levels), new_cells, list(levels), cleared_cells


__all__ = ["clear_planes", "full_levels"]
