from __future__ import annotations

from typing import Callable

import pygame

from tet4d.ui.pygame.launch.leaderboard_menu import maybe_record_leaderboard_session
from tet4d.ui.pygame.render.gfx_game import GfxFonts
from tet4d.ui.pygame.runtime_ui.pause_menu import run_pause_menu

from .front2d_session import LoopContext2D
from .front2d_tutorial import (
    pause_tutorial_restart_2d,
    pause_tutorial_skip_2d,
    restart_tutorial_if_running_2d,
    tutorial_observe_action,
)


def _resolve_loop_decision(
    *,
    decision: str,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    pause_menu_runner: Callable[..., tuple[str, pygame.Surface]] | None = None,
) -> tuple[str, pygame.Surface]:
    if decision == "quit":
        return "quit", screen
    if decision != "menu":
        return "continue", screen
    pause_decision, next_screen = (
        run_pause_menu if pause_menu_runner is None else pause_menu_runner
    )(
        screen,
        fonts,
        dimension=2,
        on_tutorial_restart=lambda: pause_tutorial_restart_2d(loop),
        on_tutorial_skip=lambda: pause_tutorial_skip_2d(loop),
        on_escape_back=lambda: tutorial_observe_action(loop, "menu_back"),
    )
    if pause_decision == "quit":
        return "quit", next_screen
    if pause_decision == "menu":
        return "menu", next_screen
    if pause_decision == "restart":
        if restart_tutorial_if_running_2d(loop):
            return "continue", next_screen
        loop.on_restart()
        return "restart", next_screen
    return "continue", next_screen


def _resolve_terminal_status(
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
    return None


def _record_leaderboard_session_2d(
    *,
    tutorial_lesson_id: str | None,
    screen: pygame.Surface,
    fonts: GfxFonts,
    loop: LoopContext2D,
    session_start_ms: int,
    outcome: str,
) -> None:
    if tutorial_lesson_id:
        return
    elapsed_ms = max(0, pygame.time.get_ticks() - session_start_ms)
    try:
        maybe_record_leaderboard_session(
            screen,
            fonts,
            dimension=2,
            score=int(loop.state.score),
            lines_cleared=int(loop.state.lines_cleared),
            start_speed_level=int(loop.base_speed_level),
            end_speed_level=int(loop.cfg.speed_level),
            duration_seconds=float(elapsed_ms / 1000.0),
            outcome=outcome,
            bot_mode=str(loop.bot.mode.value),
            grid_mode=str(loop.grid_mode.value),
            random_mode=str(loop.cfg.rng_mode),
            topology_mode=str(loop.cfg.topology_mode),
            kick_level=str(loop.cfg.kick_level),
            exploration_mode=bool(loop.cfg.exploration_mode),
        )
    except Exception:
        return
