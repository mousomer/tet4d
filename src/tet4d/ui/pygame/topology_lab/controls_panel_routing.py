from __future__ import annotations

import pygame

from tet4d.engine.runtime.api import runtime_binding_groups_for_dimension_runtime
from tet4d.ui.pygame.input.key_dispatch import match_bound_action

from .common import TopologyLabHitTarget
from .controls_panel_rows import _rows_for_state
from .scene_state import (
    PANE_CONTROLS,
    PANE_SCENE,
    TOOL_EDIT,
    TOOL_PLAY,
    TOOL_PROBE,
    TOOL_SANDBOX,
    TopologyLabState,
    controls_pane_active,
    current_explorer_profile,
    cycle_active_pane,
    scene_pane_active,
    set_active_tool,
    uses_general_explorer_editor,
)

_TOOL_SHORTCUT_KEYS = {
    pygame.K_e: TOOL_EDIT,
    pygame.K_i: TOOL_PROBE,
    pygame.K_b: TOOL_SANDBOX,
    pygame.K_p: TOOL_PLAY,
    pygame.K_g: TOOL_EDIT,
    pygame.K_t: TOOL_EDIT,
}
_PROBE_MOVEMENT_TOOLS = {TOOL_PROBE, TOOL_EDIT}
_SANDBOX_STEP_KEYS = {
    pygame.K_LEFT: "x-",
    pygame.K_RIGHT: "x+",
    pygame.K_UP: "y-",
    pygame.K_DOWN: "y+",
    pygame.K_PAGEUP: "y-",
    pygame.K_PAGEDOWN: "y+",
}


def set_active_pane_from_target(
    state: TopologyLabState,
    target: TopologyLabHitTarget,
) -> None:
    if target.kind in {"row_select", "row_step"}:
        state.active_pane = PANE_CONTROLS
        return
    state.active_pane = PANE_SCENE


def _binding_groups_for_dimension(
    dimension: int,
) -> dict[str, dict[str, tuple[int, ...]]]:
    return {
        str(group_name): {
            str(action): tuple(int(key) for key in keys)
            for action, keys in dict(binding_map).items()
        }
        for group_name, binding_map in runtime_binding_groups_for_dimension_runtime(
            int(dimension)
        ).items()
    }


def _explorer_bindings_for_dimension(dimension: int):
    return _binding_groups_for_dimension(dimension).get("explorer", {})


def _gameplay_bindings_for_dimension(dimension: int):
    return _binding_groups_for_dimension(dimension).get("game", {})


def _camera_bindings_for_dimension(dimension: int):
    return _binding_groups_for_dimension(dimension).get("camera", {})


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


def _bound_explorer_step_label(state: TopologyLabState, key: int) -> str | None:
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


def _bound_sandbox_rotation_action(state: TopologyLabState, key: int) -> str | None:
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


def _sandbox_piece_cycle_step(key: int) -> int | None:
    if key == pygame.K_LEFTBRACKET:
        return -1
    if key in (pygame.K_RIGHTBRACKET, pygame.K_SPACE):
        return 1
    return None


def handle_navigation_key(
    state: TopologyLabState,
    nav_key: int,
    selectable: tuple[int, ...],
    *,
    adjust_active_row,
    play_sfx,
) -> bool:
    if not controls_pane_active(state):
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
        if adjust_active_row(state, step):
            play_sfx("menu_move")
        return True
    return False


def _handle_save_export_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    save_profile,
    run_export,
) -> bool:
    if scene_pane_active(state):
        return False
    if key == pygame.K_s:
        save_profile(state)
        return True
    if key == pygame.K_e:
        run_export(state)
        return True
    return False


def _handle_tool_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    mod: int = 0,
) -> bool:
    if not uses_general_explorer_editor(state):
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


def _handle_probe_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    apply_probe_step,
) -> bool:
    if (
        state.active_tool not in _PROBE_MOVEMENT_TOOLS
        or not uses_general_explorer_editor(state)
        or not scene_pane_active(state)
    ):
        return False
    step_label = _bound_explorer_step_label(state, key)
    if step_label is None:
        step_label = _SANDBOX_STEP_KEYS.get(key)
    if step_label is None:
        return False
    apply_probe_step(state, step_label)
    return True


def _handle_sandbox_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    apply_sandbox_shortcut_step,
    cycle_sandbox_piece,
    ensure_piece_sandbox,
    handle_scene_camera_key,
    play_sfx,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    rotate_sandbox_piece_action,
    set_status,
) -> bool:
    if (
        state.active_tool != TOOL_SANDBOX
        or not uses_general_explorer_editor(state)
        or not scene_pane_active(state)
    ):
        return False
    step_label = _bound_explorer_step_label(state, key)
    if step_label is None:
        step_label = _SANDBOX_STEP_KEYS.get(key)
    if step_label is not None:
        apply_sandbox_shortcut_step(state, step_label)
        return True
    rotation_action = _bound_sandbox_rotation_action(state, key)
    if rotation_action is not None:
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = rotate_sandbox_piece_action(state, profile, rotation_action)
        set_status(state, message, is_error=not ok)
        return True
    if key == pygame.K_r:
        profile = current_explorer_profile(state)
        assert profile is not None
        ok, message = rotate_sandbox_piece(state, profile)
        set_status(state, message, is_error=not ok)
        return True
    cycle_step = _sandbox_piece_cycle_step(key)
    if cycle_step is not None:
        cycle_sandbox_piece(state, cycle_step)
        return True
    if key == pygame.K_0:
        reset_sandbox_piece(state)
        set_status(state, "Sandbox reset")
        return True
    if key == pygame.K_t:
        ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.show_trace = not state.sandbox.show_trace
        set_status(
            state,
            f"Sandbox trace {'shown' if state.sandbox.show_trace else 'hidden'}",
        )
        return True
    return False


def _handle_glue_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    remove_explorer_glue,
) -> bool:
    if not uses_general_explorer_editor(state):
        return False
    if key not in (pygame.K_DELETE, pygame.K_BACKSPACE):
        return False
    remove_explorer_glue(state)
    return True


def _handle_reset_defaults_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    reset_explorer_play_settings_to_defaults,
) -> bool:
    if key != pygame.K_F8 or not uses_general_explorer_editor(state):
        return False
    reset_explorer_play_settings_to_defaults(state)
    return True


def _handle_camera_shortcut(
    state: TopologyLabState,
    key: int,
    *,
    handle_scene_camera_key,
) -> bool:
    if (
        not uses_general_explorer_editor(state)
        or not scene_pane_active(state)
        or state.active_tool not in _PROBE_MOVEMENT_TOOLS
    ):
        return False
    camera_bindings = _camera_bindings_for_dimension(state.dimension)
    if not camera_bindings or match_bound_action(
        key,
        camera_bindings,
        tuple(camera_bindings),
    ) is None:
        return False
    return handle_scene_camera_key(state.dimension, key, state.scene_camera)


def handle_shortcut_key(
    state: TopologyLabState,
    key: int,
    *,
    mod: int = 0,
    apply_probe_step,
    apply_sandbox_shortcut_step,
    cycle_sandbox_piece,
    ensure_piece_sandbox,
    handle_scene_camera_key,
    play_sfx,
    remove_explorer_glue,
    reset_explorer_play_settings_to_defaults,
    reset_sandbox_piece,
    rotate_sandbox_piece,
    rotate_sandbox_piece_action,
    run_export,
    save_profile,
    set_status,
) -> bool:
    return (
        _handle_camera_shortcut(
            state,
            key,
            handle_scene_camera_key=handle_scene_camera_key,
        )
        or _handle_probe_shortcut(
            state,
            key,
            apply_probe_step=apply_probe_step,
        )
        or _handle_reset_defaults_shortcut(
            state,
            key,
            reset_explorer_play_settings_to_defaults=(
                reset_explorer_play_settings_to_defaults
            ),
        )
        or _handle_sandbox_shortcut(
            state,
            key,
            apply_sandbox_shortcut_step=apply_sandbox_shortcut_step,
            cycle_sandbox_piece=cycle_sandbox_piece,
            ensure_piece_sandbox=ensure_piece_sandbox,
            handle_scene_camera_key=handle_scene_camera_key,
            play_sfx=play_sfx,
            reset_sandbox_piece=reset_sandbox_piece,
            rotate_sandbox_piece=rotate_sandbox_piece,
            rotate_sandbox_piece_action=rotate_sandbox_piece_action,
            set_status=set_status,
        )
        or _handle_save_export_shortcut(
            state,
            key,
            save_profile=save_profile,
            run_export=run_export,
        )
        or _handle_tool_shortcut(state, key, mod=mod)
        or _handle_glue_shortcut(
            state,
            key,
            remove_explorer_glue=remove_explorer_glue,
        )
    )


def handle_enter_key(
    state: TopologyLabState,
    selectable: tuple[int, ...],
    *,
    adjust_active_row,
    apply_explorer_glue,
    play_sfx,
    remove_explorer_glue,
    run_export,
    run_experiments,
    save_profile,
) -> None:
    if scene_pane_active(state):
        if uses_general_explorer_editor(state) and state.active_tool == TOOL_PLAY:
            state.play_preview_requested = True
        return
    row = _rows_for_state(state)[selectable[state.selected]]
    if row.key == "save_profile":
        save_profile(state)
        return
    if row.key == "export":
        run_export(state)
        return
    if row.key == "experiments":
        run_experiments(state)
        return
    if row.key == "apply_glue":
        apply_explorer_glue(state)
        return
    if row.key == "remove_glue":
        remove_explorer_glue(state)
        return
    if row.key == "back":
        state.running = False
        return
    if adjust_active_row(state, 1):
        play_sfx("menu_move")
