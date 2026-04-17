from __future__ import annotations

import pygame
from dataclasses import dataclass

from tet4d.engine.gameplay.topology import (
    EDGE_BEHAVIOR_OPTIONS,
    default_edge_rules_for_mode,
    topology_mode_from_index,
)
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    TopologyProfileState,
    designer_profiles_for_dimension,
    export_topology_profile_state,
    profile_state_from_preset,
    validate_topology_profile_state,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview as _compile_explorer_topology_preview,
    export_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_explorer_runtime import (
    compile_runtime_explorer_experiments,
    export_runtime_explorer_experiments,
    load_runtime_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_explorer_store import save_explorer_topology_profile
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    save_topology_profile,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx

from .interaction_audit import (
    record_interaction_handler,
    record_interaction_phase,
)
from tet4d.ui.pygame.topology_lab.controls_panel_rows import (
    _RowSpec,
    _rows_for_state,
    _selectable_row_indexes,
)
from tet4d.ui.pygame.topology_lab.controls_panel_actions import (
    _adjust_explorer_row,
    _apply_explorer_glue,
    _cycle_explorer_preset,  # noqa: F401 - compatibility re-export
    _explorer_presets,  # noqa: F401 - compatibility re-export
    _mark_updated,
    _normalize_explorer_draft,
    _remove_explorer_glue,
    _reset_explorer_play_settings_to_defaults,
    _select_explorer_draft_slot,  # noqa: F401 - compatibility re-export
    _set_topology_status_after_refresh,
    _toggle_explorer_sign,  # noqa: F401 - compatibility re-export
    _toggle_sandbox_neighbor_search,  # noqa: F401 - compatibility re-export
)
from tet4d.ui.pygame.topology_lab.controls_panel_values import (
    _sandbox_neighbor_search_enabled,  # noqa: F401 - compatibility re-export
)
from tet4d.ui.pygame.topology_lab.controls_panel_commands import (
    run_experiments as _run_experiments_impl,
    run_export as _run_export_impl,
    save_profile as _save_profile_impl,
)
from tet4d.ui.pygame.topology_lab.controls_panel_launch import (
    launch_play_preview as _launch_play_preview_impl,
)
from tet4d.ui.pygame.topology_lab.controls_panel_routing import (
    handle_enter_key as _handle_enter_key_impl,
    handle_navigation_key as _handle_navigation_key_impl,
    handle_shortcut_key as _handle_shortcut_key_impl,
    set_active_pane_from_target as _set_active_pane_from_target_impl,
)
from tet4d.ui.pygame.topology_lab.camera_controls import (
    ensure_mouse_orbit_state,
    ensure_scene_camera,
    handle_scene_camera_key,
)
from tet4d.ui.pygame.topology_lab.common import (
    TopologyLabHitTarget,
)
from tet4d.ui.pygame.topology_lab.scene_preview_state import (
    clear_explorer_scene_state as _clear_explorer_scene_state_impl,
    preview_signature_for_state as _preview_signature_for_state_impl,
    refresh_explorer_scene_state as _refresh_explorer_scene_state_impl,
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
    ExplorerPreviewCompileSignature,
    TOOL_EDIT,
    TopologyLabState,
    current_explorer_draft,
    current_explorer_profile,
    current_play_settings,
    current_probe_coord,
    current_probe_path,
    current_probe_trace,
    ensure_probe_state as _ensure_probe_state,
    ensure_explorer_draft,
    playground_dims_for_state,
    replace_explorer_profile,
    replace_play_settings,
    replace_probe_state,
    reset_probe_state,
    set_dirty,
    set_highlighted_glue_id,
    set_selected_boundary_index,  # noqa: F401 - compatibility re-export
    set_selected_glue_id,  # noqa: F401 - compatibility re-export
    sync_canonical_playground_state,
    uses_general_explorer_editor as uses_general_explorer_editor_runtime,
)
from tet4d.ui.pygame.topology_lab.app import (
    build_explorer_playground_settings,
    mode_settings_snapshot_for_dimension,
)
from tet4d.ui.pygame.topology_lab.play_launch import launch_playground_state_gameplay


_INITIAL_TOOL_BY_GAMEPLAY_MODE = {
    GAMEPLAY_MODE_NORMAL: TOOL_EDIT,
    GAMEPLAY_MODE_EXPLORER: TOOL_EDIT,
}
_TopologyLabState = TopologyLabState
_TOPOLOGY_DIMENSIONS = (2, 3, 4)


@dataclass(frozen=True)
class _LegacyRowAdjustment:
    handled: bool
    profile: TopologyProfileState | None = None
    error: str | None = None


def _board_dims_for_state(state: _TopologyLabState) -> tuple[int, ...]:
    return playground_dims_for_state(state)


def compile_explorer_topology_preview(*args, **kwargs):
    return _compile_explorer_topology_preview(*args, **kwargs)


def _configured_explorer_play_settings_for_dimension(
    dimension: int,
):
    return build_explorer_playground_settings(
        dimension=dimension,
        source_settings=mode_settings_snapshot_for_dimension(dimension),
    )


def _legacy_preset_profiles(state: _TopologyLabState):
    return designer_profiles_for_dimension(state.dimension, state.gameplay_mode)


def _legacy_preset_index(state: _TopologyLabState) -> int:
    profiles = _legacy_preset_profiles(state)
    preset_id = state.profile.preset_id
    if not preset_id:
        return 0
    for idx, profile in enumerate(profiles):
        if profile.profile_id == preset_id:
            return idx
    return 0


def _legacy_profile_from_preset(
    state: _TopologyLabState,
    step: int,
) -> TopologyProfileState:
    profiles = _legacy_preset_profiles(state)
    idx = (_legacy_preset_index(state) + step) % len(profiles)
    return profile_state_from_preset(
        dimension=state.dimension,
        gravity_axis=1,
        gameplay_mode=state.gameplay_mode,
        preset_index=idx,
        topology_mode=state.profile.topology_mode,
    )


def _legacy_profile_from_topology_mode(
    state: _TopologyLabState,
    step: int,
) -> TopologyProfileState:
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
    return validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=next_mode,
        edge_rules=rules,
        preset_id=None,
    )


def _legacy_profile_from_edge_rule(
    state: _TopologyLabState,
    *,
    axis: int,
    side: int,
    step: int,
) -> TopologyProfileState:
    current = state.profile.edge_rules[axis][side]
    idx = EDGE_BEHAVIOR_OPTIONS.index(current)
    next_value = EDGE_BEHAVIOR_OPTIONS[(idx + step) % len(EDGE_BEHAVIOR_OPTIONS)]
    rules = [tuple(axis_rule) for axis_rule in state.profile.edge_rules]
    axis_rule = list(rules[axis])
    axis_rule[side] = next_value
    rules[axis] = tuple(axis_rule)
    return validate_topology_profile_state(
        gameplay_mode=state.gameplay_mode,
        dimension=state.dimension,
        gravity_axis=1,
        topology_mode=state.profile.topology_mode,
        edge_rules=tuple(rules),
        preset_id=None,
    )


def _resolve_legacy_row_adjustment(
    state: _TopologyLabState,
    *,
    key: str,
    axis: int | None,
    side: int | None,
    disabled: bool,
    step: int,
    locked_message: str,
) -> _LegacyRowAdjustment:
    try:
        if key == "preset":
            return _LegacyRowAdjustment(
                handled=True,
                profile=_legacy_profile_from_preset(state, step),
            )
        if key == "topology_mode":
            return _LegacyRowAdjustment(
                handled=True,
                profile=_legacy_profile_from_topology_mode(state, step),
            )
        if axis is not None and side is not None:
            if disabled:
                return _LegacyRowAdjustment(handled=True, error=locked_message)
            return _LegacyRowAdjustment(
                handled=True,
                profile=_legacy_profile_from_edge_rule(
                    state,
                    axis=axis,
                    side=side,
                    step=step,
                ),
            )
    except ValueError as exc:
        return _LegacyRowAdjustment(handled=True, error=str(exc))
    return _LegacyRowAdjustment(handled=False)


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


def _clear_explorer_scene_state(state: _TopologyLabState) -> None:
    _clear_explorer_scene_state_impl(state)


def _preview_signature_for_state(
    state: _TopologyLabState,
) -> ExplorerPreviewCompileSignature | None:
    return _preview_signature_for_state_impl(state)


def _refresh_explorer_scene_state(state: _TopologyLabState) -> None:
    _refresh_explorer_scene_state_impl(state)


def _sync_explorer_state(state: _TopologyLabState) -> None:
    if not _uses_general_explorer_editor(state):
        state.explorer_profile = None
        state.explorer_draft = None
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
                "Editor probe is unavailable until the current gluing fits the board dimensions",
                is_error=True,
            )
            return
        start = probe_coord
        frame_permutation = tuple(range(state.dimension))
        frame_signs = tuple(1 for _ in range(state.dimension))
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
        replace_probe_state(
            state,
            coord=target,
            trace=trace[-6:],
            path=path[-20:],
            highlighted_glue_id=highlighted_glue_id,
            frame_permutation=frame_permutation,
            frame_signs=frame_signs,
        )
        _set_status(
            state,
            str(result["message"]),
            is_error=bool(result.get("blocked", False)),
        )


def _reset_probe(state: _TopologyLabState) -> None:
    reset_probe_state(state)
    _ensure_probe_state(state)
    probe_coord = current_probe_coord(state)
    if probe_coord is None:
        message = next(iter(current_probe_trace(state) or ()), "Probe unavailable")
        _set_status(state, message, is_error=True)
        return
    _set_status(state, f"Editor probe reset to {list(probe_coord)}")


def _apply_profile(state: _TopologyLabState, profile: TopologyProfileState) -> None:
    state.profile = profile
    _mark_updated(state)


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
        set_dirty(state, True)
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
    result = _resolve_legacy_row_adjustment(
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


def _save_profile(state: _TopologyLabState) -> tuple[bool, str]:
    return _save_profile_impl(
        state,
        save_explorer_topology_profile=save_explorer_topology_profile,
        save_topology_profile=save_topology_profile,
        set_status=_set_status,
    )


def _run_export(state: _TopologyLabState) -> None:
    _run_export_impl(
        state,
        export_explorer_topology_preview=export_explorer_topology_preview,
        export_topology_profile_state=export_topology_profile_state,
        play_sfx=play_sfx,
        set_status=_set_status,
    )


def _run_experiments(state: _TopologyLabState) -> None:
    _run_experiments_impl(
        state,
        compile_runtime_explorer_experiments=compile_runtime_explorer_experiments,
        export_runtime_explorer_experiments=export_runtime_explorer_experiments,
        play_sfx=play_sfx,
        set_status=_set_status,
    )


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


def _adjust_active_row(state: _TopologyLabState, step: int) -> bool:
    row = _rows_for_state(state)[_selectable_row_indexes(state)[state.selected]]
    return _adjust_row(state, row, step)


def _set_active_pane_from_target(
    state: _TopologyLabState, target: TopologyLabHitTarget
) -> None:
    _set_active_pane_from_target_impl(state, target)


def _handle_navigation_key(
    state: _TopologyLabState, nav_key: int, selectable: tuple[int, ...]
) -> bool:
    return _handle_navigation_key_impl(
        state,
        nav_key,
        selectable,
        adjust_active_row=_adjust_active_row,
        play_sfx=play_sfx,
    )


def _apply_sandbox_shortcut_step(state: _TopologyLabState, step_label: str) -> None:
    profile = current_explorer_profile(state)
    assert profile is not None
    ok, message = move_sandbox_piece(state, profile, step_label)
    _set_status(state, message, is_error=not ok)


def _handle_shortcut_key(state: _TopologyLabState, key: int, *, mod: int = 0) -> bool:
    return _handle_shortcut_key_impl(
        state,
        key,
        mod=mod,
        apply_probe_step=_apply_probe_step,
        apply_sandbox_shortcut_step=_apply_sandbox_shortcut_step,
        cycle_sandbox_piece=cycle_sandbox_piece,
        ensure_piece_sandbox=ensure_piece_sandbox,
        handle_scene_camera_key=handle_scene_camera_key,
        play_sfx=play_sfx,
        remove_explorer_glue=_remove_explorer_glue,
        reset_explorer_play_settings_to_defaults=(
            _reset_explorer_play_settings_to_defaults
        ),
        reset_sandbox_piece=reset_sandbox_piece,
        rotate_sandbox_piece=rotate_sandbox_piece,
        rotate_sandbox_piece_action=rotate_sandbox_piece_action,
        run_export=_run_export,
        save_profile=_save_profile,
        set_status=_set_status,
    )


def _handle_enter_key(state: _TopologyLabState, selectable: tuple[int, ...]) -> None:
    _handle_enter_key_impl(
        state,
        selectable,
        adjust_active_row=_adjust_active_row,
        apply_explorer_glue=_apply_explorer_glue,
        play_sfx=play_sfx,
        remove_explorer_glue=_remove_explorer_glue,
        run_export=_run_export,
        run_experiments=_run_experiments,
        save_profile=_save_profile,
    )


def _launch_play_preview(
    state: _TopologyLabState,
    screen: pygame.Surface,
    fonts_nd,
    *,
    fonts_2d=None,
    display_settings=None,
    exploration_mode = False,
) -> tuple[pygame.Surface, object | None]:
    return _launch_play_preview_impl(
        state,
        screen,
        fonts_nd,
        launch_playground_state_gameplay=launch_playground_state_gameplay,
        set_status=_set_status,
        display_title_for_state=_display_title_for_state,
        fonts_2d=fonts_2d,
        display_settings=display_settings,
        exploration_mode=exploration_mode,
    )
