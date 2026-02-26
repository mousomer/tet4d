from __future__ import annotations

from typing import Callable, Optional, TypeVar

import pygame

from tet4d.engine.api import (
    GameConfigND,
    capture_windowed_display_settings_runtime as capture_windowed_display_settings,
    open_display_runtime as open_display,
)
from tet4d.ui.pygame.runtime_ui.display import DisplaySettings


SettingsT = TypeVar("SettingsT")


def run_nd_mode_launcher(
    *,
    display_settings: DisplaySettings,
    fonts,
    setup_caption: str,
    game_caption: str,
    run_menu: Callable[[pygame.Surface, object], Optional[SettingsT]],
    build_config: Callable[[SettingsT], GameConfigND],
    suggested_window_size: Callable[[GameConfigND], tuple[int, int]],
    run_game: Callable[[pygame.Surface, GameConfigND, object, SettingsT], bool],
) -> None:
    running = True
    while running:
        menu_screen = open_display(
            display_settings,
            caption=setup_caption,
        )
        settings = run_menu(menu_screen, fonts)
        if settings is None:
            break

        cfg = build_config(settings)
        win_w, win_h = suggested_window_size(cfg)
        preferred_size = (
            max(display_settings.windowed_size[0], win_w),
            max(display_settings.windowed_size[1], win_h),
        )
        game_screen = open_display(
            display_settings,
            caption=game_caption,
            preferred_windowed_size=preferred_size,
        )

        back_to_menu = run_game(game_screen, cfg, fonts, settings)
        if not back_to_menu:
            running = False
            continue

        display_settings = capture_windowed_display_settings(display_settings)
