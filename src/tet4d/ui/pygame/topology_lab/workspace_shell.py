from __future__ import annotations

import pygame

from tet4d.engine.runtime.topology_explorer_preview import explorer_probe_options
from tet4d.engine.topology_explorer import (
    build_explorer_transport_resolver,
    movement_steps_for_dimension,
)
from tet4d.ui.pygame.input.key_display import format_key_tuple
from tet4d.ui.pygame.keybindings import (
    EXPLORER_KEYS_2D,
    EXPLORER_KEYS_3D,
    EXPLORER_KEYS_4D,
    KEYS_2D,
    KEYS_3D,
    KEYS_4D,
)

from .common import TopologyLabHitTarget
from .copy import LAB_HINTS as _LAB_HINTS
from .controls_panel_values import (
    _explorer_active_glue_ids,
    _explorer_boundaries,
    _explorer_glue_labels,
    _explorer_permutation_labels,
    _explorer_preset_value_text,
    _explorer_preview_payload,
    _explorer_transform_label,
    _playability_panel_lines,
    _sandbox_neighbor_search_enabled,
)
from .explorer_tools import draw_tool_ribbon
from .piece_sandbox import (
    ensure_piece_sandbox,
    sandbox_cells,
    sandbox_lines,
    sandbox_validity,
)
from .preview import build_preview_lines, draw_preview_panel, draw_probe_controls
from .scene2d import draw_scene as draw_scene_2d
from .scene3d import draw_scene as draw_scene_3d
from .scene4d import draw_scene as draw_scene_4d
from .scene_state import (
    PANE_LABELS,
    TOOL_EDIT,
    TOOL_PROBE,
    WORKSPACE_EDITOR,
    WORKSPACE_LABELS,
    WORKSPACE_PLAY,
    WORKSPACE_SANDBOX,
    active_workspace_name as _active_workspace_name,
    controls_pane_active as _controls_pane_active,
    current_editor_tool as _current_editor_tool,
    current_explorer_draft as _current_explorer_draft,
    current_explorer_profile as _current_explorer_profile,
    current_highlighted_glue_id as _current_highlighted_glue_id,
    current_probe_coord as _current_probe_coord,
    current_probe_path as _current_probe_path,
    current_probe_trace as _current_probe_trace,
    current_selected_boundary_index as _current_selected_boundary_index,
    current_selected_glue_id as _current_selected_glue_id,
    ensure_probe_state as _ensure_probe_state,
    playground_dims_for_state as _board_dims_for_state,
    probe_trace_visible as _probe_trace_visible,
    scene_pane_active as _scene_pane_active,
    tool_is_edit,
    tool_is_sandbox,
    uses_general_explorer_editor as _uses_general_explorer_editor,
)
from .state_ownership import (
    current_sandbox_focus_coord as _current_sandbox_focus_coord,
    current_sandbox_focus_frame as _current_sandbox_focus_frame,
    current_sandbox_focus_path as _current_sandbox_focus_path,
    current_sandbox_focus_trace as _current_sandbox_focus_trace,
)
from .transform_editor import draw_action_buttons, draw_transform_editor
from .camera_controls import scene_camera_availability


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


def _action_buttons_for_state(state) -> tuple[tuple[str, str], ...]:
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_PLAY:
        return (
            ("play_preview", "Play This Topology"),
            ("explore_preview", "Explore This Topology"),
        )
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
    if _current_editor_tool(state) == TOOL_PROBE:
        return (("editor_probe_reset", "Reset Probe"),)
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


def _sandbox_scene_payload(state) -> tuple[tuple[tuple[int, ...], ...] | None, bool | None, str]:
    if not tool_is_sandbox(state.active_tool):
        return None, None, ""
    ensure_piece_sandbox(state)
    profile = _current_explorer_profile(state)
    assert profile is not None
    sandbox_cells_payload = sandbox_cells(state)
    sandbox_ok, sandbox_message = sandbox_validity(state, profile)
    return sandbox_cells_payload, sandbox_ok, sandbox_message


def _sandbox_anchor_coord(state) -> tuple[int, ...] | None:
    cells = sandbox_cells(state)
    if cells:
        return tuple(int(value) for value in cells[0])
    ensure_piece_sandbox(state)
    if state.sandbox is not None and state.sandbox.origin is not None:
        return tuple(int(value) for value in state.sandbox.origin)
    return _current_sandbox_focus_coord(state)


def _active_workspace_coord(state) -> tuple[int, ...] | None:
    if tool_is_sandbox(state.active_tool):
        if _sandbox_neighbor_search_enabled(state):
            return _current_sandbox_focus_coord(state)
        return _sandbox_anchor_coord(state)
    if _active_workspace_name(state) == WORKSPACE_EDITOR:
        return _current_probe_coord(state)
    return None


def _active_workspace_path(state) -> list[tuple[int, ...]]:
    if _active_workspace_name(state) == WORKSPACE_EDITOR and _probe_trace_visible(state):
        return _current_probe_path(state)
    return []


def _active_workspace_neighbor_markers(state) -> list[tuple[int, ...]]:
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


def _active_workspace_trace(state) -> list[str]:
    if tool_is_sandbox(state.active_tool):
        if not _sandbox_neighbor_search_enabled(state):
            return []
        return _current_sandbox_focus_trace(state)
    if _active_workspace_name(state) == WORKSPACE_EDITOR and _probe_trace_visible(state):
        return _current_probe_trace(state)
    return []


def _active_workspace_probe_frame(
    state,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if tool_is_sandbox(state.active_tool):
        return _current_sandbox_focus_frame(state)
    return tuple(range(state.dimension)), tuple(1 for _ in range(state.dimension))


def _draw_explorer_scene(
    screen: pygame.Surface,
    fonts,
    state,
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


def _workspace_selection_lines(state) -> list[str]:
    workspace_name = _active_workspace_name(state)
    workspace_label = WORKSPACE_LABELS[workspace_name]
    if workspace_name == WORKSPACE_EDITOR:
        tool_label = (
            "Edit tool" if _current_editor_tool(state) == TOOL_EDIT else "Probe tool"
        )
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


def _workspace_camera_lines(state) -> list[str]:
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


def _workspace_probe_lines(state) -> list[str]:
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


def _workspace_helper_lines(state) -> tuple[str, ...]:
    workspace_name = _active_workspace_name(state)
    if workspace_name == WORKSPACE_EDITOR:
        return (
            "Editor workspace: probe movement is always safe; seam mutation stays behind the explicit Edit tool.",
            "Editor movement target is the editor probe/selection only.",
            f"Editor Trace: {'on' if _probe_trace_visible(state) else 'off'}.",
        )
    if workspace_name == WORKSPACE_SANDBOX:
        neighbor_text = "on" if _sandbox_neighbor_search_enabled(state) else "off"
        return (
            "Sandbox workspace: piece controls and transport experiments stay separate from topology editing.",
            f"Sandbox Neighbors: {neighbor_text}.",
        )
    return (
        "Play workspace: launch and preview use the canonical gameplay runtime.",
        "Play movement target is the gameplay piece only.",
    )


def _workspace_guidance_lines(state) -> list[str]:
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


def _workspace_experiment_lines(state) -> list[str]:
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
    state,
    preview: dict[str, object] | None,
    preview_error: str | None,
) -> list[str]:
    del preview_error
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
    state,
    area: pygame.Rect,
    preview: dict[str, object] | None,
) -> list[TopologyLabHitTarget]:
    workspace_name = _active_workspace_name(state)
    if preview is None or workspace_name not in {WORKSPACE_EDITOR, WORKSPACE_SANDBOX}:
        return []
    profile = _current_explorer_profile(state)
    assert profile is not None
    if workspace_name == WORKSPACE_EDITOR and _current_editor_tool(state) != TOOL_PROBE:
        return []
    title = (
        "Sandbox piece moves"
        if workspace_name == WORKSPACE_SANDBOX
        else "Editor probe moves"
    )
    active_color = (78, 116, 92) if workspace_name == WORKSPACE_SANDBOX else (56, 92, 130)
    frame_permutation, frame_signs = _active_workspace_probe_frame(state)
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
    state,
    *,
    panel_x: int,
    panel_y: int,
    panel_w: int,
    panel_h: int,
    menu_w: int,
    analysis_pane_title: str,
    scene_pane_title: str,
    text_color: tuple[int, int, int],
    muted_color: tuple[int, int, int],
    highlight_color: tuple[int, int, int],
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
    focus_color = highlight_color if _scene_pane_active(state) else (92, 108, 144)
    pygame.draw.rect(screen, (16, 20, 34), main_panel_rect, border_radius=12)
    pygame.draw.rect(screen, focus_color, workspace_focus_rect, 2, border_radius=10)
    pygame.draw.rect(screen, (16, 20, 34), helper_rect, border_radius=12)
    pygame.draw.rect(screen, (96, 112, 152), helper_rect, 1, border_radius=12)
    scene_header = fonts.hint_font.render(
        scene_pane_title,
        True,
        highlight_color if _scene_pane_active(state) else muted_color,
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


def _hint_lines_for_state(state) -> tuple[str, ...]:
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
