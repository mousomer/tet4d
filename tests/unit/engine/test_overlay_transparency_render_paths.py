from __future__ import annotations

import unittest

import pygame

from tet4d.engine import front3d_render, front4d_render, frontend_nd
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.ui.pygame import front3d_game, front4d_game
from tet4d.ui.pygame.keybindings import CAMERA_KEYS_3D, CAMERA_KEYS_4D


class TestOverlayTransparencyRenderPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    @staticmethod
    def _key_for(bindings: dict[str, tuple[int, ...]], action: str) -> int:
        keys = bindings.get(action, ())
        assert keys
        return keys[0]

    @staticmethod
    def _surface_alpha_total(surface: pygame.Surface) -> int:
        rgba = pygame.image.tobytes(surface, "RGBA")
        return sum(rgba[3::4])

    def test_overlay_transparency_maps_to_inverse_opacity_scale(self) -> None:
        self.assertAlmostEqual(front3d_render._overlay_opacity_scale(0.2), 0.8)
        self.assertAlmostEqual(front3d_render._overlay_opacity_scale(0.7), 0.3)
        self.assertAlmostEqual(front3d_render._overlay_opacity_scale(1.0), 0.0)
        self.assertAlmostEqual(front4d_render._overlay_opacity_scale(0.2), 0.8)
        self.assertAlmostEqual(front4d_render._overlay_opacity_scale(0.7), 0.3)
        self.assertAlmostEqual(front4d_render._overlay_opacity_scale(1.0), 0.0)

    def test_front3d_active_piece_cells_are_not_overlay_cells(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("tri3", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), color_id=6),
            pos=(2, 3, 2),
        )
        cells = front3d_render._collect_visible_cells(state, active_overlay=None)
        active_cells = [cell for cell in cells if cell[2]]
        self.assertTrue(active_cells)
        self.assertTrue(all(not is_overlay for *_rest, is_overlay in active_cells))

    def test_front3d_overlay_cells_are_marked_for_alpha_path(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("tri3", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), color_id=7),
            pos=(2, 3, 2),
        )
        active_cells = tuple(
            (float(x), float(y), float(z))
            for x, y, z in state.current_piece_cells_mapped(include_above=False)
        )
        overlay = (active_cells, 7)
        cells = front3d_render._collect_visible_cells(state, active_overlay=overlay)
        overlay_cells = [cell for cell in cells if cell[3]]
        self.assertTrue(overlay_cells)
        self.assertTrue(all(is_overlay for *_head, is_overlay in overlay_cells))

    def test_front4d_overlay_and_piece_paths_have_distinct_overlay_flags(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        state = frontend_nd.create_initial_state(cfg)
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND(
                "tri4",
                ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
                color_id=5,
            ),
            pos=(2, 3, 2, 1),
        )
        basis = front4d_render._basis_for_view(front4d_game.LayerView3D(), cfg.dims)
        piece_cells = tuple(state.current_piece_cells_mapped(include_above=False))
        self.assertTrue(piece_cells)
        layer_value, _cell3 = front4d_render._map_coord_to_layer_cell3(
            piece_cells[0], dims4=cfg.dims, basis=basis
        )
        layer_idx = front4d_render._layer_index_if_discrete(layer_value)
        self.assertIsNotNone(layer_idx)
        assert layer_idx is not None

        piece_entries = front4d_render._piece_active_layer_cells(state, layer_idx, basis)
        self.assertTrue(piece_entries)
        self.assertTrue(all(not entry[3] for entry in piece_entries))

        overlay = (
            tuple(tuple(float(axis) for axis in coord) for coord in piece_cells),
            state.current_piece.shape.color_id,
        )
        overlay_entries = front4d_render._overlay_active_layer_cells(
            state,
            layer_idx,
            overlay,
            basis,
        )
        self.assertTrue(overlay_entries)
        self.assertTrue(all(entry[3] for entry in overlay_entries))

    def test_3d_overlay_keydown_changes_rendered_overlay_alpha(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
        loop = front3d_game.LoopContext3D.create(cfg)
        loop.state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("tri3", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), color_id=7),
            pos=(2, 3, 2),
        )
        overlay = (
            tuple(
                (float(x), float(y), float(z))
                for x, y, z in loop.state.current_piece_cells_mapped(include_above=False)
            ),
            int(loop.state.current_piece.shape.color_id),
        )
        board_rect = pygame.Rect(20, 20, 600, 600)
        before_surface = pygame.Surface((820, 720), pygame.SRCALPHA)
        front3d_render._draw_board_3d(
            before_surface,
            loop.state,
            loop.camera,
            board_rect,
            active_overlay=overlay,
            overlay_transparency=loop.overlay_transparency,
        )
        before_alpha_total = self._surface_alpha_total(before_surface)
        before_transparency = loop.overlay_transparency

        overlay_dec_key = self._key_for(CAMERA_KEYS_3D, "overlay_alpha_dec")
        loop.keydown_handler(pygame.event.Event(pygame.KEYDOWN, {"key": overlay_dec_key}))
        self.assertLess(loop.overlay_transparency, before_transparency)

        after_surface = pygame.Surface((820, 720), pygame.SRCALPHA)
        front3d_render._draw_board_3d(
            after_surface,
            loop.state,
            loop.camera,
            board_rect,
            active_overlay=overlay,
            overlay_transparency=loop.overlay_transparency,
        )
        after_alpha_total = self._surface_alpha_total(after_surface)
        self.assertGreater(after_alpha_total, before_alpha_total)

    def test_4d_overlay_keydown_changes_rendered_overlay_alpha(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        loop = front4d_game.LoopContext4D.create(cfg)
        loop.state.current_piece = ActivePieceND.from_shape(
            PieceShapeND(
                "tri4",
                ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
                color_id=5,
            ),
            pos=(2, 3, 2, 1),
        )
        basis = front4d_render._basis_for_view(loop.view, cfg.dims)
        piece_cells = tuple(loop.state.current_piece_cells_mapped(include_above=False))
        layer_value, _cell3 = front4d_render._map_coord_to_layer_cell3(
            piece_cells[0], dims4=cfg.dims, basis=basis
        )
        layer_idx = front4d_render._layer_index_if_discrete(layer_value)
        self.assertIsNotNone(layer_idx)
        assert layer_idx is not None
        overlay = (
            tuple(tuple(float(axis) for axis in coord) for coord in piece_cells),
            int(loop.state.current_piece.shape.color_id),
        )
        locked_by_layer = front4d_render._locked_cells_by_layer(loop.state, basis)
        draw_rect = pygame.Rect(20, 20, 420, 420)
        dims3 = basis.dims3
        zoom = front4d_render._fit_zoom(dims3, loop.view, draw_rect) * loop.view.zoom_scale
        center_px = (draw_rect.centerx, draw_rect.centery)

        before_surface = pygame.Surface((840, 760), pygame.SRCALPHA)
        front4d_render._draw_layer_cells(
            before_surface,
            state=loop.state,
            layer_index=layer_idx,
            view=loop.view,
            center_px=center_px,
            dims3=dims3,
            basis=basis,
            zoom=zoom,
            locked_by_layer=locked_by_layer,
            active_overlay=overlay,
            overlay_transparency=loop.overlay_transparency,
        )
        before_alpha_total = self._surface_alpha_total(before_surface)
        before_transparency = loop.overlay_transparency

        overlay_inc_key = self._key_for(CAMERA_KEYS_4D, "overlay_alpha_inc")
        loop.keydown_handler(pygame.event.Event(pygame.KEYDOWN, {"key": overlay_inc_key}))
        self.assertGreater(loop.overlay_transparency, before_transparency)

        after_surface = pygame.Surface((840, 760), pygame.SRCALPHA)
        front4d_render._draw_layer_cells(
            after_surface,
            state=loop.state,
            layer_index=layer_idx,
            view=loop.view,
            center_px=center_px,
            dims3=dims3,
            basis=basis,
            zoom=zoom,
            locked_by_layer=locked_by_layer,
            active_overlay=overlay,
            overlay_transparency=loop.overlay_transparency,
        )
        after_alpha_total = self._surface_alpha_total(after_surface)
        self.assertLess(after_alpha_total, before_alpha_total)


if __name__ == "__main__":
    unittest.main()
