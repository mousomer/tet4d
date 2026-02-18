from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Mapping

import pygame

from .keybindings import (
    CAMERA_KEYS_3D,
    CAMERA_KEYS_4D,
    KEYS_2D,
    KEYS_3D,
    KEYS_4D,
    SLICE_KEYS_3D,
    SLICE_KEYS_4D,
    SYSTEM_KEYS,
)


ControlGroup = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class _GuideFonts:
    hint_font: pygame.font.Font

_KEY_NAME_OVERRIDES = {
    "escape": "Esc",
    "return": "Enter",
    "space": "Space",
    "left shift": "LShift",
    "right shift": "RShift",
    "left": "Left",
    "right": "Right",
    "up": "Up",
    "down": "Down",
    "left bracket": "[",
    "right bracket": "]",
    "semicolon": ";",
    "quote": "'",
    "comma": ",",
    "period": ".",
}


def _display_key_name(key: int) -> str:
    raw = pygame.key.name(key)
    if not raw:
        return str(key)
    lowered = raw.lower()
    if lowered in _KEY_NAME_OVERRIDES:
        return _KEY_NAME_OVERRIDES[lowered]
    if len(raw) == 1:
        return raw.upper()
    words = []
    for word in raw.split():
        if word == "kp":
            words.append("Numpad")
        else:
            words.append(word.capitalize())
    return " ".join(words)


def _format_keys(keys: Sequence[int]) -> str:
    if not keys:
        return "-"
    return "/".join(_display_key_name(key) for key in keys)


def _format_action(bindings: Mapping[str, tuple[int, ...]], action: str) -> str:
    return _format_keys(bindings.get(action, ()))


def _format_pair(bindings: Mapping[str, tuple[int, ...]], neg_action: str, pos_action: str) -> str:
    return f"{_format_action(bindings, neg_action)}/{_format_action(bindings, pos_action)}"


def _line(keys: str, text: str) -> str:
    return f"{keys}\t{text}"


def _fit_text(font: pygame.font.Font, text: str, max_width: int) -> str:
    if max_width <= 8:
        return ""
    if font.size(text)[0] <= max_width:
        return text
    if max_width <= font.size("...")[0]:
        return ""
    trimmed = text
    while trimmed and font.size(trimmed + "...")[0] > max_width:
        trimmed = trimmed[:-1]
    return f"{trimmed}..." if trimmed else ""


def control_groups_for_dimension(dimension: int) -> list[ControlGroup]:
    if dimension == 2:
        return [
            (
                "Translation",
                (
                    _line(_format_pair(KEYS_2D, "move_x_neg", "move_x_pos"), "move x"),
                    _line(_format_action(KEYS_2D, "soft_drop"), "soft drop"),
                    _line(_format_action(KEYS_2D, "hard_drop"), "hard drop"),
                ),
            ),
            (
                "Rotation",
                (
                    _line(_format_pair(KEYS_2D, "rotate_xy_neg", "rotate_xy_pos"), "rotate x-y"),
                ),
            ),
            (
                "System",
                (
                    _line(_format_action(SYSTEM_KEYS, "toggle_grid"), "grid mode"),
                    _line(_format_action(SYSTEM_KEYS, "menu"), "pause menu"),
                    _line(_format_action(SYSTEM_KEYS, "restart"), "restart"),
                    _line(_format_action(SYSTEM_KEYS, "quit"), "quit"),
                ),
            ),
        ]

    if dimension == 3:
        return [
            (
                "Translation",
                (
                    _line(_format_pair(KEYS_3D, "move_x_neg", "move_x_pos"), "left/right"),
                    _line(_format_pair(KEYS_3D, "move_z_neg", "move_z_pos"), "away/closer"),
                    _line(_format_action(KEYS_3D, "soft_drop"), "soft drop"),
                    _line(_format_action(KEYS_3D, "hard_drop"), "hard drop"),
                ),
            ),
            (
                "Rotation",
                (
                    _line(_format_pair(KEYS_3D, "rotate_xy_neg", "rotate_xy_pos"), "plane x-y"),
                    _line(_format_pair(KEYS_3D, "rotate_xz_neg", "rotate_xz_pos"), "plane x-z"),
                    _line(_format_pair(KEYS_3D, "rotate_yz_neg", "rotate_yz_pos"), "plane y-z"),
                ),
            ),
            (
                "Camera/View",
                (
                    _line(_format_pair(CAMERA_KEYS_3D, "yaw_fine_neg", "yaw_fine_pos"), "yaw +/-15"),
                    _line(_format_pair(CAMERA_KEYS_3D, "yaw_neg", "yaw_pos"), "yaw +/-90"),
                    _line(_format_pair(CAMERA_KEYS_3D, "pitch_neg", "pitch_pos"), "pitch +/-90"),
                    _line(_format_pair(CAMERA_KEYS_3D, "zoom_out", "zoom_in"), "zoom"),
                    _line(_format_action(CAMERA_KEYS_3D, "cycle_projection"), "projection"),
                    _line(_format_action(CAMERA_KEYS_3D, "reset"), "reset camera"),
                ),
            ),
            (
                "Slice",
                (
                    _line(_format_pair(SLICE_KEYS_3D, "slice_z_neg", "slice_z_pos"), "slice z"),
                ),
            ),
            (
                "System",
                (
                    _line(_format_action(SYSTEM_KEYS, "toggle_grid"), "grid mode"),
                    _line(_format_action(SYSTEM_KEYS, "menu"), "pause menu"),
                    _line(_format_action(SYSTEM_KEYS, "restart"), "restart"),
                    _line(_format_action(SYSTEM_KEYS, "quit"), "quit"),
                ),
            ),
        ]

    if dimension == 4:
        return [
            (
                "Translation",
                (
                    _line(_format_pair(KEYS_4D, "move_x_neg", "move_x_pos"), "left/right"),
                    _line(_format_pair(KEYS_4D, "move_z_neg", "move_z_pos"), "away/closer"),
                    _line(_format_pair(KEYS_4D, "move_w_neg", "move_w_pos"), "w axis"),
                    _line(_format_action(KEYS_4D, "soft_drop"), "soft drop"),
                    _line(_format_action(KEYS_4D, "hard_drop"), "hard drop"),
                ),
            ),
            (
                "Rotation",
                (
                    _line(_format_pair(KEYS_4D, "rotate_xy_neg", "rotate_xy_pos"), "plane x-y"),
                    _line(_format_pair(KEYS_4D, "rotate_xz_neg", "rotate_xz_pos"), "plane x-z"),
                    _line(_format_pair(KEYS_4D, "rotate_yz_neg", "rotate_yz_pos"), "plane y-z"),
                    _line(_format_pair(KEYS_4D, "rotate_xw_neg", "rotate_xw_pos"), "plane x-w"),
                    _line(_format_pair(KEYS_4D, "rotate_yw_neg", "rotate_yw_pos"), "plane y-w"),
                    _line(_format_pair(KEYS_4D, "rotate_zw_neg", "rotate_zw_pos"), "plane z-w"),
                ),
            ),
            (
                "Camera/View",
                (
                    _line(_format_pair(CAMERA_KEYS_4D, "yaw_fine_neg", "yaw_fine_pos"), "yaw +/-15"),
                    _line(_format_pair(CAMERA_KEYS_4D, "yaw_neg", "yaw_pos"), "yaw +/-90"),
                    _line(_format_pair(CAMERA_KEYS_4D, "pitch_neg", "pitch_pos"), "pitch +/-90"),
                    _line(_format_pair(CAMERA_KEYS_4D, "zoom_out", "zoom_in"), "zoom"),
                    _line(_format_action(CAMERA_KEYS_4D, "reset"), "reset view"),
                ),
            ),
            (
                "Slice",
                (
                    _line(_format_pair(SLICE_KEYS_4D, "slice_z_neg", "slice_z_pos"), "slice z"),
                    _line(_format_pair(SLICE_KEYS_4D, "slice_w_neg", "slice_w_pos"), "slice w"),
                ),
            ),
            (
                "System",
                (
                    _line(_format_action(SYSTEM_KEYS, "toggle_grid"), "grid mode"),
                    _line(_format_action(SYSTEM_KEYS, "menu"), "pause menu"),
                    _line(_format_action(SYSTEM_KEYS, "restart"), "restart"),
                    _line(_format_action(SYSTEM_KEYS, "quit"), "quit"),
                ),
            ),
        ]

    return []


def _draw_overflow_hint(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    y: int,
    margin_x: int,
    hint_font: pygame.font.Font,
) -> int:
    remaining = hint_font.render("... open Help for full key guide", True, (188, 197, 228))
    surface.blit(remaining, (rect.x + margin_x, y))
    return y + remaining.get_height() + 4


def _draw_group_box(
    surface: pygame.Surface,
    *,
    box_rect: pygame.Rect,
) -> None:
    box = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(box, (10, 14, 34, 170), box.get_rect(), border_radius=10)
    pygame.draw.rect(box, (74, 92, 138, 170), box.get_rect(), width=1, border_radius=10)
    surface.blit(box, box_rect.topleft)


def _row_columns(
    *,
    box_rect: pygame.Rect,
    margin_x: int,
) -> tuple[int, int, int]:
    content_w = max(120, box_rect.width - (margin_x * 2))
    key_col_w = min(220, max(110, int(content_w * 0.42)))
    value_x = box_rect.x + margin_x + key_col_w + 8
    value_w = max(48, content_w - key_col_w - 8)
    return key_col_w, value_x, value_w


def _draw_group_rows(
    surface: pygame.Surface,
    *,
    rows: tuple[str, ...],
    box_rect: pygame.Rect,
    row_y: int,
    margin_x: int,
    panel_font: pygame.font.Font,
) -> None:
    key_col_w, value_x, value_w = _row_columns(box_rect=box_rect, margin_x=margin_x)
    for row in rows:
        key_text, _sep, desc_text = row.partition("\t")
        if not _sep:
            key_text = row
            desc_text = ""
        key_draw = _fit_text(panel_font, key_text, key_col_w)
        desc_draw = _fit_text(panel_font, desc_text, value_w)
        if key_draw:
            key_surf = panel_font.render(key_draw, True, (228, 230, 242))
            surface.blit(key_surf, (box_rect.x + margin_x, row_y))
        if desc_draw:
            desc_surf = panel_font.render(desc_draw, True, (188, 197, 228))
            surface.blit(desc_surf, (value_x, row_y))
        row_y += panel_font.get_height() + 2


def _draw_optional_guides(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    y: int,
    hint_font: pygame.font.Font,
) -> int:
    remaining_h = rect.bottom - y
    if remaining_h < 88:
        return y
    guide_rect = pygame.Rect(
        rect.x + 2,
        y,
        rect.width - 4,
        min(118, remaining_h - 2),
    )
    if guide_rect.height < 88 or guide_rect.width < 140:
        return y
    try:
        from .menu_gif_guides import draw_translation_rotation_guides
    except Exception:  # pragma: no cover - import/runtime optional path
        return y
    draw_translation_rotation_guides(
        surface,
        _GuideFonts(hint_font=hint_font),
        rect=guide_rect,
        title="Move / Rotate",
    )
    return guide_rect.bottom + 4


def draw_grouped_control_helper(
    surface: pygame.Surface,
    *,
    groups: Sequence[ControlGroup],
    rect: pygame.Rect,
    panel_font: pygame.font.Font,
    hint_font: pygame.font.Font,
    show_guides: bool = False,
) -> int:
    y = rect.y
    margin_x = 10
    for group_name, rows in groups:
        box_h = 10 + hint_font.get_height() + 6 + (len(rows) * (panel_font.get_height() + 2)) + 8
        if y + box_h > rect.bottom:
            return _draw_overflow_hint(surface, rect=rect, y=y, margin_x=margin_x, hint_font=hint_font)

        box_rect = pygame.Rect(rect.x + 2, y, rect.width - 4, box_h)
        _draw_group_box(surface, box_rect=box_rect)

        title = hint_font.render(group_name, True, (210, 220, 245))
        surface.blit(title, (box_rect.x + margin_x, box_rect.y + 8))
        row_y = box_rect.y + 8 + title.get_height() + 6
        _draw_group_rows(
            surface,
            rows=rows,
            box_rect=box_rect,
            row_y=row_y,
            margin_x=margin_x,
            panel_font=panel_font,
        )
        y += box_h + 6

    if show_guides:
        y = _draw_optional_guides(surface, rect=rect, y=y, hint_font=hint_font)
    return y
