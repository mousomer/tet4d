from __future__ import annotations

import random
from itertools import product
from typing import Any

from tet4d.engine.runtime.settings_schema import sanitize_text

from ..gameplay.challenge_mode import (
    apply_challenge_prefill_2d,
    apply_challenge_prefill_nd,
)
from ..gameplay.game2d import GameConfig, GameState
from ..gameplay.game_nd import GameConfigND, GameStateND
from ..gameplay.pieces2d import (
    PIECE_SET_2D_CLASSIC,
    ActivePiece2D,
    PieceShape2D,
    get_piece_bag_2d,
)
from ..core.piece_transform import block_axis_bounds, rotate_blocks_2d
from ..gameplay.pieces_nd import (
    PIECE_SET_3D_STANDARD,
    PIECE_SET_4D_STANDARD,
    ActivePieceND,
    PieceShapeND,
    get_piece_shapes_nd,
)

_MIN_VISIBLE_LAYER_DEFAULT = 2
_BOTTOM_LAYERS_MIN_DEFAULT = 1
_BOTTOM_LAYERS_MAX_DEFAULT = 2
_BOTTOM_LAYERS_HARD_MIN = 1
_BOTTOM_LAYERS_HARD_MAX = 2
_RNG_SEED_MIN = 0
_RNG_SEED_MAX = 999_999_999


def _normalize_text(raw: object, *, max_length: int = 128) -> str:
    if not isinstance(raw, str):
        return ""
    return sanitize_text(raw, max_length=max_length).strip()


def _normalize_setup_int(raw: object, *, default: int) -> int:
    if isinstance(raw, bool) or not isinstance(raw, int):
        return int(default)
    return int(raw)


def _normalize_seed(raw: object, *, default: int) -> int:
    seed = _normalize_setup_int(raw, default=default)
    return max(_RNG_SEED_MIN, min(_RNG_SEED_MAX, seed))


def _normalize_bottom_layers(setup: dict[str, Any]) -> tuple[int, int]:
    raw_min = _normalize_setup_int(
        setup.get("bottom_layers_min"),
        default=_BOTTOM_LAYERS_MIN_DEFAULT,
    )
    raw_max = _normalize_setup_int(
        setup.get("bottom_layers_max"),
        default=_BOTTOM_LAYERS_MAX_DEFAULT,
    )
    bounded_min = max(_BOTTOM_LAYERS_HARD_MIN, min(_BOTTOM_LAYERS_HARD_MAX, raw_min))
    bounded_max = max(_BOTTOM_LAYERS_HARD_MIN, min(_BOTTOM_LAYERS_HARD_MAX, raw_max))
    if bounded_max < bounded_min:
        bounded_max = bounded_min
    return bounded_min, bounded_max


def _setup_scope_tag(*, lesson_id: str, step_id: str) -> str:
    lesson = _normalize_text(lesson_id, max_length=96) or "unknown_lesson"
    step = _normalize_text(step_id, max_length=96) or "unknown_step"
    return f"{lesson}:{step}"


def _starter_piece_name(setup: dict[str, Any]) -> str:
    starter_name = _normalize_text(setup.get("starter_piece_id"))
    if starter_name:
        return starter_name
    return _normalize_text(setup.get("spawn_piece"))


def _clear_runtime_board_state(state: GameState | GameStateND) -> None:
    state.board.cells.clear()
    state.board.last_cleared_levels = []
    state.board.last_cleared_cells = []
    state.game_over = False


def _piece_is_visible_2d(state: GameState, piece: ActivePiece2D) -> bool:
    mapped = state.mapped_piece_cells_for_piece(piece, include_above=True)
    if mapped is None:
        return False
    return all(y >= 0 for _, y in mapped)


def _piece_min_gravity_2d(state: GameState, piece: ActivePiece2D) -> int:
    mapped = state.mapped_piece_cells_for_piece(piece, include_above=True)
    if not mapped:
        return -1
    return min(y for _, y in mapped)


def _piece_is_visible_nd(state: GameStateND, piece: ActivePieceND) -> bool:
    mapped = state._mapped_piece_cells(piece)
    if mapped is None:
        return False
    gravity_axis = state.config.gravity_axis
    return all(coord[gravity_axis] >= 0 for coord in mapped)


def _piece_min_gravity_nd(state: GameStateND, piece: ActivePieceND) -> int:
    mapped = state._mapped_piece_cells(piece)
    if not mapped:
        return -1
    gravity_axis = state.config.gravity_axis
    return min(coord[gravity_axis] for coord in mapped)


def _oriented_blocks_2d(
    shape: PieceShape2D,
    *,
    rotation: int,
) -> tuple[tuple[int, int], ...]:
    return rotate_blocks_2d(shape.blocks, int(rotation))


def _axis_candidate_values(
    *,
    axis_size: int,
    min_block: int,
    max_block: int,
    preferred: int,
) -> list[int]:
    minimum = -min_block
    maximum = (axis_size - 1) - max_block
    if minimum > maximum:
        return []
    candidates = list(range(minimum, maximum + 1))
    return sorted(candidates, key=lambda value: (abs(value - preferred), value))


def _one_away_from_boundary(
    *,
    min_value: int,
    max_value: int,
    prefer_min_boundary: bool,
) -> int:
    if prefer_min_boundary:
        candidate = min_value + 1
        if candidate <= max_value:
            return candidate
        return min_value
    candidate = max_value - 1
    if candidate >= min_value:
        return candidate
    return max_value


def _preferred_spawn_x_2d(
    *,
    state: GameState,
    min_block_x: int,
    max_block_x: int,
    required_move_delta: tuple[int, int] | None,
) -> int:
    span_x = max_block_x - min_block_x + 1
    default_x = ((state.config.width - span_x) // 2) - min_block_x
    if required_move_delta is None:
        return default_x
    delta_x = int(required_move_delta[0])
    min_x = -min_block_x
    max_x = (state.config.width - 1) - max_block_x
    if delta_x < 0:
        return _one_away_from_boundary(
            min_value=min_x,
            max_value=max_x,
            prefer_min_boundary=False,
        )
    if delta_x > 0:
        return _one_away_from_boundary(
            min_value=min_x,
            max_value=max_x,
            prefer_min_boundary=True,
        )
    return _one_away_from_boundary(
        min_value=min_x,
        max_value=max_x,
        prefer_min_boundary=False,
    )


def _spawn_y_candidates_2d(
    *,
    min_spawn_y: int,
    max_spawn_y: int,
    required_move_delta: tuple[int, int] | None,
    preferred_spawn_y: int | None = None,
) -> list[int]:
    if required_move_delta is None:
        if preferred_spawn_y is None:
            return list(range(min_spawn_y, max_spawn_y + 1))
        return sorted(
            range(min_spawn_y, max_spawn_y + 1),
            key=lambda value: (abs(value - preferred_spawn_y), value),
        )
    delta_y = int(required_move_delta[1])
    if delta_y < 0:
        preferred_y = max_spawn_y
    elif delta_y > 0:
        preferred_y = min_spawn_y
    else:
        preferred_y = min_spawn_y
    return sorted(
        range(min_spawn_y, max_spawn_y + 1),
        key=lambda value: (abs(value - preferred_y), value),
    )


def _candidate_piece_placeable_2d(
    *,
    state: GameState,
    candidate: ActivePiece2D,
    min_visible_layer: int,
    required_move_delta: tuple[int, int] | None,
    required_move_repetitions: int,
) -> bool:
    if not _piece_is_visible_2d(state, candidate):
        return False
    if _piece_min_gravity_2d(state, candidate) < min_visible_layer:
        return False
    if not state._can_exist(candidate):
        return False
    if required_move_delta is None:
        return True
    probe = candidate
    repeats = max(1, int(required_move_repetitions))
    delta_x = int(required_move_delta[0])
    delta_y = int(required_move_delta[1])
    for _ in range(repeats):
        probe = probe.moved(delta_x, delta_y)
        if not state._can_exist(probe):
            return False
    return True


def _force_piece_placement_2d(
    *,
    state: GameState,
    shape: PieceShape2D,
    rotation: int,
    min_visible_layer: int,
    scope_tag: str,
    required_move_delta: tuple[int, int] | None = None,
    required_move_repetitions: int = 1,
    preferred_min_gravity: int | None = None,
) -> None:
    oriented_blocks = _oriented_blocks_2d(shape, rotation=rotation)
    mins, maxs = block_axis_bounds(oriented_blocks)
    min_block_x = mins[0]
    max_block_x = maxs[0]
    min_block_y = mins[1]
    max_block_y = maxs[1]
    target_x = _preferred_spawn_x_2d(
        state=state,
        min_block_x=min_block_x,
        max_block_x=max_block_x,
        required_move_delta=required_move_delta,
    )
    x_candidates = _axis_candidate_values(
        axis_size=state.config.width,
        min_block=min_block_x,
        max_block=max_block_x,
        preferred=target_x,
    )
    min_spawn_y = max(min_visible_layer - min_block_y, -min_block_y)
    max_spawn_y = (state.config.height - 1) - max_block_y
    if min_spawn_y > max_spawn_y:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): min visible layer cannot fit 2D starter piece"
        )
    y_candidates = _spawn_y_candidates_2d(
        min_spawn_y=min_spawn_y,
        max_spawn_y=max_spawn_y,
        required_move_delta=required_move_delta,
        preferred_spawn_y=(
            int(preferred_min_gravity) - min_block_y
            if preferred_min_gravity is not None
            else None
        ),
    )
    for y in y_candidates:
        for x in x_candidates:
            candidate = ActivePiece2D(shape, (x, y), rotation=rotation)
            if _candidate_piece_placeable_2d(
                state=state,
                candidate=candidate,
                min_visible_layer=min_visible_layer,
                required_move_delta=required_move_delta,
                required_move_repetitions=required_move_repetitions,
            ):
                state.current_piece = candidate
                return
    raise RuntimeError(
        f"tutorial setup failed ({scope_tag}): could not place 2D starter piece without collision"
    )


def _preferred_lateral_axis_spawn_nd(
    *,
    axis: int,
    dims: tuple[int, ...],
    mins: list[int],
    maxs: list[int],
    initial_pos: list[int],
    required_move_delta: tuple[int, ...] | None,
) -> int:
    preferred = initial_pos[axis]
    if required_move_delta is None or axis >= len(required_move_delta):
        return preferred
    delta_axis = int(required_move_delta[axis])
    min_axis = -mins[axis]
    max_axis = (dims[axis] - 1) - maxs[axis]
    if delta_axis < 0:
        return _one_away_from_boundary(
            min_value=min_axis,
            max_value=max_axis,
            prefer_min_boundary=False,
        )
    if delta_axis > 0:
        return _one_away_from_boundary(
            min_value=min_axis,
            max_value=max_axis,
            prefer_min_boundary=True,
        )
    return _one_away_from_boundary(
        min_value=min_axis,
        max_value=max_axis,
        prefer_min_boundary=False,
    )


def _lateral_spawn_candidates_nd(
    *,
    dims: tuple[int, ...],
    mins: list[int],
    maxs: list[int],
    initial_pos: list[int],
    gravity_axis: int,
    required_move_delta: tuple[int, ...] | None,
    scope_tag: str,
) -> tuple[list[int], list[list[int]]]:
    lateral_axes = [axis for axis in range(len(dims)) if axis != gravity_axis]
    lateral_candidates: list[list[int]] = []
    for axis in lateral_axes:
        preferred = _preferred_lateral_axis_spawn_nd(
            axis=axis,
            dims=dims,
            mins=mins,
            maxs=maxs,
            initial_pos=initial_pos,
            required_move_delta=required_move_delta,
        )
        candidates = _axis_candidate_values(
            axis_size=dims[axis],
            min_block=mins[axis],
            max_block=maxs[axis],
            preferred=preferred,
        )
        if not candidates:
            raise RuntimeError(
                f"tutorial setup failed ({scope_tag}): no legal ND spawn positions for starter piece"
            )
        lateral_candidates.append(candidates)
    return lateral_axes, lateral_candidates


def _force_piece_placement_nd(
    *,
    state: GameStateND,
    shape: PieceShapeND,
    rel_blocks: tuple[tuple[int, ...], ...] | None,
    min_visible_layer: int,
    scope_tag: str,
    required_move_delta: tuple[int, ...] | None = None,
    required_move_repetitions: int = 1,
    preferred_min_gravity: int | None = None,
) -> None:
    dims = state.config.dims
    gravity_axis = state.config.gravity_axis
    blocks = tuple(rel_blocks) if rel_blocks is not None else shape.blocks
    mins_raw, maxs_raw = block_axis_bounds(blocks)
    mins = [int(value) for value in mins_raw]
    maxs = [int(value) for value in maxs_raw]
    initial_pos = list(state._spawn_pos_for_shape(shape))
    min_spawn_g = max(min_visible_layer - mins[gravity_axis], -mins[gravity_axis])
    max_spawn_g = (dims[gravity_axis] - 1) - maxs[gravity_axis]
    if min_spawn_g > max_spawn_g:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): min visible layer cannot fit ND starter piece"
        )
    lateral_axes, lateral_candidates = _lateral_spawn_candidates_nd(
        dims=dims,
        mins=mins,
        maxs=maxs,
        initial_pos=initial_pos,
        gravity_axis=gravity_axis,
        required_move_delta=required_move_delta,
        scope_tag=scope_tag,
    )
    gravity_values = _gravity_candidate_values(
        min_spawn=min_spawn_g,
        max_spawn=max_spawn_g,
        preferred_spawn=(
            int(preferred_min_gravity) - mins[gravity_axis]
            if preferred_min_gravity is not None
            else None
        ),
    )
    for gravity_value in gravity_values:
        for lateral_values in product(*lateral_candidates):
            candidate_pos = list(initial_pos)
            candidate_pos[gravity_axis] = gravity_value
            for axis_index, axis in enumerate(lateral_axes):
                candidate_pos[axis] = lateral_values[axis_index]
            candidate = ActivePieceND(
                shape=shape,
                pos=tuple(candidate_pos),
                rel_blocks=tuple(blocks),
            )
            if _candidate_piece_placeable_nd(
                state=state,
                candidate=candidate,
                min_visible_layer=min_visible_layer,
                required_move_delta=required_move_delta,
                required_move_repetitions=required_move_repetitions,
            ):
                state.current_piece = candidate
                return
    raise RuntimeError(
        f"tutorial setup failed ({scope_tag}): could not place ND starter piece without collision"
    )


def _gravity_candidate_values(
    *,
    min_spawn: int,
    max_spawn: int,
    preferred_spawn: int | None,
) -> list[int]:
    values = list(range(min_spawn, max_spawn + 1))
    if preferred_spawn is None:
        return values
    return sorted(values, key=lambda value: (abs(value - preferred_spawn), value))


def _goal_spawn_distance_layers_for_step(*, step_id: str, ndim: int) -> int | None:
    if ndim == 2 and step_id in {"line_fill", "full_clear_bonus"}:
        return 3
    if ndim == 3 and step_id in {"layer_fill", "full_clear_bonus"}:
        return 3
    if ndim == 4 and step_id in {"hyper_layer_fill", "full_clear_bonus"}:
        return 3
    return None


def _goal_step_requires_lateral_offset(*, step_id: str, ndim: int) -> bool:
    if ndim == 2:
        return step_id in {"line_fill", "full_clear_bonus"}
    if ndim == 3:
        return step_id in {"layer_fill", "full_clear_bonus"}
    if ndim >= 4:
        return step_id in {"hyper_layer_fill", "full_clear_bonus"}
    return False


def _goal_target_level_2d(state: GameState) -> int | None:
    if not state.board.cells:
        return None
    return min(int(coord[1]) for coord in state.board.cells)


def _goal_target_level_nd(state: GameStateND, *, gravity_axis: int) -> int | None:
    if not state.board.cells:
        return None
    return min(int(coord[gravity_axis]) for coord in state.board.cells)


def _preferred_goal_min_gravity(
    *,
    target_level: int | None,
    min_visible_layer: int,
    distance_layers: int | None,
) -> int | None:
    if target_level is None or distance_layers is None:
        return None
    return max(int(min_visible_layer), int(target_level) - int(distance_layers))


def _nudge_goal_piece_away_from_holes_2d(*, state: GameState) -> None:
    piece = state.current_piece
    if piece is None:
        return
    target_level = _goal_target_level_2d(state)
    if target_level is None:
        return
    empty_x = [
        x
        for x in range(state.config.width)
        if (x, int(target_level)) not in state.board.cells
    ]
    if not empty_x:
        return
    hole_center = float(sum(empty_x)) / float(len(empty_x))
    mapped = state.mapped_piece_cells_for_piece(piece, include_above=True)
    if not mapped:
        return
    current_center = float(sum(coord[0] for coord in mapped)) / float(len(mapped))
    current_distance = abs(current_center - hole_center)
    best_piece = piece
    best_distance = current_distance
    max_shift = max(1, min(3, int(state.config.width) - 1))
    for dx in range(-max_shift, max_shift + 1):
        if dx == 0:
            continue
        candidate = piece.moved(int(dx), 0)
        if not state._can_exist(candidate):
            continue
        candidate_cells = state.mapped_piece_cells_for_piece(candidate, include_above=True)
        if not candidate_cells:
            continue
        candidate_center = float(sum(coord[0] for coord in candidate_cells)) / float(
            len(candidate_cells)
        )
        candidate_distance = abs(candidate_center - hole_center)
        if candidate_distance > best_distance:
            best_piece = candidate
            best_distance = candidate_distance
    state.current_piece = best_piece


def _nudge_goal_piece_away_from_holes_nd(*, state: GameStateND) -> None:
    piece = state.current_piece
    if piece is None:
        return
    gravity_axis = int(state.config.gravity_axis)
    target_level = _goal_target_level_nd(state, gravity_axis=gravity_axis)
    if target_level is None:
        return
    lateral_axes = _lateral_axes_nd(state=state, gravity_axis=gravity_axis)
    if not lateral_axes:
        return
    primary_axis = int(lateral_axes[0])
    empty_primary_axis_values = _empty_primary_axis_values_for_goal_nd(
        state=state,
        target_level=int(target_level),
        gravity_axis=gravity_axis,
        lateral_axes=lateral_axes,
        primary_axis=primary_axis,
    )
    if not empty_primary_axis_values:
        return
    hole_center = float(sum(empty_primary_axis_values)) / float(
        len(empty_primary_axis_values)
    )
    current_center = _piece_center_axis_nd(state=state, piece=piece, axis=primary_axis)
    if current_center is None:
        return
    direction = 1 if current_center <= hole_center else -1
    state.current_piece = _best_nudged_piece_nd(
        state=state,
        piece=piece,
        primary_axis=primary_axis,
        direction=direction,
        hole_center=hole_center,
    )


def _lateral_axes_nd(*, state: GameStateND, gravity_axis: int) -> list[int]:
    return [axis for axis in range(state.config.ndim) if axis != gravity_axis]


def _empty_primary_axis_values_for_goal_nd(
    *,
    state: GameStateND,
    target_level: int,
    gravity_axis: int,
    lateral_axes: list[int],
    primary_axis: int,
) -> list[int]:
    empty_primary_axis_values: list[int] = []
    axis_ranges = [range(state.config.dims[axis]) for axis in lateral_axes]
    for lateral_values in product(*axis_ranges):
        coord = [0] * state.config.ndim
        coord[gravity_axis] = int(target_level)
        for idx, axis in enumerate(lateral_axes):
            coord[axis] = int(lateral_values[idx])
        if tuple(coord) not in state.board.cells:
            empty_primary_axis_values.append(coord[primary_axis])
    return empty_primary_axis_values


def _piece_center_axis_nd(
    *,
    state: GameStateND,
    piece: ActivePieceND,
    axis: int,
) -> float | None:
    mapped = state._mapped_piece_cells(piece)
    if not mapped:
        return None
    return float(sum(coord[axis] for coord in mapped)) / float(len(mapped))


def _best_nudged_piece_nd(
    *,
    state: GameStateND,
    piece: ActivePieceND,
    primary_axis: int,
    direction: int,
    hole_center: float,
) -> ActivePieceND:
    current_center = _piece_center_axis_nd(state=state, piece=piece, axis=primary_axis)
    if current_center is None:
        return piece
    best_piece = piece
    best_distance = abs(current_center - hole_center)
    max_shift = max(1, min(3, int(state.config.dims[primary_axis]) - 1))
    for step in range(1, max_shift + 1):
        delta = [0] * state.config.ndim
        delta[primary_axis] = int(direction) * int(step)
        candidate = piece.moved(tuple(delta))
        if not state._can_exist(candidate):
            continue
        candidate_center = _piece_center_axis_nd(
            state=state,
            piece=candidate,
            axis=primary_axis,
        )
        if candidate_center is None:
            continue
        candidate_distance = abs(candidate_center - hole_center)
        if candidate_distance > best_distance:
            best_piece = candidate
            best_distance = candidate_distance
    return best_piece


def _candidate_piece_placeable_nd(
    *,
    state: GameStateND,
    candidate: ActivePieceND,
    min_visible_layer: int,
    required_move_delta: tuple[int, ...] | None,
    required_move_repetitions: int,
) -> bool:
    if not _piece_is_visible_nd(state, candidate):
        return False
    if _piece_min_gravity_nd(state, candidate) < min_visible_layer:
        return False
    if not state._can_exist(candidate):
        return False
    if required_move_delta is None:
        return True
    probe = candidate
    repeats = max(1, int(required_move_repetitions))
    for _ in range(repeats):
        probe = probe.moved(required_move_delta)
        if not state._can_exist(probe):
            return False
    return True


def _candidate_supports_repeated_move_nd(
    *,
    state: GameStateND,
    candidate: ActivePieceND,
    delta: tuple[int, ...],
    repeats: int,
) -> bool:
    probe = candidate
    for _ in range(max(1, int(repeats))):
        probe = probe.moved(delta)
        if not state._can_exist(probe):
            return False
    return True


def _target_axis_score_nd(
    *,
    state: GameStateND,
    candidate: ActivePieceND,
    axis: int,
    delta: int,
) -> int:
    mapped = state._mapped_piece_cells(candidate)
    if not mapped:
        return 1_000_000
    if int(delta) > 0:
        target_min = 1
        actual_min = min(int(coord[axis]) for coord in mapped)
        return abs(actual_min - target_min)
    target_max = int(state.config.dims[axis]) - 2
    actual_max = max(int(coord[axis]) for coord in mapped)
    return abs(actual_max - target_max)


def _opening_translation_move_requirements_nd(*, ndim: int) -> tuple[tuple[int, ...], ...]:
    requirements: list[tuple[int, ...]] = []
    def _delta(values: tuple[int, ...]) -> tuple[int, ...]:
        if len(values) == ndim:
            return tuple(int(value) for value in values)
        padded = [0] * int(ndim)
        for index, value in enumerate(values):
            if index >= ndim:
                break
            padded[index] = int(value)
        return tuple(padded)
    if ndim >= 3:
        requirements.extend((_delta((-1, 0, 0)), _delta((0, 0, 1))))
    if ndim >= 4:
        requirements.append(_delta((0, 0, 0, -1)))
    return tuple(requirements)


def _opening_translation_pos_ranges_nd(
    *,
    state: GameStateND,
    piece: ActivePieceND,
    min_visible_layer: int,
    scope_tag: str,
) -> list[range]:
    ndim = int(state.config.ndim)
    gravity_axis = int(state.config.gravity_axis)
    rel_blocks = tuple(piece.rel_blocks)
    mins_raw, maxs_raw = block_axis_bounds(rel_blocks)
    mins = [int(value) for value in mins_raw]
    maxs = [int(value) for value in maxs_raw]
    pos_ranges: list[range] = []
    for axis in range(ndim):
        min_pos = -int(mins[axis])
        if axis == gravity_axis:
            min_pos = max(min_pos, int(min_visible_layer) - int(mins[axis]))
        max_pos = int(state.config.dims[axis]) - 1 - int(maxs[axis])
        if min_pos > max_pos:
            raise RuntimeError(
                f"tutorial setup failed ({scope_tag}): cannot reposition opening ND piece for axis {axis}"
            )
        pos_ranges.append(range(min_pos, max_pos + 1))
    return pos_ranges


def _opening_translation_candidate_positions_nd(
    *,
    pos_ranges: list[range],
    gravity_axis: int,
    current_pos: tuple[int, ...],
) -> list[tuple[int, ...]]:
    ndim = len(pos_ranges)
    gravity_values = (
        [current_pos[gravity_axis]]
        if current_pos[gravity_axis] in pos_ranges[gravity_axis]
        else list(pos_ranges[gravity_axis])
    )
    lateral_axes = [axis for axis in range(ndim) if axis != gravity_axis]
    lateral_ranges = [pos_ranges[axis] for axis in lateral_axes]
    positions: list[tuple[int, ...]] = []
    for gravity_value in gravity_values:
        for lateral_values in product(*lateral_ranges):
            candidate_pos = [0] * ndim
            candidate_pos[gravity_axis] = int(gravity_value)
            for index, axis in enumerate(lateral_axes):
                candidate_pos[axis] = int(lateral_values[index])
            positions.append(tuple(candidate_pos))
    return positions


def _opening_translation_candidate_valid_nd(
    *,
    state: GameStateND,
    candidate: ActivePieceND,
    min_visible_layer: int,
    requirements: tuple[tuple[int, ...], ...],
    required_move_repetitions: int,
) -> bool:
    if not _piece_is_visible_nd(state, candidate):
        return False
    if _piece_min_gravity_nd(state, candidate) < int(min_visible_layer):
        return False
    if not state._can_exist(candidate):
        return False
    return all(
        _candidate_supports_repeated_move_nd(
            state=state,
            candidate=candidate,
            delta=delta,
            repeats=required_move_repetitions,
        )
        for delta in requirements
    )


def _opening_translation_candidate_score_nd(
    *,
    state: GameStateND,
    candidate: ActivePieceND,
    current_pos: tuple[int, ...],
) -> tuple[int, ...]:
    ndim = int(state.config.ndim)
    gravity_axis = int(state.config.gravity_axis)
    lateral_axes = [axis for axis in range(ndim) if axis != gravity_axis]
    return (
        _target_axis_score_nd(state=state, candidate=candidate, axis=0, delta=-1),
        _target_axis_score_nd(state=state, candidate=candidate, axis=2, delta=1),
        _target_axis_score_nd(
            state=state,
            candidate=candidate,
            axis=3,
            delta=-1,
        )
        if ndim >= 4
        else 0,
        sum(abs(int(candidate.pos[axis]) - int(current_pos[axis])) for axis in lateral_axes),
    )


def _reposition_opening_translation_piece_nd(
    *,
    state: GameStateND,
    min_visible_layer: int,
    required_move_repetitions: int,
    scope_tag: str,
) -> None:
    piece = state.current_piece
    if piece is None:
        return
    ndim = int(state.config.ndim)
    gravity_axis = int(state.config.gravity_axis)
    rel_blocks = tuple(piece.rel_blocks)
    requirements = _opening_translation_move_requirements_nd(ndim=ndim)
    pos_ranges = _opening_translation_pos_ranges_nd(
        state=state,
        piece=piece,
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
    )
    current_pos = tuple(int(value) for value in piece.pos)

    best_piece: ActivePieceND | None = None
    best_score: tuple[int, ...] | None = None
    for candidate_pos in _opening_translation_candidate_positions_nd(
        pos_ranges=pos_ranges,
        gravity_axis=gravity_axis,
        current_pos=current_pos,
    ):
        candidate = ActivePieceND(
            shape=piece.shape,
            pos=candidate_pos,
            rel_blocks=rel_blocks,
        )
        if not _opening_translation_candidate_valid_nd(
            state=state,
            candidate=candidate,
            min_visible_layer=min_visible_layer,
            requirements=requirements,
            required_move_repetitions=required_move_repetitions,
        ):
            continue
        score = _opening_translation_candidate_score_nd(
            state=state,
            candidate=candidate,
            current_pos=current_pos,
        )
        if best_score is None or score < best_score:
            best_score = score
            best_piece = candidate
    if best_piece is None:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): opening ND translation spawn is not feasible"
        )
    state.current_piece = best_piece


def _set_seeded_runtime_rng(
    state: GameState | GameStateND,
    *,
    seed: int,
) -> random.Random:
    seeded_rng = random.Random(seed)
    state.rng = seeded_rng
    return seeded_rng


def _remove_first_shape_by_name(shapes: list[Any], shape_name: str) -> None:
    for index, shape in enumerate(shapes):
        if getattr(shape, "name", "") == shape_name:
            shapes.pop(index)
            return


def _pick_bottom_layers(
    *,
    setup_rng: random.Random,
    layer_min: int,
    layer_max: int,
) -> int:
    if layer_max <= layer_min:
        return int(layer_min)
    return int(setup_rng.randint(layer_min, layer_max))


def _board_preset_name(setup: dict[str, Any]) -> str:
    return _normalize_text(setup.get("board_preset"), max_length=96).lower()


def _apply_board_preset_2d(
    *,
    state: GameState,
    cfg: GameConfig,
    preset: str,
    setup_rng: random.Random,
    scope_tag: str,
) -> None:
    handlers = {
        "2d_almost_line": _apply_board_preset_2d_almost_line,
        "2d_almost_line_i": _apply_board_preset_2d_almost_line_i,
        "2d_almost_full_clear_o": _apply_board_preset_2d_almost_full_clear_o,
    }
    handler = handlers.get(preset)
    if handler is None:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): unknown 2D board preset '{preset}'"
        )
    handler(state=state, cfg=cfg, setup_rng=setup_rng, scope_tag=scope_tag)


def _apply_board_preset_2d_almost_line(
    *,
    state: GameState,
    cfg: GameConfig,
    setup_rng: random.Random,
    scope_tag: str,
) -> None:
    _ = scope_tag
    target_y = cfg.height - 1
    gap_x = int(setup_rng.randrange(max(1, cfg.width)))
    for x in range(cfg.width):
        if x == gap_x:
            continue
        state.board.cells[(x, target_y)] = (x % 7) + 1


def _apply_board_preset_2d_almost_line_i(
    *,
    state: GameState,
    cfg: GameConfig,
    setup_rng: random.Random,
    scope_tag: str,
) -> None:
    _ = setup_rng
    if cfg.width < 4:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 2D line-I preset requires board width >= 4"
        )
    target_y = cfg.height - 1
    base_x = max(0, min(cfg.width - 4, (cfg.width // 2) - 2))
    gap_cells = {base_x, base_x + 1, base_x + 2, base_x + 3}
    for x in range(cfg.width):
        if x in gap_cells:
            continue
        state.board.cells[(x, target_y)] = (x % 7) + 1


def _apply_board_preset_2d_almost_full_clear_o(
    *,
    state: GameState,
    cfg: GameConfig,
    setup_rng: random.Random,
    scope_tag: str,
) -> None:
    _ = setup_rng
    if cfg.width < 2 or cfg.height < 2:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 2D full-clear preset requires board >= 2x2"
        )
    target_top = cfg.height - 2
    target_bottom = cfg.height - 1
    base_x = max(0, min(cfg.width - 2, (cfg.width // 2) - 1))
    holes = {
        (base_x, target_top),
        (base_x + 1, target_top),
        (base_x, target_bottom),
        (base_x + 1, target_bottom),
    }
    for y in (target_top, target_bottom):
        for x in range(cfg.width):
            if (x, y) in holes:
                continue
            state.board.cells[(x, y)] = ((x + y) % 7) + 1


def _apply_board_preset_3d_full_clear_o3(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    scope_tag: str,
) -> None:
    if cfg.gravity_axis != 1:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 3D full-clear preset requires gravity axis 1"
        )
    dim_x, dim_y, dim_z = cfg.dims
    if dim_x < 2 or dim_y < 2 or dim_z < 1:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 3D full-clear preset requires dims >= (2,2,1)"
        )
    target_low = dim_y - 2
    target_high = dim_y - 1
    base_x = max(0, min(dim_x - 2, (dim_x // 2) - 1))
    base_z = max(0, min(dim_z - 1, dim_z // 2))
    holes = {
        (base_x, target_low, base_z),
        (base_x + 1, target_low, base_z),
        (base_x, target_high, base_z),
        (base_x + 1, target_high, base_z),
    }
    for y in (target_low, target_high):
        for x in range(dim_x):
            for z in range(dim_z):
                coord = (x, y, z)
                if coord in holes:
                    continue
                state.board.cells[coord] = ((x + y + z) % 7) + 1


def _apply_board_preset_4d_full_clear_cross4(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    scope_tag: str,
) -> None:
    if cfg.gravity_axis != 1:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 4D full-clear preset requires gravity axis 1"
        )
    dim_x, dim_y, dim_z, dim_w = cfg.dims
    if dim_x < 2 or dim_y < 2 or dim_z < 2 or dim_w < 2:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 4D full-clear preset requires dims >= (2,2,2,2)"
        )
    target_low = dim_y - 2
    target_high = dim_y - 1
    base_x = max(0, min(dim_x - 2, (dim_x // 2) - 1))
    base_z = max(0, min(dim_z - 2, (dim_z // 2) - 1))
    base_w = max(0, min(dim_w - 2, (dim_w // 2) - 1))
    holes = {
        (base_x, target_low, base_z, base_w),
        (base_x + 1, target_low, base_z, base_w),
        (base_x, target_low, base_z + 1, base_w),
        (base_x, target_low, base_z, base_w + 1),
        (base_x, target_high, base_z, base_w),
    }
    for y in (target_low, target_high):
        for x in range(dim_x):
            for z in range(dim_z):
                for w in range(dim_w):
                    coord = (x, y, z, w)
                    if coord in holes:
                        continue
                    state.board.cells[coord] = ((x + y + z + w) % 7) + 1


def _apply_board_preset_nd(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    preset: str,
    setup_rng: random.Random,
    scope_tag: str,
) -> None:
    if preset == "3d_almost_layer_screw3":
        _apply_board_preset_3d_layer_screw3(state=state, cfg=cfg, scope_tag=scope_tag)
        return
    if preset == "4d_almost_hyper_layer_skew4":
        _apply_board_preset_4d_layer_skew4(state=state, cfg=cfg, scope_tag=scope_tag)
        return
    if preset in {"3d_almost_layer", "4d_almost_hyper_layer"}:
        _apply_board_preset_nd_single_gap(
            state=state,
            cfg=cfg,
            setup_rng=setup_rng,
        )
        return
    if preset == "3d_almost_full_clear_o3":
        _apply_board_preset_3d_full_clear_o3(
            state=state,
            cfg=cfg,
            scope_tag=scope_tag,
        )
        return
    if preset == "4d_almost_full_clear_cross4":
        _apply_board_preset_4d_full_clear_cross4(
            state=state,
            cfg=cfg,
            scope_tag=scope_tag,
        )
        return
    raise RuntimeError(
        f"tutorial setup failed ({scope_tag}): unknown ND board preset '{preset}'"
    )


def _apply_board_preset_nd_single_gap(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    setup_rng: random.Random,
) -> None:
    gravity_axis = cfg.gravity_axis
    target_level = cfg.dims[gravity_axis] - 1
    lateral_axes = [axis for axis in range(cfg.ndim) if axis != gravity_axis]
    gap_coords = [
        int(setup_rng.randrange(max(1, cfg.dims[axis])))
        for axis in lateral_axes
    ]
    lateral_ranges = [range(cfg.dims[axis]) for axis in lateral_axes]
    for lateral_values in product(*lateral_ranges):
        if list(lateral_values) == gap_coords:
            continue
        coord = [0] * cfg.ndim
        coord[gravity_axis] = target_level
        for index, axis in enumerate(lateral_axes):
            coord[axis] = int(lateral_values[index])
        state.board.cells[tuple(coord)] = (sum(coord) % 7) + 1


def _apply_board_preset_3d_layer_screw3(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    scope_tag: str,
) -> None:
    if cfg.ndim != 3 or cfg.gravity_axis != 1:
        raise RuntimeError(
            "tutorial setup failed "
            f"({scope_tag}): 3D screw-layer preset requires ndim=3 and gravity axis 1"
        )
    dim_x, dim_y, dim_z = cfg.dims
    if dim_x < 2 or dim_y < 2 or dim_z < 2:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): 3D screw-layer preset requires dims >= (2,2,2)"
        )
    target_level = dim_y - 1
    base_x = max(0, min(dim_x - 2, (dim_x // 2) - 1))
    base_z = max(0, min(dim_z - 2, (dim_z // 2) - 1))
    holes = {
        (base_x + 1, target_level, base_z),
        (base_x + 1, target_level, base_z + 1),
    }
    for x in range(dim_x):
        for z in range(dim_z):
            coord = (x, target_level, z)
            if coord in holes:
                continue
            state.board.cells[coord] = (sum(coord) % 7) + 1


def _apply_board_preset_4d_layer_skew4(
    *,
    state: GameStateND,
    cfg: GameConfigND,
    scope_tag: str,
) -> None:
    if cfg.ndim != 4 or cfg.gravity_axis != 1:
        raise RuntimeError(
            "tutorial setup failed "
            f"({scope_tag}): 4D skew-layer preset requires ndim=4 and gravity axis 1"
        )
    dim_x, dim_y, dim_z, dim_w = cfg.dims
    if dim_x < 2 or dim_y < 2 or dim_z < 2 or dim_w < 2:
        raise RuntimeError(
            "tutorial setup failed "
            f"({scope_tag}): 4D skew-layer preset requires dims >= (2,2,2,2)"
        )
    target_level = dim_y - 1
    base_x = max(1, min(dim_x - 1, dim_x // 2))
    base_z = max(0, min(dim_z - 2, (dim_z // 2) - 1))
    base_w = max(0, min(dim_w - 2, (dim_w // 2) - 1))
    holes = {
        (base_x, target_level, base_z, base_w),
        (base_x, target_level, base_z + 1, base_w),
        (base_x, target_level, base_z + 1, base_w + 1),
    }
    for x in range(dim_x):
        for z in range(dim_z):
            for w in range(dim_w):
                coord = (x, target_level, z, w)
                if coord in holes:
                    continue
                state.board.cells[coord] = (sum(coord) % 7) + 1


def _ensure_current_piece_visible_2d(
    *,
    state: GameState,
    min_visible_layer: int,
    scope_tag: str,
) -> None:
    if state.current_piece is None:
        state.spawn_new_piece()
    piece = state.current_piece
    if piece is None:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): missing active 2D piece"
        )
    if (
        _piece_is_visible_2d(state, piece)
        and _piece_min_gravity_2d(state, piece) >= min_visible_layer
        and state._can_exist(piece)
    ):
        return
    required_drop = max(0, min_visible_layer - _piece_min_gravity_2d(state, piece))
    if required_drop > 0:
        candidate = piece.moved(0, required_drop)
        if (
            _piece_is_visible_2d(state, candidate)
            and _piece_min_gravity_2d(state, candidate) >= min_visible_layer
            and state._can_exist(candidate)
        ):
            state.current_piece = candidate
            return
    _force_piece_placement_2d(
        state=state,
        shape=piece.shape,
        rotation=int(piece.rotation),
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
    )


def _ensure_current_piece_visible_nd(
    *,
    state: GameStateND,
    min_visible_layer: int,
    scope_tag: str,
) -> None:
    if state.current_piece is None:
        state.spawn_new_piece()
    piece = state.current_piece
    if piece is None:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): missing active ND piece"
        )
    if (
        _piece_is_visible_nd(state, piece)
        and _piece_min_gravity_nd(state, piece) >= min_visible_layer
        and state._can_exist(piece)
    ):
        return
    required_drop = max(0, min_visible_layer - _piece_min_gravity_nd(state, piece))
    if required_drop > 0:
        delta = [0] * state.config.ndim
        delta[state.config.gravity_axis] = required_drop
        candidate = piece.moved(tuple(delta))
        if (
            _piece_is_visible_nd(state, candidate)
            and _piece_min_gravity_nd(state, candidate) >= min_visible_layer
            and state._can_exist(candidate)
        ):
            state.current_piece = candidate
            return
    _force_piece_placement_nd(
        state=state,
        shape=piece.shape,
        rel_blocks=piece.rel_blocks,
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
    )


def _find_starter_shape_2d(
    *,
    starter_piece: str,
    cfg: GameConfig,
    setup_rng: random.Random,
) -> tuple[PieceShape2D | None, str]:
    current_shapes = get_piece_bag_2d(
        cfg.piece_set,
        rng=setup_rng,
        random_cell_count=cfg.random_cell_count,
        board_dims=(cfg.width, cfg.height),
    )
    selected_shape = next(
        (shape for shape in current_shapes if shape.name == starter_piece),
        None,
    )
    if selected_shape is not None:
        return selected_shape, cfg.piece_set
    fallback_shapes = get_piece_bag_2d(
        PIECE_SET_2D_CLASSIC,
        rng=setup_rng,
        random_cell_count=cfg.random_cell_count,
        board_dims=(cfg.width, cfg.height),
    )
    fallback_shape = next(
        (shape for shape in fallback_shapes if shape.name == starter_piece),
        None,
    )
    if fallback_shape is None:
        return None, cfg.piece_set
    return fallback_shape, PIECE_SET_2D_CLASSIC


def _find_starter_shape_nd(
    *,
    starter_piece: str,
    cfg: GameConfigND,
    setup_rng: random.Random,
) -> tuple[PieceShapeND | None, str]:
    current_shapes = get_piece_shapes_nd(
        cfg.ndim,
        piece_set_id=cfg.piece_set_id,
        random_cell_count=cfg.random_cell_count,
        rng=setup_rng,
        board_dims=cfg.dims,
    )
    selected_shape = next(
        (shape for shape in current_shapes if shape.name == starter_piece),
        None,
    )
    if selected_shape is not None:
        return selected_shape, str(cfg.piece_set_id)
    fallback_piece_set = PIECE_SET_3D_STANDARD if cfg.ndim == 3 else PIECE_SET_4D_STANDARD
    fallback_shapes = get_piece_shapes_nd(
        cfg.ndim,
        piece_set_id=fallback_piece_set,
        random_cell_count=cfg.random_cell_count,
        rng=setup_rng,
        board_dims=cfg.dims,
    )
    fallback_shape = next(
        (shape for shape in fallback_shapes if shape.name == starter_piece),
        None,
    )
    if fallback_shape is None:
        return None, str(cfg.piece_set_id)
    return fallback_shape, fallback_piece_set


def _required_move_delta_for_step(
    *,
    step_id: str,
    ndim: int,
) -> tuple[int, ...] | None:
    # Align with default viewer-relative routing used in ND gameplay loops:
    # move_z_neg means "away" (positive z at default yaw), move_z_pos means
    # "closer" (negative z at default yaw).
    deltas = {
        "move_x_neg": (-1, 0, 0, 0),
        "move_x_pos": (1, 0, 0, 0),
        "move_z_neg": (0, 0, 1, 0),
        "move_z_pos": (0, 0, -1, 0),
        "move_w_neg": (0, 0, 0, -1),
        "move_w_pos": (0, 0, 0, 1),
    }
    delta_4d = deltas.get(step_id)
    if delta_4d is None:
        return None
    if ndim == 2:
        return tuple(delta_4d[:2])
    if ndim == 3:
        return tuple(delta_4d[:3])
    if ndim >= 4:
        return tuple(delta_4d[:4])
    return None


def apply_tutorial_step_setup_2d(
    state: GameState,
    cfg: GameConfig,
    setup: dict[str, Any],
    *,
    lesson_id: str,
    step_id: str,
) -> None:
    scope_tag = _setup_scope_tag(lesson_id=lesson_id, step_id=step_id)
    board_preset = _board_preset_name(setup)
    min_visible_layer = max(
        0,
        _normalize_setup_int(
            setup.get("spawn_min_visible_layer"),
            default=_MIN_VISIBLE_LAYER_DEFAULT,
        ),
    )
    starter_piece = _starter_piece_name(setup)
    board_mutation_requested = bool(
        starter_piece
        or board_preset
        or setup.get("spawn_min_visible_layer") is not None
        or setup.get("bottom_layers_min") is not None
        or setup.get("bottom_layers_max") is not None
    )
    if not board_mutation_requested:
        _ensure_current_piece_visible_2d(
            state=state,
            min_visible_layer=min_visible_layer,
            scope_tag=scope_tag,
        )
        return
    if not starter_piece:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): starter_piece_id is required"
        )
    seed = _normalize_seed(setup.get("rng_seed"), default=int(cfg.rng_seed))
    setup_rng = _set_seeded_runtime_rng(state, seed=seed)
    layers_min, layers_max = _normalize_bottom_layers(setup)
    _clear_runtime_board_state(state)

    if board_preset:
        _apply_board_preset_2d(
            state=state,
            cfg=cfg,
            preset=board_preset,
            setup_rng=setup_rng,
            scope_tag=scope_tag,
        )
    elif not cfg.exploration_mode:
        layer_count = _pick_bottom_layers(
            setup_rng=setup_rng,
            layer_min=layers_min,
            layer_max=layers_max,
        )
        apply_challenge_prefill_2d(
            state,
            layers=layer_count,
            fill_ratio=1.0,
        )

    selected_shape = _find_starter_shape_2d(
        starter_piece=starter_piece,
        cfg=cfg,
        setup_rng=setup_rng,
    )[0]
    if selected_shape is None:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): starter piece "
            f"'{starter_piece}' not found in 2D piece set '{cfg.piece_set}' "
            f"or fallback '{PIECE_SET_2D_CLASSIC}'"
        )

    state.next_bag = []
    state._refill_bag()
    _remove_first_shape_by_name(state.next_bag, starter_piece)
    clean_step_id = _normalize_text(step_id, max_length=96).lower()
    goal_distance = _goal_spawn_distance_layers_for_step(step_id=clean_step_id, ndim=2)
    preferred_min_gravity = _preferred_goal_min_gravity(
        target_level=_goal_target_level_2d(state),
        min_visible_layer=min_visible_layer,
        distance_layers=goal_distance,
    )
    required_move_delta_raw = _required_move_delta_for_step(
        step_id=clean_step_id,
        ndim=2,
    )
    required_move_delta_2d = (
        (
            int(required_move_delta_raw[0]),
            int(required_move_delta_raw[1]),
        )
        if required_move_delta_raw is not None
        else None
    )
    required_event_count = max(
        1,
        _normalize_setup_int(setup.get("required_event_count"), default=1),
    )
    _force_piece_placement_2d(
        state=state,
        shape=selected_shape,
        rotation=0,
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
        required_move_delta=required_move_delta_2d,
        required_move_repetitions=(
            required_event_count if required_move_delta_2d is not None else 1
        ),
        preferred_min_gravity=preferred_min_gravity,
    )
    if _goal_step_requires_lateral_offset(step_id=clean_step_id, ndim=2):
        _nudge_goal_piece_away_from_holes_2d(state=state)


def apply_tutorial_step_setup_nd(
    state: GameStateND,
    cfg: GameConfigND,
    setup: dict[str, Any],
    *,
    lesson_id: str,
    step_id: str,
) -> None:
    scope_tag = _setup_scope_tag(lesson_id=lesson_id, step_id=step_id)
    board_preset = _board_preset_name(setup)
    min_visible_layer = max(
        0,
        _normalize_setup_int(
            setup.get("spawn_min_visible_layer"),
            default=_MIN_VISIBLE_LAYER_DEFAULT,
        ),
    )
    starter_piece = _starter_piece_name(setup)
    board_mutation_requested = bool(
        starter_piece
        or board_preset
        or setup.get("spawn_min_visible_layer") is not None
        or setup.get("bottom_layers_min") is not None
        or setup.get("bottom_layers_max") is not None
    )
    if not board_mutation_requested:
        _ensure_current_piece_visible_nd(
            state=state,
            min_visible_layer=min_visible_layer,
            scope_tag=scope_tag,
        )
        return
    if not starter_piece:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): starter_piece_id is required"
        )
    seed = _normalize_seed(setup.get("rng_seed"), default=int(cfg.rng_seed))
    setup_rng = _set_seeded_runtime_rng(state, seed=seed)
    layers_min, layers_max = _normalize_bottom_layers(setup)
    _clear_runtime_board_state(state)

    if board_preset:
        _apply_board_preset_nd(
            state=state,
            cfg=cfg,
            preset=board_preset,
            setup_rng=setup_rng,
            scope_tag=scope_tag,
        )
    elif not cfg.exploration_mode:
        layer_count = _pick_bottom_layers(
            setup_rng=setup_rng,
            layer_min=layers_min,
            layer_max=layers_max,
        )
        apply_challenge_prefill_nd(
            state,
            layers=layer_count,
            fill_ratio=1.0,
        )

    selected_shape = _find_starter_shape_nd(
        starter_piece=starter_piece,
        cfg=cfg,
        setup_rng=setup_rng,
    )[0]
    if selected_shape is None:
        fallback_piece_set = (
            PIECE_SET_3D_STANDARD if cfg.ndim == 3 else PIECE_SET_4D_STANDARD
        )
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): starter piece "
            f"'{starter_piece}' not found in {cfg.ndim}D piece set "
            f"'{cfg.piece_set_id}' or fallback '{fallback_piece_set}'"
        )

    state.next_bag = []
    state._refill_bag()
    _remove_first_shape_by_name(state.next_bag, starter_piece)
    clean_step_id = _normalize_text(step_id, max_length=96).lower()
    goal_distance = _goal_spawn_distance_layers_for_step(
        step_id=clean_step_id,
        ndim=cfg.ndim,
    )
    preferred_min_gravity = _preferred_goal_min_gravity(
        target_level=_goal_target_level_nd(state, gravity_axis=cfg.gravity_axis),
        min_visible_layer=min_visible_layer,
        distance_layers=goal_distance,
    )
    required_move_delta = _required_move_delta_for_step(
        step_id=clean_step_id,
        ndim=cfg.ndim,
    )
    required_event_count = max(
        1,
        _normalize_setup_int(setup.get("required_event_count"), default=1),
    )
    _force_piece_placement_nd(
        state=state,
        shape=selected_shape,
        rel_blocks=None,
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
        required_move_delta=required_move_delta,
        required_move_repetitions=(
            required_event_count if required_move_delta is not None else 1
        ),
        preferred_min_gravity=preferred_min_gravity,
    )
    if clean_step_id == "move_x_neg" and cfg.ndim >= 3:
        _reposition_opening_translation_piece_nd(
            state=state,
            min_visible_layer=min_visible_layer,
            required_move_repetitions=required_event_count,
            scope_tag=scope_tag,
        )
    if _goal_step_requires_lateral_offset(step_id=clean_step_id, ndim=cfg.ndim):
        _nudge_goal_piece_away_from_holes_nd(state=state)


def ensure_tutorial_piece_visibility_2d(
    state: GameState,
    cfg: GameConfig,
    *,
    min_visible_layer: int = _MIN_VISIBLE_LAYER_DEFAULT,
) -> None:
    del cfg
    _ensure_current_piece_visible_2d(
        state=state,
        min_visible_layer=max(0, int(min_visible_layer)),
        scope_tag="runtime_visibility_2d",
    )


def ensure_tutorial_piece_visibility_nd(
    state: GameStateND,
    cfg: GameConfigND,
    *,
    min_visible_layer: int = _MIN_VISIBLE_LAYER_DEFAULT,
) -> None:
    del cfg
    _ensure_current_piece_visible_nd(
        state=state,
        min_visible_layer=max(0, int(min_visible_layer)),
        scope_tag="runtime_visibility_nd",
    )
