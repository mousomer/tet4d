from __future__ import annotations

from tet4d.ai.playbot.types import BotMode
from .runtime_config import (
    assist_bot_factor,
    assist_combined_bounds,
    assist_grid_factor,
    assist_speed_formula,
)
from ..ui_logic.view_modes import GridMode


def bot_score_factor(mode: BotMode) -> float:
    return assist_bot_factor(mode.value)


def grid_score_factor(mode: GridMode) -> float:
    return assist_grid_factor(mode.value)


def speed_score_factor(speed_level: int) -> float:
    base, per_level, min_level, max_level = assist_speed_formula()
    level = max(min_level, min(max_level, int(speed_level)))
    # Slower speed = easier game = lower score.
    return min(1.0, base + per_level * level)


def combined_score_multiplier(
    *,
    bot_mode: BotMode,
    grid_mode: GridMode,
    speed_level: int,
) -> float:
    combined = (
        bot_score_factor(bot_mode)
        * grid_score_factor(grid_mode)
        * speed_score_factor(speed_level)
    )
    min_factor, max_factor = assist_combined_bounds()
    return max(min_factor, min(max_factor, combined))
