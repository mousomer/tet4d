from __future__ import annotations

import pygame

from tet4d.ui.pygame.topology_lab.common import TopologyLabHitTarget
from tet4d.ui.pygame.ui_utils import (
    draw_fitted_text_line,
    draw_centered_wrapped_text,
    draw_panel_frame,
)

_BUTTON_BG = (38, 44, 70)
_BUTTON_ACTIVE = (86, 98, 146)
_BUTTON_TEXT = (232, 236, 248)
_DISPLAY_BG = (24, 29, 47)
_DISPLAY_BORDER = (84, 96, 132)
_DISPLAY_CAPTION = (150, 164, 198)
_DISPLAY_TEXT = (220, 228, 250)


def _draw_button(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    text: str,
    color: tuple[int, int, int],
    font,
) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=8)
    pygame.draw.rect(surface, (16, 18, 26), rect, 1, border_radius=8)
    draw_centered_wrapped_text(
        surface,
        rect=rect,
        font=font,
        text=text,
        color=_BUTTON_TEXT,
    )


def _draw_read_only_display(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    title: str,
    text: str,
    font,
) -> None:
    draw_panel_frame(
        surface,
        rect=rect,
        fill_color=_DISPLAY_BG,
        border_color=_DISPLAY_BORDER,
        border_radius=8,
    )
    draw_fitted_text_line(
        surface,
        font=font,
        text=title,
        color=_DISPLAY_CAPTION,
        max_width=rect.width - 12,
        x=rect.x + 8,
        y=rect.y + 5,
    )
    draw_fitted_text_line(
        surface,
        font=font,
        text=text,
        color=_DISPLAY_TEXT,
        max_width=rect.width - 12,
        x=rect.x + 8,
        y=rect.bottom - font.get_height() - 5,
    )


def draw_transform_editor(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    editable: bool = True,
    preset_label: str,
    glue_labels: tuple[str, ...],
    active_slot_index: int,
    transform_label: str,
    permutation_labels: tuple[str, ...],
    selected_permutation_index: int,
    signs: tuple[int, ...],
) -> list[TopologyLabHitTarget]:
    draw_panel_frame(
        surface,
        rect=area,
        fill_color=(18, 22, 38),
        border_color=(76, 84, 112),
    )
    title_text = "Transform editor" if editable else "Transform preview"
    title = draw_fitted_text_line(
        surface,
        font=fonts.hint_font,
        text=title_text,
        color=(220, 228, 250),
        max_width=area.width - 20,
        x=area.x + 10,
        y=area.y + 10,
    )
    draw_fitted_text_line(
        surface,
        font=fonts.hint_font,
        text=transform_label,
        color=(188, 198, 228),
        max_width=area.width - 20,
        x=area.x + 10,
        y=area.y + 10 + title.get_height() + 6,
    )

    hits: list[TopologyLabHitTarget] = []
    y = area.y + 54

    preset_rect = pygame.Rect(area.x + 10, y, area.width - 20, 38)
    _draw_read_only_display(
        surface,
        rect=preset_rect,
        title="Preset",
        text=preset_label,
        font=fonts.hint_font,
    )

    y += 48
    if glue_labels:
        slot_gap = 8
        slot_w = max(
            70,
            (area.width - 20 - max(0, len(glue_labels) - 1) * slot_gap)
            // max(1, len(glue_labels)),
        )
        for index, label_text in enumerate(glue_labels):
            rect = pygame.Rect(area.x + 10 + index * (slot_w + slot_gap), y, slot_w, 28)
            _draw_button(
                surface,
                rect=rect,
                text=label_text,
                color=_BUTTON_ACTIVE if index == active_slot_index else _BUTTON_BG,
                font=fonts.hint_font,
            )
            if editable:
                hits.append(TopologyLabHitTarget("glue_slot", index, rect.copy()))
        y += 38

    columns = 2 if len(permutation_labels) > 2 else max(1, len(permutation_labels))
    rows = max(1, (len(permutation_labels) + columns - 1) // columns)
    button_w = (area.width - 20 - (columns - 1) * 8) // columns
    button_h = 32
    for index, text in enumerate(permutation_labels):
        row = index // columns
        col = index % columns
        rect = pygame.Rect(
            area.x + 10 + col * (button_w + 8),
            y + row * (button_h + 8),
            button_w,
            button_h,
        )
        _draw_button(
            surface,
            rect=rect,
            text=text,
            color=_BUTTON_ACTIVE if index == selected_permutation_index else _BUTTON_BG,
            font=fonts.hint_font,
        )
        if editable:
            hits.append(TopologyLabHitTarget("perm_select", index, rect.copy()))

    y += rows * (button_h + 8) + 6
    for index, sign in enumerate(signs):
        rect = pygame.Rect(area.x + 10, y, area.width - 20, 30)
        label_text = f"Tangent {index + 1}: " + ("Flipped" if sign < 0 else "Straight")
        _draw_button(
            surface,
            rect=rect,
            text=label_text,
            color=_BUTTON_ACTIVE if sign < 0 else _BUTTON_BG,
            font=fonts.hint_font,
        )
        if editable:
            hits.append(TopologyLabHitTarget("sign_toggle", index, rect.copy()))
        y += 36

    return hits


def draw_action_buttons(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    actions: tuple[tuple[str, str], ...] | None = None,
) -> list[TopologyLabHitTarget]:
    active_actions = actions or (
        ("apply_glue", "Apply"),
        ("remove_glue", "Remove"),
        ("save_profile", "Save"),
        ("export", "Export"),
        ("play_preview", "Play"),
        ("back", "Back"),
    )
    count = len(active_actions)
    button_w = max(76, (area.width - (count - 1) * 8) // count)
    hits: list[TopologyLabHitTarget] = []
    for index, (action, label) in enumerate(active_actions):
        rect = pygame.Rect(
            area.x + index * (button_w + 8), area.y, button_w, area.height
        )
        _draw_button(
            surface,
            rect=rect,
            text=label,
            color=_BUTTON_BG,
            font=fonts.hint_font,
        )
        hits.append(TopologyLabHitTarget("action", action, rect.copy()))
    return hits


__all__ = ["draw_action_buttons", "draw_transform_editor"]
