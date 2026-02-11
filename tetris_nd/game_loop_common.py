from __future__ import annotations

from collections.abc import Callable
from typing import Literal

import pygame

GameLoopDecision = Literal["continue", "quit", "menu"]
GameKeyResult = Literal["continue", "quit", "menu", "restart", "toggle_grid"]


def process_game_events(
    keydown_handler: Callable[[pygame.event.Event], GameKeyResult],
    on_restart: Callable[[], None],
    on_toggle_grid: Callable[[], None],
) -> GameLoopDecision:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return "quit"
        if event.type != pygame.KEYDOWN:
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

    return "continue"
