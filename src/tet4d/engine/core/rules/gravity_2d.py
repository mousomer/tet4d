from __future__ import annotations

from ..model.game2d_types import GameState2DLike
from .lifecycle import advance_or_lock_and_respawn
from .state_queries import can_piece_exist_2d


def apply_gravity_tick_2d(state: GameState2DLike) -> GameState2DLike:
    if state.config.exploration_mode:
        return state

    if state.current_piece is None:
        return state

    def _try_advance() -> bool:
        moved_down = state.current_piece.moved(0, 1)
        if not can_piece_exist_2d(state, moved_down):
            return False
        state.current_piece = moved_down
        return True

    return advance_or_lock_and_respawn(state, try_advance=_try_advance)


__all__ = ["apply_gravity_tick_2d"]
