from __future__ import annotations

from importlib import import_module

_ui_menu_control_guides = import_module("tet4d.ui.pygame.menu_control_guides")


def draw_translation_rotation_guides(*args, **kwargs):
    return _ui_menu_control_guides.draw_translation_rotation_guides(*args, **kwargs)
