from __future__ import annotations

import sys

import pygame

from tet4d.ai.playbot.types import bot_mode_from_index
from tet4d.ui.pygame.render.gfx_game import CELL_SIZE, init_fonts
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings,
    capture_windowed_display_settings_from_event,
    initialize_runtime,
    open_display,
)
from tet4d.ui.pygame.runtime_ui.loop_runner_nd import process_game_events

from .front2d_input import handle_game_keydown
from .front2d_loop import (
    LoopContext2D,
    _configure_game_loop,
    _resolve_loop_decision,
    create_initial_state,
    run_game_loop,
)
from .front2d_setup import (
    GameSettings,
    MenuState,
    config_from_settings,
    run_menu,
)


def run() -> None:
    runtime = initialize_runtime(sync_audio_state=False)
    fonts = init_fonts()

    display_settings = DisplaySettings(
        fullscreen=runtime.display_settings.fullscreen,
        windowed_size=runtime.display_settings.windowed_size,
    )

    running = True
    while running:
        menu_screen = open_display(
            display_settings,
            caption="2D Tetris - Setup",
        )
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break

        cfg = _config_from_settings(settings)

        board_px_w = cfg.width * CELL_SIZE
        board_px_h = cfg.height * CELL_SIZE
        window_w = board_px_w + 200 + 3 * 20
        window_h = board_px_h + 2 * 20
        preferred_size = (
            max(window_w, display_settings.windowed_size[0]),
            max(window_h, display_settings.windowed_size[1]),
        )
        game_screen = open_display(
            display_settings,
            caption="2D Tetris",
            preferred_windowed_size=preferred_size,
        )

        back_to_menu = run_game_loop(
            game_screen,
            cfg,
            fonts,
            display_settings,
            bot_mode=bot_mode_from_index(settings.bot_mode_index),
            bot_speed_level=settings.bot_speed_level,
            bot_algorithm_index=settings.bot_algorithm_index,
            bot_profile_index=settings.bot_profile_index,
            bot_budget_ms=settings.bot_budget_ms,
        )
        display_settings = capture_windowed_display_settings(display_settings)
        if not back_to_menu:
            running = False
            continue

    pygame.quit()
    sys.exit()


_config_from_settings = config_from_settings


def main(argv=None) -> None:
    del argv
    run()


__all__ = [
    "DisplaySettings",
    "GameSettings",
    "LoopContext2D",
    "MenuState",
    "_config_from_settings",
    "_configure_game_loop",
    "_resolve_loop_decision",
    "capture_windowed_display_settings_from_event",
    "create_initial_state",
    "handle_game_keydown",
    "main",
    "process_game_events",
    "run",
    "run_game_loop",
    "run_menu",
]


if __name__ == "__main__":
    main()
