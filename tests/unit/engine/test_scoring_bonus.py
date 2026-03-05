from __future__ import annotations

import unittest

from tet4d.engine.core.rules.scoring import score_for_clear
from tet4d.engine.gameplay.scoring_bonus import (
    plane_cell_count_for_dims,
    score_with_clear_bonuses,
)


class ScoringBonusTests(unittest.TestCase):
    def test_plane_cell_count_for_dims(self) -> None:
        self.assertEqual(
            plane_cell_count_for_dims((10, 20), gravity_axis=1),
            10,
        )
        self.assertEqual(
            plane_cell_count_for_dims((4, 20, 6), gravity_axis=1),
            24,
        )
        self.assertEqual(
            plane_cell_count_for_dims((4, 20, 6, 3), gravity_axis=1),
            72,
        )

    def test_score_with_clear_bonuses_weights_by_layer_size(self) -> None:
        raw_base_points = 5 + score_for_clear(1)
        raw_small, awarded_small = score_with_clear_bonuses(
            raw_base_points=raw_base_points,
            cleared_count=1,
            plane_cell_count=10,
            board_cell_count_after_clear=5,
            score_multiplier=1.0,
        )
        raw_large, awarded_large = score_with_clear_bonuses(
            raw_base_points=raw_base_points,
            cleared_count=1,
            plane_cell_count=24,
            board_cell_count_after_clear=5,
            score_multiplier=1.0,
        )
        self.assertEqual(raw_small, raw_base_points)
        self.assertEqual(awarded_small, raw_base_points)
        # sqrt(24/10) ~= 1.549, so weighted clear points for a single clear:
        # round(40 * 1.549) = 62, yielding +22 over the 40-point base clear.
        self.assertEqual(raw_large, raw_base_points + 22)
        self.assertEqual(awarded_large, raw_base_points + 22)
        self.assertGreater(raw_large, raw_small)
        self.assertGreater(awarded_large, awarded_small)


if __name__ == "__main__":
    unittest.main()
