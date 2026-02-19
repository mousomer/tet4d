from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError as exc:  # pragma: no cover - runtime environment guard
    raise unittest.SkipTest("pygame-ce is required for control helper tests") from exc

from tetris_nd.control_helper import control_groups_for_dimension
from tetris_nd.control_icons import (
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
        draw_action_icon(surface, rect=pygame.Rect(8, 8, 20, 20), action="rotate_xy_pos")
        draw_action_icon(surface, rect=pygame.Rect(8, 8, 26, 26), action="rotate_xy_pos")
        self.assertEqual(action_icon_cache_size(), 2)

    def test_invalid_action_does_not_create_cache_entry(self) -> None:
        surface = pygame.Surface((120, 80), pygame.SRCALPHA)
        draw_action_icon(surface, rect=pygame.Rect(8, 8, 20, 20), action="unknown_action")
        self.assertEqual(action_icon_cache_size(), 0)


class TestControlGroups(unittest.TestCase):
    def test_dim2_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(2)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Translation", "Rotation", "System"])
        self.assertEqual([len(rows) for _, rows in groups], [4, 1, 5])
        translation_rows = groups[0][1]
        self.assertIn("\tmove x\t", translation_rows[0])
        self.assertIn("\thard drop\t", translation_rows[-1])

    def test_dim3_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(3)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Translation", "Rotation", "System", "Camera/View"])
        self.assertEqual([len(rows) for _, rows in groups], [5, 3, 5, 6])
        camera_rows = groups[3][1]
        self.assertTrue(any("\tprojection\t" in row for row in camera_rows))

    def test_dim4_control_group_layout(self) -> None:
        groups = control_groups_for_dimension(4)
        names = [name for name, _ in groups]
        self.assertEqual(names, ["Translation", "Rotation", "System", "Camera/View"])
        self.assertEqual([len(rows) for _, rows in groups], [6, 6, 5, 7])
        translation_rows = groups[0][1]
        camera_rows = groups[-1][1]
        self.assertTrue(any("\tw layer prev/next\t" in row for row in translation_rows))
        self.assertFalse(any("\tprojection\t" in row for row in camera_rows))
        self.assertTrue(any("\tview x-w +/-90\t" in row for row in camera_rows))
        self.assertTrue(any("\tview z-w +/-90\t" in row for row in camera_rows))

    def test_dim4_hides_exploration_rows_when_disabled(self) -> None:
        groups = control_groups_for_dimension(4, include_exploration=False)
        translation_rows = groups[0][1]
        self.assertEqual(len(translation_rows), 5)
        self.assertFalse(any("up/down (explore)" in row for row in translation_rows))


if __name__ == "__main__":
    unittest.main()
