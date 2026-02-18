from __future__ import annotations

import pygame


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
