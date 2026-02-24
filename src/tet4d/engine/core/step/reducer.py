from __future__ import annotations

from typing import Any

from ..model.game2d_types import Action, GameState2DLike


def apply_action_2d(state: GameState2DLike, action: Action) -> bool:
    if action == Action.HARD_DROP:
        state.hard_drop()
        return True

    action_handlers = {
        Action.MOVE_LEFT: lambda: state.try_move(-1, 0),
        Action.MOVE_RIGHT: lambda: state.try_move(1, 0),
        Action.SOFT_DROP: lambda: state.try_move(0, 1),
        Action.ROTATE_CW: lambda: state.try_rotate(+1),
        Action.ROTATE_CCW: lambda: state.try_rotate(-1),
    }
    handler = action_handlers.get(action)
    if handler is not None:
        handler()
    return False


def step_2d(state: GameState2DLike, action: Action) -> GameState2DLike:
    if state.game_over:
        return state

    # Hard drop locks/spawns immediately and is handled by the state helper.
    if apply_action_2d(state, action):
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
    if state.config.exploration_mode or state.game_over or state.current_piece is None:
        return state

    g = state.config.gravity_axis
    if not state.try_move_axis(g, 1):
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
    return state


__all__ = ["apply_action_2d", "step_2d", "step_nd"]
