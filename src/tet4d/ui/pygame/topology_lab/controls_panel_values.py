from __future__ import annotations

from tet4d.engine.gameplay.api import (
    piece_set_2d_label_gameplay,
    piece_set_2d_options_gameplay,
    piece_set_label_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.gameplay.topology_designer import designer_profiles_for_dimension
from tet4d.engine.gameplay.topology import topology_mode_label
from tet4d.engine.runtime.topology_playability_signal import resolve_rigid_play_enabled
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer import (
    BoundaryTransform,
    GluingDescriptor,
    tangent_axes_for_boundary,
)
from tet4d.engine.topology_explorer.presets import (
    ExplorerTopologyPreset,
    explorer_presets_for_dimension,
)

from .app import build_explorer_playground_settings
from .common import (
    boundaries_for_dimension,
    permutation_options_for_dimension,
    transform_preview_label,
)
from .controls_panel_rows import _EXPLORER_BOARD_ROW_AXES, _RowSpec
from .piece_sandbox import ensure_piece_sandbox
from .scene_state import (
    TOOL_EDIT,
    TopologyLabState,
    canonical_playground_state,
    current_editor_tool,
    current_explorer_draft,
    current_explorer_profile,
    current_play_settings,
    current_selected_boundary_index,
    current_selected_glue_id,
    playground_dims_for_state,
    probe_neighbors_visible,
    probe_trace_visible,
    uses_general_explorer_editor,
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
_LEGACY_EDGE_LABELS = {
    "bounded": "Bounded",
    "wrap": "Wrap",
    "invert": "Invert",
}


def _mode_value_text(state: TopologyLabState) -> str:
    if state.gameplay_mode == "explorer":
        return "Explorer Playground"
    return "Normal Game (legacy compat)"


def _play_settings_or_defaults(state: TopologyLabState):
    settings = current_play_settings(state)
    if settings is not None:
        return settings
    return build_explorer_playground_settings(dimension=state.dimension)


def _current_playability_analysis(
    state: TopologyLabState,
) -> TopologyPlaygroundPlayabilityAnalysis:
    runtime_state = canonical_playground_state(state)
    if runtime_state is None:
        return TopologyPlaygroundPlayabilityAnalysis()
    return runtime_state.playability_analysis


def _playability_summary_value_text(state: TopologyLabState) -> str:
    summary = _current_playability_analysis(state).summary.strip()
    return summary or "Status unavailable"


def _playability_validity_value_text(state: TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_VALIDITY_LABELS.get(analysis.validity, "Unknown")


def _playability_explorer_value_text(state: TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_EXPLORER_LABELS.get(
        analysis.explorer_usability,
        "Unknown",
    )


def _playability_rigid_value_text(state: TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    return _PLAYABILITY_RIGID_LABELS.get(analysis.rigid_playability, "Unknown")


def _resolved_rigid_play_enabled(state: TopologyLabState) -> bool:
    profile = current_explorer_profile(state)
    if profile is None:
        return True
    settings = _play_settings_or_defaults(state)
    return resolve_rigid_play_enabled(
        profile,
        dims=playground_dims_for_state(state),
        rigid_play_mode=settings.rigid_play_mode,
        analysis=_current_playability_analysis(state),
    )


def _rigid_play_mode_value_text(state: TopologyLabState) -> str:
    mode = _play_settings_or_defaults(state).rigid_play_mode
    if mode == RIGID_PLAY_MODE_ON:
        return "Rigid (Forced)"
    if mode == RIGID_PLAY_MODE_OFF:
        return "Cellwise (Forced)"
    return "Auto (Rigid)" if _resolved_rigid_play_enabled(state) else "Auto (Cellwise)"


def _playability_reason_value_text(state: TopologyLabState) -> str:
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


def _playability_launch_note_text(state: TopologyLabState) -> str:
    analysis = _current_playability_analysis(state)
    if analysis.validity == "invalid":
        return "Play launch stays restricted until the topology validates."
    mode = _play_settings_or_defaults(state).rigid_play_mode
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


def _playability_panel_lines(state: TopologyLabState) -> list[str]:
    return [
        "Topology status",
        f"Validity: {_playability_validity_value_text(state)}",
        f"Explorer: {_playability_explorer_value_text(state)}",
        f"Rigid play: {_playability_rigid_value_text(state)}",
        f"Why: {_playability_reason_value_text(state)}",
        f"Play: {_playability_launch_note_text(state)}",
    ]


def _playability_status_text(state: TopologyLabState) -> str:
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


def _explorer_presets(state: TopologyLabState) -> tuple[ExplorerTopologyPreset, ...]:
    return explorer_presets_for_dimension(state.dimension)


def _explorer_boundaries(state: TopologyLabState):
    if state.scene_boundaries and len(state.scene_boundaries) == state.dimension * 2:
        return state.scene_boundaries
    return boundaries_for_dimension(state.dimension)


def _explorer_permutations(state: TopologyLabState):
    return permutation_options_for_dimension(state.dimension)


def _explorer_glues(state: TopologyLabState) -> tuple[GluingDescriptor, ...]:
    profile = current_explorer_profile(state)
    return () if profile is None else profile.gluings


def _explorer_transform_from_draft(state: TopologyLabState) -> BoundaryTransform:
    draft = current_explorer_draft(state)
    assert draft is not None
    permutation = _explorer_permutations(state)[draft.permutation_index]
    return BoundaryTransform(permutation=permutation, signs=draft.signs)


def _explorer_transform_label(state: TopologyLabState) -> str:
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
    state: TopologyLabState,
) -> tuple[dict[str, object] | None, str | None]:
    if uses_general_explorer_editor(state):
        return state.scene_preview, state.scene_preview_error
    return None, None


def _explorer_active_glue_ids(state: TopologyLabState) -> dict[str, str]:
    if state.scene_active_glue_ids:
        return dict(state.scene_active_glue_ids)
    boundary_status = {
        boundary.label: "free" for boundary in _explorer_boundaries(state)
    }
    for glue in _explorer_glues(state):
        boundary_status[glue.source.label] = glue.glue_id
        boundary_status[glue.target.label] = glue.glue_id
    return boundary_status


def _explorer_glue_labels(state: TopologyLabState) -> tuple[str, ...]:
    return tuple(glue.glue_id for glue in _explorer_glues(state)) + ("new",)


def _explorer_permutation_labels(state: TopologyLabState) -> tuple[str, ...]:
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


def _explorer_preset_index(state: TopologyLabState) -> int:
    profile = current_explorer_profile(state)
    assert profile is not None
    presets = _explorer_presets(state)
    for idx, preset in enumerate(presets):
        if preset.profile == profile:
            return idx
    return 0


def _explorer_preset_value_text(state: TopologyLabState) -> str:
    presets = _explorer_presets(state)
    preset = presets[_explorer_preset_index(state)]
    return preset.label + (" [unsafe]" if preset.unsafe else "")


def _explorer_piece_set_options(state: TopologyLabState) -> tuple[str, ...]:
    if state.dimension == 2:
        return tuple(piece_set_2d_options_gameplay())
    return tuple(piece_set_options_for_dimension_gameplay(state.dimension))


def _explorer_piece_set_index(state: TopologyLabState) -> int:
    settings = _play_settings_or_defaults(state)
    options = _explorer_piece_set_options(state)
    if not options:
        return 0
    return max(0, min(len(options) - 1, int(settings.piece_set_index)))


def _explorer_piece_set_label(state: TopologyLabState) -> str:
    options = _explorer_piece_set_options(state)
    if not options:
        return "-"
    piece_set_id = options[_explorer_piece_set_index(state)]
    if state.dimension == 2:
        return piece_set_2d_label_gameplay(piece_set_id)
    return piece_set_label_gameplay(piece_set_id)


def _sandbox_neighbor_search_enabled(state: TopologyLabState) -> bool:
    ensure_piece_sandbox(state)
    assert state.sandbox is not None
    return bool(state.sandbox.neighbor_search_enabled)


def _sandbox_neighbor_search_value_text(state: TopologyLabState) -> str:
    return "On" if _sandbox_neighbor_search_enabled(state) else "Off"


def _editor_tool_value_text(state: TopologyLabState) -> str:
    if current_editor_tool(state) == TOOL_EDIT:
        return "Edit"
    return "Probe"


def _editor_trace_value_text(state: TopologyLabState) -> str:
    return "On" if probe_trace_visible(state) else "Off"


def _editor_probe_neighbors_value_text(state: TopologyLabState) -> str:
    return "On" if probe_neighbors_visible(state) else "Off"


def _analysis_boundary_value_text(state: TopologyLabState) -> str:
    selected_boundary_index = current_selected_boundary_index(state)
    if selected_boundary_index is None:
        return "none"
    return _explorer_boundaries(state)[selected_boundary_index].label


def _explorer_draft_boundary_value_text(
    state: TopologyLabState,
    key: str,
) -> str:
    draft = current_explorer_draft(state)
    assert draft is not None
    boundary_index = (
        draft.source_index if key == "explorer_source" else draft.target_index
    )
    return _explorer_boundaries(state)[boundary_index].label


_EXPLORER_SCALAR_ROW_VALUE_GETTERS = {
    "editor_tool": _editor_tool_value_text,
    "editor_trace": _editor_trace_value_text,
    "editor_probe_neighbors": _editor_probe_neighbors_value_text,
    "piece_set": _explorer_piece_set_label,
    "speed_level": lambda state: str(_play_settings_or_defaults(state).speed_level),
    "rigid_play_mode": _rigid_play_mode_value_text,
    "sandbox_neighbor_search": _sandbox_neighbor_search_value_text,
    "explorer_preset": _explorer_preset_value_text,
    "playability_summary": _playability_summary_value_text,
    "playability_validity": _playability_validity_value_text,
    "playability_explorer": _playability_explorer_value_text,
    "playability_rigid": _playability_rigid_value_text,
    "playability_reason": _playability_reason_value_text,
    "analysis_boundary": _analysis_boundary_value_text,
    "analysis_glue": lambda state: current_selected_glue_id(state) or "none",
    "analysis_transform": _explorer_transform_label,
}


def _explorer_scalar_row_value_text(state: TopologyLabState, key: str) -> str | None:
    getter = _EXPLORER_SCALAR_ROW_VALUE_GETTERS.get(key)
    if getter is not None:
        return getter(state)
    if key in {"explorer_source", "explorer_target"}:
        return _explorer_draft_boundary_value_text(state, key)
    return None


def _explorer_row_value_text(state: TopologyLabState, row: _RowSpec) -> str | None:
    axis = _EXPLORER_BOARD_ROW_AXES.get(row.key)
    if axis is not None:
        dims = playground_dims_for_state(state)
        return str(dims[axis]) if axis < len(dims) else None
    if row.key.startswith("explorer_sign_"):
        draft = current_explorer_draft(state)
        assert draft is not None
        sign_index = int(row.key.rsplit("_", 1)[1])
        return "Flipped" if draft.signs[sign_index] < 0 else "Straight"
    return _explorer_scalar_row_value_text(state, row.key)


def _legacy_row_value_text(state: TopologyLabState, row: _RowSpec) -> str | None:
    if row.key == "preset":
        profiles = designer_profiles_for_dimension(state.dimension, state.gameplay_mode)
        preset_id = state.profile.preset_id
        if not preset_id:
            return profiles[0].label
        for profile in profiles:
            if profile.profile_id == preset_id:
                return profile.label
        return profiles[0].label
    if row.key == "topology_mode":
        return topology_mode_label(state.profile.topology_mode)
    if row.axis is not None and row.side is not None:
        value = state.profile.edge_rules[row.axis][row.side]
        return _LEGACY_EDGE_LABELS.get(value, str(value).title())
    return None


def _row_value_text(state: TopologyLabState, row: _RowSpec) -> str:
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


__all__ = [
    "_current_playability_analysis",
    "_explorer_active_glue_ids",
    "_explorer_boundaries",
    "_explorer_glue_labels",
    "_explorer_permutation_labels",
    "_explorer_piece_set_label",
    "_explorer_preset_value_text",
    "_explorer_preview_payload",
    "_explorer_presets",
    "_explorer_transform_label",
    "_playability_panel_lines",
    "_playability_status_text",
    "_row_value_text",
    "_sandbox_neighbor_search_enabled",
]
