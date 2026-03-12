from __future__ import annotations

import pygame

from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import TopologyPlaygroundState


def launch_playground_state_gameplay(
    playground_state: TopologyPlaygroundState,
    screen: pygame.Surface,
    fonts_nd,
    *,
    return_caption: str,
    fonts_2d=None,
    display_settings=None,
) -> tuple[pygame.Surface, object | None]:
    from tet4d.ui.pygame import front2d_game, front3d_game, front4d_game
    from tet4d.ui.pygame.render.font_profiles import init_fonts as init_fonts_for_profile
    from tet4d.ui.pygame.runtime_ui.app_runtime import (
        capture_windowed_display_settings,
        open_display,
    )

    cfg = build_gameplay_config_from_topology_playground_state(playground_state)
    if playground_state.dimension == 2:
        play_fonts_2d = (
            fonts_2d if fonts_2d is not None else init_fonts_for_profile("2d")
        )
        front2d_game.run_game_loop(screen, cfg, play_fonts_2d, display_settings)
    elif playground_state.dimension == 3:
        front3d_game.run_game_loop(screen, cfg, fonts_nd)
    else:
        front4d_game.run_game_loop(screen, cfg, fonts_nd)

    if display_settings is not None:
        display_settings = capture_windowed_display_settings(display_settings)
        screen = open_display(display_settings, caption=return_caption)
    return screen, display_settings


__all__ = ["launch_playground_state_gameplay"]
