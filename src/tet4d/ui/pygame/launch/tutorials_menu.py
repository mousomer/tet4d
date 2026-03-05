from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.menu.menu_navigation_keys import normalize_menu_navigation_key
from tet4d.ui.pygame.ui_utils import draw_vertical_gradient, fit_text

_BG_TOP = (16, 22, 54)
_BG_BOTTOM = (4, 8, 22)
_TEXT_PRIMARY = (236, 238, 246)
_TEXT_MUTED = (188, 196, 224)
_TEXT_HIGHLIGHT = (255, 224, 128)

_LESSON_BY_MODE_ID = {
    "2d": "tutorial_2d_core",
    "3d": "tutorial_3d_core",
    "4d": "tutorial_4d_core",
}


@dataclass(frozen=True)
class TutorialSelection:
    mode: str
    lesson_id: str


@dataclass(frozen=True)
class _MenuRow:
    label: str
    mode: str | None


def _rows() -> tuple[_MenuRow, ...]:
    return (
        _MenuRow("2D Tutorial", "2d"),
        _MenuRow("3D Tutorial", "3d"),
        _MenuRow("4D Tutorial", "4d"),
        _MenuRow("Back", None),
    )


def _available_lesson_ids() -> set[str]:
    return set(engine_api.tutorial_lesson_ids_runtime())


def _draw_menu(
    screen: pygame.Surface,
    fonts: Any,
    *,
    selected_index: int,
    status: str,
) -> None:
    draw_vertical_gradient(screen, _BG_TOP, _BG_BOTTOM)
    width, height = screen.get_size()
    title = fonts.title_font.render("Tutorials", True, _TEXT_PRIMARY)
    subtitle = fonts.hint_font.render(
        "Select a guided tutorial pack (2D/3D/4D).",
        True,
        _TEXT_MUTED,
    )
    screen.blit(title, ((width - title.get_width()) // 2, 42))
    screen.blit(subtitle, ((width - subtitle.get_width()) // 2, 88))

    rows = _rows()
    panel_w = min(620, max(320, width - 44))
    row_h = max(fonts.menu_font.get_height() + 10, 36)
    panel_h = 44 + len(rows) * row_h
    panel_x = (width - panel_w) // 2
    panel_y = max(140, (height - panel_h) // 2)
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 156), panel.get_rect(), border_radius=12)
    screen.blit(panel, (panel_x, panel_y))

    y = panel_y + 20
    for idx, row in enumerate(rows):
        selected = idx == selected_index
        color = _TEXT_HIGHLIGHT if selected else _TEXT_PRIMARY
        text = fit_text(fonts.menu_font, row.label, panel_w - 52)
        surf = fonts.menu_font.render(text, True, color)
        if selected:
            hi = pygame.Surface((panel_w - 26, surf.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(hi, (255, 255, 255, 36), hi.get_rect(), border_radius=8)
            screen.blit(hi, (panel_x + 13, y - 4))
        screen.blit(surf, (panel_x + 24, y))
        y += row_h

    hints = [
        "Enter: Start tutorial",
        "Esc/Q: Back to launcher",
    ]
    hint_y = panel_y + panel_h + 10
    for hint in hints:
        hint_text = fit_text(fonts.hint_font, hint, width - 24)
        hint_surf = fonts.hint_font.render(hint_text, True, _TEXT_MUTED)
        screen.blit(hint_surf, ((width - hint_surf.get_width()) // 2, hint_y))
        hint_y += hint_surf.get_height() + 3

    if status:
        status_text = fit_text(fonts.hint_font, status, width - 24)
        status_surf = fonts.hint_font.render(status_text, True, _TEXT_HIGHLIGHT)
        screen.blit(status_surf, ((width - status_surf.get_width()) // 2, hint_y + 4))


def run_tutorials_menu(
    screen: pygame.Surface,
    fonts: Any,
) -> tuple[TutorialSelection | None, pygame.Surface]:
    clock = pygame.time.Clock()
    rows = _rows()
    selected = 0
    status = ""
    available_lessons = _available_lesson_ids()
    while True:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            selected, status, should_exit, selection = _handle_menu_event(
                event,
                rows=rows,
                selected=selected,
                status=status,
                available_lessons=available_lessons,
            )
            if should_exit:
                return selection, screen
        _draw_menu(screen, fonts, selected_index=selected, status=status)
        pygame.display.flip()


def _handle_menu_event(
    event: pygame.event.Event,
    *,
    rows: tuple[_MenuRow, ...],
    selected: int,
    status: str,
    available_lessons: set[str],
) -> tuple[int, str, bool, TutorialSelection | None]:
    if event.type == pygame.QUIT:
        return selected, status, True, None
    if event.type != pygame.KEYDOWN:
        return selected, status, False, None
    nav_key = normalize_menu_navigation_key(int(event.key))
    if nav_key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
        return selected, status, True, None
    if nav_key == pygame.K_UP or event.key == pygame.K_w:
        return (selected - 1) % len(rows), status, False, None
    if nav_key == pygame.K_DOWN or event.key == pygame.K_s:
        return (selected + 1) % len(rows), status, False, None
    if event.key not in (pygame.K_RETURN, pygame.K_KP_ENTER):
        return selected, status, False, None
    row = rows[selected]
    if row.mode is None:
        return selected, status, True, None
    lesson_id = _LESSON_BY_MODE_ID[row.mode]
    if lesson_id not in available_lessons:
        return selected, f"Lesson unavailable: {lesson_id}", False, None
    return (
        selected,
        status,
        True,
        TutorialSelection(mode=row.mode, lesson_id=lesson_id),
    )
