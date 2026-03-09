from __future__ import annotations

import pygame

from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.ui.pygame.front3d_render import Camera3D
from tet4d.ui.pygame.topology_lab.arrow_overlay import draw_glue_arrows
from tet4d.ui.pygame.topology_lab.common import (
    TopologyLabHitTarget,
    axis_color,
    boundary_fill_color,
)
from tet4d.ui.pygame.ui_utils import fit_text


def _camera_scalars(camera: Camera3D | None) -> tuple[float, float, float]:
    if camera is None:
        return 0.0, 0.0, 1.0
    yaw = ((float(camera.yaw_deg) + 180.0) % 360.0) - 180.0
    yaw_norm = max(-1.0, min(1.0, yaw / 120.0))
    pitch_norm = max(-1.0, min(1.0, float(camera.pitch_deg) / 74.0))
    zoom_scale = max(0.82, min(1.28, float(camera.zoom) / 52.0))
    return yaw_norm, pitch_norm, zoom_scale


def _layout_cards(
    area: pygame.Rect,
    dimension: int,
    camera: Camera3D | None = None,
) -> dict[str, pygame.Rect]:
    yaw_norm, pitch_norm, zoom_scale = _camera_scalars(camera if dimension == 3 else None)
    card_w = int(max(70, min(132, (area.width // 4) * zoom_scale)))
    card_h = int(max(54, min(96, (area.height // 4) * zoom_scale)))
    cx = area.centerx + int(yaw_norm * 18)
    cy = area.centery - int(pitch_norm * 14)
    z_dx = int(yaw_norm * 16)
    z_dy = int(pitch_norm * 12)
    return {
        'x-': pygame.Rect(cx - card_w - 28 - int(yaw_norm * 8), cy - card_h // 2, card_w, card_h),
        'x+': pygame.Rect(cx + 28 + int(yaw_norm * 8), cy - card_h // 2, card_w, card_h),
        'y-': pygame.Rect(cx - card_w // 2, cy + card_h // 2 + 18 + int(pitch_norm * 8), card_w, card_h),
        'y+': pygame.Rect(cx - card_w // 2, cy - (card_h * 3) // 2 - 18 + int(pitch_norm * 8), card_w, card_h),
        'z-': pygame.Rect(cx - card_w // 2 - 18 - z_dx, cy - card_h // 2 - 8 - z_dy, card_w, card_h),
        'z+': pygame.Rect(cx - card_w // 2 + 18 + z_dx, cy - card_h // 2 + 8 + z_dy, card_w, card_h),
    }


def _cube_rects(area: pygame.Rect, camera: Camera3D | None = None) -> tuple[pygame.Rect, pygame.Rect]:
    _yaw_norm, pitch_norm, zoom_scale = _camera_scalars(camera)
    cube = pygame.Rect(0, 0, int(max(42, area.width // 7 * zoom_scale)), int(max(42, area.height // 5 * zoom_scale)))
    cube.center = (area.centerx, area.centery - int(pitch_norm * 10))
    front = cube.inflate(-10, -10)
    return cube, front


def _draw_boundary_cards(
    surface: pygame.Surface,
    fonts,
    *,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    card_rects: dict[str, pygame.Rect],
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
) -> tuple[list[TopologyLabHitTarget], dict[str, pygame.Rect]]:
    hit_targets: list[TopologyLabHitTarget] = []
    cards_by_label: dict[str, pygame.Rect] = {}
    for index, boundary in enumerate(boundaries):
        rect = card_rects[boundary.label]
        cards_by_label[boundary.label] = rect
        fill = boundary_fill_color(boundary)
        pygame.draw.rect(surface, fill, rect, border_radius=10)
        pygame.draw.rect(surface, (18, 20, 26), rect, 2, border_radius=10)
        stripe = pygame.Rect(rect.x + 4, rect.y + 4, 8, rect.height - 8)
        pygame.draw.rect(surface, axis_color(boundary.axis), stripe, border_radius=5)
        if boundary == source_boundary:
            pygame.draw.rect(surface, (255, 226, 120), rect.inflate(6, 6), 2, border_radius=12)
        if boundary == target_boundary:
            pygame.draw.rect(surface, (112, 240, 255), rect.inflate(12, 12), 2, border_radius=14)
        if hovered_boundary_index == index:
            pygame.draw.rect(surface, (248, 248, 248), rect.inflate(2, 2), 1, border_radius=10)
        if selected_boundary_index == index:
            pygame.draw.rect(surface, (184, 204, 255), rect.inflate(10, 10), 2, border_radius=14)
        glue_id = active_glue_ids.get(boundary.label, 'free')
        label = fonts.menu_font.render(boundary.label, True, (12, 18, 28))
        status = fonts.hint_font.render(
            fit_text(fonts.hint_font, glue_id, rect.width - 20),
            True,
            (30, 34, 44),
        )
        axis_badge = fonts.hint_font.render(boundary.label[0].upper(), True, axis_color(boundary.axis))
        surface.blit(label, (rect.x + 18, rect.y + 6))
        surface.blit(axis_badge, (rect.right - axis_badge.get_width() - 8, rect.y + 6))
        surface.blit(status, (rect.x + 18, rect.bottom - status.get_height() - 8))
        hit_targets.append(TopologyLabHitTarget('boundary_pick', index, rect.copy()))
    return hit_targets, cards_by_label


def _draw_cube_guides(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    cards_by_label: dict[str, pygame.Rect],
    camera: Camera3D | None = None,
) -> tuple[pygame.Rect, pygame.Rect]:
    cube, front = _cube_rects(area, camera)
    pygame.draw.rect(surface, (42, 50, 78), cube, border_radius=8)
    pygame.draw.rect(surface, (92, 104, 146), cube, 1, border_radius=8)
    pygame.draw.rect(surface, (28, 34, 56), front, border_radius=6)
    pygame.draw.rect(surface, (120, 132, 176), front, 1, border_radius=6)
    for label in ('x-', 'x+', 'y-', 'y+', 'z-', 'z+'):
        rect = cards_by_label.get(label)
        if rect is None:
            continue
        color = axis_color('xyzw'.index(label[0]))
        pygame.draw.line(surface, color, cube.center, rect.center, 1)
    guide_text = 'Projected shell'
    if camera is not None:
        guide_text += f'  yaw {camera.yaw_deg:.0f}  pitch {camera.pitch_deg:.0f}'
    guide = fonts.hint_font.render(guide_text, True, (176, 188, 220))
    surface.blit(guide, (cube.centerx - guide.get_width() // 2, cube.bottom + 6))
    return cube, front


def _project_coord(
    front: pygame.Rect,
    coord: tuple[int, ...],
    dims: tuple[int, ...],
    camera: Camera3D | None = None,
) -> tuple[int, int]:
    x = int(coord[0]) if len(coord) >= 1 else 0
    y = int(coord[1]) if len(coord) >= 2 else 0
    z = int(coord[2]) if len(coord) >= 3 else 0
    x_span = max(1, int(dims[0]) - 1)
    y_span = max(1, int(dims[1]) - 1)
    z_span = max(1, int(dims[2]) - 1)
    x_ratio = x / x_span
    y_ratio = y / y_span
    z_ratio = z / z_span
    yaw_norm, pitch_norm, zoom_scale = _camera_scalars(camera)
    depth_x = (z_ratio - 0.5) * front.width * (0.18 + yaw_norm * 0.05)
    depth_y = z_ratio * front.height * (0.18 - pitch_norm * 0.04)
    scaled_w = front.width * zoom_scale
    scaled_h = front.height * zoom_scale
    px = int(front.centerx - scaled_w / 2 + x_ratio * scaled_w + depth_x)
    py = int(front.centery + scaled_h / 2 - y_ratio * scaled_h - depth_y)
    return px, py


def _valid_projected_points(
    front: pygame.Rect,
    preview_dims: tuple[int, ...],
    coords: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    camera: Camera3D | None = None,
) -> list[tuple[int, int]]:
    points: list[tuple[int, int]] = []
    for coord in coords or ():
        if len(coord) < 3:
            continue
        if any(int(value) < 0 or int(value) >= int(preview_dims[index]) for index, value in enumerate(coord[:3])):
            continue
        points.append(_project_coord(front, coord, preview_dims, camera))
    return points


def _draw_probe_projection(
    surface: pygame.Surface,
    *,
    front: pygame.Rect,
    preview_dims: tuple[int, ...],
    probe_coord: tuple[int, ...] | None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    camera: Camera3D | None = None,
) -> None:
    points = _valid_projected_points(front, preview_dims, probe_path, camera)
    if len(points) >= 2:
        pygame.draw.lines(surface, (92, 178, 228), False, points[-8:], 2)
    for point in points[-8:-1]:
        pygame.draw.circle(surface, (140, 168, 196), point, 4)
    if probe_coord is None or len(probe_coord) < 3:
        return
    if any(int(value) < 0 or int(value) >= int(preview_dims[index]) for index, value in enumerate(probe_coord[:3])):
        return
    point = _project_coord(front, probe_coord, preview_dims, camera)
    pygame.draw.circle(surface, (112, 240, 255), point, 8)
    pygame.draw.circle(surface, (12, 18, 26), point, 3)


def _draw_sandbox_projection(
    surface: pygame.Surface,
    *,
    front: pygame.Rect,
    preview_dims: tuple[int, ...],
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    camera: Camera3D | None = None,
) -> None:
    points = _valid_projected_points(front, preview_dims, sandbox_cells, camera)
    if not points:
        return
    fill = (236, 198, 92) if sandbox_valid or sandbox_valid is None else (220, 92, 92)
    for index, point in enumerate(points[:16]):
        radius = 6 if index == 0 else 5
        pygame.draw.circle(surface, fill, point, radius)
        pygame.draw.circle(surface, (18, 20, 26), point, 1)


def _draw_status_chips(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
    selected_glue_id: str | None,
    highlighted_glue_id: str | None,
    boundaries: tuple[BoundaryRef, ...],
) -> None:
    labels: list[str] = []
    if selected_boundary_index is not None:
        labels.append(f'Selected {boundaries[selected_boundary_index].label}')
    if hovered_boundary_index is not None:
        labels.append(f'Hover {boundaries[hovered_boundary_index].label}')
    if selected_glue_id:
        labels.append(f'Seam {selected_glue_id}')
    elif highlighted_glue_id:
        labels.append(f'Hover seam {highlighted_glue_id}')
    x = area.x + 8
    y = area.y + 8
    for label in labels[:3]:
        surf = fonts.hint_font.render(label, True, (228, 234, 248))
        bg = pygame.Rect(x, y, surf.get_width() + 12, surf.get_height() + 8)
        pygame.draw.rect(surface, (18, 22, 38), bg, border_radius=8)
        pygame.draw.rect(surface, (92, 104, 146), bg, 1, border_radius=8)
        surface.blit(surf, (bg.x + 6, bg.y + 4))
        x = bg.right + 8


def _overlay_lines(
    probe_coord: tuple[int, ...] | None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
) -> list[str]:
    lines: list[str] = []
    if probe_coord is not None:
        lines.append(f'Probe {list(probe_coord)}')
    if probe_path:
        lines.append(f'Trace {max(0, len(probe_path) - 1)} steps')
    if sandbox_cells:
        status = 'valid' if sandbox_valid or sandbox_valid is None else 'invalid'
        lines.append(f'Sandbox {len(sandbox_cells)} cells ({status})')
    if sandbox_message:
        lines.append(sandbox_message)
    return lines


def _draw_overlay_box(surface: pygame.Surface, fonts, *, area: pygame.Rect, lines: list[str]) -> None:
    if not lines:
        return
    box = pygame.Rect(area.x + 8, area.bottom - 60, min(area.width - 16, 320), 52)
    pygame.draw.rect(surface, (18, 22, 38), box, border_radius=8)
    pygame.draw.rect(surface, (76, 84, 112), box, 1, border_radius=8)
    for line_index, line in enumerate(lines[:2]):
        surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, line, box.width - 12),
            True,
            (188, 198, 228),
        )
        surface.blit(surf, (box.x + 6, box.y + 5 + line_index * (surf.get_height() + 2)))


def draw_scene(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    basis_arrows: list[dict[str, object]] | tuple[dict[str, object], ...],
    preview_dims: tuple[int, ...],
    selected_glue_id: str | None = None,
    highlighted_glue_id: str | None = None,
    hovered_boundary_index: int | None = None,
    selected_boundary_index: int | None = None,
    probe_coord: tuple[int, ...] | None = None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None = None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None = None,
    sandbox_valid: bool | None = None,
    sandbox_message: str = '',
    camera: Camera3D | None = None,
) -> list[TopologyLabHitTarget]:
    title_text = 'Boundary scene'
    if camera is not None:
        title_text = f'Boundary scene  yaw {camera.yaw_deg:.0f}  pitch {camera.pitch_deg:.0f}  zoom {camera.zoom:.0f}'
    title = fonts.hint_font.render(title_text, True, (220, 228, 250))
    surface.blit(title, (area.x, area.y - title.get_height() - 4))
    card_rects = _layout_cards(area, boundaries[0].dimension, camera)
    hit_targets, cards_by_label = _draw_boundary_cards(
        surface,
        fonts,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=active_glue_ids,
        card_rects=card_rects,
        hovered_boundary_index=hovered_boundary_index,
        selected_boundary_index=selected_boundary_index,
    )
    _draw_status_chips(
        surface,
        fonts,
        area=area,
        hovered_boundary_index=hovered_boundary_index,
        selected_boundary_index=selected_boundary_index,
        selected_glue_id=selected_glue_id,
        highlighted_glue_id=highlighted_glue_id,
        boundaries=boundaries,
    )
    _cube, front = _draw_cube_guides(surface, fonts, area=area, cards_by_label=cards_by_label, camera=camera)
    _draw_sandbox_projection(
        surface,
        front=front,
        preview_dims=preview_dims,
        sandbox_cells=sandbox_cells,
        sandbox_valid=sandbox_valid,
        camera=camera,
    )
    _draw_probe_projection(
        surface,
        front=front,
        preview_dims=preview_dims,
        probe_coord=probe_coord,
        probe_path=probe_path,
        camera=camera,
    )
    hit_targets.extend(
        draw_glue_arrows(
            surface,
            fonts,
            cards_by_label=cards_by_label,
            basis_arrows=basis_arrows,
            clip_rect=area,
            selected_glue_id=selected_glue_id,
            highlighted_glue_id=highlighted_glue_id,
        )
    )
    _draw_overlay_box(
        surface,
        fonts,
        area=area,
        lines=_overlay_lines(
            probe_coord,
            probe_path,
            sandbox_cells,
            sandbox_valid,
            sandbox_message,
        ),
    )
    return hit_targets


__all__ = ['draw_scene', '_project_coord']
