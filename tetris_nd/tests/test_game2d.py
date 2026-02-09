# tests/test_game2d.py
import unittest

from tetris_nd.board import BoardND
from tetris_nd.game2d import GameConfig, GameState, Action
from tetris_nd.pieces2d import PieceShape2D, ActivePiece2D


class TestGame2D(unittest.TestCase):

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

        # Create a 1x1 piece to fill (0,3) and complete the row
        dot = PieceShape2D("dot", [(0, 0)], color_id=2)
        state.current_piece = ActivePiece2D(shape=dot, pos=(0, 3), rotation=0)

        score_before = state.score
        lines_before = state.lines_cleared

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines_cleared, lines_before + 1)
        # Single-line clear adds +40 score in our rule
        self.assertEqual(state.score, score_before + 40)

        # Bottom row should now be empty
        for x in range(cfg.width):
            self.assertNotIn((x, 3), state.board.cells)

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


if __name__ == "__main__":
    unittest.main()
