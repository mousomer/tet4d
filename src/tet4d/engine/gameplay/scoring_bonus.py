from __future__ import annotations

from tet4d.engine.runtime.runtime_config import (
    clear_scoring_board_clear_bonus,
    clear_scoring_multi_layer_bonus,
)


def score_with_clear_bonuses(
    *,
    raw_base_points: int,
    cleared_count: int,
    board_cell_count_after_clear: int,
    score_multiplier: float,
) -> tuple[int, int]:
    raw_points = int(raw_base_points)
    cleared = max(0, int(cleared_count))
    raw_points += clear_scoring_multi_layer_bonus(cleared)
    if cleared > 0 and int(board_cell_count_after_clear) == 0:
        raw_points += clear_scoring_board_clear_bonus()
    multiplier = max(0.1, float(score_multiplier))
    awarded_points = max(0, int(round(raw_points * multiplier)))
    return raw_points, awarded_points


__all__ = ["score_with_clear_bonuses"]
