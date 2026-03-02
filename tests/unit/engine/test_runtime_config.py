from __future__ import annotations

import unittest
from pathlib import Path
from unittest import mock

from tet4d.engine.runtime import runtime_config
from tet4d.engine.runtime.runtime_config import (
    audio_event_specs,
    clear_scoring_board_clear_bonus,
    clear_scoring_multi_layer_bonus,
    gameplay_tuning_payload,
    grid_mode_cycle_names,
    playbot_adaptive_fallback_enabled,
    playbot_benchmark_p95_thresholds,
    playbot_benchmark_history_file,
    playbot_board_size_scaling_policy_for_ndim,
    playbot_budget_table_for_ndim,
    playbot_default_hard_drop_after_soft_drops,
    playbot_dry_run_defaults,
    playbot_learning_mode_policy,
    speed_curve_for_dimension,
)


class TestRuntimeConfig(unittest.TestCase):
    def test_speed_curve_defaults_match_expected_values(self) -> None:
        self.assertEqual(speed_curve_for_dimension(2), (1000, 80))
        self.assertEqual(speed_curve_for_dimension(3), (1350, 110))
        self.assertEqual(speed_curve_for_dimension(4), (1700, 140))

    def test_grid_mode_cycle_has_expected_order(self) -> None:
        self.assertEqual(grid_mode_cycle_names(), ("off", "edge", "full", "helper"))

    def test_clear_scoring_bonus_defaults_are_loaded(self) -> None:
        self.assertEqual(clear_scoring_multi_layer_bonus(0), 0)
        self.assertEqual(clear_scoring_multi_layer_bonus(1), 0)
        self.assertEqual(clear_scoring_multi_layer_bonus(2), 80)
        self.assertEqual(clear_scoring_multi_layer_bonus(3), 240)
        self.assertEqual(clear_scoring_multi_layer_bonus(4), 600)
        self.assertEqual(clear_scoring_multi_layer_bonus(8), 900)
        self.assertEqual(clear_scoring_board_clear_bonus(), 1500)

    def test_playbot_defaults_are_loaded_from_policy(self) -> None:
        self.assertEqual(playbot_budget_table_for_ndim(2), (5, 10, 18, 24))
        self.assertEqual(playbot_budget_table_for_ndim(3), (10, 20, 34, 48))
        self.assertEqual(playbot_budget_table_for_ndim(4), (16, 32, 50, 72))
        self.assertEqual(playbot_default_hard_drop_after_soft_drops(), 4)
        self.assertEqual(playbot_learning_mode_policy(), (True, 8, 0.1, 0.45))
        self.assertEqual(playbot_dry_run_defaults(), (160, 1337))
        self.assertTrue(playbot_adaptive_fallback_enabled())

    def test_playbot_board_size_scaling_policy_is_exposed(self) -> None:
        ref_2d, min_scale_2d, max_scale_2d, exponent_2d = (
            playbot_board_size_scaling_policy_for_ndim(2)
        )
        ref_4d, min_scale_4d, max_scale_4d, exponent_4d = (
            playbot_board_size_scaling_policy_for_ndim(4)
        )
        self.assertEqual(ref_2d, 200)
        self.assertEqual(ref_4d, 2592)
        self.assertLessEqual(min_scale_2d, max_scale_2d)
        self.assertLessEqual(min_scale_4d, max_scale_4d)
        self.assertGreater(exponent_2d, 0.0)
        self.assertGreater(exponent_4d, 0.0)

    def test_playbot_benchmark_thresholds_are_loaded(self) -> None:
        thresholds = playbot_benchmark_p95_thresholds()
        self.assertEqual(set(thresholds.keys()), {"2d", "3d", "4d"})
        self.assertGreater(thresholds["2d"], 0.0)
        self.assertGreater(thresholds["3d"], thresholds["2d"])
        self.assertGreater(thresholds["4d"], thresholds["3d"])

    def test_playbot_benchmark_history_file_sanitized_to_state_root(self) -> None:
        valid_policy = {
            "benchmark": {"history_file": "state/bench/custom_history.jsonl"}
        }
        with mock.patch.object(
            runtime_config, "_playbot_policy", return_value=valid_policy
        ):
            resolved = playbot_benchmark_history_file()
        expected = (
            runtime_config.CONFIG_DIR.parent / "state/bench/custom_history.jsonl"
        ).resolve()
        self.assertEqual(resolved, expected)

        invalid_policy = {"benchmark": {"history_file": "../../outside/history.jsonl"}}
        with mock.patch.object(
            runtime_config, "_playbot_policy", return_value=invalid_policy
        ):
            fallback = playbot_benchmark_history_file()
        fallback_expected = (
            runtime_config.CONFIG_DIR.parent
            / runtime_config.DEFAULT_PLAYBOT_HISTORY_FILE
        ).resolve()
        self.assertEqual(fallback, fallback_expected)

        absolute_policy = {
            "benchmark": {"history_file": str(Path("/tmp/unsafe.jsonl"))}
        }
        with mock.patch.object(
            runtime_config, "_playbot_policy", return_value=absolute_policy
        ):
            absolute_fallback = playbot_benchmark_history_file()
        self.assertEqual(absolute_fallback, fallback_expected)

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
