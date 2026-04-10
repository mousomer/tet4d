from __future__ import annotations

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


def draw_main_menu(
    screen: pygame.Surface,
    fonts,
    *,
    menu_title: str,
    items: tuple[dict[str, str], ...],
    selected_index: int,
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
        selected = idx == selected_index
        color = highlight_color if selected else text_color
        label_text = fit_text(fonts.menu_font, label, row_right - (panel_x + row_margin))
        text = fonts.menu_font.render(label_text, True, color)
        row_rect = text.get_rect(topleft=(panel_x + row_margin, y))
        if selected:
            hi = pygame.Surface((panel_w - 32, row_rect.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=9)
            screen.blit(hi, (panel_x + 16, y - 4))
        screen.blit(text, row_rect.topleft)
        y += row_step

    escape_hint = (
        launcher_copy["escape_hint_back"]
        if stack_depth > 1
        else launcher_copy["escape_hint_quit"]
    )
    info_lines = [
        launcher_copy["info_active_profile_template"].format(profile=active_key_profile()),
        launcher_copy["info_continue_mode_template"].format(mode=last_mode.upper()),
        launcher_copy[
            "controls_hint_template_tiny"
            if active_key_profile() == "tiny"
            else "controls_hint_template"
        ].format(escape_hint=escape_hint),
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
