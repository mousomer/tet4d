from __future__ import annotations

from typing import Any, Callable

from tet4d.ui.pygame.keybindings import cycle_key_profile
from tet4d.ui.pygame.launch.launcher_profile_menu import (
    is_profile_next_key,
    is_profile_prev_key,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx


def handle_launcher_route(
    route_id: str,
    *,
    route_actions: dict[str, str],
    state: Any,
    action_registry: Any,
) -> bool:
    clean_route_id = route_id.strip().lower()
    action_id = route_actions.get(clean_route_id)
    if not action_id:
        state.status = f"No action mapped for route '{clean_route_id}'"
        state.status_error = True
        return False
    try:
        return action_registry.dispatch(action_id)
    except KeyError:
        state.status = f"No handler registered for routed action '{action_id}'"
        state.status_error = True
        return False


def handle_missing_action(action_id: str, *, state: Any) -> bool:
    state.status = f"No handler registered for action '{action_id}'"
    state.status_error = True
    return False


def play_move_sfx() -> bool:
    play_sfx("menu_move")
    return False


def play_confirm_sfx() -> bool:
    play_sfx("menu_confirm")
    return False


def handle_launcher_profile_cycle_key(
    menu_id: str,
    key: int,
    *,
    menu_ids: set[str],
    state: Any,
    session: Any,
    sync_profile_rows: Callable[[], None],
    persist_session_status: Callable[[Any, Any], None],
) -> bool:
    if menu_id not in menu_ids:
        return False
    if not (is_profile_prev_key(key) or is_profile_next_key(key)):
        return False

    step = -1 if is_profile_prev_key(key) else 1
    ok, msg, profile = cycle_key_profile(step)
    if not ok:
        state.status = msg
        state.status_error = True
        return True

    sync_profile_rows()
    persist_session_status(state, session)
    state.status = f"Active key profile: {profile}"
    state.status_error = False
    play_sfx("menu_move")
    return True
