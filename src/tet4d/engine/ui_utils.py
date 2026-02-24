from __future__ import annotations

from collections import OrderedDict
from typing import Tuple

import pygame

from .project_config import project_constant_int

Color3 = Tuple[int, int, int]
_GRADIENT_CACHE_MAX = project_constant_int(
    ("cache_limits", "gradient_surface_max"),
    16,
    min_value=1,
    max_value=1024,
)
_GRADIENT_CACHE: OrderedDict[tuple[int, int, Color3, Color3], pygame.Surface] = OrderedDict()


def fit_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    if max_width <= 8:
        return ""
    if font.size(text)[0] <= max_width:
        return text
    ellipsis = "..."
    if font.size(ellipsis)[0] >= max_width:
        return ""
    trimmed = text
    while trimmed and font.size(trimmed + ellipsis)[0] > max_width:
        trimmed = trimmed[:-1]
    return trimmed + ellipsis if trimmed else ""


def _gradient_surface(width: int, height: int, top_color: Color3, bottom_color: Color3) -> pygame.Surface:
    key = (width, height, top_color, bottom_color)
    cached = _GRADIENT_CACHE.get(key)
    if cached is not None:
        _GRADIENT_CACHE.move_to_end(key)
        return cached

    gradient = pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
        pygame.draw.line(gradient, color, (0, y), (width, y))

    _GRADIENT_CACHE[key] = gradient
    _GRADIENT_CACHE.move_to_end(key)
    if len(_GRADIENT_CACHE) > _GRADIENT_CACHE_MAX:
        _GRADIENT_CACHE.popitem(last=False)
    return gradient


def draw_vertical_gradient(surface: pygame.Surface, top_color: Color3, bottom_color: Color3) -> None:
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return
    surface.blit(_gradient_surface(width, height, top_color, bottom_color), (0, 0))
