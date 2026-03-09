from __future__ import annotations

import pygame

from tet4d.ui.pygame.topology_lab.common import TopologyLabHitTarget
from tet4d.ui.pygame.ui_utils import fit_text

_BUTTON_BG = (38, 44, 70)
_BUTTON_ACTIVE = (86, 98, 146)
_BUTTON_TEXT = (232, 236, 248)


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
    text_surf = font.render(fit_text(font, text, rect.width - 10), True, _BUTTON_TEXT)
    surface.blit(
        text_surf,
        (
            rect.centerx - text_surf.get_width() // 2,
            rect.centery - text_surf.get_height() // 2,
        ),
    )


def draw_transform_editor(
    surface: pygame.Surface,
    fonts,
    *,
    area: pygame.Rect,
    preset_label: str,
    glue_labels: tuple[str, ...],
    active_slot_index: int,
    transform_label: str,
    permutation_labels: tuple[str, ...],
    selected_permutation_index: int,
    signs: tuple[int, ...],
) -> list[TopologyLabHitTarget]:
    pygame.draw.rect(surface, (18, 22, 38), area, border_radius=10)
    pygame.draw.rect(surface, (76, 84, 112), area, 1, border_radius=10)
    title = fonts.hint_font.render("Transform editor", True, (220, 228, 250))
    surface.blit(title, (area.x + 10, area.y + 10))
    label = fonts.hint_font.render(
        fit_text(fonts.hint_font, transform_label, area.width - 20),
        True,
        (188, 198, 228),
    )
    surface.blit(label, (area.x + 10, area.y + 10 + title.get_height() + 6))

    hits: list[TopologyLabHitTarget] = []
    y = area.y + 54

    prev_rect = pygame.Rect(area.x + 10, y, 34, 28)
    next_rect = pygame.Rect(area.right - 44, y, 34, 28)
    current_rect = pygame.Rect(area.x + 52, y, area.width - 104, 28)
    _draw_button(
        surface, rect=prev_rect, text="<", color=_BUTTON_BG, font=fonts.hint_font
    )
    _draw_button(
        surface, rect=next_rect, text=">", color=_BUTTON_BG, font=fonts.hint_font
    )
    _draw_button(
        surface,
        rect=current_rect,
        text=preset_label,
        color=_BUTTON_ACTIVE,
        font=fonts.hint_font,
    )
    hits.append(TopologyLabHitTarget("preset_step", -1, prev_rect.copy()))
    hits.append(TopologyLabHitTarget("preset_step", 1, next_rect.copy()))

    y += 38
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
            surface, rect=rect, text=label, color=_BUTTON_BG, font=fonts.hint_font
        )
        hits.append(TopologyLabHitTarget("action", action, rect.copy()))
    return hits


__all__ = ["draw_action_buttons", "draw_transform_editor"]
