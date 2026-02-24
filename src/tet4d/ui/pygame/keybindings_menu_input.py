from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

def process_menu_events(
    state: Any,
    binding_rows: list[Any],
    *,
    run_menu_action: Callable[[Any, int, list[Any]], bool],
    handle_text_input: Callable[[Any, str], None],
) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.key.stop_text_input()
            return True
        if event.type == pygame.TEXTINPUT and state.text_mode:
            handle_text_input(state, event.text)
            continue
        if event.type != pygame.KEYDOWN:
            continue
        if run_menu_action(state, event.key, binding_rows):
            return True
    return False
