from __future__ import annotations

from typing import Any


def step_2d(state: Any, action: Any) -> Any:
    if state.game_over:
        return state

    # Hard drop locks/spawns immediately and is handled by the state helper.
    if state._apply_action(action):
        return state

    if state.config.exploration_mode:
        return state

    if state.current_piece is None:
        return state

    moved_down = state.current_piece.moved(0, 1)
    if state._can_exist(moved_down):
        state.current_piece = moved_down
    else:
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
    return state


def step_nd(state: Any) -> Any:
    state.step()
    return state


__all__ = ["step_2d", "step_nd"]
