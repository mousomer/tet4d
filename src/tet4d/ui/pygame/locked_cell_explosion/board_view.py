from __future__ import annotations

from dataclasses import dataclass
import math
from types import SimpleNamespace

import pygame
from tet4d.engine.ui_logic.view_modes import GridMode, ShadowMode
from tet4d.ui.pygame.render.active_piece_projection_guides import (
    build_boundary_projection_face_primitives,
    build_boundary_projection_segments_2d,
    draw_boundary_projection_faces,
    draw_boundary_projection_segments_2d,
)
from tet4d.ui.pygame.render.grid_mode_render import (
    build_projected_grid_primitives,
    draw_projected_grid_mode,
    draw_projected_line_buckets,
)
from tet4d.ui.pygame.render.projected_occlusion import resolve_board_line_occlusion

from .controller import LockedCellExplosionController

_BG = (16, 20, 40)
_FRAME = (82, 96, 132)
_GRID = (64, 78, 110)
_LABEL = (216, 224, 244)
_TRACE_ALPHA = 232
_TRACE_WIDTH = 3


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
    w_movement_animation_style: str


def _rotate_xy(point: tuple[float, float], angle_deg: float) -> tuple[float, float]:
    radians = math.radians(float(angle_deg))
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (
        (point[0] * cosine) - (point[1] * sine),
        (point[0] * sine) + (point[1] * cosine),
    )


def _trace_color(color: tuple[int, int, int], *, alpha: float = 1.0) -> tuple[int, int, int, int]:
    resolved_alpha = max(0, min(255, int(round(_TRACE_ALPHA * max(0.0, min(1.0, alpha))))))
    return (*color, resolved_alpha)


def _trace_width(base_width: float, width_scale: float) -> int:
    return max(2, int(round(max(1.5, base_width) * max(0.85, float(width_scale)))))


def _overlay_color(color: tuple[int, int, int], alpha: float) -> tuple[int, int, int, int]:
    return (*color, max(0, min(255, int(round(255 * max(0.0, min(1.0, alpha)))))))


def _board_center_2d(
    board_rect: pygame.Rect,
    cell_size: float,
    coord: tuple[float, ...],
) -> tuple[float, float]:
    return (
        board_rect.x + ((float(coord[0]) + 0.5) * cell_size),
        board_rect.y + ((float(coord[1]) + 0.5) * cell_size),
    )


def _draw_2d_grid(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: float,
    width_cells: int,
    height_cells: int,
    grid_mode: GridMode,
) -> None:
    pygame.draw.rect(surface, _BG, board_rect)
    pygame.draw.rect(surface, _FRAME, board_rect, 2)
    if grid_mode == GridMode.EDGE:
        for index in range(width_cells):
            left = int(round(board_rect.x + (index * cell_size)))
            right = int(round(board_rect.x + ((index + 1) * cell_size)))
            pygame.draw.line(surface, _GRID, (left, board_rect.y), (right, board_rect.y), 1)
            pygame.draw.line(surface, _GRID, (left, board_rect.bottom), (right, board_rect.bottom), 1)
        for index in range(height_cells):
            top = int(round(board_rect.y + (index * cell_size)))
            bottom = int(round(board_rect.y + ((index + 1) * cell_size)))
            pygame.draw.line(surface, _GRID, (board_rect.x, top), (board_rect.x, bottom), 1)
            pygame.draw.line(surface, _GRID, (board_rect.right, top), (board_rect.right, bottom), 1)
        return
    if grid_mode != GridMode.FULL:
        return
    for index in range(1, width_cells):
        x = int(round(board_rect.x + (index * cell_size)))
        pygame.draw.line(surface, _GRID, (x, board_rect.y), (x, board_rect.bottom), 1)
    for index in range(1, height_cells):
        y = int(round(board_rect.y + (index * cell_size)))
        pygame.draw.line(surface, _GRID, (board_rect.x, y), (board_rect.right, y), 1)


def _draw_2d_shadow_guides(
    surface: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: float,
    dims: tuple[int, int],
    rendered_particles,
    color_for_cell,
    shadow_mode: ShadowMode,
) -> None:
    if shadow_mode == ShadowMode.OFF:
        return
    all_segments = []
    for particle in rendered_particles:
        segments = build_boundary_projection_segments_2d(
            cells=((tuple(float(value) for value in particle.render_position[:2]), 0.82),),
            dims=dims,
            gravity_axis=1,
            grid_mode=GridMode(shadow_mode.value),
            color=color_for_cell(int(particle.color_id)),
        )
        all_segments.extend(segments)
    draw_boundary_projection_segments_2d(
        surface,
        segments=tuple(all_segments),
        board_offset=(board_rect.x, board_rect.y),
        cell_size=max(1, int(round(cell_size))),
    )


def _draw_2d_traces(
    overlay: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: float,
    rendered_particles,
    color_for_cell,
) -> None:
    for particle in rendered_particles:
        color = color_for_cell(int(particle.color_id))
        trail_segments = tuple(getattr(particle, "trail_segments", ()))
        if not trail_segments:
            source = _board_center_2d(
                board_rect,
                cell_size,
                tuple(float(value) for value in getattr(particle, "source_coord", ())[:2]),
            )
            current = _board_center_2d(
                board_rect,
                cell_size,
                tuple(float(value) for value in particle.render_position[:2]),
            )
            pygame.draw.line(
                overlay,
                _trace_color(color),
                source,
                current,
                _TRACE_WIDTH,
            )
            continue
        for segment in trail_segments:
            tail = _board_center_2d(
                board_rect,
                cell_size,
                tuple(float(value) for value in segment.tail_render_position[:2]),
            )
            head = _board_center_2d(
                board_rect,
                cell_size,
                tuple(float(value) for value in segment.head_render_position[:2]),
            )
            pygame.draw.line(
                overlay,
                _trace_color(color, alpha=float(segment.alpha)),
                tail,
                head,
                _trace_width(cell_size * 0.08, float(segment.width)),
            )


def _draw_2d_particles(
    overlay: pygame.Surface,
    *,
    board_rect: pygame.Rect,
    cell_size: float,
    rendered_particles,
    color_for_cell,
) -> None:
    for particle in rendered_particles:
        center_x, center_y = _board_center_2d(
            board_rect,
            cell_size,
            tuple(float(value) for value in particle.render_position[:2]),
        )
        alpha = max(0.0, min(1.0, float(getattr(particle, "alpha", 1.0))))
        scale = max(0.52, float(getattr(particle, "size_scale", 1.0)))
        corners = []
        for local in ((-0.42, -0.42), (0.42, -0.42), (0.42, 0.42), (-0.42, 0.42)):
            rotated = _rotate_xy(local, float(particle.rotation_deg[2]))
            corners.append(
                (
                    center_x + (rotated[0] * cell_size * scale),
                    center_y + (rotated[1] * cell_size * scale),
                )
            )
        color = color_for_cell(int(particle.color_id))
        pygame.draw.polygon(overlay, (0, 0, 0, max(0, min(255, int(round(90 * alpha))))), tuple((x + 2.0, y + 2.0) for x, y in corners))
        pygame.draw.polygon(overlay, (*color, max(0, min(255, int(round(244 * alpha))))), corners)
        pygame.draw.polygon(overlay, (255, 255, 255, max(0, min(255, int(round(210 * alpha))))), corners, 2)


def _draw_shell_preview_2d(
    overlay: pygame.Surface,
    *,
    shell_preview,
    board_rect: pygame.Rect,
    cell_size: float,
    color_for_cell,
) -> None:
    if shell_preview is None:
        return
    for impact, draw_state in shell_preview.impact_frames:
        color = color_for_cell(int(impact.color_id))
        start = _board_center_2d(board_rect, cell_size, impact.start_position)
        end = _board_center_2d(board_rect, cell_size, draw_state.position)
        pygame.draw.line(overlay, _overlay_color(color, draw_state.alpha), start, end, max(2, int(round(draw_state.streak_width))))
        pygame.draw.circle(overlay, _overlay_color((255, 255, 255), draw_state.alpha), (int(round(end[0])), int(round(end[1]))), max(2, int(round(draw_state.radius))))
    preview_particles = tuple(
        SimpleNamespace(
            render_position=tuple(float(value) for value in cell.render_position[:2]),
            rotation_deg=tuple(float(value) for value in cell.rotation_deg),
            color_id=int(cell.color_id),
            alpha=float(cell.alpha),
        )
        for cell in getattr(shell_preview, "escaping_proxy_cells", ())
        if float(getattr(cell, "alpha", 0.0)) > 0.0
    )
    _draw_2d_particles(
        overlay,
        board_rect=board_rect,
        cell_size=cell_size,
        rendered_particles=preview_particles,
        color_for_cell=color_for_cell,
    )
    for impact, _shard, draw_state in shell_preview.shard_frames:
        color = color_for_cell(int(impact.color_id))
        center = _board_center_2d(board_rect, cell_size, draw_state.position)
        size = max(3.0, cell_size * max(0.18, float(draw_state.size)))
        corners = []
        for local in ((0.9, 0.0), (-0.45, 0.55), (-0.45, -0.55)):
            rotated = _rotate_xy(local, float(draw_state.rotation_deg))
            corners.append((center[0] + rotated[0] * size, center[1] + rotated[1] * size))
        pygame.draw.polygon(overlay, _overlay_color(color, draw_state.alpha), corners)
        pygame.draw.polygon(overlay, _overlay_color((255, 255, 255), draw_state.alpha), corners, 1)
    for impact, alpha in getattr(shell_preview, "residue_frames", ()):
        center = _board_center_2d(board_rect, cell_size, impact.impact_position)
        pygame.draw.circle(
            overlay,
            _overlay_color(color_for_cell(int(impact.color_id)), alpha),
            (int(round(center[0])), int(round(center[1]))),
            max(3, int(round(cell_size * 0.24))),
            2,
        )


def _draw_frozen_preview_cells_2d(
    overlay: pygame.Surface,
    *,
    frozen_cells,
    board_rect: pygame.Rect,
    cell_size: float,
    color_for_cell,
) -> None:
    preview_particles = tuple(
        SimpleNamespace(
            render_position=tuple(float(value) for value in cell.position[:2]),
            rotation_deg=(0.0, 0.0, 0.0),
            color_id=int(cell.color_id),
        )
        for cell in frozen_cells
    )
    _draw_2d_particles(
        overlay,
        board_rect=board_rect,
        cell_size=cell_size,
        rendered_particles=preview_particles,
        color_for_cell=color_for_cell,
    )


def _draw_grid_mode_3d(
    surface: pygame.Surface,
    *,
    dims: tuple[int, int, int],
    grid_mode: GridMode,
    params,
    center_px: tuple[int, int],
    board_rect: pygame.Rect,
    draw_board_grid,
    project_raw_point,
    transform_raw_point,
    depth_denominator_for_depth,
) -> None:
    draw_projected_grid_mode(
        surface=surface,
        dims=dims,
        grid_mode=grid_mode,
        draw_full_grid=lambda: draw_board_grid(
            surface,
            dims,
            params,
            board_rect,
            inner_color=(52, 64, 95),
            frame_color=(75, 90, 125),
            frame_width=2,
        ),
        project_raw=lambda raw: project_raw_point(raw, dims, params, center_px),
        transform_raw=lambda raw: transform_raw_point(raw, dims, params),
        depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
        helper_marks=(set(), set(), set()),
    )


def _draw_3d_traces(
    overlay: pygame.Surface,
    *,
    rendered_particles,
    dims: tuple[int, int, int],
    params,
    center_px: tuple[int, int],
    project_raw_point,
    color_for_cell_3d,
) -> None:
    for particle in rendered_particles:
        color = color_for_cell_3d(int(particle.color_id))
        trail_segments = tuple(getattr(particle, "trail_segments", ()))
        if not trail_segments:
            source = project_raw_point(
                tuple(float(value) for value in getattr(particle, "source_coord", ())[:3]),
                dims,
                params,
                center_px,
            )
            head = project_raw_point(
                tuple(float(value) for value in particle.render_position),
                dims,
                params,
                center_px,
            )
            if source is None or head is None:
                continue
            pygame.draw.line(overlay, _trace_color(color), source, head, _TRACE_WIDTH)
            continue
        for segment in trail_segments:
            tail = project_raw_point(
                tuple(float(value) for value in segment.tail_render_position),
                dims,
                params,
                center_px,
            )
            head = project_raw_point(
                tuple(float(value) for value in segment.head_render_position),
                dims,
                params,
                center_px,
            )
            if tail is None or head is None:
                continue
            pygame.draw.line(
                overlay,
                _trace_color(color, alpha=float(segment.alpha)),
                tail,
                head,
                _trace_width(1.6, float(segment.width)),
            )


def _draw_shell_preview_3d(
    overlay: pygame.Surface,
    *,
    shell_preview,
    dims: tuple[int, int, int],
    params,
    center_px: tuple[int, int],
    project_raw_point,
    color_for_cell_3d,
) -> None:
    if shell_preview is None:
        return
    for impact, draw_state in shell_preview.impact_frames:
        start = project_raw_point(tuple(float(v) for v in impact.start_position[:3]), dims, params, center_px)
        end = project_raw_point(tuple(float(v) for v in draw_state.position[:3]), dims, params, center_px)
        if start is None or end is None:
            continue
        color = color_for_cell_3d(int(impact.color_id))
        pygame.draw.line(overlay, _overlay_color(color, draw_state.alpha), start, end, max(2, int(round(draw_state.streak_width))))
        pygame.draw.circle(overlay, _overlay_color((255, 255, 255), draw_state.alpha), (int(round(end[0])), int(round(end[1]))), max(2, int(round(draw_state.radius))))
    for impact, _shard, draw_state in shell_preview.shard_frames:
        color = color_for_cell_3d(int(impact.color_id))
        center = tuple(float(v) for v in draw_state.position[:3])
        size = max(0.14, float(draw_state.size))
        points = []
        for local in ((0.9, 0.0), (-0.45, 0.55), (-0.45, -0.55)):
            rotated = _rotate_xy(local, float(draw_state.rotation_deg))
            projected = project_raw_point((center[0] + rotated[0] * size, center[1] + rotated[1] * size, center[2]), dims, params, center_px)
            if projected is not None:
                points.append(projected)
        if len(points) == 3:
            pygame.draw.polygon(overlay, _overlay_color(color, draw_state.alpha), points)
            pygame.draw.polygon(overlay, _overlay_color((255, 255, 255), draw_state.alpha), points, 1)
    for impact, alpha in getattr(shell_preview, "residue_frames", ()):
        center = project_raw_point(tuple(float(v) for v in impact.impact_position[:3]), dims, params, center_px)
        if center is None:
            continue
        pygame.draw.circle(
            overlay,
            _overlay_color(color_for_cell_3d(int(impact.color_id)), alpha),
            (int(round(center[0])), int(round(center[1]))),
            5,
            2,
        )


def _draw_escaping_proxy_cells_3d(
    overlay: pygame.Surface,
    *,
    shell_preview,
    dims: tuple[int, int, int],
    params,
    center_px: tuple[int, int],
    color_for_cell_3d,
    draw_cells,
    build_cell_faces,
) -> None:
    proxy_cells = [
        (
            tuple(float(value) for value in cell.render_position[:3]),
            int(cell.color_id),
            True,
            True,
        )
        for cell in getattr(shell_preview, "escaping_proxy_cells", ())
        if float(getattr(cell, "alpha", 0.0)) > 0.0
    ]
    if not proxy_cells:
        return
    opacity = max(0.0, min(1.0, max(float(cell.alpha) for cell in getattr(shell_preview, "escaping_proxy_cells", ()))))
    draw_cells(
        overlay,
        cells=proxy_cells,
        build_faces_fn=lambda coord, color, active: build_cell_faces(
            cell=coord,
            color=color,
            params=params,
            center_px=center_px,
            dims=dims,
            active=active,
        ),
        color_for_cell_fn=color_for_cell_3d,
        overlay_transparency=0.0,
        assist_overlay_opacity_scale=opacity,
    )


def _shadow_faces_for_particles_3d(
    *,
    rendered_particles,
    dims: tuple[int, int, int],
    shadow_mode: ShadowMode,
    params,
    center_px: tuple[int, int],
    project_raw_point,
    transform_raw_point,
    depth_denominator_for_depth,
    color_for_cell_3d,
) -> tuple:
    if shadow_mode == ShadowMode.OFF:
        return ()
    return tuple(
        primitive
        for particle in rendered_particles
        for primitive in build_boundary_projection_face_primitives(
            cells=((tuple(float(value) for value in particle.render_position), 0.88),),
            dims=dims,
            gravity_axis=1,
            grid_mode=GridMode(shadow_mode.value),
            project_raw=lambda raw: project_raw_point(raw, dims, params, center_px),
            transform_raw=lambda raw: transform_raw_point(raw, dims, params),
            depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
            color=color_for_cell_3d(int(particle.color_id)),
        )
    )


def _draw_native_board_2d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
    show_trace: bool,
    grid_mode: GridMode,
    shadow_mode: ShadowMode,
    shell_preview=None,
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
    _draw_2d_grid(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        width_cells=width_cells,
        height_cells=height_cells,
        grid_mode=grid_mode,
    )
    if controller is None:
        return
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    hold_preview = shell_preview is not None and getattr(shell_preview, "phase", "") == "hold"
    rendered_particles = tuple() if hold_preview else controller.render_particles(render_context=None)
    _draw_2d_shadow_guides(
        surface,
        board_rect=board_rect,
        cell_size=cell_size,
        dims=(width_cells, height_cells),
        rendered_particles=rendered_particles,
        color_for_cell=color_for_cell,
        shadow_mode=shadow_mode,
    )
    if show_trace and not hold_preview:
        _draw_2d_traces(
            overlay,
            board_rect=board_rect,
            cell_size=cell_size,
            rendered_particles=rendered_particles,
            color_for_cell=color_for_cell,
        )
    if hold_preview:
        _draw_frozen_preview_cells_2d(
            overlay,
            frozen_cells=getattr(shell_preview, "frozen_cells", ()),
            board_rect=board_rect,
            cell_size=cell_size,
            color_for_cell=color_for_cell,
        )
    _draw_shell_preview_2d(
        overlay,
        shell_preview=shell_preview,
        board_rect=board_rect,
        cell_size=cell_size,
        color_for_cell=color_for_cell,
    )
    _draw_2d_particles(
        overlay,
        board_rect=board_rect,
        cell_size=cell_size,
        rendered_particles=rendered_particles,
        color_for_cell=color_for_cell,
    )
    surface.blit(overlay, (0, 0))


def _draw_native_board_3d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
    camera_3d,
    show_trace: bool,
    grid_mode: GridMode,
    shadow_mode: ShadowMode,
    shell_preview=None,
) -> None:
    from tet4d.ui.pygame.front3d_render import Camera3D, color_for_cell_3d
    from tet4d.ui.pygame.render.front3d_cell_render import draw_cells
    from tet4d.ui.pygame.render.front3d_projection_helpers import (
        ProjectionParams3D,
        build_cell_face_primitives,
        build_cell_faces,
        draw_board_grid,
        depth_denominator_for_depth,
        fit_orthographic_zoom_for_rect,
        project_raw_point,
        transform_raw_point,
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
    center_px = (board_rect.centerx, board_rect.centery)
    board_line_primitives = build_projected_grid_primitives(
        dims=dims,
        grid_mode=grid_mode,
        project_raw=lambda raw: project_raw_point(raw, dims, params, center_px),
        transform_raw=lambda raw: transform_raw_point(raw, dims, params),
        depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
    )
    if controller is None:
        _draw_grid_mode_3d(
            surface,
            dims=dims,
            grid_mode=grid_mode,
            params=params,
            center_px=center_px,
            board_rect=board_rect,
            draw_board_grid=draw_board_grid,
            project_raw_point=project_raw_point,
            transform_raw_point=transform_raw_point,
            depth_denominator_for_depth=depth_denominator_for_depth,
        )
        return
    rendered_particles = controller.render_particles(render_context=None)
    hold_preview = shell_preview is not None and getattr(shell_preview, "phase", "") == "hold"
    if hold_preview:
        rendered_particles = tuple()
    trace_overlay = None
    if show_trace and not hold_preview:
        trace_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        _draw_3d_traces(
            trace_overlay,
            rendered_particles=rendered_particles,
            dims=dims,
            params=params,
            center_px=center_px,
            project_raw_point=project_raw_point,
            color_for_cell_3d=color_for_cell_3d,
        )
    preview_overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    _draw_shell_preview_3d(
        preview_overlay,
        shell_preview=shell_preview,
        dims=dims,
        params=params,
        center_px=center_px,
        project_raw_point=project_raw_point,
        color_for_cell_3d=color_for_cell_3d,
    )
    _draw_escaping_proxy_cells_3d(
        preview_overlay,
        shell_preview=shell_preview,
        dims=dims,
        params=params,
        center_px=center_px,
        color_for_cell_3d=color_for_cell_3d,
        draw_cells=draw_cells,
        build_cell_faces=build_cell_faces,
    )
    visible_cells = [
        (
            tuple(float(value) for value in particle.render_position),
            int(particle.color_id),
            True,
            False,
        )
        for particle in rendered_particles
    ]
    active_piece_faces = tuple(
        primitive
        for particle in rendered_particles
        for primitive in build_cell_face_primitives(
            cell=tuple(float(value) for value in particle.render_position),
            color=color_for_cell_3d(int(particle.color_id)),
            params=params,
            center_px=center_px,
            dims=dims,
            active=True,
        )
    )
    if hold_preview:
        visible_cells = [
            (
                tuple(float(value) for value in cell.position[:3]),
                int(cell.color_id),
                True,
                False,
            )
            for cell in getattr(shell_preview, "frozen_cells", ())
        ]
        active_piece_faces = tuple(
            primitive
            for coord, color_id, _active, _overlay in visible_cells
            for primitive in build_cell_face_primitives(
                cell=coord,
                color=color_for_cell_3d(int(color_id)),
                params=params,
                center_px=center_px,
                dims=dims,
                active=True,
            )
        )
    projection_faces = _shadow_faces_for_particles_3d(
        rendered_particles=rendered_particles,
        dims=dims,
        shadow_mode=shadow_mode,
        params=params,
        center_px=center_px,
        project_raw_point=project_raw_point,
        transform_raw_point=transform_raw_point,
        depth_denominator_for_depth=depth_denominator_for_depth,
        color_for_cell_3d=color_for_cell_3d,
    )
    if active_piece_faces and board_line_primitives:
        occlusion_buckets = resolve_board_line_occlusion(
            tuple(board_line_primitives),
            active_piece_faces,
        )
        draw_projected_line_buckets(
            surface=surface,
            fragments=occlusion_buckets.segments_under_piece,
            frame_color=(75, 90, 125),
            inner_color=(52, 64, 95),
            frame_width=2,
        )
    else:
        _draw_grid_mode_3d(
            surface,
            dims=dims,
            grid_mode=grid_mode,
            params=params,
            center_px=center_px,
            board_rect=board_rect,
            draw_board_grid=draw_board_grid,
            project_raw_point=project_raw_point,
            transform_raw_point=transform_raw_point,
            depth_denominator_for_depth=depth_denominator_for_depth,
        )
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
    if active_piece_faces and board_line_primitives:
        draw_projected_line_buckets(
            surface=surface,
            fragments=occlusion_buckets.segments_over_piece,
            frame_color=(75, 90, 125),
            inner_color=(52, 64, 95),
            frame_width=2,
        )
    if projection_faces:
        draw_boundary_projection_faces(surface, faces=projection_faces)
    if trace_overlay is not None:
        surface.blit(trace_overlay, (0, 0))
    surface.blit(preview_overlay, (0, 0))


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
        w_movement_animation_style="fade",
    )


def _map_4d_coord_for_render(
    coord: tuple[float, ...],
    *,
    board_dims: tuple[int, int, int, int],
    render_context: _RenderContext4D,
) -> tuple[float, float, float, float]:
    mapped: list[float] = []
    for axis, sign in render_context.basis_axis_map[:4]:
        axis_index = int(axis)
        value = float(coord[axis_index]) if 0 <= axis_index < len(coord) else 0.0
        size = float(board_dims[axis_index]) if 0 <= axis_index < len(board_dims) else 1.0
        mapped.append(value if int(sign) > 0 else (size - 1.0 - value))
    while len(mapped) < 4:
        mapped.append(0.0)
    return (mapped[0], mapped[1], mapped[2], mapped[3])


def _draw_native_board_4d_traces(
    overlay: pygame.Surface,
    *,
    rendered_particles,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> None:
    for particle in rendered_particles:
        color = color_for_cell(int(particle.color_id), color_map)
        trail_segments = tuple(getattr(particle, "trail_segments", ()))
        if not trail_segments:
            layer_weight = next(
                (
                    float(weight)
                    for candidate_layer, weight in getattr(particle, "layer_weights", ())
                    if int(candidate_layer) == layer_index
                ),
                0.0,
            )
            if layer_weight <= 0.0:
                continue
            source_render = _map_4d_coord_for_render(
                tuple(float(value) for value in getattr(particle, "source_coord", ())),
                board_dims=dims4,
                render_context=render_context,
            )
            source_point = project_raw_point(
                tuple(float(value) for value in source_render[:3]),
                basis.dims3,
                view,
                center_px,
                zoom,
            )
            head_point = project_raw_point(
                tuple(float(value) for value in particle.render_position),
                basis.dims3,
                view,
                center_px,
                zoom,
            )
            if source_point is None or head_point is None:
                continue
            pygame.draw.line(
                overlay,
                _trace_color(color, alpha=layer_weight),
                source_point,
                head_point,
                _TRACE_WIDTH,
            )
            continue
        for segment in trail_segments:
            tail_layer_weight = next(
                (
                    float(weight)
                    for candidate_layer, weight in segment.tail_layer_weights
                    if int(candidate_layer) == layer_index
                ),
                0.0,
            )
            head_layer_weight = next(
                (
                    float(weight)
                    for candidate_layer, weight in segment.head_layer_weights
                    if int(candidate_layer) == layer_index
                ),
                0.0,
            )
            layer_weight = max(tail_layer_weight, head_layer_weight)
            if layer_weight <= 0.0:
                continue
            tail_point = project_raw_point(
                tuple(float(value) for value in segment.tail_render_position),
                basis.dims3,
                view,
                center_px,
                zoom,
            )
            head_point = project_raw_point(
                tuple(float(value) for value in segment.head_render_position),
                basis.dims3,
                view,
                center_px,
                zoom,
            )
            if tail_point is None or head_point is None:
                continue
            pygame.draw.line(
                overlay,
                _trace_color(
                    color,
                    alpha=min(1.0, float(segment.alpha) * layer_weight),
                ),
                tail_point,
                head_point,
                _trace_width(1.5, float(segment.width)),
            )


def _layer_alpha_for_preview(mapped_coord: tuple[float, float, float, float], layer_index: int) -> float:
    return max(0.0, 1.0 - abs(float(mapped_coord[3]) - float(layer_index)))


def _draw_shell_preview_4d_impacts(
    overlay: pygame.Surface,
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> None:
    for impact, draw_state in shell_preview.impact_frames:
        start_render = _map_4d_coord_for_render(tuple(float(v) for v in impact.start_position[:4]), board_dims=dims4, render_context=render_context)
        end_render = _map_4d_coord_for_render(tuple(float(v) for v in draw_state.position[:4]), board_dims=dims4, render_context=render_context)
        alpha_scale = _layer_alpha_for_preview(start_render, layer_index)
        if alpha_scale <= 0.0:
            continue
        start = project_raw_point(tuple(float(v) for v in start_render[:3]), basis.dims3, view, center_px, zoom)
        end = project_raw_point(tuple(float(v) for v in end_render[:3]), basis.dims3, view, center_px, zoom)
        if start is None or end is None:
            continue
        color = color_for_cell(int(impact.color_id), color_map)
        alpha = float(draw_state.alpha) * alpha_scale
        pygame.draw.line(overlay, _overlay_color(color, alpha), start, end, max(2, int(round(draw_state.streak_width))))
        pygame.draw.circle(overlay, _overlay_color((255, 255, 255), alpha), (int(round(end[0])), int(round(end[1]))), max(2, int(round(draw_state.radius))))


def _draw_shell_preview_4d_shards(
    overlay: pygame.Surface,
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> None:
    for impact, _shard, draw_state in shell_preview.shard_frames:
        color = color_for_cell(int(impact.color_id), color_map)
        center_render = _map_4d_coord_for_render(tuple(float(v) for v in draw_state.position[:4]), board_dims=dims4, render_context=render_context)
        alpha = float(draw_state.alpha) * _layer_alpha_for_preview(center_render, layer_index)
        if alpha <= 0.0:
            continue
        center = tuple(float(v) for v in center_render[:3])
        size = max(0.14, float(draw_state.size))
        points = []
        for local in ((0.9, 0.0), (-0.45, 0.55), (-0.45, -0.55)):
            rotated = _rotate_xy(local, float(draw_state.rotation_deg))
            projected = project_raw_point((center[0] + rotated[0] * size, center[1] + rotated[1] * size, center[2]), basis.dims3, view, center_px, zoom)
            if projected is not None:
                points.append(projected)
        if len(points) == 3:
            pygame.draw.polygon(overlay, _overlay_color(color, alpha), points)
            pygame.draw.polygon(overlay, _overlay_color((255, 255, 255), alpha), points, 1)


def _draw_shell_preview_4d_residue(
    overlay: pygame.Surface,
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> None:
    for impact, alpha in getattr(shell_preview, "residue_frames", ()):
        center_render = _map_4d_coord_for_render(tuple(float(v) for v in impact.impact_position[:4]), board_dims=dims4, render_context=render_context)
        resolved_alpha = float(alpha) * _layer_alpha_for_preview(center_render, layer_index)
        if resolved_alpha <= 0.0:
            continue
        center = project_raw_point(tuple(float(v) for v in center_render[:3]), basis.dims3, view, center_px, zoom)
        if center is None:
            continue
        pygame.draw.circle(
            overlay,
            _overlay_color(color_for_cell(int(impact.color_id), color_map), resolved_alpha),
            (int(round(center[0])), int(round(center[1]))),
            5,
            2,
        )


def _draw_shell_preview_4d(
    overlay: pygame.Surface,
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> None:
    if shell_preview is None:
        return
    _draw_shell_preview_4d_impacts(
        overlay,
        shell_preview=shell_preview,
        layer_index=layer_index,
        dims4=dims4,
        render_context=render_context,
        basis=basis,
        view=view,
        center_px=center_px,
        zoom=zoom,
        project_raw_point=project_raw_point,
        color_for_cell=color_for_cell,
        color_map=color_map,
    )
    _draw_shell_preview_4d_shards(
        overlay,
        shell_preview=shell_preview,
        layer_index=layer_index,
        dims4=dims4,
        render_context=render_context,
        basis=basis,
        view=view,
        center_px=center_px,
        zoom=zoom,
        project_raw_point=project_raw_point,
        color_for_cell=color_for_cell,
        color_map=color_map,
    )
    _draw_shell_preview_4d_residue(
        overlay,
        shell_preview=shell_preview,
        layer_index=layer_index,
        dims4=dims4,
        render_context=render_context,
        basis=basis,
        view=view,
        center_px=center_px,
        zoom=zoom,
        project_raw_point=project_raw_point,
        color_for_cell=color_for_cell,
        color_map=color_map,
    )


def _collect_native_board_4d_faces(
    *,
    rendered_particles,
    layer_index: int,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    transform_raw_point,
    color_for_cell,
    color_map,
    build_oriented_cube_faces,
) -> list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]]:
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
        scale = _layer_scale_for_particle(particle, layer_index)
        if layer_weight <= 0.0 or scale <= 0.0:
            continue
        particle_faces = build_oriented_cube_faces(
            center=tuple(float(value) for value in particle.render_position),
            color=color_for_cell(int(particle.color_id), color_map),
            project_raw=lambda raw: project_raw_point(
                raw,
                basis.dims3,
                view,
                center_px,
                zoom,
            ),
            transform_raw=lambda raw: transform_raw_point(raw, basis.dims3, view),
            active=True,
            rotation_deg=tuple(float(value) for value in particle.rotation_deg),
            scale=scale,
        )
        faces.extend(
            (depth, polygon, color, min(1.0, float(particle.alpha) * layer_weight))
            for depth, polygon, color, _active in particle_faces
        )
    return faces


def _active_preview_faces_for_particles_4d(
    *,
    rendered_particles,
    layer_index: int,
    center_px: tuple[int, int],
    zoom: float,
    basis,
    view,
    build_cell_face_primitives,
    color_for_cell,
    color_map,
) -> tuple:
    return tuple(
        primitive
        for particle in rendered_particles
        for candidate_layer, weight in getattr(particle, "layer_weights", ())
        if int(candidate_layer) == layer_index and float(weight) > 0.0
        for primitive in build_cell_face_primitives(
            cell=tuple(float(value) for value in particle.render_position),
            color=color_for_cell(int(particle.color_id), color_map),
            view=view,
            center_px=center_px,
            dims3=basis.dims3,
            zoom=zoom,
            active=True,
        )
    )


def _hold_preview_faces_4d(
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    transform_raw_point,
    build_oriented_cube_faces,
    build_cell_face_primitives,
    color_for_cell,
    color_map,
) -> tuple[list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]], list]:
    faces: list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]] = []
    active_piece_faces: list = []
    for cell in getattr(shell_preview, "frozen_cells", ()):
        mapped = _map_4d_coord_for_render(tuple(float(value) for value in cell.position[:4]), board_dims=dims4, render_context=render_context)
        layer_weight = _layer_alpha_for_preview(mapped, layer_index)
        if layer_weight <= 0.0:
            continue
        cell_color = color_for_cell(int(cell.color_id), color_map)
        faces.extend(
            (depth, polygon, color, layer_weight)
            for depth, polygon, color, _active in build_oriented_cube_faces(
                center=tuple(float(value) for value in mapped[:3]),
                color=cell_color,
                project_raw=lambda raw: project_raw_point(raw, basis.dims3, view, center_px, zoom),
                transform_raw=lambda raw: transform_raw_point(raw, basis.dims3, view),
                active=True,
                rotation_deg=(0.0, 0.0, 0.0),
                scale=max(0.4, layer_weight),
            )
        )
        active_piece_faces.extend(
            build_cell_face_primitives(
                cell=tuple(float(value) for value in mapped[:3]),
                color=cell_color,
                view=view,
                center_px=center_px,
                dims3=basis.dims3,
                zoom=zoom,
                active=True,
            )
    )
    return faces, active_piece_faces


def _proxy_preview_faces_4d(
    *,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    transform_raw_point,
    build_oriented_cube_faces,
    build_cell_face_primitives,
    color_for_cell,
    color_map,
) -> tuple[list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]], list]:
    faces: list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]] = []
    active_piece_faces: list = []
    for cell in getattr(shell_preview, "escaping_proxy_cells", ()):
        mapped_source = _map_4d_coord_for_render(
            tuple(float(value) for value in cell.source_position[:4]),
            board_dims=dims4,
            render_context=render_context,
        )
        if _layer_alpha_for_preview(mapped_source, layer_index) <= 0.0:
            continue
        alpha = max(0.0, min(1.0, float(cell.alpha)))
        if alpha <= 0.0:
            continue
        mapped = _map_4d_coord_for_render(
            tuple(float(value) for value in cell.render_position[:4]),
            board_dims=dims4,
            render_context=render_context,
        )
        cell_color = color_for_cell(int(cell.color_id), color_map)
        scale = max(0.54, 0.92 - (0.16 * float(getattr(cell, "progress", 0.0))))
        faces.extend(
            (depth, polygon, color, alpha)
            for depth, polygon, color, _active in build_oriented_cube_faces(
                center=tuple(float(value) for value in mapped[:3]),
                color=cell_color,
                project_raw=lambda raw: project_raw_point(raw, basis.dims3, view, center_px, zoom),
                transform_raw=lambda raw: transform_raw_point(raw, basis.dims3, view),
                active=True,
                rotation_deg=tuple(float(value) for value in cell.rotation_deg),
                scale=scale,
            )
        )
        active_piece_faces.extend(
            build_cell_face_primitives(
                cell=tuple(float(value) for value in mapped[:3]),
                color=cell_color,
                view=view,
                center_px=center_px,
                dims3=basis.dims3,
                zoom=zoom,
                active=True,
            )
    )
    return faces, active_piece_faces


def _preview_faces_for_layer_4d(
    *,
    shell_preview,
    hold_preview: bool,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    transform_raw_point,
    build_oriented_cube_faces,
    build_cell_face_primitives,
    color_for_cell,
    color_map,
    faces: list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]],
    active_piece_faces: list,
) -> tuple[list[tuple[float, list[tuple[float, float]], tuple[int, int, int], float]], list]:
    if hold_preview:
        return _hold_preview_faces_4d(
            shell_preview=shell_preview,
            layer_index=layer_index,
            dims4=dims4,
            render_context=render_context,
            basis=basis,
            view=view,
            center_px=center_px,
            zoom=zoom,
            project_raw_point=project_raw_point,
            transform_raw_point=transform_raw_point,
            build_oriented_cube_faces=build_oriented_cube_faces,
            build_cell_face_primitives=build_cell_face_primitives,
            color_for_cell=color_for_cell,
            color_map=color_map,
        )
    if shell_preview is None:
        return faces, active_piece_faces
    proxy_faces, proxy_active_piece_faces = _proxy_preview_faces_4d(
        shell_preview=shell_preview,
        layer_index=layer_index,
        dims4=dims4,
        render_context=render_context,
        basis=basis,
        view=view,
        center_px=center_px,
        zoom=zoom,
        project_raw_point=project_raw_point,
        transform_raw_point=transform_raw_point,
        build_oriented_cube_faces=build_oriented_cube_faces,
        build_cell_face_primitives=build_cell_face_primitives,
        color_for_cell=color_for_cell,
        color_map=color_map,
    )
    return faces + proxy_faces, active_piece_faces + proxy_active_piece_faces


def _draw_empty_native_board_4d_layer(
    surface: pygame.Surface,
    *,
    basis,
    dims4: tuple[int, int, int, int],
    layer_index: int,
    view,
    draw_rect: pygame.Rect,
    center_px: tuple[int, int],
    zoom: float,
    grid_mode: GridMode,
    draw_board_grid,
    project_raw_point,
    transform_raw_point,
    orthographic_depth_denominator,
) -> None:
    draw_projected_grid_mode(
        surface=surface,
        dims=basis.dims3,
        grid_mode=grid_mode,
        draw_full_grid=lambda: draw_board_grid(
            surface,
            basis.dims3,
            dims4,
            layer_index,
            basis,
            view,
            draw_rect,
            zoom,
        ),
        project_raw=lambda raw: project_raw_point(raw, basis.dims3, view, center_px, zoom),
        transform_raw=lambda raw: transform_raw_point(raw, basis.dims3, view),
        depth_denominator=orthographic_depth_denominator,
        helper_marks=(set(), set(), set()),
    )


def _native_board_4d_overlay(
    surface: pygame.Surface,
    *,
    rendered_particles,
    show_trace: bool,
    hold_preview: bool,
    shell_preview,
    layer_index: int,
    dims4: tuple[int, int, int, int],
    render_context: _RenderContext4D,
    basis,
    view,
    center_px: tuple[int, int],
    zoom: float,
    project_raw_point,
    color_for_cell,
    color_map,
) -> pygame.Surface:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    if show_trace and not hold_preview:
        _draw_native_board_4d_traces(
            overlay,
            rendered_particles=rendered_particles,
            layer_index=layer_index,
            dims4=dims4,
            render_context=render_context,
            basis=basis,
            view=view,
            center_px=center_px,
            zoom=zoom,
            project_raw_point=project_raw_point,
            color_for_cell=color_for_cell,
            color_map=color_map,
        )
    _draw_shell_preview_4d(
        overlay,
        shell_preview=shell_preview,
        layer_index=layer_index,
        dims4=dims4,
        render_context=render_context,
        basis=basis,
        view=view,
        center_px=center_px,
        zoom=zoom,
        project_raw_point=project_raw_point,
        color_for_cell=color_for_cell,
        color_map=color_map,
    )
    return overlay


def _draw_native_board_4d(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fonts,
    controller: LockedCellExplosionController | None,
    board_dims: tuple[int, ...],
    view_4d,
    show_trace: bool,
    grid_mode: GridMode,
    shadow_mode: ShadowMode,
    w_movement_animation_style: str,
    shell_preview=None,
) -> None:
    from tet4d.ui.pygame.front4d_render import (
        COLOR_MAP,
        LayerView3D,
        _basis_for_view,
        _build_cell_face_primitives,
        _draw_board_grid,
        _fit_zoom,
        _layer_rects_by_layer,
        _orthographic_depth_denominator,
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
    render_context = _RenderContext4D(
        basis_axis_map=render_context.basis_axis_map,
        layer_count=render_context.layer_count,
        yaw_deg=render_context.yaw_deg,
        pitch_deg=render_context.pitch_deg,
        zoom=render_context.zoom,
        xw_deg=render_context.xw_deg,
        zw_deg=render_context.zw_deg,
        layer_axis_label=render_context.layer_axis_label,
        layer_axis=render_context.layer_axis,
        layer_sign=render_context.layer_sign,
        w_movement_animation_style=str(w_movement_animation_style),
    )
    rendered_particles = (
        tuple()
        if controller is None
        else controller.render_particles(render_context=render_context)
    )
    hold_preview = shell_preview is not None and getattr(shell_preview, "phase", "") == "hold"
    if hold_preview:
        rendered_particles = tuple()
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
        center_px = (draw_rect.centerx, draw_rect.centery)
        board_line_primitives = build_projected_grid_primitives(
            dims=basis.dims3,
            grid_mode=grid_mode,
            project_raw=lambda raw: _project_raw_point(raw, basis.dims3, view, center_px, zoom),
            transform_raw=lambda raw: _transform_raw_point(raw, basis.dims3, view),
            depth_denominator=_orthographic_depth_denominator,
        )
        if controller is None:
            _draw_empty_native_board_4d_layer(
                surface,
                basis=basis,
                dims4=dims4,
                layer_index=layer_index,
                view=view,
                draw_rect=draw_rect,
                center_px=center_px,
                zoom=zoom,
                grid_mode=grid_mode,
                draw_board_grid=_draw_board_grid,
                project_raw_point=_project_raw_point,
                transform_raw_point=_transform_raw_point,
                orthographic_depth_denominator=_orthographic_depth_denominator,
            )
            continue
        overlay = _native_board_4d_overlay(
            surface,
            rendered_particles=rendered_particles,
            show_trace=show_trace,
            hold_preview=hold_preview,
            shell_preview=shell_preview,
            layer_index=layer_index,
            dims4=dims4,
            render_context=render_context,
            basis=basis,
            view=view,
            center_px=center_px,
            zoom=zoom,
            project_raw_point=_project_raw_point,
            color_for_cell=color_for_cell,
            color_map=COLOR_MAP,
        )
        faces = _collect_native_board_4d_faces(
            rendered_particles=rendered_particles,
            layer_index=layer_index,
            basis=basis,
            view=view,
            center_px=center_px,
            zoom=zoom,
            project_raw_point=_project_raw_point,
            transform_raw_point=_transform_raw_point,
            color_for_cell=color_for_cell,
            color_map=COLOR_MAP,
            build_oriented_cube_faces=build_oriented_cube_faces,
        )
        active_piece_faces = _active_preview_faces_for_particles_4d(
            rendered_particles=rendered_particles,
            layer_index=layer_index,
            center_px=center_px,
            zoom=zoom,
            basis=basis,
            view=view,
            build_cell_face_primitives=_build_cell_face_primitives,
            color_for_cell=color_for_cell,
            color_map=COLOR_MAP,
        )
        faces, active_piece_faces = _preview_faces_for_layer_4d(
            shell_preview=shell_preview,
            hold_preview=hold_preview,
            layer_index=layer_index,
            dims4=dims4,
            render_context=render_context,
            basis=basis,
            view=view,
            center_px=center_px,
            zoom=zoom,
            project_raw_point=_project_raw_point,
            transform_raw_point=_transform_raw_point,
            build_oriented_cube_faces=build_oriented_cube_faces,
            build_cell_face_primitives=_build_cell_face_primitives,
            color_for_cell=color_for_cell,
            color_map=COLOR_MAP,
            faces=faces,
            active_piece_faces=list(active_piece_faces),
        )
        if active_piece_faces and board_line_primitives:
            occlusion_buckets = resolve_board_line_occlusion(
                tuple(board_line_primitives),
                active_piece_faces,
            )
            draw_projected_line_buckets(
                surface=surface,
                fragments=occlusion_buckets.segments_under_piece,
                frame_color=_FRAME,
                inner_color=(52, 64, 95),
                frame_width=2,
            )
        else:
            draw_projected_grid_mode(
                surface=surface,
                dims=basis.dims3,
                grid_mode=grid_mode,
                draw_full_grid=lambda: _draw_board_grid(
                    surface,
                    basis.dims3,
                    dims4,
                    layer_index,
                    basis,
                    view,
                    draw_rect,
                    zoom,
                ),
                project_raw=lambda raw: _project_raw_point(
                    raw,
                    basis.dims3,
                    view,
                    center_px,
                    zoom,
                ),
                transform_raw=lambda raw: _transform_raw_point(raw, basis.dims3, view),
                depth_denominator=_orthographic_depth_denominator,
                helper_marks=(set(), set(), set()),
            )
        faces.sort(key=lambda item: item[0], reverse=True)
        for _depth, polygon, color, alpha in faces:
            fill_alpha = max(0, min(255, int(round(255 * alpha))))
            outline_alpha = max(0, min(255, int(round(220 * alpha))))
            pygame.draw.polygon(overlay, (*color, fill_alpha), polygon)
            pygame.draw.polygon(overlay, (255, 255, 255, outline_alpha), polygon, 2)
        surface.blit(overlay, (0, 0))
        if active_piece_faces and board_line_primitives:
            draw_projected_line_buckets(
                surface=surface,
                fragments=occlusion_buckets.segments_over_piece,
                frame_color=_FRAME,
                inner_color=(52, 64, 95),
                frame_width=2,
            )
        projection_faces = tuple(
            primitive
            for particle in rendered_particles
            for candidate_layer, weight in getattr(particle, "layer_weights", ())
            if int(candidate_layer) == layer_index and float(weight) > 0.0
            for primitive in build_boundary_projection_face_primitives(
                cells=((tuple(float(value) for value in particle.render_position), 0.9),),
                dims=basis.dims3,
                gravity_axis=1,
                grid_mode=GridMode(shadow_mode.value),
                project_raw=lambda raw: _project_raw_point(
                    raw,
                    basis.dims3,
                    view,
                    center_px,
                    zoom,
                ),
                transform_raw=lambda raw: _transform_raw_point(raw, basis.dims3, view),
                depth_denominator=_orthographic_depth_denominator,
                color=color_for_cell(int(particle.color_id), COLOR_MAP),
            )
        )
        if shadow_mode != ShadowMode.OFF:
            draw_boundary_projection_faces(surface, faces=projection_faces)


def _layer_scale_for_particle(particle, layer_index: int) -> float:
    layer_scales = tuple(getattr(particle, "layer_scales", ()))
    if not layer_scales:
        return next(
            (
                float(weight)
                for candidate_layer, weight in getattr(particle, "layer_weights", ())
                if int(candidate_layer) == layer_index
            ),
            0.0,
        )
    return next(
        (
            float(scale)
            for candidate_layer, scale in layer_scales
            if int(candidate_layer) == layer_index
        ),
        0.0,
    )


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
    show_trace: bool = False,
    grid_mode: GridMode = GridMode.FULL,
    shadow_mode: ShadowMode = ShadowMode.OFF,
    w_movement_animation_style: str = "fade",
    shell_preview=None,
) -> None:
    if int(dimension) == 2:
        _draw_native_board_2d(
            surface,
            rect=rect,
            controller=controller,
            board_dims=board_dims,
            show_trace=show_trace,
            grid_mode=grid_mode,
            shadow_mode=shadow_mode,
            shell_preview=shell_preview,
        )
        return
    if int(dimension) == 3:
        _draw_native_board_3d(
            surface,
            rect=rect,
            controller=controller,
            board_dims=board_dims,
            camera_3d=camera_3d,
            show_trace=show_trace,
            grid_mode=grid_mode,
            shadow_mode=shadow_mode,
            shell_preview=shell_preview,
        )
        return
    _draw_native_board_4d(
        surface,
        rect=rect,
        fonts=fonts,
        controller=controller,
        board_dims=board_dims,
        view_4d=view_4d,
        show_trace=show_trace,
        grid_mode=grid_mode,
        shadow_mode=shadow_mode,
        w_movement_animation_style=w_movement_animation_style,
        shell_preview=shell_preview,
    )


__all__ = [
    "draw_native_board_view",
]
