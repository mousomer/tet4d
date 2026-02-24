from __future__ import annotations

from importlib import import_module

_ui_menu_model = import_module("tet4d.ui.pygame.menu_model")

CONFIRM_KEYS = _ui_menu_model.CONFIRM_KEYS
MenuLoopState = _ui_menu_model.MenuLoopState
is_confirm_key = _ui_menu_model.is_confirm_key
cycle_index = _ui_menu_model.cycle_index
