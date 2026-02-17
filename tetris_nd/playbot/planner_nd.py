from __future__ import annotations

import time
from bisect import bisect_right
from collections import deque
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Iterable

from ..board import BoardND
from ..game_nd import GameStateND
from ..pieces_nd import ActivePieceND, rotate_point_nd
from .types import PlanStats


RotationStep = tuple[int, int, int]
RelBlocks = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class BotPlanND:
    final_piece: ActivePieceND
    stats: PlanStats


def _canonical_blocks(blocks: Iterable[tuple[int, ...]]) -> RelBlocks:
    return tuple(sorted(tuple(block) for block in blocks))


def _rotation_planes(ndim: int, gravity_axis: int) -> tuple[tuple[int, int], ...]:
    if ndim == 3:
        extra = [axis for axis in range(ndim) if axis != 0 and axis != gravity_axis]
        z_axis = extra[0] if extra else 2
        return (
            (0, gravity_axis),
            (0, z_axis),
            (gravity_axis, z_axis),
        )
    pairs: list[tuple[int, int]] = []
    for axis_a in range(ndim):
        for axis_b in range(axis_a + 1, ndim):
            pairs.append((axis_a, axis_b))
    return tuple(pairs)


@lru_cache(maxsize=512)
def _enumerate_orientations(
    start_blocks: RelBlocks,
    ndim: int,
    gravity_axis: int,
) -> tuple[RelBlocks, ...]:
    planes = _rotation_planes(ndim, gravity_axis)
    max_depth = 7 if ndim == 3 else 6
    max_orientations = 96 if ndim == 3 else 180

    queue: deque[tuple[RelBlocks, int]] = deque([(start_blocks, 0)])
    seen: set[RelBlocks] = {start_blocks}
    ordered: list[RelBlocks] = [start_blocks]

    while queue and len(seen) < max_orientations:
        blocks, depth = queue.popleft()
        if depth >= max_depth:
            continue
        for axis_a, axis_b in planes:
            for step in (1, -1):
                rotated = _canonical_blocks(
                    rotate_point_nd(block, axis_a, axis_b, step)
                    for block in blocks
                )
                if rotated in seen:
                    continue
                seen.add(rotated)
                ordered.append(rotated)
                queue.append((rotated, depth + 1))
                if len(seen) >= max_orientations:
                    break
            if len(seen) >= max_orientations:
                break
    return tuple(ordered)


def _build_column_levels(
    cells: dict[tuple[int, ...], int],
    *,
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
) -> dict[tuple[int, ...], list[int]]:
    levels: dict[tuple[int, ...], list[int]] = {}
    for coord in cells:
        column = tuple(coord[axis] for axis in lateral_axes)
        values = levels.setdefault(column, [])
        values.append(coord[gravity_axis])
    for values in levels.values():
        values.sort()
    return levels


def _drop_piece_fast(
    piece: ActivePieceND,
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    lateral_axes: tuple[int, ...],
    column_levels: dict[tuple[int, ...], list[int]],
) -> ActivePieceND:
    drop_limit = 10**9
    for block in piece.rel_blocks:
        curr_g = piece.pos[gravity_axis] + block[gravity_axis]
        max_drop = dims[gravity_axis] - 1 - curr_g
        column = tuple(piece.pos[axis] + block[axis] for axis in lateral_axes)
        levels = column_levels.get(column)
        if levels:
            idx = bisect_right(levels, curr_g)
            if idx < len(levels):
                max_drop = min(max_drop, levels[idx] - 1 - curr_g)
        if max_drop < drop_limit:
            drop_limit = max_drop
        if drop_limit <= 0:
            return piece

    if drop_limit <= 0:
        return piece
    delta = [0] * len(dims)
    delta[gravity_axis] = drop_limit
    return piece.moved(delta)


def _column_key(coord: tuple[int, ...], lateral_axes: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(coord[axis] for axis in lateral_axes)


def _iter_lateral_columns(dims: tuple[int, ...], lateral_axes: tuple[int, ...]) -> Iterable[tuple[int, ...]]:
    axis_sizes = [dims[axis] for axis in lateral_axes]
    if not axis_sizes:
        yield tuple()
        return
    for values in product(*(range(size) for size in axis_sizes)):
        yield tuple(values)


def _coord_from_column(
    column: tuple[int, ...],
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
    gravity_value: int,
    ndim: int,
) -> tuple[int, ...]:
    coord = [0] * ndim
    coord[gravity_axis] = gravity_value
    for idx, axis in enumerate(lateral_axes):
        coord[axis] = column[idx]
    return tuple(coord)


def _height_features(
    cells: dict[tuple[int, ...], int],
    dims: tuple[int, ...],
    gravity_axis: int,
) -> tuple[int, int, int, int]:
    lateral_axes = tuple(axis for axis in range(len(dims)) if axis != gravity_axis)
    top_by_col = _top_by_column(cells, lateral_axes, gravity_axis)

    heights: dict[tuple[int, ...], int] = {}
    holes = 0
    aggregate_height = 0
    max_height = 0

    for column in _iter_lateral_columns(dims, lateral_axes):
        top = top_by_col.get(column)
        if top is None:
            heights[column] = 0
            continue

        height, col_holes = _column_height_and_holes(
            column,
            top,
            cells,
            dims=dims,
            lateral_axes=lateral_axes,
            gravity_axis=gravity_axis,
        )
        heights[column] = height
        aggregate_height += height
        if height > max_height:
            max_height = height
        holes += col_holes

    roughness = _height_roughness(heights, dims=dims, lateral_axes=lateral_axes)

    return aggregate_height, holes, roughness, max_height


def _top_by_column(
    cells: dict[tuple[int, ...], int],
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
) -> dict[tuple[int, ...], int]:
    top_by_col: dict[tuple[int, ...], int] = {}
    for coord in cells:
        column = _column_key(coord, lateral_axes)
        g_val = coord[gravity_axis]
        prev = top_by_col.get(column)
        if prev is None or g_val < prev:
            top_by_col[column] = g_val
    return top_by_col


def _column_height_and_holes(
    column: tuple[int, ...],
    top: int,
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    lateral_axes: tuple[int, ...],
    gravity_axis: int,
) -> tuple[int, int]:
    g_size = dims[gravity_axis]
    height = g_size - top
    holes = 0
    seen_block = False
    for g_val in range(top, g_size):
        coord = _coord_from_column(column, lateral_axes, gravity_axis, g_val, len(dims))
        if coord in cells:
            seen_block = True
        elif seen_block:
            holes += 1
    return height, holes


def _height_roughness(
    heights: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    lateral_axes: tuple[int, ...],
) -> int:
    roughness = 0
    for column, h_val in heights.items():
        column_list = list(column)
        for axis_idx, axis in enumerate(lateral_axes):
            if column[axis_idx] + 1 >= dims[axis]:
                continue
            column_list[axis_idx] += 1
            neighbor = tuple(column_list)
            column_list[axis_idx] -= 1
            roughness += abs(h_val - heights.get(neighbor, 0))
    return roughness


def _evaluate_nd_board(
    cells: dict[tuple[int, ...], int],
    dims: tuple[int, ...],
    gravity_axis: int,
    cleared: int,
    game_over: bool,
) -> float:
    aggregate_height, holes, roughness, max_height = _height_features(cells, dims, gravity_axis)
    score = (
        cleared * 12000
        - aggregate_height * 3.8
        - holes * 28.0
        - roughness * 1.7
        - max_height * 8.5
    )
    if game_over:
        score -= 1e9
    return score


def _simulate_lock_board(
    state: GameStateND,
    piece: ActivePieceND,
) -> tuple[dict[tuple[int, ...], int], int, bool]:
    dims = state.config.dims
    gravity_axis = state.config.gravity_axis
    game_over = any(coord[gravity_axis] < 0 for coord in piece.cells())
    board = BoardND(dims, cells=dict(state.board.cells))
    for coord in piece.cells():
        if board.inside_bounds(coord):
            board.cells[coord] = piece.shape.color_id
    cleared = board.clear_planes(gravity_axis)
    return dict(board.cells), cleared, game_over


def _simulate_lock_result(state: GameStateND, piece: ActivePieceND) -> tuple[float, int]:
    cells_after, cleared, game_over = _simulate_lock_board(state, piece)
    dims = state.config.dims
    gravity_axis = state.config.gravity_axis
    score = _evaluate_nd_board(cells_after, dims, gravity_axis, cleared, game_over)
    return score, cleared


def _level_completion_score(
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
) -> int:
    counts = [0] * dims[gravity_axis]
    for coord in cells:
        counts[coord[gravity_axis]] += 1
    # Squared occupancy rewards concentrating blocks in nearly-finished layers.
    return sum(count * count for count in counts)


def _hole_count(
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
) -> int:
    lateral_axes = tuple(axis for axis in range(len(dims)) if axis != gravity_axis)
    top_by_col: dict[tuple[int, ...], int] = {}
    for coord in cells:
        column = _column_key(coord, lateral_axes)
        g_val = coord[gravity_axis]
        prev = top_by_col.get(column)
        if prev is None or g_val < prev:
            top_by_col[column] = g_val

    holes = 0
    for column in _iter_lateral_columns(dims, lateral_axes):
        top = top_by_col.get(column)
        if top is None:
            continue
        seen_block = False
        for g_val in range(top, dims[gravity_axis]):
            coord = _coord_from_column(column, lateral_axes, gravity_axis, g_val, len(dims))
            if coord in cells:
                seen_block = True
            elif seen_block:
                holes += 1
    return holes


def _greedy_key_4d(
    cells: dict[tuple[int, ...], int],
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    cleared: int,
    game_over: bool,
) -> tuple[int, int, int, int]:
    completion = _level_completion_score(cells, dims=dims, gravity_axis=gravity_axis)
    holes = _hole_count(cells, dims=dims, gravity_axis=gravity_axis)
    # Priority order:
    # 1) non-gameover outcomes
    # 2) clear/finish layers
    # 3) avoid holes
    return (
        0 if game_over else 1,
        cleared,
        completion,
        -holes,
    )


def _greedy_score_4d(greedy_key: tuple[int, int, int, int]) -> float:
    alive, cleared, completion, neg_holes = greedy_key
    holes = -neg_holes
    return float(alive * 1_000_000_000 + cleared * 10_000_000 + completion - holes * 1_000)


def _lateral_ranges_for_blocks(
    blocks: RelBlocks,
    *,
    ndim: int,
    dims: tuple[int, ...],
    lateral_axes: tuple[int, ...],
) -> tuple[list[range], list[int]]:
    mins = [min(block[axis] for block in blocks) for axis in range(ndim)]
    maxs = [max(block[axis] for block in blocks) for axis in range(ndim)]
    ranges: list[range] = []
    for axis in lateral_axes:
        start = -mins[axis]
        stop = dims[axis] - maxs[axis]
        if start >= stop:
            return [], mins
        ranges.append(range(start, stop))
    return ranges, mins


def _candidate_from_lateral_values(
    *,
    shape,
    blocks: RelBlocks,
    ndim: int,
    gravity_axis: int,
    lateral_axes: tuple[int, ...],
    lateral_values: tuple[int, ...],
    spawn_g: int,
) -> ActivePieceND:
    pos = [0] * ndim
    pos[gravity_axis] = spawn_g
    for idx, axis in enumerate(lateral_axes):
        pos[axis] = lateral_values[idx]
    return ActivePieceND(
        shape=shape,
        pos=tuple(pos),
        rel_blocks=blocks,
    )


def _iter_settled_candidates(
    state: GameStateND,
    *,
    piece: ActivePieceND,
    orientations: tuple[RelBlocks, ...],
    ndim: int,
    dims: tuple[int, ...],
    gravity_axis: int,
    lateral_axes: tuple[int, ...],
    column_levels: dict[tuple[int, ...], list[int]],
) -> Iterable[ActivePieceND]:
    for blocks in orientations:
        ranges, mins = _lateral_ranges_for_blocks(
            blocks,
            ndim=ndim,
            dims=dims,
            lateral_axes=lateral_axes,
        )
        if not ranges:
            continue
        spawn_g = -2 - mins[gravity_axis]
        for lateral_values in product(*ranges):
            candidate = _candidate_from_lateral_values(
                shape=piece.shape,
                blocks=blocks,
                ndim=ndim,
                gravity_axis=gravity_axis,
                lateral_axes=lateral_axes,
                lateral_values=lateral_values,
                spawn_g=spawn_g,
            )
            if not state._can_exist(candidate):
                continue
            yield _drop_piece_fast(
                candidate,
                dims=dims,
                gravity_axis=gravity_axis,
                lateral_axes=lateral_axes,
                column_levels=column_levels,
            )


def _pick_greedy_4d_candidate(
    state: GameStateND,
    settled: ActivePieceND,
    *,
    dims: tuple[int, ...],
    gravity_axis: int,
    best_key_4d: tuple[int, int, int, int] | None,
    best_score: float,
    best_clears: int,
    best_piece: ActivePieceND | None,
) -> tuple[tuple[int, int, int, int] | None, float, int, ActivePieceND | None]:
    cells_after, cleared, game_over = _simulate_lock_board(state, settled)
    greedy_key = _greedy_key_4d(
        cells_after,
        dims=dims,
        gravity_axis=gravity_axis,
        cleared=cleared,
        game_over=game_over,
    )
    if best_key_4d is not None and greedy_key <= best_key_4d:
        return best_key_4d, best_score, best_clears, best_piece
    return greedy_key, _greedy_score_4d(greedy_key), cleared, settled


def _pick_heuristic_candidate(
    state: GameStateND,
    settled: ActivePieceND,
    *,
    best_score: float,
    best_clears: int,
    best_piece: ActivePieceND | None,
) -> tuple[float, int, ActivePieceND | None]:
    score, cleared = _simulate_lock_result(state, settled)
    if score > best_score or (score == best_score and cleared > best_clears):
        return score, cleared, settled
    return best_score, best_clears, best_piece


def plan_best_nd_move(state: GameStateND) -> BotPlanND | None:
    piece = state.current_piece
    if piece is None:
        return None

    t0 = time.perf_counter()
    cfg = state.config
    ndim = cfg.ndim
    gravity_axis = cfg.gravity_axis
    dims = cfg.dims
    lateral_axes = tuple(axis for axis in range(ndim) if axis != gravity_axis)

    orientations = _enumerate_orientations(
        _canonical_blocks(piece.rel_blocks),
        ndim,
        gravity_axis,
    )
    column_levels = _build_column_levels(
        state.board.cells,
        lateral_axes=lateral_axes,
        gravity_axis=gravity_axis,
    )

    use_greedy_4d = ndim >= 4
    best_key_4d: tuple[int, int, int, int] | None = None
    best_score = float("-inf")
    best_clears = 0
    best_piece: ActivePieceND | None = None
    candidate_count = 0

    for settled in _iter_settled_candidates(
        state,
        piece=piece,
        orientations=orientations,
        ndim=ndim,
        dims=dims,
        gravity_axis=gravity_axis,
        lateral_axes=lateral_axes,
        column_levels=column_levels,
    ):
        candidate_count += 1
        if use_greedy_4d:
            best_key_4d, best_score, best_clears, best_piece = _pick_greedy_4d_candidate(
                state,
                settled,
                dims=dims,
                gravity_axis=gravity_axis,
                best_key_4d=best_key_4d,
                best_score=best_score,
                best_clears=best_clears,
                best_piece=best_piece,
            )
        else:
            best_score, best_clears, best_piece = _pick_heuristic_candidate(
                state,
                settled,
                best_score=best_score,
                best_clears=best_clears,
                best_piece=best_piece,
            )

    if best_piece is None:
        return None

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return BotPlanND(
        final_piece=best_piece,
        stats=PlanStats(
            candidate_count=candidate_count,
            expected_clears=best_clears,
            heuristic_score=best_score,
            planning_ms=elapsed_ms,
        ),
    )
