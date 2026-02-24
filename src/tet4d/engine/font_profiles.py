from __future__ import annotations

from importlib import import_module
from typing import Any


_ui_font_profiles = import_module("tet4d.ui.pygame.font_profiles")
GfxFonts = _ui_font_profiles.GfxFonts


def init_fonts(profile: str = "nd") -> Any:
    # Transitional compatibility shim: pygame font profile implementation now lives in tet4d.ui.pygame.font_profiles.
    return _ui_font_profiles.init_fonts(profile)
