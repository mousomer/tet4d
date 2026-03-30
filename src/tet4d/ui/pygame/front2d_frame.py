from __future__ import annotations

from typing import Callable, Optional

import pygame

from tet4d.ai.playbot.types import (
    bot_planner_algorithm_from_index,
    bot_planner_profile_from_index,
)
from tet4d.engine.core.model import Action
from tet4d.engine.gameplay.leveling import compute_speed_level
from tet4d.engine.tutorial.api import (
    tutorial_runtime_is_running_runtime,
    tutorial_runtime_sync_and_advance_runtime,
)
from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame.render.gfx_game import (
    ClearEffect2D,
    GfxFonts,
    draw_game_frame,
    gravity_interval_ms_from_config,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings_from_event,
)
from tet4d.ui.pygame.runtime_ui.audio import play_sfx
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import process_game_events

from .front2d_session import LoopContext2D
from .front2d_tutorial import (
    apply_pending_tutorial_setup,
    draw_tutorial_overlays_2d,
    enforce_tutorial_runtime_safety_2d,
    open_help_screen,
)
from .front2d_results import _resolve_loop_decision, _resolve_terminal_status


def _step_gravity_tick(
    state, gravity_accumulator: int, gravity_interval_ms: int
) -> int:
    if not state.game_over and gravity_accumulator >= gravity_interval_ms:
        state.step(Action.NONE)
        return 0
    return gravity_accumulator


def _update_clear_animation(
    *,
    state,
    last_lines_cleared: int,
    clear_anim_levels: tuple[int, ...],
    clear_anim_elapsed_ms: float,
    clear_anim_duration_ms: float,
    dt_ms: int,
) -> tuple[tuple[int, ...], float, int]:
    if state.lines_cleared != last_lines_cleared:
        clear_anim_levels = tuple(state.board.last_cleared_levels)
        clear_anim_elapsed_ms = 0.0
        last_lines_cleared = state.lines_cleared
    if clear_anim_levels:
        clear_anim_elapsed_ms += dt_ms
        if clear_anim_elapsed_ms >= clear_anim_duration_ms:
            return (), 0.0, last_lines_cleared
    return clear_anim_levels, clear_anim_elapsed_ms, last_lines_cleared


def _clear_effect(
    levels: tuple[int, ...], elapsed_ms: float, duration_ms: float
) -> Optional[ClearEffect2D]:
    if not levels:
        return None
    return ClearEffect2D(
        levels=levels,
        progress=min(1.0, elapsed_ms / duration_ms),
    )


def _maybe_apply_auto_speedup(loop: LoopContext2D) -> int | None:
    target_speed_level = compute_speed_level(
        start_level=int(loop.base_speed_level),
        lines_cleared=int(loop.state.lines_cleared),
        enabled=bool(loop.auto_speedup_enabled),
        lines_per_level=int(loop.lines_per_level),
    )
    if int(target_speed_level) == int(loop.cfg.speed_level):
        return None
    loop.cfg.speed_level = int(target_speed_level)
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, int(loop.bot_speed_level))
    loop.gravity_accumulator = 0
    loop.refresh_score_multiplier()
    return gravity_interval_ms


def _configure_game_loop(
    *,
    loop: LoopContext2D,
    bot_speed_level: int,
    bot_algorithm_index: int,
    bot_profile_index: int,
    bot_budget_ms: int,
) -> int:
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, bot_speed_level)
    loop.bot.configure_planner(
        ndim=2,
        dims=(loop.cfg.width, loop.cfg.height),
        profile=bot_planner_profile_from_index(bot_profile_index),
        budget_ms=bot_budget_ms,
        algorithm=bot_planner_algorithm_from_index(bot_algorithm_index),
    )
    loop.refresh_score_multiplier()
    return gravity_interval_ms


def _sync_runtime_speed(loop: LoopContext2D) -> int:
    gravity_interval_ms = gravity_interval_ms_from_config(loop.cfg)
    loop.bot.configure_speed(gravity_interval_ms, int(loop.bot_speed_level))
    return gravity_interval_ms


def _advance_simulation(
    *,
    loop: LoopContext2D,
    dt: int,
    gravity_interval_ms: int,
    tutorial_step_pause_active: bool = False,
) -> None:
    if tutorial_step_pause_active or loop.cfg.exploration_mode:
        loop.gravity_accumulator = 0
        return
    loop.bot.tick_2d(loop.state, dt)
    if loop.bot.controls_descent:
        loop.gravity_accumulator = 0
        return
    loop.gravity_accumulator = _step_gravity_tick(
        loop.state,
        loop.gravity_accumulator,
        gravity_interval_ms,
    )


def _update_feedback_and_animation(
    *,
    loop: LoopContext2D,
    dt: int,
    clear_anim_duration_ms: float,
) -> None:
    if loop.state.lines_cleared != loop.last_lines_cleared:
        play_sfx("clear")
    if loop.state.game_over and not loop.was_game_over:
        play_sfx("game_over")
    loop.was_game_over = loop.state.game_over
    (
        loop.clear_anim_levels,
        loop.clear_anim_elapsed_ms,
        loop.last_lines_cleared,
    ) = _update_clear_animation(
        state=loop.state,
        last_lines_cleared=loop.last_lines_cleared,
        clear_anim_levels=loop.clear_anim_levels,
        clear_anim_elapsed_ms=loop.clear_anim_elapsed_ms,
        clear_anim_duration_ms=clear_anim_duration_ms,
        dt_ms=dt,
    )


def _handle_loop_event_cycle(
    *,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    display_settings: DisplaySettings,
    restart_with_record: Callable[[], None],
    record_session: Callable[[str], None],
    pause_menu_runner: Callable[..., tuple[str, pygame.Surface]],
) -> tuple[pygame.Surface, DisplaySettings, bool | None, bool]:
    def _runtime_event_handler(event: pygame.event.Event) -> None:
        nonlocal display_settings
        display_settings = capture_windowed_display_settings_from_event(
            display_settings,
            event=event,
        )

    decision = process_game_events(
        keydown_handler=loop.keydown_handler,
        on_restart=restart_with_record,
        on_toggle_grid=loop.on_toggle_grid,
        event_handler=_runtime_event_handler,
    )
    if decision == "help":
        return open_help_screen(screen, fonts, loop), display_settings, None, True

    status, next_screen = _resolve_loop_decision(
        decision=decision,
        screen=screen,
        fonts=fonts,
        loop=loop,
        pause_menu_runner=pause_menu_runner,
    )
    terminal = _resolve_terminal_status(status, record_session=record_session)
    if terminal is not None:
        return next_screen, display_settings, terminal, False
    if status == "restart":
        record_session("restart")
        return next_screen, display_settings, None, True
    return next_screen, display_settings, None, False


def _run_game_frame_2d(
    *,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    dt: int,
    clear_anim_duration_ms: float,
) -> None:
    tutorial_step_pause_active = (
        loop.tutorial_session is not None
        and tutorial_runtime_is_running_runtime(loop.tutorial_session)
    )
    gravity_interval_ms = _sync_runtime_speed(loop)
    _advance_simulation(
        loop=loop,
        dt=dt,
        gravity_interval_ms=gravity_interval_ms,
        tutorial_step_pause_active=tutorial_step_pause_active,
    )
    _update_feedback_and_animation(
        loop=loop,
        dt=dt,
        clear_anim_duration_ms=clear_anim_duration_ms,
    )
    _maybe_apply_auto_speedup(loop)
    if loop.tutorial_session is not None:
        tutorial_runtime_sync_and_advance_runtime(
            loop.tutorial_session,
            lines_cleared=int(loop.state.lines_cleared),
            overlay_transparency=float(loop.overlay_transparency),
            grid_visible=bool(loop.grid_mode != GridMode.OFF),
            grid_mode=str(loop.grid_mode.value),
            board_cell_count=len(loop.state.board.cells),
        )
        apply_pending_tutorial_setup(loop)
        enforce_tutorial_runtime_safety_2d(loop)
        if not tutorial_runtime_is_running_runtime(loop.tutorial_session):
            loop.tutorial_session = None
            loop.tutorial_action_cooldown_ms = 0
    clear_effect = _clear_effect(
        loop.clear_anim_levels,
        loop.clear_anim_elapsed_ms,
        clear_anim_duration_ms,
    )
    loop.rotation_anim.observe(
        loop.state.current_piece,
        dt,
        animate_translation=loop.state.consume_translation_animation_hint(),
    )
    active_overlay = loop.rotation_anim.overlay_state(loop.state.current_piece)
    draw_game_frame(
        screen,
        loop.cfg,
        loop.state,
        fonts,
        grid_mode=loop.grid_mode,
        bot_lines=tuple(loop.bot.status_lines()),
        overlay_transparency=loop.overlay_transparency,
        clear_effect=clear_effect,
        active_piece_overlay=active_overlay,
    )
    draw_tutorial_overlays_2d(screen, fonts, loop)
    pygame.display.flip()
