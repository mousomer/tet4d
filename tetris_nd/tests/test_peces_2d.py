# tests/test_pieces2d.py
import unittest

from tetris_nd.pieces2d import rotate_point_2d, ActivePiece2D, PieceShape2D


class TestPieces2D(unittest.TestCase):

    def test_rotate_point_2d(self):
        # Rotate (1, 0) around origin
        self.assertEqual(rotate_point_2d(1, 0, 0), (1, 0))   # 0°
        self.assertEqual(rotate_point_2d(1, 0, 1), (0, -1))  # 90° CW
        self.assertEqual(rotate_point_2d(1, 0, 2), (-1, 0))  # 180°
        self.assertEqual(rotate_point_2d(1, 0, 3), (0, 1))   # 270° CW
        self.assertEqual(rotate_point_2d(1, 0, 4), (1, 0))   # 360° -> back

    def test_active_piece_cells_no_rotation(self):
        shape = PieceShape2D("test", [(0, 0), (1, 0)], color_id=1)
        piece = ActivePiece2D(shape=shape, pos=(5, 10), rotation=0)
        cells = set(piece.cells())
        self.assertEqual(cells, {(5, 10), (6, 10)})

    def test_active_piece_cells_with_rotation(self):
        # Shape: two blocks horizontally
        shape = PieceShape2D("test", [(0, 0), (1, 0)], color_id=1)
        # Place pivot at (5, 10), rotate 90° CW -> blocks stacked vertically
        piece = ActivePiece2D(shape=shape, pos=(5, 10), rotation=1)
        cells = set(piece.cells())
        # (0,0) -> (0,0), (1,0) -> (0,-1) after rotation, so absolute: (5,10) and (5,9)
        self.assertEqual(cells, {(5, 10), (5, 9)})


if __name__ == "__main__":
    unittest.main()
