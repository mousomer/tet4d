from __future__ import annotations

from collections import OrderedDict
import re
from typing import Tuple

import pygame

from tet4d.engine.runtime.project_config import project_constant_color, project_constant_int

Color3 = Tuple[int, int, int]


def button_bg() -> Color3:
    return project_constant_color(("button", "bg"), (38, 44, 70))


def button_active() -> Color3:
    return project_constant_color(("button", "active"), (86, 98, 146))


def button_text() -> Color3:
    return project_constant_color(("button", "text"), (232, 236, 248))


def button_border() -> Color3:
    return project_constant_color(("button", "border"), (16, 18, 26))


def panel_bg() -> Color3:
    return project_constant_color(("panel", "bg"), (18, 22, 38))


def panel_border() -> Color3:
    return project_constant_color(("panel", "border"), (76, 84, 112))

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


def format_menu_title(text: str) -> str:
    raw = str(text).strip()
    if not raw:
        return ""
    words = re.split(r"(\s+)", raw)
    out: list[str] = []
    for word in words:
        if not word or word.isspace():
            out.append(word)
            continue
        lower = word.lower()
        if lower in {"2d", "3d", "4d"}:
            out.append(lower[:-1] + "D")
            continue
        out.append(word[0].upper() + word[1:])
    return "".join(out)


def draw_tron_menu_background(
    surface: pygame.Surface,
    *,
    top_color: Color3 = (10, 18, 44),
    bottom_color: Color3 = (1, 6, 18),
    line_color: tuple[int, int, int, int] = (52, 214, 255, 22),
) -> None:
    draw_vertical_gradient(surface, top_color, bottom_color)
    width, height = surface.get_size()
    if width <= 0 or height <= 0:
        return
    overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    spacing = max(28, min(52, width // 18 if width > 0 else 32))
    for y in range(0, height, spacing):
        pygame.draw.line(overlay, line_color, (0, y), (width, y), 1)
    for x in range(0, width, spacing):
        pygame.draw.line(overlay, line_color, (x, 0), (x, height), 1)
    pygame.draw.line(
        overlay,
        (92, 238, 255, 38),
        (0, int(height * 0.72)),
        (width, int(height * 0.62)),
        2,
    )
    surface.blit(overlay, (0, 0))


def draw_tron_panel(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fill_color: tuple[int, int, int, int] = (3, 10, 28, 188),
    glow_color: tuple[int, int, int, int] = (84, 220, 255, 42),
    border_color: tuple[int, int, int] = (92, 238, 255),
    border_radius: int = 14,
) -> None:
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(panel, fill_color, panel.get_rect(), border_radius=border_radius)
    pygame.draw.rect(panel, glow_color, panel.get_rect(), 3, border_radius=border_radius)
    pygame.draw.rect(panel, border_color, panel.get_rect(), 1, border_radius=border_radius)
    surface.blit(panel, rect.topleft)


def standard_menu_panel_rect(
    surface: pygame.Surface,
    *,
    panel_w: int,
    panel_h: int,
    panel_top: int,
    bottom_reserved: int,
    bottom_margin: int = 8,
) -> pygame.Rect:
    width, height = surface.get_size()
    rect = pygame.Rect(0, 0, panel_w, panel_h)
    rect.x = (width - panel_w) // 2
    rect.y = max(
        panel_top,
        min(
            (height - panel_h) // 2,
            height - bottom_reserved - panel_h - bottom_margin,
        ),
    )
    return rect


def default_menu_back_chip_rect(
    *,
    x: int = 18,
    y: int = 18,
    label: str = "Back",
) -> pygame.Rect:
    width = max(78, 22 + (len(str(label).strip()) * 10))
    return pygame.Rect(x, y, width, 34)


def draw_corner_chip(
    surface: pygame.Surface,
    *,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    fill_color: tuple[int, int, int, int] = (2, 18, 34, 210),
    border_color: tuple[int, int, int] = (92, 238, 255),
    text_color: Color3 = (212, 242, 255),
    border_radius: int = 10,
) -> pygame.Rect:
    text_surf = font.render(text, True, text_color)
    rect = pygame.Rect(x, y, text_surf.get_width() + 18, text_surf.get_height() + 10)
    chip = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(chip, fill_color, chip.get_rect(), border_radius=border_radius)
    pygame.draw.rect(chip, border_color, chip.get_rect(), 1, border_radius=border_radius)
    surface.blit(chip, rect.topleft)
    surface.blit(text_surf, (rect.x + 9, rect.y + 5))
    return rect


def draw_value_slider(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    fraction: float,
    flash_strength: float = 0.0,
    track_color: tuple[int, int, int] = (32, 56, 84),
    fill_color: tuple[int, int, int] = (78, 222, 255),
    border_color: tuple[int, int, int] = (124, 244, 255),
) -> None:
    clamped = max(0.0, min(1.0, float(fraction)))
    flash = max(0.0, min(1.0, float(flash_strength)))
    track = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(track, (*track_color, 220), track.get_rect(), border_radius=6)
    pygame.draw.rect(track, border_color, track.get_rect(), 1, border_radius=6)
    fill_width = max(6, int((rect.width - 2) * clamped))
    fill_rect = pygame.Rect(1, 1, max(0, fill_width), max(0, rect.height - 2))
    fill = (
        min(255, int(fill_color[0] + (40 * flash))),
        min(255, int(fill_color[1] + (30 * flash))),
        min(255, int(fill_color[2] + (20 * flash))),
        min(255, int(190 + (50 * flash))),
    )
    pygame.draw.rect(track, fill, fill_rect, border_radius=5)
    knob_x = rect.x + max(0, min(rect.width - 8, fill_width - 4))
    surface.blit(track, rect.topleft)
    pygame.draw.rect(
        surface,
        (
            min(255, int(224 + (24 * flash))),
            min(255, int(248 + (7 * flash))),
            255,
        ),
        pygame.Rect(knob_x, rect.y - 2, 8, rect.height + 4),
        border_radius=4,
    )
