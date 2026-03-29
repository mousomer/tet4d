from __future__ import annotations

import pygame

from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
)
from tet4d.engine.topology_explorer import (
    ExplorerTopologyProfile,
)
from tet4d.ui.pygame.launch.topology_lab_state_factory import (
    _initial_topology_lab_state,
)
from tet4d.ui.pygame.topology_lab.app import (
    ExplorerPlaygroundLaunch,
    build_explorer_playground_launch,
    build_explorer_playground_settings,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.topology_lab import (
    ExplorerGlueDraft,
    ExplorerPlaygroundSettings,
    PANE_CONTROLS,
    PANE_SCENE,
    TOOL_CREATE,
    TOOL_EDIT,
    TOOL_NAVIGATE,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TopologyLabHitTarget,
    apply_boundary_edit_pick,
    apply_boundary_pick,
    apply_glue_pick,
    boundaries_for_dimension,
    cycle_sandbox_piece,
    draw_action_buttons,
    ensure_piece_sandbox,
    handle_scene_camera_mouse_event,
    move_sandbox_piece,
    pick_target,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    sandbox_cells,
    spawn_sandbox_piece,
    set_active_tool,
    step_scene_camera,
    tool_is_edit,
    tool_is_sandbox,
    transform_preview_label,
    update_hover_target,
)
from tet4d.ui.pygame.topology_lab.scene_state import (
    controls_pane_active as _controls_pane_active,
    current_dirty as _current_dirty,
    current_explorer_draft as _current_explorer_draft,
    current_explorer_profile as _current_explorer_profile,
    current_probe_coord as _current_probe_coord,
    current_probe_path as _current_probe_path,
    ensure_probe_state as _ensure_probe_state,
    playground_dims_for_state as _board_dims_for_state,
    probe_neighbors_visible as _probe_neighbors_visible,
    probe_trace_visible as _probe_trace_visible,
    scene_pane_active as _scene_pane_active,
    select_projection_coord as _select_projection_coord,
    set_probe_neighbors_visible as _set_probe_neighbors_visible,
    set_active_workspace as _set_active_workspace,
    set_probe_trace_visible as _set_probe_trace_visible,
    sync_canonical_playground_state as _sync_canonical_playground_state,
    update_explorer_draft as _update_explorer_draft,
    WORKSPACE_EDITOR,
    WORKSPACE_SANDBOX,
    active_workspace_name as _active_workspace_name,
)
from tet4d.ui.pygame.topology_lab.state_ownership import (
    select_sandbox_projection_coord as _select_sandbox_projection_coord,
)
from tet4d.ui.pygame.topology_lab.copy import (
    display_title_for_state as _copy_display_title_for_state,
)
from tet4d.ui.pygame.topology_lab.controls_panel_values import (
    _explorer_active_glue_ids,
    _explorer_boundaries,
    _explorer_piece_set_label,
    _playability_shell_chip_text,
    _explorer_preset_value_text,
    _explorer_preview_payload,
    _explorer_transform_label,
    _playability_panel_lines,
    _row_value_text,
    _sandbox_neighbor_search_enabled,
)
from tet4d.ui.pygame.topology_lab.controls_panel import (
    _TopologyLabState,
    _adjust_row,
    _apply_explorer_glue,
    _apply_probe_step,
    _apply_sandbox_shortcut_step,
    _cycle_dimension,
    _cycle_edge_rule,
    _cycle_explorer_preset,
    _ensure_play_settings,
    _explorer_glues,
    _explorer_presets,
    _handle_enter_key,
    _handle_navigation_key,
    _handle_shortcut_key,
    _launch_play_preview,
    _normalize_explorer_draft,
    _refresh_explorer_scene_state,
    _remove_explorer_glue,
    _reset_probe,
    _run_export,
    _run_experiments,
    _save_profile,
    _select_explorer_draft_slot,
    _set_active_pane_from_target,
    _set_status,
    _sync_explorer_state,
    _toggle_explorer_sign,
    _toggle_sandbox_neighbor_search,
    _uses_general_explorer_editor,
)
from tet4d.ui.pygame.topology_lab.controls_panel_rows import (
    _row_is_status_display,
    _row_supports_step_adjustment,
    _rows_for_state,
    _selectable_row_indexes,
)
from tet4d.ui.pygame.topology_lab.explorer_tools import draw_tool_ribbon
from tet4d.ui.pygame.topology_lab.workspace_shell import (
    _action_buttons_for_state,
    _active_workspace_coord,
    _active_workspace_neighbor_markers,
    _active_workspace_path,
    _draw_explorer_scene,
    _draw_explorer_workspace,
    _draw_probe_controls_if_needed,
    _explorer_workspace_layout,
    _hint_lines_for_state,
    _workspace_preview_lines,
    _workspace_probe_lines,
)
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_HIGHLIGHT_COLOR = (255, 224, 128)
_MUTED_COLOR = (192, 200, 228)
_DISABLED_COLOR = (130, 138, 168)
_ANALYSIS_PANE_TITLE = "Diagnostics"
_SCENE_PANE_TITLE = "Workspace"


def _display_title_for_state(state: _TopologyLabState) -> str:
    return _copy_display_title_for_state(state)

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
    sandbox_cells,
    _ensure_probe_state,
    _explorer_preset_value_text,
    _current_probe_coord,
    _current_probe_path,
    _action_buttons_for_state,
    _active_workspace_coord,
    _active_workspace_neighbor_markers,
    _active_workspace_path,
    _draw_explorer_scene,
    _draw_probe_controls_if_needed,
    _explorer_workspace_layout,
    _hint_lines_for_state,
    _workspace_preview_lines,
    _workspace_probe_lines,
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
        f"Topology Playground {state.dimension}D",
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
        "editor_probe_reset": _reset_probe,
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
        if action == "editor_probe_neighbors":
            _set_probe_neighbors_visible(state, not _probe_neighbors_visible(state))
            _set_status(
                state,
                "Editor probe neighbors shown"
                if _probe_neighbors_visible(state)
                else "Editor probe neighbors hidden",
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
        selectable = _selectable_row_indexes(state)
        active_row = None
        if selectable:
            selected = max(0, min(state.selected, len(selectable) - 1))
            active_row = _rows_for_state(state)[selectable[selected]].key
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
    state.mouse_targets = []

    rows = _rows_for_state(state)
    selectable = _selectable_row_indexes(state)
    selected_row = _selected_row_index(state, selectable)

    if _uses_general_explorer_editor(state):
        panel_w = min(1320, max(860, width - 24))
        panel_h = min(height - 24, max(660, height - 24))
    else:
        panel_w = min(820, max(420, width - 40))
        panel_h = min(height - 178, 92 + len(rows) * 36)
    panel_x = (width - panel_w) // 2
    panel_y = max(12, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 150), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    if _uses_general_explorer_editor(state):
        top_bar_h = 46
        bottom_bar_h = 44
        content_y = panel_y + top_bar_h + 8
        content_h = panel_h - top_bar_h - bottom_bar_h - 16
        menu_w = 290 if _scene_pane_active(state) else 350
        top_bar_rect = pygame.Rect(panel_x + 10, panel_y + 10, panel_w - 20, top_bar_h)
        pygame.draw.rect(screen, (16, 20, 34), top_bar_rect, border_radius=10)
        pygame.draw.rect(screen, (96, 112, 152), top_bar_rect, 1, border_radius=10)
        title = fonts.hint_font.render("Topology Playground", True, _TEXT_COLOR)
        screen.blit(title, (top_bar_rect.x + 14, top_bar_rect.y + 12))
        state.mouse_targets = draw_tool_ribbon(
            screen,
            fonts,
            area=pygame.Rect(top_bar_rect.x + 214, top_bar_rect.y + 8, 286, 30),
            active_workspace=_active_workspace_name(state),
        )
        validity_text = _playability_shell_chip_text(state)
        validity_color = (
            (120, 214, 140)
            if validity_text == "Valid"
            else (224, 92, 92) if validity_text == "Unsafe" else (238, 158, 116)
        )
        chip_text = fonts.hint_font.render(validity_text, True, validity_color)
        dimension_text = f"{state.dimension}D"
        dimension_label = fonts.hint_font.render(dimension_text, True, _MUTED_COLOR)
        dimension_rect = pygame.Rect(
            top_bar_rect.right
            - dimension_label.get_width()
            - 88
            - chip_text.get_width(),
            top_bar_rect.y + 8,
            dimension_label.get_width() + 22,
            28,
        )
        chip_rect = pygame.Rect(
            top_bar_rect.right - chip_text.get_width() - 38,
            top_bar_rect.y + 8,
            chip_text.get_width() + 22,
            28,
        )
        pygame.draw.rect(screen, (22, 28, 48), dimension_rect, border_radius=14)
        pygame.draw.rect(screen, (82, 96, 132), dimension_rect, 1, border_radius=14)
        screen.blit(
            dimension_label,
            (
                dimension_rect.x
                + (dimension_rect.width - dimension_label.get_width()) // 2,
                dimension_rect.y
                + (dimension_rect.height - dimension_label.get_height()) // 2,
            ),
        )
        pygame.draw.rect(screen, (22, 28, 48), chip_rect, border_radius=14)
        pygame.draw.rect(screen, validity_color, chip_rect, 1, border_radius=14)
        screen.blit(
            chip_text,
            (
                chip_rect.x + (chip_rect.width - chip_text.get_width()) // 2,
                chip_rect.y + (chip_rect.height - chip_text.get_height()) // 2,
            ),
        )
        separator_x = panel_x + menu_w + 8
        pygame.draw.line(
            screen,
            (100, 116, 156),
            (separator_x, content_y + 4),
            (separator_x, content_y + content_h - 4),
            1,
        )
        controls_rect = pygame.Rect(
            panel_x + 10, content_y, menu_w - 12, content_h
        )
        pygame.draw.rect(screen, (18, 22, 38), controls_rect, border_radius=10)
        pygame.draw.rect(
            screen,
            (236, 212, 128) if _controls_pane_active(state) else (84, 96, 132),
            controls_rect,
            2,
            border_radius=10,
        )
        controls_header = fonts.hint_font.render(
            _ANALYSIS_PANE_TITLE if _controls_pane_active(state) else _SCENE_PANE_TITLE,
            True,
            _HIGHLIGHT_COLOR if _controls_pane_active(state) else _MUTED_COLOR,
        )
        screen.blit(controls_header, (controls_rect.x + 14, controls_rect.y + 10))
    else:
        menu_w = panel_w
        content_y = panel_y
        content_h = panel_h

    _draw_control_rows(
        screen,
        fonts,
        state=state,
        rows=rows,
        panel_x=panel_x,
        panel_y=content_y,
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
                panel_y=content_y,
                panel_w=panel_w,
                panel_h=content_h,
                menu_w=menu_w,
                analysis_pane_title=_ANALYSIS_PANE_TITLE,
                scene_pane_title=_SCENE_PANE_TITLE,
                text_color=_TEXT_COLOR,
                muted_color=_MUTED_COLOR,
                highlight_color=_HIGHLIGHT_COLOR,
            )
        )

    if _uses_general_explorer_editor(state):
        bottom_rect = pygame.Rect(
            panel_x + 10,
            panel_y + panel_h - 54,
            panel_w - 20,
            40,
        )
        pygame.draw.rect(screen, (16, 20, 34), bottom_rect, border_radius=10)
        pygame.draw.rect(screen, (96, 112, 152), bottom_rect, 1, border_radius=10)
        chip_labels = list(_hint_lines_for_state(state))
        chip_x = bottom_rect.x + 10
        for label in chip_labels[:3]:
            chip_width = min(190, max(56, fonts.hint_font.size(label)[0] + 18))
            chip_rect = pygame.Rect(chip_x, bottom_rect.y + 8, chip_width, 24)
            pygame.draw.rect(screen, (22, 28, 48), chip_rect, border_radius=12)
            pygame.draw.rect(screen, (82, 96, 132), chip_rect, 1, border_radius=12)
            chip_text = fonts.hint_font.render(
                fit_text(fonts.hint_font, label, chip_rect.width - 12),
                True,
                _MUTED_COLOR,
            )
            screen.blit(
                chip_text,
                (
                    chip_rect.x + (chip_rect.width - chip_text.get_width()) // 2,
                    chip_rect.y + (chip_rect.height - chip_text.get_height()) // 2,
                ),
            )
            chip_x = chip_rect.right + 8
        actions = _action_buttons_for_state(state)
        action_count = max(1, len(actions))
        action_area_w = min(
            bottom_rect.width // 2,
            action_count * 96 + max(0, action_count - 1) * 8,
        )
        action_rect = pygame.Rect(
            bottom_rect.right - action_area_w - 10,
            bottom_rect.y + 6,
            action_area_w,
            28,
        )
        state.mouse_targets.extend(
            draw_action_buttons(
                screen,
                fonts,
                area=action_rect,
                actions=actions,
            )
        )


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
    if _current_dirty(state):
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
