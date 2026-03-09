from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.topology_explorer import ExplorerTopologyProfile

from .common import ExplorerGlueDraft, default_draft_for_dimension

TOOL_NAVIGATE = "navigate"
TOOL_INSPECT = "inspect_boundary"
TOOL_CREATE = "create_gluing"
TOOL_EDIT = "edit_transform"
TOOL_PROBE = "probe"
TOOL_SANDBOX = "piece_sandbox"
TOOL_PLAY = "play_preview"
TOPOLOGY_LAB_TOOLS = (
    TOOL_NAVIGATE,
    TOOL_INSPECT,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TOOL_PLAY,
)
TOOL_LABELS = {
    TOOL_NAVIGATE: "Navigate",
    TOOL_INSPECT: "Inspect",
    TOOL_CREATE: "Create",
    TOOL_EDIT: "Edit",
    TOOL_PROBE: "Probe",
    TOOL_SANDBOX: "Sandbox",
    TOOL_PLAY: "Play",
}


@dataclass
class PieceSandboxState:
    enabled: bool = False
    piece_index: int = 0
    origin: tuple[int, ...] | None = None
    rotation_steps: int = 0
    rotation_plane: tuple[int, int] | None = None
    trace: list[str] | None = None
    invalid_message: str = ""
    show_trace: bool = True


@dataclass
class TopologyLabState:
    selected: int
    gameplay_mode: str
    dimension: int
    profile: TopologyProfileState
    explorer_profile: ExplorerTopologyProfile | None = None
    explorer_draft: ExplorerGlueDraft | None = None
    status: str = ""
    status_error: bool = False
    running: bool = True
    dirty: bool = False
    mouse_targets: list[Any] | None = None
    probe_coord: tuple[int, ...] | None = None
    probe_trace: list[str] | None = None
    probe_path: list[tuple[int, ...]] | None = None
    active_tool: str = TOOL_CREATE
    hovered_boundary_index: int | None = None
    hovered_glue_id: str | None = None
    selected_boundary_index: int | None = None
    pending_source_index: int | None = None
    selected_glue_id: str | None = None
    highlighted_glue_id: str | None = None
    sandbox: PieceSandboxState | None = None
    play_preview_requested: bool = False



def uses_general_explorer_editor(state: TopologyLabState) -> bool:
    return (
        state.gameplay_mode == GAMEPLAY_MODE_EXPLORER
        and state.dimension in (2, 3, 4)
    )



def ensure_probe_state(state: TopologyLabState) -> None:
    if state.probe_coord is None or len(state.probe_coord) != state.dimension:
        state.probe_coord = tuple(0 for _ in range(state.dimension))
    dims = explorer_topology_preview_dims(state.dimension)
    if any(
        value < 0 or value >= dims[index]
        for index, value in enumerate(state.probe_coord)
    ):
        state.probe_coord = tuple(0 for _ in range(state.dimension))
    if state.probe_trace is None:
        state.probe_trace = []
    if state.probe_path is None:
        state.probe_path = [state.probe_coord]
    elif not state.probe_path:
        state.probe_path = [state.probe_coord]
    elif state.probe_path[-1] != state.probe_coord:
        state.probe_path = [state.probe_coord]


def reset_probe_state(state: TopologyLabState) -> None:
    dims = explorer_topology_preview_dims(state.dimension)
    state.probe_coord = tuple(max(0, size // 2) for size in dims)
    state.probe_trace = []
    state.probe_path = [state.probe_coord]
    state.highlighted_glue_id = None



def ensure_explorer_draft(state: TopologyLabState) -> None:
    if state.explorer_draft is None or len(state.explorer_draft.signs) != (
        state.dimension - 1
    ):
        state.explorer_draft = default_draft_for_dimension(state.dimension)



def ensure_sandbox_state(state: TopologyLabState) -> None:
    if state.sandbox is None:
        state.sandbox = PieceSandboxState()
    if state.sandbox.trace is None:
        state.sandbox.trace = []
    if state.sandbox.origin is None or len(state.sandbox.origin) != state.dimension:
        dims = explorer_topology_preview_dims(state.dimension)
        state.sandbox.origin = tuple(max(0, size // 2) for size in dims)
    if state.sandbox.rotation_plane is None:
        if state.dimension == 2:
            state.sandbox.rotation_plane = (0, 1)
        else:
            state.sandbox.rotation_plane = (0, min(2, state.dimension - 1))



def set_active_tool(state: TopologyLabState, tool: str) -> None:
    if tool not in TOPOLOGY_LAB_TOOLS:
        raise ValueError(f"unsupported topology lab tool: {tool}")
    state.active_tool = tool
    state.pending_source_index = None
    state.hovered_boundary_index = None
    state.hovered_glue_id = None
    if tool != TOOL_SANDBOX and state.sandbox is not None:
        state.sandbox.enabled = False
    if tool == TOOL_SANDBOX:
        ensure_sandbox_state(state)
        assert state.sandbox is not None
        state.sandbox.enabled = True


__all__ = [
    "PieceSandboxState",
    "TOOL_CREATE",
    "TOOL_EDIT",
    "TOOL_INSPECT",
    "TOOL_LABELS",
    "TOOL_NAVIGATE",
    "TOOL_PLAY",
    "TOOL_PROBE",
    "TOOL_SANDBOX",
    "TOPOLOGY_LAB_TOOLS",
    "TopologyLabState",
    "ensure_explorer_draft",
    "ensure_probe_state",
    "ensure_sandbox_state",
    "reset_probe_state",
    "set_active_tool",
    "uses_general_explorer_editor",
]
