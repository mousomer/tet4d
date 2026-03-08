from __future__ import annotations

import unittest

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_INVERT, EDGE_WRAP, TopologyPolicy
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    default_topology_profile_state,
    designer_profiles_for_dimension,
    profile_state_from_preset,
    validate_topology_profile_state,
)


class TestTopologyDesigner(unittest.TestCase):
    def test_custom_per_edge_rules_apply_inversion_only_for_configured_edge(self) -> None:
        policy = TopologyPolicy(
            dims=(4, 8, 4),
            gravity_axis=1,
            mode="bounded",
            edge_rules=(
                (EDGE_INVERT, EDGE_WRAP),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_WRAP, EDGE_WRAP),
            ),
        )
        self.assertEqual(policy.map_coord((-1, 3, 1), allow_above_gravity=True), (3, 3, 2))
        self.assertEqual(policy.map_coord((4, 3, 1), allow_above_gravity=True), (0, 3, 1))

    def test_designer_profiles_are_split_by_gameplay_mode(self) -> None:
        normal_4d = designer_profiles_for_dimension(4, GAMEPLAY_MODE_NORMAL)
        explorer_4d = designer_profiles_for_dimension(4, GAMEPLAY_MODE_EXPLORER)
        self.assertTrue(normal_4d)
        self.assertTrue(explorer_4d)
        self.assertNotEqual(
            {profile.profile_id for profile in normal_4d},
            {profile.profile_id for profile in explorer_4d},
        )

    def test_normal_mode_rejects_non_bounded_y_edges(self) -> None:
        default_state = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        rules = list(default_state.edge_rules)
        rules[1] = (EDGE_WRAP, EDGE_WRAP)
        with self.assertRaises(ValueError):
            validate_topology_profile_state(
                gameplay_mode=GAMEPLAY_MODE_NORMAL,
                dimension=4,
                gravity_axis=1,
                topology_mode=default_state.topology_mode,
                edge_rules=tuple(rules),
            )

    def test_explorer_mode_allows_wrapped_y_edges(self) -> None:
        state = validate_topology_profile_state(
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            gravity_axis=1,
            topology_mode="bounded",
            edge_rules=(
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_WRAP, EDGE_WRAP),
                (EDGE_BOUNDED, EDGE_BOUNDED),
                (EDGE_BOUNDED, EDGE_BOUNDED),
            ),
        )
        self.assertEqual(state.edge_rules[1], (EDGE_WRAP, EDGE_WRAP))

    def test_all_normal_presets_keep_y_bounded(self) -> None:
        for dimension in (3, 4):
            for preset_index, _profile in enumerate(
                designer_profiles_for_dimension(dimension, GAMEPLAY_MODE_NORMAL)
            ):
                state = profile_state_from_preset(
                    dimension=dimension,
                    gravity_axis=1,
                    gameplay_mode=GAMEPLAY_MODE_NORMAL,
                    preset_index=preset_index,
                    topology_mode="bounded",
                )
                self.assertEqual(state.edge_rules[1], (EDGE_BOUNDED, EDGE_BOUNDED))

    def test_profile_state_from_explorer_preset_keeps_y_wrap(self) -> None:
        profiles = designer_profiles_for_dimension(4, GAMEPLAY_MODE_EXPLORER)
        target_index = next(
            idx for idx, profile in enumerate(profiles) if profile.profile_id == "explorer_wrap_y"
        )
        state = profile_state_from_preset(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            preset_index=target_index,
            topology_mode="bounded",
        )
        self.assertEqual(state.edge_rules[1], (EDGE_WRAP, EDGE_WRAP))


if __name__ == "__main__":
    unittest.main()
