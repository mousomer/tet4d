from __future__ import annotations

import unittest

try:
    import pygame
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised in environments without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised in environments without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for camera mouse tests")

from tet4d.ui.pygame.input.camera_mouse import (
    MAX_ABS_MOUSE_PITCH,
    MouseOrbitState,
    apply_mouse_orbit_event,
    clamp_pitch_deg,
    mouse_wheel_delta,
)


class TestCameraMouse(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_orbit_drag_updates_yaw_and_pitch(self) -> None:
        state = MouseOrbitState(yaw_sensitivity=0.5, pitch_sensitivity=0.25)
        yaw, pitch, changed = apply_mouse_orbit_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(100, 100)),
            state,
            yaw_deg=32.0,
            pitch_deg=-26.0,
        )
        self.assertFalse(changed)
        self.assertEqual((yaw, pitch), (32.0, -26.0))

        yaw2, pitch2, changed2 = apply_mouse_orbit_event(
            pygame.event.Event(pygame.MOUSEMOTION, pos=(120, 90)),
            state,
            yaw_deg=yaw,
            pitch_deg=pitch,
        )
        self.assertTrue(changed2)
        self.assertAlmostEqual(yaw2, 42.0, places=4)  # +20 * 0.5
        self.assertAlmostEqual(
            pitch2, -23.5, places=4
        )  # -26 + (-dy * 0.25) where dy=-10

    def test_pitch_is_clamped(self) -> None:
        state = MouseOrbitState(yaw_sensitivity=0.0, pitch_sensitivity=2.0)
        apply_mouse_orbit_event(
            pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=(0, 0)),
            state,
            yaw_deg=0.0,
            pitch_deg=0.0,
        )
        _yaw, pitch, changed = apply_mouse_orbit_event(
            pygame.event.Event(pygame.MOUSEMOTION, pos=(0, -1000)),
            state,
            yaw_deg=0.0,
            pitch_deg=0.0,
        )
        self.assertTrue(changed)
        self.assertEqual(pitch, MAX_ABS_MOUSE_PITCH)
        self.assertEqual(clamp_pitch_deg(-999.0), -MAX_ABS_MOUSE_PITCH)

    def test_mouse_wheel_delta(self) -> None:
        self.assertEqual(
            mouse_wheel_delta(pygame.event.Event(pygame.MOUSEWHEEL, y=2)), 2
        )
        self.assertEqual(
            mouse_wheel_delta(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=4)), 1
        )
        self.assertEqual(
            mouse_wheel_delta(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=5)), -1
        )
        self.assertEqual(
            mouse_wheel_delta(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a)), 0
        )


if __name__ == "__main__":
    unittest.main()
