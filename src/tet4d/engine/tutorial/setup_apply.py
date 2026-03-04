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
    rotate_point_2d,
)
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
    return tuple(rotate_point_2d(block[0], block[1], int(rotation)) for block in shape.blocks)


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


def _force_piece_placement_2d(
    *,
    state: GameState,
    shape: PieceShape2D,
    rotation: int,
    min_visible_layer: int,
    scope_tag: str,
) -> None:
    oriented_blocks = _oriented_blocks_2d(shape, rotation=rotation)
    min_block_x = min(block[0] for block in oriented_blocks)
    max_block_x = max(block[0] for block in oriented_blocks)
    min_block_y = min(block[1] for block in oriented_blocks)
    max_block_y = max(block[1] for block in oriented_blocks)
    span_x = max_block_x - min_block_x + 1
    target_x = ((state.config.width - span_x) // 2) - min_block_x
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

    for y in range(min_spawn_y, max_spawn_y + 1):
        for x in x_candidates:
            candidate = ActivePiece2D(shape, (x, y), rotation=rotation)
            if not _piece_is_visible_2d(state, candidate):
                continue
            if _piece_min_gravity_2d(state, candidate) < min_visible_layer:
                continue
            if state._can_exist(candidate):
                state.current_piece = candidate
                return
    raise RuntimeError(
        f"tutorial setup failed ({scope_tag}): could not place 2D starter piece without collision"
    )


def _force_piece_placement_nd(
    *,
    state: GameStateND,
    shape: PieceShapeND,
    rel_blocks: tuple[tuple[int, ...], ...] | None,
    min_visible_layer: int,
    scope_tag: str,
    required_move_delta: tuple[int, ...] | None = None,
    required_move_repetitions: int = 1,
) -> None:
    dims = state.config.dims
    ndim = state.config.ndim
    gravity_axis = state.config.gravity_axis
    blocks = tuple(rel_blocks) if rel_blocks is not None else shape.blocks
    mins = [min(block[axis] for block in blocks) for axis in range(ndim)]
    maxs = [max(block[axis] for block in blocks) for axis in range(ndim)]
    initial_pos = list(state._spawn_pos_for_shape(shape))
    min_spawn_g = max(min_visible_layer - mins[gravity_axis], -mins[gravity_axis])
    max_spawn_g = (dims[gravity_axis] - 1) - maxs[gravity_axis]
    if min_spawn_g > max_spawn_g:
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): min visible layer cannot fit ND starter piece"
        )

    lateral_axes = [axis for axis in range(ndim) if axis != gravity_axis]
    lateral_candidates: list[list[int]] = []
    for axis in lateral_axes:
        candidates = _axis_candidate_values(
            axis_size=dims[axis],
            min_block=mins[axis],
            max_block=maxs[axis],
            preferred=initial_pos[axis],
        )
        if not candidates:
            raise RuntimeError(
                f"tutorial setup failed ({scope_tag}): no legal ND spawn positions for starter piece"
            )
        lateral_candidates.append(candidates)

    for gravity_value in range(min_spawn_g, max_spawn_g + 1):
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
    if preset == "2d_almost_line":
        target_y = cfg.height - 1
        gap_x = int(setup_rng.randrange(max(1, cfg.width)))
        for x in range(cfg.width):
            if x == gap_x:
                continue
            state.board.cells[(x, target_y)] = (x % 7) + 1
        return
    if preset == "2d_almost_full_clear_o":
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
        return
    raise RuntimeError(
        f"tutorial setup failed ({scope_tag}): unknown 2D board preset '{preset}'"
    )


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
    deltas = {
        "move_x_neg": (-1, 0, 0, 0),
        "move_x_pos": (1, 0, 0, 0),
        "move_z_neg": (0, 0, -1, 0),
        "move_z_pos": (0, 0, 1, 0),
        "move_w_neg": (0, 0, 0, -1),
        "move_w_pos": (0, 0, 0, 1),
    }
    delta_4d = deltas.get(step_id)
    if delta_4d is None:
        return None
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
            f"tutorial setup failed ({scope_tag}): starter piece '{starter_piece}' not found in 2D piece set '{cfg.piece_set}' or fallback '{PIECE_SET_2D_CLASSIC}'"
        )

    state.next_bag = []
    state._refill_bag()
    _remove_first_shape_by_name(state.next_bag, starter_piece)
    _force_piece_placement_2d(
        state=state,
        shape=selected_shape,
        rotation=0,
        min_visible_layer=min_visible_layer,
        scope_tag=scope_tag,
    )


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
        fallback_piece_set = PIECE_SET_3D_STANDARD if cfg.ndim == 3 else PIECE_SET_4D_STANDARD
        raise RuntimeError(
            f"tutorial setup failed ({scope_tag}): starter piece '{starter_piece}' not found in {cfg.ndim}D piece set '{cfg.piece_set_id}' or fallback '{fallback_piece_set}'"
        )

    state.next_bag = []
    state._refill_bag()
    _remove_first_shape_by_name(state.next_bag, starter_piece)
    clean_step_id = _normalize_text(step_id, max_length=96).lower()
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
    )


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
