from __future__ import annotations


def coord_from_column(
    column: tuple[int, ...],
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
    gravity_value: int,
    ndim: int,
) -> tuple[int, ...]:
    coord = [0] * ndim
    coord[gravity_axis] = gravity_value
    for idx, axis in enumerate(lateral_axes):
        coord[axis] = column[idx]
    return tuple(coord)
