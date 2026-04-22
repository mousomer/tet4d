from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoardBoundaryPlane:
    axis: int
    side: str
    coordinate: float


def board_boundary_coordinate(*, dims: tuple[int, ...], axis: int, side: str) -> float:
    if side == "-":
        return -0.5
    return float(dims[int(axis)]) - 0.5


def board_boundary_limits(dims: tuple[int, ...]) -> tuple[tuple[float, float], ...]:
    return tuple(
        (
            board_boundary_coordinate(dims=dims, axis=axis, side="-"),
            board_boundary_coordinate(dims=dims, axis=axis, side="+"),
        )
        for axis in range(len(dims))
    )


def board_boundary_planes(dims: tuple[int, ...]) -> tuple[BoardBoundaryPlane, ...]:
    planes: list[BoardBoundaryPlane] = []
    for axis in range(len(dims)):
        planes.append(
            BoardBoundaryPlane(
                axis=axis,
                side="-",
                coordinate=board_boundary_coordinate(dims=dims, axis=axis, side="-"),
            )
        )
        planes.append(
            BoardBoundaryPlane(
                axis=axis,
                side="+",
                coordinate=board_boundary_coordinate(dims=dims, axis=axis, side="+"),
            )
        )
    return tuple(planes)
