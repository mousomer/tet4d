from __future__ import annotations

import math

import pygame


_ICON_FG = (224, 236, 252)
_ICON_CACHE_LIMIT = 192
_ICON_SURFACE_CACHE: dict[tuple[str, int, int], pygame.Surface] = {}
_MOVE_ICON_MAP: dict[str, tuple[str, int]] = {
    "move_x_neg": ("x", -1),
    "move_x_pos": ("x", 1),
    "move_y_neg": ("y", -1),
    "move_y_pos": ("y", 1),
    "move_z_neg": ("z", -1),
    "move_z_pos": ("z", 1),
    "move_w_neg": ("w", -1),
    "move_w_pos": ("w", 1),
}


def clear_action_icon_cache() -> None:
    _ICON_SURFACE_CACHE.clear()


def action_icon_cache_size() -> int:
    return len(_ICON_SURFACE_CACHE)


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


def _draw_move_icon(surface: pygame.Surface, rect: pygame.Rect, axis: str, direction: int) -> None:
    cx = rect.centerx
    cy = rect.centery
    span = max(6, min(rect.width, rect.height) // 2 - 4)

    if axis == "x":
        start = (cx - span, cy)
        end = (cx + span, cy)
    elif axis == "y":
        start = (cx, cy - span)
        end = (cx, cy + span)
    elif axis == "z":
        start = (cx, cy + span)
        end = (cx, cy - span)
    else:  # w-axis visualized as diagonal in icon space
        start = (cx - span + 2, cy + span - 2)
        end = (cx + span - 2, cy - span + 2)

    if direction < 0:
        start, end = end, start
    _draw_arrow(surface, start=start, end=end, color=_ICON_FG)


def _draw_drop_icon(surface: pygame.Surface, rect: pygame.Rect, hard: bool) -> None:
    cx = rect.centerx
    top = rect.y + 5
    bottom = rect.bottom - 5
    _draw_arrow(surface, start=(cx, top), end=(cx, bottom), color=_ICON_FG)
    if hard:
        _draw_arrow(surface, start=(cx, top + 4), end=(cx, bottom), color=_ICON_FG)


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
    icon = _cached_icon_surface(mapped, rect.width, rect.height)
    surface.blit(icon, rect.topleft)


def _cached_icon_surface(action: str, width: int, height: int) -> pygame.Surface:
    key = (action, width, height)
    cached = _ICON_SURFACE_CACHE.get(key)
    if cached is not None:
        return cached
    icon = _build_icon_surface(action, width=width, height=height)
    if len(_ICON_SURFACE_CACHE) >= _ICON_CACHE_LIMIT:
        _ICON_SURFACE_CACHE.clear()
    _ICON_SURFACE_CACHE[key] = icon
    return icon


def _build_icon_surface(action: str, *, width: int, height: int) -> pygame.Surface:
    icon = pygame.Surface((width, height), pygame.SRCALPHA)
    icon_rect = icon.get_rect()
    move_spec = _MOVE_ICON_MAP.get(action)
    if move_spec is not None:
        axis, direction = move_spec
        _draw_move_icon(icon, icon_rect, axis=axis, direction=direction)
        return icon
    if action == "soft_drop":
        _draw_drop_icon(icon, icon_rect, hard=False)
        return icon
    if action == "hard_drop":
        _draw_drop_icon(icon, icon_rect, hard=True)
        return icon
    _draw_rotate_icon(icon, icon_rect, action)
    return icon
