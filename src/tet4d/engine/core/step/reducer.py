from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...game2d import Action, GameState
    from ...game_nd import GameStateND


def step_2d(state: "GameState", action: "Action") -> "GameState":
    state.step(action)
    return state


def step_nd(state: "GameStateND") -> "GameStateND":
    state.step()
    return state


def step(state: "GameState | GameStateND", action: "Action | None" = None) -> "GameState | GameStateND":
    from ...game2d import Action, GameState

    if isinstance(state, GameState):
        step_2d(state, Action.NONE if action is None else action)
        return state
    if action is not None:
        raise TypeError("ND engine step does not accept a 2D Action")
    step_nd(state)
    return state


__all__ = ["step", "step_2d", "step_nd"]

