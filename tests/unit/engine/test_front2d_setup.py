from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest import mock

from tet4d.ui.pygame import front2d_setup


class TestFront2DSetup(unittest.TestCase):
    def test_2d_exploration_mode_uses_fixed_compact_board_profile(self) -> None:
        settings = front2d_setup.GameSettings(
            width=14,
            height=26,
            exploration_mode=1,
        )
        cfg = front2d_setup.config_from_settings(settings)
        self.assertEqual((cfg.width, cfg.height), (8, 8))

    def test_2d_build_config_uses_mode_specific_topology_profiles(self) -> None:
        normal_profile = mock.Mock(
            topology_mode="bounded", edge_rules=(("bounded", "bounded"),) * 2
        )
        explorer_profile = SimpleNamespace(dimension=2, gluings=())
        with (
            mock.patch.object(
                front2d_setup,
                "load_topology_profile",
                return_value=normal_profile,
            ) as load_profile,
            mock.patch.object(
                front2d_setup,
                "resolve_direct_explorer_launch_profile",
                return_value=("bounded", (("bounded", "bounded"),) * 2, explorer_profile),
            ) as resolve_explorer,
        ):
            normal_cfg = front2d_setup.config_from_settings(
                front2d_setup.GameSettings(topology_advanced=1, exploration_mode=0),
            )
            explorer_cfg = front2d_setup.config_from_settings(
                front2d_setup.GameSettings(topology_advanced=0, exploration_mode=1),
            )

        self.assertEqual(load_profile.call_args_list[0].args, ("normal", 2))
        self.assertEqual(resolve_explorer.call_args_list[0].kwargs["dimension"], 2)
        self.assertNotIn("topology_advanced", resolve_explorer.call_args_list[0].kwargs)
        self.assertNotIn("profile_index", resolve_explorer.call_args_list[0].kwargs)
        self.assertEqual(normal_cfg.topology_edge_rules[1], ("bounded", "bounded"))
        self.assertIs(explorer_cfg.explorer_topology_profile, explorer_profile)



    def test_2d_menu_fields_hide_topology_rows_in_explorer_mode(self) -> None:
        attrs = {
            attr_name
            for _label, attr_name, _min_val, _max_val in front2d_setup.menu_fields(
                front2d_setup.GameSettings(exploration_mode=1, topology_advanced=1)
            )
        }
        self.assertNotIn("topology_mode", attrs)
        self.assertNotIn("topology_advanced", attrs)
        self.assertNotIn("topology_profile_index", attrs)

    def test_2d_export_uses_stored_explorer_preview_in_explorer_mode(self) -> None:
        state = front2d_setup.MenuState(
            settings=front2d_setup.GameSettings(exploration_mode=1, topology_advanced=0)
        )
        with mock.patch.object(
            front2d_setup,
            "export_stored_explorer_topology_preview",
        ) as export_preview:
            front2d_setup._export_topology_profile(state)

        export_preview.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
