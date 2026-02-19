from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised in environments without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for 4D render tests")

from tetris_nd import front4d_game, front4d_render, frontend_nd, projection3d
from tetris_nd.game_nd import GameConfigND
from tetris_nd.keybindings import CAMERA_KEYS_4D
from tetris_nd.projection3d import box_raw_corners, projection_cache_key
from tetris_nd.view_modes import GridMode


def _key_for(bindings: dict[str, tuple[int, ...]], action: str) -> int:
    keys = bindings.get(action, ())
    if not keys:
        raise AssertionError(f"missing key binding for action: {action}")
    return keys[0]


class TestFront4DRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_view_hyper_turn_actions_animate(self) -> None:
        view = front4d_game.LayerView3D()
        self.assertTrue(front4d_render.handle_view_key(_key_for(CAMERA_KEYS_4D, "view_xw_pos"), view))
        self.assertTrue(view.hyper_animating)
        view.step_animation(1000.0)
        self.assertFalse(view.hyper_animating)
        self.assertAlmostEqual(view.xw_deg, 90.0, places=3)

        self.assertTrue(front4d_render.handle_view_key(_key_for(CAMERA_KEYS_4D, "view_zw_neg"), view))
        self.assertTrue(view.hyper_animating)
        view.step_animation(1000.0)
        self.assertFalse(view.hyper_animating)
        self.assertAlmostEqual(view.zw_deg, 270.0, places=3)

    def test_draw_helper_grid_with_hyper_turns_does_not_mutate_slice(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        view = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=270.0)
        fonts = frontend_nd.init_fonts()
        screen = pygame.Surface((1400, 900), pygame.SRCALPHA)

        before_slice = dict(slice_state.axis_values)
        front4d_render.draw_game_frame(
            screen,
            state,
            slice_state,
            view,
            fonts,
            grid_mode=GridMode.HELPER,
        )

        self.assertEqual(slice_state.axis_values, before_slice)

    def test_projection_cache_key_changes_when_w_size_changes(self) -> None:
        view = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=270.0)
        dims3 = (6, 12, 6)
        key_small = projection_cache_key(
            prefix="4d-full",
            dims=dims3,
            center_px=(320.0, 240.0),
            yaw_deg=view.yaw_deg,
            pitch_deg=view.pitch_deg,
            zoom=24.0,
            extras=front4d_render._projection_extras(view, (6, 12, 6, 3), 1),
        )
        key_large = projection_cache_key(
            prefix="4d-full",
            dims=dims3,
            center_px=(320.0, 240.0),
            yaw_deg=view.yaw_deg,
            pitch_deg=view.pitch_deg,
            zoom=24.0,
            extras=front4d_render._projection_extras(view, (6, 12, 6, 4), 1),
        )
        self.assertNotEqual(key_small, key_large)

    def test_fit_zoom_with_hyper_turns_keeps_layer_bounds_visible(self) -> None:
        dims3 = (6, 12, 6)
        dims4 = (6, 12, 6, 4)
        view = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=90.0)
        rect = pygame.Rect(0, 0, 460, 320)
        zoom = front4d_render._fit_zoom(dims3, dims4, 3, view, rect)
        transformed = [
            front4d_render._transform_raw_point(raw, dims3, dims4, 3, view)
            for raw in box_raw_corners(dims3)
        ]
        max_abs_x = max(abs(point[0]) for point in transformed)
        max_abs_y = max(abs(point[1]) for point in transformed)
        self.assertLessEqual(zoom * (2.0 * max_abs_x), rect.width - 14.0 + 1e-6)
        self.assertLessEqual(zoom * (2.0 * max_abs_y), rect.height - 24.0 + 1e-6)

    def test_draw_frame_cache_keeps_distinct_entries_for_different_w_sizes(self) -> None:
        projection3d.clear_projection_lattice_cache()
        try:
            fonts = frontend_nd.init_fonts()
            screen = pygame.Surface((1400, 900), pygame.SRCALPHA)
            view = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=270.0)

            cfg_w3 = GameConfigND(dims=(6, 12, 6, 3), gravity_axis=1, speed_level=1)
            state_w3 = frontend_nd.create_initial_state(cfg_w3)
            slice_w3 = frontend_nd.create_initial_slice_state(cfg_w3)
            front4d_render.draw_game_frame(screen, state_w3, slice_w3, view, fonts, grid_mode=GridMode.FULL)
            keys_after_w3 = projection3d.projection_lattice_cache_keys()
            self.assertTrue(any(isinstance(key, tuple) and key and key[0] == "4d-full" and key[-1] == 3 for key in keys_after_w3))

            cfg_w4 = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
            state_w4 = frontend_nd.create_initial_state(cfg_w4)
            slice_w4 = frontend_nd.create_initial_slice_state(cfg_w4)
            front4d_render.draw_game_frame(screen, state_w4, slice_w4, view, fonts, grid_mode=GridMode.FULL)
            keys_after_w4 = projection3d.projection_lattice_cache_keys()
            self.assertTrue(any(isinstance(key, tuple) and key and key[0] == "4d-full" and key[-1] == 3 for key in keys_after_w4))
            self.assertTrue(any(isinstance(key, tuple) and key and key[0] == "4d-full" and key[-1] == 4 for key in keys_after_w4))
            self.assertGreater(projection3d.projection_lattice_cache_size(), len(keys_after_w3))
        finally:
            projection3d.clear_projection_lattice_cache()


if __name__ == "__main__":
    unittest.main()
