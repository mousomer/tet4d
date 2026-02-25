from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any


@dataclass
class DisplaySettings:
    fullscreen: bool = False
    windowed_size: tuple[int, int] = (1200, 760)


def normalize_display_settings(settings: DisplaySettings) -> DisplaySettings:
    width = max(640, int(settings.windowed_size[0]))
    height = max(480, int(settings.windowed_size[1]))
    return DisplaySettings(
        fullscreen=bool(settings.fullscreen), windowed_size=(width, height)
    )


def apply_display_mode(
    settings: DisplaySettings,
    *,
    preferred_windowed_size: tuple[int, int] | None = None,
) -> Any:
    # Transitional compatibility shim: pygame display implementation now lives in tet4d.ui.pygame.display.
    ui_display = import_module("tet4d.ui.pygame.display")
    return ui_display.apply_display_mode(
        settings,
        preferred_windowed_size=preferred_windowed_size,
    )
