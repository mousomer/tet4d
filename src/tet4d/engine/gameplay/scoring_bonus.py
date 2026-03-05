from __future__ import annotations

import math
from functools import reduce
from operator import mul
from typing import Sequence

from tet4d.engine.core.rules.scoring import score_for_clear
from tet4d.engine.runtime.runtime_config import (
    clear_scoring_board_clear_bonus,
    clear_scoring_layer_size_weighting,
    clear_scoring_multi_layer_bonus,
)


def plane_cell_count_for_dims(dims: Sequence[int], *, gravity_axis: int) -> int:
    if not dims:
        return 1
    if gravity_axis < 0 or gravity_axis >= len(dims):
        return 1
    plane_axes = [int(size) for index, size in enumerate(dims) if index != gravity_axis]
    if not plane_axes:
        return 1
    positive_axes = [max(1, axis_size) for axis_size in plane_axes]
    return int(reduce(mul, positive_axes, 1))


def _weighted_clear_points(cleared_count: int, plane_cell_count: int) -> int:
    base_clear_points = score_for_clear(cleared_count)
    if base_clear_points <= 0:
        return 0
    enabled, reference_plane_cells = clear_scoring_layer_size_weighting()
    if not enabled:
        return int(base_clear_points)
    normalized_plane_cells = max(1, int(plane_cell_count))
    normalized_reference = max(1, int(reference_plane_cells))
    ratio = max(1.0, normalized_plane_cells / normalized_reference)
    scale = math.sqrt(ratio)
    return int(round(float(base_clear_points) * scale))


def score_with_clear_bonuses(
    *,
    raw_base_points: int,
    cleared_count: int,
    plane_cell_count: int = 1,
    board_cell_count_after_clear: int,
    score_multiplier: float,
) -> tuple[int, int]:
    raw_points = int(raw_base_points)
    cleared = max(0, int(cleared_count))
    weighted_clear_points = _weighted_clear_points(cleared, int(plane_cell_count))
    raw_points += weighted_clear_points - score_for_clear(cleared)
    raw_points += clear_scoring_multi_layer_bonus(cleared)
    if cleared > 0 and int(board_cell_count_after_clear) == 0:
        raw_points += clear_scoring_board_clear_bonus()
    multiplier = max(0.1, float(score_multiplier))
    awarded_points = max(0, int(round(raw_points * multiplier)))
    return raw_points, awarded_points


__all__ = ["plane_cell_count_for_dims", "score_with_clear_bonuses"]
