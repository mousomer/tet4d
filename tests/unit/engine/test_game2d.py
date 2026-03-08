# tests/test_game2d.py
import unittest
import random

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.pieces2d import PieceShape2D, ActivePiece2D
from tet4d.engine.gameplay.pieces2d import PIECE_SET_2D_DEBUG, PIECE_SET_2D_RANDOM
from tet4d.engine.topology_explorer.presets import axis_wrap_profile
from tet4d.engine.gameplay.topology import TOPOLOGY_INVERT_ALL, TOPOLOGY_WRAP_ALL
from tet4d.engine.core.rules.scoring import score_for_clear


class TestGame2D(unittest.TestCase):
    def test_score_table(self):
        self.assertEqual(score_for_clear(0), 0)
        self.assertEqual(score_for_clear(1), 40)
        self.assertEqual(score_for_clear(2), 100)
        self.assertEqual(score_for_clear(3), 300)
        self.assertEqual(score_for_clear(4), 1200)
        self.assertEqual(score_for_clear(5), 1600)

    def make_empty_state(self, width=10, height=20) -> GameState:
        cfg = GameConfig(width=width, height=height)
        board = BoardND((cfg.width, cfg.height))
        # We pass current_piece=None so __post_init__ will spawn one from a random bag.
        # For tests that need precise control, we'll overwrite current_piece ourselves.
        state = GameState(config=cfg, board=board)
        return state

    def test_config_rejects_non_y_gravity_for_2d(self):
        with self.assertRaises(ValueError):
            GameConfig(width=10, height=20, gravity_axis=0)

    def test_spawn_uses_bag_if_provided(self):
        cfg = GameConfig(width=10, height=20)
        board = BoardND((cfg.width, cfg.height))
        # Make a custom one-block piece to control spawn precisely
        custom_shape = PieceShape2D("dot", [(0, 0)], color_id=99)
        # Provide a predefined bag with exactly one shape
        state = GameState(
            config=cfg,
            board=board,
            current_piece=None,
            next_bag=[custom_shape],
        )
        # After __post_init__, it should spawn that shape as the current piece
        self.assertIsNotNone(state.current_piece)
        self.assertEqual(state.current_piece.shape.name, "dot")
        self.assertEqual(state.current_piece.shape.color_id, 99)

    def test_lock_current_piece_and_clear_line(self):
        # Small board for easier reasoning
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Clear existing random piece and bag; we control current_piece manually
        state.board.cells.clear()

        # Pre-fill bottom row y=3 with three blocks at x=1,2,3
        for x in (1, 2, 3):
            state.board.cells[(x, 3)] = 1
        # Keep one remaining block so this is not a full-board clear.
        state.board.cells[(0, 2)] = 9

        # Create a 1x1 piece to fill (0,3) and complete the row
        dot = PieceShape2D("dot", [(0, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=dot, pos=(0, 3), rotation=0)

        score_before = state.score
        lines_before = state.lines_cleared

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines_cleared, lines_before + 1)
        # lock_piece_points(5) + single-line clear(40)
        self.assertEqual(state.score, score_before + 45)

        # The survivor block from y=2 drops into y=3 after clear.
        self.assertEqual(state.board.cells, {(0, 3): 9})

    def test_lock_current_piece_and_clear_two_lines_scores_100(self):
        cfg = GameConfig(width=2, height=3)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)
        state.board.cells.clear()

        # Leave one gap in each target row at x=1.
        state.board.cells[(0, 1)] = 1
        state.board.cells[(0, 2)] = 1
        # Keep one survivor so this does not trigger board-clear bonus.
        state.board.cells[(0, 0)] = 1

        domino = PieceShape2D("domino", [(0, 0), (0, 1)], color_id=2)
        state.current_piece = ActivePiece2D(shape=domino, pos=(1, 1), rotation=0)

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 2)
        self.assertEqual(state.lines_cleared, 2)
        self.assertEqual(state.score, 185)
        self.assertEqual(state.board.cells, {(0, 2): 1})

    def test_score_multiplier_scales_awarded_points(self):
        cfg = GameConfig(width=2, height=2)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        state.board.cells[(0, 1)] = 1
        state.board.cells[(0, 0)] = 9
        state.current_piece = ActivePiece2D(
            PieceShape2D("dot", [(0, 0)], color_id=2), pos=(1, 1), rotation=0
        )
        state.score_multiplier = 0.5
        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        # round((5 + 40) * 0.5) = 22
        self.assertEqual(state.score, 22)

    def test_board_clear_applies_large_bonus(self):
        cfg = GameConfig(width=2, height=2)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        state.board.cells[(0, 1)] = 1
        state.current_piece = ActivePiece2D(
            PieceShape2D("dot", [(0, 0)], color_id=2),
            pos=(1, 1),
            rotation=0,
        )
        cleared = state.lock_current_piece()
        self.assertEqual(cleared, 1)
        self.assertEqual(state.board.cells, {})
        self.assertEqual(state.score, 1545)

    def test_hard_drop_places_piece_at_bottom(self):
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Wipe any existing piece
        state.board.cells.clear()

        # A simple 1x1 piece starting just above the visible area
        dot = PieceShape2D("dot", [(0, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=dot, pos=(2, -1), rotation=0)

        state.hard_drop()

        # After hard_drop, the piece should be locked at the bottom (y = height - 1)
        bottom_y = cfg.height - 1
        self.assertIn((2, bottom_y), state.board.cells)
        self.assertEqual(state.board.cells[(2, bottom_y)], 5)

    def test_can_exist_rejects_out_of_bounds(self):
        cfg = GameConfig(width=4, height=4)
        board = BoardND((cfg.width, cfg.height))
        state = GameState(config=cfg, board=board)

        # Simple 1x1 piece
        dot = PieceShape2D("dot", [(0, 0)], color_id=1)

        # Place inside bounds
        inside_piece = ActivePiece2D(shape=dot, pos=(1, 1), rotation=0)
        self.assertTrue(state._can_exist(inside_piece))

        # Outside to the left, right, and below bottom
        left_piece = ActivePiece2D(shape=dot, pos=(-1, 1), rotation=0)
        right_piece = ActivePiece2D(shape=dot, pos=(cfg.width, 1), rotation=0)
        below_piece = ActivePiece2D(shape=dot, pos=(1, cfg.height), rotation=0)

        self.assertFalse(state._can_exist(left_piece))
        self.assertFalse(state._can_exist(right_piece))
        self.assertFalse(state._can_exist(below_piece))

    def test_random_piece_set_uses_configured_cell_count(self):
        cfg = GameConfig(
            width=10,
            height=20,
            piece_set=PIECE_SET_2D_RANDOM,
            random_cell_count=5,
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.shape.blocks), 5)

    def test_debug_piece_set_does_not_immediately_game_over(self):
        cfg = GameConfig(
            width=10,
            height=20,
            piece_set=PIECE_SET_2D_DEBUG,
        )
        state = GameState(
            config=cfg,
            board=BoardND((cfg.width, cfg.height)),
            rng=random.Random(0),
        )
        for _ in range(6):
            self.assertFalse(state.game_over)
            state.hard_drop()
        self.assertFalse(state.game_over)

    def test_wrap_all_wraps_horizontal_edges(self):
        cfg = GameConfig(width=4, height=6, topology_mode=TOPOLOGY_WRAP_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=dot, pos=(-1, 2), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((3, 2),)
        )

        state.lock_current_piece()
        self.assertIn((3, 2), state.board.cells)

    def test_wrap_all_keeps_gravity_axis_bounded(self):
        cfg = GameConfig(width=4, height=6, topology_mode=TOPOLOGY_WRAP_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=dot, pos=(1, cfg.height), rotation=0)

        self.assertFalse(state._can_exist(state.current_piece))

    def test_invert_all_matches_wrap_behavior_in_2d(self):
        cfg = GameConfig(width=5, height=7, topology_mode=TOPOLOGY_INVERT_ALL)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=4)
        state.current_piece = ActivePiece2D(shape=dot, pos=(cfg.width, 3), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False), ((0, 3),)
        )

    def test_square_rotation_stays_in_place_under_center_rotation(self):
        cfg = GameConfig(width=4, height=6)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        square = PieceShape2D("square", [(0, 0), (1, 0), (0, 1), (1, 1)], color_id=2)
        state.current_piece = ActivePiece2D(shape=square, pos=(2, 3), rotation=0)

        before = tuple(sorted(state.current_piece.cells()))
        state.try_rotate(1)

        self.assertEqual(tuple(sorted(state.current_piece.cells())), before)

    def test_even_span_line_rotation_can_kick_at_edge(self):
        cfg = GameConfig(width=4, height=6, kick_level="light")
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(2, 2), rotation=1)

        before_pos = tuple(state.current_piece.pos)
        before_rotation = state.current_piece.rotation
        state.try_rotate(1)

        self.assertNotEqual(state.current_piece.rotation, before_rotation)
        self.assertNotEqual(tuple(state.current_piece.pos), before_pos)
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(len(mapped), 4)
        self.assertEqual(len(set(mapped)), 4)

    def test_wrap_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfig(
            width=4,
            height=6,
            topology_mode=TOPOLOGY_WRAP_ALL,
            kick_level="standard",
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(-2, 4), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        state.try_rotate(1)

        self.assertEqual(state.current_piece.pos, (-2, 3))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(mapped, ((2, 5), (2, 4), (2, 3), (2, 2)))
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_explorer_glue_runtime_wraps_live_2d_movement(self):
        cfg = GameConfig(
            width=4,
            height=6,
            exploration_mode=True,
            explorer_topology_profile=axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        dot = PieceShape2D("dot", [(0, 0)], color_id=5)
        state.current_piece = ActivePiece2D(shape=dot, pos=(3, 3), rotation=0)

        state.try_move(1, 0)

        self.assertEqual(
            state.current_piece_cells_mapped(include_above=False),
            ((0, 3),),
        )

    def test_invert_topology_rotation_uses_topology_mapping_with_kicks(self):
        cfg = GameConfig(
            width=4,
            height=6,
            topology_mode=TOPOLOGY_INVERT_ALL,
            kick_level="standard",
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(-2, 4), rotation=0)

        self.assertTrue(state._can_exist(state.current_piece))
        state.try_rotate(1)

        self.assertEqual(state.current_piece.pos, (-2, 3))
        mapped = state.current_piece_cells_mapped(include_above=False)
        self.assertEqual(mapped, ((2, 5), (2, 4), (2, 3), (2, 2)))
        self.assertEqual(len(mapped), len(set(mapped)))

    def test_even_span_line_rotation_fails_cleanly_at_edge(self):
        cfg = GameConfig(width=4, height=6)
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        line = PieceShape2D("I", [(-1, 0), (0, 0), (1, 0), (2, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape=line, pos=(2, 2), rotation=1)

        before_rotation = state.current_piece.rotation
        before_cells = tuple(sorted(state.current_piece.cells()))
        state.try_rotate(1)

        self.assertEqual(state.current_piece.rotation, before_rotation)
        self.assertEqual(tuple(sorted(state.current_piece.cells())), before_cells)



if __name__ == "__main__":
    unittest.main()
