from __future__ import annotations

import unittest

from tet4d.engine import front3d_setup, frontend_nd


class TestFront3DSetupDedup(unittest.TestCase):
    def test_build_config_matches_shared_nd_builder(self) -> None:
        settings = front3d_setup.GameSettings3D(
            width=6,
            height=14,
            depth=5,
            fourth=9,
            speed_level=3,
            piece_set_index=0,
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

        cfg_adapter = front3d_setup.build_config(settings)
        cfg_shared = frontend_nd.build_config(settings, 3)

        self.assertEqual(cfg_adapter.dims, cfg_shared.dims)
        self.assertEqual(cfg_adapter.gravity_axis, cfg_shared.gravity_axis)
        self.assertEqual(cfg_adapter.speed_level, cfg_shared.speed_level)
        self.assertEqual(cfg_adapter.piece_set_id, cfg_shared.piece_set_id)
        self.assertEqual(cfg_adapter.topology_mode, cfg_shared.topology_mode)
        self.assertEqual(cfg_adapter.topology_edge_rules, cfg_shared.topology_edge_rules)

    def test_gravity_interval_matches_shared_nd_builder(self) -> None:
        settings = front3d_setup.GameSettings3D(speed_level=4)
        cfg = front3d_setup.build_config(settings)
        self.assertEqual(
            front3d_setup.gravity_interval_ms_from_config(cfg),
            frontend_nd.gravity_interval_ms_from_config(cfg),
        )


if __name__ == "__main__":
    unittest.main()
