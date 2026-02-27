from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.ui.pygame.projection3d import (
    Cell3,
    Face,
    Point2,
    build_cube_faces,
    draw_projected_lattice,
    fit_orthographic_zoom,
    orthographic_point,
    perspective_point,
    projection_cache_key,
    projective_point,
    raw_to_world,
    transform_point,
)


@dataclass(frozen=True)
class ProjectionParams3D:
    projection_name: str
    yaw_deg: float
    pitch_deg: float
    zoom: float
    cam_dist: float
    projective_strength: float
    projective_bias: float


def transform_raw_point(
    raw: Cell3 | tuple[float, float, float],
    dims: Cell3,
    params: ProjectionParams3D,
) -> tuple[float, float, float]:
    world = raw_to_world(raw, dims)
    return transform_point(world, params.yaw_deg, params.pitch_deg)


def project_point(
    trans: tuple[float, float, float],
    params: ProjectionParams3D,
    center_px: Point2,
) -> Point2 | None:
    if params.projection_name == "ORTHOGRAPHIC":
        return orthographic_point(trans, center_px, params.zoom)
    if params.projection_name == "PERSPECTIVE":
        return perspective_point(trans, center_px, params.zoom, params.cam_dist)
    return projective_point(
        trans,
        center_px,
        params.zoom,
        params.projective_strength,
        params.projective_bias,
    )


def project_raw_point(
    raw: tuple[float, float, float],
    dims: Cell3,
    params: ProjectionParams3D,
    center_px: Point2,
) -> Point2 | None:
    return project_point(transform_raw_point(raw, dims, params), params, center_px)


def draw_board_grid(
    surface: pygame.Surface,
    dims: Cell3,
    params: ProjectionParams3D,
    board_rect: pygame.Rect,
    *,
    inner_color: tuple[int, int, int],
    frame_color: tuple[int, int, int],
    frame_width: int,
) -> None:
    center_px = (board_rect.centerx, board_rect.centery)
    cache_key = projection_cache_key(
        prefix="3d-full",
        dims=dims,
        center_px=center_px,
        yaw_deg=params.yaw_deg,
        pitch_deg=params.pitch_deg,
        zoom=params.zoom,
        extras=(
            params.projection_name,
            round(params.cam_dist, 3),
            round(params.projective_strength, 4),
            round(params.projective_bias, 4),
        ),
    )
    draw_projected_lattice(
        surface,
        dims,
        lambda raw: project_raw_point(raw, dims, params, center_px),
        inner_color=inner_color,
        frame_color=frame_color,
        frame_width=frame_width,
        cache_key=cache_key,
    )


def build_cell_faces(
    *,
    cell: Cell3,
    color: tuple[int, int, int],
    params: ProjectionParams3D,
    center_px: Point2,
    dims: Cell3,
    active: bool,
) -> list[Face]:
    return build_cube_faces(
        cell=cell,
        color=color,
        project_raw=lambda raw: project_raw_point(raw, dims, params, center_px),
        transform_raw=lambda raw: transform_raw_point(raw, dims, params),
        active=active,
    )


def fit_orthographic_zoom_for_rect(
    *,
    dims: tuple[int, int, int],
    yaw_deg: float,
    pitch_deg: float,
    rect: pygame.Rect,
    pad_x: int = 18,
    pad_y: int = 18,
    min_zoom: float = 12.0,
    max_zoom: float = 140.0,
) -> float:
    return fit_orthographic_zoom(
        dims=dims,
        yaw_deg=yaw_deg,
        pitch_deg=pitch_deg,
        rect=rect,
        pad_x=pad_x,
        pad_y=pad_y,
        min_zoom=min_zoom,
        max_zoom=max_zoom,
    )
