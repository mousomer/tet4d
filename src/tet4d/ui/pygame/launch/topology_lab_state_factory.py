from __future__ import annotations

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
)
from tet4d.engine.runtime.topology_profile_store import load_topology_profile
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.ui.pygame.topology_lab import (
    ExplorerPlaygroundSettings,
    PANE_SCENE,
    ensure_explorer_draft,
    ensure_mouse_orbit_state,
    ensure_scene_camera,
    set_active_tool,
)
from tet4d.ui.pygame.topology_lab.app import build_explorer_playground_settings
from tet4d.ui.pygame.topology_lab.controls_panel import (
    _INITIAL_TOOL_BY_GAMEPLAY_MODE,
    _TopologyLabState,
    _normalize_explorer_draft,
    _refresh_explorer_scene_state,
    _sync_explorer_state,
)
from tet4d.ui.pygame.topology_lab.scene_state import (
    current_play_settings,
    ensure_probe_state as _ensure_probe_state,
    replace_explorer_profile,
    replace_play_settings,
)

_TOPOLOGY_DIMENSIONS = (2, 3, 4)


def _initialize_explicit_explorer_startup(
    state: _TopologyLabState,
    *,
    initial_explorer_profile: ExplorerTopologyProfile,
) -> None:
    state.active_pane = PANE_SCENE
    if current_play_settings(state) is None:
        replace_play_settings(
            state,
            build_explorer_playground_settings(dimension=state.dimension),
        )
    replace_explorer_profile(state, initial_explorer_profile)
    ensure_explorer_draft(state)
    _normalize_explorer_draft(state)
    state.scene_camera = ensure_scene_camera(state.dimension, state.scene_camera)
    state.scene_mouse_orbit = ensure_mouse_orbit_state(state.scene_mouse_orbit)
    _refresh_explorer_scene_state(state)
    _ensure_probe_state(state)


def _initial_topology_lab_state(
    start_dimension: int,
    *,
    gameplay_mode: str = GAMEPLAY_MODE_NORMAL,
    initial_explorer_profile: ExplorerTopologyProfile | None = None,
    initial_tool: str | None = None,
    play_settings: ExplorerPlaygroundSettings | None = None,
) -> _TopologyLabState:
    dimension = start_dimension if start_dimension in _TOPOLOGY_DIMENSIONS else 3
    mode = (
        gameplay_mode
        if gameplay_mode in TOPOLOGY_GAMEPLAY_MODE_OPTIONS
        else GAMEPLAY_MODE_NORMAL
    )
    state = _TopologyLabState(
        selected=0,
        gameplay_mode=mode,
        dimension=dimension,
        profile=load_topology_profile(mode, dimension),
        play_settings=play_settings,
    )
    if mode == GAMEPLAY_MODE_EXPLORER and current_play_settings(state) is None:
        replace_play_settings(
            state,
            build_explorer_playground_settings(dimension=dimension),
        )
    if mode == GAMEPLAY_MODE_EXPLORER and initial_explorer_profile is not None:
        _initialize_explicit_explorer_startup(
            state,
            initial_explorer_profile=initial_explorer_profile,
        )
        set_active_tool(state, initial_tool or _INITIAL_TOOL_BY_GAMEPLAY_MODE[mode])
        return state
    _sync_explorer_state(state)
    if mode == GAMEPLAY_MODE_EXPLORER:
        state.active_pane = PANE_SCENE
        if current_play_settings(state) is None:
            replace_play_settings(
                state,
                build_explorer_playground_settings(dimension=dimension),
            )
            _refresh_explorer_scene_state(state)
        if initial_explorer_profile is not None:
            replace_explorer_profile(state, initial_explorer_profile)
            ensure_explorer_draft(state)
            _normalize_explorer_draft(state)
            _refresh_explorer_scene_state(state)
            _ensure_probe_state(state)
        set_active_tool(state, initial_tool or _INITIAL_TOOL_BY_GAMEPLAY_MODE[mode])
    elif initial_tool is not None:
        set_active_tool(state, initial_tool)
    return state


__all__ = ["_initial_topology_lab_state"]
