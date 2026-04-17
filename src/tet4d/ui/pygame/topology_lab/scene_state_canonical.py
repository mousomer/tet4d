from __future__ import annotations

from dataclasses import replace

from tet4d.engine.gameplay.topology_designer import designer_profiles_for_dimension
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.runtime.topology_playground_state import (
    PRESET_SOURCE_CUSTOM,
    PRESET_SOURCE_DESIGNER,
    PRESET_SOURCE_EXPLORER,
    TopologyPlaygroundLaunchSettings as RuntimeTopologyPlaygroundLaunchSettings,
    TopologyPlaygroundPresetMetadata as RuntimeTopologyPlaygroundPresetMetadata,
    TopologyPlaygroundPresetSelection as RuntimeTopologyPlaygroundPresetSelection,
    TopologyPlaygroundSandboxPieceState as RuntimeTopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundState as RuntimeTopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig as RuntimeTopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.engine.topology_explorer.presets import explorer_presets_for_dimension

from .common import default_draft_for_dimension
from .scene_state import (
    ExplorerPlaygroundSettings,
    TopologyPlaygroundState,
    _boundary_from_index,
    _boundary_index,
    _remember_play_settings,
    _runtime_draft_from_value,
    _runtime_launch_settings_from_value,
    _sandbox_visible_in_shell,
    _ui_draft_from_runtime,
    uses_general_explorer_editor,
)

_UNSET = object()


def _runtime_draft_from_ui(
    state: TopologyPlaygroundState,
):
    return _runtime_draft_from_value(
        dimension=state.dimension,
        draft=current_explorer_draft(state),
    )


def _runtime_launch_settings_from_ui(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundLaunchSettings:
    return _runtime_launch_settings_from_value(current_play_settings(state))


def _axis_sizes_from_ui(state: TopologyPlaygroundState) -> tuple[int, ...]:
    settings = current_play_settings(state)
    if settings is not None:
        dims = tuple(int(value) for value in settings.board_dims[: state.dimension])
        if len(dims) == state.dimension and all(value > 0 for value in dims):
            return dims
    if (
        state.canonical_state is not None
        and len(state.canonical_state.axis_sizes) == state.dimension
    ):
        return tuple(int(value) for value in state.canonical_state.axis_sizes)
    return explorer_topology_preview_dims(state.dimension)


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


def sync_shell_state_from_canonical(state: TopologyPlaygroundState) -> None:
    runtime_state = state.canonical_state
    if runtime_state is None:
        return
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


def canonical_playground_state(
    state: TopologyPlaygroundState,
) -> RuntimeTopologyPlaygroundState | None:
    runtime_state = state.canonical_state
    if not uses_general_explorer_editor(state) or runtime_state is None:
        return None
    if runtime_state.dimension != state.dimension:
        return None
    return runtime_state


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


def _runtime_state_for_write(
    state: TopologyPlaygroundState,
    *,
    sync_if_missing: bool = False,
) -> RuntimeTopologyPlaygroundState | None:
    if not uses_general_explorer_editor(state):
        return None
    runtime_state = state.canonical_state
    if runtime_state is None and sync_if_missing:
        sync_canonical_playground_state(state)
        runtime_state = state.canonical_state
    if runtime_state is None or runtime_state.dimension != state.dimension:
        return None
    return runtime_state


def current_explorer_profile(
    state: TopologyPlaygroundState,
) -> ExplorerTopologyProfile | None:
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        return runtime_state.explorer_profile
    return state.explorer_profile


def current_explorer_draft(state: TopologyPlaygroundState):
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


def sync_canonical_playground_state(state: TopologyPlaygroundState) -> None:
    if not uses_general_explorer_editor(state):
        state.canonical_state = None
        return
    from .scene_state_probe import _runtime_probe_state_from_ui

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


def set_dirty(state: TopologyPlaygroundState, dirty: bool) -> None:
    normalized = bool(dirty)
    if not uses_general_explorer_editor(state):
        state.dirty = normalized
        return
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None and state.canonical_state is None:
        state.dirty = normalized
        sync_canonical_playground_state(state)
        return
    if runtime_state is None:
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
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None:
        _remember_play_settings(state, settings)
        if state.canonical_state is None:
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
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None and state.canonical_state is None:
        state.explorer_profile = explorer_profile
        sync_canonical_playground_state(state)
        return
    if runtime_state is None:
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


def replace_explorer_draft(state: TopologyPlaygroundState, explorer_draft) -> None:
    if not uses_general_explorer_editor(state):
        state.explorer_draft = explorer_draft
        return
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None and state.canonical_state is None:
        state.explorer_draft = explorer_draft
        sync_canonical_playground_state(state)
        return
    if runtime_state is None:
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
):
    draft = current_explorer_draft(state) or default_draft_for_dimension(state.dimension)
    updated = type(draft)(
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
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None and state.canonical_state is None:
        state.selected_boundary_index = boundary_index
        sync_canonical_playground_state(state)
        return
    if runtime_state is None:
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
    runtime_state = _runtime_state_for_write(state)
    if runtime_state is None and state.canonical_state is None:
        state.selected_glue_id = glue_id
        sync_canonical_playground_state(state)
        return
    if runtime_state is None:
        state.selected_glue_id = glue_id
        return
    _replace_canonical_state(state, selected_gluing=glue_id)

