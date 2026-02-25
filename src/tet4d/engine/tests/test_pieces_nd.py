import unittest
import random

from tet4d.engine.pieces_nd import (
    ActivePieceND,
    PIECE_SET_4D_OPTIONS,
    PIECE_SET_3D_OPTIONS,
    PIECE_SET_3D_DEBUG,
    PIECE_SET_3D_EMBED_2D,
    PIECE_SET_3D_RANDOM,
    PIECE_SET_4D_DEBUG,
    PIECE_SET_4D_EMBED_2D,
    PIECE_SET_4D_EMBED_3D,
    PIECE_SET_4D_RANDOM,
    PIECE_SET_4D_SIX,
    get_piece_shapes_nd,
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

    def test_3d_embedded_2d_shapes_have_zero_z(self):
        shapes = get_piece_shapes_nd(3, piece_set_id=PIECE_SET_3D_EMBED_2D)
        self.assertTrue(shapes)
        self.assertTrue(
            all(block[2] == 0 for shape in shapes for block in shape.blocks)
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

        self.assertEqual(
            [shape.name for shape in shapes_4d], [shape.name for shape in shapes_5d]
        )

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

        self.assertEqual(
            [shape.name for shape in shapes_4d], [shape.name for shape in shapes_5d]
        )
        self.assertTrue(all(len(shape.blocks) == 6 for shape in shapes_5d))
        self.assertTrue(
            all(block[4] == 0 for shape in shapes_5d for block in shape.blocks)
        )

    def test_4d_embedded_3d_shapes_have_zero_w(self):
        shapes = get_piece_shapes_nd(4, piece_set_id=PIECE_SET_4D_EMBED_3D)
        self.assertTrue(shapes)
        self.assertTrue(
            any(any(block[2] != 0 for block in shape.blocks) for shape in shapes)
        )
        self.assertTrue(
            all(block[3] == 0 for shape in shapes for block in shape.blocks)
        )

    def test_4d_embedded_2d_shapes_have_zero_z_and_w(self):
        shapes = get_piece_shapes_nd(4, piece_set_id=PIECE_SET_4D_EMBED_2D)
        self.assertTrue(shapes)
        self.assertTrue(
            all(
                block[2] == 0 and block[3] == 0
                for shape in shapes
                for block in shape.blocks
            )
        )

    def test_invalid_4d_piece_set_raises(self):
        with self.assertRaises(ValueError):
            get_standard_pieces_nd(4, piece_set_4d="invalid")

    def test_random_piece_sets_are_seed_deterministic(self):
        rng_a = random.Random(1337)
        rng_b = random.Random(1337)

        shapes_3d_a = get_piece_shapes_nd(
            3, piece_set_id=PIECE_SET_3D_RANDOM, rng=rng_a
        )
        shapes_3d_b = get_piece_shapes_nd(
            3, piece_set_id=PIECE_SET_3D_RANDOM, rng=rng_b
        )
        self.assertEqual(
            [shape.blocks for shape in shapes_3d_a],
            [shape.blocks for shape in shapes_3d_b],
        )

        rng_c = random.Random(9001)
        rng_d = random.Random(9001)
        shapes_4d_a = get_piece_shapes_nd(
            4, piece_set_id=PIECE_SET_4D_RANDOM, rng=rng_c
        )
        shapes_4d_b = get_piece_shapes_nd(
            4, piece_set_id=PIECE_SET_4D_RANDOM, rng=rng_d
        )
        self.assertEqual(
            [shape.blocks for shape in shapes_4d_a],
            [shape.blocks for shape in shapes_4d_b],
        )

    def test_active_piece_rotation_preserves_non_plane_axis(self):
        shape = get_standard_pieces_nd(3)[0]
        piece = ActivePieceND.from_shape(shape, pos=(4, 0, 2))
        rotated = piece.rotated(axis_a=0, axis_b=2, delta_steps=1)

        self.assertEqual(rotated.pos, piece.pos)
        original_y_values = sorted(block[1] for block in piece.rel_blocks)
        rotated_y_values = sorted(block[1] for block in rotated.rel_blocks)
        self.assertEqual(original_y_values, rotated_y_values)

    def test_debug_3d_set_contains_large_shape_categories(self):
        shapes = get_piece_shapes_nd(
            3,
            piece_set_id=PIECE_SET_3D_DEBUG,
            board_dims=(10, 20, 6),
        )
        names = {shape.name for shape in shapes}
        self.assertSetEqual(
            names,
            {
                "DBG_LONG_1D",
                "DBG_LONG_2D",
                "DBG_LONG_3D",
                "DBG_SURFACE_FLAT",
                "DBG_SURFACE_THICK",
            },
        )

    def test_debug_4d_set_contains_requested_categories(self):
        shapes = get_piece_shapes_nd(
            4,
            piece_set_id=PIECE_SET_4D_DEBUG,
            board_dims=(10, 20, 6, 4),
        )
        names = {shape.name for shape in shapes}
        self.assertSetEqual(
            names,
            {
                "DBG_LONG_1D",
                "DBG_LONG_2D",
                "DBG_LONG_3D",
                "DBG_LONG_4D",
                "DBG_SURFACE_FLAT",
                "DBG_SURFACE_THICK",
                "DBG_LAYER_4D",
            },
        )

    def test_debug_4d_shapes_scale_with_board_size(self):
        small_shapes = get_piece_shapes_nd(
            4,
            piece_set_id=PIECE_SET_4D_DEBUG,
            board_dims=(6, 12, 4, 3),
        )
        large_shapes = get_piece_shapes_nd(
            4,
            piece_set_id=PIECE_SET_4D_DEBUG,
            board_dims=(12, 24, 8, 6),
        )
        small_counts = {shape.name: len(shape.blocks) for shape in small_shapes}
        large_counts = {shape.name: len(shape.blocks) for shape in large_shapes}

        self.assertGreater(large_counts["DBG_LONG_1D"], small_counts["DBG_LONG_1D"])
        self.assertGreater(
            large_counts["DBG_SURFACE_FLAT"], small_counts["DBG_SURFACE_FLAT"]
        )
        self.assertGreater(large_counts["DBG_LAYER_4D"], small_counts["DBG_LAYER_4D"])

    def test_all_3d_piece_sets_have_no_zero_sized_pieces(self):
        for piece_set in PIECE_SET_3D_OPTIONS:
            shapes = get_piece_shapes_nd(
                3, piece_set_id=piece_set, board_dims=(10, 20, 6)
            )
            self.assertTrue(shapes, f"empty bag for 3D set: {piece_set}")
            for shape in shapes:
                self.assertTrue(
                    shape.blocks, f"empty shape blocks: {piece_set}/{shape.name}"
                )
                spans = []
                for axis in range(3):
                    values = [block[axis] for block in shape.blocks]
                    spans.append(max(values) - min(values) + 1)
                self.assertTrue(
                    all(span >= 1 for span in spans),
                    f"zero span in 3D set: {piece_set}/{shape.name}",
                )

    def test_all_4d_piece_sets_have_no_zero_sized_pieces(self):
        for piece_set in PIECE_SET_4D_OPTIONS:
            shapes = get_piece_shapes_nd(
                4, piece_set_id=piece_set, board_dims=(10, 20, 6, 4)
            )
            self.assertTrue(shapes, f"empty bag for 4D set: {piece_set}")
            for shape in shapes:
                self.assertTrue(
                    shape.blocks, f"empty shape blocks: {piece_set}/{shape.name}"
                )
                spans = []
                for axis in range(4):
                    values = [block[axis] for block in shape.blocks]
                    spans.append(max(values) - min(values) + 1)
                self.assertTrue(
                    all(span >= 1 for span in spans),
                    f"zero span in 4D set: {piece_set}/{shape.name}",
                )


if __name__ == "__main__":
    unittest.main()
