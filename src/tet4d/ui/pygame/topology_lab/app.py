from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.runtime.menu_config import default_settings_payload
from tet4d.engine.runtime.topology_explorer_preview import compile_explorer_topology_preview
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import (
    ExplorerTopologyPreset,
    explorer_presets_for_dimension,
)

from .scene_state import (
    ExplorerPlaygroundSettings,
    TOOL_CREATE,
    TOOL_SANDBOX,
)

EntrySource = Literal["explorer", "lab"]


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


def build_explorer_playground_settings(
    *,
    dimension: int,
    source_settings: object | None = None,
) -> ExplorerPlaygroundSettings:
    dim = int(dimension)
    defaults = _default_mode_payload(dim)

    def _value(name: str) -> int:
        if source_settings is not None and hasattr(source_settings, name):
            return int(getattr(source_settings, name))
        return int(defaults[name])

    board_dims = [_value("width"), _value("height")]
    if dim >= 3:
        board_dims.append(_value("depth"))
    if dim >= 4:
        board_dims.append(_value("fourth"))
    return ExplorerPlaygroundSettings(
        board_dims=tuple(board_dims),
        piece_set_index=_value("piece_set_index"),
        speed_level=_value("speed_level"),
        random_mode_index=_value("random_mode_index"),
        game_seed=_value("game_seed"),
    )


def _profile_validation_error(
    profile: ExplorerTopologyProfile | None,
    dims: tuple[int, ...],
) -> str | None:
    if profile is None:
        return None
    try:
        compile_explorer_topology_preview(
            profile,
            dims=dims,
            source="explorer_playground_launch",
        )
    except ValueError as exc:
        return str(exc)
    return None


def _fallback_explorer_preset(
    dimension: int,
    dims: tuple[int, ...],
) -> ExplorerTopologyPreset | None:
    presets = explorer_presets_for_dimension(int(dimension))
    for allow_empty in (False, True):
        for preset in presets:
            if not allow_empty and preset.preset_id.startswith("empty_"):
                continue
            if _profile_validation_error(preset.profile, dims) is None:
                return preset
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
    if entry_source == "explorer":
        validation_error = _profile_validation_error(resolved_profile, snapshot.board_dims)
        if validation_error is not None:
            fallback = _fallback_explorer_preset(int(dimension), snapshot.board_dims)
            if fallback is not None:
                resolved_profile = fallback.profile
                startup_notice = (
                    "Stored explorer topology is invalid for the current board size; "
                    f"loaded preset '{fallback.label}' instead."
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
        return cfg

    from tet4d.ui.pygame import frontend_nd_setup

    settings = frontend_nd_setup.GameSettingsND()
    settings.width, settings.height = snapshot.board_dims[:2]
    settings.depth = int(snapshot.board_dims[2]) if len(snapshot.board_dims) >= 3 else int(settings.depth)
    settings.fourth = int(snapshot.board_dims[3]) if len(snapshot.board_dims) >= 4 else int(settings.fourth)
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
    return cfg


__all__ = [
    "ExplorerPlaygroundLaunch",
    "build_explorer_playground_config",
    "build_explorer_playground_launch",
    "build_explorer_playground_settings",
]
