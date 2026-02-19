from __future__ import annotations

from collections import OrderedDict

import pygame

from .project_config import project_constant_int

_TEXT_SURFACE_CACHE_MAX = project_constant_int(
    ("cache_limits", "text_surface_max"),
    3072,
    min_value=128,
    max_value=65536,
)
_TEXT_SURFACE_CACHE: OrderedDict[
    tuple[int, bool, str, tuple[int, int, int]],
    pygame.Surface,
] = OrderedDict()


def render_text_cached(
    *,
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    antialias: bool = True,
) -> pygame.Surface:
    key = (id(font), antialias, text, color)
    cached = _TEXT_SURFACE_CACHE.get(key)
    if cached is not None:
        _TEXT_SURFACE_CACHE.move_to_end(key)
        return cached

    rendered = font.render(text, antialias, color)
    _TEXT_SURFACE_CACHE[key] = rendered
    _TEXT_SURFACE_CACHE.move_to_end(key)
    if len(_TEXT_SURFACE_CACHE) > _TEXT_SURFACE_CACHE_MAX:
        _TEXT_SURFACE_CACHE.popitem(last=False)
    return rendered
