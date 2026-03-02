from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import pygame

import tet4d.engine.api as engine_api
from tet4d.ui.pygame.render.panel_utils import draw_unified_game_side_panel


def draw_side_panel_2d(
    surface: pygame.Surface,
    state: Any,
    panel_offset: tuple[int, int],
    fonts: Any,
    *,
    grid_mode: engine_api.GridMode = engine_api.GridMode.FULL,
    bot_lines: Sequence[str] = (),
    side_panel_width: int = 200,
    text_color: tuple[int, int, int] = (230, 230, 230),
    gravity_interval_from_config: Callable[[Any], int],
) -> None:
    _ = text_color
    px, py = panel_offset
    gravity_ms = gravity_interval_from_config(state.config)
    rows_per_sec = 1000.0 / gravity_ms if gravity_ms > 0 else 0.0
    analysis_lines = engine_api.hud_analysis_lines_runtime(state.last_score_analysis)
    data_lines = [
        f"Dims: ({state.config.width}, {state.config.height})",
        f"Score mod: x{state.score_multiplier:.2f}",
        f"Exploration: {'ON' if state.config.exploration_mode else 'OFF'}",
        f"Fall: {rows_per_sec:.2f} rows/s",
        f"Grid: {engine_api.grid_mode_label_view(grid_mode)}",
    ]
    panel_rect = pygame.Rect(
        px,
        py,
        side_panel_width,
        max(120, surface.get_height() - py - 8),
    )
    draw_unified_game_side_panel(
        surface,
        panel_rect=panel_rect,
        fonts=fonts,
        title="2D Tetris",
        score=state.score,
        lines_cleared=state.lines_cleared,
        speed_level=state.config.speed_level,
        dimension=2,
        include_exploration=bool(state.config.exploration_mode),
        data_lines=data_lines,
        bot_lines=bot_lines,
        analysis_lines=analysis_lines,
        game_over=state.game_over,
        min_controls_h=116,
    )
