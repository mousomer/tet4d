from __future__ import annotations

from typing import Callable

import pygame

from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame.render.active_piece_projection_guides import (
    draw_boundary_projection_faces,
    draw_boundary_projection_segments_2d,
)
from tet4d.ui.pygame.render.grid_mode_render import (
    draw_projected_grid_mode,
    draw_projected_line_buckets,
)
from tet4d.ui.pygame.render.projected_occlusion import resolve_board_line_occlusion
from tet4d.ui.pygame.render.w_movement_animation import (
    layer_transition_scale_for_distance,
)

_BOARD_BG = (16, 24, 52, 170)
_BOARD_FRAME = (86, 104, 146)
_BOARD_SHADOW_STRIPE = (130, 150, 190)
_GRID_COLOR_2D = (40, 40, 80)
_W_MOVEMENT_STYLES = ("fade", "box_size")


def _draw_board_shadow_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
) -> None:
    shadow = pygame.Surface(board_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow, _BOARD_BG, shadow.get_rect())
    step = max(6, int(cell_size))
    for y in range(0, board_rect.height, step):
        alpha = 20 if (y // step) % 2 == 0 else 10
        pygame.draw.line(
            shadow,
            (*_BOARD_SHADOW_STRIPE, alpha),
            (0, y),
            (board_rect.width, y),
            1,
        )
    surface.blit(shadow, board_rect.topleft)
    pygame.draw.rect(surface, _BOARD_FRAME, board_rect, 2)


def _draw_board_edges_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    width_cells: int,
    height_cells: int,
) -> None:
    for index in range(width_cells):
        left = board_rect.x + index * cell_size
        right = left + cell_size
        pygame.draw.line(surface, _GRID_COLOR_2D, (left, board_rect.y), (right, board_rect.y))
        pygame.draw.line(
            surface,
            _GRID_COLOR_2D,
            (left, board_rect.bottom),
            (right, board_rect.bottom),
        )
    for index in range(height_cells):
        top = board_rect.y + index * cell_size
        bottom = top + cell_size
        pygame.draw.line(surface, _GRID_COLOR_2D, (board_rect.x, top), (board_rect.x, bottom))
        pygame.draw.line(
            surface,
            _GRID_COLOR_2D,
            (board_rect.right, top),
            (board_rect.right, bottom),
        )
    pygame.draw.rect(surface, _BOARD_FRAME, board_rect, 2)


def _draw_full_grid_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    width_cells: int,
    height_cells: int,
) -> None:
    for x in range(width_cells + 1):
        x_px = board_rect.x + x * cell_size
        pygame.draw.line(
            surface,
            _GRID_COLOR_2D,
            (x_px, board_rect.y),
            (x_px, board_rect.y + height_cells * cell_size),
        )
    for y in range(height_cells + 1):
        y_px = board_rect.y + y * cell_size
        pygame.draw.line(
            surface,
            _GRID_COLOR_2D,
            (board_rect.x, y_px),
            (board_rect.x + width_cells * cell_size, y_px),
        )


def _draw_helper_grid_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    width_cells: int,
    height_cells: int,
    helper_marks: tuple[set[int], set[int]],
) -> None:
    x_marks, y_marks = helper_marks
    for x in sorted(x_marks):
        if 0 <= x <= width_cells:
            x_px = board_rect.x + x * cell_size
            pygame.draw.line(
                surface,
                _GRID_COLOR_2D,
                (x_px, board_rect.y),
                (x_px, board_rect.bottom),
            )
    for y in sorted(y_marks):
        if 0 <= y <= height_cells:
            y_px = board_rect.y + y * cell_size
            pygame.draw.line(
                surface,
                _GRID_COLOR_2D,
                (board_rect.x, y_px),
                (board_rect.right, y_px),
            )


def _apply_grid_shell_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    width_cells: int,
    height_cells: int,
    grid_mode: GridMode,
) -> None:
    if grid_mode in (
        GridMode.OFF,
        GridMode.SHADOW,
        GridMode.HELPER,
        GridMode.BOTTOM_BOUNDARY,
        GridMode.ALL_BOUNDARIES,
    ):
        _draw_board_shadow_2d(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
        )
    elif grid_mode == GridMode.EDGE:
        _draw_board_edges_2d(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
            width_cells=width_cells,
            height_cells=height_cells,
        )


def draw_gameplay_board_grid_2d(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: int,
    width_cells: int,
    height_cells: int,
    grid_mode: GridMode,
    helper_marks: tuple[set[int], set[int]] | None = None,
) -> None:
    _apply_grid_shell_2d(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        width_cells=width_cells,
        height_cells=height_cells,
        grid_mode=grid_mode,
    )

    if grid_mode == GridMode.FULL:
        _draw_full_grid_2d(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
            width_cells=width_cells,
            height_cells=height_cells,
        )
    elif grid_mode == GridMode.HELPER and helper_marks is not None:
        _draw_helper_grid_2d(
            surface,
            board_rect=board_rect,
            cell_size=cell_size,
            width_cells=width_cells,
            height_cells=height_cells,
            helper_marks=helper_marks,
        )


def draw_gameplay_projection_segments_2d(
    surface: pygame.Surface,
    *,
    segments,
    board_offset: tuple[int, int],
    cell_size: int,
) -> None:
    draw_boundary_projection_segments_2d(
        surface,
        segments=segments,
        board_offset=board_offset,
        cell_size=cell_size,
    )


def draw_gameplay_projected_grid(
    surface: pygame.Surface,
    *,
    dims: tuple[int, int, int],
    grid_mode: GridMode,
    draw_full_grid: Callable[[], None],
    project_raw,
    transform_raw,
    depth_denominator,
    helper_marks: tuple[set[int], set[int], set[int]],
    helper_cache_key=None,
    full_grid_cache_key=None,
    frame_color=(75, 90, 125),
    inner_color=(52, 64, 95),
    frame_width: int = 2,
    edge_width: int = 2,
) -> None:
    draw_projected_grid_mode(
        surface=surface,
        dims=dims,
        grid_mode=grid_mode,
        draw_full_grid=draw_full_grid,
        project_raw=project_raw,
        transform_raw=transform_raw,
        depth_denominator=depth_denominator,
        helper_marks=helper_marks,
        helper_cache_key=helper_cache_key,
        full_grid_cache_key=full_grid_cache_key,
        frame_color=frame_color,
        inner_color=inner_color,
        frame_width=frame_width,
        edge_width=edge_width,
    )


def draw_gameplay_projection_faces(surface: pygame.Surface, *, faces) -> None:
    draw_boundary_projection_faces(surface, faces=faces)


def resolve_and_draw_gameplay_occluded_board_lines(
    surface: pygame.Surface,
    *,
    board_line_primitives,
    active_piece_faces,
    frame_color=(75, 90, 125),
    inner_color=(52, 64, 95),
    frame_width: int = 2,
) -> tuple[tuple, tuple]:
    occlusion_buckets = resolve_board_line_occlusion(
        tuple(board_line_primitives),
        active_piece_faces,
    )
    draw_projected_line_buckets(
        surface=surface,
        fragments=occlusion_buckets.segments_under_piece,
        frame_color=frame_color,
        inner_color=inner_color,
        frame_width=frame_width,
    )
    return (
        occlusion_buckets.segments_under_piece,
        occlusion_buckets.segments_over_piece,
    )


def draw_gameplay_over_piece_board_lines(
    surface: pygame.Surface,
    *,
    fragments,
    frame_color=(75, 90, 125),
    inner_color=(52, 64, 95),
    frame_width: int = 2,
) -> None:
    draw_projected_line_buckets(
        surface=surface,
        fragments=fragments,
        frame_color=frame_color,
        inner_color=inner_color,
        frame_width=frame_width,
    )


def normalize_gameplay_w_movement_style(style: str) -> str:
    normalized = str(style).strip().lower()
    if normalized in _W_MOVEMENT_STYLES:
        return normalized
    return "fade"


def gameplay_w_movement_scale_for_layer(
    *,
    layer_distance: float,
    style: str,
) -> float:
    normalized_style = normalize_gameplay_w_movement_style(style)
    scale = layer_transition_scale_for_distance(layer_distance)
    if normalized_style == "box_size":
        return scale
    return scale
