from __future__ import annotations

import unittest

from tet4d.engine.assist_scoring import combined_score_multiplier
from tet4d.engine.api import BotMode
from tet4d.engine.view_modes import GridMode


class TestAssistScoring(unittest.TestCase):
    def test_bot_assistance_reduces_score_multiplier(self) -> None:
        off = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.OFF, speed_level=10
        )
        assist = combined_score_multiplier(
            bot_mode=BotMode.ASSIST, grid_mode=GridMode.OFF, speed_level=10
        )
        auto = combined_score_multiplier(
            bot_mode=BotMode.AUTO, grid_mode=GridMode.OFF, speed_level=10
        )
        self.assertGreater(off, assist)
        self.assertGreater(assist, auto)

    def test_grid_modes_reduce_multiplier_from_off(self) -> None:
        off = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.OFF, speed_level=10
        )
        edge = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.EDGE, speed_level=10
        )
        full = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.FULL, speed_level=10
        )
        helper = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.HELPER, speed_level=10
        )
        self.assertGreater(off, edge)
        self.assertGreater(edge, full)
        self.assertGreater(full, helper)

    def test_slower_speed_has_lower_multiplier(self) -> None:
        slow = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.OFF, speed_level=1
        )
        fast = combined_score_multiplier(
            bot_mode=BotMode.OFF, grid_mode=GridMode.OFF, speed_level=10
        )
        self.assertGreater(fast, slow)


if __name__ == "__main__":
    unittest.main()
