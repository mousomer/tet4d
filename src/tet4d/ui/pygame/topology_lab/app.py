from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile

from .scene_state import TOOL_CREATE, TOOL_PROBE

EntrySource = Literal["explorer", "lab"]


@dataclass(frozen=True)
class ExplorerPlaygroundLaunch:
    dimension: int
    gameplay_mode: str
    initial_tool: str
    entry_source: EntrySource
    explorer_profile: ExplorerTopologyProfile | None = None
    display_settings: object | None = None
    fonts_2d: object | None = None


def build_explorer_playground_launch(
    *,
    dimension: int,
    explorer_profile: ExplorerTopologyProfile | None = None,
    display_settings: object | None = None,
    fonts_2d: object | None = None,
    gameplay_mode: str = GAMEPLAY_MODE_EXPLORER,
    entry_source: EntrySource = "explorer",
    initial_tool: str | None = None,
) -> ExplorerPlaygroundLaunch:
    mode = (
        gameplay_mode
        if gameplay_mode in {GAMEPLAY_MODE_EXPLORER, GAMEPLAY_MODE_NORMAL}
        else GAMEPLAY_MODE_EXPLORER
    )
    tool = initial_tool
    if tool is None:
        tool = TOOL_PROBE if entry_source == "explorer" else TOOL_CREATE
    return ExplorerPlaygroundLaunch(
        dimension=int(dimension),
        gameplay_mode=mode,
        initial_tool=tool,
        entry_source=entry_source,
        explorer_profile=explorer_profile,
        display_settings=display_settings,
        fonts_2d=fonts_2d,
    )


def build_explorer_playground_config(
    *,
    dimension: int,
    explorer_profile: ExplorerTopologyProfile,
):
    if int(dimension) == 2:
        from tet4d.ui.pygame import front2d_setup

        settings = front2d_setup.GameSettings()
        settings.exploration_mode = 1
        settings.topology_advanced = 1
        return front2d_setup.config_from_settings(
            settings,
            explorer_topology_profile_override=explorer_profile,
        )

    from tet4d.ui.pygame import frontend_nd_setup

    settings = frontend_nd_setup.GameSettingsND()
    settings.exploration_mode = 1
    settings.topology_advanced = 1
    return frontend_nd_setup.build_config(
        settings,
        int(dimension),
        explorer_topology_profile_override=explorer_profile,
    )


__all__ = [
    "ExplorerPlaygroundLaunch",
    "build_explorer_playground_config",
    "build_explorer_playground_launch",
]