from __future__ import annotations

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
)
from tet4d.engine.topology_explorer import (
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    validate_topology_structure,
)
from tet4d.engine.topology_explorer.presets import (
    ExplorerTopologyPreset,
    explorer_presets_for_dimension,
)

from .app import (
    build_explorer_playground_settings,
)
from .common import (
    ExplorerGlueDraft,
    default_draft_for_dimension,
    permutation_options_for_dimension,
)
from .controls_panel_rows import (
    _EXPLORER_BOARD_ROW_AXES,
    _RowSpec,
)
from .controls_panel_values import (
    _current_playability_analysis,
    _explorer_boundaries,
    _playability_status_text,
    _sandbox_neighbor_search_enabled,
)
from .copy import LAB_STATUS_COPY as _LAB_STATUS_COPY
from .interaction_audit import (
    record_interaction_handler,
    record_interaction_phase,
)
from .scene_preview_state import (
    preview_signature_for_state as _preview_signature_for_state_impl,
    refresh_explorer_scene_state as _refresh_explorer_scene_state_impl,
)
from .scene_state import (
    ExplorerPlaygroundSettings,
    ExplorerPreviewCompileSignature,
    TOOL_EDIT,
    TOOL_PROBE,
    TopologyLabState,
    canonical_playground_state,
    current_editor_tool,
    current_explorer_draft,
    current_explorer_profile,
    current_play_settings,
    playground_dims_for_state,
    probe_neighbors_visible,
    probe_trace_visible,
    replace_explorer_draft,
    replace_explorer_profile,
    replace_play_settings,
    set_active_tool,
    set_dirty,
    set_highlighted_glue_id,
    set_probe_neighbors_visible,
    set_probe_trace_visible,
    set_selected_boundary_index,
    set_selected_glue_id,
    sync_canonical_playground_state,
    update_explorer_draft,
    uses_general_explorer_editor,
)

_TopologyLabState = TopologyLabState
_EDITOR_TOOL_SEQUENCE = (
    TOOL_PROBE,
    TOOL_EDIT,
)
_RIGID_PLAY_MODE_SEQUENCE = (
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_ON,
    RIGID_PLAY_MODE_OFF,
)


def _set_status(
    state: _TopologyLabState,
    message: str,
    *,
    is_error: bool = False,
) -> None:
    state.status = message
    state.status_error = is_error


def _board_dims_for_state(state: _TopologyLabState) -> tuple[int, ...]:
    return playground_dims_for_state(state)


def _ensure_play_settings(state: _TopologyLabState) -> ExplorerPlaygroundSettings:
    settings = current_play_settings(state)
    if settings is None:
        settings = build_explorer_playground_settings(dimension=state.dimension)
        replace_play_settings(state, settings)
    return settings


def _preview_signature_for_state(
    state: _TopologyLabState,
) -> ExplorerPreviewCompileSignature | None:
    return _preview_signature_for_state_impl(state)


def _refresh_explorer_scene_state(state: _TopologyLabState) -> None:
    _refresh_explorer_scene_state_impl(state)


def _explorer_presets(state: _TopologyLabState) -> tuple[ExplorerTopologyPreset, ...]:
    return explorer_presets_for_dimension(state.dimension)


def _explorer_permutations(state: _TopologyLabState):
    return permutation_options_for_dimension(state.dimension)


def _explorer_glues(state: _TopologyLabState) -> tuple[GluingDescriptor, ...]:
    profile = current_explorer_profile(state)
    return () if profile is None else profile.gluings


def _explorer_transform_from_draft(state: _TopologyLabState) -> BoundaryTransform:
    draft = current_explorer_draft(state)
    assert draft is not None
    permutation = _explorer_permutations(state)[draft.permutation_index]
    return BoundaryTransform(permutation=permutation, signs=draft.signs)


def _explorer_piece_set_options(state: _TopologyLabState) -> tuple[str, ...]:
    if state.dimension == 2:
        return tuple(piece_set_2d_options_gameplay())
    return tuple(piece_set_options_for_dimension_gameplay(state.dimension))


def _explorer_piece_set_index(state: _TopologyLabState) -> int:
    settings = _ensure_play_settings(state)
    options = _explorer_piece_set_options(state)
    if not options:
        return 0
    return max(0, min(len(options) - 1, int(settings.piece_set_index)))


def _explorer_preset_index(state: _TopologyLabState) -> int:
    profile = current_explorer_profile(state)
    assert profile is not None
    presets = _explorer_presets(state)
    for idx, preset in enumerate(presets):
        if preset.profile == profile:
            return idx
    return 0


def _select_explorer_draft_slot(state: _TopologyLabState, slot_index: int) -> None:
    update_explorer_draft(state, slot_index=slot_index)
    glues = _explorer_glues(state)
    highlighted_glue_id: str | None = None
    if slot_index >= len(glues):
        set_selected_glue_id(state, None)
    else:
        selected_glue = glues[slot_index]
        set_selected_glue_id(state, selected_glue.glue_id)
        set_selected_boundary_index(
            state,
            _explorer_boundaries(state).index(selected_glue.source),
        )
        highlighted_glue_id = selected_glue.glue_id
    _normalize_explorer_draft(state)
    set_highlighted_glue_id(state, highlighted_glue_id)


def _set_sandbox_neighbor_search_enabled(
    state: _TopologyLabState,
    *,
    enabled: bool,
) -> None:
    from tet4d.ui.pygame.topology_lab.piece_sandbox import ensure_piece_sandbox

    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    state.sandbox.neighbor_search_enabled = bool(enabled)
    if canonical_playground_state(state) is not None:
        sync_canonical_playground_state(state)
    _set_status(
        state,
        "Sandbox neighbor-search enabled"
        if enabled
        else "Sandbox neighbor-search disabled",
    )


def _mark_play_settings_updated(
    state: _TopologyLabState,
    *,
    previous_signature: ExplorerPreviewCompileSignature | None,
) -> None:
    if uses_general_explorer_editor(state):
        next_signature = _preview_signature_for_state(state)
        if next_signature != previous_signature:
            with record_interaction_phase(
                state,
                "scene_refresh",
                source="mark_play_settings_updated",
                dimension=state.dimension,
            ):
                _refresh_explorer_scene_state(state)
    _set_topology_status_after_refresh(
        state,
        ok_message="Explorer play settings updated",
    )


def _validate_explorer_profile_structure_or_error(
    state: _TopologyLabState,
    profile: ExplorerTopologyProfile,
) -> ExplorerTopologyProfile | None:
    try:
        return validate_topology_structure(profile)
    except ValueError as exc:
        _set_status(state, str(exc), is_error=True)
        return None


def _next_glue_id(state: _TopologyLabState) -> str:
    used = {glue.glue_id for glue in _explorer_glues(state)}
    index = 1
    while True:
        candidate = f"glue_{index:03d}"
        if candidate not in used:
            return candidate
        index += 1


def _cycle_editor_tool_row(state: _TopologyLabState, step: int) -> None:
    current_index = _EDITOR_TOOL_SEQUENCE.index(current_editor_tool(state))
    set_active_tool(
        state,
        _EDITOR_TOOL_SEQUENCE[
            (current_index + step) % len(_EDITOR_TOOL_SEQUENCE)
        ],
    )


def _toggle_editor_trace_row(state: _TopologyLabState) -> None:
    set_probe_trace_visible(state, not probe_trace_visible(state))
    _set_status(
        state,
        "Editor trace shown" if probe_trace_visible(state) else "Editor trace hidden",
    )


def _toggle_editor_probe_neighbors_row(state: _TopologyLabState) -> None:
    set_probe_neighbors_visible(state, not probe_neighbors_visible(state))
    _set_status(
        state,
        (
            "Editor probe neighbors shown"
            if probe_neighbors_visible(state)
            else "Editor probe neighbors hidden"
        ),
    )


def _adjust_explorer_scalar_row(
    state: _TopologyLabState,
    key: str,
    step: int,
) -> bool:
    if key == "editor_tool":
        _cycle_editor_tool_row(state, step)
        return True
    if key == "editor_trace":
        _toggle_editor_trace_row(state)
        return True
    if key == "editor_probe_neighbors":
        _toggle_editor_probe_neighbors_row(state)
        return True
    simple_handlers = {
        "piece_set": lambda: _set_explorer_piece_set_index(state, step),
        "speed_level": lambda: _set_explorer_speed_level(state, step),
        "explorer_preset": lambda: _cycle_explorer_preset(state, step),
        "rigid_play_mode": lambda: _set_explorer_rigid_play_mode(state, step),
        "sandbox_neighbor_search": lambda: _toggle_sandbox_neighbor_search(state),
        "explorer_glue": lambda: _set_explorer_draft_slot(state, step),
        "explorer_permutation": lambda: _cycle_explorer_permutation(state, step),
    }
    handler = simple_handlers.get(key)
    if handler is not None:
        handler()
        return True
    if key in {"explorer_source", "explorer_target"}:
        _cycle_explorer_boundary(state, is_source=(key == "explorer_source"), step=step)
        return True
    return False


def _reset_explorer_play_settings_to_defaults(state: _TopologyLabState) -> None:
    previous_signature = _preview_signature_for_state(state)
    replace_play_settings(
        state,
        build_explorer_playground_settings(dimension=state.dimension),
    )
    _mark_play_settings_updated(
        state,
        previous_signature=previous_signature,
    )
    _set_status(state, f"Explorer {state.dimension}D play settings reset to defaults")


def _normalize_explorer_draft(state: _TopologyLabState) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundaries = _explorer_boundaries(state)
    permutations = _explorer_permutations(state)
    glues = _explorer_glues(state)
    max_slot = len(glues)
    slot_index = max(0, min(draft.slot_index, max_slot))
    source_index = max(0, min(draft.source_index, len(boundaries) - 1))
    target_index = max(0, min(draft.target_index, len(boundaries) - 1))
    permutation_index = max(0, min(draft.permutation_index, len(permutations) - 1))
    signs = tuple(
        -1 if int(value) < 0 else 1 for value in draft.signs[: state.dimension - 1]
    )
    if len(signs) != state.dimension - 1:
        signs = tuple(1 for _ in range(state.dimension - 1))
    if slot_index < len(glues):
        glue = glues[slot_index]
        source_index = boundaries.index(glue.source)
        target_index = boundaries.index(glue.target)
        permutation_index = permutations.index(glue.transform.permutation)
        signs = glue.transform.signs
    update_explorer_draft(
        state,
        slot_index=slot_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=permutation_index,
        signs=signs,
    )


def _toggle_sandbox_neighbor_search(state: _TopologyLabState) -> None:
    _set_sandbox_neighbor_search_enabled(
        state,
        enabled=not _sandbox_neighbor_search_enabled(state),
    )


def _set_explorer_piece_set_index(state: _TopologyLabState, step: int) -> None:
    settings = _ensure_play_settings(state)
    options = _explorer_piece_set_options(state)
    if not options:
        return
    previous_signature = _preview_signature_for_state(state)
    index = (_explorer_piece_set_index(state) + step) % len(options)
    replace_play_settings(
        state,
        ExplorerPlaygroundSettings(
            board_dims=settings.board_dims,
            piece_set_index=index,
            speed_level=settings.speed_level,
            random_mode_index=settings.random_mode_index,
            game_seed=settings.game_seed,
            rigid_play_mode=settings.rigid_play_mode,
        ),
    )
    _mark_play_settings_updated(state, previous_signature=previous_signature)


def _set_explorer_board_dim(state: _TopologyLabState, axis: int, step: int) -> None:
    with record_interaction_handler(
        state,
        "board_size_change",
        axis=axis,
        step=step,
        dimension=state.dimension,
    ):
        settings = _ensure_play_settings(state)
        previous_signature = _preview_signature_for_state(state)
        mins = (4, 6, 2, 1)
        max_size = 40
        dims = list(settings.board_dims)
        while len(dims) < state.dimension:
            dims.append(mins[len(dims)])
        dims[axis] = max(mins[axis], min(max_size, int(dims[axis]) + int(step)))
        replace_play_settings(
            state,
            ExplorerPlaygroundSettings(
                board_dims=tuple(dims[: state.dimension]),
                piece_set_index=settings.piece_set_index,
                speed_level=settings.speed_level,
                random_mode_index=settings.random_mode_index,
                game_seed=settings.game_seed,
                rigid_play_mode=settings.rigid_play_mode,
            ),
        )
        _mark_play_settings_updated(state, previous_signature=previous_signature)


def _set_explorer_speed_level(state: _TopologyLabState, step: int) -> None:
    settings = _ensure_play_settings(state)
    previous_signature = _preview_signature_for_state(state)
    level = max(1, min(10, int(settings.speed_level) + int(step)))
    replace_play_settings(
        state,
        ExplorerPlaygroundSettings(
            board_dims=settings.board_dims,
            piece_set_index=settings.piece_set_index,
            speed_level=level,
            random_mode_index=settings.random_mode_index,
            game_seed=settings.game_seed,
            rigid_play_mode=settings.rigid_play_mode,
        ),
    )
    _mark_play_settings_updated(state, previous_signature=previous_signature)


def _set_explorer_rigid_play_mode(state: _TopologyLabState, step: int) -> None:
    settings = _ensure_play_settings(state)
    previous_signature = _preview_signature_for_state(state)
    current_index = _RIGID_PLAY_MODE_SEQUENCE.index(str(settings.rigid_play_mode))
    next_mode = _RIGID_PLAY_MODE_SEQUENCE[
        (current_index + step) % len(_RIGID_PLAY_MODE_SEQUENCE)
    ]
    replace_play_settings(
        state,
        ExplorerPlaygroundSettings(
            board_dims=settings.board_dims,
            piece_set_index=settings.piece_set_index,
            speed_level=settings.speed_level,
            random_mode_index=settings.random_mode_index,
            game_seed=settings.game_seed,
            rigid_play_mode=next_mode,
        ),
    )
    _mark_play_settings_updated(
        state,
        previous_signature=previous_signature,
    )


def _set_topology_status_after_refresh(
    state: _TopologyLabState,
    *,
    ok_message: str,
) -> None:
    if uses_general_explorer_editor(state):
        analysis = _current_playability_analysis(state)
        status_text = _playability_status_text(state)
        if status_text:
            _set_status(
                state,
                status_text,
                is_error=(analysis.status == "blocked"),
            )
            return
    _set_status(state, ok_message)


def _mark_updated(state: _TopologyLabState) -> None:
    set_dirty(state, True)
    if uses_general_explorer_editor(state):
        with record_interaction_phase(
            state,
            "canonical_sync",
            source="mark_updated",
            dimension=state.dimension,
        ):
            sync_canonical_playground_state(state)
        with record_interaction_phase(
            state,
            "scene_refresh",
            source="mark_updated",
            dimension=state.dimension,
        ):
            _refresh_explorer_scene_state(state)
    _set_topology_status_after_refresh(
        state,
        ok_message=str(_LAB_STATUS_COPY["updated"]),
    )


def _cycle_explorer_preset(state: _TopologyLabState, step: int) -> None:
    with record_interaction_handler(
        state,
        "preset_change",
        step=step,
        dimension=state.dimension,
    ):
        profile = current_explorer_profile(state)
        assert profile is not None
        presets = _explorer_presets(state)
        idx = (_explorer_preset_index(state) + step) % len(presets)
        next_profile = presets[idx].profile
        replace_explorer_profile(state, next_profile)
        draft = default_draft_for_dimension(state.dimension)
        replace_explorer_draft(
            state,
            ExplorerGlueDraft(
                slot_index=len(next_profile.gluings),
                source_index=draft.source_index,
                target_index=draft.target_index,
                permutation_index=draft.permutation_index,
                signs=draft.signs,
            ),
        )
        set_selected_glue_id(state, None)
        set_selected_boundary_index(state, None)
        set_highlighted_glue_id(state, None)
        _normalize_explorer_draft(state)
        _mark_updated(state)


def _set_explorer_draft_slot(state: _TopologyLabState, step: int) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    glues = _explorer_glues(state)
    slot_count = len(glues) + 1
    _select_explorer_draft_slot(
        state,
        (draft.slot_index + step) % slot_count,
    )


def _cycle_explorer_boundary(
    state: _TopologyLabState,
    *,
    is_source: bool,
    step: int,
) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundaries = _explorer_boundaries(state)
    current = draft.source_index if is_source else draft.target_index
    next_index = (current + step) % len(boundaries)
    update_explorer_draft(
        state,
        source_index=next_index if is_source else draft.source_index,
        target_index=draft.target_index if is_source else next_index,
    )
    _normalize_explorer_draft(state)


def _cycle_explorer_permutation(state: _TopologyLabState, step: int) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    options = _explorer_permutations(state)
    update_explorer_draft(
        state,
        permutation_index=(draft.permutation_index + step) % len(options),
    )


def _toggle_explorer_sign(state: _TopologyLabState, sign_index: int) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    signs = list(draft.signs)
    signs[sign_index] *= -1
    update_explorer_draft(state, signs=tuple(signs))


def _adjust_explorer_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    axis = _EXPLORER_BOARD_ROW_AXES.get(row.key)
    if axis is not None:
        _set_explorer_board_dim(state, axis, step)
        return True
    if row.key.startswith("explorer_sign_"):
        _toggle_explorer_sign(state, int(row.key.rsplit("_", 1)[1]))
        return True
    return _adjust_explorer_scalar_row(state, row.key, step)


def _apply_explorer_glue(state: _TopologyLabState) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
    action = "seam_create"
    if draft.slot_index < len(_explorer_glues(state)):
        action = "seam_edit"
    with record_interaction_handler(
        state,
        action,
        slot_index=draft.slot_index,
        dimension=state.dimension,
    ):
        profile = current_explorer_profile(state)
        draft = current_explorer_draft(state)
        assert profile is not None
        assert draft is not None
        boundaries = _explorer_boundaries(state)
        source = boundaries[draft.source_index]
        target = boundaries[draft.target_index]
        transform = _explorer_transform_from_draft(state)
        gluings = list(_explorer_glues(state))
        slot_index = draft.slot_index
        if slot_index < len(gluings):
            glue_id = gluings[slot_index].glue_id
        else:
            glue_id = _next_glue_id(state)
        try:
            glue = GluingDescriptor(
                glue_id=glue_id,
                source=source,
                target=target,
                transform=transform,
            )
        except ValueError as exc:
            _set_status(state, str(exc), is_error=True)
            return
        if slot_index < len(gluings):
            gluings[slot_index] = glue
        else:
            gluings.append(glue)
            slot_index = len(gluings) - 1
        next_profile = ExplorerTopologyProfile(
            dimension=state.dimension,
            gluings=tuple(gluings),
        )
        validated = _validate_explorer_profile_structure_or_error(state, next_profile)
        if validated is None:
            return
        replace_explorer_profile(state, validated)
        set_highlighted_glue_id(state, glue_id)
        replace_explorer_draft(
            state,
            ExplorerGlueDraft(
                slot_index=slot_index,
                source_index=draft.source_index,
                target_index=draft.target_index,
                permutation_index=draft.permutation_index,
                signs=draft.signs,
            ),
        )
        glues = _explorer_glues(state)
        set_selected_glue_id(
            state,
            None if slot_index >= len(glues) else glues[slot_index].glue_id,
        )
        _normalize_explorer_draft(state)
        _mark_updated(state)


def _remove_explorer_glue(state: _TopologyLabState) -> None:
    with record_interaction_handler(
        state,
        "seam_remove",
        dimension=state.dimension,
    ):
        profile = current_explorer_profile(state)
        draft = current_explorer_draft(state)
        assert profile is not None
        assert draft is not None
        gluings = list(_explorer_glues(state))
        if draft.slot_index >= len(gluings):
            _set_status(state, "No active glue selected", is_error=True)
            return
        del gluings[draft.slot_index]
        replace_explorer_profile(
            state,
            ExplorerTopologyProfile(
                dimension=state.dimension,
                gluings=tuple(gluings),
            ),
        )
        set_selected_glue_id(state, None)
        set_highlighted_glue_id(state, None)
        next_slot = min(draft.slot_index, len(gluings))
        replace_explorer_draft(
            state,
            ExplorerGlueDraft(
                slot_index=next_slot,
                source_index=draft.source_index,
                target_index=draft.target_index,
                permutation_index=draft.permutation_index,
                signs=draft.signs,
            ),
        )
        _normalize_explorer_draft(state)
        _mark_updated(state)


__all__ = [
    "_adjust_explorer_row",
    "_apply_explorer_glue",
    "_cycle_explorer_preset",
    "_explorer_presets",
    "_mark_updated",
    "_normalize_explorer_draft",
    "_remove_explorer_glue",
    "_reset_explorer_play_settings_to_defaults",
    "_select_explorer_draft_slot",
    "_set_topology_status_after_refresh",
    "_toggle_explorer_sign",
    "_toggle_sandbox_neighbor_search",
]
