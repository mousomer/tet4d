import unittest

from tetris_nd.pieces_nd import (
    ActivePieceND,
    PIECE_SET_4D_SIX,
    get_standard_pieces_nd,
    rotate_point_nd,
)


class TestPiecesND(unittest.TestCase):

    def test_rotate_point_nd_xz_plane(self):
        self.assertEqual(rotate_point_nd((1, 0, 0), 0, 2, 1), (0, 0, -1))
        self.assertEqual(rotate_point_nd((1, 0, 0), 0, 2, 2), (-1, 0, 0))
        self.assertEqual(rotate_point_nd((1, 0, 0), 0, 2, 3), (0, 0, 1))

    def test_lifted_shapes_have_expected_dimension(self):
        shapes = get_standard_pieces_nd(4)
        self.assertTrue(shapes)
        for block in shapes[0].blocks:
            self.assertEqual(len(block), 4)

    def test_3d_shapes_include_nonzero_z_blocks(self):
        shapes = get_standard_pieces_nd(3)
        self.assertTrue(
            any(any(block[2] != 0 for block in shape.blocks) for shape in shapes)
        )

    def test_4d_shapes_include_nonzero_w_blocks(self):
        shapes = get_standard_pieces_nd(4)
        self.assertTrue(
            any(any(block[3] != 0 for block in shape.blocks) for shape in shapes)
        )

    def test_4d_shapes_are_dedicated_and_span_all_axes(self):
        shapes = get_standard_pieces_nd(4)
        self.assertTrue(shapes)

        for shape in shapes:
            # Dedicated 4D bag uses 5-cell pieces (not lifted 2D/3D tetrominoes).
            self.assertEqual(len(shape.blocks), 5)

            axis_values = [set() for _ in range(4)]
            for block in shape.blocks:
                for axis in range(4):
                    axis_values[axis].add(block[axis])

            # Each shape varies along x, y, z, and w.
            self.assertTrue(all(len(values) > 1 for values in axis_values))

    def test_5d_shapes_embed_4d_set_with_zero_extra_axis(self):
        shapes_4d = get_standard_pieces_nd(4)
        shapes_5d = get_standard_pieces_nd(5)

        self.assertEqual([shape.name for shape in shapes_4d],
                         [shape.name for shape in shapes_5d])

        self.assertTrue(
            any(any(block[3] != 0 for block in shape.blocks) for shape in shapes_5d)
        )
        self.assertTrue(
            all(block[4] == 0 for shape in shapes_5d for block in shape.blocks)
        )

    def test_4d_six_cell_set_spans_all_axes(self):
        shapes = get_standard_pieces_nd(4, piece_set_4d=PIECE_SET_4D_SIX)
        self.assertTrue(shapes)

        for shape in shapes:
            self.assertEqual(len(shape.blocks), 6)

            axis_values = [set() for _ in range(4)]
            for block in shape.blocks:
                for axis in range(4):
                    axis_values[axis].add(block[axis])
            self.assertTrue(all(len(values) > 1 for values in axis_values))

    def test_5d_shapes_embed_selected_4d_set_with_zero_extra_axis(self):
        shapes_4d = get_standard_pieces_nd(4, piece_set_4d=PIECE_SET_4D_SIX)
        shapes_5d = get_standard_pieces_nd(5, piece_set_4d=PIECE_SET_4D_SIX)

        self.assertEqual([shape.name for shape in shapes_4d], [shape.name for shape in shapes_5d])
        self.assertTrue(all(len(shape.blocks) == 6 for shape in shapes_5d))
        self.assertTrue(all(block[4] == 0 for shape in shapes_5d for block in shape.blocks))

    def test_invalid_4d_piece_set_raises(self):
        with self.assertRaises(ValueError):
            get_standard_pieces_nd(4, piece_set_4d="invalid")

    def test_active_piece_rotation_preserves_non_plane_axis(self):
        shape = get_standard_pieces_nd(3)[0]
        piece = ActivePieceND.from_shape(shape, pos=(4, 0, 2))
        rotated = piece.rotated(axis_a=0, axis_b=2, delta_steps=1)

        self.assertEqual(rotated.pos, piece.pos)
        original_y_values = sorted(block[1] for block in piece.rel_blocks)
        rotated_y_values = sorted(block[1] for block in rotated.rel_blocks)
        self.assertEqual(original_y_values, rotated_y_values)


if __name__ == "__main__":
    unittest.main()
