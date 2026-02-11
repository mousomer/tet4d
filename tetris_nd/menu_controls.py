from __future__ import annotations

from collections.abc import Sequence
from enum import Enum, auto
from typing import Any

import pygame

from .menu_keybinding_shortcuts import (
    apply_menu_binding_action,
    menu_binding_action_for_key,
)

FieldSpec = tuple[str, str, int, int]


class MenuAction(Enum):
    QUIT = auto()
    START_GAME = auto()
    SELECT_UP = auto()
    SELECT_DOWN = auto()
    VALUE_LEFT = auto()
    VALUE_RIGHT = auto()
    LOAD_BINDINGS = auto()
    SAVE_BINDINGS = auto()
    NO_OP = auto()


_MENU_KEY_ACTIONS = {
    pygame.K_ESCAPE: MenuAction.QUIT,
    pygame.K_RETURN: MenuAction.START_GAME,
    pygame.K_KP_ENTER: MenuAction.START_GAME,
    pygame.K_UP: MenuAction.SELECT_UP,
    pygame.K_DOWN: MenuAction.SELECT_DOWN,
    pygame.K_LEFT: MenuAction.VALUE_LEFT,
    pygame.K_RIGHT: MenuAction.VALUE_RIGHT,
}


def gather_menu_actions() -> list[MenuAction]:
    actions: list[MenuAction] = []
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            actions.append(MenuAction.QUIT)
            continue
        if event.type != pygame.KEYDOWN:
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
    actions: Sequence[MenuAction],
    fields: Sequence[FieldSpec],
    dimension: int,
) -> None:
    if not fields:
        return

    field_count = len(fields)
    for action in actions:
        if action == MenuAction.NO_OP:
            continue
        if action == MenuAction.QUIT:
            state.running = False
            continue
        if action == MenuAction.START_GAME:
            state.start_game = True
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
