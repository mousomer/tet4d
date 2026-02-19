from __future__ import annotations

import pygame

from .control_helper import ControlGroup, draw_grouped_control_helper


def draw_translucent_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    *,
    alpha: int = 140,
    radius: int = 12,
    color: tuple[int, int, int] = (0, 0, 0),
) -> None:
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, (*color, alpha), panel.get_rect(), border_radius=radius)
    surface.blit(panel, rect.topleft)


def draw_text_lines(
    surface: pygame.Surface,
    *,
    lines: tuple[str, ...] | list[str],
    font: pygame.font.Font,
    start_pos: tuple[int, int],
    color: tuple[int, int, int],
    line_gap: int = 3,
) -> int:
    x, y = start_pos
    for line in lines:
        surf = font.render(line, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + line_gap
    return y


def truncate_lines_to_height(
    lines: tuple[str, ...] | list[str],
    *,
    font: pygame.font.Font,
    available_height: int,
    line_gap: int = 3,
    min_lines_for_ellipsis: int = 2,
) -> tuple[str, ...]:
    if available_height <= 0:
        return tuple()
    line_h = font.get_height() + line_gap
    if line_h <= 0:
        return tuple(lines)
    max_lines = available_height // line_h
    if max_lines <= 0:
        return tuple()
    if len(lines) <= max_lines:
        return tuple(lines)
    if max_lines < min_lines_for_ellipsis:
        return tuple()
    clipped = list(lines[: max_lines - 1])
    clipped.append("...")
    return tuple(clipped)


def draw_game_side_panel(
    surface: pygame.Surface,
    *,
    panel_rect: pygame.Rect,
    fonts,
    header_lines: tuple[str, ...] | list[str],
    control_groups: list[ControlGroup],
    low_priority_lines: tuple[str, ...] | list[str] = (),
    game_over: bool = False,
    min_controls_h: int = 140,
) -> None:
    draw_translucent_panel(surface, panel_rect, alpha=140, radius=12)

    y = draw_text_lines(
        surface,
        lines=header_lines,
        font=fonts.panel_font,
        start_pos=(panel_rect.x + 12, panel_rect.y + 14),
        color=(230, 230, 230),
        line_gap=3,
    )
    controls_top = y + 4
    reserve_bottom = 26 if game_over else 0
    available_h = max(0, panel_rect.bottom - reserve_bottom - controls_top)
    gap = 6

    low_lines: tuple[str, ...] = tuple()
    low_h = 0
    if low_priority_lines:
        max_low_h = max(0, available_h - min_controls_h - gap)
        low_lines = truncate_lines_to_height(
            tuple(low_priority_lines),
            font=fonts.hint_font,
            available_height=max(0, max_low_h - 8),
            line_gap=3,
        )
        if low_lines:
            low_h = len(low_lines) * (fonts.hint_font.get_height() + 3) + 10

    controls_bottom = panel_rect.bottom - reserve_bottom - (low_h + gap if low_h else 8)
    if controls_bottom - controls_top < 44 and low_h:
        low_lines = tuple()
        low_h = 0
        controls_bottom = panel_rect.bottom - reserve_bottom - 8

    controls_rect = pygame.Rect(
        panel_rect.x + 6,
        controls_top,
        panel_rect.width - 12,
        max(44, controls_bottom - controls_top),
    )
    draw_grouped_control_helper(
        surface,
        groups=control_groups,
        rect=controls_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )

    if low_lines:
        low_height = panel_rect.bottom - reserve_bottom - (controls_rect.bottom + 8)
        if low_height > 10:
            low_rect = pygame.Rect(
                panel_rect.x + 8,
                controls_rect.bottom + 6,
                panel_rect.width - 16,
                low_height,
            )
            draw_translucent_panel(surface, low_rect, alpha=100, radius=8, color=(8, 12, 26))
            draw_text_lines(
                surface,
                lines=low_lines,
                font=fonts.hint_font,
                start_pos=(low_rect.x + 6, low_rect.y + 5),
                color=(176, 188, 222),
                line_gap=3,
            )

    if game_over:
        over = fonts.panel_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(over, (panel_rect.x + 12, panel_rect.bottom - 26))
