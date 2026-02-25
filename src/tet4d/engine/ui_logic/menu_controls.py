from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import pygame

from ..keybindings import (
    active_key_profile,
    binding_actions_for_dimension,
    cycle_rebind_conflict_mode,
    create_auto_profile,
    cycle_key_profile,
    delete_key_profile,
    load_active_profile_bindings,
    normalize_rebind_conflict_mode,
    rebind_action_key,
    reset_active_profile_bindings,
    set_active_key_profile,
)
from ..menu_settings_state import (
    load_menu_settings,
    reset_menu_settings_to_defaults,
    save_menu_settings,
)
from .menu_keybinding_shortcuts import (
    apply_menu_binding_action,
    menu_binding_action_for_key,
)

FieldSpec = tuple[str, str, int, int]


@dataclass(frozen=True)
class RebindCapture:
    key: int


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
    NO_OP = auto()


_MENU_KEY_ACTIONS = {
    pygame.K_ESCAPE: MenuAction.QUIT,
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
    pygame.K_BACKSPACE: MenuAction.PROFILE_DELETE,
    pygame.K_b: MenuAction.REBIND_TOGGLE,
    pygame.K_TAB: MenuAction.REBIND_TARGET_NEXT,
    pygame.K_BACKQUOTE: MenuAction.REBIND_TARGET_PREV,
    pygame.K_c: MenuAction.REBIND_CONFLICT_NEXT,
    pygame.K_F6: MenuAction.RESET_BINDINGS,
    pygame.K_F7: MenuAction.RUN_DRY_RUN,
}


MenuInput = MenuAction | RebindCapture


def _set_bindings_status(state: Any, ok: bool, message: str) -> None:
    state.bindings_status = message
    state.bindings_status_error = not ok


def _ensure_rebind_state(state: Any, dimension: int) -> None:
    if not hasattr(state, "rebind_mode"):
        state.rebind_mode = False
    if not hasattr(state, "rebind_index"):
        state.rebind_index = 0
    if not hasattr(state, "rebind_targets") or not state.rebind_targets:
        targets: list[tuple[str, str]] = []
        for group_name, actions in binding_actions_for_dimension(dimension).items():
            for action_name in actions:
                targets.append((group_name, action_name))
        state.rebind_targets = targets
    if not hasattr(state, "active_profile"):
        state.active_profile = active_key_profile()
    if not hasattr(state, "rebind_conflict_mode"):
        state.rebind_conflict_mode = normalize_rebind_conflict_mode(None)


def _action_for_rebind_key(key: int) -> MenuInput:
    if key == pygame.K_ESCAPE:
        return MenuAction.REBIND_TOGGLE
    if key == pygame.K_TAB:
        return MenuAction.REBIND_TARGET_NEXT
    if key == pygame.K_BACKQUOTE:
        return MenuAction.REBIND_TARGET_PREV
    return RebindCapture(key)


def _action_for_menu_key(key: int) -> MenuAction | None:
    mapped = _MENU_KEY_ACTIONS.get(key)
    if mapped is not None:
        return mapped
    return menu_binding_action_for_key(
        key,
        MenuAction.LOAD_BINDINGS,
        MenuAction.SAVE_BINDINGS,
    )


def gather_menu_actions(
    state: Any | None = None, _dimension: int | None = None
) -> list[MenuInput]:
    actions: list[MenuInput] = []
    rebind_mode = bool(getattr(state, "rebind_mode", False))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
            continue
        if event.type != pygame.KEYDOWN:
            continue

        if rebind_mode:
            actions.append(_action_for_rebind_key(event.key))
            continue

        action = _action_for_menu_key(event.key)
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
    profile_name = str(getattr(state, "active_profile", active_key_profile()))
    ok, msg = delete_key_profile(profile_name)
    state.active_profile = active_key_profile()
    _set_bindings_status(state, ok, msg)


def _handle_settings_action(state: Any, dimension: int, action: MenuAction) -> None:
    if action == MenuAction.SAVE_SETTINGS:
        ok, msg = save_menu_settings(state, dimension)
    elif action == MenuAction.LOAD_SETTINGS:
        ok, msg = load_menu_settings(state, dimension)
    else:
        ok, msg = reset_menu_settings_to_defaults(state, dimension)
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


def _apply_single_menu_action(
    state: Any,
    action: MenuInput,
    *,
    fields: Sequence[FieldSpec],
    field_count: int,
    dimension: int,
    blocked: set[MenuAction],
) -> None:
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

    step = _SELECTION_ACTION_STEP.get(action)
    if step is not None:
        state.selected_index = (state.selected_index + step) % field_count
        return

    if action == MenuAction.RUN_DRY_RUN:
        state.run_dry_run = True
        return

    delta = _VALUE_ACTION_DELTA.get(action)
    if delta is not None:
        _handle_value_delta(state, fields, delta)
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
