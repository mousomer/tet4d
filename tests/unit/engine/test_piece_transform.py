import unittest

from tet4d.engine import api as engine_api
from tet4d.engine.core.piece_transform import (
    block_axis_bounds,
    canonicalize_blocks_2d,
    canonicalize_blocks_nd,
    enumerate_orientations_nd,
    normalize_blocks_2d,
    rotate_blocks_2d,
    rotate_blocks_nd,
    rotate_point_2d,
    rotate_point_nd,
    rotation_planes_nd,
)


class TestPieceTransform(unittest.TestCase):
    def test_rotate_blocks_2d_keeps_square_stable(self) -> None:
        blocks = ((0, 0), (1, 0), (0, 1), (1, 1))
        self.assertEqual(
            canonicalize_blocks_2d(rotate_blocks_2d(blocks, 1)),
            canonicalize_blocks_2d(blocks),
        )

    def test_rotate_blocks_2d_even_span_line_uses_between_cell_axis(self) -> None:
        blocks = ((-1, 0), (0, 0), (1, 0), (2, 0))
        self.assertEqual(
            canonicalize_blocks_2d(rotate_blocks_2d(blocks, 1)),
            ((0, -1), (0, 0), (0, 1), (0, 2)),
        )

    def test_normalize_blocks_2d_preserves_current_local_anchor(self) -> None:
        blocks = ((0, 0), (1, 0), (2, 0), (3, 0))
        self.assertEqual(
            normalize_blocks_2d(blocks),
            ((-1, 0), (0, 0), (1, 0), (2, 0)),
        )

    def test_canonicalize_blocks_2d_sorts_coords(self) -> None:
        self.assertEqual(
            canonicalize_blocks_2d(((2, 0), (0, 0), (1, 0))),
            ((0, 0), (1, 0), (2, 0)),
        )

    def test_block_axis_bounds_nd_returns_min_and_max_per_axis(self) -> None:
        blocks = ((2, -1, 4), (0, 3, 1), (1, 1, 5))
        self.assertEqual(block_axis_bounds(blocks), ((0, -1, 1), (2, 3, 5)))

    def test_rotate_blocks_nd_uses_active_plane_center(self) -> None:
        blocks = ((0, 0, 0), (1, 0, 0))
        self.assertEqual(
            canonicalize_blocks_nd(rotate_blocks_nd(blocks, 0, 2, 1)),
            ((0, 0, 0), (0, 0, 1)),
        )

    def test_rotation_planes_nd_matches_current_3d_order(self) -> None:
        self.assertEqual(rotation_planes_nd(3, 1), ((0, 1), (0, 2), (1, 2)))

    def test_enumerate_orientations_nd_preserves_domino_orientation_set(self) -> None:
        start = canonicalize_blocks_nd(((0, 0, 0), (1, 0, 0)))
        orientations = enumerate_orientations_nd(start, ndim=3, gravity_axis=1)
        self.assertEqual(
            orientations,
            (
                ((0, 0, 0), (1, 0, 0)),
                ((0, 0, 0), (0, 1, 0)),
                ((0, 0, 0), (0, 0, 1)),
            ),
        )

    def test_rotate_point_primitives_remain_origin_based(self) -> None:
        self.assertEqual(rotate_point_2d(1, 0, 1), (0, -1))
        self.assertEqual(rotate_point_nd((1, 0, 0), 0, 2, 1), (0, 0, -1))

    def test_engine_api_exports_transform_helpers(self) -> None:
        blocks_2d = ((0, 0), (1, 0), (1, 1))
        blocks_nd = ((0, 0, 0), (1, 0, 0))
        self.assertEqual(
            engine_api.rotate_blocks_2d(blocks_2d, 1),
            rotate_blocks_2d(blocks_2d, 1),
        )
        self.assertEqual(
            engine_api.canonicalize_blocks_nd(blocks_nd),
            canonicalize_blocks_nd(blocks_nd),
        )
        self.assertEqual(
            engine_api.enumerate_orientations_nd(
                canonicalize_blocks_nd(blocks_nd),
                3,
                1,
            ),
            enumerate_orientations_nd(canonicalize_blocks_nd(blocks_nd), 3, 1),
        )


if __name__ == "__main__":
    unittest.main()
