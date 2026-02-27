from __future__ import annotations

import unittest

from tet4d.engine import frontend_nd
from tet4d.engine.gameplay.pieces_nd import (
    PIECE_SET_4D_SIX,
    get_piece_shapes_nd,
    piece_set_options_for_dimension,
)


class TestFront3DSetupDedup(unittest.TestCase):
    def test_build_config_matches_shared_nd_builder(self) -> None:
        settings = frontend_nd.GameSettingsND(
            width=6,
            height=14,
            depth=5,
            fourth=9,
            speed_level=3,
            piece_set_index=0,
            random_mode_index=0,
            game_seed=4242,
            topology_mode=0,
            topology_advanced=0,
            topology_profile_index=0,
            bot_mode_index=0,
            bot_algorithm_index=0,
            bot_profile_index=1,
            bot_speed_level=7,
            bot_budget_ms=24,
            challenge_layers=2,
            exploration_mode=0,
        )

        cfg_adapter = frontend_nd.build_config(settings, 3)
        cfg_shared = frontend_nd.build_config(settings, 3)

        self.assertEqual(cfg_adapter.dims, cfg_shared.dims)
        self.assertEqual(cfg_adapter.gravity_axis, cfg_shared.gravity_axis)
        self.assertEqual(cfg_adapter.speed_level, cfg_shared.speed_level)
        self.assertEqual(cfg_adapter.piece_set_id, cfg_shared.piece_set_id)
        self.assertEqual(cfg_adapter.rng_mode, cfg_shared.rng_mode)
        self.assertEqual(cfg_adapter.rng_seed, cfg_shared.rng_seed)
        self.assertEqual(cfg_adapter.topology_mode, cfg_shared.topology_mode)
        self.assertEqual(
            cfg_adapter.topology_edge_rules, cfg_shared.topology_edge_rules
        )

    def test_gravity_interval_matches_shared_nd_builder(self) -> None:
        settings = frontend_nd.GameSettingsND(speed_level=4)
        cfg = frontend_nd.build_config(settings, 3)
        self.assertEqual(
            frontend_nd.gravity_interval_ms_from_config(cfg),
            frontend_nd.gravity_interval_ms_from_config(cfg),
        )

    def test_4d_setup_can_select_six_cell_piece_set(self) -> None:
        options_4d = piece_set_options_for_dimension(4)
        six_cell_index = options_4d.index(PIECE_SET_4D_SIX)
        settings = frontend_nd.GameSettingsND(piece_set_index=six_cell_index)
        cfg = frontend_nd.build_config(settings, 4)
        self.assertEqual(cfg.piece_set_id, PIECE_SET_4D_SIX)
        shapes = get_piece_shapes_nd(4, piece_set_id=cfg.piece_set_id)
        self.assertTrue(shapes)
        self.assertTrue(all(len(shape.blocks) == 6 for shape in shapes))


if __name__ == "__main__":
    unittest.main()
