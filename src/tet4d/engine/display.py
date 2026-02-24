from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass
class DisplaySettings:
    fullscreen: bool = False
    windowed_size: tuple[int, int] = (1200, 760)


def normalize_display_settings(settings: DisplaySettings) -> DisplaySettings:
    width = max(640, int(settings.windowed_size[0]))
    height = max(480, int(settings.windowed_size[1]))
    return DisplaySettings(fullscreen=bool(settings.fullscreen), windowed_size=(width, height))


def apply_display_mode(
    settings: DisplaySettings,
    *,
    preferred_windowed_size: tuple[int, int] | None = None,
) -> pygame.Surface:
    normalized = normalize_display_settings(settings)
    if normalized.fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    size = preferred_windowed_size if preferred_windowed_size is not None else normalized.windowed_size
    width = max(640, int(size[0]))
    height = max(480, int(size[1]))
    return pygame.display.set_mode((width, height), pygame.RESIZABLE)
