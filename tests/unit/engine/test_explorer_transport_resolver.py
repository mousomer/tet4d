from __future__ import annotations

import unittest

from tet4d.engine.core.model import BoardND
from tet4d.engine.gameplay.game2d import GameConfig, GameState
from tet4d.engine.gameplay.game_nd import GameConfigND, GameStateND
from tet4d.engine.gameplay.pieces2d import ActivePiece2D, PieceShape2D
from tet4d.engine.gameplay.pieces_nd import ActivePieceND, PieceShapeND
from tet4d.engine.topology_explorer import (
    CELLWISE_DEFORMATION,
    MoveStep,
    RIGID_TRANSFORM,
    build_explorer_transport_resolver,
    movement_steps_for_dimension,
    neighbors_for_cell,
)
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    mobius_strip_profile_2d,
    projective_plane_profile_2d,
    projective_space_profile_3d,
    sphere_profile_2d,
    sphere_profile_3d,
    sphere_profile_4d,
    swap_xw_profile_4d,
    swapped_xz_profile_3d,
)


def _reverse_exit_step(traversal) -> MoveStep:
    delta = 1 if traversal.target_boundary.side == "+" else -1
    return MoveStep(axis=traversal.target_boundary.axis, delta=delta)


def _seams_by_source_label(resolver) -> dict[str, object]:
    return {seam.source_boundary.label: seam for seam in resolver.directed_seams}


class TestExplorerTransportResolver(unittest.TestCase):
    def test_same_axis_wrap_transport_2d(self) -> None:
        resolver = build_explorer_transport_resolver(
            axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
            (4, 4),
        )

        result = resolver.resolve_cell_step((0, 2), MoveStep(axis=0, delta=-1))

        self.assertEqual(result.target, (3, 2))
        self.assertIsNotNone(result.traversal)
        self.assertEqual(result.traversal.glue_id, "wrap_0")
        self.assertEqual(result.traversal.source_boundary.label, "x-")
        self.assertEqual(result.traversal.target_boundary.label, "x+")
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(result.frame_transform.permutation, (0, 1))
        self.assertEqual(result.frame_transform.translation, (3, 0))
        self.assertEqual(result.frame_transform.apply_absolute((0, 2)), (3, 2))

    def test_orientation_reversal_transport_2d(self) -> None:
        resolver = build_explorer_transport_resolver(
            mobius_strip_profile_2d(),
            (6, 6),
        )

        result = resolver.resolve_cell_step((0, 1), MoveStep(axis=0, delta=-1))

        self.assertEqual(result.target, (5, 4))
        self.assertIsNotNone(result.traversal)
        self.assertEqual(result.traversal.glue_id, "mobius_x")
        self.assertEqual(result.traversal.source_boundary.label, "x-")
        self.assertEqual(result.traversal.target_boundary.label, "x+")
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(result.frame_transform.permutation, (0, 1))
        self.assertEqual(result.frame_transform.signs, (-1, -1))
        self.assertEqual(result.frame_transform.translation, (5, 5))
        self.assertEqual(result.frame_transform.apply_absolute((0, 1)), (5, 4))

    def test_projective_plane_materializes_all_directed_boundary_crossings(
        self,
    ) -> None:
        resolver = build_explorer_transport_resolver(
            projective_plane_profile_2d(),
            (4, 4),
        )

        self.assertEqual(len(resolver.directed_seams), 4)
        self.assertEqual(
            {
                (seam.source_boundary.label, seam.target_boundary.label)
                for seam in resolver.directed_seams
            },
            {
                ("x-", "x+"),
                ("x+", "x-"),
                ("y-", "y+"),
                ("y+", "y-"),
            },
        )

    def test_independent_seam_pairs_do_not_overwrite_each_other(self) -> None:
        resolver = build_explorer_transport_resolver(
            axis_wrap_profile(dimension=2, wrapped_axes=(0, 1)),
            (5, 4),
        )

        seams = _seams_by_source_label(resolver)

        self.assertEqual(set(seams), {"x-", "x+", "y-", "y+"})
        self.assertEqual(seams["x-"].target_boundary.label, "x+")
        self.assertEqual(seams["x+"].target_boundary.label, "x-")
        self.assertEqual(seams["y-"].target_boundary.label, "y+")
        self.assertEqual(seams["y+"].target_boundary.label, "y-")

    def test_projective_directed_crossings_roundtrip_entire_boundary(self) -> None:
        resolver = build_explorer_transport_resolver(
            projective_plane_profile_2d(),
            (4, 4),
        )
        seams = _seams_by_source_label(resolver)

        for seam in resolver.directed_seams:
            inverse = seams[seam.target_boundary.label]
            with self.subTest(source=seam.source_boundary.label):
                for source_coord, target_coord in seam.boundary_coord_map:
                    self.assertEqual(
                        inverse.target_for_source_coord(target_coord),
                        source_coord,
                    )
                    self.assertEqual(
                        inverse.frame_transform.apply_absolute(target_coord),
                        source_coord,
                    )

    def test_projective_space_3d_keeps_all_directed_seam_families(self) -> None:
        resolver = build_explorer_transport_resolver(
            projective_space_profile_3d(),
            (5, 4, 6),
        )

        self.assertEqual(len(resolver.directed_seams), 6)
        self.assertEqual(
            {seam.source_boundary.label for seam in resolver.directed_seams},
            {"x-", "x+", "y-", "y+", "z-", "z+"},
        )

    def test_cross_axis_transport_3d(self) -> None:
        resolver = build_explorer_transport_resolver(
            swapped_xz_profile_3d(),
            (4, 4, 4),
        )

        result = resolver.resolve_cell_step((0, 1, 2), MoveStep(axis=0, delta=-1))

        self.assertEqual(result.target, (2, 1, 3))
        self.assertIsNotNone(result.traversal)
        self.assertEqual(result.traversal.glue_id, "xz_swap")
        self.assertEqual(result.traversal.source_boundary.label, "x-")
        self.assertEqual(result.traversal.target_boundary.label, "z+")
        self.assertEqual(result.traversal.entry_step.label, "z-")
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(result.frame_transform.permutation, (2, 1, 0))
        self.assertEqual(result.frame_transform.signs, (-1, 1, 1))
        self.assertEqual(result.frame_transform.translation, (0, 0, 3))
        self.assertEqual(result.frame_transform.apply_absolute((0, 1, 2)), (2, 1, 3))

    def test_cross_axis_transport_4d(self) -> None:
        resolver = build_explorer_transport_resolver(
            swap_xw_profile_4d(),
            (4, 4, 4, 4),
        )

        result = resolver.resolve_cell_step((0, 1, 2, 1), MoveStep(axis=0, delta=-1))

        self.assertEqual(result.target, (1, 1, 1, 3))
        self.assertIsNotNone(result.traversal)
        self.assertEqual(result.traversal.glue_id, "swap_xw_4d")
        self.assertEqual(result.traversal.source_boundary.label, "x-")
        self.assertEqual(result.traversal.target_boundary.label, "w+")
        self.assertEqual(result.traversal.entry_step.label, "w-")
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(result.frame_transform.permutation, (3, 2, 0, 1))
        self.assertEqual(result.frame_transform.signs, (-1, 1, -1, 1))
        self.assertEqual(result.frame_transform.translation, (3, 0, 0, 3))
        self.assertEqual(
            result.frame_transform.apply_absolute((0, 1, 2, 1)),
            (1, 1, 1, 3),
        )

    def test_sphere_like_transport_routes_cross_axis_seams_consistently(self) -> None:
        cases = (
            (
                "sphere_2d",
                sphere_profile_2d(),
                (8, 8),
                (7, 7),
                MoveStep(axis=1, delta=1),
                (7, 0),
                "y+",
                "x+",
                (1, 0),
                (-1, -1),
            ),
            (
                "sphere_3d",
                sphere_profile_3d(),
                (4, 4, 4),
                (3, 3, 0),
                MoveStep(axis=1, delta=1),
                (3, 3, 0),
                "y+",
                "x+",
                (2, 0, 1),
                (-1, -1, -1),
            ),
            (
                "sphere_4d",
                sphere_profile_4d(),
                (4, 4, 4, 4),
                (3, 3, 1, 0),
                MoveStep(axis=1, delta=1),
                (3, 3, 2, 0),
                "y+",
                "x+",
                (3, 0, 2, 1),
                (-1, -1, -1, -1),
            ),
        )

        for (
            label,
            profile,
            dims,
            coord,
            step,
            expected_target,
            expected_source,
            expected_dest,
            expected_permutation,
            expected_signs,
        ) in cases:
            with self.subTest(case=label):
                resolver = build_explorer_transport_resolver(profile, dims)

                forward = resolver.resolve_cell_step(coord, step)

                self.assertEqual(forward.target, expected_target)
                self.assertIsNotNone(forward.traversal)
                self.assertEqual(forward.traversal.source_boundary.label, expected_source)
                self.assertEqual(forward.traversal.target_boundary.label, expected_dest)
                self.assertIsNotNone(forward.frame_transform)
                self.assertEqual(
                    forward.frame_transform.permutation,
                    expected_permutation,
                )
                self.assertEqual(forward.frame_transform.signs, expected_signs)

                reverse = resolver.resolve_cell_step(
                    forward.target,
                    _reverse_exit_step(forward.traversal),
                )
                self.assertEqual(reverse.target, coord)
                self.assertIsNotNone(reverse.traversal)
                self.assertEqual(reverse.traversal.glue_id, forward.traversal.glue_id)

    def test_roundtrip_seam_consistency(self) -> None:
        cases = (
            (
                axis_wrap_profile(dimension=2, wrapped_axes=(0,)),
                (4, 4),
                (0, 2),
                MoveStep(axis=0, delta=-1),
            ),
            (
                mobius_strip_profile_2d(),
                (6, 6),
                (0, 1),
                MoveStep(axis=0, delta=-1),
            ),
            (
                swapped_xz_profile_3d(),
                (4, 4, 4),
                (0, 1, 2),
                MoveStep(axis=0, delta=-1),
            ),
            (
                swap_xw_profile_4d(),
                (4, 4, 4, 4),
                (0, 1, 2, 1),
                MoveStep(axis=0, delta=-1),
            ),
        )

        for profile, dims, coord, step in cases:
            with self.subTest(dims=dims, coord=coord, step=step.label):
                resolver = build_explorer_transport_resolver(profile, dims)
                forward = resolver.resolve_cell_step(coord, step)
                self.assertIsNotNone(forward.traversal)
                reverse = resolver.resolve_cell_step(
                    forward.target,
                    _reverse_exit_step(forward.traversal),
                )
                self.assertEqual(reverse.target, coord)
                self.assertIsNotNone(reverse.traversal)
                self.assertEqual(reverse.traversal.glue_id, forward.traversal.glue_id)
                self.assertEqual(
                    reverse.traversal.source_boundary,
                    forward.traversal.target_boundary,
                )
                self.assertEqual(
                    reverse.traversal.target_boundary,
                    forward.traversal.source_boundary,
                )

    def test_torus_chart_split_piece_step_stays_rigidly_coherent(self) -> None:
        resolver = build_explorer_transport_resolver(
            axis_wrap_profile(dimension=2, wrapped_axes=(1,)),
            (4, 4),
        )

        result = resolver.resolve_piece_step(
            ((0, 0), (0, 1)),
            MoveStep(axis=1, delta=-1),
        )

        self.assertEqual(result.kind, CELLWISE_DEFORMATION)
        self.assertTrue(result.rigidly_coherent)
        self.assertEqual(result.moved_cells, ((0, 3), (0, 0)))

    def test_projective_pair_can_move_rigidly_when_all_cells_cross_same_seam(
        self,
    ) -> None:
        resolver = build_explorer_transport_resolver(
            projective_plane_profile_2d(),
            (4, 4),
        )

        result = resolver.resolve_piece_step(
            ((0, 1), (0, 2)),
            MoveStep(axis=0, delta=-1),
        )

        self.assertEqual(result.kind, RIGID_TRANSFORM)
        self.assertEqual(result.moved_cells, ((3, 2), (3, 1)))
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(
            result.frame_transform.apply_absolute((0, 1)),
            (3, 2),
        )
        self.assertEqual(
            result.frame_transform.apply_absolute((0, 2)),
            (3, 1),
        )

    def test_piece_step_preserves_rigid_cross_axis_pair_4d(self) -> None:
        resolver = build_explorer_transport_resolver(
            swap_xw_profile_4d(),
            (4, 4, 4, 4),
        )

        result = resolver.resolve_piece_step(
            ((0, 1, 2, 1), (0, 2, 2, 1)),
            MoveStep(axis=0, delta=-1),
        )

        self.assertEqual(result.kind, RIGID_TRANSFORM)
        self.assertEqual(result.moved_cells, ((1, 1, 1, 3), (1, 1, 2, 3)))
        self.assertIsNotNone(result.frame_transform)
        self.assertEqual(
            result.frame_transform.apply_absolute((0, 1, 2, 1)),
            (1, 1, 1, 3),
        )
        self.assertEqual(
            result.frame_transform.apply_absolute((0, 2, 2, 1)),
            (1, 1, 2, 3),
        )


class TestStage35TopologySemantics(unittest.TestCase):
    def test_explorer_y_seam_traversal_does_not_become_play_drop_legality_2d(
        self,
    ) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(1,))
        shape = PieceShape2D("dot", [(0, 0)], color_id=5)
        explorer_cfg = GameConfig(
            width=4,
            height=4,
            exploration_mode=True,
            explorer_topology_profile=profile,
        )
        play_cfg = GameConfig(
            width=4,
            height=4,
            exploration_mode=False,
            explorer_topology_profile=profile,
        )
        explorer_state = GameState(config=explorer_cfg, board=BoardND((4, 4)))
        play_state = GameState(config=play_cfg, board=BoardND((4, 4)))
        explorer_state.board.cells.clear()
        play_state.board.cells.clear()
        explorer_state.current_piece = ActivePiece2D(shape, pos=(1, 3), rotation=0)
        play_state.current_piece = ActivePiece2D(shape, pos=(1, 3), rotation=0)

        self.assertTrue(explorer_state.try_move(0, 1))
        self.assertEqual(explorer_state.current_piece.cells(), [(1, 0)])
        self.assertFalse(play_state.try_soft_drop())
        play_state.hard_drop()

        self.assertEqual(play_state.board.cells, {(1, 3): 5})

    def test_explorer_y_seam_traversal_does_not_become_play_drop_legality_nd(
        self,
    ) -> None:
        profile = axis_wrap_profile(dimension=3, wrapped_axes=(1,))
        shape = PieceShapeND("dot", ((0, 0, 0),), color_id=6)
        explorer_cfg = GameConfigND(
            dims=(4, 4, 3),
            gravity_axis=1,
            exploration_mode=True,
            explorer_topology_profile=profile,
        )
        play_cfg = GameConfigND(
            dims=(4, 4, 3),
            gravity_axis=1,
            exploration_mode=False,
            explorer_topology_profile=profile,
        )
        explorer_state = GameStateND(config=explorer_cfg, board=BoardND((4, 4, 3)))
        play_state = GameStateND(config=play_cfg, board=BoardND((4, 4, 3)))
        explorer_state.board.cells.clear()
        play_state.board.cells.clear()
        explorer_state.current_piece = ActivePieceND.from_shape(
            shape,
            pos=(1, 3, 1),
        )
        play_state.current_piece = ActivePieceND.from_shape(shape, pos=(1, 3, 1))

        self.assertTrue(explorer_state.try_move_axis(1, 1))
        self.assertEqual(explorer_state.current_piece.cells(), [(1, 0, 1)])
        self.assertFalse(play_state.try_soft_drop())
        play_state.hard_drop()

        self.assertEqual(play_state.board.cells, {(1, 3, 1): 6})

    def test_non_gravity_side_seams_remain_play_translation_legal(self) -> None:
        profile = axis_wrap_profile(dimension=3, wrapped_axes=(0,))
        cfg = GameConfigND(
            dims=(4, 4, 3),
            gravity_axis=1,
            exploration_mode=False,
            explorer_topology_profile=profile,
        )
        state = GameStateND(config=cfg, board=BoardND((4, 4, 3)))
        state.board.cells.clear()
        shape = PieceShapeND("dot", ((0, 0, 0),), color_id=7)
        state.current_piece = ActivePieceND.from_shape(shape, pos=(3, 2, 1))

        self.assertTrue(state.try_move_axis(0, 1))

        self.assertEqual(state.current_piece.cells(), [(0, 2, 1)])

    def test_torus_neighbors_match_resolver_targets_for_every_cell(self) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(0, 1))
        dims = (3, 4)
        resolver = build_explorer_transport_resolver(profile, dims)
        steps = tuple(movement_steps_for_dimension(2))

        for x in range(dims[0]):
            for y in range(dims[1]):
                coord = (x, y)
                with self.subTest(coord=coord):
                    graph_edges = {
                        edge.step.label: edge.target
                        for edge in neighbors_for_cell(profile, dims=dims, coord=coord)
                    }
                    resolver_edges = {
                        step.label: resolver.resolve_cell_step(coord, step).target
                        for step in steps
                    }
                    self.assertEqual(graph_edges, resolver_edges)
                    self.assertEqual(len(graph_edges), 4)

    def test_cross_axis_seam_records_entry_step_and_reverse_exit(self) -> None:
        profile = swapped_xz_profile_3d()
        dims = (4, 4, 4)
        resolver = build_explorer_transport_resolver(profile, dims)
        forward = resolver.resolve_cell_step((0, 1, 2), MoveStep(axis=0, delta=-1))
        self.assertIsNotNone(forward.traversal)

        inward = resolver.resolve_cell_step(
            forward.target,
            forward.traversal.entry_step,
        )
        reverse = resolver.resolve_cell_step(
            forward.target,
            MoveStep(axis=2, delta=1),
        )

        self.assertEqual(forward.target, (2, 1, 3))
        self.assertEqual(forward.traversal.source_boundary.label, "x-")
        self.assertEqual(forward.traversal.target_boundary.label, "z+")
        self.assertEqual(forward.traversal.entry_step.label, "z-")
        self.assertEqual(inward.target, (2, 1, 2))
        self.assertIsNone(inward.traversal)
        self.assertEqual(reverse.target, (0, 1, 2))


if __name__ == "__main__":
    unittest.main()
