from __future__ import annotations

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_EXPLORER
from tet4d.engine.runtime.menu_config import (
    default_settings_payload,
    kick_level_name_for_index,
    random_mode_id_from_index,
)
from tet4d.engine.runtime.topology_playground_state import (
    TRANSPORT_OWNER_EXPLORER,
    TopologyPlaygroundState,
)


def _settings_mode_key(dimension: int) -> str:
    return f"{int(dimension)}d"


def _default_kick_level_name(dimension: int) -> str:
    defaults = default_settings_payload()["settings"][_settings_mode_key(dimension)]
    return kick_level_name_for_index(int(defaults["kick_level_index"]))


def _clamp_index(index: int, size: int) -> int:
    return max(0, min(int(size) - 1, int(index)))


def _piece_set_id_for_state(state: TopologyPlaygroundState) -> str:
    if state.dimension == 2:
        options = piece_set_2d_options_gameplay()
    else:
        options = piece_set_options_for_dimension_gameplay(state.dimension)
    if not options:
        raise ValueError("piece set catalog is empty")
    return options[_clamp_index(state.launch_settings.piece_set_index, len(options))]


def build_gameplay_config_from_topology_playground_state(
    state: TopologyPlaygroundState,
) -> GameConfig | GameConfigND:
    if state.gameplay_mode != GAMEPLAY_MODE_EXPLORER:
        raise ValueError("direct playground launch requires Explorer gameplay mode")
    if state.transport_policy.owner != TRANSPORT_OWNER_EXPLORER:
        raise ValueError("direct playground launch requires explorer-owned transport")

    axis_sizes = tuple(int(value) for value in state.axis_sizes)
    common_kwargs = dict(
        gravity_axis=int(state.gravity_mode.gravity_axis),
        speed_level=int(state.launch_settings.speed_level),
        topology_mode=state.transport_policy.base_policy.mode,
        wrap_gravity_axis=bool(state.transport_policy.base_policy.wrap_gravity_axis),
        topology_edge_rules=state.transport_policy.base_policy.edge_rules,
        kick_level=_default_kick_level_name(state.dimension),
        challenge_layers=0,
        exploration_mode=True,
        explorer_topology_profile=state.explorer_profile,
        rng_mode=random_mode_id_from_index(state.launch_settings.random_mode_index),
        rng_seed=int(state.launch_settings.game_seed),
    )
    piece_set_id = _piece_set_id_for_state(state)

    if state.dimension == 2:
        return GameConfig(
            width=axis_sizes[0],
            height=axis_sizes[1],
            piece_set=piece_set_id,
            **common_kwargs,
        )

    return GameConfigND(
        dims=axis_sizes,
        piece_set_id=piece_set_id,
        **common_kwargs,
    )


__all__ = ["build_gameplay_config_from_topology_playground_state"]