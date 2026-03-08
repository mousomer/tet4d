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
    explorer_presets_for_dimension,
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

    def test_2d_presets_include_classic_surface_examples(self) -> None:
        presets = explorer_presets_for_dimension(2)
        preset_ids = {preset.preset_id for preset in presets}
        self.assertIn("torus_2d", preset_ids)
        self.assertIn("mobius_2d", preset_ids)
        self.assertIn("klein_2d", preset_ids)
        self.assertIn("projective_2d", preset_ids)
        self.assertIn("sphere_2d", preset_ids)
        unsafe_ids = {preset.preset_id for preset in presets if preset.unsafe}
        self.assertIn("projective_2d", unsafe_ids)
        self.assertIn("sphere_2d", unsafe_ids)


    def test_3d_presets_include_unsafe_projective_and_sphere(self) -> None:
        presets = explorer_presets_for_dimension(3)
        preset_ids = {preset.preset_id for preset in presets}
        self.assertIn("projective_3d", preset_ids)
        self.assertIn("sphere_3d", preset_ids)
        unsafe_ids = {preset.preset_id for preset in presets if preset.unsafe}
        self.assertIn("projective_3d", unsafe_ids)
        self.assertIn("sphere_3d", unsafe_ids)


    def test_4d_presets_include_full_wrap_and_twist(self) -> None:
        presets = explorer_presets_for_dimension(4)
        preset_ids = {preset.preset_id for preset in presets}
        self.assertIn("full_wrap_4d", preset_ids)
        self.assertIn("twist_y_4d", preset_ids)
        self.assertIn("projective_4d", preset_ids)
        self.assertIn("sphere_4d", preset_ids)
        full_wrap = next(preset for preset in presets if preset.preset_id == "full_wrap_4d")
        self.assertEqual(full_wrap.profile.dimension, 4)
        self.assertEqual(len(full_wrap.profile.gluings), 4)


    def test_unsafe_projective_and_sphere_presets_validate_for_preview_dims(self) -> None:
        for dimension, projective_id, sphere_id in (
            (2, "projective_2d", "sphere_2d"),
            (3, "projective_3d", "sphere_3d"),
            (4, "projective_4d", "sphere_4d"),
        ):
            presets = {preset.preset_id: preset for preset in explorer_presets_for_dimension(dimension)}
            for preset_id in (projective_id, sphere_id):
                preset = presets[preset_id]
                validated = validate_explorer_topology_profile(
                    preset.profile, dims=tuple(4 for _ in range(dimension))
                )
                self.assertEqual(validated.dimension, dimension)


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
