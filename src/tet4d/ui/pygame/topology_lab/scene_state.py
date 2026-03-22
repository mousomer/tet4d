from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    TopologyProfileState,
    designer_profiles_for_dimension,
)
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.runtime.topology_explorer_preview import (
    recommended_explorer_probe_coord,
)
from tet4d.engine.runtime.topology_playground_state import (
    PRESET_SOURCE_CUSTOM,
    PRESET_SOURCE_DESIGNER,
    PRESET_SOURCE_EXPLORER,
    RIGID_PLAY_MODE_AUTO,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TOPOLOGY_PLAYGROUND_TOOLS,
    TopologyPlaygroundGluingDraft as RuntimeTopologyPlaygroundGluingDraft,
    TopologyPlaygroundLaunchSettings as RuntimeTopologyPlaygroundLaunchSettings,
    TopologyPlaygroundPresetMetadata as RuntimeTopologyPlaygroundPresetMetadata,
    TopologyPlaygroundPresetSelection as RuntimeTopologyPlaygroundPresetSelection,
    TopologyPlaygroundProbeState as RuntimeTopologyPlaygroundProbeState,
    TopologyPlaygroundSandboxPieceState as RuntimeTopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig as RuntimeTopologyPlaygroundTopologyConfig,
    WORKSPACE_EDITOR,
    WORKSPACE_PLAY,
    WORKSPACE_SANDBOX,
    canonical_tool_name as runtime_canonical_tool_name,
    workspace_for_tool as runtime_workspace_for_tool,
)
from tet4d.engine.topology_explorer import BoundaryRef, ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension

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


@dataclass(frozen=True)
class ExplorerPlaygroundSettings:
    board_dims: tuple[int, ...]
    piece_set_index: int = 0
    speed_level: int = 1
    random_mode_index: int = 0
    game_seed: int = 0
    rigid_play_mode: str = RIGID_PLAY_MODE_AUTO


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
    experiment_batch: dict[str, object] | None = None
    interaction_audit: ExplorerInteractionAudit = field(
        default_factory=ExplorerInteractionAudit
    )
    canonical_state: RuntimeTopologyPlaygroundState | None = None


TopologyLabState = TopologyPlaygroundState

_UNSET = object()


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


def _runtime_draft_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundGluingDraft:
    return _runtime_draft_from_value(
        dimension=state.dimension,
        draft=current_explorer_draft(state),
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
) -> RuntimeTopologyPlaygroundLaunchSettings:
    if settings is None:
        return RuntimeTopologyPlaygroundLaunchSettings()
    return RuntimeTopologyPlaygroundLaunchSettings(
        piece_set_index=int(settings.piece_set_index),
        speed_level=int(settings.speed_level),
        random_mode_index=int(settings.random_mode_index),
        game_seed=int(settings.game_seed),
        rigid_play_mode=str(settings.rigid_play_mode),
    )


def _runtime_launch_settings_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundLaunchSettings:
    return _runtime_launch_settings_from_value(current_play_settings(state))


def _axis_sizes_from_ui(state: TopologyPlaygroundState) -> tuple[int, ...]:
    settings = current_play_settings(state)
    if settings is not None:
        dims = tuple(
            int(value) for value in settings.board_dims[: state.dimension]
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
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        coord = runtime_state.probe_state.coord
        path = runtime_state.probe_state.path
        trace = runtime_state.probe_state.trace
        highlighted_gluing = runtime_state.probe_state.highlighted_gluing
    else:
        coord = None
        path = ()
        trace = ()
        highlighted_gluing = (
            None if state.highlighted_glue_id is None else str(state.highlighted_glue_id)
        )
    frame_permutation, frame_signs = current_probe_frame(state)
    return RuntimeTopologyPlaygroundProbeState(
        coord=coord,
        path=path,
        trace=trace,
        show_trace=probe_trace_visible(state),
        show_neighbors=probe_neighbors_visible(state),
        highlighted_gluing=highlighted_gluing,
        frame_permutation=frame_permutation,
        frame_signs=frame_signs,
    )


def _runtime_sandbox_state_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundSandboxPieceState:
    if state.sandbox is None:
        return RuntimeTopologyPlaygroundSandboxPieceState()
    origin = state.sandbox.origin
    local_blocks = state.sandbox.local_blocks
    if origin is not None and len(origin) != state.dimension:
        return RuntimeTopologyPlaygroundSandboxPieceState()
    if local_blocks is not None and any(
        len(block) != state.dimension for block in local_blocks
    ):
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


def _runtime_explorer_preset_selection_from_value(
    dimension: int,
    profile: ExplorerTopologyProfile | None,
) -> RuntimeTopologyPlaygroundPresetSelection:
    if profile is None:
        return RuntimeTopologyPlaygroundPresetSelection(source=PRESET_SOURCE_CUSTOM)
    for preset in explorer_presets_for_dimension(dimension):
        if preset.profile == profile:
            return RuntimeTopologyPlaygroundPresetSelection(
                preset_id=preset.preset_id,
                label=preset.label,
                description=preset.description,
                source=PRESET_SOURCE_EXPLORER,
                unsafe=preset.unsafe,
            )
    return RuntimeTopologyPlaygroundPresetSelection(source=PRESET_SOURCE_CUSTOM)


def _runtime_explorer_preset_selection_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundPresetSelection:
    return _runtime_explorer_preset_selection_from_value(
        state.dimension,
        current_explorer_profile(state),
    )


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


def tool_is_play(tool: str) -> bool:
    return canonical_tool_name(tool) == TOOL_PLAY


def sync_shell_state_from_canonical(state: TopologyPlaygroundState) -> None:
    runtime_state = state.canonical_state
    if runtime_state is None:
        return
    # Retained shell fields stay as synchronized compatibility projections for
    # the still-live shell/runtime bridge only. Canonical runtime state remains
    # the input authority via current_* selectors, and only a narrowed subset of
    # shell mirrors still sync here for explicit compatibility readers/tests.
    # Explorer profile/draft now stay canonical-only on the migrated path; the
    # raw shell fields survive only as fallback storage when canonical state is
    # absent.
    settings = ExplorerPlaygroundSettings(
        board_dims=tuple(int(value) for value in runtime_state.axis_sizes),
        piece_set_index=int(runtime_state.launch_settings.piece_set_index),
        speed_level=int(runtime_state.launch_settings.speed_level),
        random_mode_index=int(runtime_state.launch_settings.random_mode_index),
        game_seed=int(runtime_state.launch_settings.game_seed),
        rigid_play_mode=str(runtime_state.launch_settings.rigid_play_mode),
    )
    _remember_play_settings(state, settings, dimension=runtime_state.dimension)
    state.active_tool = runtime_state.active_tool
    state.editor_tool = runtime_state.editor_state.active_tool
    sandbox_state = runtime_state.sandbox_piece_state
    state.sandbox = (
        sandbox_state if _sandbox_visible_in_shell(state, sandbox_state) else None
    )


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


def sync_canonical_playground_state(state: TopologyPlaygroundState) -> None:
    if not uses_general_explorer_editor(state):
        state.canonical_state = None
        return
    explorer_profile = current_explorer_profile(state)
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
            current_selected_boundary_index(state),
        ),
        selected_gluing=current_selected_glue_id(state),
        active_tool=state.active_tool,
        editor_tool=state.editor_tool,
        probe_state=_runtime_probe_state_from_ui(state),
        sandbox_piece_state=_runtime_sandbox_state_from_ui(state),
        launch_settings=_runtime_launch_settings_from_ui(state),
        transport_policy=None,
        preset_metadata=_runtime_preset_metadata_from_ui(state),
        dirty=current_dirty(state),
    )
    if (
        state.canonical_state is None
        or state.canonical_state.dimension != state.dimension
    ):
        state.canonical_state = RuntimeTopologyPlaygroundState(**runtime_kwargs)
    else:
        state.canonical_state = replace(state.canonical_state, **runtime_kwargs)
    sync_shell_state_from_canonical(state)


def _replace_canonical_state(
    state: TopologyPlaygroundState,
    **changes: object,
) -> RuntimeTopologyPlaygroundState | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None or not uses_general_explorer_editor(state):
        return None
    state.canonical_state = replace(runtime_state, **changes)
    sync_shell_state_from_canonical(state)
    return state.canonical_state


def canonical_playground_state(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundState | None:
    runtime_state = state.canonical_state
    if not uses_general_explorer_editor(state) or runtime_state is None:
        return None
    if runtime_state.dimension != state.dimension:
        return None
    return runtime_state


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


def current_play_settings(
    state: TopologyPlaygroundState,
) -> ExplorerPlaygroundSettings | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        return state.play_settings
    return ExplorerPlaygroundSettings(
        board_dims=tuple(int(value) for value in runtime_state.axis_sizes),
        piece_set_index=int(runtime_state.launch_settings.piece_set_index),
        speed_level=int(runtime_state.launch_settings.speed_level),
        random_mode_index=int(runtime_state.launch_settings.random_mode_index),
        game_seed=int(runtime_state.launch_settings.game_seed),
        rigid_play_mode=str(runtime_state.launch_settings.rigid_play_mode),
    )


def current_dirty(state: TopologyPlaygroundState) -> bool:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return bool(runtime_state.dirty)
    return bool(state.dirty)


def set_dirty(state: TopologyPlaygroundState, dirty: bool) -> None:
    normalized = bool(dirty)
    if not uses_general_explorer_editor(state):
        state.dirty = normalized
        return
    runtime_state = state.canonical_state
    if runtime_state is None:
        state.dirty = normalized
        sync_canonical_playground_state(state)
        return
    if runtime_state.dimension != state.dimension:
        state.dirty = normalized
        return
    _replace_canonical_state(state, dirty=normalized)


def replace_play_settings(
    state: TopologyPlaygroundState,
    settings: ExplorerPlaygroundSettings,
) -> None:
    if not uses_general_explorer_editor(state):
        _remember_play_settings(state, settings)
        return
    runtime_state = state.canonical_state
    if runtime_state is None or runtime_state.dimension != state.dimension:
        _remember_play_settings(state, settings)
        if runtime_state is None:
            sync_canonical_playground_state(state)
        return
    axis_sizes = tuple(int(value) for value in settings.board_dims[: state.dimension])
    if len(axis_sizes) != state.dimension or any(value <= 0 for value in axis_sizes):
        axis_sizes = runtime_state.axis_sizes
    _replace_canonical_state(
        state,
        axis_sizes=axis_sizes,
        launch_settings=_runtime_launch_settings_from_value(settings),
        transport_policy=None,
    )


def replace_explorer_profile(
    state: TopologyPlaygroundState,
    explorer_profile: ExplorerTopologyProfile | None,
) -> None:
    if not uses_general_explorer_editor(state):
        state.explorer_profile = explorer_profile
        return
    runtime_state = state.canonical_state
    if runtime_state is None:
        state.explorer_profile = explorer_profile
        sync_canonical_playground_state(state)
        return
    if runtime_state.dimension != state.dimension:
        state.explorer_profile = explorer_profile
        return
    _replace_canonical_state(
        state,
        topology_config=replace(
            runtime_state.topology_config,
            explorer_profile=explorer_profile,
        ),
        preset_metadata=replace(
            runtime_state.preset_metadata,
            explorer_preset=_runtime_explorer_preset_selection_from_value(
                state.dimension,
                explorer_profile,
            ),
        ),
        transport_policy=None,
    )


def replace_explorer_draft(
    state: TopologyPlaygroundState,
    explorer_draft: ExplorerGlueDraft,
) -> None:
    if not uses_general_explorer_editor(state):
        state.explorer_draft = explorer_draft
        return
    runtime_state = state.canonical_state
    if runtime_state is None:
        state.explorer_draft = explorer_draft
        sync_canonical_playground_state(state)
        return
    if runtime_state.dimension != state.dimension:
        state.explorer_draft = explorer_draft
        sync_canonical_playground_state(state)
        return
    _replace_canonical_state(
        state,
        topology_config=replace(
            runtime_state.topology_config,
            gluing_draft=_runtime_draft_from_value(
                dimension=state.dimension,
                draft=explorer_draft,
            ),
        ),
        transport_policy=None,
    )


def update_explorer_draft(
    state: TopologyPlaygroundState,
    *,
    slot_index: int | object = _UNSET,
    source_index: int | object = _UNSET,
    target_index: int | object = _UNSET,
    permutation_index: int | object = _UNSET,
    signs: tuple[int, ...] | object = _UNSET,
) -> ExplorerGlueDraft:
    draft = current_explorer_draft(state) or default_draft_for_dimension(
        state.dimension
    )
    updated = ExplorerGlueDraft(
        slot_index=draft.slot_index if slot_index is _UNSET else int(slot_index),
        source_index=(
            draft.source_index if source_index is _UNSET else int(source_index)
        ),
        target_index=(
            draft.target_index if target_index is _UNSET else int(target_index)
        ),
        permutation_index=(
            draft.permutation_index
            if permutation_index is _UNSET
            else int(permutation_index)
        ),
        signs=draft.signs if signs is _UNSET else tuple(int(value) for value in signs),
    )
    replace_explorer_draft(state, updated)
    return updated


def current_selected_boundary_index(
    state: TopologyPlaygroundState,
) -> int | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return _boundary_index(runtime_state.selected_boundary)
    return state.selected_boundary_index


def set_selected_boundary_index(
    state: TopologyPlaygroundState,
    boundary_index: int | None,
) -> None:
    if not uses_general_explorer_editor(state):
        state.selected_boundary_index = boundary_index
        return
    runtime_state = state.canonical_state
    if runtime_state is None:
        state.selected_boundary_index = boundary_index
        sync_canonical_playground_state(state)
        return
    if runtime_state.dimension != state.dimension:
        state.selected_boundary_index = boundary_index
        return
    _replace_canonical_state(
        state,
        selected_boundary=_boundary_from_index(state.dimension, boundary_index),
    )


def current_selected_glue_id(state: TopologyPlaygroundState) -> str | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.selected_gluing
    return state.selected_glue_id


def set_selected_glue_id(
    state: TopologyPlaygroundState,
    glue_id: str | None,
) -> None:
    if not uses_general_explorer_editor(state):
        state.selected_glue_id = glue_id
        return
    runtime_state = state.canonical_state
    if runtime_state is None:
        state.selected_glue_id = glue_id
        sync_canonical_playground_state(state)
        return
    if runtime_state.dimension != state.dimension:
        state.selected_glue_id = glue_id
        return
    _replace_canonical_state(state, selected_gluing=glue_id)


def current_highlighted_glue_id(state: TopologyPlaygroundState) -> str | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.highlighted_gluing
    return state.highlighted_glue_id


def _normalize_probe_coord_value(
    dimension: int,
    coord: tuple[int, ...] | None,
) -> tuple[int, ...] | None:
    if coord is None:
        return None
    normalized = tuple(int(value) for value in coord)
    if len(normalized) != dimension:
        return None
    return normalized


def _normalize_probe_trace_value(
    trace: list[str] | tuple[str, ...] | None,
) -> tuple[str, ...]:
    return tuple(str(entry) for entry in (trace or ()))


def _normalize_probe_path_value(
    dimension: int,
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
) -> tuple[tuple[int, ...], ...]:
    normalized: list[tuple[int, ...]] = []
    for entry in path or ():
        coord = tuple(int(value) for value in entry)
        if len(coord) == dimension:
            normalized.append(coord)
    return tuple(normalized)


def current_probe_coord(state: TopologyPlaygroundState) -> tuple[int, ...] | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.probe_state.coord
    return None


def current_probe_trace(state: TopologyPlaygroundState) -> list[str]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.trace)
    return []


def probe_trace_visible(state: TopologyPlaygroundState) -> bool:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return bool(runtime_state.probe_state.show_trace)
    return bool(state.probe_show_trace)


def probe_neighbors_visible(state: TopologyPlaygroundState) -> bool:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return bool(runtime_state.probe_state.show_neighbors)
    return bool(state.probe_show_neighbors)


def current_probe_path(state: TopologyPlaygroundState) -> list[tuple[int, ...]]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return list(runtime_state.probe_state.path)
    return []


def current_probe_frame(
    state: TopologyPlaygroundState,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return _normalize_probe_frame_value(
            state.dimension,
            runtime_state.probe_state.frame_permutation,
            runtime_state.probe_state.frame_signs,
        )
    return _normalize_probe_frame_value(
        state.dimension,
        state.probe_frame_permutation,
        state.probe_frame_signs,
    )


def replace_probe_state(
    state: TopologyPlaygroundState,
    *,
    coord: tuple[int, ...] | None,
    trace: list[str] | tuple[str, ...] | None,
    path: list[tuple[int, ...]] | tuple[tuple[int, ...], ...] | None,
    highlighted_glue_id: str | None,
    frame_permutation: tuple[int, ...] | object = _UNSET,
    frame_signs: tuple[int, ...] | object = _UNSET,
) -> None:
    normalized_coord = _normalize_probe_coord_value(state.dimension, coord)
    normalized_trace = _normalize_probe_trace_value(trace)
    normalized_path = _normalize_probe_path_value(state.dimension, path)
    normalized_highlight = (
        None if highlighted_glue_id is None else str(highlighted_glue_id)
    )
    current_permutation, current_signs = current_probe_frame(state)
    normalized_permutation, normalized_signs = _normalize_probe_frame_value(
        state.dimension,
        current_permutation if frame_permutation is _UNSET else frame_permutation,
        current_signs if frame_signs is _UNSET else frame_signs,
    )
    runtime_state = canonical_playground_state(state)
    if runtime_state is None and uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)
        runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=RuntimeTopologyPlaygroundProbeState(
                coord=normalized_coord,
                path=normalized_path,
                trace=normalized_trace,
                show_trace=probe_trace_visible(state),
                show_neighbors=probe_neighbors_visible(state),
                highlighted_gluing=normalized_highlight,
                frame_permutation=normalized_permutation,
                frame_signs=normalized_signs,
            ),
        )
        return
    state.probe_show_trace = probe_trace_visible(state)
    state.probe_show_neighbors = probe_neighbors_visible(state)
    state.probe_frame_permutation = normalized_permutation
    state.probe_frame_signs = normalized_signs
    state.highlighted_glue_id = normalized_highlight


def set_probe_trace_visible(
    state: TopologyPlaygroundState,
    enabled: bool,
) -> None:
    normalized_enabled = bool(enabled)
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=replace(
                runtime_state.probe_state,
                show_trace=normalized_enabled,
            ),
        )
        return
    state.probe_show_trace = normalized_enabled
    if uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)


def set_probe_neighbors_visible(
    state: TopologyPlaygroundState,
    enabled: bool,
) -> None:
    normalized_enabled = bool(enabled)
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        _replace_canonical_state(
            state,
            probe_state=replace(
                runtime_state.probe_state,
                show_neighbors=normalized_enabled,
            ),
        )
        return
    state.probe_show_neighbors = normalized_enabled
    if uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)


def set_highlighted_glue_id(
    state: TopologyPlaygroundState,
    glue_id: str | None,
) -> None:
    replace_probe_state(
        state,
        coord=current_probe_coord(state),
        trace=current_probe_trace(state),
        path=current_probe_path(state),
        highlighted_glue_id=glue_id,
    )


def select_projection_coord(
    state: TopologyPlaygroundState,
    coord: tuple[int, ...],
) -> tuple[int, ...] | None:
    normalized = _normalize_probe_coord_value(state.dimension, coord)
    if normalized is None:
        return None
    dims = playground_dims_for_state(state)
    if any(value < 0 or value >= dims[index] for index, value in enumerate(normalized)):
        return None
    identity_permutation, identity_signs = _identity_probe_frame(state.dimension)
    replace_probe_state(
        state,
        coord=normalized,
        trace=(),
        path=(normalized,),
        highlighted_glue_id=current_highlighted_glue_id(state),
        frame_permutation=identity_permutation,
        frame_signs=identity_signs,
    )
    return normalized


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


def _normalize_probe_support_state(state: TopologyPlaygroundState) -> None:
    state.probe_show_trace = bool(state.probe_show_trace)
    state.probe_show_neighbors = bool(state.probe_show_neighbors)
    state.probe_frame_permutation, state.probe_frame_signs = (
        _normalize_probe_frame_value(
            state.dimension,
            state.probe_frame_permutation,
            state.probe_frame_signs,
        )
    )


def _set_probe_unavailable(
    state: TopologyPlaygroundState,
    *,
    message: str,
) -> None:
    replace_probe_state(
        state,
        coord=None,
        trace=[f"Probe unavailable: {message}"],
        path=[],
        highlighted_glue_id=None,
        frame_permutation=tuple(range(state.dimension)),
        frame_signs=tuple(1 for _ in range(state.dimension)),
    )


def _set_recommended_probe_coord(
    state: TopologyPlaygroundState,
    *,
    profile: ExplorerTopologyProfile,
    dims: tuple[int, ...],
) -> None:
    try:
        probe_coord = recommended_explorer_probe_coord(profile, dims=dims)
    except ValueError as exc:
        _set_probe_unavailable(state, message=str(exc))
        return
    replace_probe_state(
        state,
        coord=probe_coord,
        trace=[],
        path=[probe_coord],
        highlighted_glue_id=None,
        frame_permutation=tuple(range(state.dimension)),
        frame_signs=tuple(1 for _ in range(state.dimension)),
    )


def ensure_probe_state(state: TopologyPlaygroundState) -> None:
    profile = current_explorer_profile(state)
    probe_coord = current_probe_coord(state)
    probe_path = current_probe_path(state)
    needs_default = (
        probe_coord is None or len(probe_coord) != state.dimension or not probe_path
    )
    dims = playground_dims_for_state(state)
    _normalize_probe_support_state(state)
    if profile is None:
        return
    if state.scene_preview_error is not None:
        _set_probe_unavailable(state, message=state.scene_preview_error)
        return
    probe_coord = current_probe_coord(state)
    probe_out_of_bounds = probe_coord is not None and any(
        value < 0 or value >= dims[index] for index, value in enumerate(probe_coord)
    )
    if probe_coord is None or needs_default or probe_out_of_bounds:
        _set_recommended_probe_coord(state, profile=profile, dims=dims)


def reset_probe_state(state: TopologyPlaygroundState) -> None:
    dims = playground_dims_for_state(state)
    probe_coord = tuple(max(0, size // 2) for size in dims)
    frame_permutation, frame_signs = _identity_probe_frame(state.dimension)
    replace_probe_state(
        state,
        coord=probe_coord,
        trace=[],
        path=[probe_coord],
        highlighted_glue_id=None,
        frame_permutation=frame_permutation,
        frame_signs=frame_signs,
    )


def ensure_explorer_draft(state: TopologyPlaygroundState) -> None:
    draft = current_explorer_draft(state)
    if draft is None or len(draft.signs) != state.dimension - 1:
        replace_explorer_draft(state, default_draft_for_dimension(state.dimension))


def ensure_sandbox_state(state: TopologyPlaygroundState) -> None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None and uses_general_explorer_editor(state):
        sync_canonical_playground_state(state)
        runtime_state = canonical_playground_state(state)
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
    "current_highlighted_glue_id",
    "current_play_settings",
    "current_probe_coord",
    "current_probe_frame",
    "current_probe_path",
    "current_probe_trace",
    "probe_neighbors_visible",
    "probe_trace_visible",
    "current_selected_boundary_index",
    "current_selected_glue_id",
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
    "set_highlighted_glue_id",
    "set_selected_boundary_index",
    "set_selected_glue_id",
    "sync_canonical_playground_state",
    "sync_shell_state_from_canonical",
    "tool_is_edit",
    "tool_is_probe",
    "tool_is_play",
    "tool_is_sandbox",
    "update_explorer_draft",
    "uses_general_explorer_editor",
]
