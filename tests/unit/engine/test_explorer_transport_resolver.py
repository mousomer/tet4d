from __future__ import annotations

import unittest

from tet4d.engine.topology_explorer import (
    MoveStep,
    RIGID_TRANSFORM,
    build_explorer_transport_resolver,
)
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    mobius_strip_profile_2d,
    projective_plane_profile_2d,
    projective_space_profile_3d,
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


if __name__ == "__main__":
    unittest.main()
