from __future__ import annotations

from importlib import import_module

_ui_keybindings_defaults = import_module("tet4d.ui.pygame.keybindings_defaults")


def __getattr__(name: str):
    return getattr(_ui_keybindings_defaults, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_ui_keybindings_defaults)))
