from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.engine.gameplay.topology import EDGE_BOUNDED, EDGE_WRAP
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    default_topology_profile_state,
)
from tet4d.ui.pygame.launch import topology_lab_menu


class TestTopologyLabMenu(unittest.TestCase):
    def test_rows_lock_y_boundaries_in_normal_mode(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            dimension=3,
            profile=profile,
        )
        rows = topology_lab_menu._rows_for_state(state)
        y_rows = [row for row in rows if row.key in {"y_neg", "y_pos"}]
        self.assertEqual(len(y_rows), 2)
        self.assertTrue(all(row.disabled for row in y_rows))

    def test_rows_enable_y_boundaries_in_explorer_mode(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            profile=profile,
        )
        rows = topology_lab_menu._rows_for_state(state)
        y_rows = [row for row in rows if row.key in {"y_neg", "y_pos"}]
        self.assertEqual(len(y_rows), 2)
        self.assertTrue(all(not row.disabled for row in y_rows))

    def test_cycle_edge_rule_blocks_normal_y_wrap(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            dimension=3,
            profile=profile,
        )
        row = next(row for row in topology_lab_menu._rows_for_state(state) if row.key == "y_neg")
        topology_lab_menu._cycle_edge_rule(state, row, 1)
        self.assertEqual(state.profile.edge_rules[1], (EDGE_BOUNDED, EDGE_BOUNDED))
        self.assertTrue(state.status_error)

    def test_cycle_edge_rule_allows_explorer_y_wrap(self) -> None:
        profile = default_topology_profile_state(
            dimension=3,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=profile,
        )
        row = next(row for row in topology_lab_menu._rows_for_state(state) if row.key == "y_neg")
        topology_lab_menu._cycle_edge_rule(state, row, 1)
        self.assertEqual(state.profile.edge_rules[1][0], EDGE_WRAP)
        self.assertTrue(state.dirty)

    def test_save_profile_persists_selected_mode_dimension(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=4,
            profile=profile,
            dirty=True,
        )
        with patch.object(topology_lab_menu, 'save_topology_profile', return_value=(True, 'saved')) as save_profile:
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_profile.assert_called_once_with(state.profile)


if __name__ == "__main__":
    unittest.main()
