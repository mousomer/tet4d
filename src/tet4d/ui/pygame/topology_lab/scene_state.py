from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TOPOLOGY_PLAYGROUND_TOOLS,
    TopologyPlaygroundGluingDraft as RuntimeTopologyPlaygroundGluingDraft,
    TopologyPlaygroundPlayabilityAnalysis as RuntimeTopologyPlaygroundPlayabilityAnalysis,
    TopologyPlaygroundSandboxPieceState as RuntimeTopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
    WORKSPACE_EDITOR,
    WORKSPACE_PLAY,
    WORKSPACE_SANDBOX,
    canonical_tool_name as runtime_canonical_tool_name,
    workspace_for_tool as runtime_workspace_for_tool,
)
from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile

from .common import (
    ExplorerGlueDraft,
    boundaries_for_dimension,
    default_draft_for_dimension,
    permutation_options_for_dimension,
)
from .interaction_audit import ExplorerInteractionAudit

PANE_CONTROLS = "controls"
PANE_SCENE = "scene"
TOPOLOGY_LAB_PANES = (PANE_CONTROLS, PANE_SCENE)
PANE_LABELS = {
    PANE_CONTROLS: "Diagnostics",
    PANE_SCENE: "Workspace",
}
TOPOLOGY_LAB_WORKSPACES = (
    WORKSPACE_EDITOR,
    WORKSPACE_SANDBOX,
    WORKSPACE_PLAY,
)
WORKSPACE_LABELS = {
    WORKSPACE_EDITOR: "Editor",
    WORKSPACE_SANDBOX: "Sandbox",
    WORKSPACE_PLAY: "Play",
}
TOPOLOGY_LAB_TOOLS = TOPOLOGY_PLAYGROUND_TOOLS
TOOL_LABELS = {
    TOOL_EDIT: "Edit",
    TOOL_PROBE: "Probe",
    TOOL_SANDBOX: "Sandbox",
    TOOL_PLAY: "Play",
}
_VALID_RIGID_PLAY_MODES = frozenset(
    (RIGID_PLAY_MODE_AUTO, RIGID_PLAY_MODE_ON, RIGID_PLAY_MODE_OFF)
)


def _normalize_rigid_play_mode(value: object) -> str:
    mode = str(value).strip().lower()
    if mode in _VALID_RIGID_PLAY_MODES:
        return mode
    return RIGID_PLAY_MODE_AUTO


@dataclass(frozen=True)
class ExplorerPlaygroundSettings:
    board_dims: tuple[int, ...]
    piece_set_index: int = 0
    speed_level: int = 1
    random_mode_index: int = 0
    game_seed: int = 0
    rigid_play_mode: str = RIGID_PLAY_MODE_AUTO

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "rigid_play_mode",
            _normalize_rigid_play_mode(self.rigid_play_mode),
        )


@dataclass(frozen=True)
class ExplorerPreviewCompileSignature:
    profile: ExplorerTopologyProfile
    dims: tuple[int, ...]


@dataclass(frozen=True)
class ExplorerPreviewCompileArtifacts:
    signature: ExplorerPreviewCompileSignature
    preview: dict[str, object] | None
    preview_error: str | None


@dataclass(frozen=True)
class ExplorerPlayabilityArtifacts:
    signature: ExplorerPreviewCompileSignature
    analysis: RuntimeTopologyPlaygroundPlayabilityAnalysis


@dataclass
class TopologyPlaygroundState:
    selected: int
    gameplay_mode: str
    dimension: int
    profile: TopologyProfileState
    explorer_profile: ExplorerTopologyProfile | None = None
    explorer_draft: ExplorerGlueDraft | None = None
    play_settings: ExplorerPlaygroundSettings | None = None
    play_settings_by_dimension: dict[int, ExplorerPlaygroundSettings] = field(
        default_factory=dict
    )
    status: str = ""
    status_error: bool = False
    running: bool = True
    dirty: bool = False
    mouse_targets: list[Any] | None = None
    probe_show_trace: bool = True
    probe_show_neighbors: bool = False
    probe_frame_permutation: tuple[int, ...] | None = None
    probe_frame_signs: tuple[int, ...] | None = None
    active_tool: str = TOOL_EDIT
    editor_tool: str = TOOL_EDIT
    active_pane: str = PANE_CONTROLS
    hovered_boundary_index: int | None = None
    hovered_glue_id: str | None = None
    selected_boundary_index: int | None = None
    pending_source_index: int | None = None
    selected_glue_id: str | None = None
    highlighted_glue_id: str | None = None
    sandbox: RuntimeTopologyPlaygroundSandboxPieceState | None = None
    play_preview_requested: bool = False
    explore_preview_requested: bool = False
    scene_camera: Any | None = None
    scene_mouse_orbit: Any | None = None
    scene_boundaries: tuple[BoundaryRef, ...] = ()
    scene_preview_dims: tuple[int, ...] = ()
    scene_active_glue_ids: dict[str, str] = field(default_factory=dict)
    scene_basis_arrows: tuple[dict[str, object], ...] = ()
    scene_preview: dict[str, object] | None = None
    scene_preview_error: str | None = None
    scene_preview_signature: ExplorerPreviewCompileSignature | None = None
    scene_preview_cache: ExplorerPreviewCompileArtifacts | None = None
    scene_playability_cache: ExplorerPlayabilityArtifacts | None = None
    scene_pending_playability_signature: ExplorerPreviewCompileSignature | None = None
    scene_pending_playability_delay_frames: int = 0
    experiment_batch: dict[str, object] | None = None
    pending_explosion_surface_state: Any | None = None
    scene_explosion: object | None = None
    interaction_audit: ExplorerInteractionAudit = field(
        default_factory=ExplorerInteractionAudit
    )
    canonical_state: RuntimeTopologyPlaygroundState | None = None


TopologyLabState = TopologyPlaygroundState


def _identity_probe_frame(dimension: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(range(dimension)), tuple(1 for _ in range(dimension))


def _normalize_probe_frame_value(
    dimension: int,
    permutation: tuple[int, ...] | None,
    signs: tuple[int, ...] | None,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    default_permutation, default_signs = _identity_probe_frame(dimension)
    normalized_permutation = (
        default_permutation
        if permutation is None
        else tuple(int(value) for value in permutation)
    )
    normalized_signs = (
        default_signs if signs is None else tuple(int(value) for value in signs)
    )
    if len(normalized_permutation) != dimension:
        normalized_permutation = default_permutation
    if len(normalized_signs) != dimension:
        normalized_signs = default_signs
    if tuple(sorted(normalized_permutation)) != tuple(range(dimension)):
        normalized_permutation = default_permutation
    if any(value not in (-1, 1) for value in normalized_signs):
        normalized_signs = default_signs
    return normalized_permutation, normalized_signs


def _boundary_index(boundary: BoundaryRef | None) -> int | None:
    if boundary is None:
        return None
    return boundary.axis * 2 + (1 if boundary.side == "+" else 0)


def _boundary_from_index(
    dimension: int,
    boundary_index: int | None,
) -> BoundaryRef | None:
    if boundary_index is None:
        return None
    boundaries = boundaries_for_dimension(dimension)
    index = int(boundary_index)
    if not 0 <= index < len(boundaries):
        return None
    return boundaries[index]


def _runtime_draft_from_value(
    *,
    dimension: int,
    draft: ExplorerGlueDraft | None,
) -> RuntimeTopologyPlaygroundGluingDraft:
    resolved_draft = draft or default_draft_for_dimension(dimension)
    boundaries = boundaries_for_dimension(dimension)
    permutations = permutation_options_for_dimension(dimension)
    source_index = max(0, min(int(resolved_draft.source_index), len(boundaries) - 1))
    target_index = max(0, min(int(resolved_draft.target_index), len(boundaries) - 1))
    permutation_index = max(
        0,
        min(int(resolved_draft.permutation_index), len(permutations) - 1),
    )
    signs = tuple(-1 if int(value) < 0 else 1 for value in resolved_draft.signs)
    if len(signs) != dimension - 1:
        signs = tuple(1 for _ in range(dimension - 1))
    return RuntimeTopologyPlaygroundGluingDraft(
        slot_index=max(0, int(resolved_draft.slot_index)),
        source_boundary=boundaries[source_index],
        target_boundary=boundaries[target_index],
        permutation=permutations[permutation_index],
        signs=signs,
        enabled=True,
    )


def _ui_draft_from_runtime(
    runtime_state: RuntimeTopologyPlaygroundState,
) -> ExplorerGlueDraft:
    runtime_draft = runtime_state.topology_config.gluing_draft
    default_draft = default_draft_for_dimension(runtime_state.dimension)
    boundaries = boundaries_for_dimension(runtime_state.dimension)
    permutations = permutation_options_for_dimension(runtime_state.dimension)
    source_index = _boundary_index(runtime_draft.source_boundary)
    if source_index is None:
        source_index = default_draft.source_index
    target_index = _boundary_index(runtime_draft.target_boundary)
    if target_index is None:
        target_index = default_draft.target_index
    try:
        permutation_index = permutations.index(runtime_draft.permutation)
    except ValueError:
        permutation_index = default_draft.permutation_index
    if not 0 <= source_index < len(boundaries):
        source_index = default_draft.source_index
    if not 0 <= target_index < len(boundaries):
        target_index = default_draft.target_index
    signs = tuple(-1 if int(value) < 0 else 1 for value in runtime_draft.signs)
    if len(signs) != runtime_state.dimension - 1:
        signs = default_draft.signs
    return ExplorerGlueDraft(
        slot_index=max(0, int(runtime_draft.slot_index)),
        source_index=source_index,
        target_index=target_index,
        permutation_index=permutation_index,
        signs=signs,
    )


def _runtime_launch_settings_from_value(
    settings: ExplorerPlaygroundSettings | None,
):
    from tet4d.engine.runtime.topology_playground_state import (
        TopologyPlaygroundLaunchSettings as RuntimeTopologyPlaygroundLaunchSettings,
    )

    if settings is None:
        return RuntimeTopologyPlaygroundLaunchSettings()
    return RuntimeTopologyPlaygroundLaunchSettings(
        piece_set_index=int(settings.piece_set_index),
        speed_level=int(settings.speed_level),
        random_mode_index=int(settings.random_mode_index),
        game_seed=int(settings.game_seed),
        rigid_play_mode=str(settings.rigid_play_mode),
    )


def _sandbox_visible_in_shell(
    state: TopologyPlaygroundState,
    sandbox_state: RuntimeTopologyPlaygroundSandboxPieceState,
) -> bool:
    return bool(
        state.active_tool == TOOL_SANDBOX
        or sandbox_state.enabled
        or sandbox_state.origin is not None
        or sandbox_state.local_blocks is not None
        or sandbox_state.trace
        or sandbox_state.seam_crossings
        or sandbox_state.invalid_message
    )


def _remember_play_settings(
    state: TopologyPlaygroundState,
    settings: ExplorerPlaygroundSettings,
    *,
    dimension: int | None = None,
) -> None:
    target_dimension = state.dimension if dimension is None else int(dimension)
    state.play_settings = settings
    state.play_settings_by_dimension[target_dimension] = settings


def canonical_tool_name(tool: str) -> str:
    return runtime_canonical_tool_name(tool)


def active_workspace_name(state: TopologyPlaygroundState) -> str:
    return runtime_workspace_for_tool(state.active_tool)


def current_editor_tool(state: TopologyPlaygroundState) -> str:
    return canonical_tool_name(state.editor_tool)


def tool_is_edit(tool: str) -> bool:
    return canonical_tool_name(tool) == TOOL_EDIT


def tool_is_probe(tool: str) -> bool:
    return canonical_tool_name(tool) == TOOL_PROBE


def tool_is_sandbox(tool: str) -> bool:
    return canonical_tool_name(tool) == TOOL_SANDBOX


def uses_general_explorer_editor(state: TopologyPlaygroundState) -> bool:
    return state.gameplay_mode == GAMEPLAY_MODE_EXPLORER and state.dimension in (
        2,
        3,
        4,
    )


def controls_pane_active(state: TopologyPlaygroundState) -> bool:
    return state.active_pane == PANE_CONTROLS


def scene_pane_active(state: TopologyPlaygroundState) -> bool:
    return state.active_pane == PANE_SCENE


# `scene_state.py` owns the state shape and shell-owned routing fields.
# Focused helper modules own canonical runtime sync/write logic and probe-state
# selectors/mutations. This facade only re-exports the broad state selectors
# that remain part of the shared shell surface.
from . import scene_state_canonical as _scene_state_canonical  # noqa: E402
from . import scene_state_probe as _scene_state_probe  # noqa: E402

sync_shell_state_from_canonical = _scene_state_canonical.sync_shell_state_from_canonical
sync_canonical_playground_state = _scene_state_canonical.sync_canonical_playground_state
_replace_canonical_state = _scene_state_canonical._replace_canonical_state
_runtime_state_for_write = _scene_state_canonical._runtime_state_for_write
canonical_playground_state = _scene_state_canonical.canonical_playground_state
current_explorer_profile = _scene_state_canonical.current_explorer_profile
current_explorer_draft = _scene_state_canonical.current_explorer_draft
current_play_settings = _scene_state_canonical.current_play_settings
current_dirty = _scene_state_canonical.current_dirty
set_dirty = _scene_state_canonical.set_dirty
replace_play_settings = _scene_state_canonical.replace_play_settings
replace_explorer_profile = _scene_state_canonical.replace_explorer_profile
replace_explorer_draft = _scene_state_canonical.replace_explorer_draft
update_explorer_draft = _scene_state_canonical.update_explorer_draft
current_probe_coord = _scene_state_probe.current_probe_coord
current_probe_trace = _scene_state_probe.current_probe_trace
probe_trace_visible = _scene_state_probe.probe_trace_visible
probe_neighbors_visible = _scene_state_probe.probe_neighbors_visible
current_probe_path = _scene_state_probe.current_probe_path
current_probe_frame = _scene_state_probe.current_probe_frame
replace_probe_state = _scene_state_probe.replace_probe_state
set_probe_trace_visible = _scene_state_probe.set_probe_trace_visible
set_probe_neighbors_visible = _scene_state_probe.set_probe_neighbors_visible
select_projection_coord = _scene_state_probe.select_projection_coord
playground_dims_for_state = _scene_state_probe.playground_dims_for_state
ensure_probe_state = _scene_state_probe.ensure_probe_state
reset_probe_state = _scene_state_probe.reset_probe_state


def ensure_explorer_draft(state: TopologyPlaygroundState) -> None:
    draft = current_explorer_draft(state)
    if draft is None or len(draft.signs) != state.dimension - 1:
        replace_explorer_draft(state, default_draft_for_dimension(state.dimension))


def ensure_sandbox_state(state: TopologyPlaygroundState) -> None:
    runtime_state = _runtime_state_for_write(state, sync_if_missing=True)
    if runtime_state is not None:
        state.sandbox = runtime_state.sandbox_piece_state
        return
    if state.sandbox is None:
        state.sandbox = RuntimeTopologyPlaygroundSandboxPieceState()


def set_active_tool(state: TopologyPlaygroundState, tool: str) -> None:
    normalized_tool = canonical_tool_name(tool)
    if normalized_tool in {TOOL_EDIT, TOOL_PROBE}:
        state.editor_tool = normalized_tool
    state.active_tool = normalized_tool
    state.pending_source_index = None
    state.hovered_boundary_index = None
    state.hovered_glue_id = None
    if not tool_is_sandbox(state.active_tool) and state.sandbox is not None:
        state.sandbox.enabled = False
    if tool_is_sandbox(state.active_tool):
        ensure_sandbox_state(state)
        assert state.sandbox is not None
        state.sandbox.enabled = True
    if canonical_playground_state(state) is not None:
        sync_canonical_playground_state(state)


def set_active_workspace(state: TopologyPlaygroundState, workspace: str) -> None:
    workspace_name = str(workspace)
    if workspace_name == WORKSPACE_EDITOR:
        set_active_tool(state, state.editor_tool)
        return
    if workspace_name == WORKSPACE_SANDBOX:
        set_active_tool(state, TOOL_SANDBOX)
        return
    if workspace_name == WORKSPACE_PLAY:
        set_active_tool(state, TOOL_PLAY)
        return
    raise ValueError(f"unsupported topology lab workspace: {workspace}")


def cycle_active_pane(state: TopologyPlaygroundState, step: int) -> None:
    current = TOPOLOGY_LAB_PANES.index(state.active_pane)
    state.active_pane = TOPOLOGY_LAB_PANES[(current + step) % len(TOPOLOGY_LAB_PANES)]


__all__ = [
    "ExplorerPlayabilityArtifacts",
    "ExplorerPlaygroundSettings",
    "PANE_CONTROLS",
    "PANE_LABELS",
    "PANE_SCENE",
    "TOOL_CREATE",
    "TOOL_EDIT",
    "TOOL_LABELS",
    "TOOL_NAVIGATE",
    "TOOL_PLAY",
    "TOOL_PROBE",
    "TOOL_SANDBOX",
    "TOPOLOGY_LAB_TOOLS",
    "TOPOLOGY_LAB_WORKSPACES",
    "TopologyLabState",
    "TopologyPlaygroundState",
    "WORKSPACE_EDITOR",
    "WORKSPACE_LABELS",
    "WORKSPACE_PLAY",
    "WORKSPACE_SANDBOX",
    "active_workspace_name",
    "canonical_playground_state",
    "canonical_tool_name",
    "controls_pane_active",
    "current_editor_tool",
    "current_explorer_draft",
    "current_explorer_profile",
    "current_dirty",
    "current_play_settings",
    "current_probe_coord",
    "current_probe_frame",
    "current_probe_path",
    "current_probe_trace",
    "probe_neighbors_visible",
    "probe_trace_visible",
    "cycle_active_pane",
    "ensure_explorer_draft",
    "ensure_probe_state",
    "ensure_sandbox_state",
    "playground_dims_for_state",
    "replace_explorer_draft",
    "replace_explorer_profile",
    "replace_play_settings",
    "replace_probe_state",
    "select_projection_coord",
    "reset_probe_state",
    "scene_pane_active",
    "set_probe_neighbors_visible",
    "set_probe_trace_visible",
    "set_active_tool",
    "set_active_workspace",
    "set_dirty",
    "sync_canonical_playground_state",
    "sync_shell_state_from_canonical",
    "tool_is_edit",
    "tool_is_probe",
    "tool_is_sandbox",
    "update_explorer_draft",
    "uses_general_explorer_editor",
]
