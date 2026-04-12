from __future__ import annotations

from typing import Any

import pygame

from tet4d.ui.pygame.keybindings import active_key_profile
from tet4d.ui.pygame.ui_utils import (
    draw_corner_chip,
    draw_tron_menu_background,
    draw_tron_panel,
    fit_text,
    format_menu_title,
    standard_menu_panel_rect,
)

_DEFAULT_CONTROLS_HINT_TEMPLATES = {
    "controls_hint_template": "Up/Down select   Enter open   {escape_hint}",
    "controls_hint_template_tiny": "I/K select   Enter open   {escape_hint}",
    "controls_hint_action_group_template": (
        "Up/Down select   Left/Right choose Play/Setup   Enter open   {escape_hint}"
    ),
    "controls_hint_action_group_template_tiny": (
        "I/K select   J/L choose Play/Setup   Enter open   {escape_hint}"
    ),
}


def _action_group_index(
    item: dict[str, Any],
    *,
    selected_action_indexes: dict[str, int],
) -> int:
    raw_actions = item.get("actions", ())
    if not isinstance(raw_actions, tuple) or not raw_actions:
        return 0
    item_id = str(item.get("id", "")).strip().lower()
    index = int(selected_action_indexes.get(item_id, 0))
    return max(0, min(len(raw_actions) - 1, index))


def _draw_action_group_row(
    screen: pygame.Surface,
    *,
    fonts,
    item: dict[str, Any],
    label: str,
    y: int,
    row_step: int,
    panel_x: int,
    row_margin: int,
    row_right: int,
    color: tuple[int, int, int],
    highlight_color: tuple[int, int, int],
    muted_color: tuple[int, int, int],
    selected_action_indexes: dict[str, int],
) -> None:
    raw_actions = item.get("actions", ())
    actions = raw_actions if isinstance(raw_actions, tuple) else tuple()
    active_index = _action_group_index(
        item,
        selected_action_indexes=selected_action_indexes,
    )
    action_gap = 10
    action_pad_x = 12
    action_pad_y = 5
    action_rects: list[tuple[pygame.Surface, pygame.Rect, bool]] = []
    total_actions_width = 0
    for action_idx, action in enumerate(actions):
        action_label = str(action.get("label", ""))
        action_color = highlight_color if action_idx == active_index else muted_color
        action_surface = fonts.hint_font.render(action_label, True, action_color)
        action_rect = pygame.Rect(
            0,
            0,
            action_surface.get_width() + action_pad_x * 2,
            action_surface.get_height() + action_pad_y * 2,
        )
        action_rects.append((action_surface, action_rect, action_idx == active_index))
        total_actions_width += action_rect.width
    if action_rects:
        total_actions_width += action_gap * (len(action_rects) - 1)
    label_max_width = max(
        80,
        row_right - (panel_x + row_margin) - total_actions_width - 24,
    )
    label_text = fit_text(fonts.menu_font, label, label_max_width)
    text = fonts.menu_font.render(label_text, True, color)
    text_y = y + max(0, (row_step - text.get_height()) // 2 - 2)
    screen.blit(text, (panel_x + row_margin, text_y))

    action_x = row_right - total_actions_width
    for action_surface, action_rect, is_active in action_rects:
        action_rect.topleft = (
            action_x,
            y + max(0, (row_step - action_rect.height) // 2 - 1),
        )
        bg_color = (*highlight_color, 42) if is_active else (255, 255, 255, 18)
        chip = pygame.Surface(action_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(chip, bg_color, chip.get_rect(), border_radius=8)
        pygame.draw.rect(
            chip,
            highlight_color if is_active else muted_color,
            chip.get_rect(),
            width=1,
            border_radius=8,
        )
        screen.blit(chip, action_rect.topleft)
        screen.blit(
            action_surface,
            (
                action_rect.x + action_pad_x,
                action_rect.y + action_pad_y,
            ),
        )
        action_x += action_rect.width + action_gap


def _controls_hint_key(
    *,
    has_action_groups: bool,
    active_profile: str,
) -> str:
    if has_action_groups:
        if active_profile == "tiny":
            return "controls_hint_action_group_template_tiny"
        return "controls_hint_action_group_template"
    if active_profile == "tiny":
        return "controls_hint_template_tiny"
    return "controls_hint_template"


def _controls_hint_text(
    *,
    launcher_copy: dict[str, str],
    has_action_groups: bool,
    active_profile: str,
    escape_hint: str,
) -> str:
    key = _controls_hint_key(
        has_action_groups=has_action_groups,
        active_profile=active_profile,
    )
    template = str(launcher_copy.get(key, "")).strip()
    if not template:
        template = _DEFAULT_CONTROLS_HINT_TEMPLATES[key]
    return template.format(escape_hint=escape_hint)


def draw_main_menu(
    screen: pygame.Surface,
    fonts,
    *,
    menu_title: str,
    items: tuple[dict[str, Any], ...],
    selected_index: int,
    selected_action_indexes: dict[str, int],
    stack_depth: int,
    status: str,
    status_error: bool,
    last_mode: str,
    launcher_copy: dict[str, str],
    signature_author: str,
    signature_message: str,
    bg_top: tuple[int, int, int],
    bg_bottom: tuple[int, int, int],
    text_color: tuple[int, int, int],
    highlight_color: tuple[int, int, int],
    muted_color: tuple[int, int, int],
) -> None:
    draw_tron_menu_background(screen, top_color=bg_top, bottom_color=bg_bottom)
    width, height = screen.get_size()
    title = fonts.title_font.render(format_menu_title(menu_title), True, text_color)
    title_y = 40
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    draw_corner_chip(
        screen,
        font=fonts.hint_font,
        text="Back" if stack_depth > 1 else "Quit",
        x=18,
        y=18,
    )

    hint_line_h = fonts.hint_font.get_height() + 3
    bottom_lines = 3 + (1 if status else 0)
    bottom_reserved = bottom_lines * hint_line_h + 14
    top_reserved = title_y + title.get_height() + 18
    panel_w = min(620, max(320, width - 40))
    row_count = max(1, len(items))
    max_panel_h = max(120, height - top_reserved - bottom_reserved - 10)
    row_step = min(
        52, max(fonts.menu_font.get_height() + 8, (max_panel_h - 48) // row_count)
    )
    panel_h = min(max_panel_h, 48 + row_count * row_step)
    panel_rect = standard_menu_panel_rect(
        screen,
        panel_w=panel_w,
        panel_h=panel_h,
        panel_top=top_reserved,
        bottom_reserved=bottom_reserved,
    )
    panel_x = panel_rect.x
    panel_y = panel_rect.y

    draw_tron_panel(screen, rect=panel_rect)

    y = panel_y + 20
    row_margin = 28
    row_right = panel_x + panel_w - row_margin
    for idx, item in enumerate(items):
        label = str(item.get("label", ""))
        item_type = str(item.get("type", "")).strip().lower()
        selected = idx == selected_index
        color = highlight_color if selected else text_color
        if selected:
            hi = pygame.Surface((panel_w - 32, row_step - 6), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=9)
            screen.blit(hi, (panel_x + 16, y - 4))
        if item_type == "action_group":
            _draw_action_group_row(
                screen,
                fonts=fonts,
                item=item,
                label=label,
                y=y,
                row_step=row_step,
                panel_x=panel_x,
                row_margin=row_margin,
                row_right=row_right,
                color=color,
                highlight_color=highlight_color,
                muted_color=muted_color,
                selected_action_indexes=selected_action_indexes,
            )
            y += row_step
            continue
        label_text = fit_text(fonts.menu_font, label, row_right - (panel_x + row_margin))
        text = fonts.menu_font.render(label_text, True, color)
        row_rect = text.get_rect(topleft=(panel_x + row_margin, y))
        screen.blit(text, row_rect.topleft)
        y += row_step

    has_action_groups = any(
        str(item.get("type", "")).strip().lower() == "action_group" for item in items
    )
    escape_hint = (
        launcher_copy["escape_hint_back"]
        if stack_depth > 1
        else launcher_copy["escape_hint_quit"]
    )
    info_lines = [
        launcher_copy["info_active_profile_template"].format(profile=active_key_profile()),
        launcher_copy["info_continue_mode_template"].format(mode=last_mode.upper()),
        _controls_hint_text(
            launcher_copy=launcher_copy,
            has_action_groups=has_action_groups,
            active_profile=active_key_profile(),
            escape_hint=escape_hint,
        ),
    ]
    info_y = panel_y + panel_h + 10
    max_bottom_lines = max(1, (height - info_y - 8) // max(1, hint_line_h))
    info_budget = max(1, max_bottom_lines - (1 if status else 0))
    for line in info_lines[:info_budget]:
        line_draw = fit_text(fonts.hint_font, line, width - 24)
        text = fonts.hint_font.render(line_draw, True, muted_color)
        screen.blit(text, ((width - text.get_width()) // 2, info_y))
        info_y += text.get_height() + 3

    if status and info_y + hint_line_h <= height - 6:
        status_color = (255, 150, 150) if status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, status, width - 24)
        status_surface = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(
            status_surface,
            (
                (width - status_surface.get_width()) // 2,
                min(height - 34, info_y + 2),
            ),
        )
        info_y = min(height - 34, info_y + 2) + status_surface.get_height() + 2

    for signature_line in (signature_author, signature_message):
        if info_y + hint_line_h > height - 6:
            break
        line_draw = fit_text(fonts.hint_font, signature_line, width - 24)
        text = fonts.hint_font.render(line_draw, True, muted_color)
        screen.blit(text, ((width - text.get_width()) // 2, info_y))
        info_y += text.get_height() + 2
