from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module

_ui_key_display = import_module("tet4d.ui.pygame.key_display")


def display_key_name(key: int) -> str:
    return _ui_key_display.display_key_name(key)


def format_key_tuple(keys: Sequence[int]) -> str:
    return _ui_key_display.format_key_tuple(keys)
