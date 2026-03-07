from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.launch.leaderboard_menu import maybe_record_leaderboard_session
from tet4d.ui.pygame.runtime_ui.tutorial_overlay import draw_tutorial_overlay

GameLoopDecision = Literal["continue", "quit", "menu", "help"]
GameKeyResult = Literal["continue", "quit", "menu", "restart", "toggle_grid", "help"]


def _mode_key_for_dimension(dimension: int) -> str:
    if dimension == 2:
        return "2d"
    if dimension == 3:
        return "3d"
    if dimension == 4:
        return "4d"
    return "2d"


def _load_speedup_settings_for_dimension(dimension: int) -> tuple[int, int]:
    mode_key = _mode_key_for_dimension(dimension)
    return engine_api.gameplay_mode_speedup_settings_runtime(mode_key)


def process_game_events(
    keydown_handler: Callable[[pygame.event.Event], GameKeyResult],
    on_restart: Callable[[], None],
    on_toggle_grid: Callable[[], None],
    event_handler: Callable[[pygame.event.Event], None] | None = None,
) -> GameLoopDecision:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type != pygame.KEYDOWN:
            if event_handler is not None:
                event_handler(event)
            continue
        result = keydown_handler(event)
        if result == "quit":
            return "quit"
        if result == "menu":
            return "menu"
        if result == "restart":
            on_restart()
            continue
        if result == "toggle_grid":
            on_toggle_grid()
            continue
        if result == "help":
            return "help"
    return "continue"


def _open_help(
    *,
    screen: pygame.Surface,
    fonts: Any,
    loop: Any,
    pause_dimension: int,
    run_help_menu: Callable[..., pygame.Surface],
) -> pygame.Surface:
    return run_help_menu(
        screen,
        fonts,
        pause_dimension,
        f"{pause_dimension}D Gameplay",
        on_escape_back=lambda: loop._tutorial_observe_action("menu_back"),
    )


def _restart_tutorial_if_running_nd(loop: Any) -> bool:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return False
    if not engine_api.tutorial_runtime_is_running_runtime(tutorial_session):
        return False
    if hasattr(loop, "_tutorial_observe_action"):
        loop._tutorial_observe_action("restart")
    restarted = engine_api.tutorial_runtime_restart_runtime(tutorial_session)
    if not restarted:
        return False
    on_restart = getattr(loop, "_apply_pending_tutorial_setup", None)
    if callable(on_restart):
        on_restart()
    if hasattr(loop, "tutorial_action_cooldown_ms"):
        loop.tutorial_action_cooldown_ms = 0
    return True


def _pause_tutorial_restart_nd(loop: Any) -> bool:
    if not _restart_tutorial_if_running_nd(loop):
        return False
    return True


def _pause_tutorial_skip_nd(loop: Any) -> bool:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return False
    return bool(engine_api.tutorial_runtime_skip_runtime(tutorial_session))


def _resolve_menu_decision(
    *,
    decision: str,
    screen: pygame.Surface,
    fonts: Any,
    loop: Any,
    pause_dimension: int,
    run_pause_menu: Callable[..., tuple[str, pygame.Surface]],
) -> tuple[str, pygame.Surface]:
    if decision == "quit":
        return "quit", screen
    if decision != "menu":
        return "continue", screen
    pause_decision, next_screen = run_pause_menu(
        screen,
        fonts,
        dimension=pause_dimension,
        on_tutorial_restart=lambda: _pause_tutorial_restart_nd(loop),
        on_tutorial_skip=lambda: _pause_tutorial_skip_nd(loop),
        on_escape_back=lambda: loop._tutorial_observe_action("menu_back"),
    )
    if pause_decision == "quit":
        return "quit", next_screen
    if pause_decision == "menu":
        return "menu", next_screen
    if pause_decision == "restart":
        if _restart_tutorial_if_running_nd(loop):
            return "continue", next_screen
        loop.on_restart()
        return "restart", next_screen
    return "continue", next_screen


def _advance_simulation_step(
    *,
    loop: Any,
    dt: int,
    gravity_interval_ms: int,
    tutorial_step_pause_active: bool = False,
) -> None:
    if tutorial_step_pause_active:
        loop.gravity_accumulator = 0
        return
    if loop.state.config.exploration_mode:
        loop.gravity_accumulator = 0
        return
    loop.bot.tick_nd(loop.state, dt)
    if loop.bot.controls_descent:
        loop.gravity_accumulator = 0
        return
    loop.gravity_accumulator = engine_api.advance_gravity_runtime(
        loop.state,
        loop.gravity_accumulator,
        gravity_interval_ms,
    )


def _update_loop_effects(
    *,
    loop: Any,
    dt: int,
    spawn_clear_animation: Callable[[Any, int], tuple[Any, int]],
    play_clear_sfx: Callable[[], None],
    play_game_over_sfx: Callable[[], None],
    step_view: Callable[[float], None],
) -> Any:
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
    loop.clear_anim = engine_api.tick_animation_runtime(loop.clear_anim, dt)
    loop.rotation_anim.observe(loop.state.current_piece, dt)
    return loop.rotation_anim.overlay_cells(loop.state.current_piece)


def _maybe_apply_auto_speedup(
    *,
    loop: Any,
    auto_speedup_enabled: int,
    lines_per_level: int,
    gravity_interval_from_config: Callable[[Any], int],
) -> None:
    target_speed_level = engine_api.compute_speed_level_runtime(
        start_level=int(getattr(loop, "base_speed_level", 1)),
        lines_cleared=int(loop.state.lines_cleared),
        enabled=bool(auto_speedup_enabled),
        lines_per_level=int(lines_per_level),
    )
    if int(target_speed_level) == int(loop.state.config.speed_level):
        return
    loop.state.config.speed_level = int(target_speed_level)
    new_interval = int(gravity_interval_from_config(loop.state.config))
    loop.bot.configure_speed(new_interval, int(getattr(loop, "bot_speed_level", 7)))
    loop.gravity_accumulator = 0
    loop.refresh_score_multiplier()


def _handle_runtime_decision(
    *,
    decision: str,
    screen: pygame.Surface,
    fonts: Any,
    loop: Any,
    pause_dimension: int,
    run_pause_menu: Callable[..., tuple[str, pygame.Surface]],
    run_help_menu: Callable[..., pygame.Surface],
) -> tuple[str, pygame.Surface]:
    if decision == "help":
        return (
            "continue",
            _open_help(
                screen=screen,
                fonts=fonts,
                loop=loop,
                pause_dimension=pause_dimension,
                run_help_menu=run_help_menu,
            ),
        )
    return _resolve_menu_decision(
        decision=decision,
        screen=screen,
        fonts=fonts,
        loop=loop,
        pause_dimension=pause_dimension,
        run_pause_menu=run_pause_menu,
    )


def _terminal_from_status(
    status: str,
    *,
    record_session: Callable[[str], None],
) -> bool | None:
    if status == "quit":
        record_session("quit")
        return False
    if status == "menu":
        record_session("menu")
        return True
    if status == "restart":
        record_session("restart")
        return None
    return None


def _draw_runtime_frame(
    *,
    screen: pygame.Surface,
    fonts: Any,
    pause_dimension: int,
    draw_frame: Callable[[pygame.Surface, Any], None],
    active_overlay: Any,
    loop: Any,
) -> None:
    draw_frame(screen, active_overlay)
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is not None:
        draw_tutorial_overlay(
            screen,
            fonts,
            dimension=pause_dimension,
            tutorial_session=tutorial_session,
            panel_offset=tuple(getattr(loop, "tutorial_panel_offset", (0, 0))),
        )
    pygame.display.flip()


def _update_tutorial_action_cooldown(loop: Any, dt: int) -> None:
    if not hasattr(loop, "tutorial_action_cooldown_ms"):
        return
    loop.tutorial_action_cooldown_ms = max(
        0,
        int(getattr(loop, "tutorial_action_cooldown_ms", 0)) - int(dt),
    )


def _tutorial_step_pause_active(loop: Any) -> bool:
    tutorial_session = getattr(loop, "tutorial_session", None)
    if tutorial_session is None:
        return False
    return bool(engine_api.tutorial_runtime_is_running_runtime(tutorial_session))


def _run_optional_tutorial_safety(loop: Any) -> None:
    maintain_tutorial_safety = getattr(loop, "_maintain_tutorial_safety", None)
    if callable(maintain_tutorial_safety):
        maintain_tutorial_safety()


def _maybe_sync_tutorial(tutorial_sync: Callable[[int], bool] | None, loop: Any) -> None:
    if tutorial_sync is not None:
        tutorial_sync(int(loop.state.lines_cleared))


def run_nd_loop(
    *,
    screen: pygame.Surface,
    fonts: Any,
    loop: Any,
    gravity_interval_from_config: Callable[[Any], int],
    pause_dimension: int,
    run_pause_menu: Callable[..., tuple[str, pygame.Surface]],
    run_help_menu: Callable[..., pygame.Surface],
    spawn_clear_animation: Callable[[Any, int], tuple[Any, int]],
    step_view: Callable[[float], None],
    draw_frame: Callable[[pygame.Surface, Any], None],
    play_clear_sfx: Callable[[], None],
    play_game_over_sfx: Callable[[], None],
    event_handler: Callable[[pygame.event.Event], None] | None = None,
    tutorial_sync: Callable[[int], bool] | None = None,
) -> bool:
    """
    Shared game-loop orchestration for 3D and 4D runtime contexts.

    The caller owns loop construction and supplies callbacks for view stepping,
    clear animation creation, and frame rendering.
    """
    clock = pygame.time.Clock()
    session_start_ms = pygame.time.get_ticks()
    auto_speedup_enabled, lines_per_level = _load_speedup_settings_for_dimension(
        pause_dimension
    )

    def _record_session(outcome: str) -> None:
        if getattr(loop, "tutorial_session", None) is not None:
            return
        elapsed_ms = max(0, pygame.time.get_ticks() - session_start_ms)
        try:
            maybe_record_leaderboard_session(
                screen,
                fonts,
                dimension=int(pause_dimension),
                score=int(loop.state.score),
                lines_cleared=int(loop.state.lines_cleared),
                start_speed_level=int(getattr(loop, "base_speed_level", 1)),
                end_speed_level=int(loop.state.config.speed_level),
                duration_seconds=float(elapsed_ms / 1000.0),
                outcome=outcome,
                bot_mode=str(getattr(loop.bot.mode, "value", "off")),
                grid_mode=str(getattr(loop.grid_mode, "value", "full")),
                random_mode=str(loop.state.config.rng_mode),
                topology_mode=str(loop.state.config.topology_mode),
                kick_level=str(loop.state.config.kick_level),
                exploration_mode=bool(loop.state.config.exploration_mode),
            )
        except Exception:
            return

    def _restart_with_record() -> None:
        if _restart_tutorial_if_running_nd(loop):
            return
        _record_session("restart")
        loop.on_restart()

    while True:
        dt = clock.tick(60)
        loop.gravity_accumulator += dt
        _update_tutorial_action_cooldown(loop, dt)
        loop.refresh_score_multiplier()

        decision = process_game_events(
            keydown_handler=loop.keydown_handler,
            on_restart=_restart_with_record,
            on_toggle_grid=loop.on_toggle_grid,
            event_handler=event_handler,
        )
        status, screen = _handle_runtime_decision(
            decision=decision,
            screen=screen,
            fonts=fonts,
            loop=loop,
            pause_dimension=pause_dimension,
            run_pause_menu=run_pause_menu,
            run_help_menu=run_help_menu,
        )
        terminal = _terminal_from_status(status, record_session=_record_session)
        if terminal is not None:
            return terminal
        if status == "restart":
            continue

        gravity_interval_ms = int(gravity_interval_from_config(loop.state.config))
        loop.bot.configure_speed(
            gravity_interval_ms,
            int(getattr(loop, "bot_speed_level", 7)),
        )
        _advance_simulation_step(
            loop=loop,
            dt=dt,
            gravity_interval_ms=gravity_interval_ms,
            tutorial_step_pause_active=_tutorial_step_pause_active(loop),
        )
        _run_optional_tutorial_safety(loop)
        _maybe_apply_auto_speedup(
            loop=loop,
            auto_speedup_enabled=auto_speedup_enabled,
            lines_per_level=lines_per_level,
            gravity_interval_from_config=gravity_interval_from_config,
        )
        _maybe_sync_tutorial(tutorial_sync, loop)
        active_overlay = _update_loop_effects(
            loop=loop,
            dt=dt,
            spawn_clear_animation=spawn_clear_animation,
            play_clear_sfx=play_clear_sfx,
            play_game_over_sfx=play_game_over_sfx,
            step_view=step_view,
        )

        _draw_runtime_frame(
            screen=screen,
            fonts=fonts,
            pause_dimension=pause_dimension,
            draw_frame=draw_frame,
            active_overlay=active_overlay,
            loop=loop,
        )


