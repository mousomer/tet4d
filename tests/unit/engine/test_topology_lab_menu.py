from __future__ import annotations

import unittest
from unittest.mock import patch

from tet4d.engine.topology_explorer import (
    BoundaryRef,
    BoundaryTransform,
    ExplorerTopologyProfile,
    GluingDescriptor,
)

from tet4d.engine.gameplay.topology import EDGE_BOUNDED
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    default_topology_profile_state,
)
from tet4d.ui.pygame.launch import topology_lab_menu


class TestTopologyLabMenu(unittest.TestCase):
    def _explorer_state(self, dimension: int) -> topology_lab_menu._TopologyLabState:
        profile = default_topology_profile_state(
            dimension=dimension,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        tangent_dimension = dimension - 1
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=dimension,
            profile=profile,
            explorer_profile=ExplorerTopologyProfile(dimension=dimension, gluings=()),
            explorer_draft=topology_lab_menu.ExplorerGlueDraft(
                slot_index=0,
                source_index=0,
                target_index=1,
                permutation_index=0,
                signs=tuple(1 for _ in range(tangent_dimension)),
            ),
        )
        topology_lab_menu._normalize_explorer_draft(state)
        return state

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
        row = next(
            row
            for row in topology_lab_menu._rows_for_state(state)
            if row.key == "y_neg"
        )
        topology_lab_menu._cycle_edge_rule(state, row, 1)
        self.assertEqual(state.profile.edge_rules[1], (EDGE_BOUNDED, EDGE_BOUNDED))
        self.assertTrue(state.status_error)

    def test_save_profile_persists_selected_mode_dimension_for_legacy_path(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            dimension=4,
            profile=profile,
            dirty=True,
        )
        with patch.object(
            topology_lab_menu, "save_topology_profile", return_value=(True, "saved")
        ) as save_profile:
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_profile.assert_called_once_with(state.profile)

    def test_export_runs_legacy_path_for_normal_mode(self) -> None:
        profile = default_topology_profile_state(
            dimension=4,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            dimension=4,
            profile=profile,
        )
        with (
            patch.object(
                topology_lab_menu,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
            patch.object(
                topology_lab_menu,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
        ):
            topology_lab_menu._run_export(state)
        export_legacy.assert_called_once()
        export_preview.assert_not_called()
        self.assertIn("legacy exported", state.status)

    def test_rows_switch_to_direct_explorer_editor_for_2d(self) -> None:
        state = self._explorer_state(2)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("explorer_source", row_keys)
        self.assertIn("explorer_sign_0", row_keys)
        self.assertIn("apply_glue", row_keys)
        self.assertNotIn("topology_mode", row_keys)
        self.assertNotIn("y_neg", row_keys)

    def test_apply_explorer_glue_adds_2d_gluing_to_profile(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu._apply_explorer_glue(state)
        self.assertIsNotNone(state.explorer_profile)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 1)
        self.assertEqual(state.explorer_profile.dimension, 2)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_2d(self) -> None:
        state = self._explorer_state(2)
        with (
            patch.object(
                topology_lab_menu,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_menu,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(state.explorer_profile)
        save_legacy.assert_not_called()

    def test_unsafe_explorer_preset_label_is_marked(self) -> None:
        state = self._explorer_state(2)
        presets = topology_lab_menu._explorer_presets(state)
        unsafe_index = next(
            index for index, preset in enumerate(presets) if preset.preset_id == "projective_2d"
        )
        state.explorer_profile = presets[unsafe_index].profile
        label = topology_lab_menu._explorer_preset_value_text(state)
        self.assertIn("[unsafe]", label)

    def test_export_uses_direct_explorer_preview_for_2d_editor(self) -> None:
        state = self._explorer_state(2)
        with (
            patch.object(
                topology_lab_menu,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_menu,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
        ):
            topology_lab_menu._run_export(state)
        export_preview.assert_called_once()
        export_legacy.assert_not_called()
        self.assertIn("preview exported", state.status)

    def test_rows_switch_to_direct_explorer_editor_for_3d(self) -> None:
        state = self._explorer_state(3)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("explorer_source", row_keys)
        self.assertIn("apply_glue", row_keys)
        self.assertNotIn("topology_mode", row_keys)
        self.assertNotIn("y_neg", row_keys)

    def test_apply_explorer_glue_adds_gluing_to_profile_3d(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        self.assertIsNotNone(state.explorer_profile)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 1)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_3d(self) -> None:
        state = self._explorer_state(3)
        with (
            patch.object(
                topology_lab_menu,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_menu,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(state.explorer_profile)
        save_legacy.assert_not_called()

    def test_export_uses_direct_explorer_preview_for_3d_editor(self) -> None:
        state = self._explorer_state(3)
        with (
            patch.object(
                topology_lab_menu,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_menu,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
        ):
            topology_lab_menu._run_export(state)
        export_preview.assert_called_once()
        export_legacy.assert_not_called()
        self.assertIn("preview exported", state.status)

    def test_rows_switch_to_direct_explorer_editor_for_4d(self) -> None:
        state = self._explorer_state(4)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("explorer_source", row_keys)
        self.assertIn("explorer_sign_2", row_keys)
        self.assertIn("apply_glue", row_keys)
        self.assertNotIn("topology_mode", row_keys)
        self.assertNotIn("y_neg", row_keys)

    def test_apply_explorer_glue_adds_4d_gluing_to_profile(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu._apply_explorer_glue(state)
        self.assertIsNotNone(state.explorer_profile)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 1)
        self.assertEqual(state.explorer_profile.dimension, 4)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_4d(self) -> None:
        state = self._explorer_state(4)
        with (
            patch.object(
                topology_lab_menu,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_menu,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(state.explorer_profile)
        save_legacy.assert_not_called()

    def test_export_uses_direct_explorer_preview_for_4d_editor(self) -> None:
        state = self._explorer_state(4)
        with (
            patch.object(
                topology_lab_menu,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_menu,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
        ):
            topology_lab_menu._run_export(state)
        export_preview.assert_called_once()
        export_legacy.assert_not_called()
        self.assertIn("preview exported", state.status)

    def test_preview_lines_show_engine_owned_warnings(self) -> None:
        state = self._explorer_state(3)
        state.explorer_profile = ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="twist",
                    source=BoundaryRef(dimension=3, axis=0, side="-"),
                    target=BoundaryRef(dimension=3, axis=0, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1), signs=(-1, 1)),
                ),
            ),
        )
        lines = topology_lab_menu._explorer_sidebar_lines(state)
        self.assertIn("  Warnings", lines)
        self.assertTrue(
            any("orientation-reversing seam transforms" in line for line in lines)
        )

    def test_remove_explorer_glue_drops_selected_gluing(self) -> None:
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=0, side="+"),
            transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
        )
        state = self._explorer_state(3)
        state.explorer_profile = ExplorerTopologyProfile(dimension=3, gluings=(glue,))
        state.explorer_draft = topology_lab_menu.ExplorerGlueDraft(
            slot_index=0,
            source_index=0,
            target_index=1,
            permutation_index=0,
            signs=(1, 1),
        )
        topology_lab_menu._normalize_explorer_draft(state)
        topology_lab_menu._remove_explorer_glue(state)
        assert state.explorer_profile is not None
        self.assertEqual(state.explorer_profile.gluings, ())


if __name__ == "__main__":
    unittest.main()
