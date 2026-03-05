from __future__ import annotations

from typing import Any

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.ui_utils import fit_text

_PANEL_BG = (8, 12, 28, 190)
_PANEL_BORDER = (110, 136, 210, 220)
_TEXT_PRIMARY = (236, 240, 252)
_TEXT_SECONDARY = (198, 208, 236)
_TEXT_HIGHLIGHT = (255, 224, 128)
_LAST_PANEL_RECT_BY_DIMENSION: dict[int, pygame.Rect] = {}


def _normalized_dimension(dimension: int) -> int:
    return max(2, min(4, int(dimension)))


def tutorial_panel_last_rect(dimension: int) -> pygame.Rect | None:
    rect = _LAST_PANEL_RECT_BY_DIMENSION.get(_normalized_dimension(dimension))
    return rect.copy() if rect is not None else None


def _binding_lookup_for_dimension(dimension: int) -> dict[str, tuple[int, ...]]:
    merged: dict[str, tuple[int, ...]] = {}
    groups = engine_api.runtime_binding_groups_for_dimension(dimension)
    for binding_map in groups.values():
        for action_id, keys in binding_map.items():
            merged[str(action_id)] = tuple(int(key) for key in keys)
    if dimension == 2:
        camera_groups = engine_api.runtime_binding_groups_for_dimension(3)
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
        return "-"
    return engine_api.format_key_tuple(keys)


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
    _append_focus_lines(lines, payload)
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
    if step_text:
        lines.append((f"Task: {step_text}", _TEXT_PRIMARY, False))
    step_hint = str(payload.get("step_hint", "")).strip()
    if step_hint:
        lines.append((f"How: {step_hint}", _TEXT_SECONDARY, False))
    return lines


def _append_focus_lines(
    lines: list[tuple[str, tuple[int, int, int], bool]],
    payload: dict[str, Any],
) -> None:
    highlights = payload.get("highlights")
    if isinstance(highlights, list) and highlights:
        focus = ", ".join(str(item).strip() for item in highlights[:3] if str(item).strip())
        if focus:
            lines.append((f"Focus: {focus}", _TEXT_SECONDARY, False))


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
        action_label = engine_api.binding_action_description(action_id)
        lines.append((f"KEY: {key_label}  ACTION: {action_label}", _TEXT_HIGHLIGHT, True))
    controls = _system_controls_line(binding_map=binding_map)
    if controls:
        lines.append((controls, _TEXT_SECONDARY, False))


def _system_controls_line(*, binding_map: dict[str, tuple[int, ...]]) -> str:
    action_order = ("help", "menu", "restart", "quit")
    parts: list[str] = []
    for action_id in action_order:
        key_label = _key_label_for_action(action_id, binding_map=binding_map)
        if key_label == "-":
            continue
        label = engine_api.binding_action_description(action_id)
        parts.append(f"{label}: {key_label}")
    if not parts:
        return ""
    return "System (not staged): " + " | ".join(parts)


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
            margin = int(engine_api.front3d_render_margin())
            side_panel = int(engine_api.front3d_render_side_panel())
        else:
            margin = int(engine_api.front4d_render_margin())
            side_panel = int(engine_api.front4d_render_side_panel())
        hud_x = width - side_panel - margin
        panel_x = max(12, hud_x + 8)
        panel_w = max(240, side_panel - 16)
        panel_w = min(panel_w, max(240, width - panel_x - 12))
        panel_y = max(12, margin + 8)
        return panel_x, panel_y, panel_w
    panel_w = min(760, max(420, int(width * 0.52)))
    return 12, 12, panel_w


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

    max_x = max(0, width - panel_w)
    max_y = max(0, height - panel_h)
    panel_x = max(0, min(max_x, panel_x))
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
    payload = engine_api.tutorial_runtime_overlay_payload_runtime(tutorial_session)
    base_lines = _overlay_lines(payload, dimension=dimension)
    if not base_lines:
        return

    width, height = screen.get_size()
    dim = _normalized_dimension(dimension)
    _base_x, _base_y, panel_w = _panel_base_geometry(width=width, dimension=dim)
    text_w = max(120, panel_w - 18)

    drawn_rows: list[tuple[pygame.font.Font, str, tuple[int, int, int], bool, int]] = []
    for idx, (line, color, bold) in enumerate(base_lines):
        font = fonts.menu_font if idx == 0 else fonts.hint_font
        wrapped = _wrap_text_line(font, line, max_width=text_w)
        if not wrapped:
            continue
        row_h = max(16, font.get_height() + 4)
        for wrapped_line in wrapped:
            drawn_rows.append((font, wrapped_line, color, bold, row_h))
    if not drawn_rows:
        return

    panel_h = 12 + sum(row_h for *_rest, row_h in drawn_rows)
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
    for font, line, color, bold, row_h in drawn_rows:
        draw_text = fit_text(font, line, text_w)
        line_surf = _render_line(font, draw_text, color, bold=bold)
        screen.blit(line_surf, (panel_rect.x + 9, y))
        y += row_h
