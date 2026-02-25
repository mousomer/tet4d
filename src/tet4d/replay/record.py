from __future__ import annotations

from collections.abc import Iterable

from tet4d.engine import api

from .format import ReplayEvent2D, ReplayScript2D, ReplayTickScriptND


def record_replay_2d(
    *, config: api.GameConfig, seed: int, actions: Iterable[api.Action]
) -> ReplayScript2D:
    events = tuple(ReplayEvent2D(action=action.name) for action in actions)
    return ReplayScript2D(seed=int(seed), config=config, events=events)


def record_replay_nd_ticks(
    *, config: api.GameConfigND, seed: int, ticks: int
) -> ReplayTickScriptND:
    return ReplayTickScriptND(seed=int(seed), config=config, ticks=max(0, int(ticks)))
