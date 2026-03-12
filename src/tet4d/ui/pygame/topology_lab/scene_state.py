from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
    designer_profiles_for_dimension,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.runtime.topology_playground_state import (
    PRESET_SOURCE_CUSTOM,
    PRESET_SOURCE_DESIGNER,
    PRESET_SOURCE_EXPLORER,
    TopologyPlaygroundGluingDraft as RuntimeTopologyPlaygroundGluingDraft,
    TopologyPlaygroundLaunchSettings as RuntimeTopologyPlaygroundLaunchSettings,
    TopologyPlaygroundPresetMetadata as RuntimeTopologyPlaygroundPresetMetadata,
    TopologyPlaygroundPresetSelection as RuntimeTopologyPlaygroundPresetSelection,
    TopologyPlaygroundProbeState as RuntimeTopologyPlaygroundProbeState,
    TopologyPlaygroundSandboxPieceState as RuntimeTopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig as RuntimeTopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension

from .common import (
    ExplorerGlueDraft,
    boundaries_for_dimension,
    default_draft_for_dimension,
    permutation_options_for_dimension,
)

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
    PANE_CONTROLS: "Analysis View",
    PANE_SCENE: "Explorer Editor",
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


@dataclass(frozen=True)
class ExplorerPreviewCompileSignature:
    profile: ExplorerTopologyProfile
    dims: tuple[int, ...]


@dataclass(frozen=True)
class ExplorerPreviewCompileArtifacts:
    signature: ExplorerPreviewCompileSignature
    preview: dict[str, object] | None
    preview_error: str | None


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
    sandbox: RuntimeTopologyPlaygroundSandboxPieceState | None = None
    play_preview_requested: bool = False
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
    experiment_batch: dict[str, object] | None = None
    canonical_state: RuntimeTopologyPlaygroundState | None = None


TopologyLabState = TopologyPlaygroundState


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


def _runtime_draft_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundGluingDraft:
    draft = state.explorer_draft or default_draft_for_dimension(state.dimension)
    boundaries = boundaries_for_dimension(state.dimension)
    permutations = permutation_options_for_dimension(state.dimension)
    source_index = max(0, min(int(draft.source_index), len(boundaries) - 1))
    target_index = max(0, min(int(draft.target_index), len(boundaries) - 1))
    permutation_index = max(
        0,
        min(int(draft.permutation_index), len(permutations) - 1),
    )
    signs = tuple(-1 if int(value) < 0 else 1 for value in draft.signs)
    if len(signs) != state.dimension - 1:
        signs = tuple(1 for _ in range(state.dimension - 1))
    return RuntimeTopologyPlaygroundGluingDraft(
        slot_index=max(0, int(draft.slot_index)),
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


def _runtime_launch_settings_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundLaunchSettings:
    settings = state.play_settings
    if settings is None:
        return RuntimeTopologyPlaygroundLaunchSettings()
    return RuntimeTopologyPlaygroundLaunchSettings(
        piece_set_index=int(settings.piece_set_index),
        speed_level=int(settings.speed_level),
        random_mode_index=int(settings.random_mode_index),
        game_seed=int(settings.game_seed),
    )


def _axis_sizes_from_ui(state: TopologyPlaygroundState) -> tuple[int, ...]:
    if state.play_settings is not None:
        dims = tuple(
            int(value) for value in state.play_settings.board_dims[: state.dimension]
        )
        if len(dims) == state.dimension and all(value > 0 for value in dims):
            return dims
    if (
        state.canonical_state is not None
        and len(state.canonical_state.axis_sizes) == state.dimension
    ):
        return tuple(int(value) for value in state.canonical_state.axis_sizes)
    return explorer_topology_preview_dims(state.dimension)


def _runtime_probe_state_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundProbeState:
    coord = state.probe_coord
    if coord is not None and len(coord) != state.dimension:
        coord = None
    path = tuple(
        tuple(int(value) for value in entry)
        for entry in (state.probe_path or ())
        if len(entry) == state.dimension
    )
    trace = tuple(str(entry) for entry in (state.probe_trace or ()))
    return RuntimeTopologyPlaygroundProbeState(
        coord=coord,
        path=path,
        trace=trace,
        highlighted_gluing=state.highlighted_glue_id,
    )


def _runtime_sandbox_state_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundSandboxPieceState:
    if state.sandbox is None:
        return RuntimeTopologyPlaygroundSandboxPieceState()
    return state.sandbox


def _runtime_topology_preset_selection_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundPresetSelection:
    preset_id = state.profile.preset_id
    if preset_id is None:
        return RuntimeTopologyPlaygroundPresetSelection(source=PRESET_SOURCE_CUSTOM)
    for preset in designer_profiles_for_dimension(state.dimension, state.gameplay_mode):
        if preset.profile_id == preset_id:
            return RuntimeTopologyPlaygroundPresetSelection(
                preset_id=preset.profile_id,
                label=preset.label,
                description=preset.description,
                source=PRESET_SOURCE_DESIGNER,
            )
    return RuntimeTopologyPlaygroundPresetSelection(
        preset_id=preset_id,
        source=PRESET_SOURCE_CUSTOM,
    )


def _runtime_explorer_preset_selection_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundPresetSelection:
    profile = state.explorer_profile
    if profile is None:
        return RuntimeTopologyPlaygroundPresetSelection(source=PRESET_SOURCE_CUSTOM)
    for preset in explorer_presets_for_dimension(state.dimension):
        if preset.profile == profile:
            return RuntimeTopologyPlaygroundPresetSelection(
                preset_id=preset.preset_id,
                label=preset.label,
                description=preset.description,
                source=PRESET_SOURCE_EXPLORER,
                unsafe=preset.unsafe,
            )
    return RuntimeTopologyPlaygroundPresetSelection(source=PRESET_SOURCE_CUSTOM)


def _runtime_preset_metadata_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundPresetMetadata:
    return RuntimeTopologyPlaygroundPresetMetadata(
        topology_preset=_runtime_topology_preset_selection_from_ui(state),
        explorer_preset=_runtime_explorer_preset_selection_from_ui(state),
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


def sync_shell_state_from_canonical(state: TopologyPlaygroundState) -> None:
    runtime_state = state.canonical_state
    if runtime_state is None:
        return
    state.explorer_profile = runtime_state.explorer_profile
    state.explorer_draft = _ui_draft_from_runtime(runtime_state)
    state.play_settings = ExplorerPlaygroundSettings(
        board_dims=tuple(int(value) for value in runtime_state.axis_sizes),
        piece_set_index=int(runtime_state.launch_settings.piece_set_index),
        speed_level=int(runtime_state.launch_settings.speed_level),
        random_mode_index=int(runtime_state.launch_settings.random_mode_index),
        game_seed=int(runtime_state.launch_settings.game_seed),
    )
    probe_unavailable = any(
        str(entry).startswith("Probe unavailable:")
        for entry in (state.probe_trace or ())
    )
    if not probe_unavailable:
        state.probe_coord = runtime_state.probe_state.coord
        state.probe_trace = list(runtime_state.probe_state.trace)
        state.probe_path = list(runtime_state.probe_state.path)
        state.highlighted_glue_id = runtime_state.probe_state.highlighted_gluing
    sandbox_state = runtime_state.sandbox_piece_state
    state.sandbox = (
        sandbox_state if _sandbox_visible_in_shell(state, sandbox_state) else None
    )
    state.selected_boundary_index = _boundary_index(runtime_state.selected_boundary)
    state.selected_glue_id = runtime_state.selected_gluing
    state.dirty = bool(runtime_state.dirty)


def uses_general_explorer_editor(state: TopologyPlaygroundState) -> bool:
    return state.gameplay_mode == GAMEPLAY_MODE_EXPLORER and state.dimension in (
        2,
        3,
        4,
    )


def sync_canonical_playground_state(state: TopologyPlaygroundState) -> None:
    if not uses_general_explorer_editor(state):
        state.canonical_state = None
        return
    explorer_profile = state.explorer_profile
    if explorer_profile is None:
        explorer_profile = ExplorerTopologyProfile(
            dimension=state.dimension,
            gluings=(),
        )
    topology_config = RuntimeTopologyPlaygroundTopologyConfig(
        legacy_profile=state.profile,
        explorer_profile=explorer_profile,
        gluing_draft=_runtime_draft_from_ui(state),
    )
    runtime_kwargs = dict(
        dimension=state.dimension,
        axis_sizes=_axis_sizes_from_ui(state),
        topology_config=topology_config,
        selected_boundary=_boundary_from_index(
            state.dimension,
            state.selected_boundary_index,
        ),
        selected_gluing=state.selected_glue_id,
        active_tool=state.active_tool,
        probe_state=_runtime_probe_state_from_ui(state),
        sandbox_piece_state=_runtime_sandbox_state_from_ui(state),
        launch_settings=_runtime_launch_settings_from_ui(state),
        transport_policy=None,
        preset_metadata=_runtime_preset_metadata_from_ui(state),
        dirty=state.dirty,
    )
    if state.canonical_state is None:
        state.canonical_state = RuntimeTopologyPlaygroundState(**runtime_kwargs)
    else:
        state.canonical_state = replace(state.canonical_state, **runtime_kwargs)
    sync_shell_state_from_canonical(state)


def canonical_playground_state(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundState | None:
    return state.canonical_state if uses_general_explorer_editor(state) else None


def current_explorer_profile(
    state: TopologyPlaygroundState,
) -> ExplorerTopologyProfile | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.explorer_profile
    return state.explorer_profile


def current_explorer_draft(
    state: TopologyPlaygroundState,
) -> ExplorerGlueDraft | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return _ui_draft_from_runtime(runtime_state)
    return state.explorer_draft


def current_selected_boundary_index(
    state: TopologyPlaygroundState,
) -> int | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return _boundary_index(runtime_state.selected_boundary)
    return state.selected_boundary_index


def current_selected_glue_id(state: TopologyPlaygroundState) -> str | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.selected_gluing
    return state.selected_glue_id


def current_highlighted_glue_id(state: TopologyPlaygroundState) -> str | None:
    if _probe_unavailable_locally(state):
        return state.highlighted_glue_id
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.highlighted_gluing
    return state.highlighted_glue_id


def _probe_unavailable_locally(state: TopologyPlaygroundState) -> bool:
    return any(
        str(entry).startswith("Probe unavailable:")
        for entry in (state.probe_trace or ())
    )


def current_probe_coord(state: TopologyPlaygroundState) -> tuple[int, ...] | None:
    if _probe_unavailable_locally(state):
        return state.probe_coord
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.coord
    return state.probe_coord


def current_probe_trace(state: TopologyPlaygroundState) -> list[str]:
    if _probe_unavailable_locally(state):
        return list(state.probe_trace or ())
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.trace)
    return list(state.probe_trace or ())


def current_probe_path(state: TopologyPlaygroundState) -> list[tuple[int, ...]]:
    if _probe_unavailable_locally(state):
        return list(state.probe_path or ())
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.path)
    return list(state.probe_path or ())


def playground_dims_for_state(state: TopologyPlaygroundState) -> tuple[int, ...]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        dims = runtime_state.axis_sizes
    else:
        dims = (
            state.play_settings.board_dims
            if state.play_settings is not None
            else explorer_topology_preview_dims(state.dimension)
        )
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
    if state.canonical_state is not None:
        sync_canonical_playground_state(state)


def reset_probe_state(state: TopologyPlaygroundState) -> None:
    dims = playground_dims_for_state(state)
    state.probe_coord = tuple(max(0, size // 2) for size in dims)
    state.probe_trace = []
    state.probe_path = [state.probe_coord]
    state.highlighted_glue_id = None
    if state.canonical_state is not None:
        sync_canonical_playground_state(state)


def ensure_explorer_draft(state: TopologyPlaygroundState) -> None:
    if state.explorer_draft is None or len(state.explorer_draft.signs) != (
        state.dimension - 1
    ):
        state.explorer_draft = default_draft_for_dimension(state.dimension)


def ensure_sandbox_state(state: TopologyPlaygroundState) -> None:
    if state.canonical_state is None and uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)
    if state.canonical_state is not None:
        state.sandbox = state.canonical_state.sandbox_piece_state
        return
    if state.sandbox is None:
        state.sandbox = RuntimeTopologyPlaygroundSandboxPieceState()


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
    if state.canonical_state is not None:
        sync_canonical_playground_state(state)


def cycle_active_pane(state: TopologyPlaygroundState, step: int) -> None:
    current = TOPOLOGY_LAB_PANES.index(state.active_pane)
    state.active_pane = TOPOLOGY_LAB_PANES[(current + step) % len(TOPOLOGY_LAB_PANES)]


__all__ = [
    "ExplorerPlaygroundSettings",
    "PANE_CONTROLS",
    "PANE_LABELS",
    "PANE_SCENE",
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
    "canonical_playground_state",
    "current_explorer_draft",
    "current_explorer_profile",
    "current_highlighted_glue_id",
    "current_probe_coord",
    "current_probe_path",
    "current_probe_trace",
    "current_selected_boundary_index",
    "current_selected_glue_id",
    "cycle_active_pane",
    "ensure_explorer_draft",
    "ensure_probe_state",
    "ensure_sandbox_state",
    "playground_dims_for_state",
    "reset_probe_state",
    "set_active_tool",
    "sync_canonical_playground_state",
    "sync_shell_state_from_canonical",
    "uses_general_explorer_editor",
]
