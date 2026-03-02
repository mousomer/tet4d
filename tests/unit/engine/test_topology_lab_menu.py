from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.ui.pygame.launch import topology_lab_menu


class TestTopologyLabMenu(unittest.TestCase):
    def test_load_dimension_settings_reads_mode_payload(self) -> None:
        state = topology_lab_menu._TopologyLabState(
            payload={
                "settings": {
                    "3d": {
                        "topology_mode": 2,
                        "topology_advanced": 1,
                        "topology_profile_index": 1,
                    }
                }
            },
            selected=0,
            dimension=3,
            topology_mode_index=0,
            topology_advanced=0,
            topology_profile_index=0,
        )

        topology_lab_menu._load_dimension_settings(state)

        self.assertEqual(state.topology_mode_index, 2)
        self.assertEqual(state.topology_advanced, 1)
        self.assertGreaterEqual(state.topology_profile_index, 0)

    def test_save_dimension_settings_updates_selected_mode(self) -> None:
        state = topology_lab_menu._TopologyLabState(
            payload={"settings": {"2d": {}}},
            selected=0,
            dimension=2,
            topology_mode_index=1,
            topology_advanced=1,
            topology_profile_index=2,
        )

        with patch.object(
            topology_lab_menu.engine_api,
            "save_menu_payload_runtime",
            return_value=(True, "saved"),
        ) as save_payload:
            ok, _msg = topology_lab_menu._save_dimension_settings(state)

        self.assertTrue(ok)
        mode_settings = state.payload["settings"]["2d"]
        self.assertEqual(mode_settings["topology_mode"], 1)
        self.assertEqual(mode_settings["topology_advanced"], 1)
        self.assertEqual(mode_settings["topology_profile_index"], 2)
        save_payload.assert_called_once_with(state.payload)

    def test_profile_text_input_clamps_index(self) -> None:
        state = topology_lab_menu._TopologyLabState(
            payload={"settings": {"4d": {}}},
            selected=0,
            dimension=4,
            topology_mode_index=0,
            topology_advanced=0,
            topology_profile_index=0,
            text_mode_row_key="topology_profile_index",
            text_mode_buffer="9999",
        )

        updated = topology_lab_menu._apply_profile_index_from_text(state)

        self.assertTrue(updated)
        self.assertEqual(
            state.topology_profile_index,
            topology_lab_menu._profile_count_for_dimension(4) - 1,
        )


if __name__ == "__main__":
    unittest.main()
