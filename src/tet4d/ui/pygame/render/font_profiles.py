from __future__ import annotations

from dataclasses import dataclass

import pygame


@dataclass(frozen=True)
class _FontProfile:
    title_size: int
    menu_size: int
    hint_size: int
    panel_size: int


@dataclass
class GfxFonts:
    title_font: pygame.font.Font
    menu_font: pygame.font.Font
    hint_font: pygame.font.Font
    # Dense helper/reference panels still use this smaller face; primary menu
    # family rows should render with menu_font.
    panel_font: pygame.font.Font


_TITLE_FONT_CANDIDATES = (
    "orbitron",
    "eurostile",
    "bankgothic md bt",
    "microgramma",
    "square721 bt",
    "arial",
)


_FONT_PROFILES: dict[str, _FontProfile] = {
    "2d": _FontProfile(
        title_size=36,
        menu_size=24,
        hint_size=18,
        panel_size=18,
    ),
    "nd": _FontProfile(
        title_size=36,
        menu_size=24,
        hint_size=18,
        panel_size=17,
    ),
}


def init_fonts(profile: str = "nd") -> GfxFonts:
    spec = _FONT_PROFILES.get(profile.strip().lower(), _FONT_PROFILES["nd"])
    try:
        title_font = None
        for candidate in _TITLE_FONT_CANDIDATES:
            matched = pygame.font.match_font(candidate, bold=True)
            if matched:
                title_font = pygame.font.Font(matched, spec.title_size)
                break
        if title_font is None:
            title_font = pygame.font.SysFont("arial", spec.title_size, bold=True)
        return GfxFonts(
            title_font=title_font,
            menu_font=pygame.font.SysFont("consolas", spec.menu_size),
            hint_font=pygame.font.SysFont("consolas", spec.hint_size),
            panel_font=pygame.font.SysFont("consolas", spec.panel_size),
        )
    except (pygame.error, OSError):
        return GfxFonts(
            title_font=pygame.font.Font(None, spec.title_size),
            menu_font=pygame.font.Font(None, spec.menu_size),
            hint_font=pygame.font.Font(None, spec.hint_size),
            panel_font=pygame.font.Font(None, spec.panel_size),
        )
