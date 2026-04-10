from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pygame

from tet4d.ui.pygame.ui_utils import default_menu_back_chip_rect


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
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and int(getattr(event, "button", 0)) == 1
            and default_menu_back_chip_rect().collidepoint(getattr(event, "pos", (-1, -1)))
        ):
            if state.section_mode or not state.allow_scope_sections:
                pygame.key.stop_text_input()
                return True
            state.section_mode = True
            state.capture_mode = False
            state.flash_selected_frames = 0
            state.status = "Returned to keybinding sections"
            state.status_error = False
            continue
        if event.type == pygame.TEXTINPUT and state.text_mode:
            handle_text_input(state, event.text)
            continue
        if event.type != pygame.KEYDOWN:
            continue
        if run_menu_action(state, event.key, binding_rows):
            return True
    return False
