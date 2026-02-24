from __future__ import annotations

import unittest

from tet4d.engine.menu_layout import compute_menu_layout_zones


class TestMenuLayout(unittest.TestCase):
    def _assert_zone_order(self, width: int, height: int) -> None:
        zones = compute_menu_layout_zones(
            width=width,
            height=height,
            outer_pad=20,
            header_height=120,
            footer_height=28,
            gap=8,
            min_content_height=160,
        )

        self.assertGreaterEqual(zones.frame.x, 0)
        self.assertGreaterEqual(zones.frame.y, 0)
        self.assertGreaterEqual(zones.frame.width, 1)
        self.assertGreaterEqual(zones.frame.height, 1)
        self.assertLessEqual(zones.frame.right, width)
        self.assertLessEqual(zones.frame.bottom, height)

        self.assertEqual(zones.header.x, zones.frame.x)
        self.assertEqual(zones.content.x, zones.frame.x)
        self.assertEqual(zones.footer.x, zones.frame.x)
        self.assertEqual(zones.header.width, zones.frame.width)
        self.assertEqual(zones.content.width, zones.frame.width)
        self.assertEqual(zones.footer.width, zones.frame.width)

        self.assertLessEqual(zones.header.bottom, zones.content.y)
        self.assertLessEqual(zones.content.bottom, zones.footer.y)
        self.assertGreaterEqual(zones.content.height, 1)
        self.assertGreaterEqual(zones.footer.height, 1)

    def test_layout_zones_non_overlapping_standard_window(self) -> None:
        self._assert_zone_order(width=1280, height=800)

    def test_layout_zones_non_overlapping_compact_windows(self) -> None:
        for width, height in ((800, 520), (640, 420), (520, 340), (420, 300)):
            with self.subTest(size=(width, height)):
                self._assert_zone_order(width=width, height=height)


if __name__ == "__main__":
    unittest.main()
