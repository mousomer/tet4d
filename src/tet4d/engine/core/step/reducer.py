from __future__ import annotations

from typing import Any

from ..model.game2d_types import Action, GameState2DLike
from ..rules.gravity_2d import apply_gravity_tick_2d
from ..rules.lifecycle import advance_or_lock_and_respawn


def apply_action_2d(state: GameState2DLike, action: Action) -> bool:
    if action == Action.HARD_DROP:
        state.hard_drop()
        return True

    action_handlers = {
        Action.MOVE_LEFT: lambda: state.try_move(-1, 0),
        Action.MOVE_RIGHT: lambda: state.try_move(1, 0),
        Action.SOFT_DROP: state.try_soft_drop,
        Action.ROTATE_POSITIVE: lambda: state.try_rotate(+1),
        Action.ROTATE_NEGATIVE: lambda: state.try_rotate(-1),
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

    return apply_gravity_tick_2d(state)


def step_nd(state: Any) -> Any:
    if state.config.exploration_mode or state.game_over or state.current_piece is None:
        return state

    return advance_or_lock_and_respawn(
        state,
        try_advance=state.try_gravity_step,
    )


__all__ = ["apply_action_2d", "step_2d", "step_nd"]
