from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

from tet4d.engine.gameplay.topology import (
    EDGE_BEHAVIOR_OPTIONS,
    default_edge_rules_for_mode,
    topology_mode_from_index,
    topology_mode_label,
)
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    designer_profiles_for_dimension,
    export_topology_profile_state,
    profile_state_from_preset,
    topology_gameplay_mode_label,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.api import topology_lab_menu_payload_runtime
from tet4d.engine.runtime.project_config import explorer_topology_preview_dims
from tet4d.engine.runtime.topology_explorer_runtime import (
    export_explorer_preview_from_profile_state,
    load_runtime_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview,
    explorer_probe_options,
    export_explorer_topology_preview,
    recommended_explorer_probe_coord,
)
from tet4d.engine.runtime.topology_explorer_store import (
    save_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    save_topology_profile,
    topology_profile_note,
)
from tet4d.engine.topology_explorer import (
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    tangent_axes_for_boundary,
    validate_explorer_topology_profile,
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
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.topology_lab import (
    ExplorerGlueDraft,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_INSPECT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TopologyLabHitTarget,
    TopologyLabState,
    apply_boundary_edit_pick,
    apply_boundary_pick,
    apply_glue_pick,
    boundaries_for_dimension,
    build_preview_lines,
    cycle_sandbox_piece,
    cycle_tool,
    default_draft_for_dimension,
    draw_action_buttons,
    draw_preview_panel,
    draw_probe_controls,
    draw_scene_2d,
    draw_scene_3d,
    draw_scene_4d,
    draw_tool_ribbon,
    draw_transform_editor,
    ensure_explorer_draft,
    ensure_piece_sandbox,
    ensure_probe_state as ensure_probe_state_runtime,
    reset_probe_state,
    move_sandbox_piece,
    permutation_options_for_dimension,
    pick_target,
    update_hover_target,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    sandbox_cells,
    sandbox_lines,
    sandbox_validity,
    set_active_tool,
    transform_preview_label,
    uses_general_explorer_editor as uses_general_explorer_editor_runtime,
)
from tet4d.ui.pygame.topology_lab.app import (
    ExplorerPlaygroundLaunch,
    build_explorer_playground_config,
    build_explorer_playground_launch,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (130, 138, 168)
_TOPOLOGY_DIMENSIONS = (2, 3, 4)
_EDGE_LABELS = {
    "bounded": "Bounded",
    "wrap": "Wrap",
    "invert": "Invert",
}
_AXIS_LABELS = {"x": "X", "y": "Y", "z": "Z", "w": "W"}


def _safe_lab_payload() -> dict[str, Any]:
    fallback = {
        "title": "Topology Lab",
        "subtitle": "Mode-aware topology profiles",
        "hints": (
            "Up/Down select row",
            "Left/Right change values",
            "Enter triggers Save/Export/Back",
            "Normal Game locks Y boundaries",
            "Explorer Mode allows vertical wrapping",
        ),
        "status_copy": {
            "saved": "Saved topology profile for {mode_label} {dimension}D",
            "save_failed": "Failed saving topology profile: {message}",
            "updated": "Topology profile updated (not saved yet)",
            "locked": "Y boundaries are fixed in Normal Game",
            "export_ok": "{message}",
            "export_error": "{message}",
        },
    }
    try:
        payload = topology_lab_menu_payload_runtime()
    except (OSError, ValueError, RuntimeError):
        return fallback
    if not isinstance(payload, dict):
        return fallback
    return {
        "title": str(payload.get("title", fallback["title"])),
        "subtitle": str(payload.get("subtitle", fallback["subtitle"])),
        "hints": tuple(payload.get("hints", fallback["hints"])),
        "status_copy": dict(payload.get("status_copy", fallback["status_copy"])),
    }


_LAB_COPY = _safe_lab_payload()
_LAB_TITLE = str(_LAB_COPY["title"])
_LAB_SUBTITLE = str(_LAB_COPY["subtitle"])


def _display_title_for_state(state: _TopologyLabState) -> str:
    if state.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
        return f"Explorer {state.dimension}D Playground"
    return _LAB_TITLE


_LAB_HINTS = tuple(str(hint) for hint in _LAB_COPY["hints"])
_LAB_STATUS_COPY = dict(_LAB_COPY["status_copy"])


@dataclass(frozen=True)
class _RowSpec:
    key: str
    label: str
    axis: int | None = None
    side: int | None = None
    disabled: bool = False


_TopologyLabState = TopologyLabState

_INITIAL_TOOL_BY_GAMEPLAY_MODE = {
    GAMEPLAY_MODE_NORMAL: TOOL_CREATE,
    GAMEPLAY_MODE_EXPLORER: TOOL_PROBE,
}


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


def _profile_for_state(state: _TopologyLabState) -> TopologyProfileState:
    return load_topology_profile(state.gameplay_mode, state.dimension)


def _sync_profile(state: _TopologyLabState) -> None:
    state.profile = _profile_for_state(state)


def _uses_general_explorer_editor(state: _TopologyLabState) -> bool:
    return uses_general_explorer_editor_runtime(state)


def _sync_explorer_state(state: _TopologyLabState) -> None:
    if not _uses_general_explorer_editor(state):
        state.explorer_profile = None
        state.explorer_draft = None
        state.probe_coord = None
        state.probe_trace = None
        state.probe_path = None
        state.hovered_boundary_index = None
        state.hovered_glue_id = None
        return
    state.explorer_profile = load_runtime_explorer_topology_profile(state.dimension)
    if (
        state.explorer_draft is None
        or len(state.explorer_draft.signs) != state.dimension - 1
    ):
        ensure_explorer_draft(state)
    _normalize_explorer_draft(state)
    _ensure_probe_state(state)


def _preset_profiles(state: _TopologyLabState):
    return designer_profiles_for_dimension(state.dimension, state.gameplay_mode)


def _explorer_presets(state: _TopologyLabState) -> tuple[ExplorerTopologyPreset, ...]:
    return explorer_presets_for_dimension(state.dimension)


def _preset_index(state: _TopologyLabState) -> int:
    profiles = _preset_profiles(state)
    preset_id = state.profile.preset_id
    if not preset_id:
        return 0
    for idx, profile in enumerate(profiles):
        if profile.profile_id == preset_id:
            return idx
    return 0


def _explorer_boundaries(state: _TopologyLabState):
    return boundaries_for_dimension(state.dimension)


def _explorer_permutations(state: _TopologyLabState):
    return permutation_options_for_dimension(state.dimension)


def _explorer_glues(state: _TopologyLabState) -> tuple[GluingDescriptor, ...]:
    return () if state.explorer_profile is None else state.explorer_profile.gluings


def _normalize_explorer_draft(state: _TopologyLabState) -> None:
    assert state.explorer_draft is not None
    boundaries = _explorer_boundaries(state)
    permutations = _explorer_permutations(state)
    glues = _explorer_glues(state)
    max_slot = len(glues)
    slot_index = max(0, min(state.explorer_draft.slot_index, max_slot))
    source_index = max(0, min(state.explorer_draft.source_index, len(boundaries) - 1))
    target_index = max(0, min(state.explorer_draft.target_index, len(boundaries) - 1))
    permutation_index = max(
        0, min(state.explorer_draft.permutation_index, len(permutations) - 1)
    )
    signs = tuple(
        -1 if int(value) < 0 else 1
        for value in state.explorer_draft.signs[: state.dimension - 1]
    )
    if len(signs) != state.dimension - 1:
        signs = tuple(1 for _ in range(state.dimension - 1))
    if slot_index < len(glues):
        glue = glues[slot_index]
        source_index = boundaries.index(glue.source)
        target_index = boundaries.index(glue.target)
        permutation_index = permutations.index(glue.transform.permutation)
        signs = glue.transform.signs
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=slot_index,
        source_index=source_index,
        target_index=target_index,
        permutation_index=permutation_index,
        signs=signs,
    )


def _explorer_slot_label(state: _TopologyLabState) -> str:
    assert state.explorer_draft is not None
    glues = _explorer_glues(state)
    if state.explorer_draft.slot_index >= len(glues):
        return "New glue"
    return glues[state.explorer_draft.slot_index].glue_id


def _explorer_transform_from_draft(state: _TopologyLabState) -> BoundaryTransform:
    assert state.explorer_draft is not None
    permutation = _explorer_permutations(state)[state.explorer_draft.permutation_index]
    return BoundaryTransform(permutation=permutation, signs=state.explorer_draft.signs)


def _explorer_transform_label(state: _TopologyLabState) -> str:
    assert state.explorer_draft is not None
    boundaries = _explorer_boundaries(state)
    source = boundaries[state.explorer_draft.source_index]
    target = boundaries[state.explorer_draft.target_index]
    return transform_preview_label(
        source,
        target,
        _explorer_transform_from_draft(state),
    )


def _explorer_preview_payload(
    state: _TopologyLabState,
) -> tuple[dict[str, object] | None, str | None]:
    assert state.explorer_profile is not None
    try:
        return (
            compile_explorer_topology_preview(
                state.explorer_profile,
                dims=explorer_topology_preview_dims(state.dimension),
                source="topology_lab_live_preview",
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _explorer_active_glue_ids(state: _TopologyLabState) -> dict[str, str]:
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
    assert state.explorer_draft is not None
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=slot_index,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    glues = _explorer_glues(state)
    state.selected_glue_id = None if slot_index >= len(glues) else glues[slot_index].glue_id
    _normalize_explorer_draft(state)


def _explorer_permutation_labels(state: _TopologyLabState) -> tuple[str, ...]:
    assert state.explorer_draft is not None
    boundaries = _explorer_boundaries(state)
    source = boundaries[state.explorer_draft.source_index]
    target = boundaries[state.explorer_draft.target_index]
    source_axes = tangent_axes_for_boundary(source)
    target_axes = tangent_axes_for_boundary(target)
    labels: list[str] = []
    for permutation in _explorer_permutations(state):
        source_text = ",".join("xyzw"[axis] for axis in source_axes)
        target_text = ",".join("xyzw"[target_axes[index]] for index in permutation)
        labels.append(f"{source_text}->{target_text}")
    return tuple(labels)


def _ensure_probe_state(state: _TopologyLabState) -> None:
    needs_default = (
        state.probe_coord is None
        or len(state.probe_coord) != state.dimension
        or state.probe_path is None
    )
    ensure_probe_state_runtime(state)
    if state.explorer_profile is None:
        return
    dims = explorer_topology_preview_dims(state.dimension)
    if needs_default or any(
        value < 0 or value >= dims[index]
        for index, value in enumerate(state.probe_coord or ())
    ):
        state.probe_coord = recommended_explorer_probe_coord(
            state.explorer_profile,
            dims=dims,
        )
        state.probe_trace = []
        state.probe_path = [state.probe_coord]


def _apply_probe_step(state: _TopologyLabState, step_label: str) -> None:
    assert state.explorer_profile is not None
    _ensure_probe_state(state)
    assert state.probe_coord is not None
    start = state.probe_coord
    target, result = advance_explorer_probe(
        state.explorer_profile,
        dims=explorer_topology_preview_dims(state.dimension),
        coord=state.probe_coord,
        step_label=step_label,
    )
    state.probe_coord = target
    traversal = result.get("traversal")
    state.highlighted_glue_id = None if traversal is None else str(traversal.get("glue_id"))
    trace = list(state.probe_trace or [])
    trace.append(str(result["message"]))
    state.probe_trace = trace[-6:]
    path = list(state.probe_path or [start])
    if not path or path[-1] != start:
        path.append(start)
    if target != start:
        path.append(target)
    state.probe_path = path[-20:]
    _set_status(
        state, str(result["message"]), is_error=bool(result.get("blocked", False))
    )


def _reset_probe(state: _TopologyLabState) -> None:
    if state.explorer_profile is None:
        reset_probe_state(state)
    else:
        state.probe_coord = recommended_explorer_probe_coord(
            state.explorer_profile,
            dims=explorer_topology_preview_dims(state.dimension),
        )
        state.probe_trace = []
        state.probe_path = [state.probe_coord]
        state.highlighted_glue_id = None
    _set_status(state, f"Probe reset to {list(state.probe_coord or ())}")


def _rows_for_state(state: _TopologyLabState) -> tuple[_RowSpec, ...]:
    if _uses_general_explorer_editor(state):
        rows = [
            _RowSpec("gameplay_mode", "Game Type"),
            _RowSpec("dimension", "Dimension"),
            _RowSpec("explorer_preset", "Explorer Preset"),
            _RowSpec("explorer_glue", "Active Glue"),
            _RowSpec("explorer_source", "Source Boundary"),
            _RowSpec("explorer_target", "Target Boundary"),
            _RowSpec("explorer_permutation", "Tangent Map"),
        ]
        for index in range(state.dimension - 1):
            rows.append(_RowSpec(f"explorer_sign_{index}", f"Flip Tangent {index + 1}"))
        rows.extend(
            (
                _RowSpec("apply_glue", "Apply / Update Glue"),
                _RowSpec("remove_glue", "Remove Active Glue"),
                _RowSpec("save_profile", "Save Profile"),
                _RowSpec("export", "Export Explorer Preview"),
                _RowSpec("back", "Back"),
            )
        )
        return tuple(rows)

    rows = [
        _RowSpec("gameplay_mode", "Game Type"),
        _RowSpec("dimension", "Dimension"),
        _RowSpec("preset", "Preset"),
        _RowSpec("topology_mode", "Topology Mode"),
    ]
    axis_names = tuple("xyzw"[: state.dimension])
    for axis_name in axis_names:
        axis = "xyzw".index(axis_name)
        disabled = axis_name == "y" and state.gameplay_mode == GAMEPLAY_MODE_NORMAL
        rows.append(
            _RowSpec(
                f"{axis_name}_neg",
                f"{_AXIS_LABELS[axis_name]}-",
                axis=axis,
                side=0,
                disabled=disabled,
            )
        )
        rows.append(
            _RowSpec(
                f"{axis_name}_pos",
                f"{_AXIS_LABELS[axis_name]}+",
                axis=axis,
                side=1,
                disabled=disabled,
            )
        )
    rows.extend(
        (
            _RowSpec("save_profile", "Save Profile"),
            _RowSpec("export", "Export Resolved Profile"),
            _RowSpec("back", "Back"),
        )
    )
    return tuple(rows)


def _selectable_row_indexes(state: _TopologyLabState) -> tuple[int, ...]:
    return tuple(idx for idx, _row in enumerate(_rows_for_state(state)))


def _mode_value_text(state: _TopologyLabState) -> str:
    return topology_gameplay_mode_label(state.gameplay_mode)


def _preset_value_text(state: _TopologyLabState) -> str:
    profiles = _preset_profiles(state)
    index = _preset_index(state)
    return profiles[index].label


def _explorer_preset_index(state: _TopologyLabState) -> int:
    assert state.explorer_profile is not None
    presets = _explorer_presets(state)
    for idx, preset in enumerate(presets):
        if preset.profile == state.explorer_profile:
            return idx
    return 0


def _explorer_preset_value_text(state: _TopologyLabState) -> str:
    presets = _explorer_presets(state)
    preset = presets[_explorer_preset_index(state)]
    return preset.label + (" [unsafe]" if preset.unsafe else "")


def _edge_value_text(state: _TopologyLabState, axis: int, side: int) -> str:
    value = state.profile.edge_rules[axis][side]
    return _EDGE_LABELS.get(value, str(value).title())


def _explorer_row_value_text(state: _TopologyLabState, row: _RowSpec) -> str | None:
    if row.key == "explorer_preset":
        return _explorer_preset_value_text(state)
    if row.key == "explorer_glue":
        return _explorer_slot_label(state)
    if row.key == "explorer_source":
        assert state.explorer_draft is not None
        return _explorer_boundaries(state)[state.explorer_draft.source_index].label
    if row.key == "explorer_target":
        assert state.explorer_draft is not None
        return _explorer_boundaries(state)[state.explorer_draft.target_index].label
    if row.key == "explorer_permutation":
        return _explorer_transform_label(state)
    if row.key.startswith("explorer_sign_"):
        assert state.explorer_draft is not None
        sign_index = int(row.key.rsplit("_", 1)[1])
        return "Flipped" if state.explorer_draft.signs[sign_index] < 0 else "Straight"
    return None


def _legacy_row_value_text(state: _TopologyLabState, row: _RowSpec) -> str | None:
    if row.key == "preset":
        return _preset_value_text(state)
    if row.key == "topology_mode":
        return topology_mode_label(state.profile.topology_mode)
    if row.axis is not None and row.side is not None:
        return _edge_value_text(state, row.axis, row.side)
    return None


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


def _mark_updated(state: _TopologyLabState) -> None:
    state.dirty = True
    _set_status(state, str(_LAB_STATUS_COPY["updated"]))


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
    idx = _TOPOLOGY_DIMENSIONS.index(state.dimension)
    state.dimension = _TOPOLOGY_DIMENSIONS[(idx + step) % len(_TOPOLOGY_DIMENSIONS)]
    _sync_profile(state)
    _sync_explorer_state(state)
    _mark_updated(state)


def _cycle_preset(state: _TopologyLabState, step: int) -> None:
    profiles = _preset_profiles(state)
    idx = (_preset_index(state) + step) % len(profiles)
    profile = profile_state_from_preset(
        dimension=state.dimension,
        gravity_axis=1,
        gameplay_mode=state.gameplay_mode,
        preset_index=idx,
        topology_mode=state.profile.topology_mode,
    )
    _apply_profile(state, profile)


def _cycle_explorer_preset(state: _TopologyLabState, step: int) -> None:
    assert state.explorer_profile is not None
    presets = _explorer_presets(state)
    idx = (_explorer_preset_index(state) + step) % len(presets)
    state.explorer_profile = presets[idx].profile
    draft = default_draft_for_dimension(state.dimension)
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=len(state.explorer_profile.gluings),
        source_index=draft.source_index,
        target_index=draft.target_index,
        permutation_index=draft.permutation_index,
        signs=draft.signs,
    )
    _normalize_explorer_draft(state)
    _mark_updated(state)


def _cycle_topology_mode(state: _TopologyLabState, step: int) -> None:
    options = tuple(topology_mode_from_index(idx) for idx in range(3))
    current = state.profile.topology_mode
    idx = options.index(current)
    next_mode = options[(idx + step) % len(options)]
    rules = default_edge_rules_for_mode(
        state.dimension,
        1,
        mode=next_mode,
        wrap_gravity_axis=(state.gameplay_mode == GAMEPLAY_MODE_EXPLORER),
    )
    profile = validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=next_mode,
        edge_rules=rules,
        preset_id=None,
    )
    _apply_profile(state, profile)


def _cycle_edge_rule(state: _TopologyLabState, row: _RowSpec, step: int) -> None:
    if row.disabled:
        _set_status(state, str(_LAB_STATUS_COPY["locked"]), is_error=True)
        return
    assert row.axis is not None and row.side is not None
    current = state.profile.edge_rules[row.axis][row.side]
    idx = EDGE_BEHAVIOR_OPTIONS.index(current)
    next_value = EDGE_BEHAVIOR_OPTIONS[(idx + step) % len(EDGE_BEHAVIOR_OPTIONS)]
    rules = [tuple(axis_rule) for axis_rule in state.profile.edge_rules]
    axis_rule = list(rules[row.axis])
    axis_rule[row.side] = next_value
    rules[row.axis] = tuple(axis_rule)
    try:
        profile = validate_topology_profile_state(
            gameplay_mode=state.gameplay_mode,
            dimension=state.dimension,
            gravity_axis=1,
            topology_mode=state.profile.topology_mode,
            edge_rules=tuple(rules),
            preset_id=None,
        )
    except ValueError as exc:
        _set_status(state, str(exc), is_error=True)
        return
    _apply_profile(state, profile)


def _set_explorer_draft_slot(state: _TopologyLabState, step: int) -> None:
    assert state.explorer_draft is not None
    glues = _explorer_glues(state)
    slot_count = len(glues) + 1
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=(state.explorer_draft.slot_index + step) % slot_count,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    _normalize_explorer_draft(state)


def _cycle_explorer_boundary(
    state: _TopologyLabState, *, is_source: bool, step: int
) -> None:
    assert state.explorer_draft is not None
    boundaries = _explorer_boundaries(state)
    current = (
        state.explorer_draft.source_index
        if is_source
        else state.explorer_draft.target_index
    )
    next_index = (current + step) % len(boundaries)
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=state.explorer_draft.slot_index,
        source_index=next_index if is_source else state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index if is_source else next_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    _normalize_explorer_draft(state)


def _cycle_explorer_permutation(state: _TopologyLabState, step: int) -> None:
    assert state.explorer_draft is not None
    options = _explorer_permutations(state)
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=state.explorer_draft.slot_index,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=(state.explorer_draft.permutation_index + step)
        % len(options),
        signs=state.explorer_draft.signs,
    )


def _toggle_explorer_sign(state: _TopologyLabState, sign_index: int) -> None:
    assert state.explorer_draft is not None
    signs = list(state.explorer_draft.signs)
    signs[sign_index] *= -1
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=state.explorer_draft.slot_index,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=tuple(signs),
    )


def _validate_explorer_profile_or_error(
    state: _TopologyLabState,
    profile: ExplorerTopologyProfile,
) -> ExplorerTopologyProfile | None:
    try:
        return validate_explorer_topology_profile(
            profile,
            dims=explorer_topology_preview_dims(state.dimension),
        )
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
    assert state.explorer_profile is not None
    assert state.explorer_draft is not None
    boundaries = _explorer_boundaries(state)
    source = boundaries[state.explorer_draft.source_index]
    target = boundaries[state.explorer_draft.target_index]
    transform = _explorer_transform_from_draft(state)
    gluings = list(_explorer_glues(state))
    slot_index = state.explorer_draft.slot_index
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
    profile = ExplorerTopologyProfile(dimension=state.dimension, gluings=tuple(gluings))
    validated = _validate_explorer_profile_or_error(state, profile)
    if validated is None:
        return
    state.explorer_profile = validated
    state.selected_glue_id = glue_id
    state.highlighted_glue_id = glue_id
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=slot_index,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    glues = _explorer_glues(state)
    state.selected_glue_id = None if slot_index >= len(glues) else glues[slot_index].glue_id
    _normalize_explorer_draft(state)
    _mark_updated(state)


def _remove_explorer_glue(state: _TopologyLabState) -> None:
    assert state.explorer_profile is not None
    assert state.explorer_draft is not None
    gluings = list(_explorer_glues(state))
    if state.explorer_draft.slot_index >= len(gluings):
        _set_status(state, "No active glue selected", is_error=True)
        return
    del gluings[state.explorer_draft.slot_index]
    state.explorer_profile = ExplorerTopologyProfile(
        dimension=state.dimension,
        gluings=tuple(gluings),
    )
    state.selected_glue_id = None
    state.highlighted_glue_id = None
    next_slot = min(state.explorer_draft.slot_index, len(gluings))
    state.explorer_draft = ExplorerGlueDraft(
        slot_index=next_slot,
        source_index=state.explorer_draft.source_index,
        target_index=state.explorer_draft.target_index,
        permutation_index=state.explorer_draft.permutation_index,
        signs=state.explorer_draft.signs,
    )
    _normalize_explorer_draft(state)
    _mark_updated(state)


def _save_profile(state: _TopologyLabState) -> tuple[bool, str]:
    if _uses_general_explorer_editor(state):
        assert state.explorer_profile is not None
        ok, message = save_explorer_topology_profile(state.explorer_profile)
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
    if _uses_general_explorer_editor(state):
        assert state.explorer_profile is not None
        ok, message, _path = export_explorer_topology_preview(
            state.explorer_profile,
            dims=explorer_topology_preview_dims(state.dimension),
            source=f"topology_lab_{state.dimension}d_mvp",
        )
        if not ok:
            _set_status(
                state,
                str(_LAB_STATUS_COPY["export_error"]).format(message=message),
                is_error=True,
            )
            return
        _set_status(state, str(_LAB_STATUS_COPY["export_ok"]).format(message=message))
        play_sfx("menu_confirm")
        return

    ok, message, _path = export_topology_profile_state(
        profile=state.profile,
        gravity_axis=1,
    )
    if not ok:
        _set_status(
            state,
            str(_LAB_STATUS_COPY["export_error"]).format(message=message),
            is_error=True,
        )
        return

    status_lines = [str(_LAB_STATUS_COPY["export_ok"]).format(message=message)]
    if state.gameplay_mode == GAMEPLAY_MODE_EXPLORER:
        try:
            preview_ok, preview_message, _preview_path = (
                export_explorer_preview_from_profile_state(
                    state.profile,
                    dims=explorer_topology_preview_dims(state.dimension),
                    source="legacy_edge_rules_bridge",
                )
            )
        except ValueError as exc:
            status_lines.append(f"Explorer gluing preview unavailable: {exc}")
        else:
            if not preview_ok:
                _set_status(
                    state,
                    str(_LAB_STATUS_COPY["export_error"]).format(
                        message=preview_message
                    ),
                    is_error=True,
                )
                return
            status_lines.append(preview_message)

    _set_status(state, " | ".join(status_lines))
    play_sfx("menu_confirm")


def _adjust_explorer_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    if row.key == "explorer_preset":
        _cycle_explorer_preset(state, step)
        return True
    if row.key == "explorer_glue":
        _set_explorer_draft_slot(state, step)
        return True
    if row.key == "explorer_source":
        _cycle_explorer_boundary(state, is_source=True, step=step)
        return True
    if row.key == "explorer_target":
        _cycle_explorer_boundary(state, is_source=False, step=step)
        return True
    if row.key == "explorer_permutation":
        _cycle_explorer_permutation(state, step)
        return True
    if row.key.startswith("explorer_sign_"):
        _toggle_explorer_sign(state, int(row.key.rsplit("_", 1)[1]))
        return True
    return False


def _adjust_legacy_row(state: _TopologyLabState, row: _RowSpec, step: int) -> bool:
    if row.key == "preset":
        _cycle_preset(state, step)
        return True
    if row.key == "topology_mode":
        _cycle_topology_mode(state, step)
        return True
    if row.axis is not None:
        _cycle_edge_rule(state, row, step)
        return True
    return False


def _adjust_active_row(state: _TopologyLabState, step: int) -> bool:
    row = _rows_for_state(state)[_selectable_row_indexes(state)[state.selected]]
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


def _handle_navigation_key(
    state: _TopologyLabState, nav_key: int, selectable: tuple[int, ...]
) -> bool:
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


_TOOL_SHORTCUT_KEYS = {
    pygame.K_n: "navigate",
    pygame.K_i: "inspect_boundary",
    pygame.K_g: "create_gluing",
    pygame.K_t: "edit_transform",
    pygame.K_p: "probe",
    pygame.K_b: "piece_sandbox",
}

_SANDBOX_STEP_KEYS = {
    pygame.K_LEFT: "x-",
    pygame.K_RIGHT: "x+",
    pygame.K_UP: "y-",
    pygame.K_DOWN: "y+",
}

_PROBE_MOVEMENT_TOOLS = {
    TOOL_NAVIGATE,
    TOOL_INSPECT,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_PROBE,
    TOOL_PLAY,
}


def _handle_save_export_shortcut(state: _TopologyLabState, key: int) -> bool:
    if key == pygame.K_s:
        _save_profile(state)
        return True
    if key == pygame.K_e:
        _run_export(state)
        return True
    return False


def _handle_tool_shortcut(state: _TopologyLabState, key: int) -> bool:
    if not _uses_general_explorer_editor(state):
        return False
    if key == pygame.K_TAB:
        cycle_tool(state, 1)
        return True
    tool_name = _TOOL_SHORTCUT_KEYS.get(key)
    if tool_name is not None:
        set_active_tool(state, tool_name)
        return True
    if key == pygame.K_F5:
        state.play_preview_requested = True
        return True
    return False


def _apply_sandbox_shortcut_step(state: _TopologyLabState, step_label: str) -> None:
    assert state.explorer_profile is not None
    ok, message = move_sandbox_piece(state, state.explorer_profile, step_label)
    _set_status(state, message, is_error=not ok)


def _handle_probe_shortcut(state: _TopologyLabState, key: int) -> bool:
    if (
        state.active_tool not in _PROBE_MOVEMENT_TOOLS
        or not _uses_general_explorer_editor(state)
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
    if state.active_tool != TOOL_SANDBOX or not _uses_general_explorer_editor(state):
        return False
    step_label = _bound_explorer_step_label(state, key)
    if step_label is None:
        step_label = _SANDBOX_STEP_KEYS.get(key)
    if step_label is not None:
        _apply_sandbox_shortcut_step(state, step_label)
        return True
    if key == pygame.K_r:
        assert state.explorer_profile is not None
        ok, message = rotate_sandbox_piece(state, state.explorer_profile)
        _set_status(state, message, is_error=not ok)
        return True
    if key == pygame.K_LEFTBRACKET:
        cycle_sandbox_piece(state, -1)
        return True
    if key == pygame.K_RIGHTBRACKET:
        cycle_sandbox_piece(state, 1)
        return True
    if key == pygame.K_0:
        reset_sandbox_piece(state)
        _set_status(state, "Sandbox reset")
        return True
    if key == pygame.K_t:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.show_trace = not state.sandbox.show_trace
        _set_status(state, f"Sandbox trace {'shown' if state.sandbox.show_trace else 'hidden'}")
        return True
    return False


def _handle_shortcut_key(state: _TopologyLabState, key: int) -> bool:
    return (
        _handle_save_export_shortcut(state, key)
        or _handle_tool_shortcut(state, key)
        or _handle_probe_shortcut(state, key)
        or _handle_sandbox_shortcut(state, key)
    )


def _handle_enter_key(state: _TopologyLabState, selectable: tuple[int, ...]) -> None:
    row = _rows_for_state(state)[selectable[state.selected]]
    if row.key == "save_profile":
        _save_profile(state)
        return
    if row.key == "export":
        _run_export(state)
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
    if not _uses_general_explorer_editor(state) or state.explorer_profile is None:
        return screen, display_settings
    from tet4d.ui.pygame.runtime_ui.app_runtime import (
        capture_windowed_display_settings,
        open_display,
    )
    from tet4d.ui.pygame import front2d_game, front3d_game, front4d_game
    from tet4d.ui.pygame.render.font_profiles import init_fonts as init_fonts_for_profile

    play_fonts_2d = fonts_2d if fonts_2d is not None else init_fonts_for_profile("2d")
    try:
        cfg = build_explorer_playground_config(
            dimension=state.dimension,
            explorer_profile=state.explorer_profile,
        )
        if state.dimension == 2:
            front2d_game.run_game_loop(
                screen,
                cfg,
                play_fonts_2d,
                display_settings,
            )
        else:
            if state.dimension == 3:
                front3d_game.run_game_loop(screen, cfg, fonts_nd)
            else:
                front4d_game.run_game_loop(screen, cfg, fonts_nd)
    except Exception as exc:
        _set_status(state, f"Play preview failed: {exc}", is_error=True)
        return screen, display_settings
    if display_settings is not None:
        display_settings = capture_windowed_display_settings(display_settings)
        screen = open_display(display_settings, caption=_display_title_for_state(state))
    _set_status(state, f"Returned from Explorer {state.dimension}D play preview")
    return screen, display_settings


def _topology_note_text(state: _TopologyLabState) -> str:
    if _uses_general_explorer_editor(state):
        return f"Explorer {state.dimension}D uses direct boundary gluings with tangent transforms."
    return topology_profile_note(state.gameplay_mode)


def _explorer_boundary_lines(state: _TopologyLabState) -> list[str]:
    boundary_status = _explorer_active_glue_ids(state)
    lines = ["Boundaries"]
    for boundary in _explorer_boundaries(state):
        lines.append(f"  {boundary.label}: {boundary_status[boundary.label]}")
    return lines


def _explorer_gluing_lines(state: _TopologyLabState) -> list[str]:
    lines = ["Gluings"]
    glues = _explorer_glues(state)
    if not glues:
        lines.append("  none")
        return lines
    for glue in glues:
        lines.append(
            "  " + transform_preview_label(glue.source, glue.target, glue.transform)
        )
    return lines


def _explorer_preview_lines(
    state: _TopologyLabState, preview: dict[str, object]
) -> list[str]:
    graph = preview["movement_graph"]
    lines = ["Preview"]
    lines.append(
        f"  Cells: {graph['cell_count']}  Edges: {graph['directed_edge_count']}"
    )
    lines.append(
        "  Traversals: "
        f"{graph['boundary_traversal_count']}  Components: {graph['component_count']}"
    )
    warnings = preview.get("warnings", ())
    if warnings:
        lines.append("  Warnings")
        for warning in warnings[:3]:
            lines.append(f"    {warning}")
    basis_arrows = preview.get("basis_arrows", ())
    if basis_arrows:
        lines.append("  Arrow basis")
        for arrow in basis_arrows[:2]:
            lines.append(f"    {arrow['crossing']}")
            for pair in arrow.get("basis_pairs", ())[: max(1, state.dimension - 1)]:
                lines.append(f"      {pair['from']} -> {pair['to']}")
    samples = preview["sample_boundary_traversals"]
    if samples:
        lines.append("  Samples")
        for sample in samples[:4]:
            lines.append(
                "    "
                f"{sample['source_boundary']} -> {sample['target_boundary']} via {sample['step']}"
            )
    return lines


def _explorer_sidebar_lines(state: _TopologyLabState) -> list[str]:
    assert state.explorer_profile is not None
    lines = [
        f"Explorer {state.dimension}D gluing editor",
        _explorer_transform_label(state),
        "",
    ]
    lines.extend(_explorer_boundary_lines(state))
    lines.append("")
    lines.extend(_explorer_gluing_lines(state))
    lines.append("")
    preview, preview_error = _explorer_preview_payload(state)
    if preview is None:
        lines.append(f"Preview invalid: {preview_error}")
        return lines
    lines.extend(_explorer_preview_lines(state, preview))
    return lines


def _action_buttons_for_state(state: _TopologyLabState) -> tuple[tuple[str, str], ...]:
    if state.active_tool == TOOL_PROBE:
        return (
            ("probe_reset", "Reset Probe"),
            ("play_preview", "Play"),
            ("save_profile", "Save"),
            ("back", "Back"),
        )
    if state.active_tool == TOOL_SANDBOX:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        return (
            ("sandbox_prev", "Prev Piece"),
            ("sandbox_next", "Next Piece"),
            ("sandbox_rotate", "Rotate"),
            ("sandbox_trace", "Hide Trace" if state.sandbox.show_trace else "Show Trace"),
            ("sandbox_reset", "Reset"),
            ("play_preview", "Play"),
            ("save_profile", "Save"),
            ("back", "Back"),
        )
    return (
        ("apply_glue", "Apply"),
        ("remove_glue", "Remove"),
        ("save_profile", "Save"),
        ("export", "Export"),
        ("play_preview", "Play"),
        ("back", "Back"),
    )


def _explorer_workspace_layout(
    *,
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
    menu_w: int,
) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect, pygame.Rect]:
    workspace_x = panel_x + menu_w + 18
    workspace_w = panel_w - menu_w - 30
    tool_h = 34
    top_h = max(180, min(300, int(panel_h * 0.36)))
    editor_h = max(190, min(250, int(panel_h * 0.24)))
    actions_h = 38
    gap = 12
    tool_rect = pygame.Rect(workspace_x, panel_y + 14, workspace_w, tool_h)
    top_rect = pygame.Rect(workspace_x, tool_rect.bottom + gap, workspace_w, top_h)
    editor_rect = pygame.Rect(workspace_x, top_rect.bottom + gap, workspace_w, editor_h)
    preview_rect = pygame.Rect(
        workspace_x,
        editor_rect.bottom + gap,
        workspace_w,
        max(110, panel_y + panel_h - (editor_rect.bottom + gap) - 56),
    )
    action_rect = pygame.Rect(
        workspace_x,
        panel_y + panel_h - actions_h - 16,
        workspace_w,
        actions_h,
    )
    if preview_rect.bottom > action_rect.y - gap:
        preview_rect.height = max(88, action_rect.y - gap - preview_rect.y)
    return tool_rect, top_rect, editor_rect, preview_rect, action_rect


def _sandbox_scene_payload(
    state: _TopologyLabState,
) -> tuple[tuple[tuple[int, ...], ...] | None, bool | None, str]:
    if state.active_tool != TOOL_SANDBOX:
        return None, None, ""
    ensure_piece_sandbox(state)
    assert state.explorer_profile is not None
    sandbox_cells_payload = sandbox_cells(state)
    sandbox_ok, sandbox_message = sandbox_validity(state, state.explorer_profile)
    return sandbox_cells_payload, sandbox_ok, sandbox_message


def _draw_explorer_scene(
    screen: pygame.Surface,
    fonts,
    state: _TopologyLabState,
    *,
    area: pygame.Rect,
    boundaries,
    source_boundary,
    target_boundary,
    active_glue_ids: dict[str, str],
    basis_arrows: list[dict[str, object]],
    preview_dims: tuple[int, ...],
    sandbox_cells_payload: tuple[tuple[int, ...], ...] | None,
    sandbox_ok: bool | None,
    sandbox_message: str,
) -> list[TopologyLabHitTarget]:
    scene_kwargs = dict(
        area=area,
        boundaries=boundaries,
        source_boundary=source_boundary,
        target_boundary=target_boundary,
        active_glue_ids=active_glue_ids,
        basis_arrows=basis_arrows,
        preview_dims=preview_dims,
        selected_glue_id=state.selected_glue_id,
        highlighted_glue_id=(state.hovered_glue_id or state.highlighted_glue_id),
        hovered_boundary_index=state.hovered_boundary_index,
        selected_boundary_index=state.selected_boundary_index,
        probe_coord=state.probe_coord,
        probe_path=tuple(state.probe_path or ()),
        sandbox_cells=sandbox_cells_payload,
        sandbox_valid=sandbox_ok,
        sandbox_message=sandbox_message,
    )
    if state.dimension == 2:
        return draw_scene_2d(screen, fonts, **scene_kwargs)
    if state.dimension == 4:
        return draw_scene_4d(screen, fonts, **scene_kwargs)
    return draw_scene_3d(screen, fonts, **scene_kwargs)


def _workspace_preview_lines(
    state: _TopologyLabState,
    preview: dict[str, object] | None,
    preview_error: str | None,
) -> list[str]:
    lines = (
        [f"Preview invalid: {preview_error}"]
        if preview is None
        else build_preview_lines(preview, dimension=state.dimension)
    )
    if state.selected_boundary_index is not None:
        boundary = _explorer_boundaries(state)[state.selected_boundary_index].label
        lines.append(f"Selected boundary: {boundary}")
    if state.probe_coord is not None:
        lines.append(f"Probe: {list(state.probe_coord)}")
        lines.append(f"Trace points: {max(0, len(state.probe_path or []) - 1)}")
        for line in (state.probe_trace or [])[-3:]:
            lines.append(f"  {line}")
    if state.active_tool == TOOL_SANDBOX:
        ensure_piece_sandbox(state)
        assert state.explorer_profile is not None
        lines.append("")
        lines.extend(sandbox_lines(state, state.explorer_profile))
    return lines


def _draw_probe_controls_if_needed(
    screen: pygame.Surface,
    fonts,
    *,
    state: _TopologyLabState,
    area: pygame.Rect,
    preview: dict[str, object] | None,
) -> list[TopologyLabHitTarget]:
    if preview is None or state.active_tool not in {TOOL_PROBE, TOOL_SANDBOX}:
        return []
    return draw_probe_controls(
        screen,
        fonts,
        area=area,
        step_options=explorer_probe_options(
            state.explorer_profile,
            dims=explorer_topology_preview_dims(state.dimension),
            coord=state.probe_coord or tuple(0 for _ in range(state.dimension)),
        ),
    )


def _draw_explorer_workspace(
    screen: pygame.Surface,
    fonts,
    state: _TopologyLabState,
    *,
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
    menu_w: int,
) -> list[TopologyLabHitTarget]:
    assert state.explorer_profile is not None
    assert state.explorer_draft is not None
    tool_rect, top_rect, editor_rect, preview_rect, action_rect = _explorer_workspace_layout(
        panel_x=panel_x,
        panel_y=panel_y,
        panel_w=panel_w,
        panel_h=panel_h,
        menu_w=menu_w,
    )
    hits = draw_tool_ribbon(screen, fonts, area=tool_rect, active_tool=state.active_tool)

    boundaries = _explorer_boundaries(state)
    source_boundary = boundaries[state.explorer_draft.source_index]
    target_boundary = boundaries[state.explorer_draft.target_index]
    active_glue_ids = _explorer_active_glue_ids(state)
    preview, preview_error = _explorer_preview_payload(state)
    basis_arrows = [] if preview is None else list(preview.get("basis_arrows", ()))
    preview_dims = explorer_topology_preview_dims(state.dimension)
    sandbox_cells_payload, sandbox_ok, sandbox_message = _sandbox_scene_payload(state)
    hits.extend(
        _draw_explorer_scene(
            screen,
            fonts,
            state,
            area=top_rect,
            boundaries=boundaries,
            source_boundary=source_boundary,
            target_boundary=target_boundary,
            active_glue_ids=active_glue_ids,
            basis_arrows=basis_arrows,
            preview_dims=preview_dims,
            sandbox_cells_payload=sandbox_cells_payload,
            sandbox_ok=sandbox_ok,
            sandbox_message=sandbox_message,
        )
    )
    hits.extend(
        draw_transform_editor(
            screen,
            fonts,
            area=editor_rect,
            preset_label=_explorer_preset_value_text(state),
            glue_labels=_explorer_glue_labels(state),
            active_slot_index=state.explorer_draft.slot_index,
            transform_label=_explorer_transform_label(state),
            permutation_labels=_explorer_permutation_labels(state),
            selected_permutation_index=state.explorer_draft.permutation_index,
            signs=state.explorer_draft.signs,
        )
    )
    hits.extend(
        draw_action_buttons(
            screen,
            fonts,
            area=action_rect,
            actions=_action_buttons_for_state(state),
        )
    )

    _ensure_probe_state(state)
    preview_lines = _workspace_preview_lines(state, preview, preview_error)
    probe_area = pygame.Rect(preview_rect.x + 10, preview_rect.bottom - 70, preview_rect.width - 20, 56)
    preview_body_rect = preview_rect.copy()
    preview_body_rect.height = max(80, preview_rect.height - 76)
    draw_preview_panel(
        screen,
        fonts,
        area=preview_body_rect,
        title=f"Explorer {state.dimension}D preview",
        lines=preview_lines,
    )
    hits.extend(
        _draw_probe_controls_if_needed(
            screen,
            fonts,
            state=state,
            area=probe_area,
            preview=preview,
        )
    )
    return hits


def _set_selected_row_by_key(state: _TopologyLabState, key: str) -> None:
    selectable = _selectable_row_indexes(state)
    rows = _rows_for_state(state)
    for index, row_index in enumerate(selectable):
        if rows[row_index].key == key:
            state.selected = index
            return


def _handle_standard_action(state: _TopologyLabState, action: str) -> bool:
    handlers = {
        "apply_glue": _apply_explorer_glue,
        "remove_glue": _remove_explorer_glue,
        "save_profile": _save_profile,
        "export": _run_export,
        "probe_reset": _reset_probe,
    }
    handler = handlers.get(action)
    if handler is None:
        return False
    handler(state)
    return True


def _handle_sandbox_action(state: _TopologyLabState, action: str) -> bool:
    if action == "sandbox_prev":
        cycle_sandbox_piece(state, -1)
        return True
    if action == "sandbox_next":
        cycle_sandbox_piece(state, 1)
        return True
    if action == "sandbox_rotate":
        assert state.explorer_profile is not None
        ok, message = rotate_sandbox_piece(state, state.explorer_profile)
        _set_status(state, message, is_error=not ok)
        return True
    if action == "sandbox_reset":
        reset_sandbox_piece(state)
        _set_status(state, "Sandbox reset")
        return True
    if action == "sandbox_trace":
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.show_trace = not state.sandbox.show_trace
        _set_status(state, f"Sandbox trace {'shown' if state.sandbox.show_trace else 'hidden'}")
        return True
    return False


def _activate_action(state: _TopologyLabState, action: str) -> None:
    if _handle_standard_action(state, action):
        return
    if _handle_sandbox_action(state, action):
        return
    if action == "play_preview":
        state.play_preview_requested = True
        return
    if action == "back":
        state.running = False


def _handle_mouse_editor_target(
    state: _TopologyLabState, target: TopologyLabHitTarget
) -> bool:
    if target.kind == "preset_step":
        _cycle_explorer_preset(state, int(target.value))
        _set_selected_row_by_key(state, "explorer_preset")
        play_sfx("menu_move")
        return True
    if target.kind == "tool_mode":
        set_active_tool(state, str(target.value))
        play_sfx("menu_move")
        return True
    if state.explorer_draft is None:
        return True
    if target.kind == "glue_slot":
        _select_explorer_draft_slot(state, int(target.value))
        _set_selected_row_by_key(state, "explorer_glue")
        play_sfx("menu_move")
        return True
    if target.kind == "perm_select":
        state.explorer_draft = ExplorerGlueDraft(
            slot_index=state.explorer_draft.slot_index,
            source_index=state.explorer_draft.source_index,
            target_index=state.explorer_draft.target_index,
            permutation_index=int(target.value),
            signs=state.explorer_draft.signs,
        )
        _set_selected_row_by_key(state, "explorer_permutation")
        play_sfx("menu_move")
        return True
    if target.kind == "sign_toggle":
        _toggle_explorer_sign(state, int(target.value))
        _set_selected_row_by_key(state, f"explorer_sign_{int(target.value)}")
        play_sfx("menu_move")
        return True
    return False


def _handle_mouse_action_target(
    state: _TopologyLabState, target: TopologyLabHitTarget
) -> bool:
    if target.kind == "action":
        _activate_action(state, str(target.value))
        if state.running:
            play_sfx(
                "menu_confirm"
                if str(target.value) in {"save_profile", "export", "apply_glue", "play_preview"}
                else "menu_move"
            )
        return True
    if target.kind == "probe_step" and _uses_general_explorer_editor(state):
        if state.active_tool == TOOL_SANDBOX:
            assert state.explorer_profile is not None
            ok, message = move_sandbox_piece(state, state.explorer_profile, str(target.value))
            _set_status(state, message, is_error=not ok)
        else:
            _apply_probe_step(state, str(target.value))
        play_sfx("menu_move")
        return True
    return False


def _handle_mouse_boundary_target(
    state: _TopologyLabState, target: TopologyLabHitTarget, button: int
) -> bool:
    boundary_index = int(target.value)
    if _uses_general_explorer_editor(state) and state.explorer_draft is not None:
        active_row = _rows_for_state(state)[_selectable_row_indexes(state)[state.selected]].key
        if active_row in {"explorer_source", "explorer_target"}:
            state.explorer_draft = ExplorerGlueDraft(
                slot_index=state.explorer_draft.slot_index,
                source_index=boundary_index
                if active_row == "explorer_source"
                else state.explorer_draft.source_index,
                target_index=boundary_index
                if active_row == "explorer_target"
                else state.explorer_draft.target_index,
                permutation_index=state.explorer_draft.permutation_index,
                signs=state.explorer_draft.signs,
            )
            _normalize_explorer_draft(state)
            play_sfx("menu_move")
            return True
    if button == 3 and state.active_tool in {TOOL_NAVIGATE, TOOL_INSPECT, TOOL_PROBE, TOOL_PLAY}:
        message = apply_boundary_edit_pick(state, boundary_index)
    else:
        message = apply_boundary_pick(state, boundary_index)
    _normalize_explorer_draft(state)
    if message:
        _set_status(state, message)
    play_sfx("menu_move")
    return True


def _dispatch_mouse_target(
    state: _TopologyLabState, target: TopologyLabHitTarget, button: int
) -> bool:
    if target.kind == "row_select":
        _set_selected_row_by_key(state, str(target.value))
        play_sfx("menu_move")
        return True
    if target.kind == "glue_pick" and _uses_general_explorer_editor(state):
        message = apply_glue_pick(state, str(target.value))
        _normalize_explorer_draft(state)
        if message:
            _set_status(state, message)
        play_sfx("menu_move")
        return True
    if target.kind == "boundary_pick":
        return _handle_mouse_boundary_target(state, target, button)
    if target.kind in {"preset_step", "tool_mode", "glue_slot", "perm_select", "sign_toggle"}:
        return _handle_mouse_editor_target(state, target)
    if target.kind in {"action", "probe_step"}:
        return _handle_mouse_action_target(state, target)
    return False


def _handle_mouse_down(
    state: _TopologyLabState, pos: tuple[int, int], button: int
) -> None:
    if button not in (1, 3):
        return
    target = pick_target(state.mouse_targets, pos)
    update_hover_target(state, target)
    if target is not None:
        _dispatch_mouse_target(state, target, button)


def _handle_mouse_motion(state: _TopologyLabState, pos: tuple[int, int]) -> None:
    update_hover_target(state, pick_target(state.mouse_targets, pos))


def _draw_menu(screen: pygame.Surface, fonts, state: _TopologyLabState) -> None:
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render(_display_title_for_state(state), True, _TEXT_COLOR)
    subtitle_text = fit_text(fonts.hint_font, _LAB_SUBTITLE, width - 28)
    subtitle = fonts.hint_font.render(subtitle_text, True, _MUTED_COLOR)
    note_text = fit_text(fonts.hint_font, _topology_note_text(state), width - 28)
    note = fonts.hint_font.render(note_text, True, _HIGHLIGHT_COLOR)
    title_y = 42
    screen.blit(title, ((width - title.get_width()) // 2, title_y))
    screen.blit(
        subtitle,
        ((width - subtitle.get_width()) // 2, title_y + title.get_height() + 6),
    )
    screen.blit(
        note,
        (
            (width - note.get_width()) // 2,
            title_y + title.get_height() + subtitle.get_height() + 14,
        ),
    )

    rows = _rows_for_state(state)
    selectable = _selectable_row_indexes(state)
    selected_row = selectable[state.selected]

    panel_w = min(
        1040 if _uses_general_explorer_editor(state) else 820, max(420, width - 40)
    )
    panel_h = min(height - 210, 80 + len(rows) * 38)
    panel_x = (width - panel_w) // 2
    panel_y = max(150, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    if _uses_general_explorer_editor(state):
        menu_w = min(460, panel_w - 300)
        separator_x = panel_x + menu_w + 8
        pygame.draw.line(
            screen,
            (100, 116, 156),
            (separator_x, panel_y + 14),
            (separator_x, panel_y + panel_h - 14),
            1,
        )
    else:
        menu_w = panel_w

    state.mouse_targets = []
    y = panel_y + 16
    for idx, row in enumerate(rows):
        selected = idx == selected_row
        row_rect = pygame.Rect(
            panel_x + 14, y - 4, menu_w - 28, fonts.menu_font.get_height() + 10
        )
        state.mouse_targets.append(
            TopologyLabHitTarget("row_select", row.key, row_rect)
        )
        color = (
            _DISABLED_COLOR
            if row.disabled
            else (_HIGHLIGHT_COLOR if selected else _TEXT_COLOR)
        )
        if selected:
            hi = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, row_rect.topleft)
        label_text = row.label + (" (locked)" if row.disabled else "")
        label = fonts.menu_font.render(
            fit_text(fonts.menu_font, label_text, max(160, menu_w // 2 - 10)),
            True,
            color,
        )
        value = fonts.menu_font.render(
            fit_text(
                fonts.menu_font, _row_value_text(state, row), max(160, menu_w // 2 - 10)
            ),
            True,
            color,
        )
        screen.blit(label, (panel_x + 22, y))
        screen.blit(value, (panel_x + menu_w - value.get_width() - 22, y))
        y += 38

    if _uses_general_explorer_editor(state):
        state.mouse_targets.extend(
            _draw_explorer_workspace(
                screen,
                fonts,
                state,
                panel_x=panel_x,
                panel_y=panel_y,
                panel_w=panel_w,
                panel_h=panel_h,
                menu_w=menu_w,
            )
        )

    hint_y = panel_y + panel_h + 10
    for hint in _LAB_HINTS:
        hint_text = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_text, True, _MUTED_COLOR)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3
    if state.status:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 24)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 2))


def _dispatch_key(state: _TopologyLabState, key: int) -> None:
    nav_key = normalize_menu_navigation_key(key)
    selectable = _selectable_row_indexes(state)
    if key == pygame.K_q or nav_key == pygame.K_ESCAPE:
        state.running = False
        return
    if _handle_shortcut_key(state, key):
        return
    if _handle_navigation_key(state, nav_key, selectable):
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_enter_key(state, selectable)


def _initial_topology_lab_state(
    start_dimension: int,
    *,
    gameplay_mode: str = GAMEPLAY_MODE_NORMAL,
    initial_explorer_profile: ExplorerTopologyProfile | None = None,
    initial_tool: str | None = None,
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
    )
    _sync_explorer_state(state)
    if mode == GAMEPLAY_MODE_EXPLORER:
        if initial_explorer_profile is not None:
            state.explorer_profile = initial_explorer_profile
            ensure_explorer_draft(state)
            _normalize_explorer_draft(state)
            _ensure_probe_state(state)
        set_active_tool(state, initial_tool or _INITIAL_TOOL_BY_GAMEPLAY_MODE[mode])
    elif initial_tool is not None:
        set_active_tool(state, initial_tool)
    return state


def _process_topology_lab_events(state: _TopologyLabState) -> None:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state.running = False
            return
        if event.type == pygame.KEYDOWN:
            _dispatch_key(state, event.key)
        elif event.type == pygame.MOUSEMOTION:
            _handle_mouse_motion(state, event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            _handle_mouse_down(state, event.pos, event.button)
        if not state.running:
            return


def _handle_pending_play_preview(
    state: _TopologyLabState,
    screen: pygame.Surface,
    fonts,
    *,
    fonts_2d=None,
    display_settings=None,
) -> tuple[pygame.Surface, object | None]:
    if not state.play_preview_requested:
        return screen, display_settings
    state.play_preview_requested = False
    return _launch_play_preview(
        state,
        screen,
        fonts,
        fonts_2d=fonts_2d,
        display_settings=display_settings,
    )


def _finalize_topology_lab_result(state: _TopologyLabState) -> tuple[bool, str]:
    if state.dirty:
        ok, message = _save_profile(state)
        return ok, message
    if state.status:
        return (not state.status_error), state.status
    return True, "Topology Lab unchanged"


def run_topology_lab_menu(
    screen: pygame.Surface,
    fonts,
    *,
    launch: ExplorerPlaygroundLaunch | None = None,
    start_dimension: int,
    display_settings=None,
    fonts_2d=None,
    gameplay_mode: str = GAMEPLAY_MODE_NORMAL,
    initial_explorer_profile: ExplorerTopologyProfile | None = None,
    initial_tool: str | None = None,
) -> tuple[bool, str]:
    resolved_launch = launch or build_explorer_playground_launch(
        dimension=start_dimension,
        explorer_profile=initial_explorer_profile,
        display_settings=display_settings,
        fonts_2d=fonts_2d,
        gameplay_mode=gameplay_mode,
        entry_source="lab",
        initial_tool=initial_tool,
    )
    display_settings = (
        display_settings
        if display_settings is not None
        else resolved_launch.display_settings
    )
    fonts_2d = fonts_2d if fonts_2d is not None else resolved_launch.fonts_2d
    state = _initial_topology_lab_state(
        resolved_launch.dimension,
        gameplay_mode=resolved_launch.gameplay_mode,
        initial_explorer_profile=resolved_launch.explorer_profile,
        initial_tool=resolved_launch.initial_tool,
    )
    clock = pygame.time.Clock()
    while state.running:
        _dt = clock.tick(60)
        _process_topology_lab_events(state)
        if not state.running:
            break
        screen, display_settings = _handle_pending_play_preview(
            state,
            screen,
            fonts,
            fonts_2d=fonts_2d,
            display_settings=display_settings,
        )
        _draw_menu(screen, fonts, state)
        pygame.display.flip()
    return _finalize_topology_lab_result(state)


def run_explorer_playground(
    screen: pygame.Surface,
    fonts,
    *,
    launch: ExplorerPlaygroundLaunch | None = None,
    dimension: int | None = None,
    explorer_profile: ExplorerTopologyProfile | None = None,
    display_settings=None,
    fonts_2d=None,
) -> tuple[bool, str]:
    resolved_launch = launch
    if resolved_launch is None:
        if dimension is None:
            raise ValueError("dimension is required when launch is not provided")
        resolved_launch = build_explorer_playground_launch(
            dimension=dimension,
            explorer_profile=explorer_profile,
            display_settings=display_settings,
            fonts_2d=fonts_2d,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            entry_source="explorer",
            initial_tool=TOOL_PROBE,
        )
    return run_topology_lab_menu(
        screen,
        fonts,
        launch=resolved_launch,
        start_dimension=resolved_launch.dimension,
        display_settings=resolved_launch.display_settings,
        fonts_2d=resolved_launch.fonts_2d,
    )
