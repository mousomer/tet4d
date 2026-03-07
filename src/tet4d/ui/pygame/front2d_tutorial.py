from __future__ import annotations

from typing import Any

import pygame

from tet4d.engine.runtime.menu_settings_state import (
    DEFAULT_OVERLAY_TRANSPARENCY,
    clamp_overlay_transparency,
)
from tet4d.engine.runtime.project_config import project_constant_int
from tet4d.engine.tutorial.api import (
    tutorial_apply_step_setup_2d_runtime,
    tutorial_board_dims_runtime,
    tutorial_ensure_piece_visibility_2d_runtime,
    tutorial_runtime_action_allowed_runtime,
    tutorial_runtime_allowed_actions_runtime,
    tutorial_runtime_consume_pending_setup_runtime,
    tutorial_runtime_create_session_runtime,
    tutorial_runtime_is_running_runtime,
    tutorial_runtime_next_stage_runtime,
    tutorial_runtime_observe_action_runtime,
    tutorial_runtime_overlay_payload_runtime,
    tutorial_runtime_previous_stage_runtime,
    tutorial_runtime_redo_stage_runtime,
    tutorial_runtime_required_action_runtime,
    tutorial_runtime_restart_runtime,
    tutorial_runtime_skip_runtime,
)
from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame.render.gfx_game import CELL_SIZE, GfxFonts, compute_game_layout
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.runtime_ui.help_menu import run_help_menu
from tet4d.ui.pygame.runtime_ui.tutorial_loop_common import tutorial_action_delay_ms
from tet4d.ui.pygame.runtime_ui.tutorial_overlay import draw_tutorial_overlay

from .front2d_input import overlay_action_for_key_2d

_TUTORIAL_DELAYED_ACTIONS_2D = {
    "move_x_neg",
    "move_x_pos",
    "move_y_neg",
    "move_y_pos",
    "rotate_xy_pos",
    "rotate_xy_neg",
    "soft_drop",
    "hard_drop",
}
_TUTORIAL_ALWAYS_LEGAL_ACTIONS_2D = {"menu", "help", "restart", "menu_back"}
_TUTORIAL_MOVE_DELTAS_2D = {
    "move_x_neg": (-1, 0),
    "move_x_pos": (1, 0),
    "move_y_neg": (0, -1),
    "move_y_pos": (0, 1),
}
_TUTORIAL_ROTATIONS_2D = {
    "rotate_xy_pos": 1,
    "rotate_xy_neg": -1,
}
_TUTORIAL_GRID_OFF_STEPS_2D = frozenset({"toggle_grid"})
_TUTORIAL_GRID_HELPER_STEPS_2D = frozenset({"line_fill", "full_clear_bonus"})
_TUTORIAL_MIN_VISIBLE_LAYER = project_constant_int(
    ("tutorial", "min_visible_layer"),
    2,
    min_value=0,
    max_value=10,
)
_TUTORIAL_TARGET_FILL_RGBA = (255, 214, 80, 72)
_TUTORIAL_TARGET_BORDER_RGBA = (255, 242, 168, 220)


def tutorial_create_session_2d(*, lesson_id: str) -> Any:
    return tutorial_runtime_create_session_runtime(lesson_id=lesson_id, mode="2d")


def tutorial_board_dims_2d() -> tuple[int, int]:
    dims = tutorial_board_dims_runtime("2d")
    return (int(dims[0]), int(dims[1]))


def tutorial_action_allowed(loop: Any, action_id: str) -> bool:
    if loop.tutorial_session is None:
        return True
    if (
        int(loop.tutorial_action_cooldown_ms) > 0
        and action_id in _TUTORIAL_DELAYED_ACTIONS_2D
    ):
        return False
    return tutorial_runtime_action_allowed_runtime(loop.tutorial_session, action_id)


def tutorial_observe_action(loop: Any, action_id: str) -> None:
    if loop.tutorial_session is None:
        return
    tutorial_runtime_observe_action_runtime(loop.tutorial_session, action_id)
    loop.tutorial_action_cooldown_ms = tutorial_action_delay_ms(action_id)


def _tutorial_required_action_legal_2d(loop: Any, action_id: str) -> bool:
    if action_id in _TUTORIAL_ALWAYS_LEGAL_ACTIONS_2D:
        return True
    return _tutorial_can_apply_piece_action_2d(loop, action_id)


def _tutorial_can_apply_piece_action_2d(loop: Any, action_id: str) -> bool:
    piece = loop.state.current_piece
    if piece is None or loop.state.game_over:
        return False
    if action_id == "hard_drop":
        return True
    if action_id == "soft_drop":
        return bool(loop.state._can_exist(piece.moved(0, 1)))
    move_delta = _TUTORIAL_MOVE_DELTAS_2D.get(action_id)
    if move_delta is not None:
        return bool(loop.state._can_exist(piece.moved(*move_delta)))
    rotation = _TUTORIAL_ROTATIONS_2D.get(action_id)
    if rotation is not None:
        return bool(loop.state._can_exist(piece.rotated(rotation)))
    return True


def _tutorial_has_legal_action_2d(loop: Any, action_ids: tuple[str, ...] | list[str]) -> bool:
    return any(_tutorial_required_action_legal_2d(loop, action_id) for action_id in action_ids)


def _tutorial_running_session_2d(loop: Any) -> object | None:
    tutorial_session = loop.tutorial_session
    if tutorial_session is None:
        return None
    if not tutorial_runtime_is_running_runtime(tutorial_session):
        return None
    return tutorial_session


def _redo_tutorial_stage_2d(loop: Any, tutorial_session: object) -> None:
    if tutorial_runtime_redo_stage_runtime(tutorial_session):
        apply_pending_tutorial_setup(loop)


def _tutorial_required_action_blocked_2d(loop: Any, tutorial_session: object) -> bool:
    required_action = tutorial_runtime_required_action_runtime(tutorial_session)
    if not required_action:
        return False
    return not _tutorial_required_action_legal_2d(loop, required_action)


def _tutorial_allowed_actions_blocked_2d(loop: Any, tutorial_session: object) -> bool:
    allowed_actions = tutorial_runtime_allowed_actions_runtime(tutorial_session)
    if not allowed_actions:
        return False
    return not _tutorial_has_legal_action_2d(loop, allowed_actions)


def enforce_tutorial_runtime_safety_2d(loop: Any) -> None:
    tutorial_session = _tutorial_running_session_2d(loop)
    if tutorial_session is None:
        return

    if loop.state.game_over:
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    visible = tutorial_ensure_piece_visibility_2d_runtime(
        loop.state,
        loop.cfg,
        min_visible_layer=int(_TUTORIAL_MIN_VISIBLE_LAYER),
    )
    if not visible:
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    if _tutorial_allowed_actions_blocked_2d(loop, tutorial_session):
        _redo_tutorial_stage_2d(loop, tutorial_session)
        return

    if _tutorial_required_action_blocked_2d(loop, tutorial_session):
        _redo_tutorial_stage_2d(loop, tutorial_session)



def _tutorial_overlay_start_from_setup(payload: dict[str, object]) -> float | None:
    setup_payload = payload.get("setup")
    if not isinstance(setup_payload, dict):
        return None
    raw_percent = setup_payload.get("overlay_start_percent")
    if isinstance(raw_percent, bool) or not isinstance(raw_percent, int):
        return None
    bounded_percent = max(0, min(100, int(raw_percent)))
    return float(bounded_percent) / 100.0


def apply_pending_tutorial_setup(loop: Any) -> None:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return
    payload = tutorial_runtime_consume_pending_setup_runtime(tutorial_session)
    if not isinstance(payload, dict):
        return
    step_id = str(payload.get("step_id", "")).strip().lower()
    tutorial_apply_step_setup_2d_runtime(loop.state, loop.cfg, payload)
    if step_id in _TUTORIAL_GRID_OFF_STEPS_2D:
        loop.grid_mode = GridMode.OFF
    elif step_id in _TUTORIAL_GRID_HELPER_STEPS_2D:
        loop.grid_mode = GridMode.HELPER
    start_overlay = _tutorial_overlay_start_from_setup(payload)
    if start_overlay is not None:
        loop.overlay_transparency = clamp_overlay_transparency(
            start_overlay,
            default=float(DEFAULT_OVERLAY_TRANSPARENCY),
        )



def handle_tutorial_hotkey(loop: Any, key: int) -> str | None:
    session = loop.tutorial_session
    if session is None:
        return None
    stage_nav = {
        pygame.K_F5: tutorial_runtime_previous_stage_runtime,
        pygame.K_F6: tutorial_runtime_next_stage_runtime,
        pygame.K_F7: tutorial_runtime_redo_stage_runtime,
    }
    step_action = stage_nav.get(key)
    if step_action is not None:
        if step_action(session):
            apply_pending_tutorial_setup(loop)
            loop.tutorial_action_cooldown_ms = 0
            play_sfx("menu_confirm" if key == pygame.K_F7 else "menu_move")
        return "continue"
    if key == pygame.K_F8:
        tutorial_runtime_skip_runtime(session)
        play_sfx("menu_move")
        return "menu"
    if key == pygame.K_F9:
        if tutorial_runtime_restart_runtime(session):
            apply_pending_tutorial_setup(loop)
            loop.tutorial_action_cooldown_ms = 0
        else:
            loop.on_restart()
        play_sfx("menu_confirm")
        return "continue"
    return None


def handle_overlay_hotkey(loop: Any, key: int) -> bool:
    action = overlay_action_for_key_2d(key)
    if action is None:
        return False
    if not tutorial_action_allowed(loop, action):
        return True
    direction = -1 if action == "overlay_alpha_dec" else 1
    loop.adjust_overlay_transparency(direction)
    tutorial_observe_action(loop, action)
    play_sfx("menu_move")
    return True


def open_help_screen(
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: Any,
) -> pygame.Surface:
    return run_help_menu(
        screen,
        fonts,
        dimension=2,
        context_label="2D Gameplay",
        on_escape_back=lambda: tutorial_observe_action(loop, "menu_back"),
    )


def restart_tutorial_if_running_2d(loop: Any) -> bool:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return False
    if not tutorial_runtime_is_running_runtime(tutorial_session):
        return False
    tutorial_observe_action(loop, "restart")
    restarted = tutorial_runtime_restart_runtime(tutorial_session)
    if not restarted:
        return False
    apply_pending_tutorial_setup(loop)
    loop.tutorial_action_cooldown_ms = 0
    return True


def pause_tutorial_restart_2d(loop: Any) -> bool:
    return restart_tutorial_if_running_2d(loop)


def pause_tutorial_skip_2d(loop: Any) -> bool:
    if loop.tutorial_session is None:
        return False
    return bool(tutorial_runtime_skip_runtime(loop.tutorial_session))


def _tutorial_target_cells_2d(loop: Any) -> tuple[tuple[int, int], ...]:
    session = loop.tutorial_session
    if session is None:
        return ()
    payload = tutorial_runtime_overlay_payload_runtime(session)
    step_id = str(payload.get("step_id", "")).strip().lower()
    if step_id not in {"target_drop", "line_fill", "full_clear_bonus"}:
        return ()

    if step_id == "full_clear_bonus":
        candidate_rows = (loop.cfg.height - 2, loop.cfg.height - 1)
    else:
        candidate_rows = (loop.cfg.height - 1,)
    target_cells: list[tuple[int, int]] = []
    for y in candidate_rows:
        for x in range(loop.cfg.width):
            if (x, y) in loop.state.board.cells:
                continue
            target_cells.append((x, y))
    return tuple(target_cells)


def _draw_tutorial_targets_2d(screen: pygame.Surface, loop: Any) -> None:
    target_cells = _tutorial_target_cells_2d(loop)
    if not target_cells:
        return
    board_offset, _panel_offset = compute_game_layout(screen, loop.cfg)
    ox, oy = board_offset
    for x, y in target_cells:
        rect = pygame.Rect(
            ox + x * CELL_SIZE + 2,
            oy + y * CELL_SIZE + 2,
            CELL_SIZE - 4,
            CELL_SIZE - 4,
        )
        fill = pygame.Surface(rect.size, pygame.SRCALPHA)
        fill.fill(_TUTORIAL_TARGET_FILL_RGBA)
        screen.blit(fill, rect.topleft)
        pygame.draw.rect(screen, _TUTORIAL_TARGET_BORDER_RGBA, rect, 2)


def draw_tutorial_overlays_2d(screen: pygame.Surface, fonts: GfxFonts, loop: Any) -> None:
    if loop.tutorial_session is None:
        return
    _draw_tutorial_targets_2d(screen, loop)
    draw_tutorial_overlay(
        screen,
        fonts,
        dimension=2,
        tutorial_session=loop.tutorial_session,
    )


def apply_tutorial_board_profile_2d(cfg: Any, *, tutorial_lesson_id: str | None) -> None:
    if not tutorial_lesson_id:
        return
    width, height = tutorial_board_dims_2d()
    cfg.width = int(width)
    cfg.height = int(height)


__all__ = [
    "apply_pending_tutorial_setup",
    "apply_tutorial_board_profile_2d",
    "draw_tutorial_overlays_2d",
    "enforce_tutorial_runtime_safety_2d",
    "handle_overlay_hotkey",
    "handle_tutorial_hotkey",
    "open_help_screen",
    "pause_tutorial_restart_2d",
    "pause_tutorial_skip_2d",
    "restart_tutorial_if_running_2d",
    "tutorial_action_allowed",
    "tutorial_board_dims_2d",
    "tutorial_create_session_2d",
    "tutorial_observe_action",
]
