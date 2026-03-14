from __future__ import annotations

from dataclasses import dataclass

import pygame

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    topology_gameplay_mode_label,
)
from tet4d.engine.gameplay.api import (
    piece_set_2d_label_gameplay,
    piece_set_2d_options_gameplay,
    piece_set_label_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview,
    export_explorer_topology_preview,
    recommended_explorer_probe_coord,
)
from tet4d.engine.runtime.topology_explorer_runtime import (
    compile_runtime_explorer_experiments,
    export_runtime_explorer_experiments,
    load_runtime_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_playability_signal import (
    resolve_rigid_play_enabled,
    update_topology_playability_analysis,
)
from tet4d.engine.runtime.topology_explorer_store import save_explorer_topology_profile
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    save_topology_profile,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import (
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    tangent_axes_for_boundary,
    validate_topology_structure,
)
from tet4d.engine.topology_explorer.presets import (
    ExplorerTopologyPreset,
    explorer_presets_for_dimension,
)
from tet4d.ui.pygame.input.key_dispatch import match_bound_action
from tet4d.ui.pygame.keybindings import (
    EXPLORER_KEYS_2D,
    EXPLORER_KEYS_3D,
    EXPLORER_KEYS_4D,
    KEYS_2D,
    KEYS_3D,
    KEYS_4D,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx

from . import legacy_panel_support
from .interaction_audit import (
    record_interaction_handler,
    record_interaction_phase,
)
from tet4d.ui.pygame.topology_lab.camera_controls import (
    ensure_mouse_orbit_state,
    ensure_scene_camera,
    handle_scene_camera_key,
)
from tet4d.ui.pygame.topology_lab.common import (
    ExplorerGlueDraft,
    TopologyLabHitTarget,
    boundaries_for_dimension,
    default_draft_for_dimension,
    permutation_options_for_dimension,
    transform_preview_label,
)
from tet4d.ui.pygame.topology_lab.copy import (
    LAB_STATUS_COPY as _LAB_STATUS_COPY,
    display_title_for_state as _display_title_for_state,
)
from tet4d.ui.pygame.topology_lab.piece_sandbox import (
    cycle_sandbox_piece,
    ensure_piece_sandbox,
    move_sandbox_piece,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    rotate_sandbox_piece_action,
)
from tet4d.ui.pygame.topology_lab.scene_state import (
    ExplorerPlaygroundSettings,
    ExplorerPreviewCompileArtifacts,
    ExplorerPreviewCompileSignature,
    PANE_CONTROLS,
    PANE_SCENE,
    TOOL_EDIT,
    TOOL_INSPECT,
    TOOL_PLAY,
    TOOL_SANDBOX,
    TopologyLabState,
    canonical_playground_state,
    current_explorer_draft,
    current_explorer_profile,
    current_play_settings,
    current_probe_coord,
    current_probe_frame,
    current_probe_path,
    current_probe_trace,
    current_selected_boundary_index,
    current_selected_glue_id,
    cycle_active_pane,
    ensure_explorer_draft,
    ensure_probe_state as ensure_probe_state_runtime,
    playground_dims_for_state,
    replace_explorer_draft,
    replace_explorer_profile,
    replace_play_settings,
    replace_probe_state,
    reset_probe_state,
    set_active_tool,
    set_highlighted_glue_id,
    set_selected_boundary_index,
    set_selected_glue_id,
    sync_canonical_playground_state,
    tool_is_inspect,
    update_explorer_draft,
    uses_general_explorer_editor as uses_general_explorer_editor_runtime,
)
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_settings,
    mode_settings_snapshot_for_dimension,
)
from tet4d.ui.pygame.topology_lab.play_launch import launch_playground_state_gameplay


@dataclass(frozen=True)
class _RowSpec:
    key: str
    label: str
    axis: int | None = None
    side: int | None = None
    disabled: bool = False


_INITIAL_TOOL_BY_GAMEPLAY_MODE = {
    GAMEPLAY_MODE_NORMAL: TOOL_EDIT,
    GAMEPLAY_MODE_EXPLORER: TOOL_SANDBOX,
}
_TopologyLabState = TopologyLabState
_TOPOLOGY_DIMENSIONS = (2, 3, 4)
_TOOL_SHORTCUT_KEYS = {
    pygame.K_e: TOOL_EDIT,
    pygame.K_i: TOOL_INSPECT,
    pygame.K_b: TOOL_SANDBOX,
    pygame.K_p: TOOL_PLAY,
    pygame.K_g: TOOL_EDIT,
    pygame.K_t: TOOL_EDIT,
}
_PROBE_MOVEMENT_TOOLS = {TOOL_INSPECT}
_SANDBOX_STEP_KEYS = {
    pygame.K_LEFT: "x-",
    pygame.K_RIGHT: "x+",
    pygame.K_UP: "y-",
    pygame.K_DOWN: "y+",
    pygame.K_PAGEUP: "y-",
    pygame.K_PAGEDOWN: "y+",
    pygame.K_n: "w-",
    pygame.K_SLASH: "w+",
}
_STATUS_ROW_KEYS = frozenset(
    {
        "playability_summary",
        "playability_validity",
        "playability_explorer",
        "playability_rigid",
        "playability_reason",
        "analysis_boundary",
        "analysis_glue",
        "analysis_transform",
    }
)
_PLAYABILITY_VALIDITY_LABELS = {
    "unknown": "Unknown",
    "valid": "Valid",
    "invalid": "Invalid",
}
_PLAYABILITY_EXPLORER_LABELS = {
    "unknown": "Unknown",
    "cellwise_explorable": "Cellwise explorable",
    "not_explorable": "Not explorable",
}
_PLAYABILITY_RIGID_LABELS = {
    "unknown": "Unknown",
    "rigid_playable": "Rigid-playable",
    "not_rigid_playable": "Not rigid-playable",
}
_RIGID_PLAY_MODE_SEQUENCE = (
    RIGID_PLAY_MODE_AUTO,
    RIGID_PLAY_MODE_ON,
    RIGID_PLAY_MODE_OFF,
)


def _explorer_bindings_for_dimension(dimension: int):
    if int(dimension) == 2:
        return EXPLORER_KEYS_2D
    if int(dimension) == 3:
        return EXPLORER_KEYS_3D
    return EXPLORER_KEYS_4D


def _gameplay_bindings_for_dimension(dimension: int):
    if int(dimension) == 2:
        return KEYS_2D
    if int(dimension) == 3:
        return KEYS_3D
    return KEYS_4D


def _explorer_action_to_step_label(action: str) -> str | None:
    return {
        "move_x_neg": "x-",
        "move_x_pos": "x+",
        "move_up": "y-",
        "move_down": "y+",
        "move_z_neg": "z-",
        "move_z_pos": "z+",
        "move_w_neg": "w-",
        "move_w_pos": "w+",
    }.get(action)


def _board_dims_for_state(state: _TopologyLabState) -> tuple[int, ...]:
    return playground_dims_for_state(state)


def _ensure_play_settings(state: _TopologyLabState) -> ExplorerPlaygroundSettings:
    settings = current_play_settings(state)
    if settings is None:
        settings = build_explorer_playground_settings(dimension=state.dimension)
        replace_play_settings(state, settings)
    return settings


def _configured_explorer_play_settings_for_dimension(
    dimension: int,
) -> ExplorerPlaygroundSettings:
    return build_explorer_playground_settings(
        dimension=dimension,
        source_settings=mode_settings_snapshot_for_dimension(dimension),
    )


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


def _bound_sandbox_rotation_action(state: _TopologyLabState, key: int) -> str | None:
    rotation_actions = ["rotate_xy_pos", "rotate_xy_neg"]
    if state.dimension >= 3:
        rotation_actions.extend(
            (
                "rotate_xz_pos",
                "rotate_xz_neg",
                "rotate_yz_pos",
                "rotate_yz_neg",
            )
        )
    if state.dimension >= 4:
        rotation_actions.extend(
            (
                "rotate_xw_pos",
                "rotate_xw_neg",
                "rotate_yw_pos",
                "rotate_yw_neg",
                "rotate_zw_pos",
                "rotate_zw_neg",
            )
        )
    return match_bound_action(
        key,
        _gameplay_bindings_for_dimension(state.dimension),
        tuple(rotation_actions),
    )


def _bound_explorer_step_label(state: _TopologyLabState, key: int) -> str | None:
    movement_actions = [
        "move_x_neg",
        "move_x_pos",
    ]
    if state.dimension >= 3:
        movement_actions.extend(("move_z_neg", "move_z_pos"))
    if state.dimension >= 4:
        movement_actions.extend(("move_w_neg", "move_w_pos"))
    action = match_bound_action(
        key,
        _gameplay_bindings_for_dimension(state.dimension),
        tuple(movement_actions),
    )
    if action is None:
        action = match_bound_action(
            key,
            _explorer_bindings_for_dimension(state.dimension),
            ("move_up", "move_down"),
        )
    if action is None:
        return None
    return _explorer_action_to_step_label(action)


def _set_status(
    state: _TopologyLabState, message: str, *, is_error: bool = False
) -> None:
    state.status = message
    state.status_error = is_error


def _current_playability_analysis(
    state: _TopologyLabState,
) -> TopologyPlaygroundPlayabilityAnalysis:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        return TopologyPlaygroundPlayabilityAnalysis()
    return runtime_state.playability_analysis


def _playability_summary_value_text(state: _TopologyLabState) -> str:
    summary = _current_playability_analysis(state).summary.strip()
    return summary or "Status unavailable"


def _playability_validity_value_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_VALIDITY_LABELS.get(analysis.validity, "Unknown")


def _playability_explorer_value_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_EXPLORER_LABELS.get(
        analysis.explorer_usability,
        "Unknown",
    )


def _playability_rigid_value_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_RIGID_LABELS.get(analysis.rigid_playability, "Unknown")


def _resolved_rigid_play_enabled(state: _TopologyLabState) -> bool:
    profile = current_explorer_profile(state)
    if profile is None:
        return True
    settings = _ensure_play_settings(state)
    return resolve_rigid_play_enabled(
        profile,
        dims=_board_dims_for_state(state),
        rigid_play_mode=settings.rigid_play_mode,
        analysis=_current_playability_analysis(state),
    )


def _rigid_play_mode_value_text(state: _TopologyLabState) -> str:
    mode = _ensure_play_settings(state).rigid_play_mode
    if mode == RIGID_PLAY_MODE_ON:
        return "Rigid (Forced)"
    if mode == RIGID_PLAY_MODE_OFF:
        return "Cellwise (Forced)"
    return "Auto (Rigid)" if _resolved_rigid_play_enabled(state) else "Auto (Cellwise)"


def _playability_reason_value_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    if analysis.validity == "invalid" and analysis.validity_reason:
        return analysis.validity_reason
    if analysis.rigid_playability == "not_rigid_playable" and analysis.rigid_reason:
        return analysis.rigid_reason
    if analysis.explorer_usability == "not_explorable" and analysis.explorer_reason:
        return analysis.explorer_reason
    return (
        analysis.rigid_reason
        or analysis.validity_reason
        or analysis.explorer_reason
        or "No additional reason"
    )


def _playability_launch_note_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    if analysis.validity == "invalid":
        return "Play launch stays restricted until the topology validates."
    mode = _ensure_play_settings(state).rigid_play_mode
    if mode == RIGID_PLAY_MODE_ON:
        return "Play uses rigid transport because the user forced rigid play."
    if mode == RIGID_PLAY_MODE_OFF:
        return (
            "Play uses cellwise seam transport because the user forced cellwise play."
        )
    if analysis.summary:
        return (
            "Play uses rigid transport automatically for this topology."
            if _resolved_rigid_play_enabled(state)
            else "Play uses cellwise seam transport automatically for this topology."
        )
    return "Play launch status is still being derived."


def _playability_panel_lines(state: _TopologyLabState) -> list[str]:
    lines = [
        "Topology status",
        f"Validity: {_playability_validity_value_text(state)}",
        f"Explorer: {_playability_explorer_value_text(state)}",
        f"Rigid play: {_playability_rigid_value_text(state)}",
        f"Why: {_playability_reason_value_text(state)}",
        f"Play: {_playability_launch_note_text(state)}",
    ]
    return lines


def _playability_status_text(state: _TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    summary = analysis.summary.strip()
    if not summary:
        return ""
    reason = ""
    if analysis.validity == "invalid" and analysis.validity_reason:
        reason = analysis.validity_reason
    elif analysis.rigid_playability == "not_rigid_playable" and analysis.rigid_reason:
        reason = analysis.rigid_reason
    if not reason or reason in summary:
        return summary
    return f"{summary} {reason}"


def _profile_for_state(state: _TopologyLabState) -> TopologyProfileState:
    return load_topology_profile(state.gameplay_mode, state.dimension)


def _sync_profile(state: _TopologyLabState) -> None:
    state.profile = _profile_for_state(state)


def _uses_general_explorer_editor(state: _TopologyLabState) -> bool:
    return uses_general_explorer_editor_runtime(state)


def _clear_explorer_scene_state(state: _TopologyLabState) -> None:
    state.scene_boundaries = ()
    state.scene_preview_dims = ()
    state.scene_active_glue_ids = {}
    state.scene_basis_arrows = ()
    state.scene_preview = None
    state.scene_preview_error = None
    state.scene_preview_signature = None
    state.scene_preview_cache = None
    state.experiment_batch = None


def _preview_signature_for_state(
    state: _TopologyLabState,
) -> ExplorerPreviewCompileSignature | None:
    profile = current_explorer_profile(state)
    if profile is None:
        return None
    # Tool, pane, piece set, and speed only affect live UI state; preview compile
    # output is driven by the effective explorer profile plus board dimensions.
    return ExplorerPreviewCompileSignature(
        profile=profile,
        dims=tuple(int(value) for value in _board_dims_for_state(state)),
    )


def _compile_explorer_preview_payload(
    signature: ExplorerPreviewCompileSignature,
) -> tuple[dict[str, object] | None, str | None]:
    try:
        return (
            compile_explorer_topology_preview(
                signature.profile,
                dims=signature.dims,
                source="topology_lab_live_preview",
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _preview_compile_artifacts(
    state: _TopologyLabState,
    *,
    signature: ExplorerPreviewCompileSignature,
) -> ExplorerPreviewCompileArtifacts:
    cached = state.scene_preview_cache
    if cached is not None and cached.signature == signature:
        return cached
    preview, preview_error = _compile_explorer_preview_payload(signature)
    artifacts = ExplorerPreviewCompileArtifacts(
        signature=signature,
        preview=preview,
        preview_error=preview_error,
    )
    state.scene_preview_cache = artifacts
    return artifacts


def _refresh_explorer_scene_state(state: _TopologyLabState) -> None:
    if not _uses_general_explorer_editor(state):
        _clear_explorer_scene_state(state)
        return
    signature = _preview_signature_for_state(state)
    if signature is None:
        _clear_explorer_scene_state(state)
        return
    boundaries = boundaries_for_dimension(signature.profile.dimension)
    preview_artifacts = _preview_compile_artifacts(state, signature=signature)
    active_glue_ids = {boundary.label: "free" for boundary in boundaries}
    for glue in signature.profile.gluings:
        active_glue_ids[glue.source.label] = glue.glue_id
        active_glue_ids[glue.target.label] = glue.glue_id
    state.scene_boundaries = boundaries
    state.scene_preview_dims = signature.dims
    state.scene_active_glue_ids = active_glue_ids
    state.scene_preview = preview_artifacts.preview
    state.scene_preview_error = preview_artifacts.preview_error
    state.scene_basis_arrows = (
        ()
        if preview_artifacts.preview is None
        else tuple(preview_artifacts.preview.get("basis_arrows", ()))
    )
    if state.scene_preview_signature != signature:
        state.experiment_batch = None
    state.scene_preview_signature = signature
    runtime_state = canonical_playground_state(state)
    if runtime_state is not None:
        update_topology_playability_analysis(
            runtime_state,
            preview=state.scene_preview,
            preview_error=state.scene_preview_error,
        )


def _sync_explorer_state(state: _TopologyLabState) -> None:
    if not _uses_general_explorer_editor(state):
        state.explorer_profile = None
        state.explorer_draft = None
        state.probe_coord = None
        state.probe_trace = None
        state.probe_path = None
        state.canonical_state = None
        state.hovered_boundary_index = None
        state.hovered_glue_id = None
        state.scene_camera = None
        state.scene_mouse_orbit = None
        setattr(state, "sandbox_focus_coord", None)
        setattr(state, "sandbox_focus_trace", [])
        setattr(state, "sandbox_focus_path", [])
        setattr(state, "sandbox_focus_frame_permutation", None)
        setattr(state, "sandbox_focus_frame_signs", None)
        _clear_explorer_scene_state(state)
        return
    replace_explorer_profile(
        state,
        load_runtime_explorer_topology_profile(state.dimension),
    )
    draft = current_explorer_draft(state)
    if draft is None or len(draft.signs) != state.dimension - 1:
        ensure_explorer_draft(state)
    _normalize_explorer_draft(state)
    with record_interaction_phase(
        state,
        "canonical_sync",
        source="sync_explorer_state",
        dimension=state.dimension,
    ):
        sync_canonical_playground_state(state)
    state.scene_camera = ensure_scene_camera(state.dimension, state.scene_camera)
    state.scene_mouse_orbit = ensure_mouse_orbit_state(state.scene_mouse_orbit)
    with record_interaction_phase(
        state,
        "scene_refresh",
        source="sync_explorer_state",
        dimension=state.dimension,
    ):
        _refresh_explorer_scene_state(state)
    with record_interaction_phase(
        state,
        "probe_refresh",
        source="sync_explorer_state",
        dimension=state.dimension,
    ):
        _ensure_probe_state(state)


def _explorer_presets(state: _TopologyLabState) -> tuple[ExplorerTopologyPreset, ...]:
    return explorer_presets_for_dimension(state.dimension)


def _explorer_boundaries(state: _TopologyLabState):
    if state.scene_boundaries and len(state.scene_boundaries) == state.dimension * 2:
        return state.scene_boundaries
    return boundaries_for_dimension(state.dimension)


def _explorer_permutations(state: _TopologyLabState):
    return permutation_options_for_dimension(state.dimension)


def _explorer_glues(state: _TopologyLabState) -> tuple[GluingDescriptor, ...]:
    profile = current_explorer_profile(state)
    return () if profile is None else profile.gluings


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


def _explorer_slot_label(state: _TopologyLabState) -> str:
    draft = current_explorer_draft(state)
    assert draft is not None
    glues = _explorer_glues(state)
    if draft.slot_index >= len(glues):
        return "New glue"
    return glues[draft.slot_index].glue_id


def _explorer_transform_from_draft(state: _TopologyLabState) -> BoundaryTransform:
    draft = current_explorer_draft(state)
    assert draft is not None
    permutation = _explorer_permutations(state)[draft.permutation_index]
    return BoundaryTransform(permutation=permutation, signs=draft.signs)


def _explorer_transform_label(state: _TopologyLabState) -> str:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundaries = _explorer_boundaries(state)
    source = boundaries[draft.source_index]
    target = boundaries[draft.target_index]
    return transform_preview_label(
        source,
        target,
        _explorer_transform_from_draft(state),
    )


def _explorer_preview_payload(
    state: _TopologyLabState,
) -> tuple[dict[str, object] | None, str | None]:
    if _uses_general_explorer_editor(state):
        return state.scene_preview, state.scene_preview_error
    return None, None


def _explorer_active_glue_ids(state: _TopologyLabState) -> dict[str, str]:
    if state.scene_active_glue_ids:
        return dict(state.scene_active_glue_ids)
    boundary_status = {
        boundary.label: "free" for boundary in _explorer_boundaries(state)
    }
    for glue in _explorer_glues(state):
        boundary_status[glue.source.label] = glue.glue_id
        boundary_status[glue.target.label] = glue.glue_id
    return boundary_status


def _explorer_glue_labels(state: _TopologyLabState) -> tuple[str, ...]:
    return tuple(glue.glue_id for glue in _explorer_glues(state)) + ("new",)


def _select_explorer_draft_slot(state: _TopologyLabState, slot_index: int) -> None:
    draft = current_explorer_draft(state)
    assert draft is not None
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


def _explorer_permutation_labels(state: _TopologyLabState) -> tuple[str, ...]:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundaries = _explorer_boundaries(state)
    source = boundaries[draft.source_index]
    target = boundaries[draft.target_index]
    source_axes = tangent_axes_for_boundary(source)
    target_axes = tangent_axes_for_boundary(target)
    labels: list[str] = []
    for permutation in _explorer_permutations(state):
        source_text = ",".join("xyzw"[axis] for axis in source_axes)
        target_text = ",".join("xyzw"[target_axes[index]] for index in permutation)
        labels.append(f"{source_text}->{target_text}")
    return tuple(labels)


def _ensure_probe_state(state: _TopologyLabState) -> None:
    profile = current_explorer_profile(state)
    probe_coord = current_probe_coord(state)
    probe_path = current_probe_path(state)
    needs_default = (
        probe_coord is None or len(probe_coord) != state.dimension or not probe_path
    )
    ensure_probe_state_runtime(state)
    if profile is None:
        return
    if state.scene_preview_error is not None:
        replace_probe_state(
            state,
            coord=None,
            trace=[f"Probe unavailable: {state.scene_preview_error}"],
            path=[],
            highlighted_glue_id=None,
            frame_permutation=tuple(range(state.dimension)),
            frame_signs=tuple(1 for _ in range(state.dimension)),
        )
        return
    dims = _board_dims_for_state(state)
    probe_coord = current_probe_coord(state)
    if (
        probe_coord is None
        or needs_default
        or any(
            value < 0 or value >= dims[index] for index, value in enumerate(probe_coord)
        )
    ):
        try:
            probe_coord = recommended_explorer_probe_coord(
                profile,
                dims=dims,
            )
            replace_probe_state(
                state,
                coord=probe_coord,
                trace=[],
                path=[probe_coord],
                highlighted_glue_id=None,
                frame_permutation=tuple(range(state.dimension)),
                frame_signs=tuple(1 for _ in range(state.dimension)),
            )
        except ValueError as exc:
            replace_probe_state(
                state,
                coord=None,
                trace=[f"Probe unavailable: {exc}"],
                path=[],
                highlighted_glue_id=None,
                frame_permutation=tuple(range(state.dimension)),
                frame_signs=tuple(1 for _ in range(state.dimension)),
            )


def _apply_probe_step(state: _TopologyLabState, step_label: str) -> None:
    with record_interaction_handler(
        state,
        "probe_move",
        step=step_label,
        dimension=state.dimension,
    ):
        profile = current_explorer_profile(state)
        assert profile is not None
        _ensure_probe_state(state)
        probe_coord = current_probe_coord(state)
        if probe_coord is None:
            _set_status(
                state,
                "Inspect mode is unavailable until the current gluing fits the board dimensions",
                is_error=True,
            )
            return
        start = probe_coord
        frame_permutation, frame_signs = current_probe_frame(state)
        try:
            target, result = advance_explorer_probe(
                profile,
                dims=_board_dims_for_state(state),
                coord=probe_coord,
                step_label=step_label,
                frame_permutation=frame_permutation,
                frame_signs=frame_signs,
            )
        except ValueError as exc:
            set_highlighted_glue_id(state, None)
            _set_status(state, str(exc), is_error=True)
            return
        traversal = result.get("traversal")
        highlighted_glue_id = (
            None if traversal is None else str(traversal.get("glue_id"))
        )
        trace = current_probe_trace(state)
        trace.append(str(result["message"]))
        path = current_probe_path(state) or [start]
        if not path or path[-1] != start:
            path.append(start)
        if target != start:
            path.append(target)
        next_frame_permutation = tuple(
            int(value) for value in result.get("frame_permutation", frame_permutation)
        )
        next_frame_signs = tuple(
            int(value) for value in result.get("frame_signs", frame_signs)
        )
        replace_probe_state(
            state,
            coord=target,
            trace=trace[-6:],
            path=path[-20:],
            highlighted_glue_id=highlighted_glue_id,
            frame_permutation=next_frame_permutation,
            frame_signs=next_frame_signs,
        )
        _set_status(
            state,
            str(result["message"]),
            is_error=bool(result.get("blocked", False)),
        )


def _reset_probe(state: _TopologyLabState) -> None:
    profile = current_explorer_profile(state)
    if profile is None:
        reset_probe_state(state)
        _set_status(
            state, f"Inspect reset to {list(current_probe_coord(state) or ())}"
        )
        return
    try:
        probe_coord = recommended_explorer_probe_coord(
            profile,
            dims=_board_dims_for_state(state),
        )
        replace_probe_state(
            state,
            coord=probe_coord,
            trace=[],
            path=[probe_coord],
            highlighted_glue_id=None,
            frame_permutation=tuple(range(state.dimension)),
            frame_signs=tuple(1 for _ in range(state.dimension)),
        )
        _set_status(state, f"Inspect reset to {list(probe_coord)}")
        return
    except ValueError as exc:
        replace_probe_state(
            state,
            coord=None,
            trace=[f"Probe unavailable: {exc}"],
            path=[],
            highlighted_glue_id=None,
            frame_permutation=tuple(range(state.dimension)),
            frame_signs=tuple(1 for _ in range(state.dimension)),
        )
        _set_status(state, str(exc), is_error=True)


def _rows_for_state(state: _TopologyLabState) -> tuple[_RowSpec, ...]:
    if _uses_general_explorer_editor(state):
        rows = [
            _RowSpec("gameplay_mode", "Workspace Path"),
            _RowSpec("dimension", "Dimension"),
            _RowSpec("board_x", "Board X"),
            _RowSpec("board_y", "Board Y"),
        ]
        if state.dimension >= 3:
            rows.append(_RowSpec("board_z", "Board Z"))
        if state.dimension >= 4:
            rows.append(_RowSpec("board_w", "Board W"))
        rows.extend(
            (
                _RowSpec("piece_set", "Piece Set"),
                _RowSpec("speed_level", "Speed"),
                _RowSpec("rigid_play_mode", "Play Transport"),
                _RowSpec("explorer_preset", "Explorer Preset"),
                _RowSpec("playability_summary", "Topology Status"),
                _RowSpec("playability_validity", "Validity"),
                _RowSpec("playability_explorer", "Explorer"),
                _RowSpec("playability_rigid", "Rigid Play"),
                _RowSpec("playability_reason", "Why"),
                _RowSpec("analysis_boundary", "Selected Boundary"),
                _RowSpec("analysis_glue", "Selected Seam"),
                _RowSpec("analysis_transform", "Draft Transform"),
                _RowSpec("save_profile", "Save Profile"),
                _RowSpec("export", "Export Explorer Preview"),
                _RowSpec("experiments", "Build Experiment Pack"),
                _RowSpec("back", "Back"),
            )
        )
        return tuple(rows)

    rows = [
        _RowSpec("gameplay_mode", "Workspace Path"),
        _RowSpec("dimension", "Dimension"),
    ]
    rows.extend(
        _RowSpec(
            spec.key,
            spec.label,
            axis=spec.axis,
            side=spec.side,
            disabled=spec.disabled,
        )
        for spec in legacy_panel_support.legacy_row_specs(state)
    )
    rows.extend(
        (
            _RowSpec("save_profile", "Save Legacy Profile"),
            _RowSpec("export", "Export Legacy Resolved Profile"),
            _RowSpec("back", "Back"),
        )
    )
    return tuple(rows)


def _selectable_row_indexes(state: _TopologyLabState) -> tuple[int, ...]:
    return tuple(
        idx
        for idx, row in enumerate(_rows_for_state(state))
        if not _row_is_status_display(row)
    )


def _mode_value_text(state: _TopologyLabState) -> str:
    if state.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
        return "Explorer Playground"
    return "Normal Game (legacy compat)"


def _explorer_preset_index(state: _TopologyLabState) -> int:
    profile = current_explorer_profile(state)
    assert profile is not None
    presets = _explorer_presets(state)
    for idx, preset in enumerate(presets):
        if preset.profile == profile:
            return idx
    return 0


def _explorer_preset_value_text(state: _TopologyLabState) -> str:
    presets = _explorer_presets(state)
    preset = presets[_explorer_preset_index(state)]
    return preset.label + (" [unsafe]" if preset.unsafe else "")


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


def _explorer_piece_set_label(state: _TopologyLabState) -> str:
    options = _explorer_piece_set_options(state)
    if not options:
        return "-"
    piece_set_id = options[_explorer_piece_set_index(state)]
    if state.dimension == 2:
        return piece_set_2d_label_gameplay(piece_set_id)
    return piece_set_label_gameplay(piece_set_id)


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
        mins = (4, 8, 2, 1)
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


_EXPLORER_BOARD_ROW_AXES = {
    "board_x": 0,
    "board_y": 1,
    "board_z": 2,
    "board_w": 3,
}


def _analysis_boundary_value_text(state: _TopologyLabState) -> str:
    selected_boundary_index = current_selected_boundary_index(state)
    if selected_boundary_index is None:
        return "none"
    return _explorer_boundaries(state)[selected_boundary_index].label


def _explorer_draft_boundary_value_text(
    state: _TopologyLabState,
    key: str,
) -> str:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundary_index = (
        draft.source_index if key == "explorer_source" else draft.target_index
    )
    return _explorer_boundaries(state)[boundary_index].label


_EXPLORER_SCALAR_ROW_VALUE_GETTERS = {
    "piece_set": _explorer_piece_set_label,
    "speed_level": lambda state: str(_ensure_play_settings(state).speed_level),
    "rigid_play_mode": _rigid_play_mode_value_text,
    "explorer_preset": _explorer_preset_value_text,
    "playability_summary": _playability_summary_value_text,
    "playability_validity": _playability_validity_value_text,
    "playability_explorer": _playability_explorer_value_text,
    "playability_rigid": _playability_rigid_value_text,
    "playability_reason": _playability_reason_value_text,
    "analysis_boundary": _analysis_boundary_value_text,
    "analysis_glue": lambda state: current_selected_glue_id(state) or "none",
    "analysis_transform": _explorer_transform_label,
    "explorer_glue": _explorer_slot_label,
    "explorer_permutation": _explorer_transform_label,
}


def _explorer_scalar_row_value_text(state: _TopologyLabState, key: str) -> str | None:
    getter = _EXPLORER_SCALAR_ROW_VALUE_GETTERS.get(key)
    if getter is not None:
        return getter(state)
    if key in {"explorer_source", "explorer_target"}:
        return _explorer_draft_boundary_value_text(state, key)
    return None


def _explorer_row_value_text(state: _TopologyLabState, row: _RowSpec) -> str | None:
    axis = _EXPLORER_BOARD_ROW_AXES.get(row.key)
    if axis is not None:
        dims = _board_dims_for_state(state)
        return str(dims[axis]) if axis < len(dims) else None
    if row.key.startswith("explorer_sign_"):
        draft = current_explorer_draft(state)
        assert draft is not None
        sign_index = int(row.key.rsplit("_", 1)[1])
        return "Flipped" if draft.signs[sign_index] < 0 else "Straight"
    return _explorer_scalar_row_value_text(state, row.key)


def _legacy_row_value_text(state: _TopologyLabState, row: _RowSpec) -> str | None:
    return legacy_panel_support.legacy_row_value_text(
        state,
        key=row.key,
        axis=row.axis,
        side=row.side,
    )


def _row_value_text(state: _TopologyLabState, row: _RowSpec) -> str:
    if row.key == "gameplay_mode":
        return _mode_value_text(state)
    if row.key == "dimension":
        return f"{state.dimension}D"
    explorer_value = _explorer_row_value_text(state, row)
    if explorer_value is not None:
        return explorer_value
    legacy_value = _legacy_row_value_text(state, row)
    if legacy_value is not None:
        return legacy_value
    return ""


def _set_topology_status_after_refresh(
    state: _TopologyLabState,
    *,
    ok_message: str,
) -> None:
    if _uses_general_explorer_editor(state):
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
    state.dirty = True
    if _uses_general_explorer_editor(state):
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


def _mark_play_settings_updated(
    state: _TopologyLabState,
    *,
    previous_signature: ExplorerPreviewCompileSignature | None,
) -> None:
    if _uses_general_explorer_editor(state):
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


def _apply_profile(state: _TopologyLabState, profile: TopologyProfileState) -> None:
    state.profile = profile
    _mark_updated(state)


def _reset_to_mode_dimension(state: _TopologyLabState) -> None:
    _sync_profile(state)
    _sync_explorer_state(state)
    state.dirty = False
    _set_status(state, "")


def _cycle_gameplay_mode(state: _TopologyLabState, step: int) -> None:
    idx = TOPOLOGY_GAMEPLAY_MODE_OPTIONS.index(state.gameplay_mode)
    state.gameplay_mode = TOPOLOGY_GAMEPLAY_MODE_OPTIONS[
        (idx + step) % len(TOPOLOGY_GAMEPLAY_MODE_OPTIONS)
    ]
    _sync_profile(state)
    _sync_explorer_state(state)
    _mark_updated(state)


def _cycle_dimension(state: _TopologyLabState, step: int) -> None:
    with record_interaction_handler(
        state,
        "dimension_change",
        step=step,
        previous_dimension=state.dimension,
    ):
        previous_dimension = state.dimension
        previous_settings = current_play_settings(state)
        if previous_settings is not None:
            state.play_settings_by_dimension[previous_dimension] = previous_settings
        idx = _TOPOLOGY_DIMENSIONS.index(state.dimension)
        state.dimension = _TOPOLOGY_DIMENSIONS[(idx + step) % len(_TOPOLOGY_DIMENSIONS)]
        state.dirty = True
        state.sandbox = None
        setattr(state, "sandbox_focus_coord", None)
        setattr(state, "sandbox_focus_trace", [])
        setattr(state, "sandbox_focus_path", [])
        setattr(state, "sandbox_focus_frame_permutation", None)
        setattr(state, "sandbox_focus_frame_signs", None)
        _sync_profile(state)
        if state.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
            next_settings = state.play_settings_by_dimension.get(state.dimension)
            if next_settings is None:
                next_settings = _configured_explorer_play_settings_for_dimension(
                    state.dimension,
                )
            replace_play_settings(state, next_settings)
        _sync_explorer_state(state)
        _set_topology_status_after_refresh(
            state,
            ok_message=str(_LAB_STATUS_COPY["updated"]),
        )


def _apply_legacy_row_adjustment(
    state: _TopologyLabState,
    *,
    key: str,
    axis: int | None,
    side: int | None,
    disabled: bool,
    step: int,
) -> bool:
    result = legacy_panel_support.adjust_legacy_row(
        state,
        key=key,
        axis=axis,
        side=side,
        disabled=disabled,
        step=step,
        locked_message=str(_LAB_STATUS_COPY["locked"]),
    )
    if not result.handled:
        return False
    if result.error is not None:
        _set_status(state, result.error, is_error=True)
        return True
    assert result.profile is not None
    _apply_profile(state, result.profile)
    return True


def _cycle_preset(state: _TopologyLabState, step: int) -> None:
    _apply_legacy_row_adjustment(
        state,
        key="preset",
        axis=None,
        side=None,
        disabled=False,
        step=step,
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


def _cycle_topology_mode(state: _TopologyLabState, step: int) -> None:
    _apply_legacy_row_adjustment(
        state,
        key="topology_mode",
        axis=None,
        side=None,
        disabled=False,
        step=step,
    )


def _cycle_edge_rule(state: _TopologyLabState, row: _RowSpec, step: int) -> None:
    _apply_legacy_row_adjustment(
        state,
        key=row.key,
        axis=row.axis,
        side=row.side,
        disabled=row.disabled,
        step=step,
    )


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
    state: _TopologyLabState, *, is_source: bool, step: int
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


def _save_profile(state: _TopologyLabState) -> tuple[bool, str]:
    if _uses_general_explorer_editor(state):
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = save_explorer_topology_profile(profile)
    else:
        ok, message = save_topology_profile(state.profile)
    if ok:
        state.dirty = False
        _set_status(
            state,
            str(_LAB_STATUS_COPY["saved"]).format(
                mode_label=topology_gameplay_mode_label(state.gameplay_mode),
                dimension=state.dimension,
            ),
        )
        return True, message
    _set_status(
        state,
        str(_LAB_STATUS_COPY["save_failed"]).format(message=message),
        is_error=True,
    )
    return False, message


def _run_export(state: _TopologyLabState) -> None:
    with record_interaction_handler(
        state,
        "preview_export",
        dimension=state.dimension,
        gameplay_mode=state.gameplay_mode,
    ):
        if _uses_general_explorer_editor(state):
            profile = current_explorer_profile(state)
            assert profile is not None
            if state.scene_preview_error is not None:
                _set_status(state, state.scene_preview_error, is_error=True)
                return
            live_preview_payload = None
            export_signature = _preview_signature_for_state(state)
            if (
                export_signature is not None
                and state.scene_preview_signature == export_signature
                and state.scene_preview_error is None
                and state.scene_preview is not None
            ):
                live_preview_payload = state.scene_preview
            with record_interaction_phase(
                state,
                "preview_export_call",
                dimension=state.dimension,
                dims=_board_dims_for_state(state),
                glue_count=len(profile.gluings),
            ):
                ok, message, _path = export_explorer_topology_preview(
                    profile,
                    dims=_board_dims_for_state(state),
                    source=f"topology_lab_{state.dimension}d_mvp",
                    preview_payload=live_preview_payload,
                )
            if not ok:
                _set_status(
                    state,
                    str(_LAB_STATUS_COPY["export_error"]).format(message=message),
                    is_error=True,
                )
                return
            _set_status(
                state, str(_LAB_STATUS_COPY["export_ok"]).format(message=message)
            )
            play_sfx("menu_confirm")
            return

        with record_interaction_phase(
            state,
            "legacy_export_call",
            dimension=state.dimension,
            gameplay_mode=state.gameplay_mode,
        ):
            result = legacy_panel_support.export_legacy_profile(state.profile)
        if not result.ok:
            _set_status(
                state,
                str(_LAB_STATUS_COPY["export_error"]).format(message=result.error),
                is_error=True,
            )
            return

        status_lines = [
            str(_LAB_STATUS_COPY["export_ok"]).format(message=message)
            for message in result.status_lines
        ]
        _set_status(state, " | ".join(status_lines))
        play_sfx("menu_confirm")


def _run_experiments(state: _TopologyLabState) -> None:
    with record_interaction_handler(
        state,
        "experiment_pack_generation",
        dimension=state.dimension,
        gameplay_mode=state.gameplay_mode,
    ):
        if not _uses_general_explorer_editor(state):
            _set_status(
                state,
                "Experiment packs are only available in Explorer Playground",
                is_error=True,
            )
            return
        profile = current_explorer_profile(state)
        assert profile is not None
        if state.scene_preview_error is not None:
            _set_status(state, state.scene_preview_error, is_error=True)
            return
        dims = _board_dims_for_state(state)
        with record_interaction_phase(
            state,
            "experiment_compile",
            dimension=state.dimension,
            dims=dims,
            glue_count=len(profile.gluings),
        ):
            batch = compile_runtime_explorer_experiments(
                profile,
                dims=dims,
                source=f"topology_lab_{state.dimension}d_experiments",
            )
        state.experiment_batch = batch
        with record_interaction_phase(
            state,
            "experiment_export",
            dimension=state.dimension,
            dims=dims,
            glue_count=len(profile.gluings),
        ):
            ok, message, _path = export_runtime_explorer_experiments(
                profile,
                dims=dims,
                source=f"topology_lab_{state.dimension}d_experiments",
                batch_payload=batch,
            )
        recommendation = batch.get("recommendation")
        if not ok:
            _set_status(
                state,
                str(
                    _LAB_STATUS_COPY.get(
                        "experiments_error",
                        "Failed exporting explorer experiment pack: {message}",
                    )
                ).format(message=message),
                is_error=True,
            )
            return
        status = str(
            _LAB_STATUS_COPY.get(
                "experiments_ok",
                "Explorer experiment pack ready: {message}",
            )
        ).format(message=message)
        if isinstance(recommendation, dict):
            status += (
                f" | Next: {recommendation.get('label', 'n/a')}"
                f" ({recommendation.get('reason', 'no reason')})"
            )
        _set_status(state, status)
        play_sfx("menu_confirm")


def _adjust_explorer_scalar_row(state: _TopologyLabState, key: str, step: int) -> bool:
    if key == "piece_set":
        _set_explorer_piece_set_index(state, step)
        return True
    if key == "speed_level":
        _set_explorer_speed_level(state, step)
        return True
    if key == "explorer_preset":
        _cycle_explorer_preset(state, step)
        return True
    if key == "rigid_play_mode":
        _set_explorer_rigid_play_mode(state, step)
        return True
    if key == "explorer_glue":
        _set_explorer_draft_slot(state, step)
        return True
    if key in {"explorer_source", "explorer_target"}:
        _cycle_explorer_boundary(state, is_source=(key == "explorer_source"), step=step)
        return True
    if key == "explorer_permutation":
        _cycle_explorer_permutation(state, step)
        return True
    return False


def _adjust_explorer_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    axis = _EXPLORER_BOARD_ROW_AXES.get(row.key)
    if axis is not None:
        _set_explorer_board_dim(state, axis, step)
        return True
    if row.key.startswith("explorer_sign_"):
        _toggle_explorer_sign(state, int(row.key.rsplit("_", 1)[1]))
        return True
    return _adjust_explorer_scalar_row(state, row.key, step)


def _adjust_legacy_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    return _apply_legacy_row_adjustment(
        state,
        key=row.key,
        axis=row.axis,
        side=row.side,
        disabled=row.disabled,
        step=step,
    )


def _adjust_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    if row.disabled:
        return False
    if row.key == "gameplay_mode":
        _cycle_gameplay_mode(state, step)
        return True
    if row.key == "dimension":
        _cycle_dimension(state, step)
        return True
    if _adjust_explorer_row(state, row, step):
        return True
    if _adjust_legacy_row(state, row, step):
        return True
    return False


def _row_supports_step_adjustment(row: _RowSpec) -> bool:
    return (
        (not row.disabled)
        and (not _row_is_status_display(row))
        and row.key
        not in {
            "analysis_boundary",
            "analysis_glue",
            "analysis_transform",
            "apply_glue",
            "remove_glue",
            "save_profile",
            "export",
            "experiments",
            "back",
        }
    )


def _row_is_status_display(row: _RowSpec) -> bool:
    return row.key in _STATUS_ROW_KEYS


def _adjust_active_row(state: _TopologyLabState, step: int) -> bool:
    row = _rows_for_state(state)[_selectable_row_indexes(state)[state.selected]]
    return _adjust_row(state, row, step)


def _controls_pane_active(state: _TopologyLabState) -> bool:
    return state.active_pane == PANE_CONTROLS


def _scene_pane_active(state: _TopologyLabState) -> bool:
    return state.active_pane == PANE_SCENE


def _set_active_pane_from_target(
    state: _TopologyLabState, target: TopologyLabHitTarget
) -> None:
    if target.kind in {"row_select", "row_step"}:
        state.active_pane = PANE_CONTROLS
    else:
        state.active_pane = PANE_SCENE


def _handle_navigation_key(
    state: _TopologyLabState, nav_key: int, selectable: tuple[int, ...]
) -> bool:
    if not _controls_pane_active(state):
        return False
    if nav_key == pygame.K_UP:
        state.selected = (state.selected - 1) % len(selectable)
        play_sfx("menu_move")
        return True
    if nav_key == pygame.K_DOWN:
        state.selected = (state.selected + 1) % len(selectable)
        play_sfx("menu_move")
        return True
    if nav_key in (pygame.K_LEFT, pygame.K_RIGHT):
        step = -1 if nav_key == pygame.K_LEFT else 1
        if _adjust_active_row(state, step):
            play_sfx("menu_move")
        return True
    return False


def _handle_save_export_shortcut(state: _TopologyLabState, key: int) -> bool:
    if _scene_pane_active(state):
        return False
    if key == pygame.K_s:
        _save_profile(state)
        return True
    if key == pygame.K_e:
        _run_export(state)
        return True
    return False


def _handle_tool_shortcut(state: _TopologyLabState, key: int, *, mod: int = 0) -> bool:
    if not _uses_general_explorer_editor(state):
        return False
    if key == pygame.K_TAB:
        cycle_active_pane(state, -1 if (mod & pygame.KMOD_SHIFT) else 1)
        return True
    tool_name = _TOOL_SHORTCUT_KEYS.get(key)
    if tool_name is not None:
        set_active_tool(state, tool_name)
        state.active_pane = PANE_SCENE
        return True
    if key == pygame.K_F5:
        state.active_pane = PANE_SCENE
        state.play_preview_requested = True
        return True
    return False


def _apply_sandbox_shortcut_step(state: _TopologyLabState, step_label: str) -> None:
    profile = current_explorer_profile(state)
    assert profile is not None
    ok, message = move_sandbox_piece(state, profile, step_label)
    _set_status(state, message, is_error=not ok)


def _sandbox_piece_cycle_step(key: int) -> int | None:
    if key == pygame.K_LEFTBRACKET:
        return -1
    if key in (pygame.K_RIGHTBRACKET, pygame.K_SPACE):
        return 1
    return None


def _handle_probe_shortcut(state: _TopologyLabState, key: int) -> bool:
    if (
        state.active_tool not in _PROBE_MOVEMENT_TOOLS
        or not _uses_general_explorer_editor(state)
        or not _scene_pane_active(state)
    ):
        return False
    step_label = _bound_explorer_step_label(state, key)
    if step_label is None:
        step_label = _SANDBOX_STEP_KEYS.get(key)
    if step_label is None:
        return False
    _apply_probe_step(state, step_label)
    return True


def _handle_sandbox_shortcut(state: _TopologyLabState, key: int) -> bool:
    if (
        state.active_tool != TOOL_SANDBOX
        or not _uses_general_explorer_editor(state)
        or not _scene_pane_active(state)
    ):
        return False
    step_label = _bound_explorer_step_label(state, key)
    if step_label is None:
        step_label = _SANDBOX_STEP_KEYS.get(key)
    if step_label is not None:
        _apply_sandbox_shortcut_step(state, step_label)
        return True
    rotation_action = _bound_sandbox_rotation_action(state, key)
    if rotation_action is not None:
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = rotate_sandbox_piece_action(state, profile, rotation_action)
        _set_status(state, message, is_error=not ok)
        return True
    if key == pygame.K_r:
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = rotate_sandbox_piece(state, profile)
        _set_status(state, message, is_error=not ok)
        return True
    cycle_step = _sandbox_piece_cycle_step(key)
    if cycle_step is not None:
        cycle_sandbox_piece(state, cycle_step)
        return True
    if key == pygame.K_0:
        reset_sandbox_piece(state)
        _set_status(state, "Sandbox reset")
        return True
    if key == pygame.K_t:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.show_trace = not state.sandbox.show_trace
        _set_status(
            state, f"Sandbox trace {'shown' if state.sandbox.show_trace else 'hidden'}"
        )
        return True
    return False


def _handle_glue_shortcut(state: _TopologyLabState, key: int) -> bool:
    if not _uses_general_explorer_editor(state):
        return False
    if key not in (pygame.K_DELETE, pygame.K_BACKSPACE):
        return False
    _remove_explorer_glue(state)
    return True


def _handle_reset_defaults_shortcut(state: _TopologyLabState, key: int) -> bool:
    if key != pygame.K_F8 or not _uses_general_explorer_editor(state):
        return False
    _reset_explorer_play_settings_to_defaults(state)
    return True


def _handle_camera_shortcut(state: _TopologyLabState, key: int) -> bool:
    if (
        not _uses_general_explorer_editor(state)
        or not _scene_pane_active(state)
        or not tool_is_inspect(state.active_tool)
    ):
        return False
    return handle_scene_camera_key(state.dimension, key, state.scene_camera)


def _handle_shortcut_key(state: _TopologyLabState, key: int, *, mod: int = 0) -> bool:
    return (
        _handle_camera_shortcut(state, key)
        or _handle_probe_shortcut(state, key)
        or _handle_reset_defaults_shortcut(state, key)
        or _handle_sandbox_shortcut(state, key)
        or _handle_save_export_shortcut(state, key)
        or _handle_tool_shortcut(state, key, mod=mod)
        or _handle_glue_shortcut(state, key)
    )


def _handle_enter_key(state: _TopologyLabState, selectable: tuple[int, ...]) -> None:
    if _scene_pane_active(state):
        if _uses_general_explorer_editor(state) and state.active_tool == TOOL_PLAY:
            state.play_preview_requested = True
        return
    row = _rows_for_state(state)[selectable[state.selected]]
    if row.key == "save_profile":
        _save_profile(state)
        return
    if row.key == "export":
        _run_export(state)
        return
    if row.key == "experiments":
        _run_experiments(state)
        return
    if row.key == "apply_glue":
        _apply_explorer_glue(state)
        return
    if row.key == "remove_glue":
        _remove_explorer_glue(state)
        return
    if row.key == "back":
        state.running = False
        return
    if _adjust_active_row(state, 1):
        play_sfx("menu_move")


def _launch_play_preview(
    state: _TopologyLabState,
    screen: pygame.Surface,
    fonts_nd,
    *,
    fonts_2d=None,
    display_settings=None,
) -> tuple[pygame.Surface, object | None]:
    with record_interaction_handler(
        state,
        "play_preview_launch",
        dimension=state.dimension,
        glue_count=len(_explorer_glues(state)),
    ):
        runtime_state = canonical_playground_state(state)
        if _uses_general_explorer_editor(state):
            if runtime_state is None:
                with record_interaction_phase(
                    state,
                    "canonical_sync",
                    source="play_preview_launch",
                    dimension=state.dimension,
                ):
                    sync_canonical_playground_state(state)
                runtime_state = canonical_playground_state(state)
            expected_signature = _preview_signature_for_state(state)
            if runtime_state is not None and (
                state.scene_preview_signature != expected_signature
                or state.scene_preview_error is not None
            ):
                with record_interaction_phase(
                    state,
                    "scene_refresh",
                    source="play_preview_launch",
                    dimension=state.dimension,
                ):
                    _refresh_explorer_scene_state(state)
                runtime_state = canonical_playground_state(state)
        if not _uses_general_explorer_editor(state) or runtime_state is None:
            _set_status(
                state,
                "Play preview is unavailable until the canonical playground state is ready",
                is_error=True,
            )
            return screen, display_settings
        if state.scene_preview_error:
            _set_status(
                state,
                f"Cannot play current topology: {state.scene_preview_error}",
                is_error=True,
            )
            return screen, display_settings
        try:
            with record_interaction_phase(
                state,
                "play_launch",
                dimension=state.dimension,
                dims=_board_dims_for_state(state),
                glue_count=len(runtime_state.explorer_profile.gluings),
            ):
                screen, display_settings = launch_playground_state_gameplay(
                    runtime_state,
                    screen,
                    fonts_nd,
                    return_caption=_display_title_for_state(state),
                    fonts_2d=fonts_2d,
                    display_settings=display_settings,
                )
        except Exception as exc:
            _set_status(state, f"Play preview failed: {exc}", is_error=True)
            return screen, display_settings
        _set_status(state, f"Returned from Explorer {state.dimension}D play preview")
        return screen, display_settings
