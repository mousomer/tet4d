from __future__ import annotations

import unittest

from tet4d.engine.speed_curve import gravity_interval_ms


class TestSpeedCurve(unittest.TestCase):
    def test_default_level_1_intervals_are_dimension_scaled(self) -> None:
        self.assertEqual(gravity_interval_ms(1, dimension=2), 1000)
        self.assertEqual(gravity_interval_ms(1, dimension=3), 1350)
        self.assertEqual(gravity_interval_ms(1, dimension=4), 1700)

    def test_level_10_intervals_are_dimension_scaled(self) -> None:
        self.assertEqual(gravity_interval_ms(10, dimension=2), 100)
        self.assertEqual(gravity_interval_ms(10, dimension=3), 135)
        self.assertEqual(gravity_interval_ms(10, dimension=4), 170)

    def test_same_level_gets_slower_for_higher_dimensions(self) -> None:
        for level in (1, 2, 4, 7, 10):
            interval_2d = gravity_interval_ms(level, dimension=2)
            interval_3d = gravity_interval_ms(level, dimension=3)
            interval_4d = gravity_interval_ms(level, dimension=4)
            self.assertGreater(interval_3d, interval_2d)
            self.assertGreater(interval_4d, interval_3d)

    def test_speed_level_is_clamped(self) -> None:
        self.assertEqual(
            gravity_interval_ms(0, dimension=2), gravity_interval_ms(1, dimension=2)
        )
        self.assertEqual(
            gravity_interval_ms(99, dimension=4), gravity_interval_ms(10, dimension=4)
        )


if __name__ == "__main__":
    unittest.main()
