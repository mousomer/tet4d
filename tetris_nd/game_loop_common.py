from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import pygame

GameLoopDecision = Literal["continue", "quit", "menu", "help"]
GameKeyResult = Literal["continue", "quit", "menu", "restart", "toggle_grid", "help"]


def process_game_events(
    keydown_handler: Callable[[pygame.event.Event], GameKeyResult],
    on_restart: Callable[[], None],
    on_toggle_grid: Callable[[], None],
    on_help: Callable[[], None],
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
            on_help()

    return "continue"
