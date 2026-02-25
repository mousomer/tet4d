from __future__ import annotations

from typing import Any

import pygame

from .control_icons import draw_action_icon
from .key_display import format_key_tuple
from .keybindings import binding_action_description
from .ui_logic.keybindings_menu_model import (
    BindingRow,
    RenderedRow,
    binding_keys,
    binding_title,
)
from .ui_utils import draw_vertical_gradient, fit_text


def _draw_background(surface: pygame.Surface) -> None:
    draw_vertical_gradient(surface, (14, 18, 42), (4, 7, 20))


def _draw_menu_header(
    surface: pygame.Surface, fonts, state: Any, scope_label_fn
) -> None:
    width, _ = surface.get_size()
    title = fonts.title_font.render("Keybindings Setup", True, (232, 232, 240))
    subtitle_text = (
        "Up/Down select section, Enter open, Esc back"
        if state.section_mode
        else "Up/Down select, Enter rebind, Tab sections, Esc back"
    )
    subtitle = fonts.hint_font.render(subtitle_text, True, (192, 200, 228))
    surface.blit(title, ((width - title.get_width()) // 2, 28))
    surface.blit(subtitle, ((width - subtitle.get_width()) // 2, 74))

    header = (
        f"Scope: {scope_label_fn(state.scope)}   "
        f"Profile: {state.active_profile}   "
        f"Conflict: {state.conflict_mode}"
    )
    header_surf = fonts.hint_font.render(
        fit_text(fonts.hint_font, header, width - 28), True, (210, 220, 245)
    )
    surface.blit(header_surf, ((width - header_surf.get_width()) // 2, 106))


def _panel_geometry(surface: pygame.Surface) -> tuple[int, int, int, int]:
    width, height = surface.get_size()
    panel_w = min(1120, max(320, width - 40))
    panel_h = min(580, max(220, height - 260))
    panel_x = (width - panel_w) // 2
    panel_y = max(122, min(138, height - panel_h - 110))
    return panel_x, panel_y, panel_w, panel_h


def _draw_panel(
    surface: pygame.Surface, *, panel_x: int, panel_y: int, panel_w: int, panel_h: int
) -> None:
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 152), panel.get_rect(), border_radius=14)
    surface.blit(panel, (panel_x, panel_y))


def _selected_render_index(
    state: Any,
    rendered_rows: list[RenderedRow],
    binding_rows: list[BindingRow],
) -> int:
    if not binding_rows:
        return 0
    state.selected_binding = max(0, min(len(binding_rows) - 1, state.selected_binding))
    selected_row = binding_rows[state.selected_binding]
    for idx, rendered in enumerate(rendered_rows):
        if rendered.binding == selected_row:
            return idx
    return 0


def _sync_scroll_window(
    state: Any,
    *,
    selected_render_index: int,
    total_rows: int,
    visible_rows: int,
) -> None:
    if selected_render_index < state.scroll_top:
        state.scroll_top = selected_render_index
    if selected_render_index >= state.scroll_top + visible_rows:
        state.scroll_top = selected_render_index - visible_rows + 1
    max_top = max(0, total_rows - visible_rows)
    state.scroll_top = max(0, min(max_top, state.scroll_top))


def _draw_row_selection(
    surface: pygame.Surface,
    *,
    panel_x: int,
    panel_w: int,
    y: int,
    line_h: int,
) -> None:
    hi = pygame.Surface((panel_w - 24, line_h + 4), pygame.SRCALPHA)
    pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
    surface.blit(hi, (panel_x + 12, y - 2))


def _draw_binding_row(
    surface: pygame.Surface,
    fonts,
    row: BindingRow,
    *,
    selected: bool,
    scope: str,
    panel_x: int,
    panel_w: int,
    y: int,
    row_h: int,
) -> None:
    color = (255, 224, 130) if selected else (228, 230, 242)
    if selected:
        _draw_row_selection(
            surface, panel_x=panel_x, panel_w=panel_w, y=y, line_h=row_h - 4
        )

    label = binding_title(row, scope)
    desc = binding_action_description(row.action)
    key_text = format_key_tuple(binding_keys(row))

    left_x = panel_x + 18
    right_x = panel_x + panel_w - 18
    max_key_w = max(56, int(panel_w * 0.34))
    key_draw = fit_text(fonts.panel_font, key_text, max_key_w)
    key_surf = fonts.panel_font.render(key_draw, True, color)
    key_x = right_x - key_surf.get_width()
    label_width = max(0, key_x - left_x - 10)
    label_draw = fit_text(fonts.panel_font, label, label_width)
    label_surf = fonts.panel_font.render(label_draw, True, color)

    surface.blit(label_surf, (left_x, y))
    surface.blit(key_surf, (key_x, y))

    desc_y = y + fonts.panel_font.get_height() + 1
    icon_rect = pygame.Rect(left_x, desc_y - 1, 20, fonts.hint_font.get_height() + 2)
    draw_action_icon(surface, rect=icon_rect, action=row.action)
    desc_x = icon_rect.right + 6
    desc_width = max(0, right_x - desc_x)
    desc_draw = fit_text(fonts.hint_font, desc, desc_width)
    desc_surf = fonts.hint_font.render(desc_draw, True, (168, 182, 215))
    surface.blit(desc_surf, (desc_x, desc_y))


def _draw_rows(
    surface: pygame.Surface,
    fonts,
    *,
    state: Any,
    rendered_rows: list[RenderedRow],
    binding_rows: list[BindingRow],
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
) -> int:
    row_h = fonts.panel_font.get_height() + fonts.hint_font.get_height() + 12
    visible_rows = max(4, (panel_h - 20) // row_h)
    selected_render_index = _selected_render_index(state, rendered_rows, binding_rows)
    _sync_scroll_window(
        state,
        selected_render_index=selected_render_index,
        total_rows=len(rendered_rows),
        visible_rows=visible_rows,
    )

    draw_rows = rendered_rows[state.scroll_top : state.scroll_top + visible_rows]
    y = panel_y + 12
    selected_binding = binding_rows[state.selected_binding] if binding_rows else None
    for row in draw_rows:
        if row.kind == "header":
            header_color = (170, 186, 224) if row.text else (132, 142, 172)
            surf = fonts.hint_font.render(row.text, True, header_color)
            header_y = y + (row_h - surf.get_height()) // 2
            surface.blit(surf, (panel_x + 16, header_y))
            y += row_h
            continue
        if row.binding is None:
            y += row_h
            continue
        _draw_binding_row(
            surface,
            fonts,
            row.binding,
            selected=(row.binding == selected_binding),
            scope=state.scope,
            panel_x=panel_x,
            panel_w=panel_w,
            y=y,
            row_h=row_h,
        )
        y += row_h
    return y


def _draw_hints(
    surface: pygame.Surface,
    fonts,
    state: Any,
    panel_y: int,
    panel_h: int,
    scope_file_hint_fn,
) -> int:
    width, height = surface.get_size()
    hints = [
        "L load   S save   F3 save as   F2 rename   F6 reset (confirm)",
        "[ / ] profile prev/next   N new profile   Backspace delete custom profile",
        "C conflict mode cycle   Enter capture   Tab section menu   Esc cancel/back",
        scope_file_hint_fn(state.scope),
    ]
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
    binding_rows: list[BindingRow],
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
        f"Press a key for {binding_title(selected, state.scope)} (Esc cancels)",
        max_w,
    )
    cap = fonts.hint_font.render(
        cap_text,
        True,
        (255, 226, 144),
    )
    surface.blit(cap, ((width - cap.get_width()) // 2, hint_y + 2))
    return hint_y + cap.get_height() + 4


def _draw_text_mode_hint(
    surface: pygame.Surface, fonts, state: Any, hint_y: int, text_mode_label_fn
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
        fit_text(fonts.hint_font, "Enter confirm   Esc cancel", max_w),
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
    panel_x, panel_y, panel_w, panel_h = _panel_geometry(surface)
    _draw_panel(
        surface, panel_x=panel_x, panel_y=panel_y, panel_w=panel_w, panel_h=panel_h
    )

    row_h_default = fonts.panel_font.get_height() + fonts.hint_font.get_height() + 14
    row_h = min(
        row_h_default,
        max(
            fonts.panel_font.get_height() + fonts.hint_font.get_height() + 6,
            (panel_h - 24) // max(1, len(section_menu)),
        ),
    )
    y = panel_y + 12
    row_left = panel_x + 18
    row_width = panel_w - 36
    row_bottom = panel_y + panel_h - 8
    for idx, (_scope, title, description) in enumerate(section_menu):
        if y + fonts.panel_font.get_height() > row_bottom:
            break
        selected = idx == state.selected_section
        color = (255, 224, 130) if selected else (228, 230, 242)
        if selected:
            hi = pygame.Surface((panel_w - 24, row_h - 2), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            surface.blit(hi, (panel_x + 12, y - 3))

        title_surf = fonts.panel_font.render(
            fit_text(fonts.panel_font, title, row_width), True, color
        )
        desc_surf = fonts.hint_font.render(
            fit_text(fonts.hint_font, description, row_width),
            True,
            (168, 182, 215),
        )
        surface.blit(title_surf, (row_left, y))
        surface.blit(desc_surf, (row_left, y + fonts.panel_font.get_height() + 1))
        y += row_h

    width, height = surface.get_size()
    hints = (
        "Enter open section   Up/Down select section   Esc back",
        "[ / ] profile prev/next   N new profile   F2 rename   F3 save as",
    )
    hy = panel_y + panel_h + 10
    line_h = fonts.hint_font.get_height() + 3
    max_lines = max(0, (height - hy - 6) // max(1, line_h))
    hint_budget = max(
        0, max_lines - (1 if state.text_mode else 0) - (1 if state.status else 0)
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
    rendered_rows: list[RenderedRow],
    binding_rows: list[BindingRow],
    scope_label_fn,
    scope_file_hint_fn,
    text_mode_label_fn,
) -> None:
    _draw_background(surface)
    _draw_menu_header(surface, fonts, state, scope_label_fn)
    panel_x, panel_y, panel_w, panel_h = _panel_geometry(surface)
    _draw_panel(
        surface, panel_x=panel_x, panel_y=panel_y, panel_w=panel_w, panel_h=panel_h
    )
    _draw_rows(
        surface,
        fonts,
        state=state,
        rendered_rows=rendered_rows,
        binding_rows=binding_rows,
        panel_x=panel_x,
        panel_y=panel_y,
        panel_w=panel_w,
        panel_h=panel_h,
    )
    hint_y = _draw_hints(surface, fonts, state, panel_y, panel_h, scope_file_hint_fn)
    hint_y = _draw_capture_hint(surface, fonts, state, binding_rows, hint_y)
    hint_y = _draw_text_mode_hint(surface, fonts, state, hint_y, text_mode_label_fn)
    _draw_status(surface, fonts, state, hint_y)
