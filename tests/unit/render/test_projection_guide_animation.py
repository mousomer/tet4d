from __future__ import annotations

import unittest
from unittest import mock

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for projection-guide animation tests")

from tet4d.engine.gameplay.game2d import GameConfig
from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.rotation_anim import (
    PieceRotationAnimator2D,
    PieceRotationAnimatorND,
)
from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame import front4d_game, front4d_render, frontend_nd_state
from tet4d.ui.pygame.front2d_session import LoopContext2D
from tet4d.ui.pygame.render import gfx_game


class TestProjectionGuideAnimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _create_2d_loop(self) -> LoopContext2D:
        cfg = GameConfig(
            width=10,
            height=20,
            gravity_axis=1,
            speed_level=1,
        )
        loop = LoopContext2D.create(
            cfg,
            rotation_animation_mode="cellwise_sliding",
            rotation_animation_duration_ms=160.0,
            translation_animation_duration_ms=120.0,
        )
        loop.state.board.cells.clear()
        loop.state.current_piece = ActivePiece2D(
            shape=PieceShape2D("el", [(0, 0), (1, 0), (0, 1)], color_id=3),
            pos=(4, 6),
            rotation=0,
        )
        loop.rotation_anim.reset()
        return loop

    def test_2d_projection_guide_follows_translation_while_board_shadow_stays_stable(
        self,
    ) -> None:
        screen = pygame.Surface((1024, 840), pygame.SRCALPHA)
        loop = self._create_2d_loop()
        piece = loop.state.current_piece
        assert piece is not None
        animator = PieceRotationAnimator2D(
            duration_ms=160.0,
            translation_duration_ms=120.0,
        )
        animator.observe(piece, 0.0)

        self.assertTrue(loop.state.try_move(1, 0, animate_translation=True))
        moved_piece = loop.state.current_piece
        assert moved_piece is not None
        animator.observe(
            moved_piece,
            0.0,
            animate_translation=loop.state.consume_translation_animation_hint(),
        )
        start_overlay = animator.overlay_state(moved_piece)
        self.assertIsNotNone(start_overlay)
        assert start_overlay is not None
        animator.observe(moved_piece, 60.0)
        mid_overlay = animator.overlay_state(moved_piece)
        self.assertIsNotNone(mid_overlay)
        assert mid_overlay is not None

        board_offset, _panel_offset = gfx_game.compute_game_layout(screen, loop.cfg)
        shadow_rects: list[pygame.Rect] = []
        guide_segments: list[tuple[object, ...]] = []
        original_shadow = gfx_game._draw_board_shadow

        def record_shadow(surface, board_rect):
            shadow_rects.append(board_rect.copy())
            return original_shadow(surface, board_rect)

        def record_segments(*_args, segments, **_kwargs):
            guide_segments.append(tuple(segments))

        with (
            mock.patch.object(gfx_game, "_draw_board_shadow", side_effect=record_shadow),
            mock.patch.object(
                gfx_game,
                "draw_boundary_projection_segments_2d",
                side_effect=record_segments,
            ),
        ):
            gfx_game.draw_board(
                screen,
                loop.state,
                board_offset,
                grid_mode=gfx_game.GridMode.ALL_BOUNDARIES,
                active_piece_overlay=start_overlay,
            )
            gfx_game.draw_board(
                screen,
                loop.state,
                board_offset,
                grid_mode=gfx_game.GridMode.ALL_BOUNDARIES,
                active_piece_overlay=mid_overlay,
            )

        self.assertEqual(len(shadow_rects), 2)
        self.assertEqual(shadow_rects[0], shadow_rects[1])
        self.assertEqual(len(guide_segments), 2)
        self.assertNotEqual(guide_segments[0], guide_segments[1])

    def test_4d_frozen_layer_presentation_builds_once_per_animation_move(self) -> None:
        view = front4d_game.LayerView3D(yaw_deg=32.0, pitch_deg=-26.0)
        screen = pygame.Surface((1280, 820))
        fonts = front4d_game.init_fonts()
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
        layer_count = front4d_render._basis_for_view(view, cfg.dims).layer_count

        for grid_mode in (GridMode.HELPER, GridMode.ALL_BOUNDARIES):
            with self.subTest(grid_mode=grid_mode.value):
                state = frontend_nd_state.create_initial_state(cfg)
                state.board.cells[(1, 8, 2, 1)] = 4
                state.current_piece = ActivePieceND.from_shape(
                    PieceShapeND(
                        "tri4",
                        ((0, 0, 0, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0)),
                        color_id=5,
                    ),
                    pos=(2, 3, 2, 1),
                )
                animator = PieceRotationAnimatorND(
                    ndim=4,
                    gravity_axis=cfg.gravity_axis,
                    duration_ms=300.0,
                    translation_duration_ms=120.0,
                )
                assert state.current_piece is not None
                animator.observe(state.current_piece, 0.0, animate_translation=False)
                self.assertTrue(state.try_move_axis(0, 1, animate_translation=True))
                assert state.current_piece is not None
                animator.observe(
                    state.current_piece,
                    0.0,
                    animate_translation=state.consume_translation_animation_hint(),
                )
                start_state = animator.render_state(state.current_piece)
                assert start_state is not None
                view.frozen_piece_presentation = None
                with mock.patch.object(
                    front4d_render,
                    "_build_layer_presentation",
                    wraps=front4d_render._build_layer_presentation,
                ) as build_presentation:
                    front4d_render.draw_game_frame(
                        screen,
                        state,
                        view,
                        fonts,
                        grid_mode=grid_mode,
                        active_overlay=start_state,
                    )
                    self.assertEqual(build_presentation.call_count, layer_count)

                    animator.observe(state.current_piece, 60.0, animate_translation=False)
                    mid_state = animator.render_state(state.current_piece)
                    assert mid_state is not None
                    front4d_render.draw_game_frame(
                        screen,
                        state,
                        view,
                        fonts,
                        grid_mode=grid_mode,
                        active_overlay=mid_state,
                    )
                    self.assertEqual(build_presentation.call_count, layer_count)


if __name__ == "__main__":
    unittest.main()
