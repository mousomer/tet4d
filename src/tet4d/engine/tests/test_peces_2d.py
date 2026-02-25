# tests/test_pieces2d.py
import unittest

from tet4d.engine.pieces2d import (
    ActivePiece2D,
    PIECE_SET_2D_OPTIONS,
    PieceShape2D,
    get_piece_bag_2d,
    get_debug_rectangles_2d,
    rotate_point_2d,
)


class TestPieces2D(unittest.TestCase):
    def test_rotate_point_2d(self):
        # Rotate (1, 0) around origin
        self.assertEqual(rotate_point_2d(1, 0, 0), (1, 0))  # 0°
        self.assertEqual(rotate_point_2d(1, 0, 1), (0, -1))  # 90° CW
        self.assertEqual(rotate_point_2d(1, 0, 2), (-1, 0))  # 180°
        self.assertEqual(rotate_point_2d(1, 0, 3), (0, 1))  # 270° CW
        self.assertEqual(rotate_point_2d(1, 0, 4), (1, 0))  # 360° -> back

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

    def test_debug_2d_set_contains_large_shape_categories(self):
        shapes = get_debug_rectangles_2d(board_dims=(10, 20))
        names = {shape.name for shape in shapes}
        self.assertSetEqual(
            names,
            {
                "DBG_LONG_1D",
                "DBG_LONG_2D",
                "DBG_SURFACE_FLAT",
                "DBG_SURFACE_THICK",
            },
        )

    def test_debug_2d_shapes_scale_with_board_size(self):
        small_shapes = get_debug_rectangles_2d(board_dims=(6, 12))
        large_shapes = get_debug_rectangles_2d(board_dims=(14, 28))
        small_counts = {shape.name: len(shape.blocks) for shape in small_shapes}
        large_counts = {shape.name: len(shape.blocks) for shape in large_shapes}

        self.assertGreater(large_counts["DBG_LONG_1D"], small_counts["DBG_LONG_1D"])
        self.assertGreater(
            large_counts["DBG_SURFACE_THICK"], small_counts["DBG_SURFACE_THICK"]
        )

    def test_all_2d_piece_sets_have_no_zero_sized_pieces(self):
        for piece_set in PIECE_SET_2D_OPTIONS:
            shapes = get_piece_bag_2d(piece_set, board_dims=(10, 20))
            self.assertTrue(shapes, f"empty bag for 2D set: {piece_set}")
            for shape in shapes:
                self.assertTrue(
                    shape.blocks, f"empty shape blocks: {piece_set}/{shape.name}"
                )
                xs = [block[0] for block in shape.blocks]
                ys = [block[1] for block in shape.blocks]
                self.assertGreaterEqual(
                    max(xs) - min(xs) + 1, 1, f"zero x-span: {piece_set}/{shape.name}"
                )
                self.assertGreaterEqual(
                    max(ys) - min(ys) + 1, 1, f"zero y-span: {piece_set}/{shape.name}"
                )


if __name__ == "__main__":
    unittest.main()
