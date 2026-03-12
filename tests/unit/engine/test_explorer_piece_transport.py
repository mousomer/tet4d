from __future__ import annotations

import unittest

from tet4d.engine.gameplay.explorer_piece_transport import (
    CELLWISE_DEFORMATION,
    PLAIN_TRANSLATION,
    RIGID_TRANSFORM,
    classify_explorer_piece_move,
)


class TestExplorerPieceTransport(unittest.TestCase):
    def test_classifies_plain_translation(self) -> None:
        outcome = classify_explorer_piece_move(
            ((2, 3), (3, 3)),
            ((1, 3), (2, 3)),
        )

        self.assertEqual(outcome.kind, PLAIN_TRANSLATION)
        assert outcome.frame_transform is not None
        self.assertEqual(outcome.frame_transform.translation, (-1, 0))
        self.assertTrue(outcome.frame_transform.is_identity_linear())

    def test_classifies_rigid_transform(self) -> None:
        source = ((3, 0), (3, 1))
        moved = ((0, 2), (0, 1))

        outcome = classify_explorer_piece_move(source, moved)

        self.assertEqual(outcome.kind, RIGID_TRANSFORM)
        assert outcome.frame_transform is not None
        self.assertFalse(outcome.frame_transform.is_identity_linear())
        self.assertEqual(
            tuple(outcome.frame_transform.apply_absolute(coord) for coord in source),
            moved,
        )

    def test_classifies_cellwise_deformation(self) -> None:
        outcome = classify_explorer_piece_move(
            ((2, 1), (3, 1)),
            ((3, 1), (0, 1)),
        )

        self.assertEqual(outcome.kind, CELLWISE_DEFORMATION)
        self.assertIsNone(outcome.frame_transform)

    def test_classifies_nd_axis_swap_as_rigid_transform(self) -> None:
        source = ((3, 2, 1, 0), (3, 2, 1, 1))
        moved = ((0, 2, 1, 3), (1, 2, 1, 3))

        outcome = classify_explorer_piece_move(source, moved)

        self.assertEqual(outcome.kind, RIGID_TRANSFORM)
        assert outcome.frame_transform is not None
        self.assertEqual(
            tuple(outcome.frame_transform.apply_absolute(coord) for coord in source),
            moved,
        )


if __name__ == "__main__":
    unittest.main()
