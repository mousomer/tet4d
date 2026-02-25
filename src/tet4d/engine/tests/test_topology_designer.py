from __future__ import annotations

import unittest

from tet4d.engine.topology import (
    EDGE_BOUNDED,
    EDGE_INVERT,
    EDGE_WRAP,
    TOPOLOGY_BOUNDED,
    TopologyPolicy,
)
from tet4d.engine.gameplay.topology_designer import (
    designer_profile_index_by_id,
    designer_profiles_for_dimension,
    resolve_topology_designer_selection,
)


class TestTopologyDesigner(unittest.TestCase):
    def test_custom_per_edge_rules_apply_inversion_only_for_configured_edge(
        self,
    ) -> None:
        policy = TopologyPolicy(
            dims=(4, 8, 4),
            gravity_axis=1,
            mode=TOPOLOGY_BOUNDED,
            edge_rules=(
                (EDGE_INVERT, EDGE_WRAP),  # x: neg invert, pos wrap
                (EDGE_BOUNDED, EDGE_BOUNDED),  # y: bounded
                (EDGE_WRAP, EDGE_WRAP),  # z: wrap
            ),
        )
        # Negative x edge inverts z.
        self.assertEqual(
            policy.map_coord((-1, 3, 1), allow_above_gravity=True), (3, 3, 2)
        )
        # Positive x edge wraps without inversion.
        self.assertEqual(
            policy.map_coord((4, 3, 1), allow_above_gravity=True), (0, 3, 1)
        )

    def test_designer_profiles_load_for_dimensions(self) -> None:
        profiles_2d = designer_profiles_for_dimension(2)
        profiles_4d = designer_profiles_for_dimension(4)
        self.assertGreater(len(profiles_2d), 0)
        self.assertGreaterEqual(len(profiles_4d), len(profiles_2d))

    def test_designer_selection_returns_edge_rules_when_advanced_enabled(self) -> None:
        profile_index = designer_profile_index_by_id(4, "twist_w_pos_only")
        mode, edge_rules, profile = resolve_topology_designer_selection(
            dimension=4,
            gravity_axis=1,
            topology_mode="wrap_all",
            topology_advanced=True,
            profile_index=profile_index,
        )
        self.assertEqual(mode, "wrap_all")
        self.assertIsNotNone(edge_rules)
        self.assertIsNotNone(profile)
        assert edge_rules is not None
        # W-axis index is 3 for 4D.
        self.assertEqual(edge_rules[3], (EDGE_WRAP, EDGE_INVERT))

    def test_designer_selection_disabled_keeps_mode_only(self) -> None:
        mode, edge_rules, profile = resolve_topology_designer_selection(
            dimension=3,
            gravity_axis=1,
            topology_mode="invert_all",
            topology_advanced=False,
            profile_index=2,
        )
        self.assertEqual(mode, "invert_all")
        self.assertIsNone(edge_rules)
        self.assertIsNone(profile)


if __name__ == "__main__":
    unittest.main()
