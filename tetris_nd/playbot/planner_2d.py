from __future__ import annotations

import time
from dataclasses import dataclass

from ..board import BoardND
from ..game2d import GameState
from ..pieces2d import ActivePiece2D, rotate_point_2d
from .types import PlanStats


@dataclass(frozen=True)
class BotPlan2D:
    final_piece: ActivePiece2D
    stats: PlanStats


def _orientation_blocks(piece: ActivePiece2D, rotation: int) -> tuple[tuple[int, int], ...]:
    return tuple(sorted(rotate_point_2d(x, y, rotation) for x, y in piece.shape.blocks))


def _drop_piece(state: GameState, piece: ActivePiece2D) -> ActivePiece2D:
    settled = piece
    while True:
        moved = settled.moved(0, 1)
        if not state._can_exist(moved):
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


def _simulate_lock_result(state: GameState, piece: ActivePiece2D) -> tuple[float, int]:
    width, height = state.config.width, state.config.height
    game_over = any(y < 0 for _x, y in piece.cells())
    board = BoardND((width, height), cells=dict(state.board.cells))
    for x, y in piece.cells():
        if 0 <= x < width and 0 <= y < height:
            board.cells[(x, y)] = piece.shape.color_id
    cleared = board.clear_planes(state.config.gravity_axis)
    score = _evaluate_2d_board(board.cells, width, height, cleared, game_over)
    return score, cleared


def plan_best_2d_move(state: GameState) -> BotPlan2D | None:
    piece = state.current_piece
    if piece is None:
        return None

    t0 = time.perf_counter()
    width = state.config.width
    candidate_count = 0
    best_score = float("-inf")
    best_clears = 0
    best_piece: ActivePiece2D | None = None

    orientation_seen: set[tuple[tuple[int, int], ...]] = set()
    for rotation in range(4):
        orient = _orientation_blocks(piece, rotation)
        if orient in orientation_seen:
            continue
        orientation_seen.add(orient)
        min_x = min(x for x, _y in orient)
        max_x = max(x for x, _y in orient)
        min_y = min(y for _x, y in orient)
        spawn_y = -2 - min_y
        for target_x in range(-min_x, width - max_x):
            candidate = ActivePiece2D(
                shape=piece.shape,
                pos=(target_x, spawn_y),
                rotation=rotation,
            )
            if not state._can_exist(candidate):
                continue
            settled = _drop_piece(state, candidate)
            candidate_count += 1
            score, cleared = _simulate_lock_result(state, settled)
            if (
                score > best_score
                or (score == best_score and cleared > best_clears)
            ):
                best_score = score
                best_clears = cleared
                best_piece = settled

    if best_piece is None:
        return None

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return BotPlan2D(
        final_piece=best_piece,
        stats=PlanStats(
            candidate_count=candidate_count,
            expected_clears=best_clears,
            heuristic_score=best_score,
            planning_ms=elapsed_ms,
        ),
    )
