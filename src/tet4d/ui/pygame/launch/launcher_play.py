from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TypeVar

import pygame

from tet4d.engine.runtime.menu_config import branding_copy, default_settings_payload
from tet4d.engine.runtime.menu_settings_state import load_app_settings_payload
from tet4d.ai.playbot.types import bot_mode_from_index
from tet4d.ui.pygame.runtime_ui.app_runtime import (
    DisplaySettings,
    capture_windowed_display_settings,
    open_display,
)


_BRANDING = branding_copy()
_GAME_TITLE = str(_BRANDING["game_title"])
SettingsT = TypeVar("SettingsT")


def setup_caption_for_dimension(dimension: int) -> str:
    return f"{_GAME_TITLE} - {dimension}D setup"


def game_caption_for_dimension(dimension: int) -> str:
    return f"{_GAME_TITLE} - {dimension}D"


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


def _merged_mode_settings(mode_key: str) -> dict[str, object]:
    payload = load_app_settings_payload()
    defaults = default_settings_payload()
    merged_mode_settings: dict[str, object] = {}
    if (
        isinstance(defaults, dict)
        and isinstance(defaults.get("settings"), dict)
        and isinstance(defaults["settings"].get(mode_key), dict)
    ):
        merged_mode_settings.update(defaults["settings"][mode_key])
    if (
        isinstance(payload, dict)
        and isinstance(payload.get("settings"), dict)
        and isinstance(payload["settings"].get(mode_key), dict)
    ):
        merged_mode_settings.update(payload["settings"][mode_key])
    return merged_mode_settings


def _tutorial_settings_from_payload(
    settings_type: type[SettingsT],
    mode_key: str,
) -> SettingsT:
    field_names = {field.name for field in fields(settings_type)}
    settings_kwargs = {
        attr_name: value
        for attr_name, value in _merged_mode_settings(mode_key).items()
        if attr_name in field_names
    }
    return settings_type(**settings_kwargs)


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
    mode_key: str,
    tutorial_settings_type: type[SettingsT] | None = None,
    tutorial_lesson_id: str | None = None,
) -> LaunchResult:
    settings = None
    if tutorial_lesson_id:
        if tutorial_settings_type is None:
            raise RuntimeError(
                f"Tutorial launch requires a settings dataclass for mode {mode_key}"
            )
        settings = _tutorial_settings_from_payload(tutorial_settings_type, mode_key)
    else:
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
        tutorial_lesson_id=tutorial_lesson_id,
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
    *,
    tutorial_lesson_id: str | None = None,
) -> LaunchResult:
    from tet4d.ui.pygame import front2d_game

    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_2d,
        display_settings=display_settings,
        setup_caption=setup_caption_for_dimension(2),
        game_caption=game_caption_for_dimension(2),
        run_menu_fn=front2d_game.run_menu,
        build_cfg_fn=front2d_game._config_from_settings,
        suggested_size_fn=_suggested_window_size_2d,
        run_game_loop_fn=lambda game_screen, cfg, active_fonts, **kwargs: (
            front2d_game.run_game_loop(
                game_screen,
                cfg,
                active_fonts,
                display_settings,
                **kwargs,
            )
        ),
        default_budget_ms=12,
        mode_key="2d",
        tutorial_settings_type=front2d_game.GameSettings,
        tutorial_lesson_id=tutorial_lesson_id,
    )


def launch_3d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
    *,
    tutorial_lesson_id: str | None = None,
) -> LaunchResult:
    from tet4d.ui.pygame import front3d_game, frontend_nd_setup

    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_nd,
        display_settings=display_settings,
        setup_caption=setup_caption_for_dimension(3),
        game_caption=game_caption_for_dimension(3),
        run_menu_fn=lambda menu_screen, active_fonts: frontend_nd_setup.run_menu(
            menu_screen,
            active_fonts,
            3,
        ),
        build_cfg_fn=lambda settings: frontend_nd_setup.build_play_menu_config(
            settings,
            3,
        ),
        suggested_size_fn=front3d_game.suggested_window_size,
        run_game_loop_fn=front3d_game.run_game_loop,
        default_budget_ms=24,
        mode_key="3d",
        tutorial_settings_type=frontend_nd_setup.GameSettingsND,
        tutorial_lesson_id=tutorial_lesson_id,
    )


def launch_4d(
    screen: pygame.Surface,
    fonts_nd,
    display_settings: DisplaySettings,
    *,
    tutorial_lesson_id: str | None = None,
) -> LaunchResult:
    from tet4d.ui.pygame import front4d_game, frontend_nd_setup

    return _launch_mode_flow(
        screen=screen,
        fonts=fonts_nd,
        display_settings=display_settings,
        setup_caption=setup_caption_for_dimension(4),
        game_caption=game_caption_for_dimension(4),
        run_menu_fn=lambda menu_screen, active_fonts: frontend_nd_setup.run_menu(
            menu_screen,
            active_fonts,
            4,
        ),
        build_cfg_fn=lambda settings: frontend_nd_setup.build_play_menu_config(
            settings,
            4,
        ),
        suggested_size_fn=front4d_game.suggested_window_size,
        run_game_loop_fn=front4d_game.run_game_loop,
        default_budget_ms=36,
        mode_key="4d",
        tutorial_settings_type=frontend_nd_setup.GameSettingsND,
        tutorial_lesson_id=tutorial_lesson_id,
    )
