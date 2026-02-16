import unittest

from tetris_nd.view_controls import viewer_relative_move_axis_delta, wrapped_pitch_target


class TestViewControls(unittest.TestCase):
    def test_default_view_direction_mapping(self):
        # Default yaw ~= 32 degrees: away should map to +z, closer to -z.
        self.assertEqual(viewer_relative_move_axis_delta(32.0, "away"), (2, 1))
        self.assertEqual(viewer_relative_move_axis_delta(32.0, "closer"), (2, -1))
        self.assertEqual(viewer_relative_move_axis_delta(32.0, "left"), (0, -1))
        self.assertEqual(viewer_relative_move_axis_delta(32.0, "right"), (0, 1))

    def test_yaw_90_mapping(self):
        # At yaw=90, right/left map to z and away/closer map to x.
        self.assertEqual(viewer_relative_move_axis_delta(90.0, "left"), (2, -1))
        self.assertEqual(viewer_relative_move_axis_delta(90.0, "right"), (2, 1))
        self.assertEqual(viewer_relative_move_axis_delta(90.0, "away"), (0, -1))
        self.assertEqual(viewer_relative_move_axis_delta(90.0, "closer"), (0, 1))

    def test_pitch_wrap_avoids_flat_view(self):
        yaw, pitch = wrapped_pitch_target(32.0, -26.0, -90.0)
        self.assertTrue(-74.0 <= pitch <= 74.0)
        self.assertNotEqual(yaw, 32.0)

        yaw2, pitch2 = wrapped_pitch_target(32.0, -26.0, 90.0)
        self.assertTrue(-74.0 <= pitch2 <= 74.0)
        self.assertEqual(yaw2, 32.0)


if __name__ == "__main__":
    unittest.main()
