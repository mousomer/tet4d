from __future__ import annotations

import unittest

import pygame

from tet4d.ui.pygame.render.control_helper import control_groups_for_dimension
from tet4d.ui.pygame.render.panel_utils import (
    _append_stats_group,
    _compute_controls_rect,
    _stats_group_rows,
    _join_sections,
    _merge_summary_into_main_group,
)
from tet4d.ui.pygame.ui_utils import text_fits, wrap_text_lines


class TestPanelUtils(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

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

    def test_side_panel_controls_rect_stays_inside_panel(self) -> None:
        panel_rect = pygame.Rect(1040, 20, 200, 680)
        controls_rect = _compute_controls_rect(
            panel_rect=panel_rect,
            controls_top=120,
            reserve_bottom=26,
        )
        self.assertGreaterEqual(controls_rect.left, panel_rect.left)
        self.assertGreaterEqual(controls_rect.top, 120)
        self.assertLessEqual(controls_rect.right, panel_rect.right)
        self.assertLessEqual(controls_rect.bottom, panel_rect.bottom - 26)

    def test_side_panel_summary_lines_fit_standard_panel_width(self) -> None:
        panel_font = pygame.font.Font(None, 20)
        # draw_grouped_control_helper renders summary rows inside a box with 10px
        # horizontal margin on a panel-width-constrained lane.
        max_width = 200 - 24
        for line in ("2D Tetris", "Score: 123456", "Lines: 99", "Speed level: 10"):
            with self.subTest(line=line):
                self.assertTrue(text_fits(panel_font, line, max_width))

    def test_wrap_text_lines_preserve_words_within_budget(self) -> None:
        font = pygame.font.Font(None, 22)
        wrapped = wrap_text_lines(
            font,
            "Move X Left / Right  Move Y Up / Down",
            max_width=130,
        )
        self.assertGreater(len(wrapped), 1)
        for line in wrapped:
            with self.subTest(line=line):
                self.assertTrue(text_fits(font, line, 130))


if __name__ == "__main__":
    unittest.main()
