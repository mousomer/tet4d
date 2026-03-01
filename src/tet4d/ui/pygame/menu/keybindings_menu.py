from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import pygame

import tet4d.engine.api as engine_api

BindingRow = Any
RenderedRow = Any
REBIND_CONFLICT_REPLACE = engine_api.keybindings_rebind_conflict_replace()
SECTION_MENU = engine_api.keybindings_menu_section_menu()
active_key_profile = engine_api.keybindings_active_key_profile
clone_key_profile = engine_api.keybindings_clone_key_profile
cycle_key_profile = engine_api.keybindings_cycle_key_profile
cycle_rebind_conflict_mode = engine_api.keybindings_cycle_rebind_conflict_mode
delete_key_profile = engine_api.keybindings_delete_key_profile
load_active_profile_bindings = engine_api.keybindings_load_active_profile_bindings
load_keybindings_file = engine_api.keybindings_load_keybindings_file
next_auto_profile_name = engine_api.keybindings_next_auto_profile_name
rebind_action_key = engine_api.keybindings_rebind_action_key
rename_key_profile = engine_api.keybindings_rename_key_profile
reset_active_profile_bindings = engine_api.keybindings_reset_active_profile_bindings
save_keybindings_file = engine_api.keybindings_save_keybindings_file
set_active_key_profile = engine_api.keybindings_set_active_key_profile
resolve_initial_scope = engine_api.keybindings_menu_resolve_initial_scope
rows_for_scope = engine_api.keybindings_menu_rows_for_scope
scope_dimensions = engine_api.keybindings_menu_scope_dimensions
scope_file_hint = engine_api.keybindings_menu_scope_file_hint
scope_label = engine_api.keybindings_menu_scope_label


_TEXT_MODE_CREATE = "create"
_TEXT_MODE_RENAME = "rename"
_TEXT_MODE_SAVE_AS = "save_as"
_PROFILE_NAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789_-")


def _sanitize_profile_name(raw: str) -> str:
    lowered = engine_api.sanitize_text_runtime(raw, max_length=128).strip().lower()
    filtered = "".join(ch for ch in lowered if ch in _PROFILE_NAME_CHARS)
    return filtered[:64]


@dataclass
class KeybindingsMenuState:
    scope: str = "all"
    section_mode: bool = True
    allow_scope_sections: bool = True
    selected_section: int = 0
    selected_binding: int = 0
    scroll_top: int = 0
    capture_mode: bool = False
    conflict_mode: str = REBIND_CONFLICT_REPLACE
    status: str = ""
    status_error: bool = False
    active_profile: str = ""
    pending_reset_confirm: bool = False
    text_mode: str = ""
    text_buffer: str = ""

    def __post_init__(self) -> None:
        self.active_profile = active_key_profile()


def _set_status(state: KeybindingsMenuState, ok: bool, message: str) -> None:
    state.status = message
    state.status_error = not ok


def _clear_reset_confirmation(state: KeybindingsMenuState) -> None:
    state.pending_reset_confirm = False


def _text_mode_label(mode: str) -> str:
    if mode == _TEXT_MODE_CREATE:
        return "Create profile name"
    if mode == _TEXT_MODE_RENAME:
        return "Rename active profile"
    return "Save profile as"


def _cycle_binding(
    state: KeybindingsMenuState, binding_rows: list[BindingRow], step: int
) -> None:
    if not binding_rows:
        return
    state.selected_binding = (state.selected_binding + step) % len(binding_rows)


def _cycle_profile(state: KeybindingsMenuState, step: int) -> None:
    ok, msg, profile = cycle_key_profile(step)
    state.active_profile = profile
    _set_status(state, ok, msg)


def _activate_profile(state: KeybindingsMenuState, profile: str) -> tuple[bool, str]:
    ok, msg = set_active_key_profile(profile)
    if not ok:
        return False, msg
    ok, msg = load_active_profile_bindings()
    if not ok:
        return False, msg
    state.active_profile = active_key_profile()
    return True, f"Active key profile: {state.active_profile}"


def _delete_profile(state: KeybindingsMenuState) -> None:
    ok, msg = delete_key_profile(state.active_profile)
    state.active_profile = active_key_profile()
    _set_status(state, ok, msg)


def _start_text_mode(state: KeybindingsMenuState, mode: str) -> None:
    state.text_mode = mode
    if mode == _TEXT_MODE_RENAME:
        state.text_buffer = state.active_profile
    else:
        state.text_buffer = next_auto_profile_name("custom")
    pygame.key.start_text_input()
    _set_status(state, True, f"{_text_mode_label(mode)}: type name and press Enter")


def _stop_text_mode(state: KeybindingsMenuState) -> None:
    state.text_mode = ""
    state.text_buffer = ""
    pygame.key.stop_text_input()


def _commit_text_mode(state: KeybindingsMenuState) -> None:
    profile_name = _sanitize_profile_name(state.text_buffer)
    mode = state.text_mode
    _stop_text_mode(state)

    if not profile_name:
        _set_status(state, False, "Profile name cannot be empty")
        return

    if mode == _TEXT_MODE_RENAME:
        ok, msg = rename_key_profile(state.active_profile, profile_name)
        state.active_profile = active_key_profile()
        _set_status(state, ok, msg)
        return

    ok, msg = clone_key_profile(profile_name, source_profile=state.active_profile)
    if not ok:
        _set_status(state, ok, msg)
        return
    ok, activate_msg = _activate_profile(state, profile_name)
    if ok:
        _set_status(state, True, f"{msg}; {activate_msg}")
    else:
        _set_status(state, False, activate_msg)


def _cancel_text_mode(state: KeybindingsMenuState) -> None:
    _stop_text_mode(state)
    _set_status(state, True, "Profile input cancelled")


def _handle_text_input_event(state: KeybindingsMenuState, text: str) -> None:
    if not state.text_mode:
        return
    sanitized = engine_api.sanitize_text_runtime(text, max_length=16).lower()
    appended = "".join(ch for ch in sanitized if ch in _PROFILE_NAME_CHARS)
    if not appended:
        return
    state.text_buffer = (state.text_buffer + appended)[:64]


def _run_scope_operation(
    state: KeybindingsMenuState,
    operation: Callable[[int], tuple[bool, str]],
) -> tuple[bool, str]:
    results: list[str] = []
    ok_all = True
    for dimension in scope_dimensions(state.scope):
        ok, msg = operation(dimension)
        ok_all = ok_all and ok
        results.append(f"{dimension}D: {msg}")
    return ok_all, " | ".join(results)


def _active_binding(
    binding_rows: list[BindingRow], state: KeybindingsMenuState
) -> BindingRow | None:
    if not binding_rows:
        return None
    safe_index = max(0, min(len(binding_rows) - 1, state.selected_binding))
    return binding_rows[safe_index]


def _handle_capture_input(
    state: KeybindingsMenuState,
    key: int,
    binding_rows: list[BindingRow],
) -> bool:
    if key == pygame.K_ESCAPE:
        state.capture_mode = False
        _set_status(state, True, "Capture cancelled")
        return False

    selected = _active_binding(binding_rows, state)
    if selected is None:
        state.capture_mode = False
        return False

    if state.scope == "general" and selected.group == "system":
        results: list[str] = []
        ok = True
        for dimension in scope_dimensions(state.scope):
            dim_ok, dim_msg = rebind_action_key(
                dimension,
                selected.group,
                selected.action,
                key,
                conflict_mode=state.conflict_mode,
            )
            ok = ok and dim_ok
            results.append(f"{dimension}D: {dim_msg}")
        msg = " | ".join(results)
    else:
        ok, msg = rebind_action_key(
            selected.dimension,
            selected.group,
            selected.action,
            key,
            conflict_mode=state.conflict_mode,
        )
    _set_status(state, ok, msg)
    state.capture_mode = False
    return False


def _action_exit(_state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    return True


def _action_row_up(state: KeybindingsMenuState, rows: list[BindingRow]) -> bool:
    _cycle_binding(state, rows, -1)
    return False


def _action_row_down(state: KeybindingsMenuState, rows: list[BindingRow]) -> bool:
    _cycle_binding(state, rows, 1)
    return False


def _action_capture_start(state: KeybindingsMenuState, rows: list[BindingRow]) -> bool:
    if rows:
        state.capture_mode = True
    return False


def _action_conflict_cycle(
    state: KeybindingsMenuState, _rows: list[BindingRow]
) -> bool:
    state.conflict_mode = cycle_rebind_conflict_mode(state.conflict_mode, 1)
    _set_status(state, True, f"Conflict mode: {state.conflict_mode}")
    return False


def _action_load_file(state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    ok, msg = _run_scope_operation(state, load_keybindings_file)
    _set_status(state, ok, msg)
    return False


def _action_save_file(state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    ok, msg = _run_scope_operation(state, save_keybindings_file)
    _set_status(state, ok, msg)
    return False


def _action_reset_bindings(
    state: KeybindingsMenuState, _rows: list[BindingRow]
) -> bool:
    if not state.pending_reset_confirm:
        state.pending_reset_confirm = True
        _set_status(state, True, "Press F6 again to confirm profile reset")
        return False
    state.pending_reset_confirm = False
    ok, msg = _run_scope_operation(state, reset_active_profile_bindings)
    _set_status(state, ok, msg)
    return False


def _action_profile_prev(state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    _cycle_profile(state, -1)
    return False


def _action_profile_next(state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    _cycle_profile(state, 1)
    return False


def _action_profile_new(state: KeybindingsMenuState, _rows: list[BindingRow]) -> bool:
    _start_text_mode(state, _TEXT_MODE_CREATE)
    return False


def _action_profile_rename(
    state: KeybindingsMenuState, _rows: list[BindingRow]
) -> bool:
    _start_text_mode(state, _TEXT_MODE_RENAME)
    return False


def _action_profile_save_as(
    state: KeybindingsMenuState, _rows: list[BindingRow]
) -> bool:
    _start_text_mode(state, _TEXT_MODE_SAVE_AS)
    return False


def _action_profile_delete(
    state: KeybindingsMenuState, _rows: list[BindingRow]
) -> bool:
    _delete_profile(state)
    return False


_MENU_KEY_HANDLERS = {
    pygame.K_ESCAPE: _action_exit,
    pygame.K_UP: _action_row_up,
    pygame.K_DOWN: _action_row_down,
    pygame.K_RETURN: _action_capture_start,
    pygame.K_KP_ENTER: _action_capture_start,
    pygame.K_c: _action_conflict_cycle,
    pygame.K_l: _action_load_file,
    pygame.K_s: _action_save_file,
    pygame.K_F6: _action_reset_bindings,
    pygame.K_F2: _action_profile_rename,
    pygame.K_F3: _action_profile_save_as,
    pygame.K_LEFTBRACKET: _action_profile_prev,
    pygame.K_RIGHTBRACKET: _action_profile_next,
    pygame.K_n: _action_profile_new,
    pygame.K_BACKSPACE: _action_profile_delete,
}


def _run_menu_action(
    state: KeybindingsMenuState, key: int, rows: list[BindingRow]
) -> bool:
    if state.section_mode:
        return _run_section_mode_action(state, key)
    return _run_binding_mode_action(state, key, rows)


def _handle_text_mode_key(state: KeybindingsMenuState, key: int) -> None:
    if key == pygame.K_ESCAPE:
        _cancel_text_mode(state)
    elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _commit_text_mode(state)
    elif key == pygame.K_BACKSPACE:
        state.text_buffer = state.text_buffer[:-1]


def _run_section_mode_action(state: KeybindingsMenuState, key: int) -> bool:
    if state.text_mode:
        _handle_text_mode_key(state, key)
        return False
    return _handle_section_key(state, key)


def _run_binding_mode_action(
    state: KeybindingsMenuState, key: int, rows: list[BindingRow]
) -> bool:
    if state.capture_mode:
        _clear_reset_confirmation(state)
        return _handle_capture_input(state, key, rows)

    if state.text_mode:
        _handle_text_mode_key(state, key)
        return False

    if key == pygame.K_ESCAPE and state.allow_scope_sections:
        state.section_mode = True
        state.capture_mode = False
        _set_status(state, True, "Returned to keybinding sections")
        return False
    if key == pygame.K_TAB and state.allow_scope_sections:
        state.section_mode = True
        state.capture_mode = False
        _set_status(state, True, "Opened keybinding sections")
        return False

    if key != pygame.K_F6:
        _clear_reset_confirmation(state)

    handler = _MENU_KEY_HANDLERS.get(key)
    if handler is None:
        return False
    return handler(state, rows)


def _draw_section_menu(
    surface: pygame.Surface, fonts, state: KeybindingsMenuState
) -> None:
    from tet4d.ui.pygame.menu.keybindings_menu_view import draw_section_menu

    draw_section_menu(
        surface,
        fonts,
        state,
        section_menu=SECTION_MENU,
        scope_label_fn=scope_label,
        text_mode_label_fn=_text_mode_label,
    )


def _handle_section_key(state: KeybindingsMenuState, key: int) -> bool:
    if key == pygame.K_ESCAPE:
        return True
    if key == pygame.K_UP:
        state.selected_section = (state.selected_section - 1) % len(SECTION_MENU)
        return False
    if key == pygame.K_DOWN:
        state.selected_section = (state.selected_section + 1) % len(SECTION_MENU)
        return False
    if key in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET):
        step = -1 if key == pygame.K_LEFTBRACKET else 1
        _cycle_profile(state, step)
        return False
    if key == pygame.K_n:
        _start_text_mode(state, _TEXT_MODE_CREATE)
        return False
    if key == pygame.K_F2:
        _start_text_mode(state, _TEXT_MODE_RENAME)
        return False
    if key == pygame.K_F3:
        _start_text_mode(state, _TEXT_MODE_SAVE_AS)
        return False
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        scope = SECTION_MENU[state.selected_section][0]
        state.scope = scope
        state.section_mode = False
        state.selected_binding = 0
        state.scroll_top = 0
        state.capture_mode = False
        _set_status(state, True, f"Opened {scope_label(scope)} bindings")
    return False


def _draw_menu(
    surface: pygame.Surface,
    fonts,
    state: KeybindingsMenuState,
    rendered_rows: list[RenderedRow],
    binding_rows: list[BindingRow],
) -> None:
    from tet4d.ui.pygame.menu.keybindings_menu_view import draw_binding_menu

    draw_binding_menu(
        surface,
        fonts,
        state,
        rendered_rows=rendered_rows,
        binding_rows=binding_rows,
        scope_label_fn=scope_label,
        scope_file_hint_fn=scope_file_hint,
        text_mode_label_fn=_text_mode_label,
    )


def _build_menu_state(initial_scope: str) -> KeybindingsMenuState:
    allow_scope_sections = initial_scope in {"all", "general"}
    selected_section = 0
    for idx, (section_scope, _title, _description) in enumerate(SECTION_MENU):
        if section_scope == initial_scope:
            selected_section = idx
            break
    return KeybindingsMenuState(
        scope=initial_scope,
        section_mode=allow_scope_sections,
        allow_scope_sections=allow_scope_sections,
        selected_section=selected_section,
    )


def _sync_selection(
    state: KeybindingsMenuState, binding_rows: list[BindingRow]
) -> None:
    if binding_rows:
        state.selected_binding = max(
            0, min(len(binding_rows) - 1, state.selected_binding)
        )
    else:
        state.selected_binding = 0


def _process_menu_events(
    state: KeybindingsMenuState, binding_rows: list[BindingRow]
) -> bool:
    from tet4d.ui.pygame.menu.keybindings_menu_input import process_menu_events

    return process_menu_events(
        state,
        binding_rows,
        run_menu_action=_run_menu_action,
        handle_text_input=_handle_text_input_event,
    )


def run_keybindings_menu(
    screen: pygame.Surface,
    fonts,
    dimension: int = 2,
    *,
    scope: str | None = None,
) -> None:
    initial_scope = resolve_initial_scope(dimension, scope)
    state = _build_menu_state(initial_scope)
    clock = pygame.time.Clock()
    running = True
    while running:
        _dt = clock.tick(60)
        rendered_rows, binding_rows = rows_for_scope(state.scope)
        _sync_selection(state, binding_rows)
        if _process_menu_events(state, binding_rows):
            break

        if state.section_mode:
            _draw_section_menu(screen, fonts, state)
        else:
            _draw_menu(screen, fonts, state, rendered_rows, binding_rows)
        pygame.display.flip()

    pygame.key.stop_text_input()
