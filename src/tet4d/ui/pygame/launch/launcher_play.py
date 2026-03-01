from __future__ import annotations

from dataclasses import dataclass

import pygame

import tet4d.engine.api as engine_api
from cli import front2d
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    capture_windowed_display_settings,
    open_display,
)
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ai.playbot.types import bot_mode_from_index


@dataclass
class LaunchResult:
    screen: pygame.Surface
    display_settings: DisplaySettings
    keep_running: bool


def _preferred_windowed_size(
    display_settings: DisplaySettings,
    suggested: tuple[int, int],
) -> tuple[int, int]:
    return (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )


def _bot_kwargs(settings: object, default_budget_ms: int) -> dict[str, object]:
    return {
        "bot_mode": bot_mode_from_index(getattr(settings, "bot_mode_index", 0)),
        "bot_speed_level": getattr(settings, "bot_speed_level", 7),
        "bot_algorithm_index": getattr(settings, "bot_algorithm_index", 0),
        "bot_profile_index": getattr(settings, "bot_profile_index", 1),
        "bot_budget_ms": getattr(settings, "bot_budget_ms", default_budget_ms),
    }


def _suggested_window_size_2d(cfg) -> tuple[int, int]:
    board_px_w = cfg.width * 30
    board_px_h = cfg.height * 30
    return board_px_w + 260, board_px_h + 40


def _launch_mode_flow(
    *,
    screen: pygame.Surface,
    fonts,
    display_settings: DisplaySettings,
    setup_caption: str,
    game_caption: str,
    run_menu_fn,
    build_cfg_fn,
    suggested_size_fn,
    run_game_loop_fn,
    default_budget_ms: int,
) -> LaunchResult:
    screen = open_display(display_settings, caption=setup_caption)
    settings = run_menu_fn(screen, fonts)
    if settings is None:
        return LaunchResult(
            screen=screen, display_settings=display_settings, keep_running=True
        )

    cfg = build_cfg_fn(settings)
    preferred_size = _preferred_windowed_size(display_settings, suggested_size_fn(cfg))
    screen = open_display(
        display_settings,
        caption=game_caption,
        preferred_windowed_size=preferred_size,
    )
    back_to_menu = run_game_loop_fn(
        screen,
        cfg,
        fonts,
        **_bot_kwargs(settings, default_budget_ms),
    )
    if not back_to_menu:
        return LaunchResult(
            screen=screen, display_settings=display_settings, keep_running=False
        )
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return LaunchResult(
        screen=screen, display_settings=display_settings, keep_running=True
    )


def launch_2d(
    screen: pygame.Surface,
    fonts_2d,
    display_settings: DisplaySettings,
) -> LaunchResult:
    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_2d,
        display_settings=display_settings,
        setup_caption="2D Tetris – Setup",
        game_caption="2D Tetris",
        run_menu_fn=front2d.run_menu,
        build_cfg_fn=front2d._config_from_settings,
        suggested_size_fn=_suggested_window_size_2d,
        run_game_loop_fn=lambda game_screen, cfg, active_fonts, **kwargs: (
            front2d.run_game_loop(
                game_screen,
                cfg,
                active_fonts,
                display_settings,
                **kwargs,
            )
        ),
        default_budget_ms=12,
    )


def launch_3d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> LaunchResult:
    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_nd,
        display_settings=display_settings,
        setup_caption="3D Tetris – Setup",
        game_caption="3D Tetris",
        run_menu_fn=engine_api.launcher_play_run_menu_3d,
        build_cfg_fn=engine_api.launcher_play_build_config_3d,
        suggested_size_fn=engine_api.launcher_play_suggested_window_size_3d,
        run_game_loop_fn=engine_api.launcher_play_run_game_loop_3d,
        default_budget_ms=24,
    )


def launch_4d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> LaunchResult:
    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_nd,
        display_settings=display_settings,
        setup_caption="4D Tetris – Setup",
        game_caption="4D Tetris",
        run_menu_fn=lambda menu_screen,
        menu_fonts: engine_api.launcher_play_run_menu_nd(menu_screen, menu_fonts, 4),
        build_cfg_fn=lambda settings: engine_api.launcher_play_build_config_nd(
            settings, 4
        ),
        suggested_size_fn=engine_api.launcher_play_suggested_window_size_4d,
        run_game_loop_fn=engine_api.launcher_play_run_game_loop_4d,
        default_budget_ms=36,
    )
