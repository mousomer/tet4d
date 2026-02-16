from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import pygame

from .keybindings import (
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
from .menu_settings_state import (
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
}


MenuInput = MenuAction | RebindCapture


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


def gather_menu_actions(state: Any | None = None, dimension: int | None = None) -> list[MenuInput]:
    actions: list[MenuInput] = []
    rebind_mode = bool(getattr(state, "rebind_mode", False))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
            continue
        if event.type != pygame.KEYDOWN:
            continue

        if rebind_mode:
            if event.key == pygame.K_ESCAPE:
                actions.append(MenuAction.REBIND_TOGGLE)
                continue
            if event.key == pygame.K_TAB:
                actions.append(MenuAction.REBIND_TARGET_NEXT)
                continue
            if event.key == pygame.K_BACKQUOTE:
                actions.append(MenuAction.REBIND_TARGET_PREV)
                continue
            actions.append(RebindCapture(event.key))
            continue

        mapped = _MENU_KEY_ACTIONS.get(event.key)
        if mapped is not None:
            actions.append(mapped)
            continue

        binding_action = menu_binding_action_for_key(
            event.key,
            MenuAction.LOAD_BINDINGS,
            MenuAction.SAVE_BINDINGS,
        )
        if binding_action is not None:
            actions.append(binding_action)

    if not actions:
        actions.append(MenuAction.NO_OP)
    return actions


def apply_menu_actions(
    state: Any,
    actions: Sequence[MenuInput],
    fields: Sequence[FieldSpec],
    dimension: int,
) -> None:
    if not fields:
        return
    _ensure_rebind_state(state, dimension)

    field_count = len(fields)
    for raw_action in actions:
        if isinstance(raw_action, RebindCapture):
            if not state.rebind_targets:
                continue
            group, action_name = state.rebind_targets[state.rebind_index % len(state.rebind_targets)]
            ok, msg = rebind_action_key(
                dimension,
                group,
                action_name,
                raw_action.key,
                conflict_mode=state.rebind_conflict_mode,
            )
            if ok and state.rebind_targets:
                state.rebind_index = (state.rebind_index + 1) % len(state.rebind_targets)
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue

        action = raw_action
        if action == MenuAction.NO_OP:
            continue
        if action == MenuAction.QUIT:
            state.running = False
            continue
        if action == MenuAction.REBIND_TOGGLE:
            state.rebind_mode = not state.rebind_mode
            if state.rebind_mode and state.rebind_targets:
                group, action_name = state.rebind_targets[state.rebind_index % len(state.rebind_targets)]
                state.bindings_status = (
                    f"Rebind mode: press key for {group}.{action_name} "
                    f"(mode={state.rebind_conflict_mode}, Esc to exit)"
                )
                state.bindings_status_error = False
            else:
                state.bindings_status = "Rebind mode disabled"
                state.bindings_status_error = False
            continue
        if action == MenuAction.REBIND_TARGET_NEXT:
            if state.rebind_targets:
                state.rebind_index = (state.rebind_index + 1) % len(state.rebind_targets)
                if state.rebind_mode:
                    group, action_name = state.rebind_targets[state.rebind_index]
                    state.bindings_status = f"Rebind target: {group}.{action_name}"
                    state.bindings_status_error = False
            continue
        if action == MenuAction.REBIND_TARGET_PREV:
            if state.rebind_targets:
                state.rebind_index = (state.rebind_index - 1) % len(state.rebind_targets)
                if state.rebind_mode:
                    group, action_name = state.rebind_targets[state.rebind_index]
                    state.bindings_status = f"Rebind target: {group}.{action_name}"
                    state.bindings_status_error = False
            continue
        if action == MenuAction.REBIND_CONFLICT_NEXT:
            state.rebind_conflict_mode = cycle_rebind_conflict_mode(state.rebind_conflict_mode, 1)
            state.bindings_status = f"Rebind conflict mode: {state.rebind_conflict_mode}"
            state.bindings_status_error = False
            continue
        if action == MenuAction.RESET_BINDINGS:
            ok, msg = reset_active_profile_bindings(dimension)
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.START_GAME:
            state.start_game = True
            continue
        if action == MenuAction.SAVE_SETTINGS:
            ok, msg = save_menu_settings(state, dimension)
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.LOAD_SETTINGS:
            ok, msg = load_menu_settings(state, dimension)
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.RESET_SETTINGS:
            ok, msg = reset_menu_settings_to_defaults(state, dimension)
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.PROFILE_NEXT:
            ok, msg, profile = cycle_key_profile(1)
            state.active_profile = profile
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.PROFILE_PREV:
            ok, msg, profile = cycle_key_profile(-1)
            state.active_profile = profile
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.PROFILE_NEW:
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
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.PROFILE_DELETE:
            profile_name = str(getattr(state, "active_profile", active_key_profile()))
            ok, msg = delete_key_profile(profile_name)
            state.active_profile = active_key_profile()
            state.bindings_status = msg
            state.bindings_status_error = not ok
            continue
        if action == MenuAction.SELECT_UP:
            state.selected_index = (state.selected_index - 1) % field_count
            continue
        if action == MenuAction.SELECT_DOWN:
            state.selected_index = (state.selected_index + 1) % field_count
            continue
        if action in (MenuAction.VALUE_LEFT, MenuAction.VALUE_RIGHT):
            _, attr_name, min_val, max_val = fields[state.selected_index]
            delta = -1 if action == MenuAction.VALUE_LEFT else 1
            current = getattr(state.settings, attr_name)
            current = max(min_val, min(max_val, current + delta))
            setattr(state.settings, attr_name, current)
            continue

        apply_menu_binding_action(
            action,
            MenuAction.LOAD_BINDINGS,
            MenuAction.SAVE_BINDINGS,
            dimension,
            state,
        )
