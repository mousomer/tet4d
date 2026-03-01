from __future__ import annotations

import random
import unittest

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_CLASSIC
from tet4d.engine.api import (
    PlayBotController,
    plan_best_2d_move,
    BotMode,
    BotPlannerProfile,
    runtime_assist_combined_score_multiplier,
)
from tet4d.engine.ui_logic.view_modes import GridMode

combined_score_multiplier = runtime_assist_combined_score_multiplier


_EXPECTED_2D_SNAPSHOTS: dict[BotMode, tuple[tuple[int, int, int], ...]] = {
    BotMode.OFF: (
        (10, 130, 3),
        (20, 200, 4),
        (30, 495, 10),
        (40, 625, 13),
        (50, 785, 17),
        (60, 1080, 23),
    ),
    BotMode.ASSIST: (
        (10, 108, 3),
        (20, 164, 4),
        (30, 414, 10),
        (40, 522, 13),
        (50, 656, 17),
        (60, 906, 23),
    ),
    BotMode.AUTO: (
        (10, 74, 3),
        (20, 112, 4),
        (30, 282, 10),
        (40, 356, 13),
        (50, 448, 17),
        (60, 618, 23),
    ),
}


class TestScoreSnapshots(unittest.TestCase):
    def _run_2d_progression(self, mode: BotMode) -> tuple[tuple[int, int, int], ...]:
        cfg = GameConfig(
            width=10, height=20, piece_set=PIECE_SET_2D_CLASSIC, speed_level=4
        )
        state = GameState(
            config=cfg,
            board=BoardND((cfg.width, cfg.height)),
            rng=random.Random(17),
        )
        state.score_multiplier = combined_score_multiplier(
            bot_mode=mode,
            grid_mode=GridMode.OFF,
            speed_level=cfg.speed_level,
        )

        controller = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0)
        snapshots: list[tuple[int, int, int]] = []

        for idx in range(60):
            if state.game_over or state.current_piece is None:
                break
            if mode == BotMode.AUTO:
                self.assertTrue(controller.play_one_piece_2d(state))
            else:
                plan = plan_best_2d_move(
                    state,
                    profile=BotPlannerProfile.BALANCED,
                    budget_ms=40,
                )
                self.assertIsNotNone(plan)
                state.current_piece = plan.final_piece
                state.lock_current_piece()
                if not state.game_over:
                    state.spawn_new_piece()

            if (idx + 1) % 10 == 0:
                snapshots.append((idx + 1, state.score, state.lines_cleared))

        self.assertFalse(state.game_over)
        return tuple(snapshots)

    def test_2d_long_run_score_snapshots_across_assist_modes(self) -> None:
        for mode, expected in _EXPECTED_2D_SNAPSHOTS.items():
            self.assertEqual(self._run_2d_progression(mode), expected)

    def test_2d_long_run_snapshots_are_deterministic(self) -> None:
        for mode in (BotMode.OFF, BotMode.ASSIST, BotMode.AUTO):
            self.assertEqual(
                self._run_2d_progression(mode), self._run_2d_progression(mode)
            )


if __name__ == "__main__":
    unittest.main()
