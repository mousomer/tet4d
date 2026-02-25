from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import pygame

from .control_helper import control_groups_for_dimension, draw_grouped_control_helper
from .panel_utils import render_text_cached, truncate_lines_to_height
from .runtime.score_analyzer import hud_analysis_lines
from .ui_utils import fit_text
from .view_modes import GridMode, grid_mode_label


def _draw_side_panel_text(
    surface: pygame.Surface,
    state: Any,
    panel_offset: tuple[int, int],
    fonts: Any,
    grid_mode: GridMode,
    *,
    side_panel_width: int,
    text_color: tuple[int, int, int],
    gravity_interval_from_config: Callable[[Any], int],
) -> int:
    px, py = panel_offset
    gravity_ms = gravity_interval_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0

    lines = [
        "2D Tetris",
        "",
        f"Score: {state.score}",
        f"Lines: {state.lines_cleared}",
        f"Speed level: {state.config.speed_level}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Fall: {rows_per_sec:.2f} rows/s",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Grid: {grid_mode_label(grid_mode)}",
    ]

    y = py
    for line in lines:
        render_line = fit_text(fonts.panel_font, line, side_panel_width - 4)
        surf = render_text_cached(
            font=fonts.panel_font, text=render_line, color=text_color
        )
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4
    return y


def draw_side_panel_2d(
    surface: pygame.Surface,
    state: Any,
    panel_offset: tuple[int, int],
    fonts: Any,
    *,
    grid_mode: GridMode = GridMode.FULL,
    bot_lines: Sequence[str] = (),
    side_panel_width: int = 200,
    text_color: tuple[int, int, int] = (230, 230, 230),
    gravity_interval_from_config: Callable[[Any], int],
) -> None:
    analysis_lines = hud_analysis_lines(state.last_score_analysis)
    low_priority_lines = [
        *bot_lines,
        *([""] if bot_lines and analysis_lines else []),
        *analysis_lines,
    ]
    y_after_text = _draw_side_panel_text(
        surface,
        state,
        panel_offset,
        fonts,
        grid_mode,
        side_panel_width=side_panel_width,
        text_color=text_color,
        gravity_interval_from_config=gravity_interval_from_config,
    )

    px, _ = panel_offset
    panel_bottom = surface.get_height() - 8
    controls_top = y_after_text + 6
    reserve_bottom = 58 if state.game_over else 0
    available_h = max(0, panel_bottom - reserve_bottom - controls_top)
    min_controls_h = 116
    gap = 6

    low_lines: tuple[str, ...] = tuple()
    low_h = 0
    if low_priority_lines:
        max_low_h = max(0, available_h - min_controls_h - gap)
        low_lines = truncate_lines_to_height(
            low_priority_lines,
            font=fonts.hint_font,
            available_height=max(0, max_low_h - 8),
            line_gap=3,
        )
        if low_lines:
            low_h = len(low_lines) * (fonts.hint_font.get_height() + 3) + 10

    controls_bottom = panel_bottom - reserve_bottom - (low_h + gap if low_h else 0)
    if controls_bottom - controls_top < 42 and low_h:
        low_lines = tuple()
        low_h = 0
        controls_bottom = panel_bottom - reserve_bottom

    controls_rect = pygame.Rect(
        px, controls_top, side_panel_width, max(42, controls_bottom - controls_top)
    )
    draw_grouped_control_helper(
        surface,
        groups=control_groups_for_dimension(
            2,
            include_exploration=bool(state.config.exploration_mode),
        ),
        rect=controls_rect,
        panel_font=fonts.panel_font,
        hint_font=fonts.hint_font,
    )
    if low_lines:
        low_height = panel_bottom - (controls_rect.bottom + 8)
        if low_height > 10:
            low_rect = pygame.Rect(
                px + 2,
                controls_rect.bottom + 6,
                side_panel_width - 4,
                low_height,
            )
            panel = pygame.Surface((low_rect.width, low_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(panel, (8, 12, 26, 100), panel.get_rect(), border_radius=8)
            surface.blit(panel, low_rect.topleft)
            low_y = low_rect.y + 5
            for line in low_lines:
                surf = render_text_cached(
                    font=fonts.hint_font,
                    text=line,
                    color=(176, 188, 222),
                )
                surface.blit(surf, (low_rect.x + 6, low_y))
                low_y += surf.get_height() + 3

    if state.game_over:
        y = surface.get_height() - 58
        surf = render_text_cached(
            font=fonts.panel_font, text="GAME OVER", color=(255, 80, 80)
        )
        surface.blit(surf, (px, y))
        y += surf.get_height() + 4
        surf2 = render_text_cached(
            font=fonts.panel_font,
            text="Press R to restart",
            color=(255, 200, 200),
        )
        surface.blit(surf2, (px, y))
