from __future__ import annotations

import unittest

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for projection-guide tests")

from tet4d.engine.gameplay.game_nd import GameConfigND
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.topology_explorer.presets import (
    projective_space_profile_3d,
    projective_space_profile_4d,
)
from tet4d.engine.ui_logic.view_modes import GridMode, cycle_grid_mode, grid_mode_label
from tet4d.ui.pygame import (
    front3d_render,
    front4d_game,
    front4d_render,
    frontend_nd_state,
)
from tet4d.ui.pygame.render.active_piece_projection_guides import (
    boundary_targets_for_mode,
    build_boundary_projection_face_primitives,
    build_boundary_projection_segments_2d,
)


def _oblique_project(raw: tuple[float, float, float]) -> tuple[float, float]:
    return (
        float(raw[0]) + (0.15 * float(raw[2])),
        float(raw[1]) + (0.2 * float(raw[2])),
    )


def _identity_transform(raw: tuple[float, float, float]) -> tuple[float, float, float]:
    return (float(raw[0]), float(raw[1]), float(raw[2]))


class TestActivePieceProjectionGuides(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_grid_mode_cycle_and_labels_include_projection_guides(self) -> None:
        self.assertEqual(cycle_grid_mode(GridMode.OFF), GridMode.BOTTOM_BOUNDARY)
        self.assertEqual(cycle_grid_mode(GridMode.HELPER), GridMode.ALL_BOUNDARIES)
        self.assertEqual(grid_mode_label(GridMode.BOTTOM_BOUNDARY), "BOTTOM BOUNDARY")
        self.assertEqual(grid_mode_label(GridMode.ALL_BOUNDARIES), "ALL BOUNDARIES")

    def test_bottom_boundary_targets_follow_gravity_axis(self) -> None:
        targets = boundary_targets_for_mode(
            dims=(10, 20, 6),
            gravity_axis=1,
            grid_mode=GridMode.BOTTOM_BOUNDARY,
        )
        self.assertEqual(len(targets), 1)
        self.assertEqual(targets[0].axis, 1)
        self.assertEqual(targets[0].side, "+")
        self.assertEqual(targets[0].coordinate, 20.0)

    def test_all_boundary_targets_cover_every_axis_side(self) -> None:
        targets = boundary_targets_for_mode(
            dims=(6, 8, 4),
            gravity_axis=1,
            grid_mode=GridMode.ALL_BOUNDARIES,
        )
        self.assertEqual(len(targets), 6)
        self.assertEqual(
            {(target.axis, target.side) for target in targets},
            {(0, "-"), (0, "+"), (1, "-"), (1, "+"), (2, "-"), (2, "+")},
        )

    def test_2d_bottom_boundary_segments_align_to_bottom_line(self) -> None:
        segments = build_boundary_projection_segments_2d(
            cells=(((2.0, 3.0), 1.0),),
            dims=(10, 20),
            gravity_axis=1,
            grid_mode=GridMode.BOTTOM_BOUNDARY,
            color=(0, 255, 255),
        )
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0].start, (2.0, 20.0))
        self.assertEqual(segments[0].end, (3.0, 20.0))

    def test_2d_all_boundary_segments_cover_all_board_edges(self) -> None:
        segments = build_boundary_projection_segments_2d(
            cells=(((4.0, 6.0), 1.0),),
            dims=(10, 20),
            gravity_axis=1,
            grid_mode=GridMode.ALL_BOUNDARIES,
            color=(255, 165, 0),
        )
        self.assertEqual(len(segments), 4)
        self.assertEqual(
            {(segment.axis, segment.side) for segment in segments},
            {(0, "-"), (0, "+"), (1, "-"), (1, "+")},
        )
        self.assertTrue(any(segment.start[0] == 0.0 for segment in segments))
        self.assertTrue(any(segment.start[0] == 10.0 for segment in segments))
        self.assertTrue(any(segment.start[1] == 0.0 for segment in segments))
        self.assertTrue(any(segment.start[1] == 20.0 for segment in segments))

    def test_3d_bottom_boundary_face_primitives_exist(self) -> None:
        faces = build_boundary_projection_face_primitives(
            cells=(((1.0, 2.0, 3.0), 1.0),),
            dims=(6, 12, 6),
            gravity_axis=1,
            grid_mode=GridMode.BOTTOM_BOUNDARY,
            project_raw=_oblique_project,
            transform_raw=_identity_transform,
            depth_denominator=lambda _depth: 1.0,
            color=(255, 0, 0),
        )
        self.assertEqual(len(faces), 1)
        self.assertEqual(len(faces[0].polygon), 4)

    def test_3d_all_boundary_face_primitives_cover_all_faces(self) -> None:
        faces = build_boundary_projection_face_primitives(
            cells=(((1.0, 2.0, 3.0), 1.0),),
            dims=(6, 12, 6),
            gravity_axis=1,
            grid_mode=GridMode.ALL_BOUNDARIES,
            project_raw=_oblique_project,
            transform_raw=_identity_transform,
            depth_denominator=lambda _depth: 1.0,
            color=(0, 255, 0),
        )
        self.assertEqual(len(faces), 6)

    def test_3d_projection_guides_render_in_gameplay_and_explorer(self) -> None:
        board_rect = pygame.Rect(0, 0, 900, 680)
        camera = front3d_render.Camera3D(
            projection=front3d_render.ProjectionMode3D.ORTHOGRAPHIC,
            yaw_deg=32.0,
            pitch_deg=-26.0,
            zoom=84.0,
            auto_fit_once=False,
        )
        for cfg in (
            GameConfigND(dims=(6, 12, 6), gravity_axis=1, speed_level=1),
            GameConfigND(
                dims=(6, 12, 6),
                gravity_axis=1,
                speed_level=1,
                exploration_mode=True,
                explorer_topology_profile=projective_space_profile_3d(),
            ),
        ):
            with self.subTest(exploration=cfg.exploration_mode):
                state = frontend_nd_state.create_initial_state(cfg)
                state.current_piece = ActivePieceND.from_shape(
                    PieceShapeND("dot3", ((0, 0, 0),), color_id=6),
                    pos=(2, 3, 2),
                )
                presentation = front3d_render._build_board_presentation_3d(
                    state,
                    camera,
                    board_rect,
                    grid_mode=GridMode.BOTTOM_BOUNDARY,
                    piece_render_state=None,
                )
                faces = front3d_render._projection_guide_primitives_3d(
                    state=state,
                    presentation=presentation,
                    grid_mode=GridMode.BOTTOM_BOUNDARY,
                    piece_render_state=None,
                )
                self.assertTrue(faces)

    def test_4d_projection_guides_render_in_gameplay_and_explorer(self) -> None:
        view = front4d_game.LayerView3D(yaw_deg=32.0, pitch_deg=-26.0)
        draw_rect = pygame.Rect(0, 0, 420, 320)
        for cfg in (
            GameConfigND(dims=(6, 12, 6, 3), gravity_axis=1, speed_level=1),
            GameConfigND(
                dims=(6, 12, 6, 3),
                gravity_axis=1,
                speed_level=1,
                exploration_mode=True,
                explorer_topology_profile=projective_space_profile_4d(),
            ),
        ):
            with self.subTest(exploration=cfg.exploration_mode):
                state = frontend_nd_state.create_initial_state(cfg)
                state.current_piece = ActivePieceND.from_shape(
                    PieceShapeND("dot4", ((0, 0, 0, 0),), color_id=5),
                    pos=(2, 3, 2, 1),
                )
                basis = front4d_render._basis_for_view(view, cfg.dims)
                layer_value, _ = front4d_render._map_coord_to_layer_cell3(
                    (2.0, 3.0, 2.0, 1.0),
                    dims4=cfg.dims,
                    basis=basis,
                )
                layer_index = front4d_render._layer_index_if_discrete(layer_value)
                self.assertIsNotNone(layer_index)
                assert layer_index is not None
                presentation = front4d_render._build_layer_presentation(
                    state=state,
                    view=view,
                    draw_rect=draw_rect,
                    layer_index=layer_index,
                    basis=basis,
                    grid_mode=GridMode.ALL_BOUNDARIES,
                    piece_render_state=None,
                )
                faces = front4d_render._projection_guide_faces_4d(
                    state=state,
                    layer_index=layer_index,
                    basis=basis,
                    view=view,
                    presentation=presentation,
                    grid_mode=GridMode.ALL_BOUNDARIES,
                    piece_render_state=None,
                )
                self.assertTrue(faces)


if __name__ == "__main__":
    unittest.main()
