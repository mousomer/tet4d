import unittest
from tetris_nd.board import BoardND

class TestBoard2D(unittest.TestCase):

    def test_inside_bounds_and_can_place(self):
        board = BoardND((10, 20))

        # Inside
        self.assertTrue(board.inside_bounds((0, 0)))
        self.assertTrue(board.inside_bounds((9, 19)))
        self.assertTrue(board.can_place([(0, 0), (9, 19)]))

        # Outside
        self.assertFalse(board.inside_bounds((-1, 0)))
        self.assertFalse(board.inside_bounds((10, 0)))
        self.assertFalse(board.inside_bounds((0, 20)))
        self.assertFalse(board.can_place([(0, 0), (10, 0)]))

        # Occupied cell blocks placement
        board.cells[(3, 5)] = 1
        self.assertFalse(board.can_place([(3, 5)]))
        self.assertFalse(board.can_place([(2, 5), (3, 5)]))
        self.assertTrue(board.can_place([(2, 5)]))

    def test_clear_single_full_row(self):
        # 4x4 board, gravity along y (axis=1)
        board = BoardND((4, 4))

        # Fill bottom row y=3 completely
        for x in range(4):
            board.cells[(x, 3)] = 1

        # Put one cell above at (1, 2)
        board.cells[(1, 2)] = 2

        cleared = board.clear_planes(gravity_axis=1)
        self.assertEqual(cleared, 1)

        # Row y=3 should be gone; the cell from (1,2) should have dropped to (1,3)
        self.assertNotIn((1, 2), board.cells)
        self.assertEqual(board.cells.get((1, 3)), 2)
        self.assertEqual(len(board.cells), 1)

    def test_clear_multiple_rows(self):
        board = BoardND((3, 4))  # width=3, height=4

        # Fill rows y=1 and y=3 completely
        for x in range(3):
            board.cells[(x, 1)] = 1
            board.cells[(x, 3)] = 1

        # Single cell at (0, 0) and (2, 2)
        board.cells[(0, 0)] = 2
        board.cells[(2, 2)] = 3

        cleared = board.clear_planes(gravity_axis=1)
        self.assertEqual(cleared, 2)

        # All full rows removed, other cells shifted down appropriately
        # We can just check that no row is completely full anymore and that count is 2
        self.assertEqual(len(board.cells), 2)
        for (x, y), v in board.cells.items():
            self.assertIn(x, range(3))
            self.assertIn(y, range(4))


if __name__ == "__main__":
    unittest.main()
