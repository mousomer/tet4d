from __future__ import annotations

import random
from itertools import product

from .game2d import GameState
from .game_nd import GameStateND
from .runtime_config import challenge_prefill_ratio


def apply_challenge_prefill_2d(
    state: GameState,
    *,
    layers: int,
    fill_ratio: float | None = None,
) -> int:
    if layers <= 0:
        return 0
    ratio = challenge_prefill_ratio(2) if fill_ratio is None else float(fill_ratio)
    ratio = max(0.0, min(1.0, ratio))
    width = state.config.width
    height = state.config.height
    max_layers = max(0, height - 2)
    layer_count = max(0, min(int(layers), max_layers))
    if layer_count <= 0:
        return 0

    rng = state.rng if state.rng is not None else random.Random()
    added = 0
    for i in range(layer_count):
        y = height - 1 - i
        hole_x = rng.randrange(width)
        for x in range(width):
            if x == hole_x:
                continue
            if rng.random() > ratio:
                continue
            coord = (x, y)
            if coord in state.board.cells:
                continue
            state.board.cells[coord] = rng.randint(1, 7)
            added += 1
    return added


def apply_challenge_prefill_nd(
    state: GameStateND,
    *,
    layers: int,
    fill_ratio: float | None = None,
) -> int:
    if layers <= 0:
        return 0
    ratio = (
        challenge_prefill_ratio(state.config.ndim)
        if fill_ratio is None
        else float(fill_ratio)
    )
    ratio = max(0.0, min(1.0, ratio))
    cfg = state.config
    gravity_axis = cfg.gravity_axis
    g_size = cfg.dims[gravity_axis]
    max_layers = max(0, g_size - 2)
    layer_count = max(0, min(int(layers), max_layers))
    if layer_count <= 0:
        return 0

    rng = state.rng if state.rng is not None else random.Random()
    ndim = cfg.ndim
    lateral_axes = tuple(axis for axis in range(ndim) if axis != gravity_axis)
    lateral_ranges = [range(cfg.dims[axis]) for axis in lateral_axes]
    lateral_positions = list(product(*lateral_ranges))
    if not lateral_positions:
        return 0

    added = 0
    for i in range(layer_count):
        g_val = g_size - 1 - i
        hole = lateral_positions[rng.randrange(len(lateral_positions))]
        for lateral in lateral_positions:
            if lateral == hole:
                continue
            if rng.random() > ratio:
                continue
            coord = [0] * ndim
            coord[gravity_axis] = g_val
            for idx, axis in enumerate(lateral_axes):
                coord[axis] = lateral[idx]
            frozen = tuple(coord)
            if frozen in state.board.cells:
                continue
            state.board.cells[frozen] = rng.randint(1, 7)
            added += 1
    return added
