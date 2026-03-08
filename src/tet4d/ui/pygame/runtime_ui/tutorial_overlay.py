from __future__ import annotations

from typing import Any

import pygame

from tet4d.engine.tutorial.api import tutorial_runtime_overlay_payload_runtime
from tet4d.ui.pygame import front3d_render, front4d_render
from tet4d.ui.pygame.input.key_display import format_key_tuple
from tet4d.ui.pygame.keybindings import runtime_binding_groups_for_dimension
from tet4d.ui.pygame.ui_utils import fit_text

_PANEL_BG = (8, 12, 28, 190)
_PANEL_BORDER = (110, 136, 210, 220)
_TEXT_PRIMARY = (236, 240, 252)
_TEXT_SECONDARY = (198, 208, 236)
_TEXT_HIGHLIGHT = (255, 224, 128)
_KEY_CHIP_BG = (58, 118, 218, 220)
_KEY_CHIP_BORDER = (138, 186, 252, 230)
_KEY_CHIP_TEXT = (248, 251, 255)
_KEY_CHIP_PAD_X = 6
_KEY_CHIP_PAD_Y = 2
_KEY_CHIP_GAP = 6
_KEY_ROW_GAP = 3
_LAST_PANEL_RECT_BY_DIMENSION: dict[int, pygame.Rect] = {}
_MOUSE_ACTION_KEY_LABELS = {
    "mouse_orbit": "RMB + Move Mouse",
    "mouse_zoom": "Mouse Wheel Scroll",
}


def _normalized_dimension(dimension: int) -> int:
    return max(2, min(4, int(dimension)))


def tutorial_panel_last_rect(dimension: int) -> pygame.Rect | None:
    rect = _LAST_PANEL_RECT_BY_DIMENSION.get(_normalized_dimension(dimension))
    return rect.copy() if rect is not None else None


def _binding_lookup_for_dimension(dimension: int) -> dict[str, tuple[int, ...]]:
    merged: dict[str, tuple[int, ...]] = {}
    groups = runtime_binding_groups_for_dimension(dimension)
    for binding_map in groups.values():
        for action_id, keys in binding_map.items():
            merged[str(action_id)] = tuple(int(key) for key in keys)
    if dimension == 2:
        camera_groups = runtime_binding_groups_for_dimension(3)
        camera_map = camera_groups.get("camera", {})
        for action_id in ("overlay_alpha_dec", "overlay_alpha_inc"):
            keys = camera_map.get(action_id, ())
            if keys:
                merged[action_id] = tuple(int(key) for key in keys)
    return merged


def _key_label_for_action(
    action_id: str,
    *,
    binding_map: dict[str, tuple[int, ...]],
) -> str:
    keys = binding_map.get(action_id, ())
    if not keys:
        normalized = str(action_id).strip().lower()
        return _MOUSE_ACTION_KEY_LABELS.get(normalized, "-")
    return format_key_tuple(keys)


def _render_line(
    font: pygame.font.Font,
    text: str,
    color: tuple[int, int, int],
    *,
    bold: bool = False,
) -> pygame.Surface:
    original_bold = bool(font.get_bold())
    if original_bold != bool(bold):
        font.set_bold(bool(bold))
    surface = font.render(text, True, color)
    if original_bold != bool(bold):
        font.set_bold(original_bold)
    return surface


def _overlay_lines(
    payload: dict[str, Any],
    *,
    dimension: int,
) -> list[tuple[str, tuple[int, int, int], bool]]:
    status = str(payload.get("status", "")).strip().lower()
    running = bool(payload.get("running", False))
    status_message = str(payload.get("status_message", "")).strip()
    if not running and not status_message:
        return []
    if running:
        lines = _overlay_lines_running(payload, dimension=dimension)
    else:
        lines = _overlay_lines_terminal(status, status_message)
    lines.append(
        (
            "F5/F6: Prev/Next stage  |  F7: Redo  |  F8: Main menu  |  F9: Restart",
            _TEXT_SECONDARY,
            False,
        )
    )
    return lines


def _overlay_lines_running(
    payload: dict[str, Any],
    *,
    dimension: int,
) -> list[tuple[str, tuple[int, int, int], bool]]:
    lines = _overlay_intro_lines(payload)
    _append_key_prompt_lines(lines, payload, dimension=dimension)
    return lines


def _overlay_intro_lines(
    payload: dict[str, Any],
) -> list[tuple[str, tuple[int, int, int], bool]]:
    lines: list[tuple[str, tuple[int, int, int], bool]] = []
    lesson_title = str(payload.get("lesson_title", "")).strip() or "Tutorial"
    progress_text = str(payload.get("progress_text", "")).strip()
    heading = lesson_title if not progress_text else f"{lesson_title} ({progress_text})"
    lines.append((heading, _TEXT_HIGHLIGHT, False))
    segment_title = str(payload.get("segment_title", "")).strip()
    if segment_title:
        lines.append((f"Segment: {segment_title}", _TEXT_PRIMARY, True))
    step_text = str(payload.get("step_text", "")).strip()
    step_hint = str(payload.get("step_hint", "")).strip()
    if step_text or step_hint:
        if step_text:
            lines.append((f"Do this: {step_text}", _TEXT_PRIMARY, False))
        if step_hint and step_hint != step_text:
            lines.append((f"Tip: {step_hint}", _TEXT_SECONDARY, False))
    return lines


def _append_key_prompt_lines(
    lines: list[tuple[str, tuple[int, int, int], bool]],
    payload: dict[str, Any],
    *,
    dimension: int,
) -> None:
    key_prompts = payload.get("key_prompts")
    if not isinstance(key_prompts, list) or not key_prompts:
        return
    binding_map = _binding_lookup_for_dimension(dimension)
    for prompt_raw in key_prompts[:4]:
        action_id = str(prompt_raw).strip().lower()
        if not action_id:
            continue
        key_label = _key_label_for_action(action_id, binding_map=binding_map)
        lines.append((f"USE: {key_label}", _TEXT_HIGHLIGHT, True))


def _parse_key_action_line(line: str) -> tuple[tuple[str, ...], str] | None:
    text = str(line).strip()
    if text.lower().startswith("use:"):
        body = text[4:].strip()
        if not body:
            return None
        tokens = tuple(part.strip() for part in body.split("/") if part.strip())
        if not tokens:
            return None
        return (tokens, "")
    if not text.lower().startswith("key:"):
        return None
    body = text[4:].strip()
    key_raw, sep, action_raw = body.partition("  ")
    if not sep:
        # Backward-compatible parse path for older serialized rows.
        key_raw, sep, action_raw = body.partition("ACTION:")
    if not sep:
        return None
    key_text = str(key_raw).strip()
    action_text = str(action_raw).strip()
    if action_text.lower().startswith("action:"):
        action_text = action_text[7:].strip()
    if not key_text or not action_text:
        return None
    tokens = tuple(part.strip() for part in key_text.split("/") if part.strip())
    if not tokens:
        return None
    return (tokens, action_text)


def _key_chip_width(font: pygame.font.Font, token: str, *, max_width: int) -> int:
    label = fit_text(font, token, max_width)
    text_w = font.size(label)[0]
    return text_w + (_KEY_CHIP_PAD_X * 2)


def _wrap_key_tokens(
    font: pygame.font.Font,
    tokens: tuple[str, ...],
    *,
    max_width: int,
    first_row_prefix_w: int,
) -> tuple[tuple[str, ...], ...]:
    rows: list[list[str]] = []
    current: list[str] = []
    current_w = 0
    available_w = max(16, max_width - first_row_prefix_w)
    for token in tokens:
        token_w = _key_chip_width(font, token, max_width=max_width) + _KEY_CHIP_GAP
        if current and current_w + token_w > available_w:
            rows.append(current)
            current = [token]
            current_w = token_w
            available_w = max_width
            continue
        current.append(token)
        current_w += token_w
    if current:
        rows.append(current)
    return tuple(tuple(row) for row in rows)


def _build_key_prompt_rows(
    font: pygame.font.Font,
    *,
    key_tokens: tuple[str, ...],
    action_label: str,
    max_width: int,
) -> list[dict[str, object]]:
    key_label = "USE:"
    key_label_w = font.size(key_label)[0] + _KEY_CHIP_GAP
    token_rows = _wrap_key_tokens(
        font,
        key_tokens,
        max_width=max_width,
        first_row_prefix_w=key_label_w,
    )
    chip_h = font.get_height() + (_KEY_CHIP_PAD_Y * 2)
    key_row_h = max(chip_h, font.get_height()) + _KEY_ROW_GAP
    rows: list[dict[str, object]] = []
    for idx, token_row in enumerate(token_rows):
        rows.append(
            {
                "kind": "key_tokens",
                "font": font,
                "tokens": token_row,
                "show_key_label": idx == 0,
                "key_label": key_label,
                "row_h": key_row_h,
            }
        )
    if action_label:
        action_lines = _wrap_text_line(font, f"Do: {action_label}", max_width=max_width)
        text_row_h = max(16, font.get_height() + 4)
        for action_line in action_lines:
            rows.append(
                {
                    "kind": "text",
                    "font": font,
                    "text": action_line,
                    "color": _TEXT_PRIMARY,
                    "bold": False,
                    "row_h": text_row_h,
                }
            )
    return rows


def _draw_key_prompt_row(
    screen: pygame.Surface,
    *,
    panel_rect: pygame.Rect,
    font: pygame.font.Font,
    tokens: tuple[str, ...],
    show_key_label: bool,
    key_label: str,
    y: int,
    text_w: int,
) -> None:
    x = panel_rect.x + 9
    chip_h = font.get_height() + (_KEY_CHIP_PAD_Y * 2)
    base_y = y + 1
    if show_key_label:
        key_label_surf = _render_line(font, key_label, _TEXT_SECONDARY, bold=True)
        screen.blit(key_label_surf, (x, y))
        x += key_label_surf.get_width() + _KEY_CHIP_GAP
    max_chip_text_w = max(16, text_w - (_KEY_CHIP_PAD_X * 2))
    for token in tokens:
        token_text = fit_text(font, token, max_chip_text_w)
        token_surf = _render_line(font, token_text, _KEY_CHIP_TEXT, bold=True)
        chip_w = token_surf.get_width() + (_KEY_CHIP_PAD_X * 2)
        chip_rect = pygame.Rect(x, base_y, chip_w, chip_h)
        pygame.draw.rect(screen, _KEY_CHIP_BG, chip_rect, border_radius=8)
        pygame.draw.rect(screen, _KEY_CHIP_BORDER, chip_rect, width=1, border_radius=8)
        screen.blit(
            token_surf,
            (chip_rect.x + _KEY_CHIP_PAD_X, chip_rect.y + _KEY_CHIP_PAD_Y),
        )
        x += chip_w + _KEY_CHIP_GAP


def _overlay_lines_terminal(
    status: str,
    status_message: str,
) -> list[tuple[str, tuple[int, int, int], bool]]:
    if status == "completed":
        return [("Tutorial complete", _TEXT_HIGHLIGHT, False)]
    if status == "skipped":
        return [("Tutorial exited", _TEXT_HIGHLIGHT, False)]
    if status_message:
        return [(status_message, _TEXT_HIGHLIGHT, False)]
    return []


def _panel_base_geometry(
    *,
    width: int,
    dimension: int,
) -> tuple[int, int, int]:
    if dimension in (3, 4):
        if dimension == 3:
            margin = int(front3d_render.MARGIN)
            side_panel = int(front3d_render.SIDE_PANEL)
        else:
            margin = int(front4d_render.MARGIN)
            side_panel = int(front4d_render.SIDE_PANEL)
        lane_left = max(0, width - side_panel - margin)
        lane_width = max(0, min(side_panel, width - lane_left))
        panel_x = lane_left + 8
        panel_w = max(0, min(max(240, side_panel - 16), max(0, lane_width - 16)))
        panel_y = max(12, margin + 8)
        return panel_x, panel_y, panel_w
    panel_w = min(760, max(420, int(width * 0.52)))
    return 12, 12, panel_w


def _panel_x_bounds(
    *,
    width: int,
    dimension: int,
    panel_w: int,
) -> tuple[int, int]:
    max_x = max(0, width - panel_w)
    if dimension not in (3, 4):
        return 0, max_x
    if dimension == 3:
        margin = int(front3d_render.MARGIN)
        side_panel = int(front3d_render.SIDE_PANEL)
    else:
        margin = int(front4d_render.MARGIN)
        side_panel = int(front4d_render.SIDE_PANEL)
    lane_left = max(0, width - side_panel - margin)
    lane_right = max(lane_left, width - margin)
    min_x = max(0, lane_left + 8)
    max_lane_x = max(min_x, lane_right - 8 - panel_w)
    return min_x, min(max_x, max_lane_x)


def _panel_rect_for_dimension(
    *,
    width: int,
    height: int,
    dimension: int,
    panel_h: int,
    panel_offset: tuple[int, int] = (0, 0),
) -> pygame.Rect:
    panel_x, panel_y, panel_w = _panel_base_geometry(
        width=width,
        dimension=dimension,
    )
    offset_x = int(panel_offset[0]) if panel_offset else 0
    offset_y = int(panel_offset[1]) if panel_offset else 0
    panel_x += offset_x
    panel_y += offset_y

    min_x, max_x = _panel_x_bounds(
        width=width,
        dimension=dimension,
        panel_w=panel_w,
    )
    max_y = max(0, height - panel_h)
    panel_x = max(min_x, min(max_x, panel_x))
    panel_y = max(0, min(max_y, panel_y))
    return pygame.Rect(panel_x, panel_y, panel_w, panel_h)


def _split_long_token(
    font: pygame.font.Font,
    token: str,
    *,
    max_width: int,
) -> tuple[str, ...]:
    if not token:
        return ()
    chunks: list[str] = []
    current = ""
    for char in token:
        candidate = f"{current}{char}"
        if current and font.size(candidate)[0] > max_width:
            chunks.append(current)
            current = char
        else:
            current = candidate
    if current:
        chunks.append(current)
    return tuple(chunks)


def _wrap_text_line(
    font: pygame.font.Font,
    text: str,
    *,
    max_width: int,
) -> tuple[str, ...]:
    clean = " ".join(str(text).split())
    if not clean:
        return ()
    if font.size(clean)[0] <= max_width:
        return (clean,)

    wrapped: list[str] = []
    current = ""
    for token in clean.split(" "):
        if not token:
            continue
        candidate = token if not current else f"{current} {token}"
        if current and font.size(candidate)[0] > max_width:
            wrapped.append(current)
            current = token
        else:
            current = candidate
        if font.size(current)[0] <= max_width:
            continue
        token_chunks = _split_long_token(font, current, max_width=max_width)
        if not token_chunks:
            current = ""
            continue
        wrapped.extend(token_chunks[:-1])
        current = token_chunks[-1]

    if current:
        wrapped.append(current)
    return tuple(line for line in wrapped if line)


def draw_tutorial_overlay(
    screen: pygame.Surface,
    fonts: Any,
    *,
    dimension: int,
    tutorial_session: Any,
    panel_offset: tuple[int, int] = (0, 0),
) -> None:
    payload = tutorial_runtime_overlay_payload_runtime(tutorial_session)
    base_lines = _overlay_lines(payload, dimension=dimension)
    if not base_lines:
        return

    width, height = screen.get_size()
    dim = _normalized_dimension(dimension)
    _base_x, _base_y, panel_w = _panel_base_geometry(width=width, dimension=dim)
    text_w = max(120, panel_w - 18)

    drawn_rows: list[dict[str, object]] = []
    for idx, (line, color, bold) in enumerate(base_lines):
        font = fonts.menu_font if idx == 0 else fonts.hint_font
        key_action = _parse_key_action_line(line)
        if key_action is not None:
            key_tokens, action_label = key_action
            drawn_rows.extend(
                _build_key_prompt_rows(
                    font,
                    key_tokens=key_tokens,
                    action_label=action_label,
                    max_width=text_w,
                )
            )
            continue
        wrapped = _wrap_text_line(font, line, max_width=text_w)
        if not wrapped:
            continue
        row_h = max(16, font.get_height() + 4)
        for wrapped_line in wrapped:
            drawn_rows.append(
                {
                    "kind": "text",
                    "font": font,
                    "text": wrapped_line,
                    "color": color,
                    "bold": bold,
                    "row_h": row_h,
                }
            )
    if not drawn_rows:
        return

    panel_h = 12 + sum(int(row["row_h"]) for row in drawn_rows)
    panel_rect = _panel_rect_for_dimension(
        width=width,
        height=height,
        dimension=dim,
        panel_h=panel_h,
        panel_offset=panel_offset,
    )
    _LAST_PANEL_RECT_BY_DIMENSION[dim] = panel_rect.copy()

    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _PANEL_BG, panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, _PANEL_BORDER, panel.get_rect(), width=1, border_radius=10)
    screen.blit(panel, panel_rect.topleft)

    y = panel_rect.y + 6
    for row in drawn_rows:
        kind = str(row["kind"])
        if kind == "key_tokens":
            _draw_key_prompt_row(
                screen,
                panel_rect=panel_rect,
                font=row["font"],
                tokens=tuple(row["tokens"]),
                show_key_label=bool(row["show_key_label"]),
                key_label=str(row.get("key_label", "USE:")),
                y=y,
                text_w=text_w,
            )
            y += int(row["row_h"])
            continue
        font = row["font"]
        line = str(row["text"])
        color = tuple(row["color"])
        bold = bool(row["bold"])
        draw_text = fit_text(font, line, text_w)
        line_surf = _render_line(font, draw_text, color, bold=bold)
        screen.blit(line_surf, (panel_rect.x + 9, y))
        y += int(row["row_h"])

