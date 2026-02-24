from __future__ import annotations

from importlib import import_module

_ui_menu_runner = import_module("tet4d.ui.pygame.menu_runner")


def __getattr__(name: str):
    return getattr(_ui_menu_runner, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_ui_menu_runner)))
