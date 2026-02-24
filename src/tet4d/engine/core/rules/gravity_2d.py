from __future__ import annotations

from ..model.game2d_types import GameState2DLike
from .state_queries import can_piece_exist_2d


def apply_gravity_tick_2d(state: GameState2DLike) -> GameState2DLike:
    if state.config.exploration_mode:
        return state

    if state.current_piece is None:
        return state

    moved_down = state.current_piece.moved(0, 1)
    if can_piece_exist_2d(state, moved_down):
        state.current_piece = moved_down
    else:
        state.lock_current_piece()
        if not state.game_over:
            state.spawn_new_piece()
    return state


__all__ = ["apply_gravity_tick_2d"]
