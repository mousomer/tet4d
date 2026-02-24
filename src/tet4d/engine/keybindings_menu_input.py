from __future__ import annotations

from importlib import import_module

_ui_keybindings_menu_input = import_module("tet4d.ui.pygame.keybindings_menu_input")

process_menu_events = _ui_keybindings_menu_input.process_menu_events
