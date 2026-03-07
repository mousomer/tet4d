from __future__ import annotations

import random

from tet4d.engine.core.model import BoardND
from tet4d.engine.core.rng import RNG_MODE_TRUE_RANDOM
from tet4d.engine.gameplay.challenge_mode import apply_challenge_prefill_nd
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND


def create_initial_state(cfg: GameConfigND) -> GameStateND:
    board = BoardND(cfg.dims)
    if cfg.rng_mode == RNG_MODE_TRUE_RANDOM:
        rng = random.Random()
    else:
        rng = random.Random(cfg.rng_seed)
    state = GameStateND(config=cfg, board=board, rng=rng)
    if not cfg.exploration_mode:
        apply_challenge_prefill_nd(state, layers=cfg.challenge_layers)
    return state
