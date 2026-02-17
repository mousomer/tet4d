from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

from ..board import BoardND
from ..game2d import GameState
from ..pieces2d import ActivePiece2D, PieceShape2D, rotate_point_2d
from .types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    PlanStats,
    clamp_planning_budget_ms,
    default_planning_budget_ms,
    planning_lookahead_depth,
    planning_lookahead_top_k,
)


@dataclass(frozen=True)
class BotPlan2D:
    final_piece: ActivePiece2D
    stats: PlanStats


@dataclass(frozen=True)
class _Candidate2D:
    piece: ActivePiece2D
    score: float
    cleared: int
    cells_after: dict[tuple[int, int], int]
    game_over: bool


def _orientation_blocks(piece: ActivePiece2D, rotation: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(rotate_point_2d(x, y, rotation) for x, y in piece.shape.blocks))


def _can_exist_on_cells(
    piece: ActivePiece2D,
    *,
    cells: dict[tuple[int, int], int],
    width: int,
    height: int,
) -> bool:
    for x, y in piece.cells():
        if x < 0 or x >= width:
            return False
        if y >= height:
            return False
        if y < 0:
            continue
        if (x, y) in cells:
            return False
    return True


def _drop_piece_on_cells(
    piece: ActivePiece2D,
    *,
    cells: dict[tuple[int, int], int],
    width: int,
    height: int,
) -> ActivePiece2D:
    settled = piece
    while True:
        moved = settled.moved(0, 1)
        if not _can_exist_on_cells(moved, cells=cells, width=width, height=height):
            break
        settled = moved
    return settled


def _column_heights_holes(
    cells: dict[tuple[int, int], int],
    width: int,
    height: int,
) -> tuple[list[int], int]:
    heights: list[int] = [0] * width
    holes = 0
    for x in range(width):
        top_y: int | None = None
        for y in range(height):
            if (x, y) in cells:
                top_y = y
                break
        if top_y is None:
            continue
        heights[x] = height - top_y
        seen_block = False
        for y in range(top_y, height):
            occupied = (x, y) in cells
            if occupied:
                seen_block = True
            elif seen_block:
                holes += 1
    return heights, holes


def _evaluate_2d_board(
    cells: dict[tuple[int, int], int],
    width: int,
    height: int,
    cleared: int,
    game_over: bool,
) -> float:
    heights, holes = _column_heights_holes(cells, width, height)
    aggregate_height = sum(heights)
    bumpiness = sum(abs(heights[i] - heights[i + 1]) for i in range(max(0, width - 1)))
    max_height = max(heights) if heights else 0
    score = (
        cleared * 10000
        - aggregate_height * 4.0
        - holes * 26.0
        - bumpiness * 2.0
        - max_height * 8.0
    )
    if game_over:
        score -= 1e9
    return score


def _simulate_lock_board(
    *,
    board_cells: dict[tuple[int, int], int],
    width: int,
    height: int,
    gravity_axis: int,
    piece: ActivePiece2D,
) -> tuple[dict[tuple[int, int], int], int, bool]:
    game_over = any(y < 0 for _x, y in piece.cells())
    board = BoardND((width, height), cells=dict(board_cells))
    for x, y in piece.cells():
        if 0 <= x < width and 0 <= y < height:
            board.cells[(x, y)] = piece.shape.color_id
    cleared = board.clear_planes(gravity_axis)
    return dict(board.cells), cleared, game_over


def _simulate_lock_result(
    *,
    board_cells: dict[tuple[int, int], int],
    width: int,
    height: int,
    gravity_axis: int,
    piece: ActivePiece2D,
) -> tuple[float, int, dict[tuple[int, int], int], bool]:
    cells_after, cleared, game_over = _simulate_lock_board(
        board_cells=board_cells,
        width=width,
        height=height,
        gravity_axis=gravity_axis,
        piece=piece,
    )
    score = _evaluate_2d_board(cells_after, width, height, cleared, game_over)
    return score, cleared, cells_after, game_over


def _enumerate_candidates_2d(
    *,
    shape: PieceShape2D,
    board_cells: dict[tuple[int, int], int],
    width: int,
    height: int,
    gravity_axis: int,
    deadline_s: float,
) -> tuple[list[_Candidate2D], bool]:
    candidates: list[_Candidate2D] = []
    orientation_seen: set[tuple[tuple[int, int], ...]] = set()

    for rotation in range(4):
        orient = tuple(sorted(rotate_point_2d(x, y, rotation) for x, y in shape.blocks))
        if orient in orientation_seen:
            continue
        orientation_seen.add(orient)
        min_x = min(x for x, _y in orient)
        max_x = max(x for x, _y in orient)
        min_y = min(y for _x, y in orient)
        spawn_y = -2 - min_y

        for target_x in range(-min_x, width - max_x):
            if candidates and time.perf_counter() >= deadline_s:
                return candidates, True

            candidate = ActivePiece2D(shape=shape, pos=(target_x, spawn_y), rotation=rotation)
            if not _can_exist_on_cells(candidate, cells=board_cells, width=width, height=height):
                continue

            settled = _drop_piece_on_cells(candidate, cells=board_cells, width=width, height=height)
            score, cleared, cells_after, game_over = _simulate_lock_result(
                board_cells=board_cells,
                width=width,
                height=height,
                gravity_axis=gravity_axis,
                piece=settled,
            )
            candidates.append(
                _Candidate2D(
                    piece=settled,
                    score=score,
                    cleared=cleared,
                    cells_after=cells_after,
                    game_over=game_over,
                )
            )

    return candidates, False


def _pick_best_immediate(candidates: Iterable[_Candidate2D]) -> _Candidate2D | None:
    best: _Candidate2D | None = None
    best_score = float("-inf")
    best_clears = 0

    for candidate in candidates:
        if best is None:
            best = candidate
            best_score = candidate.score
            best_clears = candidate.cleared
            continue
        if candidate.score > best_score or (candidate.score == best_score and candidate.cleared > best_clears):
            best = candidate
            best_score = candidate.score
            best_clears = candidate.cleared
    return best


def _peek_next_shape(state: GameState) -> PieceShape2D | None:
    if not state.next_bag:
        return None
    return state.next_bag[-1]


def _followup_score_for_candidate(
    *,
    candidate: _Candidate2D,
    next_shape: PieceShape2D,
    width: int,
    height: int,
    gravity_axis: int,
    deadline_s: float,
) -> float:
    if candidate.game_over:
        return float("-inf")

    followup_candidates, _budget_hit = _enumerate_candidates_2d(
        shape=next_shape,
        board_cells=candidate.cells_after,
        width=width,
        height=height,
        gravity_axis=gravity_axis,
        deadline_s=deadline_s,
    )
    best = _pick_best_immediate(followup_candidates)
    if best is None:
        return float("-inf")
    return best.score


def _pick_with_optional_lookahead(
    *,
    candidates: list[_Candidate2D],
    next_shape: PieceShape2D | None,
    width: int,
    height: int,
    gravity_axis: int,
    profile: BotPlannerProfile,
    depth: int,
    deadline_s: float,
) -> tuple[_Candidate2D | None, float]:
    best_immediate = _pick_best_immediate(candidates)
    if best_immediate is None:
        return None, float("-inf")

    if depth <= 1 or next_shape is None:
        return best_immediate, best_immediate.score

    # Keep budget safety margin: if we're almost out of time, keep immediate best.
    if time.perf_counter() >= deadline_s - 0.001:
        return best_immediate, best_immediate.score

    top_k = planning_lookahead_top_k(2, profile)
    ranked = sorted(candidates, key=lambda c: (c.score, c.cleared), reverse=True)[:top_k]

    best_candidate = best_immediate
    best_combined = best_immediate.score
    followup_weight = 0.35

    for candidate in ranked:
        if time.perf_counter() >= deadline_s:
            break
        followup_score = _followup_score_for_candidate(
            candidate=candidate,
            next_shape=next_shape,
            width=width,
            height=height,
            gravity_axis=gravity_axis,
            deadline_s=deadline_s,
        )
        combined = candidate.score + followup_weight * followup_score
        if combined > best_combined or (
            combined == best_combined and candidate.cleared > best_candidate.cleared
        ):
            best_candidate = candidate
            best_combined = combined

    return best_candidate, best_combined


def plan_best_2d_move(
    state: GameState,
    *,
    profile: BotPlannerProfile = BotPlannerProfile.BALANCED,
    budget_ms: int | None = None,
    algorithm: BotPlannerAlgorithm = BotPlannerAlgorithm.AUTO,
) -> BotPlan2D | None:
    del algorithm  # reserved for parity with ND planner API
    piece = state.current_piece
    if piece is None:
        return None

    width = state.config.width
    height = state.config.height
    gravity_axis = state.config.gravity_axis

    planning_budget_ms = budget_ms
    if planning_budget_ms is None:
        planning_budget_ms = default_planning_budget_ms(2, profile)
    planning_budget_ms = clamp_planning_budget_ms(2, planning_budget_ms)

    t0 = time.perf_counter()
    deadline_s = t0 + planning_budget_ms / 1000.0

    candidates, _budget_hit = _enumerate_candidates_2d(
        shape=piece.shape,
        board_cells=state.board.cells,
        width=width,
        height=height,
        gravity_axis=gravity_axis,
        deadline_s=deadline_s,
    )
    if not candidates:
        return None

    depth = planning_lookahead_depth(2, profile)
    next_shape = _peek_next_shape(state)
    final_candidate, final_score = _pick_with_optional_lookahead(
        candidates=candidates,
        next_shape=next_shape,
        width=width,
        height=height,
        gravity_axis=gravity_axis,
        profile=profile,
        depth=depth,
        deadline_s=deadline_s,
    )
    if final_candidate is None:
        return None

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return BotPlan2D(
        final_piece=final_candidate.piece,
        stats=PlanStats(
            candidate_count=len(candidates),
            expected_clears=final_candidate.cleared,
            heuristic_score=final_score,
            planning_ms=elapsed_ms,
        ),
    )
