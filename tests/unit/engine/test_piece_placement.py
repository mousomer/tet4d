from __future__ import annotations

import unittest

from tet4d.engine.core.rules.piece_placement import (
    build_candidate_piece_placement,
    commit_piece_if_legal,
    piece_placement_is_legal,
    validate_candidate_piece_placement,
)


class TestPiecePlacement(unittest.TestCase):
    def test_shared_legality_is_dimension_agnostic(self) -> None:
        cases = (
            (((1, 1), (2, 1)), {(3, 1): 9}, True),
            (((2, 1), (3, 1)), {(3, 1): 9}, False),
            (((1, 1, 0), (2, 1, 0)), {(3, 1, 0): 9}, True),
            (((2, 1, 0), (3, 1, 0)), {(3, 1, 0): 9}, False),
        )

        for cells, board_cells, expected in cases:
            with self.subTest(cells=cells):
                self.assertEqual(
                    piece_placement_is_legal("piece", cells, board_cells),
                    expected,
                )

    def test_shared_commit_is_atomic_when_candidate_collides(self) -> None:
        class _State:
            current_piece = "original"

        state = _State()

        self.assertFalse(
            commit_piece_if_legal(
                state,
                "blocked",
                ((2, 1), (3, 1)),
                {(3, 1): 9},
            )
        )
        self.assertEqual(state.current_piece, "original")
        self.assertTrue(
            commit_piece_if_legal(
                state,
                "moved",
                ((1, 1), (2, 1)),
                {(3, 1): 9},
            )
        )
        self.assertEqual(state.current_piece, "moved")

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
