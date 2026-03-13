from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.runtime.menu_config import default_settings_payload
from tet4d.engine.runtime.topology_playability_signal import resolve_rigid_play_enabled
from tet4d.engine.runtime.topology_playground_state import RIGID_PLAY_MODE_AUTO
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
    build_explorer_transport_resolver,
    validate_explorer_topology_profile,
)

from .scene_state import (
    ExplorerPlaygroundSettings,
    TOOL_CREATE,
    TOOL_SANDBOX,
)

EntrySource = Literal["explorer", "launcher", "lab"]

_BOARD_DIMENSION_FIELDS = ("width", "height", "depth", "fourth")
_EXPLORER_DEFAULT_BOARD_DIMS = {
    2: (8, 8),
    3: (8, 8, 8),
    4: (8, 8, 8, 8),
}


@dataclass(frozen=True)
class ExplorerPlaygroundLaunch:
    dimension: int
    gameplay_mode: str
    initial_tool: str
    entry_source: EntrySource
    settings_snapshot: ExplorerPlaygroundSettings
    explorer_profile: ExplorerTopologyProfile | None = None
    display_settings: object | None = None
    fonts_2d: object | None = None
    startup_notice: str | None = None


def _default_mode_payload(dimension: int) -> dict[str, int]:
    payload = default_settings_payload()["settings"]
    return dict(payload[f"{int(dimension)}d"])


def _board_fields_for_dimension(dimension: int) -> tuple[str, ...]:
    dim = int(dimension)
    if dim not in _EXPLORER_DEFAULT_BOARD_DIMS:
        raise ValueError(f"unsupported explorer dimension: {dimension}")
    return _BOARD_DIMENSION_FIELDS[:dim]


def _explorer_default_board_dims(dimension: int) -> tuple[int, ...]:
    return tuple(_EXPLORER_DEFAULT_BOARD_DIMS[int(dimension)])


def _source_uses_mode_default_board_dims(
    dimension: int,
    *,
    source_settings: object | None,
    mode_defaults: dict[str, int],
) -> bool:
    if source_settings is None:
        return True
    for field_name in _board_fields_for_dimension(dimension):
        if not hasattr(source_settings, field_name):
            return True
        if int(getattr(source_settings, field_name)) != int(mode_defaults[field_name]):
            return False
    return True


def build_explorer_playground_settings(
    *,
    dimension: int,
    source_settings: object | None = None,
) -> ExplorerPlaygroundSettings:
    dim = int(dimension)
    defaults = _default_mode_payload(dim)
    use_compact_board_defaults = _source_uses_mode_default_board_dims(
        dim,
        source_settings=source_settings,
        mode_defaults=defaults,
    )
    default_board_dims = _explorer_default_board_dims(dim)

    def _board_value(name: str, axis: int) -> int:
        if (
            not use_compact_board_defaults
            and source_settings is not None
            and hasattr(source_settings, name)
        ):
            return int(getattr(source_settings, name))
        return int(default_board_dims[axis])

    def _setting_value(name: str) -> int:
        if source_settings is not None and hasattr(source_settings, name):
            return int(getattr(source_settings, name))
        return int(defaults[name])

    rigid_play_mode = (
        str(getattr(source_settings, "rigid_play_mode"))
        if source_settings is not None and hasattr(source_settings, "rigid_play_mode")
        else RIGID_PLAY_MODE_AUTO
    )
    board_dims = [
        _board_value(field_name, axis)
        for axis, field_name in enumerate(_board_fields_for_dimension(dim))
    ]
    return ExplorerPlaygroundSettings(
        board_dims=tuple(board_dims),
        piece_set_index=_setting_value("piece_set_index"),
        speed_level=_setting_value("speed_level"),
        random_mode_index=_setting_value("random_mode_index"),
        game_seed=_setting_value("game_seed"),
        rigid_play_mode=rigid_play_mode,
    )


def _profile_validation_error(
    profile: ExplorerTopologyProfile | None,
    dims: tuple[int, ...],
) -> str | None:
    if profile is None:
        return None
    try:
        validate_explorer_topology_profile(profile, dims=dims)
    except ValueError as exc:
        return str(exc)
    return None


def build_explorer_playground_launch(
    *,
    dimension: int,
    explorer_profile: ExplorerTopologyProfile | None = None,
    display_settings: object | None = None,
    fonts_2d: object | None = None,
    gameplay_mode: str = GAMEPLAY_MODE_EXPLORER,
    entry_source: EntrySource = "explorer",
    initial_tool: str | None = None,
    source_settings: object | None = None,
    settings_snapshot: ExplorerPlaygroundSettings | None = None,
) -> ExplorerPlaygroundLaunch:
    mode = (
        gameplay_mode
        if gameplay_mode in {GAMEPLAY_MODE_EXPLORER, GAMEPLAY_MODE_NORMAL}
        else GAMEPLAY_MODE_EXPLORER
    )
    tool = initial_tool
    if tool is None:
        tool = TOOL_SANDBOX if entry_source == "explorer" else TOOL_CREATE
    snapshot = settings_snapshot or build_explorer_playground_settings(
        dimension=int(dimension),
        source_settings=source_settings,
    )
    resolved_profile = explorer_profile
    startup_notice = None
    if entry_source in {"explorer", "launcher"}:
        validation_error = _profile_validation_error(
            resolved_profile, snapshot.board_dims
        )
        if validation_error is not None:
            startup_notice = (
                "Stored explorer topology is invalid for the current board size; "
                "opening Explorer Playground with the current draft for repair."
            )
    return ExplorerPlaygroundLaunch(
        dimension=int(dimension),
        gameplay_mode=mode,
        initial_tool=tool,
        entry_source=entry_source,
        settings_snapshot=snapshot,
        explorer_profile=resolved_profile,
        display_settings=display_settings,
        fonts_2d=fonts_2d,
        startup_notice=startup_notice,
    )


def build_explorer_playground_config(
    *,
    dimension: int,
    explorer_profile: ExplorerTopologyProfile,
    settings_snapshot: ExplorerPlaygroundSettings | None = None,
):
    snapshot = settings_snapshot or build_explorer_playground_settings(
        dimension=int(dimension)
    )
    if int(dimension) == 2:
        from tet4d.ui.pygame import front2d_setup

        settings = front2d_setup.GameSettings()
        settings.width, settings.height = snapshot.board_dims[:2]
        settings.piece_set_index = int(snapshot.piece_set_index)
        settings.speed_level = int(snapshot.speed_level)
        settings.random_mode_index = int(snapshot.random_mode_index)
        settings.game_seed = int(snapshot.game_seed)
        settings.exploration_mode = 1
        settings.topology_advanced = 1
        cfg = front2d_setup.config_from_settings(
            settings,
            explorer_topology_profile_override=explorer_profile,
        )
        cfg.width, cfg.height = snapshot.board_dims[:2]
        cfg.explorer_transport = build_explorer_transport_resolver(
            explorer_profile,
            snapshot.board_dims[:2],
        )
        cfg.explorer_rigid_play_enabled = resolve_rigid_play_enabled(
            explorer_profile,
            dims=snapshot.board_dims[:2],
            rigid_play_mode=snapshot.rigid_play_mode,
            resolver=cfg.explorer_transport,
        )
        return cfg

    from tet4d.ui.pygame import frontend_nd_setup

    settings = frontend_nd_setup.GameSettingsND()
    settings.width, settings.height = snapshot.board_dims[:2]
    settings.depth = (
        int(snapshot.board_dims[2])
        if len(snapshot.board_dims) >= 3
        else int(settings.depth)
    )
    settings.fourth = (
        int(snapshot.board_dims[3])
        if len(snapshot.board_dims) >= 4
        else int(settings.fourth)
    )
    settings.piece_set_index = int(snapshot.piece_set_index)
    settings.speed_level = int(snapshot.speed_level)
    settings.random_mode_index = int(snapshot.random_mode_index)
    settings.game_seed = int(snapshot.game_seed)
    settings.exploration_mode = 1
    settings.topology_advanced = 1
    cfg = frontend_nd_setup.build_config(
        settings,
        int(dimension),
        explorer_topology_profile_override=explorer_profile,
    )
    cfg.dims = tuple(int(value) for value in snapshot.board_dims)
    cfg.explorer_transport = build_explorer_transport_resolver(
        explorer_profile,
        cfg.dims,
    )
    cfg.explorer_rigid_play_enabled = resolve_rigid_play_enabled(
        explorer_profile,
        dims=cfg.dims,
        rigid_play_mode=snapshot.rigid_play_mode,
        resolver=cfg.explorer_transport,
    )
    return cfg


__all__ = [
    "ExplorerPlaygroundLaunch",
    "build_explorer_playground_config",
    "build_explorer_playground_launch",
    "build_explorer_playground_settings",
]
