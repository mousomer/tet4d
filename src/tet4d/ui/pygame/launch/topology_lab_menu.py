from __future__ import annotations

import tet4d.ui.pygame.topology_lab.controls_panel as _controls_panel_module

import pygame

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    TOPOLOGY_GAMEPLAY_MODE_OPTIONS,
    export_topology_profile_state,
)
from tet4d.engine.runtime.topology_explorer_bridge import (
    export_explorer_preview_from_legacy_profile,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    compile_explorer_topology_preview,
    explorer_probe_options,
    export_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_explorer_runtime import (
    load_runtime_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_explorer_store import (
    save_explorer_topology_profile,
)
from tet4d.engine.runtime.topology_profile_store import (
    load_topology_profile,
    save_topology_profile,
)
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
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
    cycle_active_pane,
    cycle_sandbox_piece,
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
    ensure_mouse_orbit_state,
    ensure_piece_sandbox,
    ensure_scene_camera,
    handle_scene_camera_key,
    handle_scene_camera_mouse_event,
    move_sandbox_piece,
    pick_target,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    rotate_sandbox_piece_action,
    sandbox_cells,
    sandbox_lines,
    sandbox_validity,
    spawn_sandbox_piece,
    scene_camera_availability,
    set_active_tool,
    step_scene_camera,
    transform_preview_label,
    update_hover_target,
)
from tet4d.ui.pygame.topology_lab.app import (
    ExplorerPlaygroundLaunch,
    build_explorer_playground_launch,
    build_explorer_playground_settings,
)
from tet4d.ui.pygame.topology_lab.play_launch import launch_playground_state_gameplay
from tet4d.ui.pygame.topology_lab.scene_state import (
    current_explorer_draft as _current_explorer_draft,
    current_highlighted_glue_id as _current_highlighted_glue_id,
    current_probe_coord as _current_probe_coord,
    current_probe_path as _current_probe_path,
    current_probe_trace as _current_probe_trace,
    current_selected_boundary_index as _current_selected_boundary_index,
    current_selected_glue_id as _current_selected_glue_id,
    sync_canonical_playground_state as _sync_canonical_playground_state,
)
from tet4d.ui.pygame.topology_lab.copy import (
    LAB_HINTS as _LAB_HINTS,
    LAB_SUBTITLE as _LAB_SUBTITLE,
    display_title_for_state as _display_title_for_state,
    topology_note_text as _topology_note_text,
)
from tet4d.ui.pygame.topology_lab.controls_panel import (
    _INITIAL_TOOL_BY_GAMEPLAY_MODE,
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
    _refresh_explorer_scene_state,
    _remove_explorer_glue,
    _reset_probe,
    _row_supports_step_adjustment,
    _row_value_text,
    _rows_for_state,
    _run_export,
    _run_experiments,
    _save_profile,
    _scene_pane_active,
    _select_explorer_draft_slot,
    _selectable_row_indexes,
    _set_active_pane_from_target,
    _set_status,
    _sync_explorer_state,
    _toggle_explorer_sign,
    _uses_general_explorer_editor,
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

_ORIGINAL_CYCLE_DIMENSION = _cycle_dimension
_ORIGINAL_HANDLE_ENTER_KEY = _handle_enter_key
_ORIGINAL_HANDLE_NAVIGATION_KEY = _handle_navigation_key
_ORIGINAL_HANDLE_SHORTCUT_KEY = _handle_shortcut_key
_ORIGINAL_LAUNCH_PLAY_PREVIEW = _launch_play_preview
_ORIGINAL_REFRESH_EXPLORER_SCENE_STATE = _refresh_explorer_scene_state
_ORIGINAL_RUN_EXPORT = _run_export
_ORIGINAL_SAVE_PROFILE = _save_profile
_ORIGINAL_SYNC_EXPLORER_STATE = _sync_explorer_state
_LEGACY_MENU_COMPAT_EXPORTS = (_cycle_edge_rule, _explorer_presets)
_ANALYSIS_PANE_TITLE = "Analysis View (secondary)"
_SCENE_PANE_TITLE = "Explorer Editor (primary)"


def _bind_controls_panel_compat() -> None:
    _controls_panel_module.PANE_CONTROLS = PANE_CONTROLS
    _controls_panel_module.PANE_SCENE = PANE_SCENE
    _controls_panel_module.TOOL_CREATE = TOOL_CREATE
    _controls_panel_module.TOOL_EDIT = TOOL_EDIT
    _controls_panel_module.TOOL_NAVIGATE = TOOL_NAVIGATE
    _controls_panel_module.TOOL_PLAY = TOOL_PLAY
    _controls_panel_module.TOOL_PROBE = TOOL_PROBE
    _controls_panel_module.TOOL_SANDBOX = TOOL_SANDBOX
    _controls_panel_module.boundaries_for_dimension = boundaries_for_dimension
    _controls_panel_module.compile_explorer_topology_preview = (
        compile_explorer_topology_preview
    )
    _controls_panel_module.cycle_active_pane = cycle_active_pane
    _controls_panel_module.default_draft_for_dimension = default_draft_for_dimension
    _controls_panel_module.ensure_mouse_orbit_state = ensure_mouse_orbit_state
    _controls_panel_module.ensure_scene_camera = ensure_scene_camera
    _controls_panel_module.export_explorer_preview_from_legacy_profile = (
        export_explorer_preview_from_legacy_profile
    )
    _controls_panel_module.export_explorer_topology_preview = (
        export_explorer_topology_preview
    )
    _controls_panel_module.export_topology_profile_state = (
        export_topology_profile_state
    )
    _controls_panel_module.handle_scene_camera_key = handle_scene_camera_key
    _controls_panel_module.load_runtime_explorer_topology_profile = (
        load_runtime_explorer_topology_profile
    )
    _controls_panel_module.launch_playground_state_gameplay = (
        launch_playground_state_gameplay
    )
    _controls_panel_module.play_sfx = play_sfx
    _controls_panel_module.rotate_sandbox_piece_action = (
        rotate_sandbox_piece_action
    )
    _controls_panel_module.save_explorer_topology_profile = (
        save_explorer_topology_profile
    )
    _controls_panel_module.save_topology_profile = save_topology_profile
    _controls_panel_module._apply_probe_step = _apply_probe_step
    _controls_panel_module._apply_sandbox_shortcut_step = (
        _apply_sandbox_shortcut_step
    )
    _controls_panel_module._cycle_dimension = _cycle_dimension
    _controls_panel_module._handle_enter_key = _handle_enter_key
    _controls_panel_module._handle_navigation_key = _handle_navigation_key
    _controls_panel_module._handle_shortcut_key = _handle_shortcut_key
    _controls_panel_module._launch_play_preview = _launch_play_preview
    _controls_panel_module._refresh_explorer_scene_state = (
        _refresh_explorer_scene_state
    )
    _controls_panel_module._remove_explorer_glue = _remove_explorer_glue
    _controls_panel_module._run_export = _run_export
    _controls_panel_module._save_profile = _save_profile
    _controls_panel_module._sync_explorer_state = _sync_explorer_state


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
            ("experiments", "Experiments"),
            ("play_preview", "Play This Topology"),
            ("save_profile", "Save"),
            ("back", "Back"),
        )
    if state.active_tool == TOOL_SANDBOX:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        return (
            ("sandbox_spawn", "Spawn"),
            ("sandbox_prev", "Prev Piece"),
            ("sandbox_next", "Next Piece"),
            ("sandbox_rotate", "Rotate"),
            ("sandbox_trace", "Hide Trace" if state.sandbox.show_trace else "Show Trace"),
            ("sandbox_reset", "Reset"),
            ("experiments", "Experiments"),
            ("play_preview", "Play This Topology"),
            ("save_profile", "Save"),
            ("back", "Back"),
        )
    return (
        ("apply_glue", "Apply"),
        ("remove_glue", "Remove"),
        ("save_profile", "Save"),
        ("export", "Export"),
        ("experiments", "Experiments"),
        ("play_preview", "Play This Topology"),
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
    header_h = 26
    tool_h = 34
    top_h = max(180, min(300, int(panel_h * 0.36)))
    editor_h = max(190, min(250, int(panel_h * 0.24)))
    actions_h = 38
    gap = 12
    tool_rect = pygame.Rect(workspace_x, panel_y + 14 + header_h, workspace_w, tool_h)
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
        selected_glue_id=_current_selected_glue_id(state),
        highlighted_glue_id=(
            state.hovered_glue_id or _current_highlighted_glue_id(state)
        ),
        hovered_boundary_index=state.hovered_boundary_index,
        selected_boundary_index=_current_selected_boundary_index(state),
        probe_coord=_current_probe_coord(state),
        probe_path=tuple(_current_probe_path(state)),
        sandbox_cells=sandbox_cells_payload,
        sandbox_valid=sandbox_ok,
        sandbox_message=sandbox_message,
    )
    if state.dimension == 2:
        return draw_scene_2d(screen, fonts, **scene_kwargs)
    if state.dimension == 4:
        return draw_scene_4d(screen, fonts, view=state.scene_camera, **scene_kwargs)
    return draw_scene_3d(screen, fonts, camera=state.scene_camera, **scene_kwargs)

def _workspace_selection_lines(state: _TopologyLabState) -> list[str]:
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
    lines.append(f"Tool: {state.active_tool.replace('_', ' ')}")
    return lines


def _workspace_camera_lines(state: _TopologyLabState) -> list[str]:
    availability = scene_camera_availability(state.dimension)
    if not availability.enabled or state.scene_camera is None:
        return []
    if state.dimension == 3:
        return [
            f"Camera: yaw {state.scene_camera.yaw_deg:.0f} pitch {state.scene_camera.pitch_deg:.0f} zoom {state.scene_camera.zoom:.0f}"
        ]
    if state.dimension == 4:
        return [
            f"Camera: yaw {state.scene_camera.yaw_deg:.0f} pitch {state.scene_camera.pitch_deg:.0f} xw {state.scene_camera.xw_deg:.0f} zw {state.scene_camera.zw_deg:.0f} zoom {state.scene_camera.zoom_scale:.2f}"
        ]
    return []


def _workspace_probe_lines(state: _TopologyLabState) -> list[str]:
    probe_coord = _current_probe_coord(state)
    if probe_coord is None:
        return []
    lines = [
        f"Probe: {list(probe_coord)}",
        f"Trace points: {max(0, len(_current_probe_path(state)) - 1)}",
    ]
    lines.extend(f"  {line}" for line in _current_probe_trace(state)[-3:])
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
    lines = (
        [f"Preview invalid: {preview_error}"]
        if preview is None
        else build_preview_lines(preview, dimension=state.dimension)
    )
    lines.extend(_workspace_selection_lines(state))
    lines.extend(_workspace_experiment_lines(state))
    lines.extend(_workspace_camera_lines(state))
    lines.extend(_workspace_probe_lines(state))
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
            dims=_board_dims_for_state(state),
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
    draft = _current_explorer_draft(state)
    assert draft is not None
    tool_rect, top_rect, editor_rect, preview_rect, action_rect = _explorer_workspace_layout(
        panel_x=panel_x,
        panel_y=panel_y,
        panel_w=panel_w,
        panel_h=panel_h,
        menu_w=menu_w,
    )
    workspace_focus_rect = pygame.Rect(
        tool_rect.x - 8,
        panel_y + 12,
        tool_rect.width + 16,
        action_rect.bottom - panel_y,
    )
    focus_color = _HIGHLIGHT_COLOR if _scene_pane_active(state) else (92, 108, 144)
    pygame.draw.rect(screen, focus_color, workspace_focus_rect, 2, border_radius=10)
    scene_header = fonts.hint_font.render(
        _SCENE_PANE_TITLE,
        True,
        _HIGHLIGHT_COLOR if _scene_pane_active(state) else _MUTED_COLOR,
    )
    screen.blit(scene_header, (tool_rect.x + 2, panel_y + 18))
    hits = draw_tool_ribbon(screen, fonts, area=tool_rect, active_tool=state.active_tool)

    boundaries = _explorer_boundaries(state)
    source_boundary = boundaries[draft.source_index]
    target_boundary = boundaries[draft.target_index]
    active_glue_ids = _explorer_active_glue_ids(state)
    preview, preview_error = _explorer_preview_payload(state)
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
        "experiments": _run_experiments,
        "probe_reset": _reset_probe,
    }
    handler = handlers.get(action)
    if handler is None:
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
        _sync_canonical_playground_state(state)
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
                if str(target.value) in {"save_profile", "export", "experiments", "apply_glue", "play_preview"}
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
            _sync_canonical_playground_state(state)
            play_sfx("menu_move")
            return True
    if button == 3 and state.active_tool in {TOOL_NAVIGATE, TOOL_INSPECT, TOOL_PROBE, TOOL_PLAY, TOOL_SANDBOX}:
        message = apply_boundary_edit_pick(state, boundary_index)
    else:
        message = apply_boundary_pick(state, boundary_index)
    _normalize_explorer_draft(state)
    _sync_canonical_playground_state(state)
    if message:
        _set_status(state, message)
    play_sfx("menu_move")
    return True


def _dispatch_mouse_target(
    state: _TopologyLabState, target: TopologyLabHitTarget, button: int
) -> bool:
    _set_active_pane_from_target(state, target)
    if target.kind == "row_step":
        row_key, step = target.value
        _set_selected_row_by_key(state, str(row_key))
        row = next((candidate for candidate in _rows_for_state(state) if candidate.key == str(row_key)), None)
        if row is not None and _adjust_row(state, row, int(step)):
            play_sfx("menu_move")
        return True
    if target.kind == "row_select":
        _set_selected_row_by_key(state, str(target.value))
        play_sfx("menu_move")
        return True
    if target.kind == "glue_pick" and _uses_general_explorer_editor(state):
        message = apply_glue_pick(state, str(target.value))
        _normalize_explorer_draft(state)
        _sync_canonical_playground_state(state)
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


def _handle_scene_camera_event(
    state: _TopologyLabState, event: pygame.event.Event
) -> bool:
    if (
        not _uses_general_explorer_editor(state)
        or not _scene_pane_active(state)
        or state.active_tool != TOOL_NAVIGATE
    ):
        return False
    return handle_scene_camera_mouse_event(
        state.dimension,
        event,
        state.scene_camera,
        state.scene_mouse_orbit,
    )


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
        return _LAB_HINTS
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
        f"Pane: {pane_label}   Tab/Shift+Tab switch pane   N/I/G/T/P/B choose tool   Enter plays from Play",
        *move_lines,
    ]
    if _controls_pane_active(state):
        lines.append(
            "Analysis view (secondary): Adjust settings, export, and experiments here   Seam authoring stays in Explorer Editor"
        )
    else:
        lines.append(
            "Explorer editor (primary): Left click selects boundary or seam   Right click boundary creates or edits a seam"
        )
    availability = scene_camera_availability(state.dimension)
    if availability.enabled:
        lines.append(
            f"Navigate tool camera: {availability.mouse_hint}   {availability.key_hint}"
        )
    if state.active_tool == TOOL_SANDBOX:
        lines.append(
            "Sandbox tool: movement keys move the piece, gameplay rotation keys rotate it, [ ] cycle piece, 0 resets"
        )
    else:
        lines.append(
            "Scene tools move the probe; sandbox is the only tool that captures piece movement"
        )
    lines.append(
        "Delete/Backspace removes the selected seam   Save and Export keep working from the current draft"
    )
    lines.append(
        "Experiment Pack compares the current draft against the preset family and recommends the next topology to try"
    )
    return tuple(lines)


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

    if _uses_general_explorer_editor(state):
        panel_w = min(1120, max(520, width - 40))
        panel_h = min(height - 190, max(620, 120 + len(rows) * 38))
    else:
        panel_w = min(820, max(420, width - 40))
        panel_h = min(height - 210, 80 + len(rows) * 38)
    panel_x = (width - panel_w) // 2
    panel_y = max(150, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    if _uses_general_explorer_editor(state):
        menu_w = min(360, max(260, panel_w - 340))
        separator_x = panel_x + menu_w + 8
        pygame.draw.line(
            screen,
            (100, 116, 156),
            (separator_x, panel_y + 14),
            (separator_x, panel_y + panel_h - 14),
            1,
        )
        controls_rect = pygame.Rect(panel_x + 10, panel_y + 10, menu_w - 12, panel_h - 20)
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

    state.mouse_targets = []
    y = panel_y + (48 if _uses_general_explorer_editor(state) else 16)
    for idx, row in enumerate(rows):
        selected = idx == selected_row
        row_height = fonts.menu_font.get_height() + 10
        row_rect = pygame.Rect(
            panel_x + 14, y - 4, menu_w - 28, row_height
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
                fonts.menu_font, _row_value_text(state, row), max(160, menu_w // 2 - 70)
            ),
            True,
            color,
        )
        screen.blit(label, (panel_x + 22, y))
        value_right = panel_x + menu_w - 22
        if _row_supports_step_adjustment(row):
            button_size = 18
            plus_rect = pygame.Rect(value_right - button_size, y - 1, button_size, row_height - 2)
            value_x = plus_rect.x - 8 - value.get_width()
            minus_rect = pygame.Rect(value_x - 8 - button_size, y - 1, button_size, row_height - 2)
            for step_value, glyph, button_rect in ((-1, '-', minus_rect), (1, '+', plus_rect)):
                pygame.draw.rect(screen, (78, 92, 128), button_rect, border_radius=6)
                pygame.draw.rect(screen, (128, 148, 196), button_rect, 1, border_radius=6)
                glyph_surf = fonts.hint_font.render(glyph, True, _TEXT_COLOR)
                screen.blit(
                    glyph_surf,
                    (
                        button_rect.x + (button_rect.width - glyph_surf.get_width()) // 2,
                        button_rect.y + (button_rect.height - glyph_surf.get_height()) // 2,
                    ),
                )
                state.mouse_targets.append(
                    TopologyLabHitTarget("row_step", (row.key, step_value), button_rect)
                )
            screen.blit(value, (value_x, y))
        else:
            screen.blit(value, (value_right - value.get_width(), y))
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


def _initialize_explicit_explorer_startup(
    state: _TopologyLabState,
    *,
    initial_explorer_profile: ExplorerTopologyProfile,
) -> None:
    state.active_pane = PANE_SCENE
    if state.play_settings is None:
        state.play_settings = build_explorer_playground_settings(
            dimension=state.dimension
        )
    state.explorer_profile = initial_explorer_profile
    ensure_explorer_draft(state)
    _normalize_explorer_draft(state)
    _sync_canonical_playground_state(state)
    state.scene_camera = ensure_scene_camera(state.dimension, state.scene_camera)
    state.scene_mouse_orbit = ensure_mouse_orbit_state(state.scene_mouse_orbit)
    _refresh_explorer_scene_state(state)
    _ensure_probe_state(state)


def _initial_topology_lab_state(
    start_dimension: int,
    *,
    gameplay_mode: str = GAMEPLAY_MODE_NORMAL,
    initial_explorer_profile: ExplorerTopologyProfile | None = None,
    initial_tool: str | None = None,
    play_settings: ExplorerPlaygroundSettings | None = None,
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
        play_settings=play_settings,
    )
    if mode == GAMEPLAY_MODE_EXPLORER and initial_explorer_profile is not None:
        _initialize_explicit_explorer_startup(
            state,
            initial_explorer_profile=initial_explorer_profile,
        )
        set_active_tool(state, initial_tool or _INITIAL_TOOL_BY_GAMEPLAY_MODE[mode])
        return state
    _sync_explorer_state(state)
    if mode == GAMEPLAY_MODE_EXPLORER:
        state.active_pane = PANE_SCENE
        if state.play_settings is None:
            state.play_settings = build_explorer_playground_settings(
                dimension=dimension
            )
            _sync_canonical_playground_state(state)
            _refresh_explorer_scene_state(state)
        if initial_explorer_profile is not None:
            state.explorer_profile = initial_explorer_profile
            ensure_explorer_draft(state)
            _normalize_explorer_draft(state)
            _sync_canonical_playground_state(state)
            _refresh_explorer_scene_state(state)
            _ensure_probe_state(state)
        set_active_tool(state, initial_tool or _INITIAL_TOOL_BY_GAMEPLAY_MODE[mode])
    elif initial_tool is not None:
        set_active_tool(state, initial_tool)
    return state


def _refresh_explorer_scene_state(state: _TopologyLabState) -> None:
    _bind_controls_panel_compat()
    _ORIGINAL_REFRESH_EXPLORER_SCENE_STATE(state)


def _sync_explorer_state(state: _TopologyLabState) -> None:
    _bind_controls_panel_compat()
    _ORIGINAL_SYNC_EXPLORER_STATE(state)


def _cycle_dimension(state: _TopologyLabState, step: int) -> None:
    _bind_controls_panel_compat()
    _ORIGINAL_CYCLE_DIMENSION(state, step)


def _save_profile(state: _TopologyLabState) -> tuple[bool, str]:
    _bind_controls_panel_compat()
    return _ORIGINAL_SAVE_PROFILE(state)


def _run_export(state: _TopologyLabState) -> None:
    _bind_controls_panel_compat()
    _ORIGINAL_RUN_EXPORT(state)


def _handle_navigation_key(
    state: _TopologyLabState, nav_key: int, selectable: tuple[int, ...]
) -> bool:
    _bind_controls_panel_compat()
    return _ORIGINAL_HANDLE_NAVIGATION_KEY(state, nav_key, selectable)


def _handle_shortcut_key(state: _TopologyLabState, key: int, *, mod: int = 0) -> bool:
    _bind_controls_panel_compat()
    return _ORIGINAL_HANDLE_SHORTCUT_KEY(state, key, mod=mod)


def _handle_enter_key(state: _TopologyLabState, selectable: tuple[int, ...]) -> None:
    _bind_controls_panel_compat()
    _ORIGINAL_HANDLE_ENTER_KEY(state, selectable)


def _launch_play_preview(
    state: _TopologyLabState,
    screen: pygame.Surface,
    fonts_nd,
    *,
    fonts_2d=None,
    display_settings=None,
) -> tuple[pygame.Surface, object | None]:
    _bind_controls_panel_compat()
    return _ORIGINAL_LAUNCH_PLAY_PREVIEW(
        state,
        screen,
        fonts_nd,
        fonts_2d=fonts_2d,
        display_settings=display_settings,
    )


def _process_pointer_event(
    state: _TopologyLabState, event: pygame.event.Event
) -> bool:
    if event.type in {
        pygame.MOUSEMOTION,
        pygame.MOUSEBUTTONDOWN,
        pygame.MOUSEBUTTONUP,
        pygame.MOUSEWHEEL,
    } and _handle_scene_camera_event(state, event):
        if event.type == pygame.MOUSEMOTION and hasattr(event, 'pos'):
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
    return _run_playground_shell(
        screen,
        fonts,
        resolved_launch=resolved_launch,
        display_settings=display_settings,
        fonts_2d=fonts_2d,
    )


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
