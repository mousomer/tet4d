from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from .game_loop_common import process_game_events
from .runtime_helpers import advance_gravity, tick_animation


def run_nd_loop(
    *,
    screen: pygame.Surface,
    fonts: Any,
    loop: Any,
    gravity_interval_ms: int,
    pause_dimension: int,
    run_pause_menu: Callable[[pygame.Surface, Any, int], tuple[str, pygame.Surface]],
    run_help_menu: Callable[[pygame.Surface, Any, int, str], pygame.Surface],
    spawn_clear_animation: Callable[[Any, int], tuple[Any, int]],
    step_view: Callable[[float], None],
    draw_frame: Callable[[pygame.Surface, Any], None],
    play_clear_sfx: Callable[[], None],
    play_game_over_sfx: Callable[[], None],
) -> bool:
    """
    Shared game-loop orchestration for 3D and 4D runtime contexts.

    The caller owns loop construction and supplies callbacks for view stepping,
    clear animation creation, and frame rendering.
    """
    clock = pygame.time.Clock()

    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt
        loop.refresh_score_multiplier()

        def _open_help() -> None:
            nonlocal screen
            screen = run_help_menu(
                screen,
                fonts,
                pause_dimension,
                f"{pause_dimension}D Gameplay",
            )

        decision = process_game_events(
            keydown_handler=loop.keydown_handler,
            on_restart=loop.on_restart,
            on_toggle_grid=loop.on_toggle_grid,
            on_help=_open_help,
            event_handler=loop.pointer_event_handler,
        )
        if decision == "quit":
            return False
        if decision == "menu":
            pause_decision, screen = run_pause_menu(screen, fonts, dimension=pause_dimension)
            if pause_decision == "quit":
                return False
            if pause_decision == "menu":
                return True
            if pause_decision == "restart":
                loop.on_restart()
                continue

        if loop.state.config.exploration_mode:
            loop.gravity_accumulator = 0
        else:
            loop.bot.tick_nd(loop.state, dt)
            if loop.bot.controls_descent:
                loop.gravity_accumulator = 0
            else:
                loop.gravity_accumulator = advance_gravity(
                    loop.state,
                    loop.gravity_accumulator,
                    gravity_interval_ms,
                )

        new_clear_anim, loop.last_lines_cleared = spawn_clear_animation(
            loop.state,
            loop.last_lines_cleared,
        )
        if new_clear_anim is not None:
            loop.clear_anim = new_clear_anim
            play_clear_sfx()

        if loop.state.game_over and not loop.was_game_over:
            play_game_over_sfx()
        loop.was_game_over = loop.state.game_over

        step_view(dt)
        loop.clear_anim = tick_animation(loop.clear_anim, dt)
        loop.rotation_anim.observe(loop.state.current_piece, dt)
        active_overlay = loop.rotation_anim.overlay_cells(loop.state.current_piece)

        draw_frame(screen, active_overlay)
        pygame.display.flip()
