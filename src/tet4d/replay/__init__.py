"""Replay schema + pure playback helpers (no file I/O)."""

from collections.abc import Iterable

from tet4d.engine import api

from .format import ReplayEvent2D, ReplayScript2D, ReplayTickScriptND


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


def record_replay_2d(
    *, config: api.GameConfig, seed: int, actions: Iterable[api.Action]
) -> ReplayScript2D:
    events = tuple(ReplayEvent2D(action=action.name) for action in actions)
    return ReplayScript2D(seed=int(seed), config=config, events=events)


def record_replay_nd_ticks(
    *, config: api.GameConfigND, seed: int, ticks: int
) -> ReplayTickScriptND:
    return ReplayTickScriptND(seed=int(seed), config=config, ticks=max(0, int(ticks)))


__all__ = [
    "ReplayEvent2D",
    "ReplayScript2D",
    "ReplayTickScriptND",
    "play_replay_2d",
    "play_replay_nd_ticks",
    "record_replay_2d",
    "record_replay_nd_ticks",
]
