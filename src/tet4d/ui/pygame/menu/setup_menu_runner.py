from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from tet4d.engine.runtime.menu_settings_state import (
    load_menu_settings,
    save_menu_settings,
)
from tet4d.ui.pygame.keybindings import (
    load_active_profile_bindings,
    set_active_key_profile,
)
from tet4d.ui.pygame.menu.menu_controls import (
    FieldSpec,
    MenuAction,
    apply_menu_actions,
    gather_menu_actions,
)

SETUP_MENU_BLOCKED_ACTIONS = {
    MenuAction.LOAD_BINDINGS,
    MenuAction.SAVE_BINDINGS,
    MenuAction.LOAD_SETTINGS,
    MenuAction.SAVE_SETTINGS,
    MenuAction.RESET_SETTINGS,
    MenuAction.PROFILE_PREV,
    MenuAction.PROFILE_NEXT,
    MenuAction.PROFILE_NEW,
    MenuAction.PROFILE_DELETE,
    MenuAction.REBIND_TOGGLE,
    MenuAction.REBIND_TARGET_NEXT,
    MenuAction.REBIND_TARGET_PREV,
    MenuAction.REBIND_CONFLICT_NEXT,
    MenuAction.RESET_BINDINGS,
}


def run_setup_menu_loop(
    *,
    screen: pygame.Surface,
    state: Any,
    dimension: int,
    fields_for_state: Callable[[Any], list[FieldSpec]],
    draw_frame: Callable[[pygame.Surface, Any, list[FieldSpec]], None],
    run_dry_run: Callable[[Any], None] | None = None,
    on_start_saved: Callable[[Any], None] | None = None,
) -> Any | None:
    clock = pygame.time.Clock()
    load_active_profile_bindings()
    ok, msg = load_menu_settings(state, dimension, include_profile=True)
    if ok:
        set_active_key_profile(state.active_profile)
        load_active_profile_bindings()
    else:
        state.bindings_status = msg
        state.bindings_status_error = True

    while state.running and not state.start_game:
        clock.tick(60)
        fields = fields_for_state(state.settings)
        actions = gather_menu_actions(state, dimension)
        if state.selected_index >= len(fields):
            state.selected_index = max(0, len(fields) - 1)
        apply_menu_actions(
            state,
            actions,
            fields,
            dimension,
            blocked_actions=SETUP_MENU_BLOCKED_ACTIONS,
        )
        if state.run_dry_run and run_dry_run is not None:
            run_dry_run(state)
        draw_frame(screen, state, fields)
        pygame.display.flip()

    if state.start_game and state.running:
        ok, msg = save_menu_settings(state, dimension)
        if not ok:
            state.bindings_status = msg
            state.bindings_status_error = True
        else:
            if on_start_saved is not None:
                on_start_saved(state)
        return state.settings

    save_menu_settings(state, dimension)
    return None


__all__ = ["SETUP_MENU_BLOCKED_ACTIONS", "run_setup_menu_loop"]
