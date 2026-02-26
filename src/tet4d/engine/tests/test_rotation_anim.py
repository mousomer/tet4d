from __future__ import annotations

import unittest

from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimator2D, PieceRotationAnimatorND


def _centroid(cells: tuple[tuple[float, ...], ...]) -> tuple[float, ...]:
    dims = len(cells[0]) if cells else 0
    if dims == 0:
        return tuple()
    return tuple(sum(cell[idx] for cell in cells) / len(cells) for idx in range(dims))


class TestRotationAnim(unittest.TestCase):
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

        anim.observe(visible_rot, 200.0)
        self.assertIsNone(anim.overlay_cells(visible_rot))

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


if __name__ == "__main__":
    unittest.main()
