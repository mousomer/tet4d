from __future__ import annotations

from tet4d.engine import api

from .format import ReplayScript2D, ReplayTickScriptND


def play_replay_2d(script: ReplayScript2D) -> api.GameState2D:
    state = api.new_game_state_2d(script.config, seed=script.seed)
    for event in script.events:
        api.step_2d(state, api.Action[event.action])
    return state


def play_replay_nd_ticks(script: ReplayTickScriptND) -> api.GameStateND:
    state = api.new_game_state_nd(script.config, seed=script.seed)
    for _ in range(max(0, script.ticks)):
        api.step_nd(state)
    return state
