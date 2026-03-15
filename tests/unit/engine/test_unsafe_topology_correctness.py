from __future__ import annotations

import unittest

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    default_topology_profile_state,
)
from tet4d.engine.runtime.topology_explorer_preview import (
    advance_explorer_probe,
    compile_explorer_topology_preview,
)
from tet4d.engine.runtime.topology_playability_signal import (
    derive_topology_playability_analysis,
)
from tet4d.engine.runtime.topology_playground_launch import (
    build_gameplay_config_from_topology_playground_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    RIGID_PLAYABILITY_BLOCKED,
    TopologyPlaygroundState,
    TopologyPlaygroundTopologyConfig,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile, MoveStep
from tet4d.engine.topology_explorer.presets import (
    full_wrap_profile_3d,
    full_wrap_profile_4d,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    projective_space_profile_4d,
    sphere_profile_2d,
    sphere_profile_3d,
    sphere_profile_4d,
    torus_profile_2d,
)


class TestUnsafeTopologyCorrectness(unittest.TestCase):
    def _playground_state(
        self,
        dimension: int,
        *,
        axis_sizes: tuple[int, ...],
        explorer_profile,
    ) -> TopologyPlaygroundState:
        legacy_profile = default_topology_profile_state(
            dimension=dimension,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        return TopologyPlaygroundState(
            dimension=dimension,
            axis_sizes=axis_sizes,
            topology_config=TopologyPlaygroundTopologyConfig(
                legacy_profile=legacy_profile,
                explorer_profile=explorer_profile,
            ),
        )

    def test_preview_safe_baselines_remain_connected_across_dimensions(self) -> None:
        cases = (
            ("bounded_2d", ExplorerTopologyProfile(dimension=2, gluings=()), (4, 4), 0),
            ("torus_2d", torus_profile_2d(), (4, 4), 1),
            (
                "bounded_3d",
                ExplorerTopologyProfile(dimension=3, gluings=()),
                (4, 4, 4),
                0,
            ),
            ("wrap_3d", full_wrap_profile_3d(), (4, 4, 4), 1),
            (
                "bounded_4d",
                ExplorerTopologyProfile(dimension=4, gluings=()),
                (4, 4, 4, 4),
                0,
            ),
            ("wrap_4d", full_wrap_profile_4d(), (4, 4, 4, 4), 1),
        )

        for label, profile, dims, min_traversals in cases:
            with self.subTest(case=label):
                preview = compile_explorer_topology_preview(
                    profile,
                    dims=dims,
                    source="unsafe_correctness_test",
                )
                graph = preview["movement_graph"]
                self.assertEqual(graph["component_count"], 1)
                if min_traversals == 0:
                    self.assertEqual(graph["boundary_traversal_count"], 0)
                else:
                    self.assertGreaterEqual(
                        graph["boundary_traversal_count"],
                        min_traversals,
                    )

    def test_projective_probe_traversal_stays_available_across_dimensions(self) -> None:
        cases = (
            (
                "projective_2d",
                projective_plane_profile_2d(),
                (4, 4),
                (0, 0),
                (3, 3),
            ),
            (
                "projective_3d",
                projective_space_profile_3d(),
                (4, 4, 4),
                (0, 0, 0),
                (3, 3, 3),
            ),
            (
                "projective_4d",
                projective_space_profile_4d(),
                (4, 4, 4, 4),
                (0, 0, 0, 0),
                (3, 3, 3, 3),
            ),
        )

        for label, profile, dims, coord, expected_target in cases:
            with self.subTest(case=label):
                target, result = advance_explorer_probe(
                    profile,
                    dims=dims,
                    coord=coord,
                    step_label="x-",
                )
                self.assertEqual(target, expected_target)
                self.assertFalse(result["blocked"])
                self.assertEqual(result["traversal"]["glue_id"], "projective_0")
                self.assertEqual(result["traversal"]["source_boundary"], "x-")
                self.assertEqual(result["traversal"]["target_boundary"], "x+")

    def test_sphere_invalid_dims_surface_explicitly_across_dimensions(self) -> None:
        cases = (
            ("sphere_2d", sphere_profile_2d(), (5, 4)),
            ("sphere_3d", sphere_profile_3d(), (4, 5, 6)),
            ("sphere_4d", sphere_profile_4d(), (4, 5, 6, 7)),
        )

        for label, profile, dims in cases:
            with self.subTest(case=label):
                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported for current board dimensions",
                ):
                    compile_explorer_topology_preview(
                        profile,
                        dims=dims,
                        source="unsafe_correctness_test",
                    )

    def test_play_launch_keeps_projective_profiles_across_dimensions(self) -> None:
        cases = (
            ("projective_2d", 2, (4, 4), projective_plane_profile_2d()),
            ("projective_3d", 3, (4, 4, 4), projective_space_profile_3d()),
            ("projective_4d", 4, (4, 4, 4, 4), projective_space_profile_4d()),
        )

        for label, dimension, dims, profile in cases:
            with self.subTest(case=label):
                state = self._playground_state(
                    dimension,
                    axis_sizes=dims,
                    explorer_profile=profile,
                )
                cfg = build_gameplay_config_from_topology_playground_state(state)
                preview = compile_explorer_topology_preview(
                    profile,
                    dims=dims,
                    source="unsafe_correctness_test",
                )
                analysis = derive_topology_playability_analysis(state, preview=preview)
                if dimension == 2:
                    self.assertIsInstance(cfg, GameConfig)
                else:
                    self.assertIsInstance(cfg, GameConfigND)
                self.assertIs(cfg.explorer_topology_profile, profile)
                self.assertIsNotNone(cfg.explorer_transport)
                self.assertFalse(cfg.explorer_rigid_play_enabled)
                probe_target, probe_result = advance_explorer_probe(
                    profile,
                    dims=dims,
                    coord=tuple(0 for _ in dims),
                    step_label="x-",
                )
                transport_result = cfg.explorer_transport.resolve_cell_step(
                    tuple(0 for _ in dims),
                    MoveStep(axis=0, delta=-1),
                )
                self.assertEqual(transport_result.target, probe_target)
                self.assertEqual(
                    transport_result.traversal.glue_id,
                    probe_result["traversal"]["glue_id"],
                )
                self.assertEqual(analysis.rigid_playability, RIGID_PLAYABILITY_BLOCKED)

    def test_projective_gameplay_allows_non_flat_cellwise_move_in_auto_mode(
        self,
    ) -> None:
        cases = (
            (
                2,
                (4, 4),
                projective_plane_profile_2d(),
                (0, 0),
                ((0, 0), (1, 0)),
            ),
            (
                3,
                (4, 4, 4),
                projective_space_profile_3d(),
                (0, 0, 0),
                ((0, 0, 0), (1, 0, 0)),
            ),
            (
                4,
                (4, 4, 4, 4),
                projective_space_profile_4d(),
                (0, 0, 0, 0),
                ((0, 0, 0, 0), (1, 0, 0, 0)),
            ),
        )

        for dimension, dims, profile, origin, blocks in cases:
            with self.subTest(dimension=dimension, dims=dims):
                playground_state = self._playground_state(
                    dimension,
                    axis_sizes=dims,
                    explorer_profile=profile,
                )
                cfg = build_gameplay_config_from_topology_playground_state(
                    playground_state
                )
                expected = cfg.explorer_transport.resolve_piece_step(
                    tuple(
                        tuple(origin[axis] + block[axis] for axis in range(len(dims)))
                        for block in blocks
                    ),
                    MoveStep(axis=0, delta=-1),
                )
                self.assertEqual(expected.kind, "cellwise_deformation")
                self.assertFalse(cfg.explorer_rigid_play_enabled)

                if dimension == 2:
                    state = GameState(config=cfg, board=BoardND(dims))
                    state.board.cells.clear()
                    state.current_piece = ActivePiece2D(
                        shape=PieceShape2D("pair2", list(blocks), color_id=4),
                        pos=origin,
                        rotation=0,
                    )
                    state.try_move(-1, 0)
                    actual_cells = tuple(sorted(state.current_piece.cells()))
                else:
                    state = GameStateND(config=cfg, board=BoardND(dims))
                    state.board.cells.clear()
                    state.current_piece = ActivePieceND.from_shape(
                        PieceShapeND("pair_nd", tuple(blocks), color_id=4),
                        pos=origin,
                    )
                    self.assertTrue(state.try_move_axis(0, -1))
                    actual_cells = tuple(sorted(state.current_piece.cells()))

                self.assertEqual(actual_cells, tuple(sorted(expected.moved_cells)))


    def test_play_launch_rejects_invalid_non_bijective_profiles_across_dimensions(
        self,
    ) -> None:
        cases = (
            ("sphere_2d", 2, (5, 4), sphere_profile_2d()),
            ("sphere_3d", 3, (4, 5, 6), sphere_profile_3d()),
            ("sphere_4d", 4, (4, 5, 6, 7), sphere_profile_4d()),
        )

        for label, dimension, dims, profile in cases:
            with self.subTest(case=label):
                state = self._playground_state(
                    dimension,
                    axis_sizes=dims,
                    explorer_profile=profile,
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported for current board dimensions",
                ):
                    build_gameplay_config_from_topology_playground_state(state)
