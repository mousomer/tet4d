from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Mapping

import pygame

from tet4d.engine.api import format_key_tuple, runtime_binding_groups_for_dimension

from .control_icons import draw_action_icon
from .text_render_cache import render_text_cached
from tet4d.ui.pygame.ui_utils import fit_text


ControlGroup = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class _GuideFonts:
    hint_font: pygame.font.Font


def _format_action(bindings: Mapping[str, tuple[int, ...]], action: str) -> str:
    return format_key_tuple(bindings.get(action, ()))


def _format_pair(
    bindings: Mapping[str, tuple[int, ...]], neg_action: str, pos_action: str
) -> str:
    return (
        f"{_format_action(bindings, neg_action)}/{_format_action(bindings, pos_action)}"
    )


def _line(keys: str, text: str) -> str:
    return f"{keys}\t{text}\t"


def _line_with_icon(keys: str, text: str, action: str) -> str:
    return f"{keys}\t{text}\t{action}"


_PairIconSpec = tuple[str, str, str, str]
_SingleIconSpec = tuple[str, str, str]
_PairLineSpec = tuple[str, str, str]
_SingleLineSpec = tuple[str, str]

_TRANSLATION_PAIR_ROWS: dict[int, tuple[_PairIconSpec, ...]] = {
    2: (("move_x_neg", "move_x_pos", "move x", "move_x_pos"),),
    3: (
        ("move_x_neg", "move_x_pos", "left/right", "move_x_pos"),
        ("move_z_neg", "move_z_pos", "away/closer", "move_z_neg"),
    ),
    4: (
        ("move_x_neg", "move_x_pos", "left/right", "move_x_pos"),
        ("move_z_neg", "move_z_pos", "away/closer", "move_z_neg"),
        ("move_w_neg", "move_w_pos", "w layer prev/next", "move_w_pos"),
    ),
}

_TRANSLATION_EXPLORATION_ROWS: dict[int, _PairIconSpec] = {
    2: ("move_y_neg", "move_y_pos", "up/down (explore)", "move_y_neg"),
    3: ("move_y_neg", "move_y_pos", "up/down (explore)", "move_y_neg"),
    4: ("move_y_neg", "move_y_pos", "up/down (explore)", "move_y_neg"),
}

_TRANSLATION_SINGLE_ROWS: dict[int, tuple[_SingleIconSpec, ...]] = {
    2: (
        ("soft_drop", "soft drop", "soft_drop"),
        ("hard_drop", "hard drop", "hard_drop"),
    ),
    3: (
        ("soft_drop", "soft drop", "soft_drop"),
        ("hard_drop", "hard drop", "hard_drop"),
    ),
    4: (
        ("soft_drop", "soft drop", "soft_drop"),
        ("hard_drop", "hard drop", "hard_drop"),
    ),
}

_ROTATION_PAIR_ROWS: dict[int, tuple[_PairIconSpec, ...]] = {
    2: (("rotate_xy_neg", "rotate_xy_pos", "rotate x-y", "rotate_xy_pos"),),
    3: (
        ("rotate_xy_neg", "rotate_xy_pos", "plane x-y", "rotate_xy_pos"),
        ("rotate_xz_neg", "rotate_xz_pos", "plane x-z", "rotate_xz_pos"),
        ("rotate_yz_neg", "rotate_yz_pos", "plane y-z", "rotate_yz_pos"),
    ),
    4: (
        ("rotate_xy_neg", "rotate_xy_pos", "plane x-y", "rotate_xy_pos"),
        ("rotate_xz_neg", "rotate_xz_pos", "plane x-z", "rotate_xz_pos"),
        ("rotate_yz_neg", "rotate_yz_pos", "plane y-z", "rotate_yz_pos"),
        ("rotate_xw_neg", "rotate_xw_pos", "plane x-w", "rotate_xw_pos"),
        ("rotate_yw_neg", "rotate_yw_pos", "plane y-w", "rotate_yw_pos"),
        ("rotate_zw_neg", "rotate_zw_pos", "plane z-w", "rotate_zw_pos"),
    ),
}

_SYSTEM_ROWS: tuple[_SingleLineSpec, ...] = (
    ("toggle_grid", "grid mode"),
    ("help", "help"),
    ("menu", "pause menu"),
    ("restart", "restart"),
    ("quit", "quit"),
)

_CAMERA_PAIR_ROWS: dict[int, tuple[_PairLineSpec, ...]] = {
    3: (
        ("yaw_fine_neg", "yaw_fine_pos", "yaw +/-15"),
        ("yaw_neg", "yaw_pos", "yaw +/-90"),
        ("pitch_neg", "pitch_pos", "pitch +/-90"),
        ("zoom_out", "zoom_in", "zoom"),
    ),
    4: (
        ("yaw_fine_neg", "yaw_fine_pos", "yaw +/-15"),
        ("yaw_neg", "yaw_pos", "yaw +/-90"),
        ("pitch_neg", "pitch_pos", "pitch +/-90"),
        ("view_xw_neg", "view_xw_pos", "view x-w +/-90"),
        ("view_zw_neg", "view_zw_pos", "view z-w +/-90"),
        ("zoom_out", "zoom_in", "zoom"),
    ),
}

_CAMERA_SINGLE_ROWS: dict[int, tuple[_SingleLineSpec, ...]] = {
    3: (("cycle_projection", "projection"), ("reset", "reset camera")),
    4: (("reset", "reset view"),),
}


def _rows_with_icon_pairs(
    bindings: Mapping[str, tuple[int, ...]],
    specs: tuple[_PairIconSpec, ...],
) -> tuple[str, ...]:
    return tuple(
        _line_with_icon(
            _format_pair(bindings, neg_action, pos_action), label, icon_action
        )
        for neg_action, pos_action, label, icon_action in specs
    )


def _rows_with_icon_actions(
    bindings: Mapping[str, tuple[int, ...]],
    specs: tuple[_SingleIconSpec, ...],
) -> tuple[str, ...]:
    return tuple(
        _line_with_icon(_format_action(bindings, action), label, icon_action)
        for action, label, icon_action in specs
    )


def _rows_with_pairs(
    bindings: Mapping[str, tuple[int, ...]],
    specs: tuple[_PairLineSpec, ...],
) -> tuple[str, ...]:
    return tuple(
        _line(_format_pair(bindings, neg_action, pos_action), label)
        for neg_action, pos_action, label in specs
    )


def _rows_with_actions(
    bindings: Mapping[str, tuple[int, ...]],
    specs: tuple[_SingleLineSpec, ...],
) -> tuple[str, ...]:
    return tuple(
        _line(_format_action(bindings, action), label) for action, label in specs
    )


def control_groups_for_dimension(
    dimension: int, *, include_exploration: bool = True
) -> list[ControlGroup]:
    dim = max(2, min(4, int(dimension)))
    groups = runtime_binding_groups_for_dimension(dim)
    game_keys = groups.get("game", {})
    camera_keys = groups.get("camera", {})
    system_keys = groups.get("system", {})

    translation_specs = list(_TRANSLATION_PAIR_ROWS[dim])
    if include_exploration:
        translation_specs.append(_TRANSLATION_EXPLORATION_ROWS[dim])
    translation_rows = _rows_with_icon_pairs(
        game_keys, tuple(translation_specs)
    ) + _rows_with_icon_actions(
        game_keys,
        _TRANSLATION_SINGLE_ROWS[dim],
    )
    rotation_rows = _rows_with_icon_pairs(game_keys, _ROTATION_PAIR_ROWS[dim])
    control_groups: list[ControlGroup] = [
        ("Translation", translation_rows),
        ("Rotation", rotation_rows),
        ("System", _rows_with_actions(system_keys, _SYSTEM_ROWS)),
    ]

    if dim >= 3:
        camera_rows = _rows_with_pairs(
            camera_keys, _CAMERA_PAIR_ROWS[dim]
        ) + _rows_with_actions(camera_keys, _CAMERA_SINGLE_ROWS[dim])
        control_groups.append(("Camera/View", camera_rows))

    return control_groups


def _draw_overflow_hint(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    y: int,
    margin_x: int,
    hint_font: pygame.font.Font,
) -> int:
    remaining = render_text_cached(
        font=hint_font,
        text="... open Help for full key guide",
        color=(188, 197, 228),
    )
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
) -> tuple[int, int, int, int]:
    content_w = max(120, box_rect.width - (margin_x * 2))
    key_col_w = min(220, max(96, int(content_w * 0.36)))
    icon_w = 22
    value_x = box_rect.x + margin_x + key_col_w + icon_w + 10
    value_w = max(48, content_w - key_col_w - icon_w - 10)
    icon_x = box_rect.x + margin_x + key_col_w + 4
    return key_col_w, icon_x, value_x, value_w


def _draw_group_rows(
    surface: pygame.Surface,
    *,
    rows: tuple[str, ...],
    box_rect: pygame.Rect,
    row_y: int,
    margin_x: int,
    panel_font: pygame.font.Font,
) -> None:
    key_col_w, icon_x, value_x, value_w = _row_columns(
        box_rect=box_rect, margin_x=margin_x
    )
    for row in rows:
        parts = row.split("\t")
        if not parts:
            continue
        key_text = parts[0]
        desc_text = parts[1] if len(parts) > 1 else ""
        icon_action = parts[2] if len(parts) > 2 and parts[2] else None
        if len(parts) == 1:
            key_text = row
            desc_text = ""
        key_draw = fit_text(panel_font, key_text, key_col_w)
        desc_draw = fit_text(panel_font, desc_text, value_w)
        if key_draw:
            key_surf = render_text_cached(
                font=panel_font,
                text=key_draw,
                color=(228, 230, 242),
            )
            surface.blit(key_surf, (box_rect.x + margin_x, row_y))
        if icon_action is not None:
            icon_rect = pygame.Rect(icon_x, row_y - 1, 20, panel_font.get_height() + 2)
            draw_action_icon(surface, rect=icon_rect, action=icon_action)
        if desc_draw:
            desc_surf = render_text_cached(
                font=panel_font,
                text=desc_draw,
                color=(188, 197, 228),
            )
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
        from .menu.menu_control_guides import draw_translation_rotation_guides
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
        box_h = (
            10
            + hint_font.get_height()
            + 6
            + (len(rows) * (panel_font.get_height() + 2))
            + 8
        )
        if y + box_h > rect.bottom:
            return _draw_overflow_hint(
                surface, rect=rect, y=y, margin_x=margin_x, hint_font=hint_font
            )

        box_rect = pygame.Rect(rect.x + 2, y, rect.width - 4, box_h)
        _draw_group_box(surface, box_rect=box_rect)

        title = render_text_cached(
            font=hint_font,
            text=group_name,
            color=(210, 220, 245),
        )
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
