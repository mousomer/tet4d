"""Replay schema + pure playback helpers (no file I/O)."""

from collections.abc import Iterable

from tet4d.engine import api
from tet4d.engine.topology_explorer.domain_validation import (
    require_instance,
    require_integral,
    require_non_negative_integral,
)

from .format import (
    REPLAY_SCHEMA_VERSION,
    ReplayEvent2D,
    ReplayFormatError,
    ReplayScript2D,
    ReplayTickScriptND,
)


def play_replay_2d(script: ReplayScript2D) -> api.GameState2D:
    state = api.new_game_state_2d(script.config, seed=script.seed)
    for event in script.events:
        api.step_2d(state, api.Action[event.action])
    return state


def play_replay_nd_ticks(script: ReplayTickScriptND) -> api.GameStateND:
    state = api.new_game_state_nd(script.config, seed=script.seed)
    for _ in range(script.ticks):
        api.step_nd(state)
    return state


def record_replay_2d(
    *, config: api.GameConfig, seed: int, actions: Iterable[api.Action]
) -> ReplayScript2D:
    validated_config = require_instance(config, "config", api.GameConfig)
    validated_seed = require_integral(seed, "seed")
    events: list[ReplayEvent2D] = []
    for index, action in enumerate(actions):
        validated_action = require_instance(action, f"actions[{index}]", api.Action)
        events.append(ReplayEvent2D(action=validated_action.name))
    return ReplayScript2D(
        seed=validated_seed,
        config=validated_config,
        events=tuple(events),
    )


def record_replay_nd_ticks(
    *, config: api.GameConfigND, seed: int, ticks: int
) -> ReplayTickScriptND:
    return ReplayTickScriptND(
        seed=require_integral(seed, "seed"),
        config=require_instance(config, "config", api.GameConfigND),
        ticks=require_non_negative_integral(ticks, "ticks"),
    )


__all__ = [
    "REPLAY_SCHEMA_VERSION",
    "ReplayEvent2D",
    "ReplayFormatError",
    "ReplayScript2D",
    "ReplayTickScriptND",
    "play_replay_2d",
    "play_replay_nd_ticks",
    "record_replay_2d",
    "record_replay_nd_ticks",
]
