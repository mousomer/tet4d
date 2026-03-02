from __future__ import annotations

from functools import lru_cache
from dataclasses import dataclass
from collections.abc import Sequence
from typing import Mapping
import re

import pygame

from tet4d.engine.api import (
    format_key_tuple,
    help_action_layout_payload_runtime,
    help_action_panel_specs_runtime,
    runtime_binding_groups_for_dimension,
)

from .control_icons import draw_action_icon
from .text_render_cache import render_text_cached
from tet4d.ui.pygame.ui_utils import fit_text


ControlGroup = tuple[str, tuple[str, ...]]
PlannedGroupRows = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class _GuideFonts:
    hint_font: pygame.font.Font


def _format_action(bindings: Mapping[str, tuple[int, ...]], action: str) -> str:
    return format_key_tuple(bindings.get(action, ()))


def _line(keys: str, text: str) -> str:
    return f"{keys}\t{text}\t"


def _line_with_icon(keys: str, text: str, action: str) -> str:
    return f"{keys}\t{text}\t{action}"


_KEY_TOKEN_RE = re.compile(r"\{key:([a-z0-9_]+)\}")
_MODE_BY_DIMENSION = {2: "2d", 3: "3d", 4: "4d"}
_KEY_GROUP_PRIORITY = ("system", "game", "camera")

_MIN_ROWS_BY_GROUP: dict[str, int] = {
    "Main": 7,
    "Translation": 2,
    "Rotation": 1,
    "Camera": 3,
}


@lru_cache(maxsize=1)
def _canonical_panel_titles() -> tuple[str, ...]:
    payload = help_action_layout_payload_runtime()
    raw_panels = tuple(payload.get("panels", ()))
    titles: list[str] = []
    for panel in sorted(
        raw_panels,
        key=lambda item: (int(item.get("order", 0)), str(item.get("id", ""))),
    ):
        title = str(panel.get("title", "")).strip()
        if not title or title in titles:
            continue
        titles.append(title)
    return tuple(titles)


def _binding_map_for_groups(
    groups: Mapping[str, Mapping[str, tuple[int, ...]]],
) -> dict[str, tuple[int, ...]]:
    merged: dict[str, tuple[int, ...]] = {}
    for group_name in _KEY_GROUP_PRIORITY:
        bindings = groups.get(group_name, {})
        for action, keys in bindings.items():
            merged.setdefault(action, tuple(keys))
    return merged


def _keys_text_for_actions(
    action_bindings: Mapping[str, tuple[int, ...]],
    actions: Sequence[str],
) -> str:
    labels = tuple(
        _format_action(action_bindings, action)
        for action in actions
        if str(action).strip()
    )
    filtered = tuple(label for label in labels if label)
    return "/".join(filtered)


def _resolve_template_tokens(
    template: str,
    action_bindings: Mapping[str, tuple[int, ...]],
) -> str:
    def replace(match: re.Match[str]) -> str:
        action = str(match.group(1))
        label = _format_action(action_bindings, action)
        return label or f"<{action}>"

    return _KEY_TOKEN_RE.sub(replace, template)


def _helper_capabilities(
    *,
    dimension: int,
    mode: str,
    include_exploration: bool,
) -> dict[str, object]:
    return {
        "mode": mode,
        "camera.enabled": dimension >= 3,
        "rotation.nd": int(dimension),
        "slice.w.enabled": dimension >= 4,
        "piece.hold.enabled": False,
        "ghost.enabled": True,
        "controls.scheme": "keyboard",
        "exploration.enabled": bool(include_exploration),
    }


def control_groups_for_dimension(
    dimension: int,
    *,
    include_exploration: bool = True,
    unified_structure: bool = False,
) -> list[ControlGroup]:
    dim = max(2, min(4, int(dimension)))
    mode = _MODE_BY_DIMENSION[dim]
    panel_specs = help_action_panel_specs_runtime(
        mode=mode,
        capabilities=_helper_capabilities(
            dimension=dim,
            mode=mode,
            include_exploration=include_exploration,
        ),
    )
    groups = runtime_binding_groups_for_dimension(dim)
    action_bindings = _binding_map_for_groups(groups)
    control_groups: list[ControlGroup] = []
    for panel in panel_specs:
        title = str(panel.get("title", "")).strip()
        if not title:
            continue
        rows: list[str] = []
        for line in panel.get("lines", ()):
            action_ids = tuple(str(item) for item in line.get("key_actions", ()))
            keys_text = _keys_text_for_actions(action_bindings, action_ids)
            template = str(line.get("template", ""))
            desc_text = _resolve_template_tokens(template, action_bindings)
            icon_action_raw = line.get("icon_action")
            icon_action = (
                str(icon_action_raw).strip() if icon_action_raw is not None else ""
            )
            if icon_action:
                rows.append(_line_with_icon(keys_text, desc_text, icon_action))
            else:
                rows.append(_line(keys_text, desc_text))
        if rows:
            control_groups.append((title, tuple(rows)))
    if not unified_structure:
        return control_groups
    by_title: dict[str, tuple[str, ...]] = {name: rows for name, rows in control_groups}
    unavailable_row = _line("", f"not available in {dim}D")
    unified: list[ControlGroup] = []
    for title in _canonical_panel_titles():
        rows = by_title.get(title)
        unified.append((title, rows if rows else (unavailable_row,)))
    return unified if unified else control_groups


def _draw_overflow_hint(
    surface: pygame.Surface,
    *,
    rect: pygame.Rect,
    y: int,
    margin_x: int,
    hint_font: pygame.font.Font,
) -> int:
    return y


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
    icon_w = 22
    if content_w < 260:
        key_col_w = max(50, min(116, int(content_w * 0.22)))
        min_value_w = 104
    else:
        key_col_w = max(84, min(220, int(content_w * 0.34)))
        min_value_w = 80
    max_key_w = max(64, content_w - icon_w - 10 - min_value_w)
    key_col_w = min(key_col_w, max_key_w)
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
        no_key_row = not key_text.strip() and icon_action is None
        if no_key_row:
            summary_draw = fit_text(
                panel_font,
                desc_text,
                max(40, box_rect.width - (margin_x * 2)),
            )
            if summary_draw:
                summary_surf = render_text_cached(
                    font=panel_font,
                    text=summary_draw,
                    color=(228, 230, 242),
                )
                surface.blit(summary_surf, (box_rect.x + margin_x, row_y))
            row_y += panel_font.get_height() + 2
            continue
        key_draw = fit_text(panel_font, key_text, key_col_w)
        desc_draw = fit_text(panel_font, desc_text, value_w)
        if key_draw:
            key_surf = render_text_cached(
                font=panel_font,
                text=key_draw,
                color=(228, 230, 242),
            )
            key_x = box_rect.x + margin_x
            surface.blit(key_surf, (key_x, row_y))
            # Draw once more at +1px for a stronger key emphasis.
            surface.blit(key_surf, (key_x + 1, row_y))
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


def _minimum_rows_for_group(group_name: str, rows: tuple[str, ...]) -> int:
    if not rows:
        return 0
    if group_name == "Rotation":
        return len(rows)
    configured = _MIN_ROWS_BY_GROUP.get(group_name, 1)
    return max(1, min(len(rows), int(configured)))


def _planned_group_rows(
    *,
    groups: Sequence[ControlGroup],
    available_height: int,
    panel_font: pygame.font.Font,
    hint_font: pygame.font.Font,
) -> tuple[tuple[PlannedGroupRows, ...], bool]:
    row_h = panel_font.get_height() + 2
    box_base_h = 10 + hint_font.get_height() + 6 + 8
    gap = 6
    consumed_h = 0
    overflow = False
    planned: list[PlannedGroupRows] = []
    for idx, (group_name, rows) in enumerate(groups):
        if not rows:
            continue
        remaining_groups = tuple(groups[idx + 1 :])
        reserved_h = 0
        for remaining_name, remaining_rows in remaining_groups:
            min_rows = _minimum_rows_for_group(remaining_name, remaining_rows)
            if min_rows <= 0:
                continue
            reserved_h += box_base_h + (min_rows * row_h) + gap

        max_rows_fit = (
            available_height - consumed_h - reserved_h - box_base_h
        ) // row_h
        minimum_rows = _minimum_rows_for_group(group_name, rows)
        if max_rows_fit < minimum_rows:
            max_rows_without_reserve = (
                available_height - consumed_h - box_base_h
            ) // row_h
            if max_rows_without_reserve <= 0:
                overflow = True
                continue
            max_rows_fit = max_rows_without_reserve
            overflow = True
        if max_rows_fit <= 0:
            overflow = True
            continue

        visible_count = min(len(rows), int(max_rows_fit))
        if visible_count <= 0:
            overflow = True
            continue
        if visible_count < len(rows):
            overflow = True
        visible_rows = rows[:visible_count]
        planned.append((group_name, tuple(visible_rows)))
        consumed_h += box_base_h + (visible_count * row_h) + gap
    return tuple(planned), overflow


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
    row_h = panel_font.get_height() + 2
    box_base_h = 10 + hint_font.get_height() + 6 + 8
    planned_groups, overflow = _planned_group_rows(
        groups=groups,
        available_height=max(0, rect.bottom - rect.y),
        panel_font=panel_font,
        hint_font=hint_font,
    )
    if not planned_groups:
        return _draw_overflow_hint(
            surface, rect=rect, y=y, margin_x=margin_x, hint_font=hint_font
        )

    for group_name, rows in planned_groups:
        visible_rows = tuple(rows)
        if not visible_rows:
            overflow = True
            continue
        if y + box_base_h + (len(visible_rows) * row_h) > rect.bottom:
            overflow = True
            break
        box_h = box_base_h + (len(visible_rows) * row_h)
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
            rows=visible_rows,
            box_rect=box_rect,
            row_y=row_y,
            margin_x=margin_x,
            panel_font=panel_font,
        )
        y += box_h + 6

    if overflow:
        if y >= rect.bottom:
            return _draw_overflow_hint(
                surface,
                rect=rect,
                y=rect.bottom - (hint_font.get_height() + 6),
                margin_x=margin_x,
                hint_font=hint_font,
            )
        y = _draw_overflow_hint(
            surface, rect=rect, y=y, margin_x=margin_x, hint_font=hint_font
        )

    if show_guides:
        y = _draw_optional_guides(surface, rect=rect, y=y, hint_font=hint_font)
    return y
