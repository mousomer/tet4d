from __future__ import annotations

import math

import pygame


_PANEL_BG = (0, 0, 0, 132)
_BOX_BG = (0, 0, 0, 110)
_LABEL_COLOR = (188, 197, 228)
_ACCENT = (126, 214, 255)
_ARROW = (232, 232, 245)


def _draw_arrow(
    surface: pygame.Surface,
    *,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    width: int = 2,
    head: int = 8,
) -> None:
    pygame.draw.line(surface, color, start, end, width)
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = max(1.0, math.hypot(dx, dy))
    ux = dx / length
    uy = dy / length
    px = -uy
    py = ux
    left = (
        int(end[0] - ux * head + px * (head * 0.5)),
        int(end[1] - uy * head + py * (head * 0.5)),
    )
    right = (
        int(end[0] - ux * head - px * (head * 0.5)),
        int(end[1] - uy * head - py * (head * 0.5)),
    )
    pygame.draw.polygon(surface, color, [end, left, right])


def _draw_translation_box(surface: pygame.Surface, fonts, rect: pygame.Rect) -> None:
    title = fonts.hint_font.render("Translation", True, _LABEL_COLOR)
    surface.blit(title, (rect.x + 8, rect.y + 6))

    cx = rect.centerx
    cy = rect.centery + 6
    body = pygame.Rect(0, 0, 22, 22)
    body.center = (cx, cy)
    pygame.draw.rect(surface, _ACCENT, body, width=2, border_radius=4)

    _draw_arrow(surface, start=(cx - 16, cy), end=(cx - 38, cy), color=_ARROW)
    _draw_arrow(surface, start=(cx + 16, cy), end=(cx + 38, cy), color=_ARROW)
    _draw_arrow(surface, start=(cx, cy - 16), end=(cx, cy - 38), color=_ARROW)
    _draw_arrow(surface, start=(cx, cy + 16), end=(cx, cy + 38), color=_ARROW)

    left_label = fonts.hint_font.render("Left", True, _LABEL_COLOR)
    right_label = fonts.hint_font.render("Right", True, _LABEL_COLOR)
    up_label = fonts.hint_font.render("Away", True, _LABEL_COLOR)
    down_label = fonts.hint_font.render("Closer", True, _LABEL_COLOR)
    key_label = fonts.hint_font.render("Arrow keys", True, _ACCENT)

    surface.blit(left_label, (cx - 56 - left_label.get_width(), cy - 8))
    surface.blit(right_label, (cx + 48, cy - 8))
    surface.blit(up_label, (cx - up_label.get_width() // 2, cy - 58))
    surface.blit(down_label, (cx - down_label.get_width() // 2, cy + 42))
    surface.blit(key_label, (rect.x + 8, rect.bottom - key_label.get_height() - 6))


def _draw_rotation_box(surface: pygame.Surface, fonts, rect: pygame.Rect) -> None:
    title = fonts.hint_font.render("Rotation", True, _LABEL_COLOR)
    surface.blit(title, (rect.x + 8, rect.y + 6))

    cx = rect.centerx
    cy = rect.centery + 2
    ring = pygame.Rect(0, 0, 54, 54)
    ring.center = (cx, cy)
    pygame.draw.ellipse(surface, _ACCENT, ring, width=2)

    _draw_arrow(surface, start=(cx + 22, cy), end=(cx + 8, cy - 15), color=_ARROW)
    _draw_arrow(surface, start=(cx - 22, cy), end=(cx - 8, cy + 15), color=_ARROW)

    pairs = (
        "2D: Q/A",
        "3D: Q/A W/S E/D",
        "4D: + R/F",
    )
    y = rect.y + 30
    for text in pairs:
        surf = fonts.hint_font.render(text, True, _LABEL_COLOR)
        surface.blit(surf, (rect.x + 8, y))
        y += surf.get_height() + 2

    hint = fonts.hint_font.render("Column pairs = axis-plane turns", True, _ACCENT)
    surface.blit(hint, (rect.x + 8, rect.bottom - hint.get_height() - 6))


def _draw_box_container(surface: pygame.Surface, rect: pygame.Rect) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _BOX_BG, panel.get_rect(), border_radius=9)
    pygame.draw.rect(panel, (92, 116, 168), panel.get_rect(), width=1, border_radius=9)
    surface.blit(panel, rect.topleft)


def draw_translation_rotation_guides(
    surface: pygame.Surface,
    fonts,
    *,
    rect: pygame.Rect,
    title: str = "Control Guides",
    elapsed_ms: int | None = None,
) -> None:
    del elapsed_ms  # kept for API compatibility with previous animated implementation
    if rect.width < 140 or rect.height < 82:
        return

    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _PANEL_BG, panel.get_rect(), border_radius=11)
    surface.blit(panel, rect.topleft)

    title_surf = fonts.hint_font.render(title, True, _LABEL_COLOR)
    surface.blit(title_surf, (rect.x + 10, rect.y + 6))

    inner_y = rect.y + title_surf.get_height() + 11
    inner_h = rect.bottom - inner_y - 8
    if inner_h < 28:
        return

    gap = 10
    if rect.width < 320:
        box_w = rect.width - 20
        box_h = (inner_h - gap) // 2
        if box_h < 30:
            return
        left = pygame.Rect(rect.x + 10, inner_y, box_w, box_h)
        right = pygame.Rect(rect.x + 10, left.bottom + gap, box_w, box_h)
    else:
        box_w = (rect.width - 30 - gap) // 2
        left = pygame.Rect(rect.x + 10, inner_y, box_w, inner_h)
        right = pygame.Rect(left.right + gap, inner_y, box_w, inner_h)

    _draw_box_container(surface, left)
    _draw_box_container(surface, right)
    _draw_translation_box(surface, fonts, left)
    _draw_rotation_box(surface, fonts, right)
