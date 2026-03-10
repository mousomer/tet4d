from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile

from .common import ExplorerGlueDraft, default_draft_for_dimension

TOOL_NAVIGATE = "navigate"
TOOL_INSPECT = "inspect_boundary"
TOOL_CREATE = "create_gluing"
TOOL_EDIT = "edit_transform"
TOOL_PROBE = "probe"
TOOL_SANDBOX = "piece_sandbox"
TOOL_PLAY = "play_preview"
PANE_CONTROLS = "controls"
PANE_SCENE = "scene"
TOPOLOGY_LAB_PANES = (PANE_CONTROLS, PANE_SCENE)
PANE_LABELS = {
    PANE_CONTROLS: "Analysis",
    PANE_SCENE: "Explorer",
}
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
    TOOL_PLAY: "Play This Topology",
}


@dataclass(frozen=True)
class ExplorerPlaygroundSettings:
    board_dims: tuple[int, ...]
    piece_set_index: int = 0
    speed_level: int = 1
    random_mode_index: int = 0
    game_seed: int = 0


@dataclass
class PieceSandboxState:
    enabled: bool = False
    piece_index: int = 0
    origin: tuple[int, ...] | None = None
    local_blocks: tuple[tuple[int, ...], ...] | None = None
    trace: list[str] | None = None
    seam_crossings: list[str] | None = None
    invalid_message: str = ""
    show_trace: bool = True


@dataclass
class TopologyPlaygroundState:
    selected: int
    gameplay_mode: str
    dimension: int
    profile: TopologyProfileState
    explorer_profile: ExplorerTopologyProfile | None = None
    explorer_draft: ExplorerGlueDraft | None = None
    play_settings: ExplorerPlaygroundSettings | None = None
    status: str = ""
    status_error: bool = False
    running: bool = True
    dirty: bool = False
    mouse_targets: list[Any] | None = None
    probe_coord: tuple[int, ...] | None = None
    probe_trace: list[str] | None = None
    probe_path: list[tuple[int, ...]] | None = None
    active_tool: str = TOOL_CREATE
    active_pane: str = PANE_CONTROLS
    hovered_boundary_index: int | None = None
    hovered_glue_id: str | None = None
    selected_boundary_index: int | None = None
    pending_source_index: int | None = None
    selected_glue_id: str | None = None
    highlighted_glue_id: str | None = None
    sandbox: PieceSandboxState | None = None
    play_preview_requested: bool = False
    scene_camera: Any | None = None
    scene_mouse_orbit: Any | None = None
    scene_boundaries: tuple[BoundaryRef, ...] = ()
    scene_preview_dims: tuple[int, ...] = ()
    scene_active_glue_ids: dict[str, str] = field(default_factory=dict)
    scene_basis_arrows: tuple[dict[str, object], ...] = ()
    scene_preview: dict[str, object] | None = None
    scene_preview_error: str | None = None


TopologyLabState = TopologyPlaygroundState


def uses_general_explorer_editor(state: TopologyPlaygroundState) -> bool:
    return (
        state.gameplay_mode == GAMEPLAY_MODE_EXPLORER
        and state.dimension in (2, 3, 4)
    )


def playground_dims_for_state(state: TopologyPlaygroundState) -> tuple[int, ...]:
    dims = state.play_settings.board_dims if state.play_settings is not None else explorer_topology_preview_dims(state.dimension)
    normalized = tuple(int(value) for value in dims[: state.dimension])
    if len(normalized) != state.dimension or any(value <= 0 for value in normalized):
        return explorer_topology_preview_dims(state.dimension)
    return normalized


def ensure_probe_state(state: TopologyPlaygroundState) -> None:
    dims = playground_dims_for_state(state)
    if state.probe_coord is None or len(state.probe_coord) != state.dimension:
        state.probe_coord = tuple(0 for _ in range(state.dimension))
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


def reset_probe_state(state: TopologyPlaygroundState) -> None:
    dims = playground_dims_for_state(state)
    state.probe_coord = tuple(max(0, size // 2) for size in dims)
    state.probe_trace = []
    state.probe_path = [state.probe_coord]
    state.highlighted_glue_id = None


def ensure_explorer_draft(state: TopologyPlaygroundState) -> None:
    if state.explorer_draft is None or len(state.explorer_draft.signs) != (
        state.dimension - 1
    ):
        state.explorer_draft = default_draft_for_dimension(state.dimension)


def ensure_sandbox_state(state: TopologyPlaygroundState) -> None:
    if state.sandbox is None:
        state.sandbox = PieceSandboxState()
    if state.sandbox.trace is None:
        state.sandbox.trace = []
    if state.sandbox.seam_crossings is None:
        state.sandbox.seam_crossings = []
    if state.sandbox.origin is None or len(state.sandbox.origin) != state.dimension:
        dims = playground_dims_for_state(state)
        state.sandbox.origin = tuple(max(0, size // 2) for size in dims)


def set_active_tool(state: TopologyPlaygroundState, tool: str) -> None:
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


def cycle_active_pane(state: TopologyPlaygroundState, step: int) -> None:
    current = TOPOLOGY_LAB_PANES.index(state.active_pane)
    state.active_pane = TOPOLOGY_LAB_PANES[(current + step) % len(TOPOLOGY_LAB_PANES)]


__all__ = [
    "ExplorerPlaygroundSettings",
    "PANE_CONTROLS",
    "PANE_LABELS",
    "PANE_SCENE",
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
    "TopologyPlaygroundState",
    "cycle_active_pane",
    "ensure_explorer_draft",
    "ensure_probe_state",
    "ensure_sandbox_state",
    "playground_dims_for_state",
    "reset_probe_state",
    "set_active_tool",
    "uses_general_explorer_editor",
]
