from __future__ import annotations

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
    return f"{keys:<14} {text}"


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


def draw_grouped_control_helper(
    surface: pygame.Surface,
    *,
    groups: Sequence[ControlGroup],
    rect: pygame.Rect,
    panel_font: pygame.font.Font,
    hint_font: pygame.font.Font,
) -> int:
    y = rect.y
    margin_x = 10
    for group_name, rows in groups:
        box_h = 10 + hint_font.get_height() + 6 + (len(rows) * (panel_font.get_height() + 2)) + 8
        if y + box_h > rect.bottom:
            remaining = hint_font.render("... open Help for full key guide", True, (188, 197, 228))
            surface.blit(remaining, (rect.x + margin_x, y))
            return y + remaining.get_height() + 4

        box_rect = pygame.Rect(rect.x + 2, y, rect.width - 4, box_h)
        box = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(box, (10, 14, 34, 170), box.get_rect(), border_radius=10)
        pygame.draw.rect(box, (74, 92, 138, 170), box.get_rect(), width=1, border_radius=10)
        surface.blit(box, box_rect.topleft)

        title = hint_font.render(group_name, True, (210, 220, 245))
        surface.blit(title, (box_rect.x + margin_x, box_rect.y + 8))
        row_y = box_rect.y + 8 + title.get_height() + 6
        for row in rows:
            line = panel_font.render(row, True, (228, 230, 242))
            surface.blit(line, (box_rect.x + margin_x, row_y))
            row_y += line.get_height() + 2
        y += box_h + 6
    return y
