from __future__ import annotations

from dataclasses import dataclass

import pygame

import front2d
from .app_runtime import capture_windowed_display_settings, open_display
from .display import DisplaySettings
from .front3d_game import (
    build_config as build_config_3d,
    run_game_loop as run_game_loop_3d,
    run_menu as run_menu_3d,
    suggested_window_size as suggested_window_size_3d,
)
from .front4d_game import run_game_loop as run_game_loop_4d, suggested_window_size as suggested_window_size_4d
from .frontend_nd import build_config as build_config_nd, run_menu as run_menu_nd
from .playbot.types import bot_mode_from_index


@dataclass
class LaunchResult:
    screen: pygame.Surface
    display_settings: DisplaySettings
    keep_running: bool


def launch_2d(
    screen: pygame.Surface,
    fonts_2d,
    display_settings: DisplaySettings,
) -> LaunchResult:
    screen = open_display(display_settings, caption="2D Tetris – Setup")
    settings = front2d.run_menu(screen, fonts_2d)
    if settings is None:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)

    cfg = front2d._config_from_settings(settings)
    board_px_w = cfg.width * 30
    board_px_h = cfg.height * 30
    suggested = (board_px_w + 200 + 60, board_px_h + 40)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="2D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = front2d.run_game_loop(
        screen,
        cfg,
        fonts_2d,
        bot_mode=bot_mode_from_index(getattr(settings, "bot_mode_index", 0)),
        bot_speed_level=getattr(settings, "bot_speed_level", 7),
        bot_algorithm_index=getattr(settings, "bot_algorithm_index", 0),
        bot_profile_index=getattr(settings, "bot_profile_index", 1),
        bot_budget_ms=getattr(settings, "bot_budget_ms", 12),
    )
    if not back_to_menu:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=False)
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)


def launch_3d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> LaunchResult:
    screen = open_display(display_settings, caption="3D Tetris – Setup")
    settings = run_menu_3d(screen, fonts_nd)
    if settings is None:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)

    cfg = build_config_3d(settings)
    suggested = suggested_window_size_3d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="3D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = run_game_loop_3d(
        screen,
        cfg,
        fonts_nd,
        bot_mode=bot_mode_from_index(getattr(settings, "bot_mode_index", 0)),
        bot_speed_level=getattr(settings, "bot_speed_level", 7),
        bot_algorithm_index=getattr(settings, "bot_algorithm_index", 0),
        bot_profile_index=getattr(settings, "bot_profile_index", 1),
        bot_budget_ms=getattr(settings, "bot_budget_ms", 24),
    )
    if not back_to_menu:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=False)
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)


def launch_4d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
) -> LaunchResult:
    screen = open_display(display_settings, caption="4D Tetris – Setup")
    settings = run_menu_nd(screen, fonts_nd, 4)
    if settings is None:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)

    cfg = build_config_nd(settings, 4)
    suggested = suggested_window_size_4d(cfg)
    preferred_size = (
        max(display_settings.windowed_size[0], suggested[0]),
        max(display_settings.windowed_size[1], suggested[1]),
    )
    screen = open_display(
        display_settings,
        caption="4D Tetris",
        preferred_windowed_size=preferred_size,
    )

    back_to_menu = run_game_loop_4d(
        screen,
        cfg,
        fonts_nd,
        bot_mode=bot_mode_from_index(getattr(settings, "bot_mode_index", 0)),
        bot_speed_level=getattr(settings, "bot_speed_level", 7),
        bot_algorithm_index=getattr(settings, "bot_algorithm_index", 0),
        bot_profile_index=getattr(settings, "bot_profile_index", 1),
        bot_budget_ms=getattr(settings, "bot_budget_ms", 36),
    )
    if not back_to_menu:
        return LaunchResult(screen=screen, display_settings=display_settings, keep_running=False)
    display_settings = capture_windowed_display_settings(display_settings)
    screen = open_display(display_settings)
    return LaunchResult(screen=screen, display_settings=display_settings, keep_running=True)
