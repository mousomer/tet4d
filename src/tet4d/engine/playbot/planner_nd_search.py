from __future__ import annotations

import random
import time
from dataclasses import dataclass

from ..core.model import BoardND
from ..gameplay.game_nd import GameConfigND, GameStateND
from ..pieces_nd import ActivePieceND, PieceShapeND
from tet4d.ai.playbot.lookahead_common import choose_best_with_followup
from .planner_nd_core import (
    build_column_levels,
    canonical_blocks,
    enumerate_orientations,
    evaluate_nd_board,
    greedy_key_4d,
    greedy_score_4d,
    iter_settled_candidates,
    simulate_lock_board,
)
from .types import (
    BotPlannerAlgorithm,
    BotPlannerProfile,
    PlanStats,
    adaptive_candidate_cap,
    adaptive_deadline_safety_ms,
    planning_lookahead_depth,
    planning_lookahead_top_k,
    resolve_auto_planner_algorithm,
)


@dataclass(frozen=True)
class SearchPlanND:
    final_piece: ActivePieceND
    stats: PlanStats


@dataclass(frozen=True)
class _CandidateND:
    piece: ActivePieceND
    score: float
    cleared: int
    cells_after: dict[tuple[int, ...], int]
    game_over: bool


def _resolve_nd_algorithm(
    state: GameStateND, algorithm: BotPlannerAlgorithm
) -> BotPlannerAlgorithm:
    if algorithm != BotPlannerAlgorithm.AUTO:
        return algorithm
    return resolve_auto_planner_algorithm(
        ndim=state.config.ndim,
        dims=state.config.dims,
        occupied_cells=len(state.board.cells),
        lines_cleared=state.lines_cleared,
    )


def _peek_next_shape(state: GameStateND) -> PieceShapeND | None:
    if not state.next_bag:
        return None
    return state.next_bag[-1]


def _push_top_candidates(
    top_candidates: list[_CandidateND],
    candidate: _CandidateND,
    top_k: int,
) -> None:
    top_candidates.append(candidate)
    top_candidates.sort(key=lambda item: (item.score, item.cleared), reverse=True)
    if len(top_candidates) > top_k:
        top_candidates.pop()


def _build_candidate(
    *,
    settled: ActivePieceND,
    cells_after: dict[tuple[int, ...], int],
    cleared: int,
    game_over: bool,
    dims: tuple[int, ...],
    gravity_axis: int,
    algorithm: BotPlannerAlgorithm,
) -> _CandidateND:
    if algorithm == BotPlannerAlgorithm.GREEDY_LAYER:
        greedy = greedy_key_4d(
            cells_after,
            dims=dims,
            gravity_axis=gravity_axis,
            cleared=cleared,
            game_over=game_over,
        )
        score = greedy_score_4d(greedy)
    else:
        score = evaluate_nd_board(cells_after, dims, gravity_axis, cleared, game_over)
    return _CandidateND(
        piece=settled,
        score=score,
        cleared=cleared,
        cells_after=cells_after,
        game_over=game_over,
    )


def _better_candidate(
    current: _CandidateND | None, candidate: _CandidateND
) -> _CandidateND:
    if current is None:
        return candidate
    if candidate.score > current.score:
        return candidate
    if candidate.score == current.score and candidate.cleared > current.cleared:
        return candidate
    return current


def _spawn_followup_state_nd(
    cfg: GameConfigND,
    *,
    cells_after: dict[tuple[int, ...], int],
    next_shape: PieceShapeND,
) -> GameStateND:
    board = BoardND(cfg.dims, cells=dict(cells_after))
    return GameStateND(
        config=cfg,
        board=board,
        next_bag=[next_shape],
        rng=random.Random(0),
    )


def _followup_score_nd(
    *,
    candidate: _CandidateND,
    cfg: GameConfigND,
    next_shape: PieceShapeND,
    profile: BotPlannerProfile,
    depth: int,
    deadline_s: float,
    algorithm: BotPlannerAlgorithm,
    planning_budget_ms: int,
) -> float:
    if candidate.game_over or time.perf_counter() >= deadline_s:
        return float("-inf")

    follow_state = _spawn_followup_state_nd(
        cfg,
        cells_after=candidate.cells_after,
        next_shape=next_shape,
    )
    if follow_state.game_over or follow_state.current_piece is None:
        return float("-inf")

    follow_plan = _plan_best_nd_with_deadline(
        follow_state,
        profile=profile,
        depth=depth,
        deadline_s=deadline_s,
        algorithm=algorithm,
        planning_budget_ms=planning_budget_ms,
    )
    if follow_plan is None:
        return float("-inf")
    return follow_plan.stats.heuristic_score


def _apply_optional_lookahead(
    *,
    state: GameStateND,
    best_candidate: _CandidateND,
    top_candidates: list[_CandidateND],
    profile: BotPlannerProfile,
    depth: int,
    deadline_s: float,
    algorithm: BotPlannerAlgorithm,
    planning_budget_ms: int,
) -> tuple[_CandidateND, float]:
    safety_window = adaptive_deadline_safety_ms() / 1000.0
    can_lookahead = (
        algorithm == BotPlannerAlgorithm.HEURISTIC
        and depth > 1
        and time.perf_counter() < deadline_s - safety_window
    )
    next_shape = _peek_next_shape(state)
    if not can_lookahead or next_shape is None or not top_candidates:
        return best_candidate, best_candidate.score

    ranked = sorted(
        top_candidates, key=lambda item: (item.score, item.cleared), reverse=True
    )
    return choose_best_with_followup(
        candidates=ranked,
        base_candidate=best_candidate,
        score_of=lambda candidate: candidate.score,
        cleared_of=lambda candidate: candidate.cleared,
        followup_score_of=lambda candidate: _followup_score_nd(
            candidate=candidate,
            cfg=state.config,
            next_shape=next_shape,
            profile=profile,
            depth=depth - 1,
            deadline_s=deadline_s,
            algorithm=algorithm,
            planning_budget_ms=planning_budget_ms,
        ),
        deadline_s=deadline_s,
        followup_weight=0.30,
    )


def _plan_best_nd_with_deadline(
    state: GameStateND,
    *,
    profile: BotPlannerProfile,
    depth: int,
    deadline_s: float,
    algorithm: BotPlannerAlgorithm,
    planning_budget_ms: int,
) -> SearchPlanND | None:
    piece = state.current_piece
    if piece is None:
        return None

    t0 = time.perf_counter()
    cfg = state.config
    ndim = cfg.ndim
    gravity_axis = cfg.gravity_axis
    dims = cfg.dims
    lateral_axes = tuple(axis for axis in range(ndim) if axis != gravity_axis)

    active_algorithm = _resolve_nd_algorithm(state, algorithm)

    orientations = enumerate_orientations(
        canonical_blocks(piece.rel_blocks),
        ndim,
        gravity_axis,
    )
    column_levels = build_column_levels(
        state.board.cells,
        lateral_axes=lateral_axes,
        gravity_axis=gravity_axis,
    )

    best_candidate: _CandidateND | None = None
    candidate_count = 0
    top_candidates: list[_CandidateND] = []
    top_k = planning_lookahead_top_k(ndim, profile, budget_ms=planning_budget_ms)
    candidate_cap = adaptive_candidate_cap(ndim, planning_budget_ms, dims=dims)

    for settled in iter_settled_candidates(
        state,
        piece=piece,
        orientations=orientations,
        ndim=ndim,
        dims=dims,
        gravity_axis=gravity_axis,
        lateral_axes=lateral_axes,
        column_levels=column_levels,
    ):
        if candidate_count > 0 and time.perf_counter() >= deadline_s:
            break
        if candidate_count >= candidate_cap:
            break

        candidate_count += 1
        cells_after, cleared, game_over = simulate_lock_board(state, settled)
        candidate = _build_candidate(
            settled=settled,
            cells_after=cells_after,
            cleared=cleared,
            game_over=game_over,
            dims=dims,
            gravity_axis=gravity_axis,
            algorithm=active_algorithm,
        )

        best_candidate = _better_candidate(best_candidate, candidate)
        if depth > 1 and active_algorithm == BotPlannerAlgorithm.HEURISTIC:
            _push_top_candidates(top_candidates, candidate, top_k)

    if best_candidate is None:
        return None

    final_candidate, final_score = _apply_optional_lookahead(
        state=state,
        best_candidate=best_candidate,
        top_candidates=top_candidates,
        profile=profile,
        depth=depth,
        deadline_s=deadline_s,
        algorithm=active_algorithm,
        planning_budget_ms=planning_budget_ms,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return SearchPlanND(
        final_piece=final_candidate.piece,
        stats=PlanStats(
            candidate_count=candidate_count,
            expected_clears=final_candidate.cleared,
            heuristic_score=final_score,
            planning_ms=elapsed_ms,
        ),
    )


def plan_best_nd_with_budget(
    state: GameStateND,
    *,
    profile: BotPlannerProfile,
    planning_budget_ms: int,
    algorithm: BotPlannerAlgorithm,
) -> SearchPlanND | None:
    depth = planning_lookahead_depth(
        state.config.ndim,
        profile,
        budget_ms=planning_budget_ms,
    )
    deadline_s = time.perf_counter() + planning_budget_ms / 1000.0
    return _plan_best_nd_with_deadline(
        state,
        profile=profile,
        depth=depth,
        deadline_s=deadline_s,
        algorithm=algorithm,
        planning_budget_ms=planning_budget_ms,
    )
