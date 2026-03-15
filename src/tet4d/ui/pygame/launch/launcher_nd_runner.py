from __future__ import annotations

from typing import Callable, Optional, TypeVar

import pygame

from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.ui.pygame.launch.topology_lab_menu import run_explorer_playground
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings,
    open_display,
)
from tet4d.ui.pygame.topology_lab.app import build_explorer_playground_launch


SettingsT = TypeVar("SettingsT")


def _run_default_explorer_playground(
    screen: pygame.Surface,
    cfg: GameConfigND,
    fonts,
    _settings: SettingsT,
    display_settings: DisplaySettings,
) -> bool:
    run_explorer_playground(
        screen,
        fonts,
        launch=build_explorer_playground_launch(
            dimension=cfg.ndim,
            explorer_profile=cfg.explorer_topology_profile,
            display_settings=display_settings,
            entry_source="explorer",
            source_settings=_settings,
        ),
    )
    return True


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
    run_explorer: Callable[
        [pygame.Surface, GameConfigND, object, SettingsT, DisplaySettings], bool
    ]
    | None = None,
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
        if bool(getattr(cfg, "exploration_mode", False)):
            explorer_screen = open_display(
                display_settings,
                caption=f"Explorer {cfg.ndim}D Playground",
            )
            explorer_runner = run_explorer or _run_default_explorer_playground
            back_to_menu = explorer_runner(
                explorer_screen,
                cfg,
                fonts,
                settings,
                display_settings,
            )
            display_settings = capture_windowed_display_settings(display_settings)
            if not back_to_menu:
                running = False
                continue
            continue

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
        display_settings = capture_windowed_display_settings(display_settings)
        if not back_to_menu:
            running = False
            continue
