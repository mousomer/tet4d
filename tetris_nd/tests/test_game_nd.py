import unittest

from tetris_nd.board import BoardND
from tetris_nd.game_nd import GameConfigND, GameStateND
from tetris_nd.pieces_nd import ActivePieceND, PIECE_SET_4D_SIX, PieceShapeND


class TestGameND(unittest.TestCase):

    def test_spawn_piece_matches_config_dimension(self):
        cfg = GameConfigND(dims=(6, 12, 4), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.pos), 3)
        for coord in state.current_piece.cells():
            self.assertEqual(len(coord), 3)

    def test_move_along_extra_axis(self):
        cfg = GameConfigND(dims=(5, 10, 3), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=9)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(2, 0, 1))

        self.assertTrue(state.try_move_axis(2, 1))
        self.assertEqual(state.current_piece.pos, (2, 0, 2))
        self.assertFalse(state.try_move_axis(2, 1))

    def test_hard_drop_locks_to_bottom_along_gravity_axis(self):
        cfg = GameConfigND(dims=(4, 5, 3), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=5)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(1, -1, 2))

        state.hard_drop()

        self.assertIn((1, 4, 2), state.board.cells)
        self.assertEqual(state.board.cells[(1, 4, 2)], 5)

    def test_lock_piece_clears_full_3d_plane(self):
        cfg = GameConfigND(dims=(2, 3, 2), gravity_axis=1)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()

        # Fill full bottom plane y=2 except one hole at (0, 2, 0)
        for x in range(cfg.dims[0]):
            for z in range(cfg.dims[2]):
                if (x, z) != (0, 0):
                    state.board.cells[(x, 2, z)] = 1

        # One block above; should drop after clear.
        state.board.cells[(1, 1, 1)] = 2

        dot = PieceShapeND("dot", ((0, 0, 0),), color_id=3)
        state.current_piece = ActivePieceND.from_shape(dot, pos=(0, 2, 0))

        cleared = state.lock_current_piece()

        self.assertEqual(cleared, 1)
        self.assertEqual(state.lines_cleared, 1)
        self.assertEqual(state.board.cells.get((1, 2, 1)), 2)

    def test_4d_config_can_use_six_cell_piece_set(self):
        cfg = GameConfigND(dims=(5, 10, 5, 4), gravity_axis=1, piece_set_4d=PIECE_SET_4D_SIX)
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(state.current_piece)
        self.assertEqual(len(state.current_piece.shape.blocks), 6)

    def test_invalid_4d_piece_set_rejected_by_config(self):
        with self.assertRaises(ValueError):
            GameConfigND(dims=(5, 10, 5, 4), gravity_axis=1, piece_set_4d="invalid")


if __name__ == "__main__":
    unittest.main()
