from __future__ import annotations

from typing import Any

import pygame

from .keybindings import load_keybindings_file, save_keybindings_file


def menu_binding_action_for_key(
    key: int, load_action: Any, save_action: Any
) -> Any | None:
    if key == pygame.K_l:
        return load_action
    if key == pygame.K_s:
        return save_action
    return None


def apply_menu_binding_action(
    action: Any, load_action: Any, save_action: Any, dimension: int, state: Any
) -> bool:
    if action == load_action:
        ok, msg = load_keybindings_file(dimension)
    elif action == save_action:
        ok, msg = save_keybindings_file(dimension)
    else:
        return False

    state.bindings_status = msg
    state.bindings_status_error = not ok
    return True


def menu_binding_status_color(is_error: bool) -> tuple[int, int, int]:
    return (255, 150, 150) if is_error else (170, 240, 170)
