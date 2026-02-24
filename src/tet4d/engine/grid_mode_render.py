from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

import pygame

from .projection3d import draw_projected_box_edges, draw_projected_box_shadow, draw_projected_helper_lattice
from .view_modes import GridMode


MarkSet3: TypeAlias = tuple[set[int], set[int], set[int]]


def draw_projected_grid_mode(
    *,
    surface: pygame.Surface,
    dims: tuple[int, int, int],
    grid_mode: GridMode,
    draw_full_grid: Callable[[], None],
    project_raw: Callable[[tuple[float, float, float]], tuple[float, float] | None],
    transform_raw: Callable[[tuple[float, float, float]], tuple[float, float, float]],
    helper_marks: MarkSet3 | None = None,
    helper_cache_key: object | None = None,
    frame_color: tuple[int, int, int] = (75, 90, 125),
    inner_color: tuple[int, int, int] = (52, 64, 95),
    frame_width: int = 2,
    edge_width: int = 2,
) -> None:
    if grid_mode == GridMode.FULL:
        draw_full_grid()
        return

    if grid_mode == GridMode.EDGE:
        draw_projected_box_edges(
            surface,
            dims,
            project_raw,
            edge_color=frame_color,
            edge_width=edge_width,
        )
        return

    draw_projected_box_shadow(
        surface,
        dims,
        project_raw=project_raw,
        transform_raw=transform_raw,
    )
    if grid_mode != GridMode.HELPER:
        return

    x_marks, y_marks, z_marks = helper_marks if helper_marks is not None else (set(), set(), set())
    draw_projected_helper_lattice(
        surface,
        dims,
        project_raw,
        x_marks=x_marks,
        y_marks=y_marks,
        z_marks=z_marks,
        inner_color=inner_color,
        frame_color=frame_color,
        frame_width=frame_width,
        cache_key=helper_cache_key,
    )
