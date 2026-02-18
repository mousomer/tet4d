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
