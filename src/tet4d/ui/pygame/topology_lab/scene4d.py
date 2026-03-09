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


def _layout_cards(area: pygame.Rect, count: int) -> list[pygame.Rect]:
    columns = 4 if count >= 8 else 3
    rows = max(1, (count + columns - 1) // columns)
    gutter = 12
    card_w = max(72, (area.width - gutter * (columns - 1)) // columns)
    card_h = max(54, (area.height - gutter * (rows - 1)) // rows)
    rects: list[pygame.Rect] = []
    for index in range(count):
        row = index // columns
        col = index % columns
        rects.append(
            pygame.Rect(
                area.x + col * (card_w + gutter),
                area.y + row * (card_h + gutter),
                card_w,
                card_h,
            )
        )
    return rects


def _draw_boundary_cards(
    surface: pygame.Surface,
    fonts,
    *,
    boundaries: tuple[BoundaryRef, ...],
    source_boundary: BoundaryRef,
    target_boundary: BoundaryRef,
    active_glue_ids: dict[str, str],
    rects: list[pygame.Rect],
    hovered_boundary_index: int | None,
    selected_boundary_index: int | None,
) -> tuple[list[TopologyLabHitTarget], dict[str, pygame.Rect]]:
    hit_targets: list[TopologyLabHitTarget] = []
    cards_by_label: dict[str, pygame.Rect] = {}
    for index, boundary in enumerate(boundaries):
        rect = rects[index]
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
    box = pygame.Rect(area.right - 292, area.bottom - 58, 284, 50)
    pygame.draw.rect(surface, (18, 22, 38), box, border_radius=8)
    pygame.draw.rect(surface, (76, 84, 112), box, 1, border_radius=8)
    for line_index, line in enumerate(lines[:2]):
        surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, line, box.width - 12),
            True,
            (188, 198, 228),
        )
        surface.blit(surf, (box.x + 6, box.y + 6 + line_index * (surf.get_height() + 2)))


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
    title = fonts.hint_font.render("Hyperface graph", True, (220, 228, 250))
    surface.blit(title, (area.x, area.y - title.get_height() - 4))
    rects = _layout_cards(area, len(boundaries))
    hit_targets, cards_by_label = _draw_boundary_cards(
        surface,
        fonts,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=active_glue_ids,
        rects=rects,
        hovered_boundary_index=hovered_boundary_index,
        selected_boundary_index=selected_boundary_index,
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


__all__ = ["draw_scene"]
