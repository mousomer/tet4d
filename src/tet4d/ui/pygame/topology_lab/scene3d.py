from __future__ import annotations

import pygame

from tet4d.engine.topology_explorer import BoundaryRef
from tet4d.ui.pygame.topology_lab.arrow_overlay import draw_glue_arrows
from tet4d.ui.pygame.topology_lab.common import (
    TopologyLabHitTarget,
    axis_color,
    boundary_fill_color,
)
from tet4d.ui.pygame.ui_utils import fit_text


def _layout_cards(area: pygame.Rect, dimension: int) -> dict[str, pygame.Rect]:
    card_w = max(70, min(120, area.width // 4))
    card_h = max(54, min(88, area.height // 4))
    cx = area.centerx
    cy = area.centery
    if dimension == 2:
        return {
            "x-": pygame.Rect(cx - card_w - 18, cy - card_h // 2, card_w, card_h),
            "x+": pygame.Rect(cx + 18, cy - card_h // 2, card_w, card_h),
            "y-": pygame.Rect(cx - card_w // 2, cy + 18, card_w, card_h),
            "y+": pygame.Rect(cx - card_w // 2, cy - card_h - 18, card_w, card_h),
        }
    return {
        "x-": pygame.Rect(cx - card_w - 28, cy - card_h // 2, card_w, card_h),
        "x+": pygame.Rect(cx + 28, cy - card_h // 2, card_w, card_h),
        "y-": pygame.Rect(cx - card_w // 2, cy + card_h // 2 + 14, card_w, card_h),
        "y+": pygame.Rect(cx - card_w // 2, cy - (card_h * 3) // 2 - 14, card_w, card_h),
        "z-": pygame.Rect(cx - card_w // 2 - 18, cy - card_h // 2 - 8, card_w, card_h),
        "z+": pygame.Rect(cx - card_w // 2 + 18, cy - card_h // 2 + 8, card_w, card_h),
    }


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
        if boundary == source_boundary:
            pygame.draw.rect(surface, (255, 226, 120), rect.inflate(6, 6), 2, border_radius=12)
        if boundary == target_boundary:
            pygame.draw.rect(surface, (112, 240, 255), rect.inflate(12, 12), 2, border_radius=14)
        if hovered_boundary_index == index:
            pygame.draw.rect(surface, (248, 248, 248), rect.inflate(2, 2), 1, border_radius=10)
        if selected_boundary_index == index:
            pygame.draw.rect(surface, (184, 204, 255), rect.inflate(10, 10), 2, border_radius=14)
        glue_id = active_glue_ids.get(boundary.label, "free")
        label = fonts.menu_font.render(boundary.label, True, (12, 18, 28))
        status = fonts.hint_font.render(
            fit_text(fonts.hint_font, glue_id, rect.width - 10),
            True,
            (30, 34, 44),
        )
        axis_badge = fonts.hint_font.render(boundary.label[0].upper(), True, axis_color(boundary.axis))
        surface.blit(label, (rect.x + 8, rect.y + 6))
        surface.blit(axis_badge, (rect.right - axis_badge.get_width() - 8, rect.y + 6))
        surface.blit(status, (rect.x + 8, rect.bottom - status.get_height() - 8))
        hit_targets.append(TopologyLabHitTarget("boundary_pick", index, rect.copy()))
    return hit_targets, cards_by_label


def _draw_cube_guides(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    cards_by_label: dict[str, pygame.Rect],
) -> None:
    cube = pygame.Rect(0, 0, max(42, area.width // 7), max(42, area.height // 5))
    cube.center = area.center
    pygame.draw.rect(surface, (42, 50, 78), cube, border_radius=8)
    pygame.draw.rect(surface, (92, 104, 146), cube, 1, border_radius=8)
    front = cube.inflate(-10, -10)
    pygame.draw.rect(surface, (28, 34, 56), front, border_radius=6)
    pygame.draw.rect(surface, (120, 132, 176), front, 1, border_radius=6)
    for label in ("x-", "x+", "y-", "y+", "z-", "z+"):
        rect = cards_by_label.get(label)
        if rect is None:
            continue
        color = axis_color("xyzw".index(label[0]))
        pygame.draw.line(surface, color, cube.center, rect.center, 1)
    guide = fonts.hint_font.render("Projected shell", True, (176, 188, 220))
    surface.blit(guide, (cube.centerx - guide.get_width() // 2, cube.bottom + 6))


def _overlay_lines(
    probe_coord: tuple[int, ...] | None,
    probe_path: tuple[tuple[int, ...], ...] | list[tuple[int, ...]] | None,
    sandbox_cells: tuple[tuple[int, ...], ...] | None,
    sandbox_valid: bool | None,
    sandbox_message: str,
) -> list[str]:
    lines: list[str] = []
    if probe_coord is not None:
        lines.append(f"Probe {list(probe_coord)}")
    if probe_path:
        lines.append(f"Trace {max(0, len(probe_path) - 1)} steps")
    if sandbox_cells:
        status = "valid" if sandbox_valid or sandbox_valid is None else "invalid"
        lines.append(f"Sandbox {len(sandbox_cells)} cells ({status})")
    if sandbox_message:
        lines.append(sandbox_message)
    return lines


def _draw_overlay_box(surface: pygame.Surface, fonts, *, area: pygame.Rect, lines: list[str]) -> None:
    if not lines:
        return
    box = pygame.Rect(area.x + 8, area.bottom - 50, min(area.width - 16, 280), 42)
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
    sandbox_message: str = "",
) -> list[TopologyLabHitTarget]:
    del preview_dims
    title = fonts.hint_font.render("Boundary scene", True, (220, 228, 250))
    surface.blit(title, (area.x, area.y - title.get_height() - 4))
    card_rects = _layout_cards(area, boundaries[0].dimension)
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
    _draw_cube_guides(surface, fonts, area=area, cards_by_label=cards_by_label)
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


__all__ = ["draw_scene"]
