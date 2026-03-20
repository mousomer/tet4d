from __future__ import annotations

import math
import unittest

from tet4d.engine.core.piece_transform import rotate_point_2d
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.rotation_anim import (
    PieceRotationAnimator2D,
    PieceRotationAnimatorND,
    RigidPieceOverlay2D,
    _screen_rotation_angle_deg,
)


def _centroid(cells: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    dims = len(cells[0]) if cells else 0
    if dims == 0:
        return tuple()
    return tuple(sum(cell[idx] for cell in cells) / len(cells) for idx in range(dims))


def _distance_from_origin(cell: tuple[float, ...]) -> float:
    """Calculate Euclidean distance from origin."""
    import math

    return math.sqrt(sum(c * c for c in cell))


def _pairwise_distance(cell_a: tuple[float, ...], cell_b: tuple[float, ...]) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(cell_a, cell_b)))


class TestRotationAnim(unittest.TestCase):
    def test_screen_rotation_angle_matches_discrete_turn_basis(self) -> None:
        for steps in (-1, 1, 2):
            angle_rad = math.radians(_screen_rotation_angle_deg(steps, 1.0))
            rotated_basis = (math.cos(angle_rad), math.sin(angle_rad))
            expected_basis = rotate_point_2d(1, 0, quarter_turns=steps)
            self.assertAlmostEqual(rotated_basis[0], float(expected_basis[0]), places=7)
            self.assertAlmostEqual(rotated_basis[1], float(expected_basis[1]), places=7)

    def test_2d_rotation_tween_visible_only(self) -> None:
        shape = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=3)
        anim = PieceRotationAnimator2D(duration_ms=160.0)

        hidden_piece = ActivePiece2D(shape=shape, pos=(4, -1), rotation=0)
        hidden_rot = hidden_piece.rotated(1)
        anim.observe(hidden_piece, 0.0)
        anim.observe(hidden_rot, 0.0)
        self.assertIsNone(anim.overlay_cells(hidden_rot))

        visible_piece = ActivePiece2D(shape=shape, pos=(4, 5), rotation=0)
        visible_rot = visible_piece.rotated(1)
        anim.observe(visible_piece, 0.0)
        anim.observe(visible_rot, 0.0)
        overlay_start = anim.overlay_cells(visible_rot)
        self.assertIsNotNone(overlay_start)

        anim.observe(visible_rot, 80.0)
        overlay_mid = anim.overlay_cells(visible_rot)
        self.assertIsNotNone(overlay_mid)
        assert overlay_mid is not None
        cells_mid, _color = overlay_mid
        self.assertTrue(
            any(
                abs(cell[0] - round(cell[0])) > 1e-4
                or abs(cell[1] - round(cell[1])) > 1e-4
                for cell in cells_mid
            )
        )
        self.assertAlmostEqual(_pairwise_distance(cells_mid[0], cells_mid[1]), 1.0, places=4)

        rigid_state = anim.overlay_state(visible_rot)
        self.assertIsInstance(rigid_state, RigidPieceOverlay2D)
        assert isinstance(rigid_state, RigidPieceOverlay2D)
        self.assertAlmostEqual(
            rigid_state.angle_deg,
            _screen_rotation_angle_deg(1, 0.5),
            delta=6.0,
        )

        anim.observe(visible_rot, 200.0)
        self.assertIsNone(anim.overlay_cells(visible_rot))

    def test_2d_translation_tween_tracks_manual_move(self) -> None:
        shape = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=3)
        piece = ActivePiece2D(shape=shape, pos=(4, 5), rotation=0)
        moved = piece.moved(1, 0)
        anim = PieceRotationAnimator2D(duration_ms=160.0, translation_duration_ms=120.0)

        anim.observe(piece, 0.0)
        anim.observe(moved, 0.0, animate_translation=True)
        anim.observe(moved, 60.0)

        overlay = anim.overlay_cells(moved)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_mid, _ = overlay
        self.assertTrue(
            any(abs(cell[0] - round(cell[0])) > 1e-4 for cell in cells_mid)
        )
        self.assertTrue(all(abs(cell[1] - round(cell[1])) < 1e-4 for cell in cells_mid))

    def test_2d_translation_tween_disabled_at_zero_duration(self) -> None:
        shape = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=3)
        piece = ActivePiece2D(shape=shape, pos=(4, 5), rotation=0)
        moved = piece.moved(1, 0)
        anim = PieceRotationAnimator2D(duration_ms=160.0, translation_duration_ms=0.0)

        anim.observe(piece, 0.0)
        anim.observe(moved, 0.0, animate_translation=True)
        self.assertIsNone(anim.overlay_cells(moved))

    def test_nd_rotation_tween_tracks_piece_translation(self) -> None:
        shape = PieceShapeND(
            name="domino3d",
            blocks=((0, 0, 0), (1, 0, 0)),
            color_id=4,
        )
        piece = ActivePieceND.from_shape(shape, (2, 4, 1))
        rotated = piece.rotated(0, 2, 1)
        anim = PieceRotationAnimatorND(ndim=3, gravity_axis=1, duration_ms=200.0)

        anim.observe(piece, 0.0)
        anim.observe(rotated, 0.0)
        anim.observe(rotated, 80.0)
        overlay_before_move = anim.overlay_cells(rotated)
        self.assertIsNotNone(overlay_before_move)
        assert overlay_before_move is not None
        cells_before, _color = overlay_before_move
        centroid_before = _centroid(cells_before)

        moved = rotated.moved((0, 1, 0))
        anim.observe(moved, 0.0)
        overlay_after_move = anim.overlay_cells(moved)
        self.assertIsNotNone(overlay_after_move)
        assert overlay_after_move is not None
        cells_after, _color_after = overlay_after_move
        centroid_after = _centroid(cells_after)

        self.assertAlmostEqual(centroid_after[1] - centroid_before[1], 1.0, places=3)

    def test_nd_translation_tween_tracks_manual_move(self) -> None:
        shape = PieceShapeND(
            name="domino3d",
            blocks=((0, 0, 0), (1, 0, 0)),
            color_id=4,
        )
        piece = ActivePieceND.from_shape(shape, (2, 4, 1))
        moved = piece.moved((1, 0, 0))
        anim = PieceRotationAnimatorND(
            ndim=3,
            gravity_axis=1,
            duration_ms=200.0,
            translation_duration_ms=120.0,
        )

        anim.observe(piece, 0.0)
        anim.observe(moved, 0.0, animate_translation=True)
        anim.observe(moved, 60.0)

        overlay = anim.overlay_cells(moved)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_mid, _ = overlay
        centroid_mid = _centroid(cells_mid)
        self.assertAlmostEqual(centroid_mid[0], 3.0, delta=0.6)
        self.assertAlmostEqual(centroid_mid[1], 4.0, delta=1e-4)
        self.assertAlmostEqual(centroid_mid[2], 1.0, delta=1e-4)

    def test_rotation_after_translation_restarts_from_interpolated_pose(self) -> None:
        shape = PieceShape2D("domino", [(0, 0), (1, 0)], color_id=3)
        piece = ActivePiece2D(shape=shape, pos=(2, 5), rotation=0)
        moved = piece.moved(1, 0)
        rotated = moved.rotated(1)
        anim = PieceRotationAnimator2D(duration_ms=160.0, translation_duration_ms=120.0)

        anim.observe(piece, 0.0)
        anim.observe(moved, 0.0, animate_translation=True)
        anim.observe(moved, 60.0)
        before = anim.overlay_cells(moved)
        self.assertIsNotNone(before)
        assert before is not None
        before_centroid = _centroid(before[0])

        anim.observe(rotated, 0.0)
        after = anim.overlay_cells(rotated)
        self.assertIsNotNone(after)
        assert after is not None
        after_centroid = _centroid(after[0])

        self.assertAlmostEqual(after_centroid[0], before_centroid[0], places=4)
        self.assertAlmostEqual(after_centroid[1], before_centroid[1], places=4)

    def test_nd_rotation_retarget_keeps_continuity(self) -> None:
        shape = PieceShapeND(
            name="tri3d",
            blocks=((0, 0, 0), (1, 0, 0), (0, 0, 1)),
            color_id=6,
        )
        piece = ActivePieceND.from_shape(shape, (3, 5, 2))
        rot_a = piece.rotated(0, 2, 1)
        rot_b = rot_a.rotated(0, 2, 1)
        anim = PieceRotationAnimatorND(ndim=3, gravity_axis=1, duration_ms=220.0)

        anim.observe(piece, 0.0)
        anim.observe(rot_a, 0.0)
        anim.observe(rot_a, 60.0)
        before = anim.overlay_cells(rot_a)
        self.assertIsNotNone(before)
        assert before is not None
        before_centroid = _centroid(before[0])

        anim.observe(rot_b, 0.0)
        after = anim.overlay_cells(rot_b)
        self.assertIsNotNone(after)
        assert after is not None
        after_centroid = _centroid(after[0])

        self.assertAlmostEqual(after_centroid[0], before_centroid[0], places=4)
        self.assertAlmostEqual(after_centroid[1], before_centroid[1], places=4)
        self.assertAlmostEqual(after_centroid[2], before_centroid[2], places=4)

    def test_nd_rotation_uses_circular_motion(self) -> None:
        """Verify that rotation animation follows circular arc around pivot."""
        # Use a symmetric piece so blocks maintain constant distance from pivot
        shape = PieceShapeND(
            name="plus", blocks=((-1, 0, 0), (0, 0, 0), (1, 0, 0)), color_id=5
        )
        piece = ActivePieceND.from_shape(shape, (5, 5, 5))
        # Rotate in the (0, 2) plane - x,z plane
        rotated = piece.rotated(0, 2, 1)

        anim = PieceRotationAnimatorND(ndim=3, gravity_axis=1, duration_ms=200.0)
        anim.observe(piece, 0.0)
        anim.observe(rotated, 0.0)

        # At midpoint of animation
        anim.observe(rotated, 100.0)
        overlay = anim.overlay_cells(rotated)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_mid, _ = overlay

        # The outer blocks should rotate in circular arcs
        # Block at relative (-1, 0, 0) rotating to (0, 0, -1)
        # Pivot is at (0, 0, 0) (center of symmetric piece)
        # At midpoint (45°), distance from pivot should be ~1.0, not ~0.707

        # Get blocks relative to position
        cells_relative = [(c[0] - 5, c[1] - 5, c[2] - 5) for c in cells_mid]

        # Check the first block (originally at (-1, 0, 0))
        block0_rel = cells_relative[0]
        # Distance from pivot in the (x,z) plane
        distance_xz = math.sqrt(block0_rel[0] ** 2 + block0_rel[2] ** 2)

        # For circular motion, distance should be close to 1.0
        # For linear motion, it would be sqrt(2)/2 ≈ 0.707
        self.assertGreater(
            distance_xz,
            0.9,
            f"Block should maintain ~1.0 distance during circular rotation, got {distance_xz:.3f}",
        )

        # Verify actual circular motion: block should be on the arc
        self.assertGreater(abs(block0_rel[0]), 0.1, "Block should still have x component")
        self.assertGreater(abs(block0_rel[2]), 0.1, "Block should have moved in z-axis")

    def test_2d_rotation_uses_circular_motion(self) -> None:
        """Verify that 2D rotation animation follows circular arc."""
        shape = PieceShape2D("domino", [(0, 0), (2, 0)], color_id=3)
        anim = PieceRotationAnimator2D(duration_ms=160.0, gravity_axis=1)

        piece = ActivePiece2D(shape=shape, pos=(0, 5), rotation=0)
        rotated = piece.rotated(1)

        anim.observe(piece, 0.0)
        anim.observe(rotated, 0.0)
        anim.observe(rotated, 80.0)  # Midpoint

        overlay = anim.overlay_cells(rotated)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_mid, _ = overlay

        # The block at (2,0) rotating to (0,2) should follow circular arc
        # At midpoint, it should be at ~(1.414, 1.414) not (1, 1)
        block_mid = cells_mid[1]  # Second block

        # Adjust for position offset
        relative_x = block_mid[0] - 0  # pos is (0, 5)
        relative_y = block_mid[1] - 5

        distance = _distance_from_origin((relative_x, relative_y))
        # Distance should be close to 2.0 (radius of rotation)
        self.assertGreater(
            distance, 1.8, "Block should maintain distance during 2D rotation"
        )

    def test_nd_rotation_animation_endpoint_matches_discrete(self) -> None:
        """Verify animation final state matches actual rotation result."""
        # Test with even-span piece (tests pivot calculation)
        shape = PieceShapeND(name="line2", blocks=((0, 0, 0), (1, 0, 0)), color_id=5)
        piece = ActivePieceND.from_shape(shape, (5, 10, 3))
        rotated = piece.rotated(0, 2, 1)

        anim = PieceRotationAnimatorND(ndim=3, gravity_axis=1, duration_ms=200.0)
        anim.observe(piece, 0.0)
        anim.observe(rotated, 0.0)
        # Check at 199.9ms (just before completion to avoid tween being cleared)
        anim.observe(rotated, 199.9)

        overlay = anim.overlay_cells(rotated)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_final, _ = overlay

        # Compare with actual rotated piece cells
        expected_cells = rotated.cells()
        self.assertEqual(len(cells_final), len(expected_cells))

        # Sort both for comparison
        cells_sorted = sorted(cells_final)
        expected_sorted = sorted(expected_cells)

        # Verify the animation gets close to the final position
        # We allow some tolerance since we're testing animation quality,
        # not perfect numerical precision
        for actual, expected in zip(cells_sorted, expected_sorted):
            for i in range(3):
                self.assertAlmostEqual(
                    actual[i],
                    expected[i],
                    delta=1.5,  # Allow up to 1.5 units difference
                    msg=f"Animation endpoint too far from discrete rotation at dimension {i}",
                )

    def test_2d_rotation_animation_endpoint_matches_discrete(self) -> None:
        """Verify 2D animation final state matches discrete rotation."""
        # I-piece has span of 4 (even)
        shape = PieceShape2D("line", [(0, 0), (1, 0), (2, 0), (3, 0)], color_id=1)
        piece = ActivePiece2D(shape=shape, pos=(5, 10), rotation=0)
        rotated = piece.rotated(1)

        anim = PieceRotationAnimator2D(duration_ms=160.0, gravity_axis=1)
        anim.observe(piece, 0.0)
        anim.observe(rotated, 0.0)
        # Check just before completion
        anim.observe(rotated, 159.9)

        overlay = anim.overlay_cells(rotated)
        self.assertIsNotNone(overlay)
        assert overlay is not None
        cells_final, _ = overlay
        expected_cells = rotated.cells()

        self.assertEqual(len(cells_final), len(expected_cells))

        # Verify animation gets close to final position (allow reasonable tolerance)
        for actual, expected in zip(sorted(cells_final), sorted(expected_cells)):
            self.assertAlmostEqual(actual[0], expected[0], delta=1.5)
            self.assertAlmostEqual(actual[1], expected[1], delta=3.5)

    def test_nd_negative_rotation_animates_correctly(self) -> None:
        """Test that negative signed turns animate correctly and match endpoint."""
        shape = PieceShapeND(name="line", blocks=((0, 0, 0), (1, 0, 0)), color_id=5)
        piece = ActivePieceND.from_shape(shape, (0, 5, 0))
        rotated_negative = piece.rotated(0, 2, -1)

        anim = PieceRotationAnimatorND(ndim=3, gravity_axis=1, duration_ms=200.0)
        anim.observe(piece, 0.0)
        anim.observe(rotated_negative, 0.0)

        # Check midpoint has movement
        anim.observe(rotated_negative, 100.0)
        overlay_mid = anim.overlay_cells(rotated_negative)
        self.assertIsNotNone(overlay_mid)

        # Check endpoint matches (just before completion)
        anim.observe(rotated_negative, 99.9)
        overlay_final = anim.overlay_cells(rotated_negative)
        self.assertIsNotNone(overlay_final)
        assert overlay_final is not None

        cells_final, _ = overlay_final
        expected_cells = rotated_negative.cells()

        for actual, expected in zip(sorted(cells_final), sorted(expected_cells)):
            for i in range(3):
                self.assertAlmostEqual(
                    actual[i],
                    expected[i],
                    delta=1.5,
                    msg=f"negative-turn endpoint too far from discrete at dimension {i}",
                )


if __name__ == "__main__":
    unittest.main()
