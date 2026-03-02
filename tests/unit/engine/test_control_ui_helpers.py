from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment guard
    raise unittest.SkipTest("pygame-ce is required for control helper tests") from exc

from tet4d.ui.pygame.render.control_helper import (
    _planned_group_rows,
    control_groups_for_dimension,
)
from tet4d.ui.pygame.render.control_icons import (
    action_icon_cache_size,
    clear_action_icon_cache,
    draw_action_icon,
)


class TestControlIconCaching(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        clear_action_icon_cache()

    def test_icon_cache_reuses_surface_for_same_action_and_size(self) -> None:
        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        rect = pygame.Rect(8, 8, 20, 20)
        draw_action_icon(surface, rect=rect, action="move_x_pos")
        first_size = action_icon_cache_size()
        draw_action_icon(surface, rect=rect, action="move_x_pos")
        self.assertEqual(first_size, action_icon_cache_size())
        self.assertEqual(first_size, 1)

    def test_icon_cache_tracks_size_variants(self) -> None:
        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        draw_action_icon(
            surface, rect=pygame.Rect(8, 8, 20, 20), action="rotate_xy_pos"
        )
        draw_action_icon(
            surface, rect=pygame.Rect(8, 8, 26, 26), action="rotate_xy_pos"
        )
        self.assertEqual(action_icon_cache_size(), 2)

    def test_invalid_action_does_not_create_cache_entry(self) -> None:
        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        draw_action_icon(
            surface, rect=pygame.Rect(8, 8, 20, 20), action="unknown_action"
        )
        self.assertEqual(action_icon_cache_size(), 0)


class TestControlGroups(unittest.TestCase):
    def test_dim2_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(2)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Main", "Translation", "Rotation"])
        self.assertEqual([len(rows) for _, rows in groups], [5, 4, 1])
        main_rows = groups[0][1]
        translation_rows = groups[1][1]
        self.assertIn("\tpause menu\t", main_rows[0])
        self.assertIn("\thelp\t", main_rows[1])
        self.assertIn("\trestart\t", main_rows[2])
        self.assertTrue(any("\tmove x\t" in row for row in translation_rows))
        self.assertTrue(any("\thard drop\t" in row for row in translation_rows))

    def test_dim3_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(3)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Main", "Translation", "Rotation", "Camera"])
        self.assertEqual([len(rows) for _, rows in groups], [5, 5, 3, 7])
        main_rows = groups[0][1]
        camera_rows = groups[3][1]
        self.assertTrue(any("\thelp\t" in row for row in main_rows))
        self.assertTrue(any("\tpause menu\t" in row for row in main_rows))
        self.assertTrue(any("\trestart\t" in row for row in main_rows))
        self.assertTrue(any("\tprojection\t" in row for row in camera_rows))
        self.assertTrue(
            any("\tlocked cells alpha [,]\t" in row for row in camera_rows)
        )

    def test_dim4_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(4)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Main", "Translation", "Rotation", "Camera"])
        self.assertEqual([len(rows) for _, rows in groups], [5, 6, 6, 8])
        main_rows = groups[0][1]
        translation_rows = groups[1][1]
        camera_rows = groups[3][1]
        self.assertTrue(any("\tw layer prev/next\t" in row for row in translation_rows))
        self.assertTrue(any("\thelp\t" in row for row in main_rows))
        self.assertTrue(any("\tpause menu\t" in row for row in main_rows))
        self.assertTrue(any("\trestart\t" in row for row in main_rows))
        self.assertFalse(any("\tprojection\t" in row for row in camera_rows))
        self.assertTrue(any("\tview x-w +/-90\t" in row for row in camera_rows))
        self.assertTrue(any("\tview z-w +/-90\t" in row for row in camera_rows))
        self.assertTrue(
            any("\tlocked cells alpha [,]\t" in row for row in camera_rows)
        )

    def test_dim4_hides_exploration_rows_when_disabled(self) -> None:
        groups = control_groups_for_dimension(4, include_exploration=False)
        translation_rows = groups[1][1]
        self.assertEqual(len(translation_rows), 5)
        self.assertFalse(any("up/down (explore)" in row for row in translation_rows))

    def test_unified_structure_names_match_all_dimensions(self) -> None:
        names_2d = [
            name
            for name, _ in control_groups_for_dimension(2, unified_structure=True)
        ]
        names_3d = [
            name
            for name, _ in control_groups_for_dimension(3, unified_structure=True)
        ]
        names_4d = [
            name
            for name, _ in control_groups_for_dimension(4, unified_structure=True)
        ]
        self.assertEqual(names_2d, names_3d)
        self.assertEqual(names_3d, names_4d)

    def test_unified_structure_uses_placeholder_rows_for_missing_groups(self) -> None:
        groups_2d = control_groups_for_dimension(2, unified_structure=True)
        by_name = {name: rows for name, rows in groups_2d}
        self.assertIn("Camera", by_name)
        self.assertTrue(any("not available in 2D" in row for row in by_name["Camera"]))

    def test_planning_keeps_system_group_visible_in_tight_layouts(self) -> None:
        groups = control_groups_for_dimension(4)
        if not pygame.font.get_init():
            pygame.font.init()
        panel_font = pygame.font.Font(None, 20)
        hint_font = pygame.font.Font(None, 18)
        for available_h in range(160, 320, 20):
            planned, _overflow = _planned_group_rows(
                groups=groups,
                available_height=available_h,
                panel_font=panel_font,
                hint_font=hint_font,
            )
            if not planned:
                continue
            names = [name for name, _rows in planned]
            self.assertIn("Main", names)

    def test_planning_keeps_camera_and_system_in_moderate_height(self) -> None:
        groups = control_groups_for_dimension(4)
        if not pygame.font.get_init():
            pygame.font.init()
        panel_font = pygame.font.Font(None, 20)
        hint_font = pygame.font.Font(None, 18)
        planned, _overflow = _planned_group_rows(
            groups=groups,
            available_height=420,
            panel_font=panel_font,
            hint_font=hint_font,
        )
        names = [name for name, _rows in planned]
        self.assertIn("Camera", names)
        self.assertIn("Main", names)

    def test_planning_keeps_full_rotation_rows_before_camera_trimming(self) -> None:
        groups = control_groups_for_dimension(4)
        if not pygame.font.get_init():
            pygame.font.init()
        panel_font = pygame.font.Font(None, 20)
        hint_font = pygame.font.Font(None, 18)
        planned, _overflow = _planned_group_rows(
            groups=groups,
            available_height=520,
            panel_font=panel_font,
            hint_font=hint_font,
        )
        by_name = {name: rows for name, rows in planned}
        self.assertIn("Rotation", by_name)
        self.assertIn("Camera", by_name)
        expected_rotation = next(rows for name, rows in groups if name == "Rotation")
        self.assertEqual(len(by_name["Rotation"]), len(expected_rotation))


if __name__ == "__main__":
    unittest.main()
