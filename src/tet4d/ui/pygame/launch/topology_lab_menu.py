from __future__ import annotations

import pygame

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
)
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
    build_explorer_transport_resolver,
    movement_steps_for_dimension,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    explorer_probe_options,
)
from tet4d.ui.pygame.launch.topology_lab_state_factory import (
    _initial_topology_lab_state,
)
from tet4d.ui.pygame.topology_lab.app import (
    ExplorerPlaygroundLaunch,
    build_explorer_playground_launch,
    build_explorer_playground_settings,
)
from tet4d.ui.pygame.input.key_display import format_key_tuple
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.topology_lab import (
    ExplorerGlueDraft,
    ExplorerPlaygroundSettings,
    PANE_CONTROLS,
    PANE_LABELS,
    PANE_SCENE,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_INSPECT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TopologyLabHitTarget,
    apply_boundary_edit_pick,
    apply_boundary_pick,
    apply_glue_pick,
    boundaries_for_dimension,
    build_preview_lines,
    cycle_sandbox_piece,
    draw_action_buttons,
    draw_preview_panel,
    draw_probe_controls,
    draw_scene_2d,
    draw_scene_3d,
    draw_scene_4d,
    draw_tool_ribbon,
    draw_transform_editor,
    ensure_piece_sandbox,
    handle_scene_camera_mouse_event,
    move_sandbox_piece,
    pick_target,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    sandbox_cells,
    sandbox_lines,
    sandbox_validity,
    spawn_sandbox_piece,
    scene_camera_availability,
    set_active_tool,
    step_scene_camera,
    tool_is_edit,
    tool_is_sandbox,
    transform_preview_label,
    update_hover_target,
)
from tet4d.ui.pygame.topology_lab.scene_state import (
    current_explorer_draft as _current_explorer_draft,
    current_editor_tool as _current_editor_tool,
    current_explorer_profile as _current_explorer_profile,
    current_highlighted_glue_id as _current_highlighted_glue_id,
    current_probe_coord as _current_probe_coord,
    current_probe_path as _current_probe_path,
    current_probe_trace as _current_probe_trace,
    current_selected_boundary_index as _current_selected_boundary_index,
    current_selected_glue_id as _current_selected_glue_id,
    probe_trace_visible as _probe_trace_visible,
    select_projection_coord as _select_projection_coord,
    set_active_workspace as _set_active_workspace,
    set_probe_trace_visible as _set_probe_trace_visible,
    sync_canonical_playground_state as _sync_canonical_playground_state,
    update_explorer_draft as _update_explorer_draft,
    WORKSPACE_EDITOR,
    WORKSPACE_PLAY,
    WORKSPACE_SANDBOX,
    WORKSPACE_LABELS,
    active_workspace_name as _active_workspace_name,
)
from tet4d.ui.pygame.topology_lab.state_ownership import (
    current_sandbox_focus_coord as _current_sandbox_focus_coord,
    current_sandbox_focus_frame as _current_sandbox_focus_frame,
    current_sandbox_focus_path as _current_sandbox_focus_path,
    current_sandbox_focus_trace as _current_sandbox_focus_trace,
    select_sandbox_projection_coord as _select_sandbox_projection_coord,
)
from tet4d.ui.pygame.topology_lab.copy import (
    LAB_HINTS as _LAB_HINTS,
    LAB_SUBTITLE as _LAB_SUBTITLE,
    display_title_for_state as _display_title_for_state,
    topology_note_text as _topology_note_text,
)
from tet4d.ui.pygame.topology_lab.controls_panel import (
    _TopologyLabState,
    _adjust_row,
    _apply_explorer_glue,
    _apply_probe_step,
    _apply_sandbox_shortcut_step,
    _board_dims_for_state,
    _controls_pane_active,
    _cycle_dimension,
    _cycle_edge_rule,
    _cycle_explorer_preset,
    _ensure_play_settings,
    _ensure_probe_state,
    _explorer_active_glue_ids,
    _explorer_bindings_for_dimension,
    _explorer_boundaries,
    _explorer_glue_labels,
    _explorer_glues,
    _explorer_permutation_labels,
    _explorer_piece_set_label,
    _explorer_presets,
    _explorer_preset_value_text,
    _explorer_preview_payload,
    _explorer_transform_label,
    _gameplay_bindings_for_dimension,
    _handle_enter_key,
    _handle_navigation_key,
    _handle_shortcut_key,
    _launch_play_preview,
    _normalize_explorer_draft,
    _playability_panel_lines,
    _refresh_explorer_scene_state,
    _remove_explorer_glue,
    _reset_probe,
    _row_is_status_display,
    _row_supports_step_adjustment,
    _row_value_text,
    _rows_for_state,
    _run_export,
    _run_experiments,
    _save_profile,
    _scene_pane_active,
    _select_explorer_draft_slot,
    _selectable_row_indexes,
    _sandbox_neighbor_search_enabled,
    _set_active_pane_from_target,
    _set_status,
    _sync_explorer_state,
    _toggle_explorer_sign,
    _toggle_sandbox_neighbor_search,
    _uses_general_explorer_editor,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (130, 138, 168)
_ANALYSIS_PANE_TITLE = "Analysis View (secondary)"
_SCENE_PANE_TITLE = "Explorer Workspace (primary)"

# Re-exported compatibility surface kept for tests while menu cleanup stays
# in flight.
_COMPAT_EXPORTS = (
    ExplorerGlueDraft,
    ExplorerPlaygroundSettings,
    build_explorer_playground_settings,
    PANE_CONTROLS,
    PANE_SCENE,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_INSPECT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    boundaries_for_dimension,
    set_active_tool,
    _sync_canonical_playground_state,
    _apply_sandbox_shortcut_step,
    _cycle_dimension,
    _cycle_edge_rule,
    _explorer_presets,
    _refresh_explorer_scene_state,
    _sync_explorer_state,
)


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
    profile = _current_explorer_profile(state)
    assert profile is not None
    settings = _ensure_play_settings(state)
    dims = list(_board_dims_for_state(state))
    lines = [
        f"Explorer Playground {state.dimension}D",
        "Presets, board size, seam editing, sandbox play, and launch all happen in this shell.",
        f"Board: {dims}",
        f"Piece set: {_explorer_piece_set_label(state)}",
        f"Speed: {settings.speed_level}",
        _explorer_transform_label(state),
        "",
    ]
    lines.extend(_playability_panel_lines(state))
    lines.append("")
    lines.extend(_explorer_boundary_lines(state))
    lines.append("")
    lines.extend(_explorer_gluing_lines(state))
    lines.append("")
    preview, preview_error = _explorer_preview_payload(state)
    if preview is None:
        lines.append("Preview unavailable until the topology validates.")
        return lines
    lines.extend(_explorer_preview_lines(state, preview))
    return lines


def _action_buttons_for_state(state: _TopologyLabState) -> tuple[tuple[str, str], ...]:
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_PLAY:
        return (("play_preview", "Play This Topology"),
                ("explore_preview", "Explore This Topology"),)
    if workspace_name == WORKSPACE_SANDBOX:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        return (
            ("sandbox_spawn", "Spawn"),
            ("sandbox_prev", "Prev Piece"),
            ("sandbox_next", "Next Piece"),
            ("sandbox_rotate", "Rotate"),
            (
                "sandbox_trace",
                "Hide Path" if state.sandbox.show_trace else "Show Path",
            ),
            ("sandbox_reset", "Reset"),
        )
    if _current_editor_tool(state) == TOOL_INSPECT:
        return (("inspect_reset", "Reset Probe"),)
    return (("apply_glue", "Apply"), ("remove_glue", "Remove"))


def _explorer_workspace_layout(
    *,
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
    menu_w: int,
) -> tuple[
    pygame.Rect,
    pygame.Rect,
    pygame.Rect,
    pygame.Rect,
    pygame.Rect,
    pygame.Rect,
]:
    workspace_x = panel_x + menu_w + 18
    workspace_w = panel_w - menu_w - 30
    header_h = 26
    tool_h = 34
    actions_h = 38
    gap = 12
    helper_w = max(176, int(workspace_w * 0.28))
    helper_w = min(helper_w, max(176, workspace_w - gap - 320))
    main_w = workspace_w - helper_w - gap
    if main_w < 280:
        helper_w = max(160, workspace_w - gap - 280)
        main_w = workspace_w - helper_w - gap
    if main_w < 240:
        helper_w = max(144, workspace_w - gap - 240)
        main_w = workspace_w - helper_w - gap
    tool_rect = pygame.Rect(workspace_x, panel_y + 14 + header_h, workspace_w, tool_h)
    action_rect = pygame.Rect(
        workspace_x,
        panel_y + panel_h - actions_h - 16,
        main_w,
        actions_h,
    )
    content_y = tool_rect.bottom + gap
    content_h = max(320, action_rect.y - gap - content_y)
    top_h = max(212, min(332, int(content_h * 0.6)))
    editor_y = content_y + top_h + gap
    editor_h = max(170, content_y + content_h - editor_y)
    top_rect = pygame.Rect(workspace_x, content_y, main_w, top_h)
    editor_rect = pygame.Rect(workspace_x, editor_y, main_w, editor_h)
    helper_rect = pygame.Rect(top_rect.right + gap, content_y, helper_w, content_h)
    helper_controls_rect = pygame.Rect(
        helper_rect.x + 10,
        helper_rect.bottom - 92,
        helper_rect.width - 20,
        78,
    )
    return (
        tool_rect,
        top_rect,
        editor_rect,
        helper_rect,
        helper_controls_rect,
        action_rect,
    )

def _sandbox_scene_payload(
    state: _TopologyLabState,
) -> tuple[tuple[tuple[int, ...], ...] | None, bool | None, str]:
    if not tool_is_sandbox(state.active_tool):
        return None, None, ""
    ensure_piece_sandbox(state)
    profile = _current_explorer_profile(state)
    assert profile is not None
    sandbox_cells_payload = sandbox_cells(state)
    sandbox_ok, sandbox_message = sandbox_validity(state, profile)
    return sandbox_cells_payload, sandbox_ok, sandbox_message


def _sandbox_anchor_coord(state: _TopologyLabState) -> tuple[int, ...] | None:
    cells = sandbox_cells(state)
    if cells:
        return tuple(int(value) for value in cells[0])
    ensure_piece_sandbox(state)
    if state.sandbox is not None and state.sandbox.origin is not None:
        return tuple(int(value) for value in state.sandbox.origin)
    return _current_sandbox_focus_coord(state)


def _active_workspace_coord(state: _TopologyLabState) -> tuple[int, ...] | None:
    if tool_is_sandbox(state.active_tool):
        if _sandbox_neighbor_search_enabled(state):
            return _current_sandbox_focus_coord(state)
        return _sandbox_anchor_coord(state)
    if _active_workspace_name(state) == WORKSPACE_EDITOR:
        return _current_probe_coord(state)
    return None


def _active_workspace_path(state: _TopologyLabState) -> list[tuple[int, ...]]:
    if _active_workspace_name(state) == WORKSPACE_EDITOR and _probe_trace_visible(state):
        return _current_probe_path(state)
    return []


def _active_workspace_neighbor_markers(state: _TopologyLabState) -> list[tuple[int, ...]]:
    if tool_is_sandbox(state.active_tool) and _sandbox_neighbor_search_enabled(state):
        profile = _current_explorer_profile(state)
        if profile is None:
            return []
        try:
            resolver = build_explorer_transport_resolver(
                profile,
                _board_dims_for_state(state),
            )
        except ValueError:
            return []
        piece_cells = tuple(
            tuple(int(value) for value in coord)
            for coord in (sandbox_cells(state) or ())
        )
        if not piece_cells:
            return []
        markers: list[tuple[int, ...]] = []
        seen: set[tuple[int, ...]] = set()
        occupied = set(piece_cells)
        for step in movement_steps_for_dimension(state.dimension):
            result = resolver.resolve_piece_step(piece_cells, step)
            if result.moved_cells is None:
                continue
            for coord in result.moved_cells:
                target = tuple(int(value) for value in coord)
                if target in occupied or target in seen:
                    continue
                seen.add(target)
                markers.append(target)
        return markers
    return []


def _active_workspace_trace(state: _TopologyLabState) -> list[str]:
    if tool_is_sandbox(state.active_tool):
        if not _sandbox_neighbor_search_enabled(state):
            return []
        return _current_sandbox_focus_trace(state)
    if _active_workspace_name(state) == WORKSPACE_EDITOR and _probe_trace_visible(state):
        return _current_probe_trace(state)
    return []


def _active_workspace_frame(
    state: _TopologyLabState,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if tool_is_sandbox(state.active_tool):
        return _current_sandbox_focus_frame(state)
    return tuple(range(state.dimension)), tuple(1 for _ in range(state.dimension))


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
        selected_glue_id=_current_selected_glue_id(state),
        highlighted_glue_id=(
            state.hovered_glue_id or _current_highlighted_glue_id(state)
        ),
        hovered_boundary_index=state.hovered_boundary_index,
        selected_boundary_index=_current_selected_boundary_index(state),
        probe_coord=_active_workspace_coord(state),
        probe_path=tuple(_active_workspace_path(state)),
        neighbor_markers=tuple(_active_workspace_neighbor_markers(state)),
        sandbox_cells=sandbox_cells_payload,
        sandbox_valid=sandbox_ok,
        sandbox_message=sandbox_message,
    )
    if state.dimension == 2:
        return draw_scene_2d(screen, fonts, **scene_kwargs)
    scene_kwargs["profile"] = _current_explorer_profile(state)
    scene_kwargs["active_tool"] = state.active_tool
    if state.dimension == 4:
        return draw_scene_4d(screen, fonts, view=state.scene_camera, **scene_kwargs)
    return draw_scene_3d(screen, fonts, camera=state.scene_camera, **scene_kwargs)


def _workspace_selection_lines(state: _TopologyLabState) -> list[str]:
    workspace_name = _active_workspace_name(state)
    workspace_label = WORKSPACE_LABELS[workspace_name]
    if workspace_name == WORKSPACE_EDITOR:
        tool_label = "Edit tool" if _current_editor_tool(state) == TOOL_EDIT else "Probe tool"
    elif tool_is_sandbox(state.active_tool):
        tool_label = "Sandbox controls"
    else:
        tool_label = "Play launch"
    lines = [f"Pane: {PANE_LABELS.get(state.active_pane, state.active_pane)}"]
    selected_boundary_index = _current_selected_boundary_index(state)
    if selected_boundary_index is not None:
        boundary = _explorer_boundaries(state)[selected_boundary_index].label
        lines.append(f"Selected boundary: {boundary}")
    if state.hovered_boundary_index is not None:
        hovered = _explorer_boundaries(state)[state.hovered_boundary_index].label
        lines.append(f"Hover boundary: {hovered}")
    selected_glue_id = _current_selected_glue_id(state)
    if selected_glue_id:
        lines.append(f"Selected seam: {selected_glue_id}")
    elif state.hovered_glue_id:
        lines.append(f"Hover seam: {state.hovered_glue_id}")
    lines.append(f"Workspace: {workspace_label}")
    lines.append(f"Tool focus: {tool_label}")
    return lines


def _workspace_camera_lines(state: _TopologyLabState) -> list[str]:
    if not _uses_general_explorer_editor(state):
        return []
    probe_coord = _active_workspace_coord(state)
    if probe_coord is None:
        return []
    pairs = (
        ((0, 1), (0, 2), (1, 2))
        if state.dimension == 3
        else ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
    )
    labels: list[str] = []
    for axes in pairs:
        hidden_axes = [axis for axis in range(state.dimension) if axis not in axes]
        hidden_label = ", ".join(
            f"{'xyzw'[axis]}={probe_coord[axis]}" for axis in hidden_axes
        )
        pair_label = "".join("xyzw"[axis] for axis in axes)
        labels.append(f"{pair_label}[{hidden_label}]" if hidden_label else pair_label)
    return ["Projection slices: " + "  ".join(labels)]


def _workspace_probe_lines(state: _TopologyLabState) -> list[str]:
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_SANDBOX:
        if not _sandbox_neighbor_search_enabled(state):
            anchor = _sandbox_anchor_coord(state)
            lines = ["Sandbox neighbor-search: off"]
            if anchor is not None:
                lines.append(f"Sandbox anchor: {list(anchor)}")
            return lines
        focus_coord = _current_sandbox_focus_coord(state)
        lines = [
            f"Sandbox focus: {list(focus_coord)}",
            f"Focus steps: {max(0, len(_current_sandbox_focus_path(state)) - 1)}",
        ]
        lines.extend(f"  {line}" for line in _current_sandbox_focus_trace(state)[-3:])
        return lines
    if workspace_name != WORKSPACE_EDITOR:
        return []
    probe_coord = _current_probe_coord(state)
    if probe_coord is None:
        return []
    lines = [
        f"Editor cell: {list(probe_coord)}",
        f"Editor trace: {'on' if _probe_trace_visible(state) else 'off'}",
    ]
    if _probe_trace_visible(state):
        lines.append(f"Editor steps: {max(0, len(_current_probe_path(state)) - 1)}")
        lines.extend(f"  {line}" for line in _active_workspace_trace(state)[-3:])
    return lines


def _workspace_helper_lines(state: _TopologyLabState) -> tuple[str, ...]:
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_EDITOR:
        return (
            "Editor workspace: probe movement is always safe; seam mutation stays behind the explicit Edit tool.",
            "Editor movement target is the editor probe/selection only.",
            f"Editor Trace: {'on' if _probe_trace_visible(state) else 'off'}.",
        )
    if workspace_name == WORKSPACE_SANDBOX:
        neighbor_text = (
            "on"
            if _sandbox_neighbor_search_enabled(state)
            else "off"
        )
        return (
            "Sandbox workspace: piece controls and transport experiments stay separate from topology editing.",
            f"Sandbox Neighbors: {neighbor_text}.",
        )
    return (
        "Play workspace: launch and preview use the canonical gameplay runtime.",
        "Play movement target is the gameplay piece only.",
    )


def _workspace_guidance_lines(state: _TopologyLabState) -> list[str]:
    def _binding_text(bindings, action: str) -> str:
        return format_key_tuple(bindings.get(action, ()))

    def _compact_lines(prefix: str, parts: list[str]) -> list[str]:
        lines: list[str] = []
        for index in range(0, len(parts), 2):
            label = prefix if not lines else " " * len(prefix)
            lines.append(label + "  ".join(parts[index : index + 2]))
        return lines

    gameplay = _gameplay_bindings_for_dimension(state.dimension)
    explorer = _explorer_bindings_for_dimension(state.dimension)
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_EDITOR:
        context = (
            "Context: Editor / Edit."
            if _current_editor_tool(state) == TOOL_EDIT
            else "Context: Editor / Probe."
        )
    elif workspace_name == WORKSPACE_SANDBOX:
        neighbor_text = "on" if _sandbox_neighbor_search_enabled(state) else "off"
        context = f"Context: Sandbox. Neighbors {neighbor_text}."
    else:
        context = "Context: Play launch."
    move_parts = [
        f"X {_binding_text(gameplay, 'move_x_neg')} / {_binding_text(gameplay, 'move_x_pos')}",
        f"Y {_binding_text(explorer, 'move_up')} / {_binding_text(explorer, 'move_down')}",
    ]
    if state.dimension >= 3:
        move_parts.append(
            f"Z {_binding_text(gameplay, 'move_z_neg')} / {_binding_text(gameplay, 'move_z_pos')}"
        )
    if state.dimension >= 4:
        move_parts.append(
            f"W {_binding_text(gameplay, 'move_w_neg')} / {_binding_text(gameplay, 'move_w_pos')}"
        )
    rotate_parts = [
        f"XY {_binding_text(gameplay, 'rotate_xy_pos')} / {_binding_text(gameplay, 'rotate_xy_neg')}",
    ]
    if state.dimension >= 3:
        rotate_parts.extend(
            [
                f"XZ {_binding_text(gameplay, 'rotate_xz_pos')} / {_binding_text(gameplay, 'rotate_xz_neg')}",
                f"YZ {_binding_text(gameplay, 'rotate_yz_pos')} / {_binding_text(gameplay, 'rotate_yz_neg')}",
            ]
        )
    if state.dimension >= 4:
        rotate_parts.extend(
            [
                f"XW {_binding_text(gameplay, 'rotate_xw_pos')} / {_binding_text(gameplay, 'rotate_xw_neg')}",
                f"YW {_binding_text(gameplay, 'rotate_yw_pos')} / {_binding_text(gameplay, 'rotate_yw_neg')}",
                f"ZW {_binding_text(gameplay, 'rotate_zw_pos')} / {_binding_text(gameplay, 'rotate_zw_neg')}",
            ]
        )
    lines = [context]
    lines.extend(_compact_lines("Move: ", move_parts))
    lines.extend(_compact_lines("Rotate: ", rotate_parts))
    return lines


def _workspace_experiment_lines(state: _TopologyLabState) -> list[str]:
    batch = state.experiment_batch
    if not isinstance(batch, dict):
        return []
    total = int(batch.get("experiment_count", 0))
    valid = int(batch.get("valid_experiment_count", 0))
    if total <= 0:
        return []
    lines = ["", f"Experiments: {valid}/{total} valid"]
    recommendation = batch.get("recommendation")
    if isinstance(recommendation, dict):
        lines.append(f"Next: {recommendation.get('label', 'n/a')}")
        lines.append(f"Why: {recommendation.get('reason', 'no reason')}")
    return lines


def _workspace_preview_lines(
    state: _TopologyLabState,
    preview: dict[str, object] | None,
    preview_error: str | None,
) -> list[str]:
    lines = list(_playability_panel_lines(state))
    lines.append("")
    if preview is None:
        lines.append("Preview unavailable until the topology validates.")
    else:
        lines.extend(build_preview_lines(preview, dimension=state.dimension))
    lines.extend(_workspace_selection_lines(state))
    lines.extend(_workspace_experiment_lines(state))
    lines.extend(_workspace_camera_lines(state))
    lines.extend(_workspace_probe_lines(state))
    if tool_is_sandbox(state.active_tool):
        ensure_piece_sandbox(state)
        profile = _current_explorer_profile(state)
        assert profile is not None
        lines.append("")
        lines.extend(sandbox_lines(state, profile))
    return lines


def _draw_probe_controls_if_needed(
    screen: pygame.Surface,
    fonts,
    *,
    state: _TopologyLabState,
    area: pygame.Rect,
    preview: dict[str, object] | None,
) -> list[TopologyLabHitTarget]:
    workspace_name = _active_workspace_name(state)
    if preview is None or workspace_name not in {WORKSPACE_EDITOR, WORKSPACE_SANDBOX}:
        return []
    profile = _current_explorer_profile(state)
    assert profile is not None
    if workspace_name == WORKSPACE_EDITOR and _current_editor_tool(state) != TOOL_INSPECT:
        return []
    title = (
        "Sandbox piece moves"
        if workspace_name == WORKSPACE_SANDBOX
        else "Editor probe moves"
    )
    active_color = (78, 116, 92) if workspace_name == WORKSPACE_SANDBOX else (56, 92, 130)
    frame_permutation, frame_signs = _active_workspace_frame(state)
    return draw_probe_controls(
        screen,
        fonts,
        area=area,
        step_options=explorer_probe_options(
            profile,
            dims=_board_dims_for_state(state),
            coord=_active_workspace_coord(state)
            or tuple(0 for _ in range(state.dimension)),
            frame_permutation=frame_permutation,
            frame_signs=frame_signs,
        ),
        title=title,
        active_color=active_color,
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
    profile = _current_explorer_profile(state)
    assert profile is not None
    draft = _current_explorer_draft(state)
    assert draft is not None
    tool_rect, top_rect, editor_rect, helper_rect, _probe_rect, action_rect = (
        _explorer_workspace_layout(
            panel_x=panel_x,
            panel_y=panel_y,
            panel_w=panel_w,
            panel_h=panel_h,
            menu_w=menu_w,
        )
    )
    main_tool_rect = tool_rect.copy()
    ribbon_rect = main_tool_rect.copy()
    main_panel_rect = pygame.Rect(
        main_tool_rect.x - 8,
        main_tool_rect.y - 8,
        top_rect.width + 16,
        action_rect.bottom - main_tool_rect.y + 16,
    )
    workspace_focus_rect = pygame.Rect(
        main_panel_rect.x,
        main_panel_rect.y,
        main_panel_rect.width,
        main_panel_rect.height,
    )
    focus_color = _HIGHLIGHT_COLOR if _scene_pane_active(state) else (92, 108, 144)
    pygame.draw.rect(screen, (16, 20, 34), main_panel_rect, border_radius=12)
    pygame.draw.rect(screen, focus_color, workspace_focus_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (16, 20, 34), helper_rect, border_radius=12)
    pygame.draw.rect(screen, (96, 112, 152), helper_rect, 1, border_radius=12)
    scene_header = fonts.hint_font.render(
        _SCENE_PANE_TITLE,
        True,
        _HIGHLIGHT_COLOR if _scene_pane_active(state) else _MUTED_COLOR,
    )
    screen.blit(scene_header, (tool_rect.x + 2, panel_y + 18))
    hits = draw_tool_ribbon(
        screen,
        fonts,
        area=ribbon_rect,
        active_workspace=_active_workspace_name(state),
    )
    boundaries = _explorer_boundaries(state)
    source_boundary = boundaries[draft.source_index]
    target_boundary = boundaries[draft.target_index]
    active_glue_ids = _explorer_active_glue_ids(state)
    preview, _preview_error = _explorer_preview_payload(state)
    basis_arrows = list(state.scene_basis_arrows)
    preview_dims = state.scene_preview_dims or _board_dims_for_state(state)
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
            editable=tool_is_edit(state.active_tool),
            preset_label=_explorer_preset_value_text(state),
            glue_labels=_explorer_glue_labels(state),
            active_slot_index=draft.slot_index,
            transform_label=_explorer_transform_label(state),
            permutation_labels=_explorer_permutation_labels(state),
            selected_permutation_index=draft.permutation_index,
            signs=draft.signs,
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
    helper_lines = _workspace_guidance_lines(state)
    preview_body_rect = helper_rect.inflate(-10, -10)
    draw_preview_panel(
        screen,
        fonts,
        area=preview_body_rect,
        title=f"Explorer {state.dimension}D keys",
        lines=helper_lines,
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
        "experiments": _run_experiments,
        "inspect_reset": _reset_probe,
    }
    handler = handlers.get(action)
    if handler is None:
        if action == "editor_trace":
            _set_probe_trace_visible(state, not _probe_trace_visible(state))
            _set_status(
                state,
                f"Editor trace {'shown' if _probe_trace_visible(state) else 'hidden'}",
            )
            return True
        if action == "sandbox_neighbor_search":
            _toggle_sandbox_neighbor_search(state)
            return True
        return False
    handler(state)
    return True


def _handle_sandbox_action(state: _TopologyLabState, action: str) -> bool:
    if action == "sandbox_spawn":
        spawn_sandbox_piece(state)
        _set_status(state, "Sandbox piece spawned")
        return True
    if action == "sandbox_prev":
        cycle_sandbox_piece(state, -1)
        return True
    if action == "sandbox_next":
        cycle_sandbox_piece(state, 1)
        return True
    if action == "sandbox_rotate":
        profile = _current_explorer_profile(state)
        assert profile is not None
        ok, message = rotate_sandbox_piece(state, profile)
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
        _set_status(
            state, f"Sandbox path {'shown' if state.sandbox.show_trace else 'hidden'}"
        )
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
    if action == "explore_preview":
        state.explore_preview_requested = True
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
    if target.kind == "workspace_mode":
        _set_active_workspace(state, str(target.value))
        play_sfx("menu_move")
        return True
    if not tool_is_edit(state.active_tool):
        return False
    draft = _current_explorer_draft(state)
    if draft is None:
        return True
    if target.kind == "glue_slot":
        _select_explorer_draft_slot(state, int(target.value))
        _set_selected_row_by_key(state, "explorer_glue")
        play_sfx("menu_move")
        return True
    if target.kind == "perm_select":
        _update_explorer_draft(
            state,
            slot_index=draft.slot_index,
            source_index=draft.source_index,
            target_index=draft.target_index,
            permutation_index=int(target.value),
            signs=draft.signs,
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
                if str(target.value)
                in {
                    "save_profile",
                    "export",
                    "experiments",
                    "apply_glue",
                    "play_preview",
                }
                else "menu_move"
            )
        return True
    if target.kind == "probe_step" and _uses_general_explorer_editor(state):
        if tool_is_sandbox(state.active_tool):
            profile = _current_explorer_profile(state)
            assert profile is not None
            ok, message = move_sandbox_piece(state, profile, str(target.value))
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
    draft = _current_explorer_draft(state)
    if _uses_general_explorer_editor(state) and draft is not None:
        active_row = _rows_for_state(state)[
            _selectable_row_indexes(state)[state.selected]
        ].key
        if active_row in {"explorer_source", "explorer_target"}:
            _update_explorer_draft(
                state,
                slot_index=draft.slot_index,
                source_index=(
                    boundary_index
                    if active_row == "explorer_source"
                    else draft.source_index
                ),
                target_index=(
                    boundary_index
                    if active_row == "explorer_target"
                    else draft.target_index
                ),
                permutation_index=draft.permutation_index,
                signs=draft.signs,
            )
            _normalize_explorer_draft(state)
            play_sfx("menu_move")
            return True
    if button == 3 and tool_is_edit(state.active_tool):
        message = apply_boundary_edit_pick(state, boundary_index)
    else:
        message = apply_boundary_pick(state, boundary_index)
    _normalize_explorer_draft(state)
    if message:
        _set_status(state, message)
    play_sfx("menu_move")
    return True


def _handle_projection_cell_target(
    state: _TopologyLabState,
    target: TopologyLabHitTarget,
) -> bool:
    if target.kind != "projection_cell" or not _uses_general_explorer_editor(state):
        return False
    coord = tuple(int(value) for value in tuple(target.value))
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_SANDBOX:
        if not _sandbox_neighbor_search_enabled(state):
            _set_status(state, "Sandbox neighbor-search is disabled")
            return True
        selected = _select_sandbox_projection_coord(state, coord)
        if selected is not None:
            _set_status(state, f"Sandbox focus {list(selected)}")
            play_sfx("menu_move")
        return True
    if workspace_name != WORKSPACE_EDITOR:
        return False
    selected = _select_projection_coord(state, coord)
    if selected is not None:
        _set_status(state, f"Selected cell {list(selected)}")
        play_sfx("menu_move")
    return True


def _handle_row_mouse_target(
    state: _TopologyLabState,
    target: TopologyLabHitTarget,
) -> bool:
    if target.kind == "row_step":
        row_key, step = target.value
        _set_selected_row_by_key(state, str(row_key))
        row = next(
            (
                candidate
                for candidate in _rows_for_state(state)
                if candidate.key == str(row_key)
            ),
            None,
        )
        if row is not None and _adjust_row(state, row, int(step)):
            play_sfx("menu_move")
        return True
    if target.kind == "row_select":
        _set_selected_row_by_key(state, str(target.value))
        play_sfx("menu_move")
        return True
    return False


def _dispatch_mouse_target(
    state: _TopologyLabState, target: TopologyLabHitTarget, button: int
) -> bool:
    _set_active_pane_from_target(state, target)
    if _handle_projection_cell_target(state, target):
        return True
    if _handle_row_mouse_target(state, target):
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
    if target.kind in {
        "preset_step",
        "workspace_mode",
        "glue_slot",
        "perm_select",
        "sign_toggle",
    }:
        return _handle_mouse_editor_target(state, target)
    if target.kind in {"action", "probe_step"}:
        return _handle_mouse_action_target(state, target)
    return False


def _handle_scene_camera_event(
    state: _TopologyLabState, event: pygame.event.Event
) -> bool:
    if (
        not _uses_general_explorer_editor(state)
        or not _scene_pane_active(state)
        or _active_workspace_name(state) != WORKSPACE_EDITOR
    ):
        return False
    if event.type == pygame.MOUSEWHEEL:
        return handle_scene_camera_mouse_event(
            state.dimension,
            event,
            state.scene_camera,
            state.scene_mouse_orbit,
        )
    if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}:
        if getattr(event, "button", None) != 2:
            return False
        return handle_scene_camera_mouse_event(
            state.dimension,
            event,
            state.scene_camera,
            state.scene_mouse_orbit,
        )
    if event.type == pygame.MOUSEMOTION and getattr(
        state.scene_mouse_orbit, "dragging", False
    ):
        return handle_scene_camera_mouse_event(
            state.dimension,
            event,
            state.scene_camera,
            state.scene_mouse_orbit,
        )
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


def _hint_lines_for_state(state: _TopologyLabState) -> tuple[str, ...]:
    if not _uses_general_explorer_editor(state):
        return (
            *_LAB_HINTS,
            "Legacy compatibility: Normal Game keeps the retained profile rows and export bridge; Explorer Playground is the primary editor.",
        )
    gameplay = _gameplay_bindings_for_dimension(state.dimension)
    explorer = _explorer_bindings_for_dimension(state.dimension)
    pane_label = PANE_LABELS.get(state.active_pane, state.active_pane.title())
    move_lines = [
        f"Move X: {format_key_tuple(gameplay.get('move_x_neg', ()))} / {format_key_tuple(gameplay.get('move_x_pos', ()))}",
        f"Move Y: {format_key_tuple(explorer.get('move_up', ()))} / {format_key_tuple(explorer.get('move_down', ()))}",
    ]
    if state.dimension >= 3:
        move_lines.append(
            f"Move Z: {format_key_tuple(gameplay.get('move_z_neg', ()))} / {format_key_tuple(gameplay.get('move_z_pos', ()))}"
        )
    if state.dimension >= 4:
        move_lines.append(
            f"Move W: {format_key_tuple(gameplay.get('move_w_neg', ()))} / {format_key_tuple(gameplay.get('move_w_pos', ()))}"
        )
    lines = [
        "Explorer Playground keeps presets, board size, seam editing, sandbox, and play on one screen.",
        "Graphical explorer is the primary editor; Analysis View is optional secondary research and diagnostics.",
        f"Pane: {pane_label}   Tab/Shift+Tab switch pane   E/I choose Editor tool   B Sandbox   P Play   Enter plays from Play",
        "F8 resets the current dimension's Explorer play settings to the configured defaults",
        *move_lines,
    ]
    if _controls_pane_active(state):
        lines.append(
            "Analysis view (secondary): adjust settings, workspace-owned contextual controls, and Save/Export/Experiments/Back here   Status rows only report the current seam context"
        )
    else:
        lines.append(
            "Explorer workspace (primary): the right-side helper stays keys-first, Editor movement always updates the safe probe/selection target, and Edit still requires explicit Apply/Remove"
        )
    availability = scene_camera_availability(state.dimension)
    if availability.enabled:
        lines.append(
            "Projection sync: selecting a cell in any panel updates all visible slices "
            "and movement previews together"
        )
    lines.extend(_workspace_helper_lines(state))
    if tool_is_sandbox(state.active_tool):
        lines.append(
            "Sandbox tool: movement keys and the footer grid move the piece, gameplay rotation keys rotate it, Space or ] next piece, [ previous piece, 0 resets"
        )
    lines.append(
        "Workspace-owned contextual controls live in Analysis View: Editor owns Trace, Sandbox owns Neighbors, and the scene action bar stays focused on probe/apply, piece, or play actions"
    )
    lines.append(
        "Explorer Preset is adjusted from Analysis View   Transform editor only shows the current preset while editing the draft transform"
    )
    return tuple(lines)


def _selected_row_index(state: _TopologyLabState, selectable: tuple[int, ...]) -> int:
    if selectable:
        state.selected = max(0, min(state.selected, len(selectable) - 1))
        return selectable[state.selected]
    state.selected = 0
    return -1


def _draw_control_rows(
    screen: pygame.Surface,
    fonts,
    *,
    state: _TopologyLabState,
    rows,
    panel_x: int,
    panel_y: int,
    menu_w: int,
    selected_row: int,
) -> None:
    state.mouse_targets = []
    y = panel_y + (48 if _uses_general_explorer_editor(state) else 16)
    for idx, row in enumerate(rows):
        is_status_row = _row_is_status_display(row)
        selected = idx == selected_row and not is_status_row
        row_height = fonts.menu_font.get_height() + 10
        row_rect = pygame.Rect(panel_x + 14, y - 4, menu_w - 28, row_height)
        if not is_status_row:
            state.mouse_targets.append(
                TopologyLabHitTarget("row_select", row.key, row_rect)
            )
        if is_status_row:
            pygame.draw.rect(screen, (22, 28, 48), row_rect, border_radius=8)
            pygame.draw.rect(screen, (82, 96, 132), row_rect, 1, border_radius=8)
        color = (
            _DISABLED_COLOR
            if row.disabled
            else (
                _HIGHLIGHT_COLOR
                if selected
                else (_MUTED_COLOR if is_status_row else _TEXT_COLOR)
            )
        )
        value_color = (
            _DISABLED_COLOR
            if row.disabled
            else (_TEXT_COLOR if is_status_row else color)
        )
        if selected:
            hi = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 38), hi.get_rect(), border_radius=8)
            screen.blit(hi, row_rect.topleft)
        label_width = max(268, min(row_rect.width - 120, int(menu_w * 0.78)))
        value_width = max(96, row_rect.width - label_width - 56)
        label_text = row.label + (" (locked)" if row.disabled else "")
        label = fonts.menu_font.render(
            fit_text(fonts.menu_font, label_text, label_width),
            True,
            color,
        )
        value = fonts.menu_font.render(
            fit_text(
                fonts.menu_font,
                _row_value_text(state, row),
                value_width,
            ),
            True,
            value_color,
        )
        screen.blit(label, (panel_x + 22, y))
        value_right = panel_x + menu_w - 22
        if _row_supports_step_adjustment(row):
            button_size = 18
            plus_rect = pygame.Rect(
                value_right - button_size, y - 1, button_size, row_height - 2
            )
            value_x = plus_rect.x - 8 - value.get_width()
            minus_rect = pygame.Rect(
                value_x - 8 - button_size, y - 1, button_size, row_height - 2
            )
            for step_value, glyph, button_rect in (
                (-1, "-", minus_rect),
                (1, "+", plus_rect),
            ):
                pygame.draw.rect(screen, (78, 92, 128), button_rect, border_radius=6)
                pygame.draw.rect(
                    screen, (128, 148, 196), button_rect, 1, border_radius=6
                )
                glyph_surf = fonts.hint_font.render(glyph, True, _TEXT_COLOR)
                screen.blit(
                    glyph_surf,
                    (
                        button_rect.x
                        + (button_rect.width - glyph_surf.get_width()) // 2,
                        button_rect.y
                        + (button_rect.height - glyph_surf.get_height()) // 2,
                    ),
                )
                state.mouse_targets.append(
                    TopologyLabHitTarget("row_step", (row.key, step_value), button_rect)
                )
            screen.blit(value, (value_x, y))
        else:
            screen.blit(value, (value_right - value.get_width(), y))
        y += row_height + 2


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
    selected_row = _selected_row_index(state, selectable)

    if _uses_general_explorer_editor(state):
        panel_w = min(1200, max(560, width - 32))
        panel_h = min(height - 154, max(640, 132 + len(rows) * 36))
    else:
        panel_w = min(820, max(420, width - 40))
        panel_h = min(height - 178, 92 + len(rows) * 36)
    panel_x = (width - panel_w) // 2
    panel_y = max(126, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    if _uses_general_explorer_editor(state):
        menu_w = min(568, max(392, panel_w - 392))
        separator_x = panel_x + menu_w + 8
        pygame.draw.line(
            screen,
            (100, 116, 156),
            (separator_x, panel_y + 14),
            (separator_x, panel_y + panel_h - 14),
            1,
        )
        controls_rect = pygame.Rect(
            panel_x + 10, panel_y + 10, menu_w - 12, panel_h - 20
        )
        pygame.draw.rect(
            screen,
            (236, 212, 128) if _controls_pane_active(state) else (84, 96, 132),
            controls_rect,
            2,
            border_radius=10,
        )
        controls_header = fonts.hint_font.render(
            _ANALYSIS_PANE_TITLE,
            True,
            _HIGHLIGHT_COLOR if _controls_pane_active(state) else _MUTED_COLOR,
        )
        screen.blit(controls_header, (panel_x + 22, panel_y + 18))
    else:
        menu_w = panel_w

    _draw_control_rows(
        screen,
        fonts,
        state=state,
        rows=rows,
        panel_x=panel_x,
        panel_y=panel_y,
        menu_w=menu_w,
        selected_row=selected_row,
    )

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
    for hint in _hint_lines_for_state(state):
        hint_text = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_text, True, _MUTED_COLOR)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3
    if state.status:
        status_color = (255, 150, 150) if state.status_error else (170, 240, 170)
        status_text = fit_text(fonts.hint_font, state.status, width - 24)
        status_surf = fonts.hint_font.render(status_text, True, status_color)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 2))


def _dispatch_key(state: _TopologyLabState, key: int, mod: int = 0) -> None:
    nav_key = normalize_menu_navigation_key(key)
    selectable = _selectable_row_indexes(state)
    if _handle_shortcut_key(state, key, mod=mod):
        return
    if key == pygame.K_q or nav_key == pygame.K_ESCAPE:
        state.running = False
        return
    if _handle_navigation_key(state, nav_key, selectable):
        return
    if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
        _handle_enter_key(state, selectable)


def _process_pointer_event(state: _TopologyLabState, event: pygame.event.Event) -> bool:
    if event.type in {
        pygame.MOUSEMOTION,
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEWHEEL,
    } and _handle_scene_camera_event(state, event):
        if event.type == pygame.MOUSEMOTION and hasattr(event, "pos"):
            _handle_mouse_motion(state, event.pos)
        return True
    if event.type == pygame.MOUSEMOTION:
        _handle_mouse_motion(state, event.pos)
        return True
    if event.type == pygame.MOUSEBUTTONDOWN:
        _handle_mouse_down(state, event.pos, event.button)
        return True
    return False


def _process_single_topology_lab_event(
    state: _TopologyLabState, event: pygame.event.Event
) -> None:
    if event.type == pygame.QUIT:
        state.running = False
        return
    if _process_pointer_event(state, event):
        return
    if event.type == pygame.KEYDOWN:
        _dispatch_key(state, event.key, event.mod)


def _process_topology_lab_events(state: _TopologyLabState, dt_ms: float) -> None:
    for event in pygame.event.get():
        _process_single_topology_lab_event(state, event)
        if not state.running:
            return
    if _uses_general_explorer_editor(state):
        step_scene_camera(state.scene_camera, dt_ms)


def _handle_pending_play_preview(
    state: _TopologyLabState,
    screen: pygame.Surface,
    fonts,
    *,
    fonts_2d=None,
    display_settings=None,
) -> tuple[pygame.Surface, object | None]:
    play_requested = state.play_preview_requested
    explore_requested = state.explore_preview_requested

    if not (play_requested or explore_requested):
        return screen, display_settings

    state.play_preview_requested = False
    state.explore_preview_requested = False

    if play_requested and explore_requested:
        raise RuntimeError("Conflicting pending topology launch modes")

    return _launch_play_preview(
        state,
        screen,
        fonts,
        fonts_2d=fonts_2d,
        display_settings=display_settings,
        exploration_mode=explore_requested,
    )


def _finalize_topology_lab_result(state: _TopologyLabState) -> tuple[bool, str]:
    if state.dirty:
        ok, message = _save_profile(state)
        return ok, message
    if state.status:
        return (not state.status_error), state.status
    return True, "Explorer playground unchanged"


def _run_playground_shell(
    screen: pygame.Surface,
    fonts,
    *,
    resolved_launch: ExplorerPlaygroundLaunch,
    display_settings=None,
    fonts_2d=None,
) -> tuple[bool, str]:
    display_settings = (
        resolved_launch.display_settings
        if display_settings is None
        else display_settings
    )
    fonts_2d = resolved_launch.fonts_2d if fonts_2d is None else fonts_2d
    state = _initial_topology_lab_state(
        resolved_launch.dimension,
        gameplay_mode=resolved_launch.gameplay_mode,
        initial_explorer_profile=resolved_launch.explorer_profile,
        initial_tool=resolved_launch.initial_tool,
        play_settings=resolved_launch.settings_snapshot,
    )
    if resolved_launch.startup_notice:
        _set_status(state, resolved_launch.startup_notice, is_error=True)
    clock = pygame.time.Clock()
    while state.running:
        _dt = clock.tick(60)
        _process_topology_lab_events(state, _dt)
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
        )
    return _run_playground_shell(
        screen,
        fonts,
        resolved_launch=resolved_launch,
        display_settings=display_settings,
        fonts_2d=fonts_2d,
    )
