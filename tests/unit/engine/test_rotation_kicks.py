from __future__ import annotations

import unittest

from tet4d.engine.core.rotation_kicks import (
    kick_candidate_vectors,
    normalize_kick_level_name,
    resolve_kicked_candidate,
)


class TestRotationKicks(unittest.TestCase):
    def test_kick_candidate_vectors_filter_positive_gravity_offsets(self) -> None:
        self.assertEqual(
            kick_candidate_vectors(
                ndim=2,
                axis_a=0,
                axis_b=1,
                gravity_axis=1,
                plane_offsets=((1, 0), (-1, 0), (0, 1), (0, -1)),
            ),
            ((1, 0), (-1, 0), (0, -1)),
        )

    def test_normalize_kick_level_name_falls_back(self) -> None:
        self.assertEqual(
            normalize_kick_level_name("weird", allowed_levels=("off", "light")),
            "off",
        )

    def test_resolve_kicked_candidate_uses_first_legal_offset(self) -> None:
        rotated_piece = (0, 0)
        candidate = resolve_kicked_candidate(
            rotated_piece,
            candidate_vectors=((1, 0), (-1, 0), (0, -1)),
            move_piece=lambda piece, vector: (piece[0] + vector[0], piece[1] + vector[1]),
            can_place=lambda piece: piece == (-1, 0),
        )
        self.assertEqual(candidate, (-1, 0))


if __name__ == "__main__":
    unittest.main()
