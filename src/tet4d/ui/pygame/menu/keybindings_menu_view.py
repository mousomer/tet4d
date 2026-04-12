from __future__ import annotations

from typing import Any

import pygame

from tet4d.engine.runtime.menu_config import ui_copy_section
from tet4d.engine.ui_logic.keybindings_catalog import binding_action_description
from tet4d.ui.pygame.input.key_display import format_key_tuple
from tet4d.ui.pygame.menu.keybindings_menu_model import binding_keys, binding_title
from tet4d.ui.pygame.render.control_icons import draw_action_icon
from tet4d.ui.pygame.ui_utils import (
    compute_vertical_scroll_metrics,
    draw_corner_chip,
    draw_selection_highlight,
    draw_tron_menu_background,
    draw_tron_panel,
    draw_vertical_scrollbar,
    ensure_scroll_offset_visible,
    fit_text,
    format_menu_title,
    standard_menu_panel_rect,
)

_KEYBINDINGS_MENU_COPY = ui_copy_section("keybindings_menu")


def _draw_background(surface: pygame.Surface) -> None:
    draw_tron_menu_background(surface, top_color=(14, 18, 42), bottom_color=(4, 7, 20))


def _draw_menu_header(surface: pygame.Surface, fonts, state: Any, scope_label_fn) -> None:
    width, _ = surface.get_size()
    title = fonts.title_font.render(
        format_menu_title(_KEYBINDINGS_MENU_COPY["title"]), True, (232, 232, 240)
    )
    surface.blit(title, ((width - title.get_width()) // 2, 28))
    draw_corner_chip(surface, font=fonts.hint_font, text="Back", x=18, y=18)

    header = (
        f"Scope: {scope_label_fn(state.scope)}   "
        f"Profile: {state.active_profile}   "
        f"Conflict: {state.conflict_mode}"
    )
    header_surf = fonts.hint_font.render(
        fit_text(fonts.hint_font, header, width - 28), True, (210, 220, 245)
    )
    surface.blit(header_surf, ((width - header_surf.get_width()) // 2, 74))


def _panel_geometry(surface: pygame.Surface) -> pygame.Rect:
    width, height = surface.get_size()
    panel_w = min(1120, max(320, width - 40))
    panel_h = min(580, max(220, height - 260))
    return standard_menu_panel_rect(
        surface,
        panel_w=panel_w,
        panel_h=panel_h,
        panel_top=98,
        bottom_reserved=102,
    )


def _draw_panel(surface: pygame.Surface, *, panel_rect: pygame.Rect) -> None:
    draw_tron_panel(surface, rect=panel_rect)


def _selected_render_index(
    state: Any,
    rendered_rows: list[Any],
    binding_rows: list[Any],
) -> int:
    if not binding_rows:
        return 0
    state.selected_binding = max(0, min(len(binding_rows) - 1, state.selected_binding))
    selected_row = binding_rows[state.selected_binding]
    for idx, rendered in enumerate(rendered_rows):
        if rendered.binding == selected_row:
            return idx
    return 0


def _draw_row_selection(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    flash_strength: float = 0.0,
) -> None:
    draw_selection_highlight(surface, rect=rect, border_radius=8)
    if flash_strength > 0.0:
        draw_selection_highlight(
            surface,
            rect=rect,
            color=(112, 236, 255, min(120, int(42 + (78 * flash_strength)))),
            border_radius=8,
        )


def _draw_binding_row(
    surface: pygame.Surface,
    fonts,
    row: Any,
    *,
    flash_frames: int,
    selected: bool,
    scope: str,
    draw_rect: pygame.Rect,
) -> None:
    color = (255, 224, 130) if selected else (228, 230, 242)
    row_font = fonts.menu_font
    if selected:
        _draw_row_selection(
            surface,
            rect=draw_rect.inflate(0, 4),
            flash_strength=max(0.0, min(1.0, flash_frames / 12.0)),
        )

    label = binding_title(row, scope)
    desc = binding_action_description(row.action)
    key_text = format_key_tuple(binding_keys(row))

    left_x = draw_rect.x + 8
    right_x = draw_rect.right - 8
    max_key_w = max(56, int(draw_rect.width * 0.34))
    key_draw = fit_text(row_font, key_text, max_key_w)
    key_surf = row_font.render(key_draw, True, color)
    key_x = right_x - key_surf.get_width()
    label_width = max(0, key_x - left_x - 10)
    label_draw = fit_text(row_font, label, label_width)
    label_surf = row_font.render(label_draw, True, color)

    surface.blit(label_surf, (left_x, draw_rect.y))
    surface.blit(key_surf, (key_x, draw_rect.y))

    desc_y = draw_rect.y + row_font.get_height() + 1
    icon_rect = pygame.Rect(left_x, desc_y - 1, 20, fonts.hint_font.get_height() + 2)
    draw_action_icon(surface, rect=icon_rect, action=row.action)
    desc_x = icon_rect.right + 6
    desc_width = max(0, right_x - desc_x)
    desc_draw = fit_text(fonts.hint_font, desc, desc_width)
    desc_surf = fonts.hint_font.render(desc_draw, True, (168, 182, 215))
    surface.blit(desc_surf, (desc_x, desc_y))


def _draw_binding_rows(
    surface: pygame.Surface,
    fonts,
    *,
    state: Any,
    rendered_rows: list[Any],
    binding_rows: list[Any],
    viewport_rect: pygame.Rect,
) -> None:
    row_h = fonts.menu_font.get_height() + fonts.hint_font.get_height() + 12
    content_height = len(rendered_rows) * row_h
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=state.scroll_offset,
    )
    selected_render_index = _selected_render_index(state, rendered_rows, binding_rows)
    selected_top = selected_render_index * row_h
    state.scroll_offset = ensure_scroll_offset_visible(
        metrics.scroll_offset,
        item_top=selected_top,
        item_bottom=selected_top + row_h,
        viewport_height=metrics.viewport_height,
        content_height=content_height,
    )
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=state.scroll_offset,
    )

    content_rect = viewport_rect.copy()
    content_rect.width -= metrics.reserved_width
    previous_clip = surface.get_clip()
    surface.set_clip(viewport_rect)
    selected_binding = binding_rows[state.selected_binding] if binding_rows else None
    for idx, row in enumerate(rendered_rows):
        draw_y = content_rect.y + (idx * row_h) - metrics.scroll_offset
        draw_rect = pygame.Rect(content_rect.x, draw_y, content_rect.width, row_h)
        if draw_rect.bottom < viewport_rect.y or draw_rect.top > viewport_rect.bottom:
            continue
        if row.kind == "header":
            header_color = (170, 186, 224) if row.text else (132, 142, 172)
            surf = fonts.hint_font.render(row.text, True, header_color)
            header_y = draw_rect.y + (row_h - surf.get_height()) // 2
            surface.blit(surf, (draw_rect.x + 6, header_y))
            continue
        if row.binding is None:
            continue
        _draw_binding_row(
            surface,
            fonts,
            row.binding,
            flash_frames=state.flash_selected_frames,
            selected=(row.binding == selected_binding),
            scope=state.scope,
            draw_rect=draw_rect,
        )
    surface.set_clip(previous_clip)
    draw_vertical_scrollbar(surface, metrics=metrics)


def _draw_hints(
    surface: pygame.Surface,
    fonts,
    state: Any,
    panel_y: int,
    panel_h: int,
    scope_file_hint_fn,
) -> int:
    width, height = surface.get_size()
    scope_hint = scope_file_hint_fn(state.scope)
    hints = tuple(
        str(item).format(scope_file_hint=scope_hint)
        for item in _KEYBINDINGS_MENU_COPY["hints"]
    )
    hint_y = panel_y + panel_h + 12
    max_w = max(80, width - 36)
    line_h = fonts.hint_font.get_height() + 3
    max_lines = max(0, (height - hint_y - 6) // max(1, line_h))
    draw_lines = hints[:max_lines]
    for line in draw_lines:
        line_draw = fit_text(fonts.hint_font, line, max_w)
        surf = fonts.hint_font.render(line_draw, True, (188, 197, 228))
        surface.blit(surf, ((width - surf.get_width()) // 2, hint_y))
        hint_y += surf.get_height() + 3
    return hint_y


def _draw_capture_hint(
    surface: pygame.Surface,
    fonts,
    state: Any,
    binding_rows: list[Any],
    hint_y: int,
) -> int:
    if not state.capture_mode or not binding_rows:
        return hint_y
    width, height = surface.get_size()
    if hint_y + fonts.hint_font.get_height() + 4 > height - 4:
        return hint_y
    selected = binding_rows[state.selected_binding]
    max_w = max(80, width - 36)
    cap_text = fit_text(
        fonts.hint_font,
        _KEYBINDINGS_MENU_COPY["capture_template"].format(
            binding_title=binding_title(selected, state.scope)
        ),
        max_w,
    )
    cap = fonts.hint_font.render(cap_text, True, (255, 226, 144))
    surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
    return hint_y + cap.get_height() + 4


def _draw_text_mode_hint(
    surface: pygame.Surface,
    fonts,
    state: Any,
    hint_y: int,
    text_mode_label_fn,
) -> int:
    if not state.text_mode:
        return hint_y
    width, height = surface.get_size()
    if hint_y + (fonts.hint_font.get_height() * 2) + 10 > height - 4:
        return hint_y
    max_w = max(80, width - 36)
    prompt = fit_text(
        fonts.hint_font,
        f"{text_mode_label_fn(state.text_mode)}: {state.text_buffer}_",
        max_w,
    )
    cap = fonts.hint_font.render(prompt, True, (255, 226, 144))
    surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
    hint_y += cap.get_height() + 4
    tip = fonts.hint_font.render(
        fit_text(
            fonts.hint_font,
            _KEYBINDINGS_MENU_COPY["text_mode_confirm_hint"],
            max_w,
        ),
        True,
        (188, 197, 228),
    )
    surface.blit(tip, ((width - tip.get_width()) // 2, hint_y + 2))
    return hint_y + tip.get_height() + 4


def _draw_status(surface: pygame.Surface, fonts, state: Any, hint_y: int) -> None:
    if not state.status:
        return
    width, height = surface.get_size()
    if hint_y + fonts.hint_font.get_height() + 4 > height - 4:
        return
    color = (255, 150, 150) if state.status_error else (170, 240, 170)
    status_text = fit_text(fonts.hint_font, state.status, max(80, width - 36))
    status = fonts.hint_font.render(status_text, True, color)
    surface.blit(status, ((width - status.get_width()) // 2, hint_y + 2))


def draw_section_menu(
    surface: pygame.Surface,
    fonts,
    state: Any,
    *,
    section_menu: tuple[tuple[str, str, str], ...],
    scope_label_fn,
    text_mode_label_fn,
) -> None:
    _draw_background(surface)
    _draw_menu_header(surface, fonts, state, scope_label_fn)
    panel_rect = _panel_geometry(surface)
    _draw_panel(surface, panel_rect=panel_rect)

    row_h = fonts.menu_font.get_height() + fonts.hint_font.get_height() + 14
    viewport_rect = pygame.Rect(
        panel_rect.x + 16,
        panel_rect.y + 12,
        panel_rect.width - 32,
        panel_rect.height - 20,
    )
    content_height = len(section_menu) * row_h
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=state.scroll_offset,
    )
    selected_top = max(0, state.selected_section) * row_h
    state.scroll_offset = ensure_scroll_offset_visible(
        metrics.scroll_offset,
        item_top=selected_top,
        item_bottom=selected_top + row_h,
        viewport_height=metrics.viewport_height,
        content_height=content_height,
    )
    metrics = compute_vertical_scroll_metrics(
        viewport_rect=viewport_rect,
        content_height=content_height,
        scroll_offset=state.scroll_offset,
    )
    content_rect = viewport_rect.copy()
    content_rect.width -= metrics.reserved_width
    previous_clip = surface.get_clip()
    surface.set_clip(viewport_rect)
    for idx, (_scope, title, description) in enumerate(section_menu):
        draw_y = content_rect.y + (idx * row_h) - metrics.scroll_offset
        draw_rect = pygame.Rect(content_rect.x, draw_y, content_rect.width, row_h)
        if draw_rect.bottom < viewport_rect.y or draw_rect.top > viewport_rect.bottom:
            continue
        selected = idx == state.selected_section
        color = (255, 224, 130) if selected else (228, 230, 242)
        if selected:
            _draw_row_selection(surface, rect=draw_rect.inflate(0, 4))
        title_surf = fonts.menu_font.render(
            fit_text(fonts.menu_font, title, draw_rect.width),
            True,
            color,
        )
        desc_surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, description, draw_rect.width),
            True,
            (168, 182, 215),
        )
        surface.blit(title_surf, (draw_rect.x + 8, draw_rect.y))
        surface.blit(
            desc_surf,
            (draw_rect.x + 8, draw_rect.y + fonts.menu_font.get_height() + 1),
        )
    surface.set_clip(previous_clip)
    draw_vertical_scrollbar(surface, metrics=metrics)

    width, height = surface.get_size()
    hints = tuple(_KEYBINDINGS_MENU_COPY["section_hints"])
    hy = panel_rect.y + panel_rect.height + 10
    line_h = fonts.hint_font.get_height() + 3
    max_lines = max(0, (height - hy - 6) // max(1, line_h))
    hint_budget = max(
        0,
        max_lines - (1 if state.text_mode else 0) - (1 if state.status else 0),
    )
    for line in hints[:hint_budget]:
        surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, line, width - 36), True, (188, 197, 228)
        )
        surface.blit(surf, ((width - surf.get_width()) // 2, hy))
        hy += surf.get_height() + 3
    hy = _draw_text_mode_hint(surface, fonts, state, hy, text_mode_label_fn)
    if state.status:
        _draw_status(surface, fonts, state, hy)


def draw_binding_menu(
    surface: pygame.Surface,
    fonts,
    state: Any,
    *,
    rendered_rows: list[Any],
    binding_rows: list[Any],
    scope_label_fn,
    scope_file_hint_fn,
    text_mode_label_fn,
) -> None:
    _draw_background(surface)
    _draw_menu_header(surface, fonts, state, scope_label_fn)
    panel_rect = _panel_geometry(surface)
    _draw_panel(surface, panel_rect=panel_rect)
    viewport_rect = pygame.Rect(
        panel_rect.x + 16,
        panel_rect.y + 12,
        panel_rect.width - 32,
        panel_rect.height - 20,
    )
    _draw_binding_rows(
        surface,
        fonts,
        state=state,
        rendered_rows=rendered_rows,
        binding_rows=binding_rows,
        viewport_rect=viewport_rect,
    )
    hint_y = _draw_hints(
        surface,
        fonts,
        state,
        panel_rect.y,
        panel_rect.height,
        scope_file_hint_fn,
    )
    hint_y = _draw_capture_hint(surface, fonts, state, binding_rows, hint_y)
    hint_y = _draw_text_mode_hint(surface, fonts, state, hint_y, text_mode_label_fn)
    _draw_status(surface, fonts, state, hint_y)
