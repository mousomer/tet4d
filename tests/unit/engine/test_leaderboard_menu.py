from __future__ import annotations

import importlib.util
import unittest

if importlib.util.find_spec("pygame") is None:  # pragma: no cover - env guard
    raise unittest.SkipTest("pygame-ce is required for leaderboard menu tests")

from tet4d.ui.pygame.launch import leaderboard_menu


class TestLeaderboardMenuLayout(unittest.TestCase):
    def test_scaled_column_widths_match_requested_width(self) -> None:
        for total_width in (260, 320, 520, 900, 1220):
            widths = leaderboard_menu._scaled_column_widths(total_width)
            self.assertEqual(sum(widths), total_width)
            self.assertTrue(all(width > 0 for width in widths))

    def test_scaled_column_widths_allow_narrow_panels_without_overflow(self) -> None:
        narrow_width = 240
        widths = leaderboard_menu._scaled_column_widths(narrow_width)
        self.assertEqual(sum(widths), narrow_width)
        self.assertLessEqual(max(widths), narrow_width)


if __name__ == "__main__":
    unittest.main()
