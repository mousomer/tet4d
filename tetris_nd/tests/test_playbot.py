from __future__ import annotations

import random
import unittest

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState
from tetris_nd.game_nd import GameConfigND, GameStateND
from tetris_nd.pieces2d import ActivePiece2D, PieceShape2D
from tetris_nd.pieces2d import PIECE_SET_2D_DEBUG
from tetris_nd.pieces_nd import (
    ActivePieceND,
    PIECE_SET_3D_DEBUG,
    PIECE_SET_4D_DEBUG,
    PieceShapeND,
)
from tetris_nd.playbot import PlayBotController, run_dry_run_2d, run_dry_run_nd
from tetris_nd.playbot.planner_nd import _greedy_key_4d, _simulate_lock_board, plan_best_nd_move
from tetris_nd.playbot.types import BotMode
from tetris_nd.view_modes import GridMode, cycle_grid_mode


class TestPlaybot(unittest.TestCase):
    def test_grid_mode_cycle(self) -> None:
        self.assertEqual(cycle_grid_mode(GridMode.OFF), GridMode.EDGE)
        self.assertEqual(cycle_grid_mode(GridMode.EDGE), GridMode.FULL)
        self.assertEqual(cycle_grid_mode(GridMode.FULL), GridMode.HELPER)
        self.assertEqual(cycle_grid_mode(GridMode.HELPER), GridMode.OFF)
        self.assertEqual(cycle_grid_mode(GridMode.SHADOW), GridMode.EDGE)

    def test_controller_can_place_one_piece_2d(self) -> None:
        cfg = GameConfig(width=10, height=20, piece_set=PIECE_SET_2D_DEBUG)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(0))
        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0)

        before_piece = state.current_piece
        before_lines = state.lines_cleared
        self.assertTrue(bot.play_one_piece_2d(state))
        self.assertIsNotNone(state.current_piece)
        self.assertTrue(state.current_piece is not before_piece or state.lines_cleared > before_lines)

    def test_controller_can_place_one_piece_nd(self) -> None:
        cfg = GameConfigND(dims=(6, 14, 4), gravity_axis=1, piece_set_id=PIECE_SET_3D_DEBUG)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0)

        before_piece = state.current_piece
        before_lines = state.lines_cleared
        self.assertTrue(bot.play_one_piece_nd(state))
        self.assertIsNotNone(state.current_piece)
        self.assertTrue(state.current_piece is not before_piece or state.lines_cleared > before_lines)

    def test_auto_tick_is_incremental_soft_drop_2d(self) -> None:
        cfg = GameConfig(width=10, height=20, piece_set=PIECE_SET_2D_DEBUG)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(0))
        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=1)

        before_cells = len(state.board.cells)
        before_piece = state.current_piece
        before_pos = before_piece.pos if before_piece is not None else None
        before_rot = before_piece.rotation if before_piece is not None else None
        bot.tick_2d(state, dt_ms=16)

        self.assertEqual(len(state.board.cells), before_cells)
        if before_piece is not None and state.current_piece is not None and before_pos is not None and before_rot is not None:
            changed = (
                state.current_piece.pos != before_pos
                or state.current_piece.rotation != before_rot
            )
            self.assertTrue(changed)

    def test_dry_run_reports_clears_for_debug_sets(self) -> None:
        cfg_2d = GameConfig(width=6, height=14, piece_set=PIECE_SET_2D_DEBUG)
        report_2d = run_dry_run_2d(cfg_2d, max_pieces=30, seed=0)
        self.assertTrue(report_2d.passed)
        self.assertGreater(report_2d.clears_observed, 0)

        cfg_3d = GameConfigND(dims=(6, 14, 4), gravity_axis=1, piece_set_id=PIECE_SET_3D_DEBUG)
        report_3d = run_dry_run_nd(cfg_3d, max_pieces=24, seed=0)
        self.assertTrue(report_3d.passed)
        self.assertGreater(report_3d.clears_observed, 0)

        cfg_4d = GameConfigND(dims=(6, 14, 4, 3), gravity_axis=1, piece_set_id=PIECE_SET_4D_DEBUG)
        report_4d = run_dry_run_nd(cfg_4d, max_pieces=16, seed=0)
        self.assertTrue(report_4d.passed)
        self.assertGreater(report_4d.clears_observed, 0)

    def test_bot_speed_interval_mapping(self) -> None:
        gravity_ms = 120
        slow = PlayBotController.action_interval_from_speed(gravity_ms, 1)
        fast = PlayBotController.action_interval_from_speed(gravity_ms, 10)
        self.assertGreater(slow, fast)
        self.assertGreaterEqual(fast, 20)

    def test_rotations_wait_until_piece_is_visible_2d(self) -> None:
        cfg = GameConfig(width=10, height=20, piece_set=PIECE_SET_2D_DEBUG)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(0))
        state.board.cells.clear()
        state.current_piece = ActivePiece2D(
            PieceShape2D("domino", [(0, 0), (1, 0)], color_id=8),
            pos=(4, -1),
            rotation=0,
        )

        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0)
        # Freeze target so this test isolates visibility gating.
        bot._update_assist_2d = lambda _state: None  # type: ignore[method-assign]
        bot._target_rot_2d = 1
        bot._target_x_2d = 4

        rot_before = state.current_piece.rotation
        pos_before = state.current_piece.pos
        bot._step_piece_2d(state)
        self.assertEqual(state.current_piece.rotation, rot_before)
        self.assertNotEqual(state.current_piece.pos, pos_before)

        bot._step_piece_2d(state)
        self.assertNotEqual(state.current_piece.rotation, rot_before)

    def test_4d_greedy_key_prioritizes_clear_completion_then_holes(self) -> None:
        dims = (2, 4, 2, 1)
        gravity_axis = 1

        # Completion beats hole minimization when cleared layers are equal.
        more_complete_more_holes = {
            (0, 1, 0, 0),
            (1, 1, 0, 0),
        }
        less_complete_fewer_holes = {
            (0, 2, 0, 0),
            (1, 3, 0, 0),
        }
        key_more_complete = _greedy_key_4d(
            {coord: 1 for coord in more_complete_more_holes},
            dims=dims,
            gravity_axis=gravity_axis,
            cleared=0,
            game_over=False,
        )
        key_less_complete = _greedy_key_4d(
            {coord: 1 for coord in less_complete_fewer_holes},
            dims=dims,
            gravity_axis=gravity_axis,
            cleared=0,
            game_over=False,
        )
        self.assertGreater(key_more_complete, key_less_complete)

        # Any layer clear beats non-clear outcomes.
        clear_with_holes = {
            (0, 1, 0, 0),
            (0, 3, 0, 0),
        }
        clean_no_clear = {
            (0, 2, 0, 0),
            (0, 3, 0, 0),
        }
        key_clear = _greedy_key_4d(
            {coord: 1 for coord in clear_with_holes},
            dims=dims,
            gravity_axis=gravity_axis,
            cleared=1,
            game_over=False,
        )
        key_no_clear = _greedy_key_4d(
            {coord: 1 for coord in clean_no_clear},
            dims=dims,
            gravity_axis=gravity_axis,
            cleared=0,
            game_over=False,
        )
        self.assertGreater(key_clear, key_no_clear)

    def test_4d_planner_prefers_placement_that_clears_a_plane(self) -> None:
        cfg = GameConfigND(dims=(3, 5, 2, 2), gravity_axis=1, piece_set_id=PIECE_SET_4D_DEBUG)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        state.board.cells.clear()

        y = cfg.dims[cfg.gravity_axis] - 1
        # Fill the bottom 3D layer except two adjacent x-cells at (z=0, w=0).
        for x in range(cfg.dims[0]):
            for z in range(cfg.dims[2]):
                for w in range(cfg.dims[3]):
                    if (x, z, w) in {(1, 0, 0), (2, 0, 0)}:
                        continue
                    state.board.cells[(x, y, z, w)] = 9

        shape = PieceShapeND(
            name="domino_x_4d",
            blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
            color_id=3,
        )
        state.current_piece = ActivePieceND.from_shape(shape, (1, -2, 0, 0))

        plan = plan_best_nd_move(state)
        if plan is None:
            self.fail("expected a valid 4D bot plan")
        _cells_after, cleared, game_over = _simulate_lock_board(state, plan.final_piece)
        self.assertFalse(game_over)
        self.assertEqual(cleared, 1)

    def test_bot_hard_drops_after_configured_soft_drops_2d(self) -> None:
        cfg = GameConfig(width=10, height=20, piece_set=PIECE_SET_2D_DEBUG)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)), rng=random.Random(0))
        state.board.cells.clear()
        state.current_piece = ActivePiece2D(
            PieceShape2D("domino", [(0, 0), (1, 0)], color_id=8),
            pos=(4, 0),
            rotation=0,
        )

        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0, hard_drop_after_soft_drops=2)
        # Freeze target so only descent behavior is tested.
        bot._update_assist_2d = lambda _state: None  # type: ignore[method-assign]
        bot._target_rot_2d = state.current_piece.rotation
        bot._target_x_2d = state.current_piece.pos[0]

        before_cells = len(state.board.cells)
        bot._step_piece_2d(state)
        self.assertEqual(len(state.board.cells), before_cells)
        bot._step_piece_2d(state)
        self.assertEqual(len(state.board.cells), before_cells)
        bot._step_piece_2d(state)
        self.assertGreater(len(state.board.cells), before_cells)

    def test_bot_hard_drops_after_configured_soft_drops_nd(self) -> None:
        cfg = GameConfigND(dims=(4, 8, 2, 1), gravity_axis=1, piece_set_id=PIECE_SET_4D_DEBUG)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims), rng=random.Random(0))
        state.board.cells.clear()
        shape = PieceShapeND(
            name="domino_x_4d",
            blocks=((0, 0, 0, 0), (1, 0, 0, 0)),
            color_id=3,
        )
        state.current_piece = ActivePieceND.from_shape(shape, (1, 0, 0, 0))

        bot = PlayBotController(mode=BotMode.AUTO, action_interval_ms=0, hard_drop_after_soft_drops=2)
        # Freeze target so only descent behavior is tested.
        bot._update_assist_nd = lambda _state: None  # type: ignore[method-assign]
        bot._target_blocks_nd = tuple(sorted(tuple(block) for block in state.current_piece.rel_blocks))
        bot._target_lateral_nd = (state.current_piece.pos[0], state.current_piece.pos[2], state.current_piece.pos[3])
        bot._rotation_plan_nd = []

        before_cells = len(state.board.cells)
        bot._step_piece_nd(state)
        self.assertEqual(len(state.board.cells), before_cells)
        bot._step_piece_nd(state)
        self.assertEqual(len(state.board.cells), before_cells)
        bot._step_piece_nd(state)
        self.assertGreater(len(state.board.cells), before_cells)


if __name__ == "__main__":
    unittest.main()
