from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame

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
from tet4d.ui.pygame.keybindings import KEYS_3D, KEYS_4D
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

    def _invalid_explorer_profile(self, dimension: int) -> ExplorerTopologyProfile:
        if dimension == 3:
            return ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="invalid_dims",
                        source=BoundaryRef(dimension=3, axis=0, side="-"),
                        target=BoundaryRef(dimension=3, axis=2, side="+"),
                        transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
                    ),
                ),
            )
        return ExplorerTopologyProfile(
            dimension=4,
            gluings=(
                GluingDescriptor(
                    glue_id="invalid_dims",
                    source=BoundaryRef(dimension=4, axis=0, side="-"),
                    target=BoundaryRef(dimension=4, axis=2, side="+"),
                    transform=BoundaryTransform(permutation=(0, 1, 2), signs=(1, 1, 1)),
                ),
            ),
        )

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

    def test_draw_menu_does_not_crash_for_normal_2d(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((960, 720))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        profile = default_topology_profile_state(
            dimension=2,
            gravity_axis=1,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
        )
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_NORMAL,
            dimension=2,
            profile=profile,
        )
        topology_lab_menu._draw_menu(screen, fonts, state)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertEqual(row_keys.count("x_neg"), 1)
        self.assertEqual(row_keys.count("y_pos"), 1)
        self.assertNotIn("z_neg", row_keys)

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

    def test_save_profile_persists_selected_mode_dimension_for_legacy_path(
        self,
    ) -> None:
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

    def test_initial_state_can_boot_directly_into_explorer_probe_mode(self) -> None:
        profile = topology_lab_menu._explorer_presets(self._explorer_state(3))[1].profile
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=profile,
            initial_tool=topology_lab_menu.TOOL_PROBE,
        )
        self.assertEqual(state.gameplay_mode, GAMEPLAY_MODE_EXPLORER)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)
        self.assertIs(state.explorer_profile, profile)
        self.assertIsNotNone(state.probe_coord)

    def test_probe_tool_uses_bound_explorer_key_for_vertical_movement(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        with patch.object(topology_lab_menu, "_apply_probe_step") as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_step.assert_called_once_with(state, "y-")

    def test_navigate_tool_routes_bound_explorer_key_to_probe_step(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        with patch.object(topology_lab_menu, "_apply_probe_step") as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_step.assert_called_once_with(state, "y-")

    def test_sandbox_tool_keeps_explorer_key_for_piece_motion(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        with (
            patch.object(topology_lab_menu, "_apply_probe_step") as apply_probe_step,
            patch.object(topology_lab_menu, "_apply_sandbox_shortcut_step") as apply_sandbox_step,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_probe_step.assert_not_called()
        apply_sandbox_step.assert_called_once_with(state, "y-")

    def test_navigate_tool_routes_3d_depth_translation_to_probe_step(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        move_z_neg = KEYS_3D["move_z_neg"][0]
        with patch.object(topology_lab_menu, "_apply_probe_step") as apply_step:
            topology_lab_menu._dispatch_key(state, move_z_neg)
        apply_step.assert_called_once_with(state, "z-")

    def test_navigate_tool_routes_4d_w_translation_to_probe_step(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        move_w_pos = KEYS_4D["move_w_pos"][0]
        with patch.object(topology_lab_menu, "_apply_probe_step") as apply_step:
            topology_lab_menu._dispatch_key(state, move_w_pos)
        apply_step.assert_called_once_with(state, "w+")

    def test_play_tool_routes_bound_translation_to_probe_step(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        with patch.object(topology_lab_menu, "_apply_probe_step") as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
        apply_step.assert_called_once_with(state, "x+")

    def test_shift_tab_cycles_tools_backward(self) -> None:
        state = self._explorer_state(3)
        with patch.object(topology_lab_menu, "cycle_tool") as cycle_tool:
            topology_lab_menu._dispatch_key(
                state,
                pygame.K_TAB,
                pygame.KMOD_SHIFT,
            )
        cycle_tool.assert_called_once_with(state, -1)

    def test_enter_in_play_tool_requests_play_preview(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        self.assertFalse(state.play_preview_requested)
        topology_lab_menu._dispatch_key(state, pygame.K_RETURN)
        self.assertTrue(state.play_preview_requested)

    def test_backspace_removes_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 1)
        topology_lab_menu._dispatch_key(state, pygame.K_BACKSPACE)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 0)

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
            index
            for index, preset in enumerate(presets)
            if preset.preset_id == "projective_2d"
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

    def test_rows_include_play_settings_for_3d_explorer(self) -> None:
        state = self._explorer_state(3)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("board_x", row_keys)
        self.assertIn("board_y", row_keys)
        self.assertIn("board_z", row_keys)
        self.assertIn("piece_set", row_keys)
        self.assertIn("speed_level", row_keys)

    def test_rows_include_play_settings_for_4d_explorer(self) -> None:
        state = self._explorer_state(4)
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("board_x", row_keys)
        self.assertIn("board_y", row_keys)
        self.assertIn("board_z", row_keys)
        self.assertIn("board_w", row_keys)
        self.assertIn("piece_set", row_keys)
        self.assertIn("speed_level", row_keys)

    def test_helper_lines_expose_unified_shell_and_vertical_keys_for_nd(self) -> None:
        state = self._explorer_state(4)
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertIn("Explorer Playground: Explorer Mode and Topology Lab are aliases into this shell.", lines)
        self.assertTrue(any(line.startswith("Move Y:") for line in lines))
        self.assertIn("Click +/- on left rows to change board, piece set, and speed", lines)

    def test_row_step_target_adjusts_explorer_board_z(self) -> None:
        state = self._explorer_state(3)
        state.play_settings = topology_lab_menu.build_explorer_playground_settings(dimension=3)
        initial_dims = topology_lab_menu._board_dims_for_state(state)
        target = topology_lab_menu.TopologyLabHitTarget("row_step", ("board_z", 1), pygame.Rect(0, 0, 10, 10))
        handled = topology_lab_menu._dispatch_mouse_target(state, target, 1)
        self.assertTrue(handled)
        self.assertEqual(topology_lab_menu._board_dims_for_state(state), (initial_dims[0], initial_dims[1], initial_dims[2] + 1))

    def test_cycle_dimension_with_invalid_loaded_explorer_profile_does_not_crash(self) -> None:
        state = self._explorer_state(2)
        with patch.object(
            topology_lab_menu,
            "load_runtime_explorer_topology_profile",
            return_value=self._invalid_explorer_profile(3),
        ):
            topology_lab_menu._cycle_dimension(state, 1)
        self.assertEqual(state.dimension, 3)
        self.assertIsNone(state.probe_coord)
        self.assertEqual(state.probe_path, [])
        self.assertTrue(state.probe_trace)
        self.assertIn("Probe unavailable:", state.probe_trace[0])

    def test_draw_menu_does_not_crash_with_invalid_explorer_profile_for_current_dims(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        state = self._explorer_state(3)
        state.explorer_profile = self._invalid_explorer_profile(3)
        state.play_settings = topology_lab_menu.build_explorer_playground_settings(
            dimension=3
        )
        topology_lab_menu._draw_menu(screen, fonts, state)
        self.assertIsNone(state.probe_coord)
        self.assertEqual(state.probe_path, [])
        self.assertTrue(state.probe_trace)
        self.assertTrue(any("Preview invalid:" in line for line in topology_lab_menu._workspace_preview_lines(state, None, "gluing transform is not bijective for the board dimensions")))

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

    def test_preview_lines_show_engine_owned_arrow_basis(self) -> None:
        state = self._explorer_state(3)
        state.explorer_profile = ExplorerTopologyProfile(
            dimension=3,
            gluings=(
                GluingDescriptor(
                    glue_id="swap",
                    source=BoundaryRef(dimension=3, axis=0, side="-"),
                    target=BoundaryRef(dimension=3, axis=2, side="+"),
                    transform=BoundaryTransform(permutation=(1, 0), signs=(1, -1)),
                ),
            ),
        )
        lines = topology_lab_menu._explorer_sidebar_lines(state)
        self.assertIn("  Arrow basis", lines)
        self.assertTrue(any("x- -> z+" in line for line in lines))
        self.assertTrue(any("+y -> +y" in line for line in lines))
        self.assertTrue(any("+z -> -x" in line for line in lines))

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

    def test_draw_menu_populates_explorer_mouse_targets(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        state = self._explorer_state(3)
        topology_lab_menu._draw_menu(screen, fonts, state)
        targets = state.mouse_targets or []
        self.assertTrue(any(target.kind == "boundary_pick" for target in targets))
        self.assertTrue(any(target.kind == "preset_step" for target in targets))
        self.assertTrue(any(target.kind == "glue_slot" for target in targets))
        self.assertTrue(any(target.kind == "perm_select" for target in targets))
        self.assertTrue(any(target.kind == "action" for target in targets))

    def test_draw_menu_populates_glue_pick_targets_for_existing_glues(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        topology_lab_menu._draw_menu(screen, fonts, state)
        targets = state.mouse_targets or []
        self.assertTrue(any(target.kind == "glue_pick" for target in targets))

    def test_mouse_boundary_pick_updates_explorer_draft(self) -> None:
        state = self._explorer_state(3)
        source_target = topology_lab_menu.TopologyLabHitTarget(
            kind="boundary_pick",
            value=4,
            rect=pygame.Rect(0, 0, 40, 40),
        )
        state.mouse_targets = [source_target]
        state.selected = next(
            index
            for index, row_index in enumerate(
                topology_lab_menu._selectable_row_indexes(state)
            )
            if topology_lab_menu._rows_for_state(state)[row_index].key
            == "explorer_source"
        )
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        assert state.explorer_draft is not None
        self.assertEqual(state.explorer_draft.source_index, 4)

    def test_create_gluing_second_boundary_switches_to_edit_tool(self) -> None:
        state = self._explorer_state(3)
        state.active_tool = topology_lab_menu.TOOL_CREATE
        state.pending_source_index = 1
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=4,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        assert state.explorer_draft is not None
        self.assertEqual(state.explorer_draft.source_index, 1)
        self.assertEqual(state.explorer_draft.target_index, 4)
        self.assertEqual(state.active_tool, "edit_transform")
        self.assertIsNone(state.pending_source_index)
    def test_mouse_action_apply_glue_adds_gluing(self) -> None:
        state = self._explorer_state(3)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="action",
                value="apply_glue",
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (3, 3), 1)
        assert state.explorer_profile is not None
        self.assertEqual(len(state.explorer_profile.gluings), 1)

    def test_mouse_probe_step_updates_probe_trace(self) -> None:
        state = self._explorer_state(2)
        state.explorer_profile = topology_lab_menu._explorer_presets(state)[1].profile
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="probe_step",
                value="x-",
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertIsNotNone(state.probe_coord)
        self.assertIsNotNone(state.probe_trace)
        self.assertTrue(state.probe_trace)

    def test_mouse_preset_cycle_updates_explorer_profile(self) -> None:
        state = self._explorer_state(3)
        original = state.explorer_profile
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="preset_step",
                value=1,
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertNotEqual(state.explorer_profile, original)

    def test_probe_tool_mouse_preset_cycle_updates_explorer_profile(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        original = state.explorer_profile
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="preset_step",
                value=1,
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertNotEqual(state.explorer_profile, original)

    def test_probe_tool_right_click_boundary_starts_glue_creation(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=4,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 3)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_CREATE)
        self.assertEqual(state.pending_source_index, 4)
        self.assertEqual(state.selected_boundary_index, 4)

    def test_probe_tool_right_click_boundary_edits_existing_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        topology_lab_menu._apply_explorer_glue(state)
        assert state.explorer_profile is not None
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=0,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 3)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertEqual(state.selected_glue_id, state.explorer_profile.gluings[0].glue_id)

    def test_mouse_glue_slot_selects_existing_glue(self) -> None:
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=0, side="+"),
            transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
        )
        state = self._explorer_state(3)
        state.explorer_profile = ExplorerTopologyProfile(dimension=3, gluings=(glue,))
        state.explorer_draft = topology_lab_menu.ExplorerGlueDraft(
            slot_index=1,
            source_index=2,
            target_index=3,
            permutation_index=0,
            signs=(1, 1),
        )
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="glue_slot",
                value=0,
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        assert state.explorer_draft is not None
        self.assertEqual(state.explorer_draft.slot_index, 0)
        self.assertEqual(state.explorer_draft.source_index, 0)

    def test_mouse_tool_mode_select_updates_active_tool(self) -> None:
        state = self._explorer_state(3)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="tool_mode",
                value="probe",
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertEqual(state.active_tool, "probe")

    def test_mouse_glue_pick_switches_to_editing_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        assert state.explorer_profile is not None
        glue_id = state.explorer_profile.gluings[0].glue_id
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="glue_pick",
                value=glue_id,
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertEqual(state.active_tool, "edit_transform")
        self.assertEqual(state.selected_glue_id, glue_id)

    def test_mouse_motion_boundary_target_updates_hover_state(self) -> None:
        state = self._explorer_state(3)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=4,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        topology_lab_menu._handle_mouse_motion(state, (5, 5))
        self.assertEqual(state.hovered_boundary_index, 4)
        self.assertIsNone(state.hovered_glue_id)

    def test_mouse_motion_glue_target_updates_hover_state(self) -> None:
        state = self._explorer_state(3)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="glue_pick",
                value="glue_001",
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        topology_lab_menu._handle_mouse_motion(state, (5, 5))
        self.assertIsNone(state.hovered_boundary_index)
        self.assertEqual(state.hovered_glue_id, "glue_001")

    def test_play_preview_action_sets_request_flag(self) -> None:
        state = self._explorer_state(3)
        self.assertFalse(state.play_preview_requested)
        topology_lab_menu._activate_action(state, "play_preview")
        self.assertTrue(state.play_preview_requested)

    def test_launch_play_preview_2d_uses_draft_profile(self) -> None:
        state = self._explorer_state(2)
        profile = topology_lab_menu._explorer_presets(state)[1].profile
        state.explorer_profile = profile
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with (
            patch.object(topology_lab_menu, "build_explorer_playground_config") as build_cfg,
            patch("tet4d.ui.pygame.front2d_game.run_game_loop", return_value=True) as run_loop,
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.capture_windowed_display_settings", return_value=None),
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.open_display", return_value=screen),
        ):
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        self.assertEqual(build_cfg.call_args.kwargs["dimension"], state.dimension)
        self.assertIs(build_cfg.call_args.kwargs["explorer_profile"], profile)
        run_loop.assert_called_once()

    def test_probe_reset_action_restores_center_and_clears_trace(self) -> None:
        state = self._explorer_state(2)
        state.active_tool = topology_lab_menu.TOOL_PROBE
        state.probe_coord = (0, 0)
        state.probe_trace = ["x-: [0, 0] -> [5, 0]"]
        state.probe_path = [(0, 0), (5, 0)]
        topology_lab_menu._activate_action(state, "probe_reset")
        dims = topology_lab_menu._board_dims_for_state(state)
        self.assertEqual(state.probe_coord, tuple(max(0, size // 2) for size in dims))
        self.assertEqual(state.probe_trace, [])
        self.assertEqual(state.probe_path, [tuple(max(0, size // 2) for size in dims)])

    def test_launch_play_preview_3d_uses_draft_profile(self) -> None:
        state = self._explorer_state(3)
        profile = topology_lab_menu._explorer_presets(state)[0].profile
        state.explorer_profile = profile
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with (
            patch.object(topology_lab_menu, "build_explorer_playground_config") as build_cfg,
            patch("tet4d.ui.pygame.front3d_game.run_game_loop", return_value=True) as run_loop,
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.capture_windowed_display_settings", return_value=None),
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.open_display", return_value=screen),
        ):
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        self.assertEqual(build_cfg.call_args.kwargs["dimension"], state.dimension)
        self.assertIs(build_cfg.call_args.kwargs["explorer_profile"], profile)
        run_loop.assert_called_once()

    def test_launch_play_preview_4d_uses_draft_profile(self) -> None:
        state = self._explorer_state(4)
        profile = topology_lab_menu._explorer_presets(state)[0].profile
        state.explorer_profile = profile
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with (
            patch.object(topology_lab_menu, "build_explorer_playground_config") as build_cfg,
            patch("tet4d.ui.pygame.front4d_game.run_game_loop", return_value=True) as run_loop,
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.capture_windowed_display_settings", return_value=None),
            patch("tet4d.ui.pygame.runtime_ui.app_runtime.open_display", return_value=screen),
        ):
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        self.assertEqual(build_cfg.call_args.kwargs["dimension"], state.dimension)
        self.assertIs(build_cfg.call_args.kwargs["explorer_profile"], profile)
        run_loop.assert_called_once()

    def test_run_explorer_playground_uses_explicit_launch_contract(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            explorer_profile=ExplorerTopologyProfile(dimension=3, gluings=()),
            entry_source="explorer",
        )
        with patch.object(
            topology_lab_menu,
            "run_topology_lab_menu",
            return_value=(True, "ok"),
        ) as run_lab:
            topology_lab_menu.run_explorer_playground(
                object(),
                object(),
                launch=launch,
            )
        self.assertIs(run_lab.call_args.kwargs["launch"], launch)
        self.assertEqual(run_lab.call_args.kwargs["start_dimension"], 3)


    def test_workspace_preview_lines_include_hover_and_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.selected_boundary_index = 1
        state.hovered_boundary_index = 4
        state.selected_glue_id = "glue_001"
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={"movement_graph": {"cell_count": 1, "directed_edge_count": 0, "boundary_traversal_count": 0, "component_count": 1}, "warnings": (), "sample_boundary_traversals": ()},
            preview_error=None,
        )
        self.assertIn("Selected boundary: x+", lines)
        self.assertIn("Hover boundary: z-", lines)
        self.assertIn("Selected seam: glue_001", lines)
        self.assertIn("Tool: probe", lines)

    def test_workspace_preview_lines_fall_back_to_hovered_glue(self) -> None:
        state = self._explorer_state(3)
        state.hovered_glue_id = "glue_hover"
        state.selected_glue_id = None
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={"movement_graph": {"cell_count": 1, "directed_edge_count": 0, "boundary_traversal_count": 0, "component_count": 1}, "warnings": (), "sample_boundary_traversals": ()},
            preview_error=None,
        )
        self.assertIn("Hover seam: glue_hover", lines)

    def test_hint_lines_expose_unified_explorer_playground_shortcuts(self) -> None:
        state = self._explorer_state(4)
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertIn(
            "Explorer Playground: Explorer Mode and Topology Lab are aliases into this shell.",
            lines,
        )
        self.assertIn(
            "Tab/Shift+Tab cycle tools   Enter plays from Play tool   Delete removes selected seam",
            lines,
        )
        self.assertIn(
            "3D/4D use clickable projected faces or shell cards; side panels refine the selected seam.",
            lines,
        )



if __name__ == "__main__":
    unittest.main()


