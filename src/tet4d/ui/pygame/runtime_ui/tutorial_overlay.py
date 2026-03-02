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


def _binding_lookup_for_dimension(dimension: int) -> dict[str, tuple[int, ...]]:
    merged: dict[str, tuple[int, ...]] = {}
    groups = engine_api.runtime_binding_groups_for_dimension(dimension)
    for binding_map in groups.values():
        for action_id, keys in binding_map.items():
            merged[str(action_id)] = tuple(int(key) for key in keys)
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


def _render_line(font: pygame.font.Font, text: str, color: tuple[int, int, int]) -> pygame.Surface:
    return font.render(text, True, color)


def _overlay_lines(
    payload: dict[str, Any],
    *,
    dimension: int,
) -> list[tuple[str, tuple[int, int, int]]]:
    status = str(payload.get("status", "")).strip().lower()
    running = bool(payload.get("running", False))
    status_message = str(payload.get("status_message", "")).strip()
    if not running and not status_message:
        return []
    if running:
        lines = _overlay_lines_running(payload, dimension=dimension)
    else:
        lines = _overlay_lines_terminal(status, status_message)
    lines.append(("F8: Skip  |  F9: Restart tutorial", _TEXT_SECONDARY))
    return lines


def _overlay_lines_running(
    payload: dict[str, Any],
    *,
    dimension: int,
) -> list[tuple[str, tuple[int, int, int]]]:
    lines: list[tuple[str, tuple[int, int, int]]] = []
    lesson_title = str(payload.get("lesson_title", "")).strip() or "Tutorial"
    progress_text = str(payload.get("progress_text", "")).strip()
    heading = lesson_title if not progress_text else f"{lesson_title} ({progress_text})"
    lines.append((heading, _TEXT_HIGHLIGHT))
    step_text = str(payload.get("step_text", "")).strip()
    if step_text:
        lines.append((step_text, _TEXT_PRIMARY))
    step_hint = str(payload.get("step_hint", "")).strip()
    if step_hint:
        lines.append((step_hint, _TEXT_SECONDARY))
    highlights = payload.get("highlights")
    if isinstance(highlights, list) and highlights:
        focus = ", ".join(str(item).strip() for item in highlights[:3] if str(item).strip())
        if focus:
            lines.append((f"Focus: {focus}", _TEXT_SECONDARY))
    key_prompts = payload.get("key_prompts")
    if not isinstance(key_prompts, list) or not key_prompts:
        return lines
    binding_map = _binding_lookup_for_dimension(dimension)
    for prompt_raw in key_prompts[:4]:
        action_id = str(prompt_raw).strip().lower()
        if not action_id:
            continue
        key_label = _key_label_for_action(action_id, binding_map=binding_map)
        action_label = engine_api.binding_action_description(action_id)
        lines.append((f"{action_label}: {key_label}", _TEXT_SECONDARY))
    return lines


def _overlay_lines_terminal(
    status: str,
    status_message: str,
) -> list[tuple[str, tuple[int, int, int]]]:
    if status == "completed":
        return [("Tutorial complete", _TEXT_HIGHLIGHT)]
    if status == "skipped":
        return [("Tutorial skipped", _TEXT_HIGHLIGHT)]
    if status_message:
        return [(status_message, _TEXT_HIGHLIGHT)]
    return []


def draw_tutorial_overlay(
    screen: pygame.Surface,
    fonts: Any,
    *,
    dimension: int,
    tutorial_session: Any,
) -> None:
    payload = engine_api.tutorial_runtime_overlay_payload_runtime(tutorial_session)
    lines = _overlay_lines(payload, dimension=dimension)
    if not lines:
        return
    width, _height = screen.get_size()
    panel_w = min(560, max(320, width // 2))
    line_h = max(fonts.hint_font.get_height() + 4, 18)
    panel_h = 16 + line_h * len(lines)
    panel_x = max(12, width - panel_w - 12)
    panel_y = 12
    panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
    panel = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, _PANEL_BG, panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, _PANEL_BORDER, panel.get_rect(), width=1, border_radius=10)
    screen.blit(panel, panel_rect.topleft)

    y = panel_y + 8
    text_w = panel_w - 18
    for idx, (line, color) in enumerate(lines):
        font = fonts.menu_font if idx == 0 else fonts.hint_font
        draw_text = fit_text(font, line, text_w)
        line_surf = _render_line(font, draw_text, color)
        screen.blit(line_surf, (panel_x + 9, y))
        y += line_h
