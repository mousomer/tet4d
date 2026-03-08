from __future__ import annotations

from typing import Callable, Optional

import pygame

from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.ui.pygame.input.key_dispatch import match_bound_action
from tet4d.ui.pygame.keybindings import (
    CAMERA_KEYS_3D,
    DISABLED_KEYS_2D,
    EXPLORER_KEYS_2D,
    KEYS_2D,
    SYSTEM_KEYS,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx


def system_decision_for_key(key: int) -> str | None:
    system_action = match_bound_action(
        key,
        SYSTEM_KEYS,
        ("quit", "menu", "restart", "toggle_grid", "help"),
    )
    if system_action is None:
        return None
    if system_action == "quit" and int(key) == int(pygame.K_ESCAPE):
        play_sfx("menu_confirm")
        return "menu"
    if system_action == "quit":
        return "quit"
    if system_action == "menu":
        play_sfx("menu_confirm")
        return "menu"
    if system_action == "restart":
        play_sfx("menu_confirm")
        return "restart"
    if system_action == "help":
        play_sfx("menu_move")
        return "help"
    play_sfx("menu_move")
    return "toggle_grid"


def gameplay_action_for_key_2d(state: GameState, key: int) -> str | None:
    action_order = [
        "move_x_neg",
        "move_x_pos",
        "rotate_xy_pos",
        "rotate_xy_neg",
        "hard_drop",
        "soft_drop",
    ]
    gameplay_action = match_bound_action(key, KEYS_2D, tuple(action_order))
    if gameplay_action is not None:
        return gameplay_action
    if not state.config.exploration_mode:
        return None
    return match_bound_action(key, EXPLORER_KEYS_2D, ("move_up", "move_down"))


def overlay_action_for_key_2d(key: int) -> str | None:
    return match_bound_action(
        key,
        CAMERA_KEYS_3D,
        ("overlay_alpha_dec", "overlay_alpha_inc"),
    )


def apply_2d_gameplay_action(state: GameState, action: str) -> None:
    handlers = {
        "move_x_neg": lambda: state.try_move(-1, 0),
        "move_x_pos": lambda: state.try_move(1, 0),
        "rotate_xy_pos": lambda: state.try_rotate(+1),
        "rotate_xy_neg": lambda: state.try_rotate(-1),
        "hard_drop": state.hard_drop,
        "soft_drop": lambda: state.try_move(0, 1),
        "move_up": lambda: state.try_move(0, -1),
        "move_down": lambda: state.try_move(0, 1),
    }
    handler = handlers.get(action)
    if handler is not None:
        handler()


def dispatch_2d_gameplay_action(state: GameState, key: int) -> str | None:
    action = gameplay_action_for_key_2d(state, key)
    if action is None:
        return None
    apply_2d_gameplay_action(state, action)
    if action.startswith("rotate_"):
        play_sfx("rotate")
    elif action == "hard_drop":
        play_sfx("drop")
    else:
        play_sfx("move")
    return action


def handle_game_keydown(
    event: pygame.event.Event,
    state: GameState,
    _cfg: GameConfig,
    *,
    allow_gameplay: bool = True,
    action_filter: Callable[[str], bool] | None = None,
    action_observer: Callable[[str], None] | None = None,
) -> Optional[str]:
    key = event.key

    system_decision = system_decision_for_key(key)
    if system_decision is not None:
        if action_filter is not None and not action_filter(system_decision):
            return "continue"
        if action_observer is not None:
            action_observer(system_decision)
        return system_decision

    if not allow_gameplay:
        return "continue"

    if state.game_over:
        return "continue"

    if key in DISABLED_KEYS_2D:
        return "continue"

    gameplay_action = gameplay_action_for_key_2d(state, key)
    if gameplay_action is None:
        return "continue"
    if action_filter is not None and not action_filter(gameplay_action):
        return "continue"
    dispatch_2d_gameplay_action(state, key)
    if action_observer is not None:
        action_observer(gameplay_action)
    return "continue"


__all__ = [
    "apply_2d_gameplay_action",
    "dispatch_2d_gameplay_action",
    "gameplay_action_for_key_2d",
    "handle_game_keydown",
    "overlay_action_for_key_2d",
    "system_decision_for_key",
]
