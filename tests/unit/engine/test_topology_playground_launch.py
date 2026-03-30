from __future__ import annotations

import inspect
import unittest
from unittest import mock

from tet4d.engine.gameplay.api import (
    piece_set_2d_options_gameplay,
    piece_set_options_for_dimension_gameplay,
)
from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.topology_designer import GAMEPLAY_MODE_NORMAL
from tet4d.engine.runtime import topology_playground_launch
from tet4d.engine.runtime.topology_explorer_preview import advance_explorer_probe
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAY_MODE_OFF,
    RIGID_PLAY_MODE_ON,
    default_topology_playground_state,
)
from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
    MoveStep,
)
from tet4d.engine.topology_explorer.glue_model import SIDE_POS
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    projective_space_profile_4d,
    sphere_profile_3d,
    sphere_profile_4d,
    swap_xw_profile_4d,
    twisted_y_profile_3d,
    twisted_y_profile_4d,
)
from tet4d.ui.pygame.front2d_input import apply_2d_gameplay_action
from tet4d.ui.pygame import frontend_nd_input
from tet4d.ui.pygame.keybindings import EXPLORER_KEYS_3D, KEYS_3D
from tet4d.ui.pygame.topology_lab.play_launch import (
    _topology_playground_return_menu,
    launch_playground_state_gameplay,
)


class TestTopologyPlaygroundLaunchConfig(unittest.TestCase):
    @staticmethod
    def _custom_cross_axis_y_profile_3d() -> ExplorerTopologyProfile:
        return ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="custom_yz",
                    source=BoundaryRef(dimension=3, axis=1, side=SIDE_POS),
                    target=BoundaryRef(dimension=3, axis=2, side=SIDE_POS),
                    transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                ),
            ),
        )

    @staticmethod
    def _playground_cfg_nd(*, dimension: int, dims: tuple[int, ...], profile):
        state = default_topology_playground_state(
            dimension=dimension,
            axis_sizes=dims,
        )
        state.topology_config.explorer_profile = profile
        return build_gameplay_config_from_topology_playground_state(state)

    @staticmethod
    def _playground_cfg_2d(*, dims: tuple[int, int], profile):
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=dims,
        )
        state.topology_config.explorer_profile = profile
        return build_gameplay_config_from_topology_playground_state(state)

    @staticmethod
    def _nd_state(
        *,
        cfg: GameConfigND,
        shape: PieceShapeND,
        pos: tuple[int, ...],
    ) -> GameStateND:
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        state.current_piece = ActivePieceND.from_shape(shape, pos=pos)
        return state

    @staticmethod
    def _locked_cells_nd(
        shape: PieceShapeND,
        pos: tuple[int, ...],
    ) -> dict[tuple[int, ...], int]:
        piece = ActivePieceND.from_shape(shape, pos=pos)
        return {tuple(coord): shape.color_id for coord in piece.cells()}

    def _assert_grounded_iff_no_legal_drop_step_nd(
        self,
        *,
        cfg: GameConfigND,
        shape: PieceShapeND,
        pos: tuple[int, ...],
        expected_locked_cells: dict[tuple[int, ...], int],
    ) -> None:
        drop_state = self._nd_state(cfg=cfg, shape=shape, pos=pos)
        can_drop = drop_state.try_soft_drop()

        gravity_state = self._nd_state(cfg=cfg, shape=shape, pos=pos)
        gravity_state.step_gravity()

        if can_drop:
            self.assertFalse(gravity_state.board.cells)
            self.assertEqual(
                tuple(sorted(gravity_state.current_piece.cells())),
                tuple(sorted(drop_state.current_piece.cells())),
            )
            return

        self.assertEqual(gravity_state.board.cells, expected_locked_cells)
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in gravity_state.current_piece.cells())
        )

    def _assert_hard_drop_matches_repeated_drop_nd(
        self,
        *,
        cfg: GameConfigND,
        shape: PieceShapeND,
        pos: tuple[int, ...],
    ) -> None:
        repeated_state = self._nd_state(cfg=cfg, shape=shape, pos=pos)
        while repeated_state.try_soft_drop():
            pass
        repeated_state.lock_current_piece()
        if not repeated_state.game_over:
            repeated_state.spawn_new_piece()

        hard_drop_state = self._nd_state(cfg=cfg, shape=shape, pos=pos)
        hard_drop_state.hard_drop()

        self.assertEqual(hard_drop_state.board.cells, repeated_state.board.cells)

    def _assert_sideways_legality_does_not_imply_drop_legality_nd(
        self,
        *,
        cfg: GameConfigND,
        shape: PieceShapeND,
        pos: tuple[int, ...],
        axis: int,
        delta: int,
        expected_cells_after_translation: tuple[tuple[int, ...], ...],
    ) -> None:
        state = self._nd_state(cfg=cfg, shape=shape, pos=pos)
        self.assertTrue(state.try_move_axis(axis, delta))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(expected_cells_after_translation)),
        )
        self.assertFalse(state.try_soft_drop())

    def test_module_stays_ui_free(self) -> None:
        source = inspect.getsource(topology_playground_launch)
        self.assertNotIn("pygame", source)
        self.assertNotIn("tet4d.ui", source)

    def test_build_2d_config_uses_canonical_axis_sizes_and_launch_settings(
        self,
    ) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(12, 18),
        )
        piece_options = piece_set_2d_options_gameplay()
        piece_index = min(2, len(piece_options) - 1)
        state.launch_settings.piece_set_index = piece_index
        state.launch_settings.speed_level = 5
        state.launch_settings.random_mode_index = 1
        state.launch_settings.game_seed = 99

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertIsInstance(cfg, GameConfig)
        self.assertEqual((cfg.width, cfg.height), (12, 18))
        self.assertEqual(cfg.piece_set, piece_options[piece_index])
        self.assertEqual(cfg.speed_level, 5)
        self.assertFalse(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertIsNotNone(cfg.explorer_transport)
        self.assertEqual(cfg.explorer_transport.dims, (12, 18))
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 99)

    def test_build_4d_config_uses_canonical_axis_sizes_and_explorer_profile(
        self,
    ) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(6, 6, 6, 6),
        )
        state.topology_config.explorer_profile = swap_xw_profile_4d()
        piece_options = piece_set_options_for_dimension_gameplay(4)
        piece_index = min(1, len(piece_options) - 1)
        state.launch_settings.piece_set_index = piece_index
        state.launch_settings.speed_level = 6
        state.launch_settings.random_mode_index = 2
        state.launch_settings.game_seed = 1234

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertIsInstance(cfg, GameConfigND)
        self.assertEqual(cfg.dims, (6, 6, 6, 6))
        self.assertEqual(cfg.piece_set_id, piece_options[piece_index])
        self.assertEqual(cfg.speed_level, 6)
        self.assertFalse(cfg.exploration_mode)
        self.assertIs(cfg.explorer_topology_profile, state.explorer_profile)
        self.assertIsNotNone(cfg.explorer_transport)
        self.assertEqual(cfg.explorer_transport.dims, (6, 6, 6, 6))
        self.assertEqual(cfg.topology_mode, state.transport_policy.base_policy.mode)
        self.assertEqual(
            cfg.topology_edge_rules,
            state.transport_policy.base_policy.edge_rules,
        )
        self.assertEqual(cfg.rng_seed, 1234)
        transport_result = cfg.explorer_transport.resolve_cell_step(
            (0, 1, 2, 1),
            MoveStep(axis=0, delta=-1),
        )
        self.assertEqual(transport_result.target, (3, 1, 1, 5))
        self.assertEqual(transport_result.traversal.glue_id, "swap_xw_4d")

    def test_launch_preserves_exact_explorer_transport_mapping(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(4, 4),
        )
        state.topology_config.explorer_profile = projective_plane_profile_2d()

        cfg = build_gameplay_config_from_topology_playground_state(state)
        probe_target, probe_result = advance_explorer_probe(
            state.explorer_profile,
            dims=state.axis_sizes,
            coord=(0, 0),
            step_label="x-",
        )
        transport_result = cfg.explorer_transport.resolve_cell_step(
            (0, 0),
            MoveStep(axis=0, delta=-1),
        )

        self.assertFalse(cfg.explorer_rigid_play_enabled)
        self.assertEqual(transport_result.target, probe_target)
        self.assertEqual(transport_result.target, (3, 3))
        self.assertEqual(
            transport_result.traversal.glue_id,
            probe_result["traversal"]["glue_id"],
        )
        self.assertEqual(
            transport_result.traversal.source_boundary.label,
            probe_result["traversal"]["source_boundary"],
        )
        self.assertEqual(
            transport_result.traversal.target_boundary.label,
            probe_result["traversal"]["target_boundary"],
        )

    def test_launch_rigid_play_setting_can_force_rigid_or_cellwise_transport(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(4, 4),
        )
        state.topology_config.explorer_profile = projective_plane_profile_2d()

        state.launch_settings.rigid_play_mode = RIGID_PLAY_MODE_ON
        rigid_cfg = build_gameplay_config_from_topology_playground_state(state)
        self.assertTrue(rigid_cfg.explorer_rigid_play_enabled)

        state.launch_settings.rigid_play_mode = RIGID_PLAY_MODE_OFF
        cellwise_cfg = build_gameplay_config_from_topology_playground_state(state)
        self.assertFalse(cellwise_cfg.explorer_rigid_play_enabled)

    def test_launch_config_uses_gameplay_bindings_instead_of_explorer_traversal(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
        )
        state.topology_config.explorer_profile = axis_wrap_profile(
            dimension=3,
            wrapped_axes=(0,),
        )

        cfg = build_gameplay_config_from_topology_playground_state(state)

        self.assertEqual(
            frontend_nd_input.gameplay_action_for_key(KEYS_3D["move_x_pos"][0], cfg),
            "move_x_pos",
        )
        self.assertIsNone(
            frontend_nd_input.gameplay_action_for_key(
                EXPLORER_KEYS_3D["move_up"][0],
                cfg,
            )
        )

    def test_launch_config_spawns_playable_piece_above_gravity_axis(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
        )
        state.topology_config.explorer_profile = axis_wrap_profile(
            dimension=3,
            wrapped_axes=(0,),
        )

        cfg = build_gameplay_config_from_topology_playground_state(state)
        gameplay_state = GameStateND(config=cfg, board=BoardND(cfg.dims))

        self.assertIsNotNone(gameplay_state.current_piece)
        self.assertFalse(gameplay_state.game_over)
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in gameplay_state.current_piece.cells())
        )


    def test_launch_preserves_full_projective_directed_seam_family(self) -> None:
        cases = (
            (2, (4, 4), projective_plane_profile_2d(), {"x-", "x+", "y-", "y+"}),
            (
                3,
                (5, 4, 6),
                projective_space_profile_3d(),
                {"x-", "x+", "y-", "y+", "z-", "z+"},
            ),
        )

        for dimension, dims, profile, expected_sources in cases:
            with self.subTest(dimension=dimension, dims=dims):
                state = default_topology_playground_state(
                    dimension=dimension,
                    axis_sizes=dims,
                )
                state.topology_config.explorer_profile = profile

                cfg = build_gameplay_config_from_topology_playground_state(state)

                self.assertEqual(
                    len(cfg.explorer_transport.directed_seams),
                    2 * len(state.explorer_profile.active_gluings()),
                )
                self.assertEqual(
                    {
                        seam.source_boundary.label
                        for seam in cfg.explorer_transport.directed_seams
                    },
                    expected_sources,
                )

    def test_builder_rejects_non_explorer_playground_state(self) -> None:
        state = default_topology_playground_state(
            dimension=3,
            axis_sizes=(6, 12, 6),
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )

        with self.assertRaisesRegex(ValueError, "Explorer gameplay mode"):
            build_gameplay_config_from_topology_playground_state(state)

    def test_3d_play_continues_after_bottom_boundary_traversal_on_live_path(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=projective_space_profile_3d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("dot3", ((0, 0, 0),), color_id=5)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 3, 0))

        first = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=1, delta=1),
        )
        self.assertIsNotNone(first.moved_cells)
        self.assertTrue(state.try_move_axis(1, 1))
        self.assertEqual(tuple(sorted(state.current_piece.cells())), tuple(sorted(first.moved_cells)))

        second = cfg.explorer_transport.resolve_piece_step(
            tuple(state.current_piece.cells()),
            MoveStep(axis=1, delta=1),
        )
        self.assertIsNotNone(second.moved_cells)
        state.step_gravity()

        self.assertFalse(state.game_over)
        self.assertFalse(state.board.cells)
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(second.moved_cells)),
        )

    def test_4d_play_continues_after_bottom_boundary_traversal_on_live_path(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=4,
            dims=(4, 4, 4, 4),
            profile=projective_space_profile_4d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("dot4", ((0, 0, 0, 0),), color_id=6)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(0, 3, 0, 0))

        first = cfg.explorer_transport.resolve_piece_step(
            state.current_piece.cells(),
            MoveStep(axis=1, delta=1),
        )
        self.assertIsNotNone(first.moved_cells)
        self.assertTrue(state.try_move_axis(1, 1))
        self.assertEqual(tuple(sorted(state.current_piece.cells())), tuple(sorted(first.moved_cells)))

        second = cfg.explorer_transport.resolve_piece_step(
            tuple(state.current_piece.cells()),
            MoveStep(axis=1, delta=1),
        )
        self.assertIsNotNone(second.moved_cells)
        state.step_gravity()

        self.assertFalse(state.game_over)
        self.assertFalse(state.board.cells)
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            tuple(sorted(second.moved_cells)),
        )

    def test_3d_sphere_play_does_not_continue_drop_through_y_seam(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=sphere_profile_3d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND("sphere_domino3", ((0, 0, 0), (0, 0, 1)), color_id=5)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(3, 3, 0))

        self.assertTrue(state.try_move_axis(1, 1))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            ((3, 2, 0), (3, 3, 0)),
        )

        state.step_gravity()

        self.assertFalse(state.game_over)
        self.assertEqual(
            state.board.cells,
            {
                (3, 2, 0): shape.color_id,
                (3, 3, 0): shape.color_id,
            },
        )
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in state.current_piece.cells())
        )

    def test_4d_sphere_play_does_not_continue_drop_through_y_seam(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=4,
            dims=(4, 4, 4, 4),
            profile=sphere_profile_4d(),
        )
        state = GameStateND(config=cfg, board=BoardND(cfg.dims))
        state.board.cells.clear()
        shape = PieceShapeND(
            "sphere_tri4",
            ((0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 1, 0)),
            color_id=6,
        )
        state.current_piece = ActivePieceND.from_shape(shape, pos=(3, 3, 1, 0))

        self.assertTrue(state.try_move_axis(1, 1))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            ((3, 2, 2, 0), (3, 3, 1, 0), (3, 3, 2, 0)),
        )

        state.step_gravity()

        self.assertFalse(state.game_over)
        self.assertEqual(
            state.board.cells,
            {
                (3, 2, 2, 0): shape.color_id,
                (3, 3, 1, 0): shape.color_id,
                (3, 3, 2, 0): shape.color_id,
            },
        )
        self.assertTrue(
            any(coord[cfg.gravity_axis] < 0 for coord in state.current_piece.cells())
        )

    def test_3d_sphere_play_allows_side_entry_into_bottom_layer_before_lock(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=sphere_profile_3d(),
        )
        shape = PieceShapeND("sphere_vertical", ((0, 0, 0), (0, 1, 0)), color_id=4)
        self._assert_sideways_legality_does_not_imply_drop_legality_nd(
            cfg=cfg,
            shape=shape,
            pos=(2, 2, 0),
            axis=0,
            delta=1,
            expected_cells_after_translation=((3, 2, 0), (3, 3, 0)),
        )

        state = self._nd_state(cfg=cfg, shape=shape, pos=(2, 2, 0))
        self.assertTrue(state.try_move_axis(0, 1))
        state.step_gravity()

        self.assertEqual(
            state.board.cells,
            {
                (3, 2, 0): shape.color_id,
                (3, 3, 0): shape.color_id,
            },
        )

    def test_2d_projective_soft_drop_stays_grounded_when_y_seam_is_drop_illegal(
        self,
    ) -> None:
        cfg = self._playground_cfg_2d(
            dims=(4, 4),
            profile=projective_plane_profile_2d(),
        )
        state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        state.board.cells.clear()
        shape = PieceShape2D("dot", [(0, 0)], color_id=3)
        state.current_piece = ActivePiece2D(shape, pos=(1, 3), rotation=0)

        apply_2d_gameplay_action(state, "soft_drop")

        self.assertEqual(tuple(sorted(state.current_piece.cells())), ((1, 3),))
        self.assertFalse(state.board.cells)

    def test_2d_projective_hard_drop_matches_repeated_drop_legality(self) -> None:
        cfg = self._playground_cfg_2d(
            dims=(4, 4),
            profile=projective_plane_profile_2d(),
        )
        shape = PieceShape2D("dot", [(0, 0)], color_id=3)

        soft_state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        soft_state.board.cells.clear()
        soft_state.current_piece = ActivePiece2D(shape, pos=(1, 3), rotation=0)
        apply_2d_gameplay_action(soft_state, "soft_drop")
        soft_state.hard_drop()

        hard_state = GameState(config=cfg, board=BoardND((cfg.width, cfg.height)))
        hard_state.board.cells.clear()
        hard_state.current_piece = ActivePiece2D(shape, pos=(1, 3), rotation=0)
        hard_state.hard_drop()

        expected_board = {(1, 3): shape.color_id}
        self.assertEqual(soft_state.board.cells, expected_board)
        self.assertEqual(hard_state.board.cells, expected_board)

    def test_3d_twisted_y_play_grounds_from_drop_legality(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=twisted_y_profile_3d(),
        )
        shape = PieceShapeND("twist_dot3", ((0, 0, 0),), color_id=7)
        expected_locked_cells = self._locked_cells_nd(shape, (0, 3, 0))

        self._assert_grounded_iff_no_legal_drop_step_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0),
            expected_locked_cells=expected_locked_cells,
        )
        self._assert_hard_drop_matches_repeated_drop_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0),
        )

    def test_4d_twisted_y_play_grounds_from_drop_legality(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=4,
            dims=(4, 4, 4, 4),
            profile=twisted_y_profile_4d(),
        )
        shape = PieceShapeND("twist_dot4", ((0, 0, 0, 0),), color_id=8)
        expected_locked_cells = self._locked_cells_nd(shape, (0, 3, 0, 0))

        self._assert_grounded_iff_no_legal_drop_step_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0, 0),
            expected_locked_cells=expected_locked_cells,
        )
        self._assert_hard_drop_matches_repeated_drop_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0, 0),
        )

    def test_custom_cross_axis_y_seam_translation_remains_distinct_from_drop(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=self._custom_cross_axis_y_profile_3d(),
        )
        shape = PieceShapeND("custom_dot3", ((0, 0, 0),), color_id=9)

        move_state = self._nd_state(cfg=cfg, shape=shape, pos=(0, 3, 0))
        self.assertTrue(move_state.try_move_axis(1, 1))
        self.assertEqual(tuple(sorted(move_state.current_piece.cells())), ((0, 0, 3),))

        self._assert_grounded_iff_no_legal_drop_step_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0),
            expected_locked_cells=self._locked_cells_nd(shape, (0, 3, 0)),
        )
        self._assert_hard_drop_matches_repeated_drop_nd(
            cfg=cfg,
            shape=shape,
            pos=(0, 3, 0),
        )

    def test_rotation_near_twisted_y_seam_does_not_create_drop_continuation(self) -> None:
        cfg = self._playground_cfg_nd(
            dimension=3,
            dims=(4, 4, 4),
            profile=twisted_y_profile_3d(),
        )
        shape = PieceShapeND(
            "twist_line_x",
            ((-1, 0, 0), (0, 0, 0), (1, 0, 0)),
            color_id=6,
        )
        state = self._nd_state(cfg=cfg, shape=shape, pos=(1, 2, 0))

        self.assertTrue(state.try_rotate(0, 1, 1))
        self.assertEqual(
            tuple(sorted(state.current_piece.cells())),
            ((1, 1, 0), (1, 2, 0), (1, 3, 0)),
        )
        self.assertFalse(state.try_soft_drop())

        rotated_shape = PieceShapeND(
            "twist_line_y",
            ((0, -1, 0), (0, 0, 0), (0, 1, 0)),
            color_id=6,
        )
        self._assert_hard_drop_matches_repeated_drop_nd(
            cfg=cfg,
            shape=rotated_shape,
            pos=(1, 2, 0),
        )


class TestTopologyLabPlayLaunch(unittest.TestCase):
    def test_launch_gameplay_routes_2d_state_to_front2d(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(8, 16),
        )
        screen = object()
        fonts_nd = object()
        fonts_2d = object()
        display_settings = object()
        cfg = object()
        reopened_screen = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_game,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime."
                "capture_windowed_display_settings",
                return_value="captured",
            ) as capture_display,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime.open_display",
                return_value=reopened_screen,
            ) as open_display,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Topology Playground",
                fonts_2d=fonts_2d,
                display_settings=display_settings,
                exploration_mode=False,
            )

        build_cfg.assert_called_once_with(state, exploration_mode=False)

        run_game.assert_called_once_with(
            screen,
            cfg,
            fonts_2d,
            display_settings,
            pause_menu_runner=None,
        )
        capture_display.assert_called_once_with(display_settings)
        open_display.assert_called_once_with("captured", caption="Topology Playground")
        self.assertIs(returned_screen, reopened_screen)
        self.assertEqual(returned_display, "captured")

    def test_launch_gameplay_routes_4d_state_to_front4d(self) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(8, 16, 6, 4),
        )
        screen = object()
        fonts_nd = object()
        cfg = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_2d,
            mock.patch("tet4d.ui.pygame.front3d_game.run_game_loop") as run_3d,
            mock.patch("tet4d.ui.pygame.front4d_game.run_game_loop") as run_4d,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Topology Playground",
                display_settings=None,
                exploration_mode=False,
            )

        build_cfg.assert_called_once_with(state, exploration_mode=False)
        run_2d.assert_not_called()
        run_3d.assert_not_called()
        run_4d.assert_called_once_with(
            screen,
            cfg,
            fonts_nd,
            pause_menu_runner=None,
        )
        self.assertIs(returned_screen, screen)
        self.assertIsNone(returned_display)

    def test_launch_exploration_routes_2d_state_to_front2d(self) -> None:
        state = default_topology_playground_state(
            dimension=2,
            axis_sizes=(8, 16),
        )
        screen = object()
        fonts_nd = object()
        fonts_2d = object()
        display_settings = object()
        cfg = object()
        reopened_screen = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_game,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime."
                "capture_windowed_display_settings",
                return_value="captured",
            ) as capture_display,
            mock.patch(
                "tet4d.ui.pygame.runtime_ui.app_runtime.open_display",
                return_value=reopened_screen,
            ) as open_display,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Topology Playground",
                fonts_2d=fonts_2d,
                display_settings=display_settings,
                exploration_mode=True,
            )

        build_cfg.assert_called_once_with(state, exploration_mode=True)
        run_game.assert_called_once_with(
            screen,
            cfg,
            fonts_2d,
            display_settings,
            pause_menu_runner=_topology_playground_return_menu,
        )
        capture_display.assert_called_once_with(display_settings)
        open_display.assert_called_once_with("captured", caption="Topology Playground")
        self.assertIs(returned_screen, reopened_screen)
        self.assertEqual(returned_display, "captured")

    def test_launch_exploration_routes_4d_state_to_front4d(self) -> None:
        state = default_topology_playground_state(
            dimension=4,
            axis_sizes=(8, 16, 6, 4),
        )
        screen = object()
        fonts_nd = object()
        cfg = object()

        with (
            mock.patch(
                "tet4d.ui.pygame.topology_lab.play_launch."
                "build_gameplay_config_from_topology_playground_state",
                return_value=cfg,
            ) as build_cfg,
            mock.patch("tet4d.ui.pygame.front2d_game.run_game_loop") as run_2d,
            mock.patch("tet4d.ui.pygame.front3d_game.run_game_loop") as run_3d,
            mock.patch("tet4d.ui.pygame.front4d_game.run_game_loop") as run_4d,
        ):
            returned_screen, returned_display = launch_playground_state_gameplay(
                state,
                screen,
                fonts_nd,
                return_caption="Topology Playground",
                display_settings=None,
                exploration_mode=True,
            )

        build_cfg.assert_called_once_with(state, exploration_mode=True)
        run_2d.assert_not_called()
        run_3d.assert_not_called()
        run_4d.assert_called_once_with(
            screen,
            cfg,
            fonts_nd,
            pause_menu_runner=_topology_playground_return_menu,
        )
        self.assertIs(returned_screen, screen)
        self.assertIsNone(returned_display)


if __name__ == "__main__":
    unittest.main()
