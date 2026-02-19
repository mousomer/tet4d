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
        basis_small = front4d_render._basis_for_view(view, (6, 12, 6, 3))
        basis_large = front4d_render._basis_for_view(view, (6, 12, 6, 4))
        dims3 = basis_small.dims3
        key_small = projection_cache_key(
            prefix="4d-full",
            dims=dims3,
            center_px=(320.0, 240.0),
            yaw_deg=view.yaw_deg,
            pitch_deg=view.pitch_deg,
            zoom=24.0,
            extras=front4d_render._projection_extras(basis_small, (6, 12, 6, 3), 1),
        )
        key_large = projection_cache_key(
            prefix="4d-full",
            dims=basis_large.dims3,
            center_px=(320.0, 240.0),
            yaw_deg=view.yaw_deg,
            pitch_deg=view.pitch_deg,
            zoom=24.0,
            extras=front4d_render._projection_extras(basis_large, (6, 12, 6, 4), 1),
        )
        self.assertNotEqual(key_small, key_large)

    def test_basis_decomposition_for_xw_and_zw_turns(self) -> None:
        dims4 = (5, 4, 3, 2)
        xw_basis = front4d_render._basis_for_view(front4d_game.LayerView3D(xw_deg=90.0, zw_deg=0.0), dims4)
        self.assertEqual(xw_basis.layer_axis, 0)
        self.assertEqual(xw_basis.layer_count, 5)
        self.assertEqual(xw_basis.dims3, (2, 4, 3))

        zw_basis = front4d_render._basis_for_view(front4d_game.LayerView3D(xw_deg=0.0, zw_deg=90.0), dims4)
        self.assertEqual(zw_basis.layer_axis, 2)
        self.assertEqual(zw_basis.layer_count, 3)
        self.assertEqual(zw_basis.dims3, (5, 4, 2))

    def test_basis_coord_mapping_is_bijective(self) -> None:
        dims4 = (5, 4, 3, 2)
        basis = front4d_render._basis_for_view(front4d_game.LayerView3D(xw_deg=90.0, zw_deg=0.0), dims4)
        seen: set[tuple[int, int, int, int]] = set()

        for x in range(dims4[0]):
            for y in range(dims4[1]):
                for z in range(dims4[2]):
                    for w in range(dims4[3]):
                        layer_value, cell3 = front4d_render._map_coord_to_layer_cell3(
                            (float(x), float(y), float(z), float(w)),
                            dims4=dims4,
                            basis=basis,
                        )
                        layer_idx = front4d_render._layer_index_if_discrete(layer_value)
                        cell3_i = front4d_render._cell3_if_discrete(cell3)
                        self.assertIsNotNone(layer_idx)
                        self.assertIsNotNone(cell3_i)
                        assert layer_idx is not None and cell3_i is not None
                        self.assertTrue(front4d_render._in_bounds_layer_cell(layer_idx, cell3, basis))
                        key = (layer_idx, cell3_i[0], cell3_i[1], cell3_i[2])
                        self.assertNotIn(key, seen)
                        seen.add(key)

        self.assertEqual(len(seen), dims4[0] * dims4[1] * dims4[2] * dims4[3])

    def test_w_move_overrides_follow_basis_layer_axis(self) -> None:
        dims4 = (5, 4, 3, 2)
        identity = front4d_render.movement_axis_overrides_for_view(front4d_game.LayerView3D(xw_deg=0.0, zw_deg=0.0), dims4)
        self.assertEqual(identity["move_w_neg"], (3, -1))
        self.assertEqual(identity["move_w_pos"], (3, 1))

        xw_view = front4d_render.movement_axis_overrides_for_view(front4d_game.LayerView3D(xw_deg=90.0, zw_deg=0.0), dims4)
        self.assertEqual(xw_view["move_w_neg"], (0, -1))
        self.assertEqual(xw_view["move_w_pos"], (0, 1))

        zw_view = front4d_render.movement_axis_overrides_for_view(front4d_game.LayerView3D(xw_deg=0.0, zw_deg=90.0), dims4)
        self.assertEqual(zw_view["move_w_neg"], (2, -1))
        self.assertEqual(zw_view["move_w_pos"], (2, 1))

    def test_fractional_overlay_cells_are_not_quantized(self) -> None:
        view = front4d_game.LayerView3D()
        dims3 = (6, 12, 6)
        center = (240.0, 200.0)
        faces_a = front4d_render._build_cell_faces(
            cell=(1.10, 2.0, 3.0),
            color=(255, 255, 255),
            view=view,
            center_px=center,
            dims3=dims3,
            zoom=24.0,
            active=True,
        )
        faces_b = front4d_render._build_cell_faces(
            cell=(1.20, 2.0, 3.0),
            color=(255, 255, 255),
            view=view,
            center_px=center,
            dims3=dims3,
            zoom=24.0,
            active=True,
        )
        self.assertTrue(faces_a)
        self.assertTrue(faces_b)
        self.assertNotEqual(faces_a[0][1][0], faces_b[0][1][0])

    def test_layer_rect_mapping_uses_dynamic_layer_count(self) -> None:
        area = pygame.Rect(10, 20, 920, 620)
        rect_map_2 = front4d_render._layer_rects_by_layer(area=area, layer_count=2)
        rect_map_5 = front4d_render._layer_rects_by_layer(area=area, layer_count=5)
        self.assertEqual(set(rect_map_2.keys()), {0, 1})
        self.assertEqual(set(rect_map_5.keys()), {0, 1, 2, 3, 4})
        self.assertNotEqual(rect_map_2[1].topleft, rect_map_5[1].topleft)

    def test_fit_zoom_with_hyper_turns_keeps_layer_bounds_visible(self) -> None:
        dims4 = (6, 12, 6, 4)
        view = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=90.0)
        basis = front4d_render._basis_for_view(view, dims4)
        dims3 = basis.dims3
        rect = pygame.Rect(0, 0, 460, 320)
        zoom = front4d_render._fit_zoom(dims3, view, rect)
        transformed = [
            front4d_render._transform_raw_point(raw, dims3, view)
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
            self.assertTrue(
                any(
                    isinstance(key, tuple)
                    and key
                    and key[0] == "4d-full"
                    and len(key) > 11
                    and key[8:12] == (6, 12, 6, 3)
                    for key in keys_after_w3
                )
            )

            cfg_w4 = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
            state_w4 = frontend_nd.create_initial_state(cfg_w4)
            slice_w4 = frontend_nd.create_initial_slice_state(cfg_w4)
            front4d_render.draw_game_frame(screen, state_w4, slice_w4, view, fonts, grid_mode=GridMode.FULL)
            keys_after_w4 = projection3d.projection_lattice_cache_keys()
            self.assertTrue(
                any(
                    isinstance(key, tuple)
                    and key
                    and key[0] == "4d-full"
                    and len(key) > 11
                    and key[8:12] == (6, 12, 6, 3)
                    for key in keys_after_w4
                )
            )
            self.assertTrue(
                any(
                    isinstance(key, tuple)
                    and key
                    and key[0] == "4d-full"
                    and len(key) > 11
                    and key[8:12] == (6, 12, 6, 4)
                    for key in keys_after_w4
                )
            )
            self.assertGreater(projection3d.projection_lattice_cache_size(), len(keys_after_w3))
        finally:
            projection3d.clear_projection_lattice_cache()

    def test_layer_region_is_cleared_when_layer_count_shrinks(self) -> None:
        cfg = GameConfigND(dims=(5, 4, 3, 2), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        slice_state = frontend_nd.create_initial_slice_state(cfg)
        fonts = frontend_nd.init_fonts()
        screen = pygame.Surface((1400, 900), pygame.SRCALPHA)

        view_many = front4d_game.LayerView3D(xw_deg=90.0, zw_deg=0.0)
        front4d_render.draw_game_frame(screen, state, slice_state, view_many, fonts, grid_mode=GridMode.FULL)
        layers_rect = pygame.Rect(
            front4d_render.MARGIN,
            front4d_render.MARGIN,
            screen.get_width() - front4d_render.SIDE_PANEL - 3 * front4d_render.MARGIN,
            screen.get_height() - 2 * front4d_render.MARGIN,
        )
        rects_many = front4d_render._layer_rects_by_layer(area=layers_rect, layer_count=5)
        stale_rect = rects_many[4]

        view_few = front4d_game.LayerView3D(xw_deg=0.0, zw_deg=0.0)
        front4d_render.draw_game_frame(screen, state, slice_state, view_few, fonts, grid_mode=GridMode.FULL)
        rects_few = front4d_render._layer_rects_by_layer(area=layers_rect, layer_count=2)

        sample = stale_rect.center
        if any(rect.collidepoint(sample) for rect in rects_few.values()):
            sample = (stale_rect.left + 4, stale_rect.top + 4)
        self.assertFalse(any(rect.collidepoint(sample) for rect in rects_few.values()))
        self.assertEqual(screen.get_at(sample)[:3], (14, 18, 36))


if __name__ == "__main__":
    unittest.main()
