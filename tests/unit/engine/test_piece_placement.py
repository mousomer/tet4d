from __future__ import annotations

import unittest

from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    validate_candidate_piece_placement,
)


class TestPiecePlacement(unittest.TestCase):
    def test_self_vacated_move_is_valid_atomically(self) -> None:
        source_cells = ((1, 1), (2, 1))
        candidate = build_candidate_piece_placement("domino", ((2, 1), (3, 1)))

        self.assertTrue(
            validate_candidate_piece_placement(
                candidate,
                {coord: 9 for coord in source_cells},
                ignore_cells=source_cells,
            )
        )

    def test_rotation_is_valid_when_only_overlapping_vacated_source_cells(self) -> None:
        source_cells = ((1, 1), (2, 1))
        candidate = build_candidate_piece_placement("domino", ((1, 1), (1, 2)))

        self.assertTrue(
            validate_candidate_piece_placement(
                candidate,
                {coord: 9 for coord in source_cells},
                ignore_cells=source_cells,
            )
        )

    def test_genuine_collision_still_fails(self) -> None:
        source_cells = ((1, 1), (2, 1))
        candidate = build_candidate_piece_placement("domino", ((2, 1), (3, 1)))
        board_cells = {coord: 9 for coord in source_cells}
        board_cells[(3, 1)] = 4

        self.assertFalse(
            validate_candidate_piece_placement(
                candidate,
                board_cells,
                ignore_cells=source_cells,
            )
        )


if __name__ == "__main__":
    unittest.main()
