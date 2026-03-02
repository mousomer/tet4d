from __future__ import annotations

import unittest

from tet4d.ui.pygame.render.control_helper import control_groups_for_dimension
from tet4d.ui.pygame.render.panel_utils import (
    _append_stats_group,
    _stats_group_rows,
    _join_sections,
    _merge_summary_into_main_group,
)


class TestPanelUtils(unittest.TestCase):
    def test_merge_summary_into_existing_main_group(self) -> None:
        groups = [("Main", ("A\tpause menu\t",)), ("Translation", ("B\tmove x\t",))]
        merged = _merge_summary_into_main_group(
            header_lines=("2D Tetris", "Score: 12", "Lines: 3", "Speed level: 1"),
            control_groups=groups,
        )
        main_rows = merged[0][1]
        self.assertTrue(main_rows[0].startswith("\t2D Tetris\t"))
        self.assertTrue(main_rows[1].startswith("\tScore: 12\t"))
        self.assertEqual(main_rows[-1], "A\tpause menu\t")

    def test_merge_summary_creates_main_when_missing(self) -> None:
        groups = [("Translation", ("B\tmove x\t",))]
        merged = _merge_summary_into_main_group(
            header_lines=("3D Tetris", "Score: 100"),
            control_groups=groups,
        )
        self.assertEqual(merged[0][0], "Main")
        self.assertEqual(merged[1][0], "Translation")
        self.assertTrue(merged[0][1][0].startswith("\t3D Tetris\t"))

    def test_side_panel_line_builders(self) -> None:
        header_lines = ("4D Tetris", "Score: 240", "Lines: 11", "Speed level: 3")
        low_lines = _join_sections(
            ("Dims: (10, 20, 6, 4)", "Score mod: x1.25"),
            ("Bot: OFF",),
            ("Trend: stable",),
        )
        self.assertEqual(
            header_lines,
            ("4D Tetris", "Score: 240", "Lines: 11", "Speed level: 3"),
        )
        self.assertEqual(
            low_lines,
            (
                "Dims: (10, 20, 6, 4)",
                "Score mod: x1.25",
                "",
                "Bot: OFF",
                "",
                "Trend: stable",
            ),
        )

    def test_stats_group_rows_use_group_row_shape(self) -> None:
        rows = _stats_group_rows(("Dims: (10, 20)", "", "Score mod: x1.25"))
        self.assertEqual(
            rows,
            (
                "\tDims: (10, 20)\t",
                "\t\t",
                "\tScore mod: x1.25\t",
            ),
        )

    def test_stats_group_rows_placeholder_when_empty(self) -> None:
        self.assertEqual(_stats_group_rows(tuple()), ("\tno runtime stats\t",))

    def test_append_stats_group_always_adds_stats_panel(self) -> None:
        groups = [("Main", ("A\tpause menu\t",))]
        with_stats = _append_stats_group(control_groups=groups, stats_lines=tuple())
        self.assertEqual(with_stats[-1][0], "Stats")
        self.assertEqual(with_stats[-1][1], ("\tno runtime stats\t",))

    def test_all_modes_use_same_group_skeleton_with_stats(self) -> None:
        for dim in (2, 3, 4):
            groups = _append_stats_group(
                control_groups=control_groups_for_dimension(
                    dim, unified_structure=True
                ),
                stats_lines=tuple(),
            )
            self.assertEqual(
                [name for name, _ in groups],
                ["Main", "Translation", "Rotation", "Camera", "Stats"],
            )


if __name__ == "__main__":
    unittest.main()
