from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from tet4d.engine.gameplay.topology import (
    EDGE_BEHAVIOR_OPTIONS,
    default_edge_rules_for_mode,
    topology_mode_from_index,
    topology_mode_label,
)
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    designer_profiles_for_dimension,
    export_topology_profile_state,
    profile_state_from_preset,
    topology_gameplay_mode_label,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.api import topology_lab_menu_payload_runtime
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    save_topology_profile,
    topology_profile_note,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (130, 138, 168)
_TOPOLOGY_DIMENSIONS = (3, 4)
_EDGE_LABELS = {
    "bounded": "Bounded",
    "wrap": "Wrap",
    "invert": "Invert",
}
_AXIS_LABELS = {"x": "X", "y": "Y", "z": "Z", "w": "W"}


def _safe_lab_payload() -> dict[str, Any]:
    fallback = {
        "title": "Topology Lab",
        "subtitle": "Mode-aware topology profiles",
        "hints": (
            "Up/Down select row",
            "Left/Right change values",
            "Enter triggers Save/Export/Back",
            "Normal Game locks Y boundaries",
            "Explorer Mode allows vertical wrapping",
        ),
        "status_copy": {
            "saved": "Saved topology profile for {mode_label} {dimension}D",
            "save_failed": "Failed saving topology profile: {message}",
            "updated": "Topology profile updated (not saved yet)",
            "locked": "Y boundaries are fixed in Normal Game",
            "export_ok": "{message}",
            "export_error": "{message}",
        },
    }
    try:
        payload = topology_lab_menu_payload_runtime()
    except (OSError, ValueError, RuntimeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    return {
        "title": str(payload.get("title", fallback["title"])),
        "subtitle": str(payload.get("subtitle", fallback["subtitle"])),
        "hints": tuple(payload.get("hints", fallback["hints"])),
        "status_copy": dict(payload.get("status_copy", fallback["status_copy"])),
    }


_LAB_COPY = _safe_lab_payload()
_LAB_TITLE = str(_LAB_COPY["title"])
_LAB_SUBTITLE = str(_LAB_COPY["subtitle"])
_LAB_HINTS = tuple(str(hint) for hint in _LAB_COPY["hints"])
_LAB_STATUS_COPY = dict(_LAB_COPY["status_copy"])


@dataclass(frozen=True)
class _RowSpec:
    key: str
    label: str
    axis: int | None = None
    side: int | None = None
    disabled: bool = False


@dataclass
class _TopologyLabState:
    selected: int
    gameplay_mode: str
    dimension: int
    profile: TopologyProfileState
    status: str = ""
    status_error: bool = False
    running: bool = True
    dirty: bool = False


def _set_status(state: _TopologyLabState, message: str, *, is_error: bool = False) -> None:
    state.status = message
    state.status_error = is_error


def _profile_for_state(state: _TopologyLabState) -> TopologyProfileState:
    return load_topology_profile(state.gameplay_mode, state.dimension)


def _sync_profile(state: _TopologyLabState) -> None:
    state.profile = _profile_for_state(state)


def _preset_profiles(state: _TopologyLabState):
    return designer_profiles_for_dimension(state.dimension, state.gameplay_mode)


def _preset_index(state: _TopologyLabState) -> int:
    profiles = _preset_profiles(state)
    preset_id = state.profile.preset_id
    if not preset_id:
        return 0
    for idx, profile in enumerate(profiles):
        if profile.profile_id == preset_id:
            return idx
    return 0


def _rows_for_state(state: _TopologyLabState) -> tuple[_RowSpec, ...]:
    rows = [
        _RowSpec("gameplay_mode", "Game Type"),
        _RowSpec("dimension", "Dimension"),
        _RowSpec("preset", "Preset"),
        _RowSpec("topology_mode", "Topology Mode"),
    ]
    axis_names = ("x", "y", "z") if state.dimension == 3 else ("x", "y", "z", "w")
    for axis_name in axis_names:
        axis = "xyzw".index(axis_name)
        disabled = axis_name == "y" and state.gameplay_mode == GAMEPLAY_MODE_NORMAL
        rows.append(_RowSpec(f"{axis_name}_neg", f"{_AXIS_LABELS[axis_name]}-", axis=axis, side=0, disabled=disabled))
        rows.append(_RowSpec(f"{axis_name}_pos", f"{_AXIS_LABELS[axis_name]}+", axis=axis, side=1, disabled=disabled))
    rows.extend(
        (
            _RowSpec("save_profile", "Save Profile"),
            _RowSpec("export", "Export Resolved Profile"),
            _RowSpec("back", "Back"),
        )
    )
    return tuple(rows)


def _selectable_row_indexes(state: _TopologyLabState) -> tuple[int, ...]:
    return tuple(idx for idx, _row in enumerate(_rows_for_state(state)))


def _mode_value_text(state: _TopologyLabState) -> str:
    return topology_gameplay_mode_label(state.gameplay_mode)


def _preset_value_text(state: _TopologyLabState) -> str:
    profiles = _preset_profiles(state)
    index = _preset_index(state)
    return profiles[index].label


def _edge_value_text(state: _TopologyLabState, axis: int, side: int) -> str:
    value = state.profile.edge_rules[axis][side]
    return _EDGE_LABELS.get(value, str(value).title())


def _row_value_text(state: _TopologyLabState, row: _RowSpec) -> str:
    if row.key == "gameplay_mode":
        return _mode_value_text(state)
    if row.key == "dimension":
        return f"{state.dimension}D"
    if row.key == "preset":
        return _preset_value_text(state)
    if row.key == "topology_mode":
        return topology_mode_label(state.profile.topology_mode)
    if row.axis is not None and row.side is not None:
        return _edge_value_text(state, row.axis, row.side)
    return ""


def _mark_updated(state: _TopologyLabState) -> None:
    state.dirty = True
    _set_status(state, str(_LAB_STATUS_COPY["updated"]))


def _apply_profile(state: _TopologyLabState, profile: TopologyProfileState) -> None:
    state.profile = profile
    _mark_updated(state)


def _reset_to_mode_dimension(state: _TopologyLabState) -> None:
    _sync_profile(state)
    state.dirty = False
    _set_status(state, "")


def _cycle_gameplay_mode(state: _TopologyLabState, step: int) -> None:
    idx = TOPOLOGY_GAMEPLAY_MODE_OPTIONS.index(state.gameplay_mode)
    state.gameplay_mode = TOPOLOGY_GAMEPLAY_MODE_OPTIONS[(idx + step) % len(TOPOLOGY_GAMEPLAY_MODE_OPTIONS)]
    _sync_profile(state)
    _mark_updated(state)


def _cycle_dimension(state: _TopologyLabState, step: int) -> None:
    idx = _TOPOLOGY_DIMENSIONS.index(state.dimension)
    state.dimension = _TOPOLOGY_DIMENSIONS[(idx + step) % len(_TOPOLOGY_DIMENSIONS)]
    _sync_profile(state)
    _mark_updated(state)


def _cycle_preset(state: _TopologyLabState, step: int) -> None:
    profiles = _preset_profiles(state)
    idx = (_preset_index(state) + step) % len(profiles)
    profile = profile_state_from_preset(
        dimension=state.dimension,
        gravity_axis=1,
        gameplay_mode=state.gameplay_mode,
        preset_index=idx,
        topology_mode=state.profile.topology_mode,
    )
    _apply_profile(state, profile)


def _cycle_topology_mode(state: _TopologyLabState, step: int) -> None:
    options = tuple(topology_mode_from_index(idx) for idx in range(3))
    current = state.profile.topology_mode
    idx = options.index(current)
    next_mode = options[(idx + step) % len(options)]
    rules = default_edge_rules_for_mode(
        state.dimension,
        1,
        mode=next_mode,
        wrap_gravity_axis=(state.gameplay_mode == GAMEPLAY_MODE_EXPLORER),
    )
    profile = validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=next_mode,
        edge_rules=rules,
        preset_id=None,
    )
    _apply_profile(state, profile)


def _cycle_edge_rule(state: _TopologyLabState, row: _RowSpec, step: int) -> None:
    if row.disabled:
        _set_status(state, str(_LAB_STATUS_COPY["locked"]), is_error=True)
        return
    assert row.axis is not None and row.side is not None
    current = state.profile.edge_rules[row.axis][row.side]
    idx = EDGE_BEHAVIOR_OPTIONS.index(current)
    next_value = EDGE_BEHAVIOR_OPTIONS[(idx + step) % len(EDGE_BEHAVIOR_OPTIONS)]
    rules = [tuple(axis_rule) for axis_rule in state.profile.edge_rules]
    axis_rule = list(rules[row.axis])
    axis_rule[row.side] = next_value
    rules[row.axis] = tuple(axis_rule)
    try:
        profile = validate_topology_profile_state(
            gameplay_mode=state.gameplay_mode,
            dimension=state.dimension,
            gravity_axis=1,
            topology_mode=state.profile.topology_mode,
            edge_rules=tuple(rules),
            preset_id=None,
        )
    except ValueError as exc:
        _set_status(state, str(exc), is_error=True)
        return
    _apply_profile(state, profile)


def _save_profile(state: _TopologyLabState) -> tuple[bool, str]:
    ok, message = save_topology_profile(state.profile)
    if ok:
        state.dirty = False
        _set_status(
            state,
            str(_LAB_STATUS_COPY["saved"]).format(
                mode_label=topology_gameplay_mode_label(state.gameplay_mode),
                dimension=state.dimension,
            ),
        )
        return True, message
    _set_status(
        state,
        str(_LAB_STATUS_COPY["save_failed"]).format(message=message),
        is_error=True,
    )
    return False, message


def _run_export(state: _TopologyLabState) -> None:
    ok, message, _path = export_topology_profile_state(
        profile=state.profile,
        gravity_axis=1,
    )
    if ok:
        _set_status(state, str(_LAB_STATUS_COPY["export_ok"]).format(message=message))
        play_sfx("menu_confirm")
        return
    _set_status(
        state,
        str(_LAB_STATUS_COPY["export_error"]).format(message=message),
        is_error=True,
    )


def _adjust_active_row(state: _TopologyLabState, step: int) -> bool:
    row = _rows_for_state(state)[_selectable_row_indexes(state)[state.selected]]
    if row.key == "gameplay_mode":
        _cycle_gameplay_mode(state, step)
        return True
    if row.key == "dimension":
        _cycle_dimension(state, step)
        return True
    if row.key == "preset":
        _cycle_preset(state, step)
        return True
    if row.key == "topology_mode":
        _cycle_topology_mode(state, step)
        return True
    if row.axis is not None:
        _cycle_edge_rule(state, row, step)
        return True
    return False


def _handle_navigation_key(state: _TopologyLabState, nav_key: int, selectable: tuple[int, ...]) -> bool:
    if nav_key == pygame.K_UP:
        state.selected = (state.selected - 1) % len(selectable)
        play_sfx("menu_move")
        return True
    if nav_key == pygame.K_DOWN:
        state.selected = (state.selected + 1) % len(selectable)
        play_sfx("menu_move")
        return True
    if nav_key in (pygame.K_LEFT, pygame.K_RIGHT):
        step = -1 if nav_key == pygame.K_LEFT else 1
        if _adjust_active_row(state, step):
            play_sfx("menu_move")
        return True
    return False


def _handle_shortcut_key(state: _TopologyLabState, key: int) -> bool:
    if key == pygame.K_s:
        _save_profile(state)
        return True
    if key == pygame.K_e:
        _run_export(state)
        return True
    return False


def _handle_enter_key(state: _TopologyLabState, selectable: tuple[int, ...]) -> None:
    row = _rows_for_state(state)[selectable[state.selected]]
    if row.key == "save_profile":
        _save_profile(state)
        return
    if row.key == "export":
        _run_export(state)
        return
    if row.key == "back":
        state.running = False
        return
    if _adjust_active_row(state, 1):
        play_sfx("menu_move")


def _draw_menu(screen: pygame.Surface, fonts, state: _TopologyLabState) -> None:
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render(_LAB_TITLE, True, _TEXT_COLOR)
    subtitle_text = fit_text(fonts.hint_font, _LAB_SUBTITLE, width - 28)
    subtitle = fonts.hint_font.render(subtitle_text, True, _MUTED_COLOR)
    note_text = fit_text(fonts.hint_font, topology_profile_note(state.gameplay_mode), width - 28)
    note = fonts.hint_font.render(note_text, True, _HIGHLIGHT_COLOR)
    title_y = 42
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, title_y + title.get_height() + 6))
    screen.blit(note, ((width - note.get_width()) // 2, title_y + title.get_height() + subtitle.get_height() + 14))

    rows = _rows_for_state(state)
    selectable = _selectable_row_indexes(state)
    selected_row = selectable[state.selected]

    panel_w = min(820, max(420, width - 40))
    panel_h = min(height - 210, 80 + len(rows) * 38)
    panel_x = (width - panel_w) // 2
    panel_y = max(150, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 16
    for idx, row in enumerate(rows):
        selected = idx == selected_row
        color = _DISABLED_COLOR if row.disabled else (_HIGHLIGHT_COLOR if selected else _TEXT_COLOR)
        if selected:
            hi = pygame.Surface((panel_w - 28, fonts.menu_font.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 14, y - 4))
        label_text = row.label + (" (locked)" if row.disabled else "")
        label = fonts.menu_font.render(fit_text(fonts.menu_font, label_text, panel_w // 2), True, color)
        value = fonts.menu_font.render(fit_text(fonts.menu_font, _row_value_text(state, row), panel_w // 2), True, color)
        screen.blit(label, (panel_x + 22, y))
        screen.blit(value, (panel_x + panel_w - value.get_width() - 22, y))
        y += 38

    hint_y = panel_y + panel_h + 10
    for hint in _LAB_HINTS:
        hint_text = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_text, True, _MUTED_COLOR)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3
    if state.status:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 24)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 2))


def _dispatch_key(state: _TopologyLabState, key: int) -> None:
    nav_key = normalize_menu_navigation_key(key)
    selectable = _selectable_row_indexes(state)
    if key == pygame.K_q or nav_key == pygame.K_ESCAPE:
        state.running = False
        return
    if _handle_navigation_key(state, nav_key, selectable):
        return
    if _handle_shortcut_key(state, key):
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_enter_key(state, selectable)


def run_topology_lab_menu(
    screen: pygame.Surface,
    fonts,
    *,
    start_dimension: int,
) -> tuple[bool, str]:
    dimension = start_dimension if start_dimension in _TOPOLOGY_DIMENSIONS else 3
    state = _TopologyLabState(
        selected=0,
        gameplay_mode=GAMEPLAY_MODE_NORMAL,
        dimension=dimension,
        profile=load_topology_profile(GAMEPLAY_MODE_NORMAL, dimension),
    )
    clock = pygame.time.Clock()
    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                state.running = False
                break
            if event.type == pygame.KEYDOWN:
                _dispatch_key(state, event.key)
                if not state.running:
                    break
        _draw_menu(screen, fonts, state)
        pygame.display.flip()
    if state.dirty:
        ok, message = _save_profile(state)
        return ok, message
    if state.status:
        return (not state.status_error), state.status
    return True, "Topology Lab unchanged"
