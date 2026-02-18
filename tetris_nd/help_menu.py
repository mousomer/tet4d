from __future__ import annotations

from dataclasses import dataclass

import pygame

from .control_helper import control_groups_for_dimension, draw_grouped_control_helper
from .key_display import format_key_tuple
from .keybindings import (
    binding_action_description,
    binding_group_label,
    runtime_binding_groups_for_dimension,
)
from .menu_config import settings_category_docs
from .pieces2d import PIECE_SET_2D_OPTIONS, piece_set_2d_label
from .pieces_nd import piece_set_label, piece_set_options_for_dimension


_BG_TOP = (14, 18, 44)
_BG_BOTTOM = (4, 7, 20)
_TEXT_COLOR = (232, 232, 240)
_MUTED_COLOR = (192, 200, 228)
_HIGHLIGHT = (255, 224, 128)
_PAGE_COUNT = 9
_SETTINGS_DOCS = settings_category_docs()


@dataclass
class _HelpState:
    page: int = 0
    dimension: int = 2
    running: bool = True


def _current_binding_text(dimension: int, action: str, *, group: str = "system") -> str:
    groups = runtime_binding_groups_for_dimension(max(2, min(4, int(dimension))))
    keys = tuple(groups.get(group, {}).get(action, ()))
    return format_key_tuple(keys)


def _draw_gradient(surface: pygame.Surface) -> None:
    width, height = surface.get_size()
    for y in range(height):
        t = y / max(1, height - 1)
        color = (
            int(_BG_TOP[0] * (1 - t) + _BG_BOTTOM[0] * t),
            int(_BG_TOP[1] * (1 - t) + _BG_BOTTOM[1] * t),
            int(_BG_TOP[2] * (1 - t) + _BG_BOTTOM[2] * t),
        )
        pygame.draw.line(surface, color, (0, y), (width, y))


def _draw_lines(
    surface: pygame.Surface,
    font: pygame.font.Font,
    lines: list[str],
    *,
    x: int,
    y: int,
    line_gap: int = 4,
) -> None:
    height = surface.get_height()
    for line in lines:
        if y > height - 32:
            overflow = font.render("...", True, _MUTED_COLOR)
            surface.blit(overflow, (x, y))
            break

        color = _TEXT_COLOR
        text = line
        if line.startswith("## "):
            color = _HIGHLIGHT
            text = line[3:]
        elif line.startswith("-- "):
            color = _MUTED_COLOR
            text = line[3:]
        elif not line:
            y += max(4, font.get_height() // 3)
            continue

        surf = font.render(text, True, color)
        surface.blit(surf, (x, y))
        y += surf.get_height() + line_gap


def _draw_overview_page(surface: pygame.Surface, fonts, state: _HelpState, context_label: str) -> None:
    width, _ = surface.get_size()
    headline = fonts.hint_font.render("Help Overview", True, _HIGHLIGHT)
    surface.blit(headline, ((width - headline.get_width()) // 2, 118))
    lines = [
        f"## Context: {context_label}",
        "",
        "-- This help covers every game type, key category, and feature.",
        "-- All key names shown here are read live from the active keybinding profile.",
        "-- Use Left/Right to switch pages.",
        "-- Use Up/Down to switch dimension on controls/key pages.",
        "",
        "## Quick navigation",
        "- Page 2: controls helper with per-action icons",
        "- Page 3: full key map for selected dimension",
        "- Page 4: gameplay features (bot, challenge, exploration)",
        "- Page 5: settings, profiles, autosave/reset rules",
        "- Page 6: slicing and grid modes",
        "- Page 7: menu structure and workflow",
        "- Page 8: troubleshooting and gameplay shortcuts",
        "",
        "## Gameplay shortcut",
        f"- Help action ({_current_binding_text(state.dimension, 'help')}) opens this menu during gameplay.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=154)


def _draw_modes_page(surface: pygame.Surface, fonts) -> None:
    piece_sets_2d = ", ".join(piece_set_2d_label(piece_set_id) for piece_set_id in PIECE_SET_2D_OPTIONS)
    piece_sets_3d = ", ".join(piece_set_label(piece_set_id) for piece_set_id in piece_set_options_for_dimension(3))
    piece_sets_4d = ", ".join(piece_set_label(piece_set_id) for piece_set_id in piece_set_options_for_dimension(4))
    lines = [
        "## Game Types",
        "",
        "## 2D",
        "- Classic board with row clears on the X-line width.",
        f"- Piece sets: {piece_sets_2d}",
        "",
        "## 3D",
        "- Full 3D board with camera yaw/pitch/projection controls.",
        f"- Piece sets: {piece_sets_3d}",
        "",
        "## 4D",
        "- Displayed as multiple 3D boards (one board per W-layer).",
        f"- Piece sets: {piece_sets_4d}",
        "",
        "## Shared mechanics",
        "- Toggle grid modes, use pause menu, switch profiles, use bots.",
        "- Scoring includes placement points + clear points with assist multipliers.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_controls_page(surface: pygame.Surface, fonts, state: _HelpState) -> None:
    width, height = surface.get_size()
    header = fonts.hint_font.render(f"Controls Helper ({state.dimension}D)", True, _HIGHLIGHT)
    surface.blit(header, ((width - header.get_width()) // 2, 118))

    helper_rect = pygame.Rect(24, 150, width - 48, max(120, height - 176))
    draw_grouped_control_helper(
        surface,
        groups=control_groups_for_dimension(state.dimension),
        rect=helper_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )


def _draw_key_reference_page(surface: pygame.Surface, fonts, state: _HelpState) -> None:
    width, height = surface.get_size()
    title = fonts.hint_font.render(f"Full Key Map ({state.dimension}D)", True, _HIGHLIGHT)
    surface.blit(title, ((width - title.get_width()) // 2, 118))
    sub = fonts.hint_font.render(
        f"Live from active profile: {_current_binding_text(state.dimension, 'menu')}={binding_action_description('menu')}",
        True,
        _MUTED_COLOR,
    )
    surface.blit(sub, ((width - sub.get_width()) // 2, 140))

    groups = runtime_binding_groups_for_dimension(state.dimension)
    group_order = ("system", "game", "camera", "slice")
    y = 172
    line_h = fonts.hint_font.get_height() + 4
    left = 36

    for group_name in group_order:
        if group_name not in groups:
            continue

        header = fonts.hint_font.render(binding_group_label(group_name), True, _HIGHLIGHT)
        surface.blit(header, (left, y))
        y += header.get_height() + 3

        for action_name in sorted(groups[group_name].keys()):
            keys = format_key_tuple(tuple(groups[group_name][action_name]))
            desc = binding_action_description(action_name)
            row = f"{keys:<18} {desc}"
            row_surf = fonts.hint_font.render(row, True, _TEXT_COLOR)
            surface.blit(row_surf, (left + 12, y))
            y += line_h
            if y > height - 40:
                overflow = fonts.hint_font.render("...", True, _MUTED_COLOR)
                surface.blit(overflow, (left + 12, y))
                return
        y += 6


def _draw_features_page(surface: pygame.Surface, fonts) -> None:
    lines = [
        "## Gameplay Features",
        "",
        "## Bot modes",
        "- Off: human-only control.",
        "- Assist/Step/Auto: bot can suggest or play based on selected mode.",
        "",
        "## Dry-run",
        "- Setup menu includes dry-run validation (profile-independent command).",
        "- Useful for testing layer clears and piece-set viability.",
        "",
        "## Challenge mode",
        "- Starts with lower layers prefilled randomly.",
        "- Increases difficulty and changes opening planning.",
        "",
        "## Exploration mode",
        "- No gravity, no locking, no clears.",
        "- Hard-drop becomes piece-cycling for movement practice.",
        "- Board auto-sizes to minimal dimensions that fit and rotate selected pieces.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_settings_page(surface: pygame.Surface, fonts) -> None:
    lines: list[str] = [
        "## Settings, Profiles, and Persistence",
        "",
        "## Save policy",
        "- Autosave: silent session continuity.",
        "- Explicit Save: deliberate durable checkpoint.",
        "- Reset defaults: always requires confirmation.",
        "",
        "## Keybinding profiles",
        "- Create/Rename/Save-As/Delete custom profiles.",
        "- Load/Save keybinding files per dimension.",
        "- General/System keys are separated from 2D/3D/4D-specific groups.",
        "",
        "## Settings categories",
    ]
    for entry in _SETTINGS_DOCS:
        lines.append(f"- {entry['label']}: {entry['description']}")
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_slice_grid_page(surface: pygame.Surface, fonts) -> None:
    lines = [
        "## Slicing and Grid",
        "",
        "## Slice",
        "- Slicing fixes one axis coordinate for focused inspection.",
        "- In 4D, each W-layer is rendered as a separate 3D board.",
        "",
        "## Grid modes",
        "- OFF: board shadow only.",
        "- EDGE: only outer board edges.",
        "- FULL: full lattice grid.",
        "- HELPER: only lines that intersect current piece cells.",
        "",
        "## 4D helper behavior",
        "- Helper lines are now layer-local.",
        "- Lines appear only on W-boards containing current piece cells.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_workflows_page(surface: pygame.Surface, fonts) -> None:
    lines = [
        "## Menus and Workflow",
        "",
        "## Main launcher",
        "- Play 2D / 3D / 4D",
        "- Settings",
        "- Keybindings Setup",
        "- Bot Options",
        "- Help",
        "",
        "## Keybindings Setup",
        "- Top sections: General, 2D, 3D, 4D.",
        "- Enter opens section, Tab/Esc returns to sections.",
        "- Row view: action, bound key(s), description, and icon.",
        "",
        "## Pause parity",
        "- Pause menus expose Help, Settings, Bot Options, Keybindings, Restart, and Quit.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_troubleshooting_page(surface: pygame.Surface, fonts, state: _HelpState) -> None:
    dimension = state.dimension
    lines = [
        "## Troubleshooting",
        "",
        "- If controls feel wrong, open Keybindings Setup and verify active profile.",
        "- If settings look stale, save explicitly and re-open menu.",
        "- If visuals are crowded, reduce helper overlays and keep Edge/Off grid.",
        "- If gameplay debugging is needed, use debug piece sets + dry-run.",
        "",
        "## Gameplay help",
        f"- {_current_binding_text(dimension, 'help')}: open help directly during gameplay.",
        f"- {_current_binding_text(dimension, 'toggle_grid')}: cycle grid mode.",
        f"- {_current_binding_text(dimension, 'menu')}: open pause menu.",
        "",
        "## Exploration mode tip",
        "- Turn it on in setup to practice movement/rotation without gravity pressure.",
    ]
    _draw_lines(surface, fonts.hint_font, lines, x=34, y=132)


def _draw_help(surface: pygame.Surface, fonts, state: _HelpState, context_label: str) -> None:
    _draw_gradient(surface)
    width, _ = surface.get_size()
    help_binding = _current_binding_text(state.dimension, "help")
    title = fonts.title_font.render("Help & Explanations", True, _TEXT_COLOR)
    subtitle = fonts.hint_font.render(
        f"Left/Right page   Up/Down dimension   Esc back   Help key: {help_binding} (live profile)",
        True,
        _MUTED_COLOR,
    )
    page_label = fonts.hint_font.render(f"Page {state.page + 1}/{_PAGE_COUNT}", True, _MUTED_COLOR)
    surface.blit(title, ((width - title.get_width()) // 2, 34))
    surface.blit(subtitle, ((width - subtitle.get_width()) // 2, 82))
    surface.blit(page_label, (width - page_label.get_width() - 20, 16))

    if state.page == 0:
        _draw_overview_page(surface, fonts, state, context_label)
    elif state.page == 1:
        _draw_modes_page(surface, fonts)
    elif state.page == 2:
        _draw_controls_page(surface, fonts, state)
    elif state.page == 3:
        _draw_key_reference_page(surface, fonts, state)
    elif state.page == 4:
        _draw_features_page(surface, fonts)
    elif state.page == 5:
        _draw_settings_page(surface, fonts)
    elif state.page == 6:
        _draw_slice_grid_page(surface, fonts)
    elif state.page == 7:
        _draw_workflows_page(surface, fonts)
    else:
        _draw_troubleshooting_page(surface, fonts, state)


def run_help_menu(
    screen: pygame.Surface,
    fonts,
    *,
    dimension: int = 2,
    context_label: str = "Launcher",
) -> pygame.Surface:
    state = _HelpState(dimension=max(2, min(4, int(dimension))))
    clock = pygame.time.Clock()

    while state.running:
        _dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return screen
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                state.running = False
                break
            if event.key == pygame.K_LEFT:
                state.page = (state.page - 1) % _PAGE_COUNT
                continue
            if event.key == pygame.K_RIGHT:
                state.page = (state.page + 1) % _PAGE_COUNT
                continue
            if event.key == pygame.K_UP:
                state.dimension = 4 if state.dimension == 2 else state.dimension - 1
                continue
            if event.key == pygame.K_DOWN:
                state.dimension = 2 if state.dimension == 4 else state.dimension + 1
                continue

        _draw_help(screen, fonts, state, context_label)
        pygame.display.flip()

    return screen
