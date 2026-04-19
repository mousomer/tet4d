from __future__ import annotations

from dataclasses import dataclass
import math

import pygame

from .controller import LockedCellExplosionController

_BG = (16, 20, 40)
_FRAME = (82, 96, 132)
_GRID = (64, 78, 110)
_LABEL = (216, 224, 244)


@dataclass(frozen=True)
class _RenderContext4D:
    basis_axis_map: tuple[tuple[int, int], ...]
    layer_count: int
    yaw_deg: float
    pitch_deg: float
    zoom: float
    xw_deg: float
    zw_deg: float
    layer_axis_label: str
    layer_axis: int
    layer_sign: int


def _rotate_xy(point: tuple[float, float], angle_deg: float) -> tuple[float, float]:
    radians = math.radians(float(angle_deg))
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        (point[0] * cosine) - (point[1] * sine),
        (point[0] * sine) + (point[1] * cosine),
    )


def _draw_native_board_2d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
) -> None:
    from tet4d.ui.pygame.render.gfx_game import color_for_cell

    width_cells = max(1, int(board_dims[0]))
    height_cells = max(1, int(board_dims[1]))
    padding = 12
    usable_width = max(32.0, float(rect.width - (padding * 2)))
    usable_height = max(32.0, float(rect.height - (padding * 2)))
    cell_size = max(6.0, min(usable_width / width_cells, usable_height / height_cells))
    board_width = cell_size * width_cells
    board_height = cell_size * height_cells
    board_rect = pygame.Rect(
        int(round(rect.centerx - (board_width * 0.5))),
        int(round(rect.centery - (board_height * 0.5))),
        int(round(board_width)),
        int(round(board_height)),
    )
    pygame.draw.rect(surface, _BG, board_rect)
    pygame.draw.rect(surface, _FRAME, board_rect, 2)
    for index in range(1, width_cells):
        x = int(round(board_rect.x + (index * cell_size)))
        pygame.draw.line(surface, _GRID, (x, board_rect.y), (x, board_rect.bottom), 1)
    for index in range(1, height_cells):
        y = int(round(board_rect.y + (index * cell_size)))
        pygame.draw.line(surface, _GRID, (board_rect.x, y), (board_rect.right, y), 1)
    if controller is None:
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for particle in controller.render_particles(render_context=None):
        center_x = board_rect.x + ((float(particle.render_position[0]) + 0.5) * cell_size)
        center_y = board_rect.y + ((float(particle.render_position[1]) + 0.5) * cell_size)
        corners = []
        for local in ((-0.42, -0.42), (0.42, -0.42), (0.42, 0.42), (-0.42, 0.42)):
            rotated = _rotate_xy(local, float(particle.rotation_deg[2]))
            corners.append(
                (
                    center_x + (rotated[0] * cell_size),
                    center_y + (rotated[1] * cell_size),
                )
            )
        color = color_for_cell(int(particle.color_id))
        pygame.draw.polygon(overlay, (0, 0, 0, 90), tuple((x + 2.0, y + 2.0) for x, y in corners))
        pygame.draw.polygon(overlay, (*color, 244), corners)
        pygame.draw.polygon(overlay, (255, 255, 255, 210), corners, 2)
    surface.blit(overlay, (0, 0))


def _draw_native_board_3d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
    camera_3d,
) -> None:
    from tet4d.ui.pygame.front3d_render import Camera3D, color_for_cell_3d
    from tet4d.ui.pygame.render.front3d_cell_render import draw_cells
    from tet4d.ui.pygame.render.front3d_projection_helpers import (
        ProjectionParams3D,
        build_cell_faces,
        draw_board_grid,
        fit_orthographic_zoom_for_rect,
    )

    camera = camera_3d if isinstance(camera_3d, Camera3D) else Camera3D()
    dims = (
        int(board_dims[0]),
        int(board_dims[1]),
        int(board_dims[2]),
    )
    board_rect = rect.inflate(-12, -12)
    pygame.draw.rect(surface, _BG, board_rect, border_radius=10)
    if camera.projection.name == "ORTHOGRAPHIC":
        camera.zoom = fit_orthographic_zoom_for_rect(
            dims=dims,
            yaw_deg=float(camera.yaw_deg),
            pitch_deg=float(camera.pitch_deg),
            rect=board_rect,
            pad_x=18,
            pad_y=18,
            min_zoom=12.0,
            max_zoom=140.0,
        )
    params = ProjectionParams3D(
        projection_name=camera.projection.name,
        yaw_deg=float(camera.yaw_deg),
        pitch_deg=float(camera.pitch_deg),
        zoom=float(camera.zoom),
        cam_dist=float(camera.cam_dist),
        projective_strength=float(camera.projective_strength),
        projective_bias=float(camera.projective_bias),
    )
    draw_board_grid(
        surface,
        dims,
        params,
        board_rect,
        inner_color=(52, 64, 95),
        frame_color=(75, 90, 125),
        frame_width=2,
    )
    if controller is None:
        return
    center_px = (board_rect.centerx, board_rect.centery)
    visible_cells = [
        (
            tuple(float(value) for value in particle.render_position),
            int(particle.color_id),
            True,
            False,
        )
        for particle in controller.render_particles(render_context=None)
    ]
    draw_cells(
        surface,
        cells=visible_cells,
        build_faces_fn=lambda coord, color, active: build_cell_faces(
            cell=coord,
            color=color,
            params=params,
            center_px=center_px,
            dims=dims,
            active=active,
        ),
        color_for_cell_fn=color_for_cell_3d,
        overlay_transparency=0.14,
        assist_overlay_opacity_scale=0.3,
    )


def _render_context_for_4d(view, dims4: tuple[int, int, int, int]) -> _RenderContext4D:
    from tet4d.ui.pygame.front4d_render import _basis_for_view

    basis = _basis_for_view(view, dims4)
    return _RenderContext4D(
        yaw_deg=float(view.yaw_deg),
        pitch_deg=float(view.pitch_deg),
        zoom=float(view.zoom_scale),
        xw_deg=float(view.xw_deg),
        zw_deg=float(view.zw_deg),
        layer_axis_label=str(basis.layer_axis_label),
        layer_count=int(basis.layer_count),
        basis_axis_map=tuple(tuple(pair) for pair in basis.axis_map),
        layer_axis=int(basis.layer_axis),
        layer_sign=int(basis.layer_sign),
    )


def _draw_native_board_4d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fonts,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
    view_4d,
) -> None:
    from tet4d.ui.pygame.front4d_render import (
        COLOR_MAP,
        LayerView3D,
        _basis_for_view,
        _draw_board_grid,
        _fit_zoom,
        _layer_rects_by_layer,
        _project_raw_point,
        _transform_raw_point,
        color_for_cell,
    )
    from tet4d.ui.pygame.projection3d import build_oriented_cube_faces

    view = view_4d if isinstance(view_4d, LayerView3D) else LayerView3D()
    dims4 = (
        int(board_dims[0]),
        int(board_dims[1]),
        int(board_dims[2]),
        int(board_dims[3]),
    )
    basis = _basis_for_view(view, dims4)
    layer_rects = _layer_rects_by_layer(area=rect, layer_count=max(1, basis.layer_count))
    render_context = _render_context_for_4d(view, dims4)
    rendered_particles = (
        tuple()
        if controller is None
        else controller.render_particles(render_context=render_context)
    )
    for layer_index in range(max(1, basis.layer_count)):
        layer_rect = layer_rects.get(layer_index)
        if layer_rect is None:
            continue
        pygame.draw.rect(surface, _BG, layer_rect, border_radius=8)
        pygame.draw.rect(surface, _FRAME, layer_rect, 2, border_radius=8)
        label = fonts.hint_font.render(
            f"{basis.layer_axis_label} = {layer_index}",
            True,
            _LABEL,
        )
        surface.blit(label, (layer_rect.x + 8, layer_rect.y + 6))
        draw_rect = pygame.Rect(
            layer_rect.x + 6,
            layer_rect.y + 24,
            layer_rect.width - 12,
            layer_rect.height - 30,
        )
        zoom = _fit_zoom(basis.dims3, view, draw_rect) * max(0.5, float(view.zoom_scale))
        zoom = max(8.0, min(170.0, zoom))
        _draw_board_grid(
            surface,
            basis.dims3,
            dims4,
            layer_index,
            basis,
            view,
            draw_rect,
            zoom,
        )
        if controller is None:
            continue
        center_px = (draw_rect.centerx, draw_rect.centery)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        faces: list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]] = []
        for particle in rendered_particles:
            layer_weight = next(
                (
                    float(weight)
                    for candidate_layer, weight in particle.layer_weights
                    if int(candidate_layer) == layer_index
                ),
                0.0,
            )
            if layer_weight <= 0.0:
                continue
            particle_faces = build_oriented_cube_faces(
                center=tuple(float(value) for value in particle.render_position),
                color=color_for_cell(int(particle.color_id), COLOR_MAP),
                project_raw=lambda raw: _project_raw_point(
                    raw,
                    basis.dims3,
                    view,
                    center_px,
                    zoom,
                ),
                transform_raw=lambda raw: _transform_raw_point(raw, basis.dims3, view),
                active=True,
                rotation_deg=tuple(float(value) for value in particle.rotation_deg),
            )
            faces.extend(
                (depth, polygon, color, min(1.0, float(particle.alpha) * layer_weight))
                for depth, polygon, color, _active in particle_faces
            )
        faces.sort(key=lambda item: item[0], reverse=True)
        for _depth, polygon, color, alpha in faces:
            fill_alpha = max(0, min(255, int(round(255 * alpha))))
            outline_alpha = max(0, min(255, int(round(220 * alpha))))
            pygame.draw.polygon(overlay, (*color, fill_alpha), polygon)
            pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), polygon, 2)
        surface.blit(overlay, (0, 0))


def draw_native_board_view(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fonts,
    controller: LockedCellExplosionController | None,
    dimension: int,
    board_dims: tuple[int, ...],
    camera_3d=None,
    view_4d=None,
) -> None:
    if int(dimension) == 2:
        _draw_native_board_2d(
            surface,
            rect=rect,
            controller=controller,
            board_dims=board_dims,
        )
        return
    if int(dimension) == 3:
        _draw_native_board_3d(
            surface,
            rect=rect,
            controller=controller,
            board_dims=board_dims,
            camera_3d=camera_3d,
        )
        return
    _draw_native_board_4d(
        surface,
        rect=rect,
        fonts=fonts,
        controller=controller,
        board_dims=board_dims,
        view_4d=view_4d,
    )


__all__ = [
    "draw_native_board_view",
]
