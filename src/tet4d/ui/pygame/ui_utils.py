from __future__ import annotations

from collections import OrderedDict
from typing import Tuple

import pygame

from tet4d.engine.runtime.project_config import project_constant_int

Color3 = Tuple[int, int, int]
_GRADIENT_CACHE_MAX = project_constant_int(
    ("cache_limits", "gradient_surface_max"),
    16,
    min_value=1,
    max_value=1024,
)
_GRADIENT_CACHE: OrderedDict[tuple[int, int, Color3, Color3], pygame.Surface] = (
    OrderedDict()
)


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


def text_fits(font: pygame.font.Font, text: str, max_width: int) -> bool:
    if max_width <= 0:
        return False
    return font.size(str(text))[0] <= int(max_width)


def text_truncates(font: pygame.font.Font, text: str, max_width: int) -> bool:
    return fit_text(font, str(text), int(max_width)) != str(text)


def wrap_text_lines(
    font: pygame.font.Font,
    text: str,
    max_width: int,
) -> tuple[str, ...]:
    if max_width <= 8:
        return ("",)
    raw = str(text).strip()
    if not raw:
        return ("",)
    if font.size(raw)[0] <= max_width:
        return (raw,)
    words = raw.split()
    if not words:
        return ("",)
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.size(candidate)[0] <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)
    wrapped: list[str] = []
    for line in lines:
        if font.size(line)[0] <= max_width:
            wrapped.append(line)
            continue
        wrapped.append(fit_text(font, line, max_width))
    return tuple(item for item in wrapped if item)


def wrapped_row_height(
    font: pygame.font.Font,
    line_count: int,
    *,
    min_padding: int = 10,
    base_padding: int = 8,
    extra_padding_per_line: int = 3,
) -> int:
    safe_count = max(1, int(line_count))
    return safe_count * font.get_height() + max(
        int(min_padding),
        int(base_padding) + max(0, safe_count - 1) * int(extra_padding_per_line),
    )


def wrapped_label_value_layout(
    font: pygame.font.Font,
    *,
    label: str,
    value: str,
    total_width: int | None = None,
    label_width: int | None = None,
    value_width: int | None = None,
    value_width_fraction: float = 0.34,
    min_label_width: int = 80,
    horizontal_padding: int = 44,
    column_gap: int = 10,
) -> tuple[tuple[str, ...], tuple[str, ...], int]:
    if value_width is None:
        if total_width is None:
            raise ValueError("total_width is required when value_width is omitted")
        value_width = int(total_width * value_width_fraction) if value else 0
    value_lines = wrap_text_lines(font, value, value_width) if value else tuple()
    value_draw_width = (
        max(font.size(line)[0] for line in value_lines)
        if value_lines
        else 0
    )
    if label_width is None:
        if total_width is None:
            raise ValueError("total_width is required when label_width is omitted")
        remaining_width = (
            total_width - horizontal_padding - value_draw_width - column_gap
            if value_draw_width > 0
            else total_width - horizontal_padding
        )
        label_width = max(min_label_width, remaining_width)
    label_lines = wrap_text_lines(font, label, label_width)
    row_height = wrapped_row_height(
        font,
        max(len(label_lines), len(value_lines), 1),
    )
    return label_lines, value_lines, row_height


def draw_centered_wrapped_text(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    font: pygame.font.Font,
    text: str,
    color: Color3,
    max_lines: int = 2,
    line_gap: int = 2,
    text_width_padding: int = 10,
) -> tuple[str, ...]:
    wrapped = wrap_text_lines(font, text, rect.width - text_width_padding)
    lines = wrapped[: max(1, int(max_lines))] if wrapped else ("",)
    total_text_h = len(lines) * font.get_height() + max(0, len(lines) - 1) * line_gap
    y = rect.centery - total_text_h // 2
    for line in lines:
        text_surf = font.render(line, True, color)
        surface.blit(
            text_surf,
            (
                rect.centerx - text_surf.get_width() // 2,
                y,
            ),
        )
        y += font.get_height() + line_gap
    return lines


def draw_selection_highlight(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    color: tuple[int, int, int, int] = (255, 255, 255, 38),
    border_radius: int = 8,
) -> None:
    hi = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(hi, color, hi.get_rect(), border_radius=border_radius)
    surface.blit(hi, rect.topleft)


def draw_panel_frame(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fill_color: Color3,
    border_color: Color3,
    border_radius: int = 10,
    border_width: int = 1,
) -> None:
    pygame.draw.rect(surface, fill_color, rect, border_radius=border_radius)
    pygame.draw.rect(
        surface,
        border_color,
        rect,
        border_width,
        border_radius=border_radius,
    )


def draw_centered_chip(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    font: pygame.font.Font,
    text: str,
    text_color: Color3,
    fill_color: Color3 = (22, 28, 48),
    border_color: Color3 = (82, 96, 132),
    border_radius: int = 12,
    text_width_padding: int = 12,
) -> pygame.Surface:
    pygame.draw.rect(surface, fill_color, rect, border_radius=border_radius)
    pygame.draw.rect(surface, border_color, rect, 1, border_radius=border_radius)
    text_surf = draw_fitted_text_line(
        surface,
        font=font,
        text=text,
        color=text_color,
        max_width=rect.width - text_width_padding,
        center_x=rect.centerx,
        y=rect.y + (rect.height - font.get_height()) // 2,
    )
    return text_surf


def draw_wrapped_label_value_lines(
    surface: pygame.Surface,
    *,
    font: pygame.font.Font,
    label_lines: tuple[str, ...],
    value_lines: tuple[str, ...],
    label_x: int,
    value_right: int,
    top_y: int,
    label_color: Color3,
    value_color: Color3 | None = None,
    line_gap: int = 3,
) -> None:
    resolved_value_color = value_color or label_color
    label_y = top_y
    for line in label_lines:
        label_surf = font.render(line, True, label_color)
        surface.blit(label_surf, (label_x, label_y))
        label_y += font.get_height() + line_gap
    value_y = top_y
    for line in value_lines:
        value_surf = font.render(line, True, resolved_value_color)
        surface.blit(value_surf, (value_right - value_surf.get_width(), value_y))
        value_y += font.get_height() + line_gap


def draw_fitted_text_line(
    surface: pygame.Surface,
    *,
    font: pygame.font.Font,
    text: str,
    color: Color3,
    max_width: int,
    x: int | None = None,
    center_x: int | None = None,
    y: int,
) -> pygame.Surface:
    text_surf = font.render(fit_text(font, text, max_width), True, color)
    if center_x is not None:
        draw_x = center_x - text_surf.get_width() // 2
    elif x is not None:
        draw_x = x
    else:
        raise ValueError("x or center_x is required")
    surface.blit(text_surf, (draw_x, y))
    return text_surf


def _gradient_surface(
    width: int, height: int, top_color: Color3, bottom_color: Color3
) -> pygame.Surface:
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


def draw_vertical_gradient(
    surface: pygame.Surface, top_color: Color3, bottom_color: Color3
) -> None:
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return
    surface.blit(_gradient_surface(width, height, top_color, bottom_color), (0, 0))
