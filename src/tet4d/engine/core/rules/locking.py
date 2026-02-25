from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..model.board import BoardND
from ..model.types import Coord
from .scoring import score_for_clear


@dataclass(frozen=True)
class LockScoreResult:
    cleared: int
    raw_points: int
    awarded_points: int


def apply_lock_and_score(
    *,
    board: BoardND,
    visible_piece_cells: Iterable[Coord],
    color_id: int,
    gravity_axis: int,
    lock_piece_points: int,
    score_multiplier: float,
) -> LockScoreResult:
    for coord in visible_piece_cells:
        board.cells[coord] = color_id

    cleared = board.clear_planes(gravity_axis)
    raw_points = int(lock_piece_points) + score_for_clear(cleared)
    mult = max(0.1, float(score_multiplier))
    awarded_points = max(0, int(round(raw_points * mult)))
    return LockScoreResult(
        cleared=cleared,
        raw_points=raw_points,
        awarded_points=awarded_points,
    )


__all__ = ["LockScoreResult", "apply_lock_and_score"]
