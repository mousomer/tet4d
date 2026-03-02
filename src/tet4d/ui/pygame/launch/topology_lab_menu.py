from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.menu.numeric_text_input import (
    append_numeric_text,
    parse_numeric_text,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_NUMERIC_TEXT_MAX_LENGTH = 16
_TOPOLOGY_DIMENSIONS = (2, 3, 4)


def _sanitize_text(value: str, max_length: int) -> str:
    return engine_api.sanitize_text_runtime(value, max_length=max_length)


def _safe_lab_payload() -> dict[str, Any]:
    fallback = {
        "title": "Topology Lab",
        "subtitle": "Interactive topology editor",
        "rows": (
            {"key": "dimension", "label": "Dimension"},
            {"key": "topology_mode", "label": "Topology mode"},
            {"key": "topology_advanced", "label": "Advanced topology"},
            {"key": "topology_profile_index", "label": "Designer profile"},
            {"key": "save_mode", "label": "Save to mode settings"},
            {"key": "export", "label": "Export resolved profile"},
            {"key": "back", "label": "Back"},
        ),
        "hints": (
            "Up/Down select row",
            "Left/Right change values",
            "Enter triggers Save/Export/Back",
        ),
        "status_copy": {
            "saved": "Saved topology settings for {mode_key}",
            "save_failed": "Failed saving topology settings: {message}",
            "updated": "Topology setting updated (not saved yet)",
            "text_mode": "Type profile index, Enter apply, Esc cancel",
            "invalid_number": "Invalid profile index",
            "export_ok": "{message}",
            "export_error": "{message}",
        },
    }
    try:
        payload = engine_api.topology_lab_menu_payload_runtime()
    except (OSError, ValueError, RuntimeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    return {
        "title": str(payload.get("title", fallback["title"])),
        "subtitle": str(payload.get("subtitle", fallback["subtitle"])),
        "rows": tuple(payload.get("rows", fallback["rows"])),
        "hints": tuple(payload.get("hints", fallback["hints"])),
        "status_copy": dict(payload.get("status_copy", fallback["status_copy"])),
    }


_LAB_COPY = _safe_lab_payload()
_LAB_TITLE = str(_LAB_COPY["title"])
_LAB_SUBTITLE = str(_LAB_COPY["subtitle"])
_LAB_ROWS = tuple(
    (
        str(row.get("key", "")).strip().lower(),
        str(row.get("label", "")).strip(),
    )
    for row in _LAB_COPY["rows"]
    if isinstance(row, dict)
)
_LAB_HINTS = tuple(str(hint) for hint in _LAB_COPY["hints"])
_LAB_STATUS_COPY = dict(_LAB_COPY["status_copy"])
_LAB_SELECTABLE_ROWS = tuple(
    idx for idx, (row_key, _label) in enumerate(_LAB_ROWS) if bool(row_key)
)
_TOPOLOGY_MODE_OPTIONS = tuple(engine_api.topology_mode_options_runtime())


@dataclass
class _TopologyLabState:
    payload: dict[str, Any]
    selected: int
    dimension: int
    topology_mode_index: int
    topology_advanced: int
    topology_profile_index: int
    status: str = ""
    status_error: bool = False
    running: bool = True
    dirty: bool = False
    text_mode_row_key: str = ""
    text_mode_buffer: str = ""
    text_mode_replace_on_type: bool = False


def _set_status(
    state: _TopologyLabState,
    message: str,
    *,
    is_error: bool = False,
) -> None:
    state.status = message
    state.status_error = is_error


def _is_text_mode(state: _TopologyLabState) -> bool:
    return bool(state.text_mode_row_key)


def _stop_text_mode(state: _TopologyLabState) -> None:
    if _is_text_mode(state):
        pygame.key.stop_text_input()
    state.text_mode_row_key = ""
    state.text_mode_buffer = ""
    state.text_mode_replace_on_type = False


def _start_profile_text_mode(state: _TopologyLabState) -> None:
    _stop_text_mode(state)
    state.text_mode_row_key = "topology_profile_index"
    state.text_mode_buffer = str(int(state.topology_profile_index))
    state.text_mode_replace_on_type = True
    pygame.key.start_text_input()
    _set_status(state, str(_LAB_STATUS_COPY["text_mode"]))


def _safe_mode_settings(payload: dict[str, Any], mode_key: str) -> dict[str, Any]:
    settings = payload.get("settings")
    if not isinstance(settings, dict):
        settings = {}
        payload["settings"] = settings
    mode_settings = settings.get(mode_key)
    if not isinstance(mode_settings, dict):
        mode_settings = {}
        settings[mode_key] = mode_settings
    return mode_settings


def _profile_count_for_dimension(dimension: int) -> int:
    profiles = engine_api.topology_designer_profiles_runtime(dimension)
    return max(1, len(profiles))


def _clamp_profile_index(dimension: int, index: int) -> int:
    return max(0, min(_profile_count_for_dimension(dimension) - 1, int(index)))


def _mode_key_for_dimension(dimension: int) -> str:
    safe_dimension = max(2, min(4, int(dimension)))
    return f"{safe_dimension}d"


def _load_dimension_settings(state: _TopologyLabState) -> None:
    mode_key = _mode_key_for_dimension(state.dimension)
    mode_settings = _safe_mode_settings(state.payload, mode_key)
    mode_index = mode_settings.get("topology_mode", 0)
    if isinstance(mode_index, bool) or not isinstance(mode_index, int):
        mode_index = 0
    state.topology_mode_index = max(
        0,
        min(len(_TOPOLOGY_MODE_OPTIONS) - 1, int(mode_index)),
    )
    state.topology_advanced = engine_api.clamp_toggle_index_runtime(
        mode_settings.get("topology_advanced", 0),
        default=0,
    )
    profile_index = mode_settings.get("topology_profile_index", 0)
    if isinstance(profile_index, bool) or not isinstance(profile_index, int):
        profile_index = 0
    state.topology_profile_index = _clamp_profile_index(state.dimension, profile_index)


def _save_dimension_settings(state: _TopologyLabState) -> tuple[bool, str]:
    mode_key = _mode_key_for_dimension(state.dimension)
    mode_settings = _safe_mode_settings(state.payload, mode_key)
    mode_settings["topology_mode"] = int(state.topology_mode_index)
    mode_settings["topology_advanced"] = engine_api.clamp_toggle_index_runtime(
        state.topology_advanced,
        default=0,
    )
    mode_settings["topology_profile_index"] = _clamp_profile_index(
        state.dimension,
        state.topology_profile_index,
    )
    ok, msg = engine_api.save_menu_payload_runtime(state.payload)
    if ok:
        state.dirty = False
        _set_status(state, str(_LAB_STATUS_COPY["saved"]).format(mode_key=mode_key))
        return True, msg
    _set_status(
        state,
        str(_LAB_STATUS_COPY["save_failed"]).format(message=msg),
        is_error=True,
    )
    return False, msg


def _mode_value_text(state: _TopologyLabState) -> str:
    mode = engine_api.topology_mode_from_index_runtime(state.topology_mode_index)
    return engine_api.topology_mode_label_runtime(mode)


def _profile_value_text(state: _TopologyLabState) -> str:
    label = engine_api.topology_designer_profile_label_runtime(
        state.dimension,
        state.topology_profile_index,
    )
    return f"{int(state.topology_profile_index)}: {label}"


def _resolve_preview_text(state: _TopologyLabState) -> str:
    mode = engine_api.topology_mode_from_index_runtime(state.topology_mode_index)
    resolved_mode, _rules, _profile = engine_api.topology_designer_resolve_runtime(
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=mode,
        topology_advanced=bool(state.topology_advanced),
        profile_index=state.topology_profile_index,
    )
    return engine_api.topology_mode_label_runtime(resolved_mode)


def _row_value_text(state: _TopologyLabState, row_key: str) -> str:
    if _is_text_mode(state) and row_key == state.text_mode_row_key:
        return f"{state.text_mode_buffer}_"
    if row_key == "dimension":
        return f"{state.dimension}D"
    if row_key == "topology_mode":
        return _mode_value_text(state)
    if row_key == "topology_advanced":
        return "ON" if int(state.topology_advanced) else "OFF"
    if row_key == "topology_profile_index":
        return _profile_value_text(state)
    if row_key == "save_mode":
        return _mode_key_for_dimension(state.dimension).upper()
    if row_key == "export":
        return _resolve_preview_text(state)
    return ""


def _draw_menu(screen: pygame.Surface, fonts, state: _TopologyLabState) -> None:
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render(_LAB_TITLE, True, _TEXT_COLOR)
    subtitle_text = fit_text(fonts.hint_font, _LAB_SUBTITLE, width - 28)
    subtitle = fonts.hint_font.render(subtitle_text, True, _MUTED_COLOR)
    title_y = 46
    subtitle_y = title_y + title.get_height() + 8
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, subtitle_y))

    panel_w = min(760, max(360, width - 40))
    panel_h = min(height - 170, 120 + len(_LAB_ROWS) * 46)
    panel_x = (width - panel_w) // 2
    panel_y = max(130, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    selected_row = _LAB_SELECTABLE_ROWS[state.selected]
    y = panel_y + 18
    row_h = 46
    for idx, (row_key, row_label) in enumerate(_LAB_ROWS):
        selected = idx == selected_row
        color = _HIGHLIGHT_COLOR if selected else _TEXT_COLOR
        if selected:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 4))
        label_draw = fit_text(fonts.menu_font, row_label, panel_w // 2)
        label = fonts.menu_font.render(label_draw, True, color)
        value_text = _row_value_text(state, row_key)
        value_draw = fit_text(fonts.menu_font, value_text, panel_w // 2)
        value = fonts.menu_font.render(value_draw, True, color)
        screen.blit(label, (panel_x + 22, y))
        screen.blit(value, (panel_x + panel_w - value.get_width() - 22, y))
        y += row_h

    hint_y = panel_y + panel_h + 10
    for hint in _LAB_HINTS:
        hint_draw = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_draw, True, _MUTED_COLOR)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3
    if state.status:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 24)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 2))


def _mark_updated(state: _TopologyLabState) -> None:
    state.dirty = True
    _set_status(state, str(_LAB_STATUS_COPY["updated"]))


def _adjust_active_row(state: _TopologyLabState, delta_sign: int) -> bool:
    row_key = _LAB_ROWS[_LAB_SELECTABLE_ROWS[state.selected]][0]
    if row_key == "dimension":
        current = _TOPOLOGY_DIMENSIONS.index(state.dimension)
        state.dimension = _TOPOLOGY_DIMENSIONS[
            (current + delta_sign) % len(_TOPOLOGY_DIMENSIONS)
        ]
        _load_dimension_settings(state)
        _mark_updated(state)
        return True
    if row_key == "topology_mode":
        state.topology_mode_index = (
            state.topology_mode_index + delta_sign
        ) % len(_TOPOLOGY_MODE_OPTIONS)
        _mark_updated(state)
        return True
    if row_key == "topology_advanced":
        state.topology_advanced = 0 if int(state.topology_advanced) else 1
        _mark_updated(state)
        return True
    if row_key == "topology_profile_index":
        next_index = state.topology_profile_index + delta_sign
        state.topology_profile_index = _clamp_profile_index(state.dimension, next_index)
        _mark_updated(state)
        return True
    return False


def _apply_profile_index_from_text(state: _TopologyLabState) -> bool:
    parsed = parse_numeric_text(
        state.text_mode_buffer,
        max_length=_NUMERIC_TEXT_MAX_LENGTH,
        sanitize_text=_sanitize_text,
    )
    if parsed is None:
        _set_status(state, str(_LAB_STATUS_COPY["invalid_number"]), is_error=True)
        return False
    state.topology_profile_index = _clamp_profile_index(state.dimension, parsed)
    _mark_updated(state)
    return True


def _dispatch_text_mode_key(state: _TopologyLabState, key: int) -> bool:
    if not _is_text_mode(state):
        return False
    if key == pygame.K_ESCAPE:
        _stop_text_mode(state)
        _set_status(state, "Profile index edit cancelled")
        return True
    if key == pygame.K_BACKSPACE:
        state.text_mode_replace_on_type = False
        state.text_mode_buffer = state.text_mode_buffer[:-1]
        return True
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        updated = _apply_profile_index_from_text(state)
        _stop_text_mode(state)
        if updated:
            play_sfx("menu_move")
        return True
    return True


def _handle_navigation_key(state: _TopologyLabState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        state.running = False
        return True
    if key == pygame.K_UP:
        state.selected = (state.selected - 1) % len(_LAB_SELECTABLE_ROWS)
        play_sfx("menu_move")
        return True
    if key == pygame.K_DOWN:
        state.selected = (state.selected + 1) % len(_LAB_SELECTABLE_ROWS)
        play_sfx("menu_move")
        return True
    if key in (pygame.K_LEFT, pygame.K_RIGHT):
        delta_sign = -1 if key == pygame.K_LEFT else 1
        if _adjust_active_row(state, delta_sign):
            play_sfx("menu_move")
        return True
    return False


def _handle_shortcut_key(state: _TopologyLabState, key: int) -> bool:
    if key == pygame.K_e:
        _run_export(state)
        return True
    if key == pygame.K_s:
        _save_dimension_settings(state)
        return True
    return False


def _dispatch_enter(state: _TopologyLabState) -> None:
    row_key = _LAB_ROWS[_LAB_SELECTABLE_ROWS[state.selected]][0]
    if row_key == "topology_profile_index":
        _start_profile_text_mode(state)
        return
    if row_key == "save_mode":
        _save_dimension_settings(state)
        return
    if row_key == "export":
        _run_export(state)
        return
    if row_key == "back":
        state.running = False
        return
    if _adjust_active_row(state, 1):
        play_sfx("menu_move")


def _dispatch_key(state: _TopologyLabState, key: int) -> None:
    if _dispatch_text_mode_key(state, key):
        return
    if _handle_navigation_key(state, key):
        return
    if _handle_shortcut_key(state, key):
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _dispatch_enter(state)


def _run_export(state: _TopologyLabState) -> None:
    mode = engine_api.topology_mode_from_index_runtime(state.topology_mode_index)
    ok, msg, _path = engine_api.topology_designer_export_runtime(
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=mode,
        topology_advanced=bool(state.topology_advanced),
        profile_index=state.topology_profile_index,
    )
    if ok:
        _set_status(state, str(_LAB_STATUS_COPY["export_ok"]).format(message=msg))
        play_sfx("menu_confirm")
        return
    _set_status(
        state,
        str(_LAB_STATUS_COPY["export_error"]).format(message=msg),
        is_error=True,
    )


def run_topology_lab_menu(
    screen: pygame.Surface,
    fonts,
    *,
    start_dimension: int,
) -> tuple[bool, str]:
    payload = engine_api.load_menu_payload_runtime()
    initial_dimension = (
        start_dimension if start_dimension in _TOPOLOGY_DIMENSIONS else 2
    )
    state = _TopologyLabState(
        payload=payload if isinstance(payload, dict) else {},
        selected=0,
        dimension=initial_dimension,
        topology_mode_index=0,
        topology_advanced=0,
        topology_profile_index=0,
    )
    _load_dimension_settings(state)
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.running = False
                break
            if event.type == pygame.TEXTINPUT and _is_text_mode(state):
                state.text_mode_buffer, state.text_mode_replace_on_type = (
                    append_numeric_text(
                        current_buffer=state.text_mode_buffer,
                        incoming_text=event.text,
                        replace_on_type=state.text_mode_replace_on_type,
                        max_length=_NUMERIC_TEXT_MAX_LENGTH,
                        sanitize_text=_sanitize_text,
                    )
                )
                continue
            if event.type != pygame.KEYDOWN:
                continue
            _dispatch_key(state, event.key)
            if not state.running:
                break
        _draw_menu(screen, fonts, state)
        pygame.display.flip()

    _stop_text_mode(state)
    if state.dirty:
        ok, msg = _save_dimension_settings(state)
        if ok:
            return True, msg
        return False, msg
    if state.status:
        return (not state.status_error), state.status
    return True, "Topology Lab unchanged"
