from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..core.model import BoardND, Coord
from ..core.rules.locking import apply_lock_and_score
from ..runtime.score_analyzer import analyze_lock_event, record_score_analysis_event
from .scoring_bonus import plane_cell_count_for_dims, score_with_clear_bonuses


@dataclass(frozen=True)
class LockFlowResult:
    cleared: int
    raw_points: int
    awarded_points: int
    analysis: dict[str, object]


def visible_locked_cells(
    mapped_cells: Sequence[Coord], *, gravity_axis: int
) -> tuple[Coord, ...]:
    return tuple(coord for coord in mapped_cells if coord[gravity_axis] >= 0)


def has_cells_above_gravity(mapped_cells: Sequence[Coord], *, gravity_axis: int) -> bool:
    return any(coord[gravity_axis] < 0 for coord in mapped_cells)


def apply_lock_flow(
    *,
    board: BoardND,
    board_pre: dict[Coord, int],
    dims: Coord,
    gravity_axis: int,
    visible_piece_cells: Sequence[Coord],
    color_id: int,
    lock_piece_points: int,
    score_multiplier: float,
    piece_id: str,
    actor_mode: str,
    bot_mode: str,
    grid_mode: str,
    speed_level: int,
    session_id: str,
    seq: int,
) -> LockFlowResult:
    lock_result = apply_lock_and_score(
        board=board,
        visible_piece_cells=visible_piece_cells,
        color_id=color_id,
        gravity_axis=gravity_axis,
        lock_piece_points=lock_piece_points,
        score_multiplier=score_multiplier,
    )
    raw_points, awarded_points = score_with_clear_bonuses(
        raw_base_points=lock_result.raw_points,
        cleared_count=lock_result.cleared,
        plane_cell_count=plane_cell_count_for_dims(
            dims,
            gravity_axis=gravity_axis,
        ),
        board_cell_count_after_clear=len(board.cells),
        score_multiplier=score_multiplier,
    )
    analysis = analyze_lock_event(
        board_pre=board_pre,
        board_post=dict(board.cells),
        dims=dims,
        gravity_axis=gravity_axis,
        locked_cells=visible_piece_cells,
        cleared=lock_result.cleared,
        piece_id=piece_id,
        actor_mode=actor_mode,
        bot_mode=bot_mode,
        grid_mode=grid_mode,
        speed_level=speed_level,
        raw_points=raw_points,
        final_points=awarded_points,
        session_id=session_id,
        seq=seq,
    )
    record_score_analysis_event(analysis)
    return LockFlowResult(
        cleared=lock_result.cleared,
        raw_points=raw_points,
        awarded_points=awarded_points,
        analysis=analysis,
    )
