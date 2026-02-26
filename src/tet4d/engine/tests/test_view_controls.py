import unittest

from tet4d.ui.pygame.view_controls import (
    YawPitchTurnAnimator,
    viewer_relative_move_axis_delta,
    wrapped_pitch_target,
)


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

    def test_shared_turn_animator_smoke(self):
        anim = YawPitchTurnAnimator()
        self.assertFalse(anim.is_animating())
        anim.start_yaw_turn(90.0)
        self.assertTrue(anim.is_animating())
        anim.step_animation(1000.0)
        self.assertFalse(anim.is_animating())
        self.assertAlmostEqual(anim.yaw_deg, 122.0, places=2)

    def test_shared_turn_animator_pitch_wrap(self):
        anim = YawPitchTurnAnimator(yaw_deg=32.0, pitch_deg=-26.0)
        anim.start_pitch_turn(-90.0)
        self.assertTrue(anim.is_animating())
        anim.step_animation(1000.0)
        self.assertFalse(anim.is_animating())
        self.assertTrue(-74.0 <= anim.pitch_deg <= 74.0)


if __name__ == "__main__":
    unittest.main()
