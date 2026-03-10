from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import pygame

from tet4d.engine.runtime.menu_settings_state import (
    load_menu_settings,
    reset_menu_settings_to_defaults,
    save_menu_settings,
)
from tet4d.engine.runtime.settings_schema import sanitize_text
from tet4d.ui.pygame.keybindings import (
    active_key_profile,
    binding_actions_for_dimension,
    create_auto_profile,
    cycle_key_profile,
    cycle_rebind_conflict_mode,
    delete_key_profile,
    load_active_profile_bindings,
    normalize_rebind_conflict_mode,
    rebind_action_key,
    reset_active_profile_bindings,
    set_active_key_profile,
)
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key

from .menu_keybinding_shortcuts import (
    apply_menu_binding_action,
    menu_binding_action_for_key,
)
from .numeric_text_input import append_numeric_text, parse_numeric_text

FieldSpec = tuple[str, str, int, int]


@dataclass(frozen=True)
class RebindCapture:
    key: int


@dataclass(frozen=True)
class NumericTextAppend:
    text: str


class MenuAction(Enum):
    QUIT = auto()
    START_GAME = auto()
    SELECT_UP = auto()
    SELECT_DOWN = auto()
    VALUE_LEFT = auto()
    VALUE_RIGHT = auto()
    LOAD_BINDINGS = auto()
    SAVE_BINDINGS = auto()
    LOAD_SETTINGS = auto()
    SAVE_SETTINGS = auto()
    RESET_SETTINGS = auto()
    PROFILE_PREV = auto()
    PROFILE_NEXT = auto()
    PROFILE_NEW = auto()
    PROFILE_DELETE = auto()
    REBIND_TOGGLE = auto()
    REBIND_TARGET_NEXT = auto()
    REBIND_TARGET_PREV = auto()
    REBIND_CONFLICT_NEXT = auto()
    RESET_BINDINGS = auto()
    RUN_DRY_RUN = auto()
    NUMERIC_TEXT_BACKSPACE = auto()
    NUMERIC_TEXT_COMMIT = auto()
    NUMERIC_TEXT_CANCEL = auto()
    NO_OP = auto()


_MENU_KEY_ACTIONS = {
    pygame.K_q: MenuAction.QUIT,
    pygame.K_ESCAPE: MenuAction.QUIT,
    pygame.K_BACKSPACE: MenuAction.QUIT,
    pygame.K_RETURN: MenuAction.START_GAME,
    pygame.K_KP_ENTER: MenuAction.START_GAME,
    pygame.K_UP: MenuAction.SELECT_UP,
    pygame.K_DOWN: MenuAction.SELECT_DOWN,
    pygame.K_LEFT: MenuAction.VALUE_LEFT,
    pygame.K_RIGHT: MenuAction.VALUE_RIGHT,
    pygame.K_F5: MenuAction.SAVE_SETTINGS,
    pygame.K_F9: MenuAction.LOAD_SETTINGS,
    pygame.K_F8: MenuAction.RESET_SETTINGS,
    pygame.K_LEFTBRACKET: MenuAction.PROFILE_PREV,
    pygame.K_RIGHTBRACKET: MenuAction.PROFILE_NEXT,
    pygame.K_n: MenuAction.PROFILE_NEW,
    pygame.K_DELETE: MenuAction.PROFILE_DELETE,
    pygame.K_b: MenuAction.REBIND_TOGGLE,
    pygame.K_TAB: MenuAction.REBIND_TARGET_NEXT,
    pygame.K_BACKQUOTE: MenuAction.REBIND_TARGET_PREV,
    pygame.K_c: MenuAction.REBIND_CONFLICT_NEXT,
    pygame.K_F6: MenuAction.RESET_BINDINGS,
    pygame.K_F7: MenuAction.RUN_DRY_RUN,
}


MenuInput = MenuAction | NumericTextAppend | RebindCapture

_NUMERIC_TEXT_MAX_LENGTH = 12


def _sanitize_numeric_text(value: str, max_length: int) -> str:
    return sanitize_text(value, max_length=max_length)


def _set_bindings_status(state: Any, ok: bool, message: str) -> None:
    state.bindings_status = message
    state.bindings_status_error = not ok


def _numeric_text_mode_enabled(state: Any | None) -> bool:
    return bool(getattr(state, "numeric_text_mode", False))


def _set_numeric_text_status(state: Any) -> None:
    state.bindings_status = (
        f"Edit {state.numeric_text_label}: {state.numeric_text_buffer}_ "
        "(Enter apply, Esc cancel)"
    )
    state.bindings_status_error = False


def _stop_numeric_text_mode(state: Any, *, clear_buffer: bool = True) -> None:
    if _numeric_text_mode_enabled(state):
        pygame.key.stop_text_input()
    state.numeric_text_mode = False
    state.numeric_text_attr_name = ""
    state.numeric_text_label = ""
    state.numeric_text_replace_on_type = False
    if clear_buffer:
        state.numeric_text_buffer = ""


def _start_numeric_text_mode(
    state: Any,
    fields: Sequence[FieldSpec],
    *,
    incoming_text: str = "",
) -> None:
    label, attr_name, _min_val, _max_val = fields[state.selected_index]
    current_value = int(getattr(state.settings, attr_name))
    _stop_numeric_text_mode(state)
    state.numeric_text_mode = True
    state.numeric_text_attr_name = attr_name
    state.numeric_text_label = label
    state.numeric_text_buffer = str(current_value)
    state.numeric_text_replace_on_type = True
    pygame.key.start_text_input()
    if incoming_text:
        state.numeric_text_buffer, state.numeric_text_replace_on_type = append_numeric_text(
            current_buffer=state.numeric_text_buffer,
            incoming_text=incoming_text,
            replace_on_type=state.numeric_text_replace_on_type,
            max_length=_NUMERIC_TEXT_MAX_LENGTH,
            sanitize_text=_sanitize_numeric_text,
        )
    _set_numeric_text_status(state)


def _matching_field(state: Any, fields: Sequence[FieldSpec]) -> FieldSpec | None:
    attr_name = str(getattr(state, "numeric_text_attr_name", ""))
    for field in fields:
        if field[1] == attr_name:
            return field
    return None


def _apply_numeric_text_value(state: Any, fields: Sequence[FieldSpec]) -> bool:
    field = _matching_field(state, fields)
    if field is None:
        _stop_numeric_text_mode(state)
        return False
    label, attr_name, min_val, max_val = field
    parsed = parse_numeric_text(
        str(getattr(state, "numeric_text_buffer", "")),
        max_length=_NUMERIC_TEXT_MAX_LENGTH,
        sanitize_text=_sanitize_numeric_text,
    )
    if parsed is None:
        state.bindings_status = f"Invalid value for {label}"
        state.bindings_status_error = True
        return False
    setattr(state.settings, attr_name, max(min_val, min(max_val, parsed)))
    _stop_numeric_text_mode(state)
    state.bindings_status = f"Updated {label}"
    state.bindings_status_error = False
    return True


def _handle_numeric_text_input(
    state: Any,
    action: MenuInput,
    fields: Sequence[FieldSpec],
) -> bool:
    if isinstance(action, NumericTextAppend):
        if not _numeric_text_mode_enabled(state):
            _start_numeric_text_mode(state, fields, incoming_text=action.text)
            return True
        state.numeric_text_buffer, state.numeric_text_replace_on_type = append_numeric_text(
            current_buffer=str(getattr(state, "numeric_text_buffer", "")),
            incoming_text=action.text,
            replace_on_type=bool(getattr(state, "numeric_text_replace_on_type", False)),
            max_length=_NUMERIC_TEXT_MAX_LENGTH,
            sanitize_text=_sanitize_numeric_text,
        )
        _set_numeric_text_status(state)
        return True
    if not _numeric_text_mode_enabled(state):
        return False
    if action == MenuAction.NUMERIC_TEXT_BACKSPACE:
        state.numeric_text_buffer = str(getattr(state, "numeric_text_buffer", ""))[:-1]
        state.numeric_text_replace_on_type = False
        _set_numeric_text_status(state)
        return True
    if action == MenuAction.NUMERIC_TEXT_COMMIT:
        _apply_numeric_text_value(state, fields)
        return True
    if action == MenuAction.NUMERIC_TEXT_CANCEL:
        _stop_numeric_text_mode(state)
        state.bindings_status = "Numeric entry canceled"
        state.bindings_status_error = False
        return True
    return False


def _ensure_state_attr(state: Any, attr_name: str, default: Any) -> None:
    if not hasattr(state, attr_name):
        setattr(state, attr_name, default)


def _build_rebind_targets(dimension: int) -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for group_name, actions in binding_actions_for_dimension(dimension).items():
        for action_name in actions:
            targets.append((group_name, action_name))
    return targets


def _ensure_numeric_text_state(state: Any) -> None:
    _ensure_state_attr(state, "numeric_text_mode", False)
    _ensure_state_attr(state, "numeric_text_attr_name", "")
    _ensure_state_attr(state, "numeric_text_label", "")
    _ensure_state_attr(state, "numeric_text_buffer", "")
    _ensure_state_attr(state, "numeric_text_replace_on_type", False)


def _ensure_rebind_state(state: Any, dimension: int) -> None:
    _ensure_state_attr(state, "rebind_mode", False)
    _ensure_state_attr(state, "rebind_index", 0)
    if not hasattr(state, "rebind_targets") or not state.rebind_targets:
        state.rebind_targets = _build_rebind_targets(dimension)
    _ensure_state_attr(state, "active_profile", active_key_profile())
    if not hasattr(state, "rebind_conflict_mode"):
        state.rebind_conflict_mode = normalize_rebind_conflict_mode(None)
    _ensure_numeric_text_state(state)


def _action_for_rebind_key(key: int) -> MenuInput:
    if key == pygame.K_ESCAPE:
        return MenuAction.REBIND_TOGGLE
    if key == pygame.K_TAB:
        return MenuAction.REBIND_TARGET_NEXT
    if key == pygame.K_BACKQUOTE:
        return MenuAction.REBIND_TARGET_PREV
    return RebindCapture(key)


def _action_for_menu_key(key: int) -> MenuAction | None:
    nav_key = normalize_menu_navigation_key(key)
    mapped = _MENU_KEY_ACTIONS.get(nav_key)
    if mapped is not None:
        return mapped
    mapped = _MENU_KEY_ACTIONS.get(key)
    if mapped is not None:
        return mapped
    return menu_binding_action_for_key(
        key,
        MenuAction.LOAD_BINDINGS,
        MenuAction.SAVE_BINDINGS,
    )


def _decode_numeric_mode_key(key: int) -> MenuAction | None:
    if key == pygame.K_ESCAPE:
        return MenuAction.NUMERIC_TEXT_CANCEL
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return MenuAction.NUMERIC_TEXT_COMMIT
    if key == pygame.K_BACKSPACE:
        return MenuAction.NUMERIC_TEXT_BACKSPACE
    return None


def _decode_keydown_action(
    event: pygame.event.Event,
    *,
    rebind_mode: bool,
    numeric_mode: bool,
) -> MenuInput | None:
    if rebind_mode:
        return _action_for_rebind_key(event.key)
    if numeric_mode:
        return _decode_numeric_mode_key(event.key)
    if event.unicode and event.unicode.isdigit():
        return NumericTextAppend(event.unicode)
    return _action_for_menu_key(event.key)


def gather_menu_actions(
    state: Any | None = None, _dimension: int | None = None
) -> list[MenuInput]:
    actions: list[MenuInput] = []
    rebind_mode = bool(getattr(state, "rebind_mode", False))
    numeric_mode = _numeric_text_mode_enabled(state)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
            continue
        if event.type == pygame.TEXTINPUT:
            if numeric_mode:
                actions.append(NumericTextAppend(event.text))
            continue
        if event.type != pygame.KEYDOWN:
            continue

        action = _decode_keydown_action(
            event,
            rebind_mode=rebind_mode,
            numeric_mode=numeric_mode,
        )
        if action is not None:
            actions.append(action)

    if not actions:
        actions.append(MenuAction.NO_OP)
    return actions


def _current_rebind_target(state: Any) -> tuple[str, str] | None:
    if not state.rebind_targets:
        return None
    return state.rebind_targets[state.rebind_index % len(state.rebind_targets)]


def _set_rebind_target_status(state: Any, prefix: str) -> None:
    target = _current_rebind_target(state)
    if target is None:
        return
    group, action_name = target
    state.bindings_status = f"{prefix}{group}.{action_name}"
    state.bindings_status_error = False


def _handle_rebind_capture(state: Any, dimension: int, capture: RebindCapture) -> None:
    target = _current_rebind_target(state)
    if target is None:
        return
    group, action_name = target
    ok, msg = rebind_action_key(
        dimension,
        group,
        action_name,
        capture.key,
        conflict_mode=state.rebind_conflict_mode,
    )
    if ok and state.rebind_targets:
        state.rebind_index = (state.rebind_index + 1) % len(state.rebind_targets)
    _set_bindings_status(state, ok, msg)


def _handle_rebind_toggle(state: Any) -> None:
    state.rebind_mode = not state.rebind_mode
    if state.rebind_mode:
        target = _current_rebind_target(state)
        if target is None:
            state.bindings_status = "Rebind mode: no actions available"
            state.bindings_status_error = True
            return
        group, action_name = target
        state.bindings_status = (
            f"Rebind mode: press key for {group}.{action_name} "
            f"(mode={state.rebind_conflict_mode}, Esc to exit)"
        )
    else:
        state.bindings_status = "Rebind mode disabled"
    state.bindings_status_error = False


def _shift_rebind_target(state: Any, step: int) -> None:
    if not state.rebind_targets:
        return
    state.rebind_index = (state.rebind_index + step) % len(state.rebind_targets)
    if state.rebind_mode:
        _set_rebind_target_status(state, "Rebind target: ")


def _handle_reset_bindings(state: Any, dimension: int) -> None:
    ok, msg = reset_active_profile_bindings(dimension)
    _set_bindings_status(state, ok, msg)


def _handle_profile_cycle(state: Any, step: int) -> None:
    ok, msg, profile = cycle_key_profile(step)
    state.active_profile = profile
    _set_bindings_status(state, ok, msg)


def _handle_profile_create(state: Any) -> None:
    ok, msg, profile = create_auto_profile()
    if ok and profile is not None:
        set_ok, set_msg = set_active_key_profile(profile)
        if not set_ok:
            ok = False
            msg = set_msg
        else:
            load_ok, load_msg = load_active_profile_bindings()
            if not load_ok:
                ok = False
                msg = load_msg
            else:
                state.active_profile = profile
    _set_bindings_status(state, ok, msg)


def _handle_profile_delete(state: Any) -> None:
    profile_name = str(
        getattr(state, "active_profile", active_key_profile())
    )
    ok, msg = delete_key_profile(profile_name)
    state.active_profile = active_key_profile()
    _set_bindings_status(state, ok, msg)


def _sync_runtime_profile_from_state(state: Any) -> tuple[bool, str]:
    profile_name = str(getattr(state, "active_profile", active_key_profile()))
    ok, msg = set_active_key_profile(profile_name)
    if not ok:
        return False, msg
    ok, msg = load_active_profile_bindings()
    if not ok:
        return False, msg
    state.active_profile = active_key_profile()
    return True, state.active_profile


def _handle_settings_action(state: Any, dimension: int, action: MenuAction) -> None:
    if action == MenuAction.SAVE_SETTINGS:
        ok, msg = save_menu_settings(state, dimension)
    elif action == MenuAction.LOAD_SETTINGS:
        ok, msg = load_menu_settings(state, dimension)
        if ok:
            ok, msg = _sync_runtime_profile_from_state(state)
    else:
        ok, msg = reset_menu_settings_to_defaults(state, dimension)
        if ok:
            ok, msg = _sync_runtime_profile_from_state(state)
    _set_bindings_status(state, ok, msg)


def _handle_save_settings(state: Any, dimension: int) -> None:
    _handle_settings_action(state, dimension, MenuAction.SAVE_SETTINGS)


def _handle_load_settings(state: Any, dimension: int) -> None:
    _handle_settings_action(state, dimension, MenuAction.LOAD_SETTINGS)


def _handle_reset_settings(state: Any, dimension: int) -> None:
    _handle_settings_action(state, dimension, MenuAction.RESET_SETTINGS)


def _handle_profile_next(state: Any, _dimension: int) -> None:
    _handle_profile_cycle(state, 1)


def _handle_profile_prev(state: Any, _dimension: int) -> None:
    _handle_profile_cycle(state, -1)


def _handle_profile_new(state: Any, _dimension: int) -> None:
    _handle_profile_create(state)


def _handle_profile_remove(state: Any, _dimension: int) -> None:
    _handle_profile_delete(state)


def _handle_value_delta(state: Any, fields: Sequence[FieldSpec], delta: int) -> None:
    _, attr_name, min_val, max_val = fields[state.selected_index]
    current = getattr(state.settings, attr_name)
    current = max(min_val, min(max_val, current + delta))
    setattr(state.settings, attr_name, current)


def _apply_state_only_action(state: Any, action: MenuAction) -> bool:
    if action == MenuAction.NO_OP:
        return True
    if action == MenuAction.QUIT:
        state.running = False
        return True
    if action == MenuAction.START_GAME:
        state.start_game = True
        return True
    if action == MenuAction.REBIND_TOGGLE:
        _handle_rebind_toggle(state)
        return True
    if action == MenuAction.REBIND_TARGET_NEXT:
        _shift_rebind_target(state, 1)
        return True
    if action == MenuAction.REBIND_TARGET_PREV:
        _shift_rebind_target(state, -1)
        return True
    if action == MenuAction.REBIND_CONFLICT_NEXT:
        state.rebind_conflict_mode = cycle_rebind_conflict_mode(
            state.rebind_conflict_mode, 1
        )
        state.bindings_status = f"Rebind conflict mode: {state.rebind_conflict_mode}"
        state.bindings_status_error = False
        return True
    return False


_SIMPLE_ACTION_HANDLERS = {
    MenuAction.RESET_BINDINGS: _handle_reset_bindings,
    MenuAction.SAVE_SETTINGS: _handle_save_settings,
    MenuAction.LOAD_SETTINGS: _handle_load_settings,
    MenuAction.RESET_SETTINGS: _handle_reset_settings,
    MenuAction.PROFILE_NEXT: _handle_profile_next,
    MenuAction.PROFILE_PREV: _handle_profile_prev,
    MenuAction.PROFILE_NEW: _handle_profile_new,
    MenuAction.PROFILE_DELETE: _handle_profile_remove,
}

_SELECTION_ACTION_STEP = {
    MenuAction.SELECT_UP: -1,
    MenuAction.SELECT_DOWN: 1,
}

_VALUE_ACTION_DELTA = {
    MenuAction.VALUE_LEFT: -1,
    MenuAction.VALUE_RIGHT: 1,
}


def _apply_selection_or_value_action(
    state: Any,
    action: MenuAction,
    *,
    field_count: int,
    fields: Sequence[FieldSpec],
) -> bool:
    step = _SELECTION_ACTION_STEP.get(action)
    if step is not None:
        if _numeric_text_mode_enabled(state):
            _stop_numeric_text_mode(state)
        state.selected_index = (state.selected_index + step) % field_count
        return True

    delta = _VALUE_ACTION_DELTA.get(action)
    if delta is None:
        return False
    _handle_value_delta(state, fields, delta)
    return True


def _apply_single_menu_action(
    state: Any,
    action: MenuInput,
    *,
    fields: Sequence[FieldSpec],
    field_count: int,
    dimension: int,
    blocked: set[MenuAction],
) -> None:
    if _handle_numeric_text_input(state, action, fields):
        return

    if isinstance(action, RebindCapture):
        if MenuAction.REBIND_TOGGLE in blocked:
            return
        _handle_rebind_capture(state, dimension, action)
        return

    if action in blocked:
        return
    if _apply_state_only_action(state, action):
        return

    simple_handler = _SIMPLE_ACTION_HANDLERS.get(action)
    if simple_handler is not None:
        simple_handler(state, dimension)
        return

    if action == MenuAction.RUN_DRY_RUN:
        state.run_dry_run = True
        return

    if _apply_selection_or_value_action(
        state,
        action,
        field_count=field_count,
        fields=fields,
    ):
        return

    apply_menu_binding_action(
        action,
        MenuAction.LOAD_BINDINGS,
        MenuAction.SAVE_BINDINGS,
        dimension,
        state,
    )


def apply_menu_actions(
    state: Any,
    actions: Sequence[MenuInput],
    fields: Sequence[FieldSpec],
    dimension: int,
    blocked_actions: set[MenuAction] | None = None,
) -> None:
    if not fields:
        return
    _ensure_rebind_state(state, dimension)
    state.run_dry_run = False
    blocked = blocked_actions or set()
    field_count = len(fields)
    for action in actions:
        _apply_single_menu_action(
            state,
            action,
            fields=fields,
            field_count=field_count,
            dimension=dimension,
            blocked=blocked,
        )
