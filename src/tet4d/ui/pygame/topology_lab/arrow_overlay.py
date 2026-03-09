from __future__ import annotations

from typing import Any

import pygame

from tet4d.ui.pygame.topology_lab.common import TopologyLabHitTarget, axis_color


def _draw_arrowhead(
    surface: pygame.Surface,
    *,
    color: tuple[int, int, int],
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    if dx == 0 and dy == 0:
        return
    angle = pygame.math.Vector2(dx, dy).normalize()
    left = pygame.math.Vector2(-angle.y, angle.x)
    tip = pygame.Vector2(end)
    base = tip - (angle * 10)
    points = [tip, base + (left * 4), base - (left * 4)]
    pygame.draw.polygon(surface, color, points)


def _emphasize(color: tuple[int, int, int], amount: int) -> tuple[int, int, int]:
    return tuple(max(0, min(255, channel + amount)) for channel in color)


def _line_hit_rect(
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    padding: int = 10,
) -> pygame.Rect:
    left = min(start[0], end[0]) - padding
    top = min(start[1], end[1]) - padding
    width = max(24, abs(end[0] - start[0]) + padding * 2)
    height = max(24, abs(end[1] - start[1]) + padding * 2)
    return pygame.Rect(left, top, width, height)


def draw_glue_arrows(
    surface: pygame.Surface,
    fonts,
    *,
    cards_by_label: dict[str, pygame.Rect],
    basis_arrows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    clip_rect: pygame.Rect,
    selected_glue_id: str | None = None,
    highlighted_glue_id: str | None = None,
) -> list[TopologyLabHitTarget]:
    hits: list[TopologyLabHitTarget] = []
    previous_clip = surface.get_clip()
    surface.set_clip(clip_rect)
    try:
        for arrow in basis_arrows[:8]:
            source_rect = cards_by_label.get(str(arrow.get("source_boundary", "")))
            target_rect = cards_by_label.get(str(arrow.get("target_boundary", "")))
            if source_rect is None or target_rect is None:
                continue
            glue_id = str(arrow.get("id", ""))
            is_selected = glue_id == selected_glue_id
            is_highlighted = glue_id == highlighted_glue_id
            label_color = (248, 244, 196) if is_selected else (220, 228, 250)
            label_bg = (64, 52, 24) if is_selected else (24, 28, 40)
            crossing = str(arrow.get("crossing", glue_id))
            line_rect: pygame.Rect | None = None
            basis_pairs = arrow.get("basis_pairs", ())
            for index, pair in enumerate(basis_pairs[:3]):
                base = axis_color(index)
                color = base
                if is_selected:
                    color = _emphasize(base, 50)
                elif is_highlighted:
                    color = _emphasize(base, 26)
                start = (
                    int(source_rect.centerx),
                    int(source_rect.centery + ((index - 1) * 16)),
                )
                end = (
                    int(target_rect.centerx),
                    int(target_rect.centery + ((index - 1) * 16)),
                )
                width = 4 if is_selected else 3 if is_highlighted else 2
                pygame.draw.line(surface, color, start, end, width)
                pygame.draw.circle(surface, color, start, 4 if is_selected else 3)
                pygame.draw.circle(surface, color, end, 4 if is_selected else 3)
                _draw_arrowhead(surface, color=color, start=start, end=end)
                pair_label = f"{pair['from']} -> {pair['to']}"
                pair_surf = fonts.hint_font.render(pair_label, True, color)
                pair_rect = pair_surf.get_rect(
                    center=((start[0] + end[0]) // 2, (start[1] + end[1]) // 2 - 10)
                )
                pair_bg = pair_rect.inflate(8, 4)
                pygame.draw.rect(surface, (18, 22, 34), pair_bg, border_radius=5)
                pygame.draw.rect(surface, color, pair_bg, 1, border_radius=5)
                surface.blit(pair_surf, pair_rect)
                hit_rect = _line_hit_rect(start, end)
                line_rect = hit_rect if line_rect is None else line_rect.union(hit_rect)
                line_rect = line_rect.union(pair_bg)
            crossing_surf = fonts.hint_font.render(crossing, True, label_color)
            crossing_rect = crossing_surf.get_rect(
                center=(
                    (source_rect.centerx + target_rect.centerx) // 2,
                    min(source_rect.top, target_rect.top) - 10,
                )
            )
            crossing_bg = crossing_rect.inflate(12, 8)
            pygame.draw.rect(surface, label_bg, crossing_bg, border_radius=6)
            pygame.draw.rect(
                surface,
                (120, 132, 178) if is_selected else (96, 108, 148),
                crossing_bg,
                1,
                border_radius=6,
            )
            surface.blit(crossing_surf, crossing_rect)
            if line_rect is None:
                line_rect = crossing_bg.copy()
            else:
                line_rect = line_rect.union(crossing_bg)
            hits.append(TopologyLabHitTarget("glue_pick", glue_id, line_rect.clip(clip_rect)))
    finally:
        surface.set_clip(previous_clip)
    return hits


__all__ = ["draw_glue_arrows"]
