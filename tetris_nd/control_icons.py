from __future__ import annotations

import math

import pygame


_ICON_BG = (12, 18, 38, 180)
_ICON_BORDER = (88, 114, 170)
_ICON_FG = (224, 236, 252)
_ICON_ACCENT = (124, 214, 255)


def _draw_arrow(
    surface: pygame.Surface,
    *,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    width: int = 2,
    head: int = 6,
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
        int(end[0] - ux * head + px * (head * 0.45)),
        int(end[1] - uy * head + py * (head * 0.45)),
    )
    right = (
        int(end[0] - ux * head - px * (head * 0.45)),
        int(end[1] - uy * head - py * (head * 0.45)),
    )
    pygame.draw.polygon(surface, color, [end, left, right])


def _draw_icon_frame(surface: pygame.Surface, rect: pygame.Rect) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _ICON_BG, panel.get_rect(), border_radius=6)
    pygame.draw.rect(panel, _ICON_BORDER, panel.get_rect(), width=1, border_radius=6)
    surface.blit(panel, rect.topleft)


def _draw_move_icon(surface: pygame.Surface, rect: pygame.Rect, axis: str, direction: int) -> None:
    cx = rect.centerx
    cy = rect.centery
    span = max(6, min(rect.width, rect.height) // 2 - 4)

    if axis == "x":
        start = (cx - span, cy)
        end = (cx + span, cy)
    elif axis == "z":
        start = (cx, cy + span)
        end = (cx, cy - span)
    else:  # w-axis visualized as diagonal in icon space
        start = (cx - span + 2, cy + span - 2)
        end = (cx + span - 2, cy - span + 2)

    if direction < 0:
        start, end = end, start
    _draw_arrow(surface, start=start, end=end, color=_ICON_FG)

    if axis == "w":
        label = pygame.font.Font(None, 16).render("W", True, _ICON_ACCENT)
        surface.blit(label, (rect.x + 4, rect.y + 2))


def _draw_drop_icon(surface: pygame.Surface, rect: pygame.Rect, hard: bool) -> None:
    cx = rect.centerx
    top = rect.y + 5
    bottom = rect.bottom - 5
    _draw_arrow(surface, start=(cx, top), end=(cx, bottom), color=_ICON_FG)
    if hard:
        _draw_arrow(surface, start=(cx - 6, top + 4), end=(cx - 6, bottom), color=_ICON_ACCENT)
        _draw_arrow(surface, start=(cx + 6, top + 4), end=(cx + 6, bottom), color=_ICON_ACCENT)


def _rotation_plane_label(action: str) -> str:
    parts = action.split("_")
    if len(parts) >= 3:
        return parts[1].upper()
    return "R"


def _rotation_direction(action: str) -> int:
    return -1 if action.endswith("_neg") else 1


def _draw_rotate_icon(surface: pygame.Surface, rect: pygame.Rect, action: str) -> None:
    direction = _rotation_direction(action)
    ring = rect.inflate(-10, -10)
    start_ang = math.radians(210 if direction > 0 else 30)
    end_ang = math.radians(20 if direction > 0 else 200)
    pygame.draw.arc(surface, _ICON_FG, ring, start_ang, end_ang, 2)

    if direction > 0:
        tip = (ring.right - 2, ring.centery - 2)
        tail = (tip[0] - 7, tip[1] + 5)
    else:
        tip = (ring.left + 2, ring.centery + 2)
        tail = (tip[0] + 7, tip[1] - 5)
    _draw_arrow(surface, start=tail, end=tip, color=_ICON_FG, width=2, head=5)

    label = pygame.font.Font(None, 14).render(_rotation_plane_label(action), True, _ICON_ACCENT)
    surface.blit(label, (rect.centerx - label.get_width() // 2, rect.bottom - label.get_height() - 2))


def action_icon_action(action: str | None) -> str | None:
    if not action:
        return None
    if action.startswith("move_"):
        return action
    if action.startswith("rotate_"):
        return action
    if action in {"soft_drop", "hard_drop"}:
        return action
    return None


def draw_action_icon(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    action: str | None,
) -> None:
    mapped = action_icon_action(action)
    if mapped is None or rect.width < 14 or rect.height < 14:
        return

    _draw_icon_frame(surface, rect)

    if mapped == "move_x_neg":
        _draw_move_icon(surface, rect, axis="x", direction=-1)
        return
    if mapped == "move_x_pos":
        _draw_move_icon(surface, rect, axis="x", direction=1)
        return
    if mapped == "move_z_neg":
        _draw_move_icon(surface, rect, axis="z", direction=-1)
        return
    if mapped == "move_z_pos":
        _draw_move_icon(surface, rect, axis="z", direction=1)
        return
    if mapped == "move_w_neg":
        _draw_move_icon(surface, rect, axis="w", direction=-1)
        return
    if mapped == "move_w_pos":
        _draw_move_icon(surface, rect, axis="w", direction=1)
        return
    if mapped == "soft_drop":
        _draw_drop_icon(surface, rect, hard=False)
        return
    if mapped == "hard_drop":
        _draw_drop_icon(surface, rect, hard=True)
        return

    _draw_rotate_icon(surface, rect, mapped)
