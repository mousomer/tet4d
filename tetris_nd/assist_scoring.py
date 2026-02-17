from __future__ import annotations

from .playbot.types import BotMode
from .view_modes import GridMode


def bot_score_factor(mode: BotMode) -> float:
    if mode == BotMode.OFF:
        return 1.0
    if mode == BotMode.ASSIST:
        return 0.86
    if mode == BotMode.AUTO:
        return 0.58
    return 0.48


def grid_score_factor(mode: GridMode) -> float:
    if mode in (GridMode.OFF, GridMode.SHADOW):
        return 1.0
    if mode == GridMode.EDGE:
        return 0.94
    if mode == GridMode.FULL:
        return 0.88
    return 0.78


def speed_score_factor(speed_level: int) -> float:
    level = max(1, min(10, int(speed_level)))
    # Slower speed = easier game = lower score.
    return min(1.0, 0.55 + 0.05 * level)


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
    return max(0.2, min(1.0, combined))
