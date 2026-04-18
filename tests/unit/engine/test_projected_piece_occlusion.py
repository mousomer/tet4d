from __future__ import annotations

import unittest

try:
    import pygame
except (
    ModuleNotFoundError
):  # pragma: no cover - exercised when pygame-ce is unavailable
    pygame = None

if pygame is None:  # pragma: no cover - exercised when pygame-ce is unavailable
    raise unittest.SkipTest("pygame-ce is required for projected occlusion tests")

from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.rotation_anim import PieceRotationAnimatorND
from tet4d.engine.ui_logic.view_modes import GridMode
from tet4d.ui.pygame import front3d_render, front4d_game, front4d_render, frontend_nd_state
from tet4d.ui.pygame.projection3d import (
    ProjectedFacePrimitive,
    ProjectedLinePrimitive,
)
from tet4d.ui.pygame.render.front3d_projection_helpers import (
    depth_denominator_for_depth,
)
from tet4d.ui.pygame.render.grid_mode_render import build_projected_grid_primitives
from tet4d.ui.pygame.render.projected_occlusion import (
    default_segment_occlusion_policy,
    resolve_board_line_occlusion,
)


def _face(
    *,
    polygon: tuple[tuple[float, float], ...],
    depth: float,
) -> ProjectedFacePrimitive:
    return ProjectedFacePrimitive(
        avg_depth=depth,
        polygon=polygon,
        color=(255, 255, 255),
        active=True,
        vertex_depths=tuple(depth for _ in polygon),
        vertex_denominators=tuple(1.0 for _ in polygon),
    )


def _segment(
    *,
    start: tuple[float, float],
    end: tuple[float, float],
    depth: float,
) -> ProjectedLinePrimitive:
    return ProjectedLinePrimitive(
        start=start,
        end=end,
        start_depth=depth,
        end_depth=depth,
        start_denominator=1.0,
        end_denominator=1.0,
        source_type="gridline",
    )


def _line_signature(primitives: tuple) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            primitive.source_type,
            round(float(primitive.start[0]), 4),
            round(float(primitive.start[1]), 4),
            round(float(primitive.end[0]), 4),
            round(float(primitive.end[1]), 4),
        )
        for primitive in primitives
    )


def _face_signature(primitives: tuple) -> tuple[tuple[tuple[float, float], ...], ...]:
    return tuple(
        tuple((round(float(x), 4), round(float(y), 4)) for x, y in primitive.polygon)
        for primitive in primitives
    )


def _polygon_signature(faces: list) -> tuple[tuple[tuple[float, float], ...], ...]:
    return tuple(
        tuple((round(float(x), 4), round(float(y), 4)) for x, y in polygon)
        for _depth, polygon, _color, _active in faces
    )


class ProjectedOcclusionResolverTests(unittest.TestCase):
    def test_segment_fully_in_front_of_face_is_classified_over_piece(self) -> None:
        buckets = resolve_board_line_occlusion(
            (_segment(start=(15.0, 5.0), end=(15.0, 35.0), depth=0.5),),
            (
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=1.0,
                ),
            ),
        )
        self.assertEqual(len(buckets.segments_under_piece), 2)
        self.assertEqual(len(buckets.segments_over_piece), 1)

    def test_segment_fully_behind_face_is_classified_under_piece(self) -> None:
        buckets = resolve_board_line_occlusion(
            (_segment(start=(20.0, 5.0), end=(20.0, 35.0), depth=1.5),),
            (
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=1.0,
                ),
            ),
        )
        self.assertEqual(len(buckets.segments_under_piece), 3)
        self.assertFalse(buckets.segments_over_piece)

    def test_segment_crossing_piece_polygon_is_split_at_piece_boundary(self) -> None:
        buckets = resolve_board_line_occlusion(
            (_segment(start=(0.0, 20.0), end=(40.0, 20.0), depth=0.5),),
            (
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=1.0,
                ),
            ),
        )
        self.assertEqual(len(buckets.segments_under_piece), 2)
        self.assertEqual(len(buckets.segments_over_piece), 1)
        self.assertAlmostEqual(buckets.segments_over_piece[0].start[0], 10.0, places=3)
        self.assertAlmostEqual(buckets.segments_over_piece[0].end[0], 30.0, places=3)

    def test_near_tie_depths_stay_under_piece_for_stable_tie_breaking(self) -> None:
        policy = default_segment_occlusion_policy()
        buckets = resolve_board_line_occlusion(
            (
                _segment(
                    start=(20.0, 5.0),
                    end=(20.0, 35.0),
                    depth=1.0 - (policy.depth_epsilon * 0.5),
                ),
            ),
            (
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=1.0,
                ),
            ),
            policy=policy,
        )
        self.assertFalse(buckets.segments_over_piece)
        self.assertEqual(len(buckets.segments_under_piece), 3)

    def test_nearest_overlapping_piece_face_wins(self) -> None:
        buckets = resolve_board_line_occlusion(
            (_segment(start=(20.0, 5.0), end=(20.0, 35.0), depth=1.5),),
            (
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=1.0,
                ),
                _face(
                    polygon=((10.0, 10.0), (30.0, 10.0), (30.0, 30.0), (10.0, 30.0)),
                    depth=2.0,
                ),
            ),
        )
        self.assertFalse(buckets.segments_over_piece)
        self.assertEqual(len(buckets.segments_under_piece), 3)


class ProjectedOcclusionIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_3d_piece_depth_changes_board_line_overlays(self) -> None:
        near_buckets = self._resolve_3d_buckets(piece_pos=(1, 1, 0), yaw_deg=0.0)
        far_buckets = self._resolve_3d_buckets(piece_pos=(1, 1, 2), yaw_deg=0.0)
        flipped_view_buckets = self._resolve_3d_buckets(
            piece_pos=(1, 1, 0), yaw_deg=180.0
        )

        self.assertGreater(
            len(far_buckets.segments_over_piece),
            len(near_buckets.segments_over_piece),
        )
        self.assertGreater(
            len(flipped_view_buckets.segments_over_piece),
            len(near_buckets.segments_over_piece),
        )

    def test_4d_layer_projection_uses_same_occlusion_contract(self) -> None:
        near_buckets = self._resolve_4d_buckets(piece_pos=(1, 1, 0, 1), yaw_deg=0.0)
        far_buckets = self._resolve_4d_buckets(piece_pos=(1, 1, 2, 1), yaw_deg=0.0)
        flipped_view_buckets = self._resolve_4d_buckets(
            piece_pos=(1, 1, 0, 1),
            yaw_deg=180.0,
        )

        self.assertGreater(
            len(far_buckets.segments_over_piece),
            len(near_buckets.segments_over_piece),
        )
        self.assertGreater(
            len(flipped_view_buckets.segments_over_piece),
            len(near_buckets.segments_over_piece),
        )

    def _resolve_3d_buckets(
        self,
        *,
        piece_pos: tuple[int, int, int],
        yaw_deg: float,
    ):
        cfg = GameConfigND(dims=(3, 3, 3), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("dot3", ((0, 0, 0),), color_id=6),
            pos=piece_pos,
        )
        camera = front3d_render.Camera3D(
            projection=front3d_render.ProjectionMode3D.ORTHOGRAPHIC,
            yaw_deg=yaw_deg,
            pitch_deg=0.0,
            zoom=84.0,
            auto_fit_once=False,
        )
        board_rect = pygame.Rect(0, 0, 320, 320)
        center_px = (board_rect.centerx, board_rect.centery)
        params = front3d_render._projection_params(camera)
        visible_cells = front3d_render._collect_visible_cells(state)
        faces = front3d_render._active_piece_face_primitives(
            visible_cells,
            camera=camera,
            center_px=center_px,
            dims=cfg.dims,
        )
        helper_marks = front3d_render._helper_grid_marks_3d(state)
        line_primitives = build_projected_grid_primitives(
            dims=cfg.dims,
            grid_mode=GridMode.FULL,
            project_raw=lambda raw: front3d_render.project_raw_point_helper(
                raw,
                cfg.dims,
                params,
                center_px,
            ),
            transform_raw=lambda raw: front3d_render.transform_raw_point_helper(
                raw,
                cfg.dims,
                params,
            ),
            depth_denominator=lambda depth: depth_denominator_for_depth(depth, params),
            helper_marks=helper_marks,
        )
        return resolve_board_line_occlusion(tuple(line_primitives), faces)

    def test_3d_translation_animation_keeps_board_presentation_stable(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        state.board.cells[(1, 8, 2)] = 4
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("tri3", ((0, 0, 0), (1, 0, 0), (0, 1, 0)), color_id=6),
            pos=(2, 3, 2),
        )
        animator = PieceRotationAnimatorND(
            ndim=3,
            gravity_axis=cfg.gravity_axis,
            duration_ms=300.0,
            translation_duration_ms=120.0,
        )
        camera = front3d_render.Camera3D(
            projection=front3d_render.ProjectionMode3D.ORTHOGRAPHIC,
            yaw_deg=32.0,
            pitch_deg=-26.0,
            zoom=84.0,
            auto_fit_once=False,
        )
        board_rect = pygame.Rect(0, 0, 900, 680)

        animator.observe(state.current_piece, 0.0, animate_translation=False)
        self.assertTrue(state.try_move_axis(0, 1, animate_translation=True))
        animator.observe(
            state.current_piece,
            0.0,
            animate_translation=state.consume_translation_animation_hint(),
        )
        start_state = animator.render_state(state.current_piece)
        assert start_state is not None
        animator.observe(state.current_piece, 60.0, animate_translation=False)
        mid_state = animator.render_state(state.current_piece)
        assert mid_state is not None
        assert animator._tween is not None
        animator._tween.elapsed_ms = animator.translation_duration_ms
        end_state = animator.render_state(state.current_piece)
        assert end_state is not None

        presentations = [
            front3d_render._build_board_presentation_3d(
                state,
                camera,
                board_rect,
                grid_mode=GridMode.HELPER,
                piece_render_state=render_state,
            )
            for render_state in (start_state, mid_state, end_state)
        ]
        first = presentations[0]
        for candidate in presentations[1:]:
            self.assertEqual(candidate.center_px, first.center_px)
            self.assertEqual(candidate.helper_marks, first.helper_marks)
            self.assertEqual(candidate.full_grid_cache_key, first.full_grid_cache_key)
            self.assertEqual(candidate.helper_cache_key, first.helper_cache_key)
            self.assertEqual(
                _line_signature(candidate.board_line_primitives),
                _line_signature(first.board_line_primitives),
            )
            self.assertEqual(candidate.params, first.params)

        locked_faces = [
            front3d_render._build_cell_faces(
                cell=(1.0, 8.0, 2.0),
                color=front3d_render.color_for_cell_3d(4),
                camera=camera,
                center_px=presentation.center_px,
                dims=cfg.dims,
                active=False,
            )
            for presentation in presentations
        ]
        self.assertEqual(
            _polygon_signature(locked_faces[1]),
            _polygon_signature(locked_faces[0]),
        )
        self.assertEqual(
            _polygon_signature(locked_faces[2]),
            _polygon_signature(locked_faces[0]),
        )

        active_face_signatures = [
            _face_signature(
                front3d_render._active_piece_face_primitives(
                    front3d_render._collect_visible_cells(state, render_state),
                    camera=camera,
                    center_px=presentation.center_px,
                    dims=cfg.dims,
                )
            )
            for render_state, presentation in zip(
                (start_state, mid_state, end_state),
                presentations,
            )
        ]
        self.assertNotEqual(active_face_signatures[1], active_face_signatures[0])
        self.assertNotEqual(active_face_signatures[2], active_face_signatures[0])

    def test_4d_rotation_animation_keeps_layer_presentation_stable(self) -> None:
        cfg = GameConfigND(dims=(6, 12, 6, 4), gravity_axis=1, speed_level=1)
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
        view = front4d_game.LayerView3D(yaw_deg=32.0, pitch_deg=-26.0)
        basis = front4d_render._basis_for_view(view, cfg.dims)
        draw_rect = pygame.Rect(0, 0, 420, 320)
        locked_by_layer = front4d_render._locked_cells_by_layer(state, basis)

        animator.observe(state.current_piece, 0.0, animate_translation=False)
        self.assertTrue(state.try_rotate(0, 3, 1))
        animator.observe(state.current_piece, 0.0, animate_translation=False)
        start_state = animator.render_state(state.current_piece)
        assert start_state is not None
        animator.observe(state.current_piece, 150.0, animate_translation=False)
        mid_state = animator.render_state(state.current_piece)
        assert mid_state is not None
        assert animator._tween is not None
        animator._tween.elapsed_ms = animator.duration_ms
        end_state = animator.render_state(state.current_piece)
        assert end_state is not None

        layer_value, _ = front4d_render._map_coord_to_layer_cell3(
            start_state.presentation_cells[0],
            dims4=cfg.dims,
            basis=basis,
        )
        layer_index = front4d_render._layer_index_if_discrete(layer_value)
        self.assertIsNotNone(layer_index)
        assert layer_index is not None

        presentations = [
            front4d_render._build_layer_presentation(
                state=state,
                view=view,
                draw_rect=draw_rect,
                layer_index=layer_index,
                basis=basis,
                grid_mode=GridMode.HELPER,
                piece_render_state=render_state,
            )
            for render_state in (start_state, mid_state, end_state)
        ]
        first = presentations[0]
        for candidate in presentations[1:]:
            self.assertEqual(candidate.center_px, first.center_px)
            self.assertEqual(candidate.zoom, first.zoom)
            self.assertEqual(candidate.helper_marks, first.helper_marks)
            self.assertEqual(candidate.full_grid_cache_key, first.full_grid_cache_key)
            self.assertEqual(candidate.helper_cache_key, first.helper_cache_key)
            self.assertEqual(
                _line_signature(candidate.board_line_primitives),
                _line_signature(first.board_line_primitives),
            )

        layer_value, locked_cell3 = front4d_render._map_coord_to_layer_cell3(
            (1.0, 8.0, 2.0, 1.0),
            dims4=cfg.dims,
            basis=basis,
        )
        self.assertEqual(
            front4d_render._layer_index_if_discrete(layer_value),
            layer_index,
        )
        locked_faces = [
            front4d_render._build_cell_faces(
                cell=locked_cell3,
                color=front4d_render.color_for_cell(4, front4d_render.COLOR_MAP),
                view=view,
                center_px=presentation.center_px,
                dims3=basis.dims3,
                zoom=presentation.zoom,
                active=False,
            )
            for presentation in presentations
        ]
        self.assertEqual(
            _polygon_signature(locked_faces[1]),
            _polygon_signature(locked_faces[0]),
        )
        self.assertEqual(
            _polygon_signature(locked_faces[2]),
            _polygon_signature(locked_faces[0]),
        )

        active_face_signatures = [
            _face_signature(
                front4d_render._active_layer_face_primitives(
                    state,
                    layer_index,
                    view,
                    presentation.center_px,
                    basis.dims3,
                    basis,
                    presentation.zoom,
                    piece_render_state=render_state,
                )
            )
            for render_state, presentation in zip(
                (start_state, mid_state, end_state),
                presentations,
            )
        ]
        self.assertNotEqual(active_face_signatures[1], active_face_signatures[0])
        self.assertNotEqual(active_face_signatures[2], active_face_signatures[0])

        drawn_cells = [
            front4d_render._layer_cells(
                state,
                layer_index,
                locked_by_layer,
                basis,
                render_state,
            )
            for render_state in (start_state, mid_state, end_state)
        ]
        self.assertNotEqual(drawn_cells[1], drawn_cells[0])
        self.assertNotEqual(drawn_cells[2], drawn_cells[0])

    def _resolve_4d_buckets(
        self,
        *,
        piece_pos: tuple[int, int, int, int],
        yaw_deg: float,
    ):
        cfg = GameConfigND(dims=(3, 3, 3, 2), gravity_axis=1, speed_level=1)
        state = frontend_nd_state.create_initial_state(cfg)
        state.current_piece = ActivePieceND.from_shape(
            PieceShapeND("dot4", ((0, 0, 0, 0),), color_id=5),
            pos=piece_pos,
        )
        view = front4d_render.LayerView3D(yaw_deg=yaw_deg, pitch_deg=0.0)
        basis = front4d_render._basis_for_view(view, cfg.dims)
        layer_value, _cell3 = front4d_render._map_coord_to_layer_cell3(
            piece_pos,
            dims4=cfg.dims,
            basis=basis,
        )
        layer_index = front4d_render._layer_index_if_discrete(layer_value)
        self.assertIsNotNone(layer_index)
        assert layer_index is not None
        draw_rect = pygame.Rect(0, 0, 320, 320)
        zoom = front4d_render._fit_zoom(basis.dims3, view, draw_rect)
        center_px = (draw_rect.centerx, draw_rect.centery)
        faces = front4d_render._active_layer_face_primitives(
            state,
            layer_index,
            view,
            center_px,
            basis.dims3,
            basis,
            zoom,
        )
        line_primitives = build_projected_grid_primitives(
            dims=basis.dims3,
            grid_mode=GridMode.FULL,
            project_raw=lambda raw: front4d_render._project_raw_point(
                raw,
                basis.dims3,
                view,
                center_px,
                zoom,
            ),
            transform_raw=lambda raw: front4d_render._transform_raw_point(
                raw,
                basis.dims3,
                view,
            ),
            depth_denominator=front4d_render._orthographic_depth_denominator,
            helper_marks=front4d_render._helper_grid_marks_by_layer(state, basis).get(
                layer_index
            ),
        )
        return resolve_board_line_occlusion(tuple(line_primitives), faces)


if __name__ == "__main__":
    unittest.main()
