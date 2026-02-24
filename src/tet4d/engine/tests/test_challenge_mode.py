from __future__ import annotations

import random
import unittest

from tet4d.engine.board import BoardND
from tet4d.engine.challenge_mode import apply_challenge_prefill_2d, apply_challenge_prefill_nd
from tet4d.engine.game2d import GameConfig, GameState
from tet4d.engine.game_nd import GameConfigND, GameStateND


class TestChallengeMode(unittest.TestCase):
    def test_prefill_2d_fills_lower_layers_with_holes(self) -> None:
        cfg = GameConfig(width=8, height=12)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(0))
        state.board.cells.clear()

        layers = 3
        added = apply_challenge_prefill_2d(state, layers=layers, fill_ratio=1.0)
        self.assertEqual(added, (cfg.width - 1) * layers)

        for i in range(layers):
            y = cfg.height - 1 - i
            count = sum(1 for (x, yy) in state.board.cells if yy == y and 0 <= x < cfg.width)
            self.assertEqual(count, cfg.width - 1)

    def test_prefill_nd_fills_lower_layers_with_holes(self) -> None:
        cfg = GameConfigND(dims=(4, 10, 3), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        state.board.cells.clear()

        layers = 2
        added = apply_challenge_prefill_nd(state, layers=layers, fill_ratio=1.0)
        layer_size = cfg.dims[0] * cfg.dims[2]
        self.assertEqual(added, (layer_size - 1) * layers)

        for i in range(layers):
            y = cfg.dims[1] - 1 - i
            count = sum(1 for (x, yy, z) in state.board.cells if yy == y and 0 <= x < cfg.dims[0] and 0 <= z < cfg.dims[2])
            self.assertEqual(count, layer_size - 1)


if __name__ == "__main__":
    unittest.main()
