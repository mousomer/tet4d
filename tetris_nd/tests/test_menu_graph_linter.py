from __future__ import annotations

import unittest

from tetris_nd.menu_graph_linter import lint_menu_graph


class TestMenuGraphLinter(unittest.TestCase):
    def test_menu_graph_lint_passes(self) -> None:
        issues = lint_menu_graph()
        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()
