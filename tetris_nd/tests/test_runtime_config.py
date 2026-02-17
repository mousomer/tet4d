from __future__ import annotations

import unittest

from tetris_nd.runtime_config import (
    audio_event_specs,
    gameplay_tuning_payload,
    grid_mode_cycle_names,
    playbot_budget_table_for_ndim,
    playbot_default_hard_drop_after_soft_drops,
    playbot_dry_run_defaults,
    speed_curve_for_dimension,
)


class TestRuntimeConfig(unittest.TestCase):
    def test_speed_curve_defaults_match_expected_values(self) -> None:
        self.assertEqual(speed_curve_for_dimension(2), (1000, 80))
        self.assertEqual(speed_curve_for_dimension(3), (1350, 110))
        self.assertEqual(speed_curve_for_dimension(4), (1700, 140))

    def test_grid_mode_cycle_has_expected_order(self) -> None:
        self.assertEqual(grid_mode_cycle_names(), ("off", "edge", "full", "helper"))

    def test_playbot_defaults_are_loaded_from_policy(self) -> None:
        self.assertEqual(playbot_budget_table_for_ndim(2), (6, 12, 20))
        self.assertEqual(playbot_budget_table_for_ndim(3), (12, 24, 40))
        self.assertEqual(playbot_budget_table_for_ndim(4), (18, 36, 60))
        self.assertEqual(playbot_default_hard_drop_after_soft_drops(), 4)
        self.assertEqual(playbot_dry_run_defaults(), (160, 1337))

    def test_audio_event_specs_are_non_empty(self) -> None:
        specs = audio_event_specs()
        self.assertIn("move", specs)
        self.assertIn("game_over", specs)
        for frequency_hz, duration_ms, amplitude in specs.values():
            self.assertGreater(frequency_hz, 0.0)
            self.assertGreater(duration_ms, 0)
            self.assertGreaterEqual(amplitude, 0.0)
            self.assertLessEqual(amplitude, 1.0)

    def test_payload_helpers_return_copies(self) -> None:
        payload_a = gameplay_tuning_payload()
        payload_b = gameplay_tuning_payload()
        payload_a["speed_curve"]["2d"]["base_ms"] = 999
        self.assertEqual(payload_b["speed_curve"]["2d"]["base_ms"], 1000)


if __name__ == "__main__":
    unittest.main()
