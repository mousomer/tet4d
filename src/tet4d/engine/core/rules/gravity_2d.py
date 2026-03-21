from __future__ import annotations

from ..model.game2d_types import GameState2DLike


def apply_gravity_tick_2d(state: GameState2DLike) -> GameState2DLike:
    state.step_gravity()
    return state


__all__ = ["apply_gravity_tick_2d"]
