from __future__ import annotations

import pygame

from tet4d.ai.playbot.types import BotMode
from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.runtime.project_config import project_constant_float
from tet4d.ui.pygame.render.gfx_game import GfxFonts
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings

from . import front2d_frame, front2d_results
from .front2d_session import LoopContext2D
from .front2d_setup import (
    load_animation_settings_for_mode as _load_animation_settings_for_mode,
    load_overlay_transparency_for_runtime_2d as _load_overlay_transparency_for_runtime_2d,
    load_speedup_settings_for_mode as _load_speedup_settings_for_mode,
)
from .front2d_tutorial import apply_pending_tutorial_setup, restart_tutorial_if_running_2d


def run_game_loop(
    screen: pygame.Surface,
    cfg: GameConfig,
    fonts: GfxFonts,
    display_settings: DisplaySettings,
    *,
    bot_mode: BotMode = BotMode.OFF,
    bot_speed_level: int = 7,
    bot_algorithm_index: int = 0,
    bot_profile_index: int = 1,
    bot_budget_ms: int = 12,
    tutorial_lesson_id: str | None = None,
) -> bool:
    if cfg.exploration_mode:
        bot_mode = BotMode.OFF
    session_start_ms = pygame.time.get_ticks()

    def _record_session(outcome: str) -> None:
        front2d_results._record_leaderboard_session_2d(
            tutorial_lesson_id=tutorial_lesson_id,
            screen=screen,
            fonts=fonts,
            loop=loop,
            session_start_ms=session_start_ms,
            outcome=outcome,
        )

    def _restart_with_record() -> None:
        if restart_tutorial_if_running_2d(loop):
            return
        _record_session("restart")
        loop.on_restart()

    overlay_transparency = _load_overlay_transparency_for_runtime_2d()
    auto_speedup_enabled, lines_per_level = _load_speedup_settings_for_mode("2d")
    rotation_animation_duration_ms, translation_animation_duration_ms = (
        _load_animation_settings_for_mode("2d")
    )
    loop = LoopContext2D.create(
        cfg,
        bot_mode=bot_mode,
        bot_speed_level=bot_speed_level,
        auto_speedup_enabled=auto_speedup_enabled,
        lines_per_level=lines_per_level,
        rotation_animation_duration_ms=rotation_animation_duration_ms,
        translation_animation_duration_ms=translation_animation_duration_ms,
        overlay_transparency=overlay_transparency,
        tutorial_lesson_id=tutorial_lesson_id,
    )
    apply_pending_tutorial_setup(loop)
    front2d_frame._configure_game_loop(
        loop=loop,
        bot_speed_level=bot_speed_level,
        bot_algorithm_index=bot_algorithm_index,
        bot_profile_index=bot_profile_index,
        bot_budget_ms=bot_budget_ms,
    )
    clear_anim_duration_ms = project_constant_float(
        ("animation", "clear_effect_duration_ms_2d"),
        320.0,
        min_value=120.0,
        max_value=1200.0,
    )

    clock = pygame.time.Clock()
    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt
        cooldown = int(getattr(loop, "tutorial_action_cooldown_ms", 0))
        if cooldown > 0:
            loop.tutorial_action_cooldown_ms = max(0, cooldown - int(dt))
        loop.refresh_score_multiplier()

        screen, display_settings, terminal, continue_loop = (
            front2d_frame._handle_loop_event_cycle(
                screen=screen,
                fonts=fonts,
                loop=loop,
                display_settings=display_settings,
                restart_with_record=_restart_with_record,
                record_session=_record_session,
            )
        )
        if terminal is not None:
            return terminal
        if continue_loop:
            continue
        front2d_frame._run_game_frame_2d(
            screen=screen,
            fonts=fonts,
            loop=loop,
            dt=dt,
            clear_anim_duration_ms=clear_anim_duration_ms,
        )
