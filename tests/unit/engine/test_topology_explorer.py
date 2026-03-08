from __future__ import annotations

import unittest

from tet4d.engine.topology_explorer.glue_map import map_boundary_exit, move_cell
from tet4d.engine.topology_explorer.glue_model import (
    BoundaryTransform,
    ExplorerTopologyProfile,
    MoveStep,
)
from tet4d.engine.topology_explorer.glue_validate import (
    validate_explorer_topology_profile,
)
from tet4d.engine.topology_explorer.movement_graph import build_movement_graph
from tet4d.engine.topology_explorer.presets import (
    axis_wrap_profile,
    klein_bottle_profile_2d,
    mobius_strip_profile_2d,
    pair_boundaries,
    torus_profile_2d,
)


class TestTopologyExplorer(unittest.TestCase):
    def test_boundary_transform_inverse_roundtrip(self) -> None:
        transform = BoundaryTransform(permutation=(2, 0, 1), signs=(-1, 1, -1))
        inverse = transform.inverse()
        self.assertEqual(inverse.permutation, (1, 2, 0))
        self.assertEqual(inverse.signs, (1, -1, -1))

    def test_validation_rejects_duplicate_boundary_ownership(self) -> None:
        profile = ExplorerTopologyProfile(
            dimension=2,
            gluings=(
                pair_boundaries(
                    dimension=2,
                    source_axis=0,
                    source_side="-",
                    target_axis=0,
                    target_side="+",
                    glue_id="g1",
                    transform=BoundaryTransform(permutation=(0,), signs=(1,)),
                ),
                pair_boundaries(
                    dimension=2,
                    source_axis=0,
                    source_side="-",
                    target_axis=1,
                    target_side="+",
                    glue_id="g2",
                    transform=BoundaryTransform(permutation=(0,), signs=(1,)),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            validate_explorer_topology_profile(profile, dims=(4, 4))

    def test_validation_rejects_non_bijective_extent_mapping(self) -> None:
        profile = ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                pair_boundaries(
                    dimension=3,
                    source_axis=0,
                    source_side="-",
                    target_axis=2,
                    target_side="+",
                    glue_id="bad",
                    transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                ),
            ),
        )
        with self.assertRaises(ValueError):
            validate_explorer_topology_profile(profile, dims=(4, 5, 6))

    def test_torus_wrap_maps_across_x_boundary(self) -> None:
        profile = torus_profile_2d()
        self.assertEqual(
            move_cell(
                profile, dims=(4, 3), coord=(3, 1), step=MoveStep(axis=0, delta=1)
            ),
            (0, 1),
        )
        self.assertEqual(
            move_cell(
                profile, dims=(4, 3), coord=(0, 1), step=MoveStep(axis=0, delta=-1)
            ),
            (3, 1),
        )

    def test_mobius_strip_flips_tangent_coordinate(self) -> None:
        profile = mobius_strip_profile_2d()
        self.assertEqual(
            move_cell(
                profile, dims=(4, 3), coord=(3, 0), step=MoveStep(axis=0, delta=1)
            ),
            (0, 2),
        )
        self.assertEqual(
            move_cell(
                profile, dims=(4, 3), coord=(0, 2), step=MoveStep(axis=0, delta=-1)
            ),
            (3, 0),
        )

    def test_boundary_exit_reports_crossing_metadata(self) -> None:
        profile = axis_wrap_profile(dimension=2, wrapped_axes=(0,))
        traversal = map_boundary_exit(
            profile,
            dims=(4, 3),
            coord=(3, 1),
            step=MoveStep(axis=0, delta=1),
        )
        self.assertIsNotNone(traversal)
        assert traversal is not None
        self.assertEqual(traversal.source_boundary.label, "x+")
        self.assertEqual(traversal.target_boundary.label, "x-")
        self.assertEqual(traversal.target_coord, (0, 1))
        self.assertEqual(traversal.entry_step.label, "x+")

    def test_klein_bottle_graph_keeps_four_neighbors_per_cell(self) -> None:
        profile = klein_bottle_profile_2d()
        graph = build_movement_graph(profile, dims=(4, 3))
        self.assertEqual(len(graph[(0, 0)]), 4)
        right_target = next(
            edge.target for edge in graph[(3, 0)] if edge.step.label == "x+"
        )
        up_target = next(
            edge.target for edge in graph[(1, 2)] if edge.step.label == "y+"
        )
        self.assertEqual(right_target, (0, 0))
        self.assertEqual(up_target, (2, 0))


if __name__ == "__main__":
    unittest.main()
