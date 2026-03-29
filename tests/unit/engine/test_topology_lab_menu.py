from __future__ import annotations

from dataclasses import replace
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
from tet4d.engine.topology_explorer.presets import (
    projective_plane_profile_2d,
    sphere_profile_2d,
    sphere_profile_3d,
)

from tet4d.engine.gameplay.topology import EDGE_BOUNDED
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
    default_topology_profile_state,
)
from tet4d.engine.runtime.topology_playground_state import (
    PLAYABILITY_STATUS_ANALYZING,
    PLAYABILITY_STATUS_PLAYABLE,
    TopologyPlaygroundSandboxPieceState,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.ui.pygame import frontend_nd_setup
from tet4d.ui.pygame.keybindings import KEYS_3D, KEYS_4D
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import controls_panel as topology_lab_controls_panel
from tet4d.ui.pygame.topology_lab import controls_panel_values as topology_lab_control_values
from tet4d.ui.pygame.topology_lab import scene_preview_state as topology_lab_scene_preview_state
from tet4d.ui.pygame.topology_lab import scene_state as topology_lab_scene_state
from tet4d.ui.pygame.topology_lab import shell_layout as topology_lab_shell_layout
from tet4d.ui.pygame.topology_lab import workspace_shell as topology_lab_workspace_shell
from tet4d.ui.pygame.ui_utils import text_fits

class TestTopologyLabMenu(unittest.TestCase):
    def _current_explorer_profile(
        self, state: topology_lab_menu._TopologyLabState
    ) -> ExplorerTopologyProfile:
        profile = topology_lab_scene_state.current_explorer_profile(state)
        assert profile is not None
        return profile

    def _current_explorer_draft(
        self, state: topology_lab_menu._TopologyLabState
    ) -> topology_lab_menu.ExplorerGlueDraft:
        draft = topology_lab_scene_state.current_explorer_draft(state)
        assert draft is not None
        return draft

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
        state.active_pane = topology_lab_menu.PANE_SCENE
        return state

    def _invalid_explorer_profile(self, dimension: int) -> ExplorerTopologyProfile:
        if dimension == 3:
            return ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="invalid_dims",
                        source=BoundaryRef(dimension=3, axis=0, side="-"),
                        target=BoundaryRef(dimension=3, axis=1, side="+"),
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

    def _fonts(self) -> SimpleNamespace:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        return SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
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

    def test_explorer_startup_defers_rigid_playability_analysis(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=2,
            entry_source="explorer",
        )
        calls: list[bool] = []

        def _fake_update(runtime_state, **kwargs):
            include_rigid_scan = bool(kwargs["include_rigid_scan"])
            calls.append(include_rigid_scan)
            analysis = TopologyPlaygroundPlayabilityAnalysis(
                status=(
                    PLAYABILITY_STATUS_PLAYABLE
                    if include_rigid_scan
                    else PLAYABILITY_STATUS_ANALYZING
                ),
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability=(
                    "rigid_playable" if include_rigid_scan else "unknown"
                ),
                summary=(
                    "Valid. Cellwise explorable. Rigid-playable."
                    if include_rigid_scan
                    else "Valid. Cellwise explorable. Rigid play analysis pending."
                ),
                rigid_reason=(
                    "Rigid transport is ready."
                    if include_rigid_scan
                    else "Rigid transport is still being analyzed."
                ),
            )
            runtime_state.playability_analysis = analysis
            return analysis

        with patch.object(
            topology_lab_scene_preview_state,
            "update_topology_playability_analysis",
            side_effect=_fake_update,
        ), patch.object(
            topology_lab_scene_preview_state,
            "read_cached_playability_analysis",
            return_value=None,
        ):
            state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
            runtime_state = topology_lab_scene_state.canonical_playground_state(state)
            assert runtime_state is not None

            self.assertEqual(calls, [False])
            self.assertEqual(
                runtime_state.playability_analysis.status,
                PLAYABILITY_STATUS_ANALYZING,
            )

            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            self.assertEqual(calls, [False])

            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            self.assertEqual(calls, [False, True])
            self.assertEqual(
                runtime_state.playability_analysis.status,
                PLAYABILITY_STATUS_PLAYABLE,
            )
            self.assertIsNone(state.scene_pending_playability_signature)

    def test_same_signature_refresh_reuses_cached_playability_analysis(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=2,
            entry_source="explorer",
        )
        calls: list[bool] = []

        def _fake_update(runtime_state, **kwargs):
            include_rigid_scan = bool(kwargs["include_rigid_scan"])
            calls.append(include_rigid_scan)
            analysis = TopologyPlaygroundPlayabilityAnalysis(
                status=(
                    PLAYABILITY_STATUS_PLAYABLE
                    if include_rigid_scan
                    else PLAYABILITY_STATUS_ANALYZING
                ),
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability=(
                    "rigid_playable" if include_rigid_scan else "unknown"
                ),
                summary="cached playability test",
            )
            runtime_state.playability_analysis = analysis
            return analysis

        with patch.object(
            topology_lab_scene_preview_state,
            "update_topology_playability_analysis",
            side_effect=_fake_update,
        ), patch.object(
            topology_lab_scene_preview_state,
            "read_cached_playability_analysis",
            return_value=None,
        ):
            state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            self.assertEqual(calls, [False, True])

            topology_lab_menu._refresh_explorer_scene_state(state)

            self.assertEqual(calls, [False, True])
            self.assertIsNotNone(state.scene_playability_cache)
            runtime_state = topology_lab_scene_state.canonical_playground_state(state)
            assert runtime_state is not None
            self.assertEqual(
                runtime_state.playability_analysis.status,
                PLAYABILITY_STATUS_PLAYABLE,
            )

    def test_pending_playability_analysis_uses_persistent_cache_when_available(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=2,
            entry_source="explorer",
        )
        analysis = TopologyPlaygroundPlayabilityAnalysis(
            status=PLAYABILITY_STATUS_PLAYABLE,
            validity="valid",
            explorer_usability="cellwise_explorable",
            rigid_playability="rigid_playable",
            summary="persistent cached playability",
        )

        def _pending_only(runtime_state, **kwargs):
            include_rigid_scan = bool(kwargs["include_rigid_scan"])
            if include_rigid_scan:
                raise AssertionError("persistent cache should avoid recompute")
            analysis_pending = TopologyPlaygroundPlayabilityAnalysis(
                status=PLAYABILITY_STATUS_ANALYZING,
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability="unknown",
                summary="pending analysis",
            )
            runtime_state.playability_analysis = analysis_pending
            return analysis_pending

        with (
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                return_value=analysis,
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=_pending_only,
            ),
        ):
            state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
            runtime_state = topology_lab_scene_state.canonical_playground_state(state)
            assert runtime_state is not None
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            self.assertEqual(
                runtime_state.playability_analysis.status,
                PLAYABILITY_STATUS_PLAYABLE,
            )
            self.assertEqual(runtime_state.playability_analysis.summary, analysis.summary)

    def test_play_launch_forces_pending_playability_analysis(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=2,
            entry_source="explorer",
        )
        calls: list[bool] = []

        def _fake_update(runtime_state, **kwargs):
            include_rigid_scan = bool(kwargs["include_rigid_scan"])
            calls.append(include_rigid_scan)
            analysis = TopologyPlaygroundPlayabilityAnalysis(
                status=(
                    PLAYABILITY_STATUS_PLAYABLE
                    if include_rigid_scan
                    else PLAYABILITY_STATUS_ANALYZING
                ),
                validity="valid",
                explorer_usability="cellwise_explorable",
                rigid_playability=(
                    "rigid_playable" if include_rigid_scan else "unknown"
                ),
                summary="launch cache test",
            )
            runtime_state.playability_analysis = analysis
            return analysis

        screen = pygame.Surface((32, 32))
        with (
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=_fake_update,
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                return_value=None,
            ),
            patch.object(
                topology_lab_controls_panel,
                "launch_playground_state_gameplay",
                return_value=(screen, None),
            ) as launch_gameplay,
        ):
            state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
            returned_screen, _display_settings = topology_lab_controls_panel._launch_play_preview(
                state,
                screen,
                SimpleNamespace(),
            )

        self.assertIs(returned_screen, screen)
        self.assertEqual(calls, [False, True])
        launch_gameplay.assert_called_once()

    def test_explorer_rows_do_not_expose_legacy_topology_menu_labels(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_CONTROLS

        rows = topology_lab_menu._rows_for_state(state)
        labels = [row.label for row in rows]
        keys = [row.key for row in rows]

        self.assertNotIn("Path", labels)
        self.assertNotIn("Workspace Path", labels)
        self.assertNotIn("Legacy Topology", labels)
        self.assertNotIn("gameplay_mode", keys)
        self.assertNotIn("preset", keys)
        self.assertNotIn("topology_mode", keys)

    def test_explorer_helper_lines_do_not_advertise_legacy_menu_surface(self) -> None:
        state = self._explorer_state(3)
        lines = topology_lab_menu._hint_lines_for_state(state)
        joined = " ".join(lines)
        self.assertNotIn("Legacy compatibility", joined)
        self.assertNotIn("legacy-normal-mode", joined)

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
            topology_lab_controls_panel,
            "save_topology_profile",
            return_value=(True, "saved"),
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
                topology_lab_controls_panel,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
        ):
            topology_lab_menu._run_export(state)
        export_legacy.assert_called_once()
        export_preview.assert_not_called()
        self.assertIn("legacy exported", state.status)

    def test_editor_rows_follow_shell_contract_for_2d(self) -> None:
        state = self._explorer_state(2)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        rows = topology_lab_menu._rows_for_state(state)
        row_keys = [row.key for row in rows]
        self.assertEqual(
            row_keys,
            [
                "dimension",
                "editor_trace",
                "editor_probe_neighbors",
                "editor_tool",
                "board_x",
                "board_y",
                "explorer_preset",
            ],
        )

    def test_analysis_status_rows_are_display_only(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        rows = topology_lab_menu._rows_for_state(state)
        selectable_keys = [
            rows[index].key
            for index in topology_lab_menu._selectable_row_indexes(state)
        ]
        self.assertNotIn("analysis_boundary", selectable_keys)
        self.assertNotIn("analysis_glue", selectable_keys)
        self.assertNotIn("analysis_transform", selectable_keys)

    def test_normal_mode_is_labeled_legacy_compatibility(self) -> None:
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
        self.assertEqual(rows[0].label, "Workspace Path")
        self.assertEqual(
            topology_lab_menu._row_value_text(state, rows[0]),
            "Normal Game (legacy compat)",
        )
        self.assertTrue(any(row.label == "Legacy Preset" for row in rows))
        self.assertTrue(
            any(
                line.startswith("Legacy compatibility:")
                for line in topology_lab_menu._hint_lines_for_state(state)
            )
        )

    def test_dimension_roundtrip_preserves_custom_explorer_play_settings(
        self,
    ) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            4,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=ExplorerTopologyProfile(dimension=4, gluings=()),
            play_settings=topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=(11, 17, 7, 5),
                piece_set_index=2,
                speed_level=4,
                random_mode_index=1,
                game_seed=1234,
            ),
        )

        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state), (11, 17, 7, 5)
        )
        topology_lab_controls_panel._cycle_dimension(state, -1)
        topology_lab_controls_panel._cycle_dimension(state, 1)

        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state), (11, 17, 7, 5)
        )

    def test_f8_resets_current_dimension_play_settings_to_configured_defaults(
        self,
    ) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            4,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=ExplorerTopologyProfile(dimension=4, gluings=()),
            play_settings=topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=(11, 17, 7, 5),
                piece_set_index=2,
                speed_level=4,
                random_mode_index=1,
                game_seed=1234,
            ),
        )
        state.active_pane = topology_lab_menu.PANE_SCENE

        topology_lab_menu._dispatch_key(state, pygame.K_F8)

        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state), (8, 8, 8, 8)
        )
        self.assertIn("reset to defaults", state.status)
        topology_lab_controls_panel._cycle_dimension(state, -1)
        topology_lab_controls_panel._cycle_dimension(state, 1)
        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state), (8, 8, 8, 8)
        )

    def test_initial_state_can_boot_directly_into_explorer_probe_mode(self) -> None:
        profile = topology_lab_menu._explorer_presets(self._explorer_state(3))[
            1
        ].profile
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=profile,
            initial_tool=topology_lab_menu.TOOL_PROBE,
        )
        self.assertEqual(state.gameplay_mode, GAMEPLAY_MODE_EXPLORER)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertIs(self._current_explorer_profile(state), profile)
        self.assertIsNotNone(topology_lab_scene_state.current_probe_coord(state))

    def test_initial_explorer_state_uses_configured_board_defaults(self) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=sphere_profile_3d(),
        )

        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state),
            (8, 8, 8),
        )
        assert state.play_settings is not None
        self.assertEqual(state.play_settings.board_dims, (8, 8, 8))
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.axis_sizes, (8, 8, 8))
        self.assertEqual(state.canonical_state.launch_settings.game_seed, 1337)

    def test_default_explorer_probe_uses_canonical_transport_after_crossing_boundary(
        self,
    ) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=sphere_profile_3d(),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_SCENE

        selected = topology_lab_menu._select_projection_coord(state, (0, 0, 0))

        self.assertEqual(selected, (0, 0, 0))
        for _ in range(6):
            topology_lab_menu._apply_probe_step(state, "x+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (6, 0, 0))
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.probe_state.coord, (6, 0, 0))

        topology_lab_menu._apply_probe_step(state, "x+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (7, 0, 0))

        topology_lab_menu._apply_probe_step(state, "x+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (7, 7, 7))
        self.assertEqual(state.canonical_state.probe_state.coord, (7, 7, 7))
        self.assertEqual(state.canonical_state.probe_state.frame_permutation, (0, 1, 2))
        self.assertEqual(state.canonical_state.probe_state.frame_signs, (1, 1, 1))
        self.assertFalse(state.status_error)
        self.assertIn("x+ -> y+", state.status)

        expected_target, _expected_result = topology_lab_controls_panel.advance_explorer_probe(
            sphere_profile_3d(),
            dims=(8, 8, 8),
            coord=(7, 7, 7),
            step_label="x+",
        )
        topology_lab_menu._apply_probe_step(state, "x+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), expected_target)
        self.assertEqual(state.canonical_state.probe_state.coord, expected_target)
        self.assertEqual(state.canonical_state.probe_state.frame_permutation, (0, 1, 2))
        self.assertEqual(state.canonical_state.probe_state.frame_signs, (1, 1, 1))

    def test_3d_launch_from_generic_nd_defaults_keeps_canonical_transport_live(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="explorer",
            explorer_profile=sphere_profile_3d(),
            source_settings=frontend_nd_setup.GameSettingsND(),
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_SCENE

        selected = topology_lab_menu._select_projection_coord(state, (0, 0, 0))

        self.assertEqual(selected, (0, 0, 0))
        self.assertEqual(
            topology_lab_controls_panel._board_dims_for_state(state),
            (8, 8, 8),
        )
        for _ in range(6):
            topology_lab_menu._apply_probe_step(state, "z+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (0, 0, 6))

        topology_lab_menu._apply_probe_step(state, "z+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (0, 0, 7))

        topology_lab_menu._apply_probe_step(state, "z+")
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), (7, 7, 0))
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.probe_state.coord, (7, 7, 0))
        self.assertEqual(state.canonical_state.probe_state.frame_permutation, (0, 1, 2))
        self.assertEqual(state.canonical_state.probe_state.frame_signs, (1, 1, 1))
        self.assertFalse(state.status_error)
        self.assertIn("z+ -> z-", state.status)

    def test_invalid_board_dims_keep_probe_unavailable_without_shell_snapshot_reset(
        self,
    ) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            initial_explorer_profile=sphere_profile_3d(),
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        settings = state.play_settings
        assert settings is not None

        self.assertEqual(topology_lab_menu._select_projection_coord(state, (0, 0, 0)), (0, 0, 0))

        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=(5, 8, 8),
                piece_set_index=settings.piece_set_index,
                speed_level=settings.speed_level,
                random_mode_index=settings.random_mode_index,
                game_seed=settings.game_seed,
                rigid_play_mode=settings.rigid_play_mode,
            ),
        )
        topology_lab_controls_panel._refresh_explorer_scene_state(state)

        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.axis_sizes, (5, 8, 8))
        self.assertEqual(topology_lab_controls_panel._board_dims_for_state(state), (5, 8, 8))
        self.assertEqual(state.scene_preview_dims, (5, 8, 8))
        self.assertIsNotNone(state.scene_preview_error)

        topology_lab_scene_state.replace_probe_state(
            state,
            coord=(4, 4, 4),
            trace=[],
            path=[(4, 4, 4)],
            highlighted_glue_id=None,
        )

        topology_lab_menu._apply_probe_step(state, "x+")
        self.assertIsNone(topology_lab_scene_state.current_probe_coord(state))
        self.assertEqual(tuple(topology_lab_scene_state.current_probe_path(state)), ())
        self.assertIsNone(state.canonical_state.probe_state.coord)
        self.assertEqual(state.canonical_state.probe_state.path, ())
        self.assertTrue(state.status_error)
        self.assertIn("Editor probe is unavailable", state.status)

    def test_initial_state_skips_stored_profile_refresh_for_explicit_explorer_launch(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="explorer",
            explorer_profile=ExplorerTopologyProfile(dimension=3, gluings=()),
        )
        preview = {
            "movement_graph": {
                "cell_count": 1,
                "directed_edge_count": 0,
                "boundary_traversal_count": 0,
                "component_count": 1,
            },
            "warnings": (),
            "sample_boundary_traversals": (),
            "basis_arrows": (),
        }
        with (
            patch.object(
                topology_lab_controls_panel,
                "load_runtime_explorer_topology_profile",
            ) as load_runtime_profile,
            patch.object(
                topology_lab_controls_panel,
                "compile_explorer_topology_preview",
                return_value=preview,
            ) as compile_preview,
        ):
            state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
        load_runtime_profile.assert_not_called()
        compile_preview.assert_called_once()
        self.assertEqual(state.scene_preview, preview)

    def test_refresh_explorer_scene_state_uses_canonical_profile(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._sync_explorer_state(state)
        assert state.canonical_state is not None
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=2, side="+"),
            transform=BoundaryTransform(permutation=(1, 0), signs=(1, 1)),
        )
        state.canonical_state = replace(
            state.canonical_state,
            topology_config=replace(
                state.canonical_state.topology_config,
                explorer_profile=ExplorerTopologyProfile(
                    dimension=3,
                    gluings=(glue,),
                ),
            ),
            transport_policy=None,
        )
        state.explorer_profile = ExplorerTopologyProfile(dimension=3, gluings=())

        topology_lab_menu._refresh_explorer_scene_state(state)

        self.assertEqual(state.scene_active_glue_ids.get("x-"), "glue_001")
        self.assertEqual(state.scene_active_glue_ids.get("z+"), "glue_001")

    def test_perm_select_uses_canonical_draft_when_shell_mirror_is_stale(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._sync_canonical_playground_state(state)
        state.explorer_draft = topology_lab_menu.ExplorerGlueDraft(
            slot_index=0,
            source_index=4,
            target_index=5,
            permutation_index=0,
            signs=(-1, 1),
        )
        target = topology_lab_menu.TopologyLabHitTarget(
            kind="perm_select",
            value=1,
            rect=pygame.Rect(0, 0, 10, 10),
        )

        handled = topology_lab_menu._handle_mouse_editor_target(state, target)

        self.assertTrue(handled)
        assert state.canonical_state is not None
        self.assertEqual(state.explorer_draft.source_index, 4)
        self.assertEqual(state.explorer_draft.target_index, 5)
        current_draft = self._current_explorer_draft(state)
        self.assertEqual(current_draft.source_index, 0)
        self.assertEqual(current_draft.target_index, 1)
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.source_boundary,
            BoundaryRef(dimension=3, axis=0, side="-"),
        )
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.target_boundary,
            BoundaryRef(dimension=3, axis=0, side="+"),
        )
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.permutation,
            (1, 0),
        )

    def test_mouse_boundary_pick_syncs_canonical_selection(self) -> None:
        state = topology_lab_menu._initial_topology_lab_state(
            3,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        target = topology_lab_menu.TopologyLabHitTarget(
            kind="boundary_pick",
            value=4,
            rect=pygame.Rect(0, 0, 10, 10),
        )

        handled = topology_lab_menu._handle_mouse_boundary_target(state, target, 1)

        self.assertTrue(handled)
        assert state.canonical_state is not None
        self.assertEqual(
            state.canonical_state.selected_boundary,
            BoundaryRef(dimension=3, axis=2, side="-"),
        )

    def test_probe_tool_uses_bound_explorer_key_for_vertical_movement(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_step.assert_called_once_with(state, "y-")

    def test_navigate_tool_routes_bound_explorer_key_to_probe_step(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_step.assert_called_once_with(state, "y-")

    def test_sandbox_tool_keeps_explorer_key_for_piece_motion(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with (
            patch.object(
                topology_lab_controls_panel, "_apply_probe_step"
            ) as apply_probe_step,
            patch.object(
                topology_lab_controls_panel, "_apply_sandbox_shortcut_step"
            ) as apply_sandbox_step,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_UP)
        apply_probe_step.assert_not_called()
        apply_sandbox_step.assert_called_once_with(state, "y-")

    def test_inspect_tool_routes_4d_w_translation_without_switching_tool(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        move_w_neg = KEYS_4D["move_w_neg"][0]
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, move_w_neg)
        apply_step.assert_called_once_with(state, "w-")
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)

    def test_sandbox_tool_routes_4d_w_translation_without_switching_tool(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        move_w_neg = KEYS_4D["move_w_neg"][0]
        with patch.object(
            topology_lab_controls_panel, "_apply_sandbox_shortcut_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, move_w_neg)
        apply_step.assert_called_once_with(state, "w-")
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_SANDBOX)

    def test_navigate_tool_routes_3d_depth_translation_to_probe_step(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        move_z_neg = KEYS_3D["move_z_neg"][0]
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, move_z_neg)
        apply_step.assert_called_once_with(state, "z-")

    def test_navigate_tool_routes_4d_w_translation_to_probe_step(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.active_pane = topology_lab_menu.PANE_SCENE
        move_w_pos = KEYS_4D["move_w_pos"][0]
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, move_w_pos)
        apply_step.assert_called_once_with(state, "w+")

    def test_sandbox_tool_routes_2d_rotation_binding(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with patch.object(
            topology_lab_controls_panel,
            "rotate_sandbox_piece_action",
            return_value=(True, "sandbox rotated"),
        ) as rotate_action:
            topology_lab_menu._dispatch_key(state, pygame.K_q)
        rotate_action.assert_called_once_with(
            state, state.explorer_profile, "rotate_xy_pos"
        )

    def test_sandbox_tool_routes_3d_rotation_binding(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        rotate_xz = KEYS_3D["rotate_xz_pos"][0]
        with patch.object(
            topology_lab_controls_panel,
            "rotate_sandbox_piece_action",
            return_value=(True, "sandbox rotated"),
        ) as rotate_action:
            topology_lab_menu._dispatch_key(state, rotate_xz)
        rotate_action.assert_called_once_with(
            state, state.explorer_profile, "rotate_xz_pos"
        )

    def test_sandbox_tool_routes_3d_rotation_binding_without_saving(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        rotate_xz_neg = KEYS_3D["rotate_xz_neg"][0]
        with (
            patch.object(
                topology_lab_controls_panel,
                "rotate_sandbox_piece_action",
                return_value=(True, "sandbox rotated"),
            ) as rotate_action,
            patch.object(topology_lab_controls_panel, "_save_profile") as save_profile,
        ):
            topology_lab_menu._dispatch_key(state, rotate_xz_neg)
        rotate_action.assert_called_once_with(
            state, state.explorer_profile, "rotate_xz_neg"
        )
        save_profile.assert_not_called()
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_SANDBOX)

    def test_sandbox_tool_routes_4d_rotation_binding_without_switching_tool(
        self,
    ) -> None:
        state = self._explorer_state(4)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        rotate_xw_neg = KEYS_4D["rotate_xw_neg"][0]
        with patch.object(
            topology_lab_controls_panel,
            "rotate_sandbox_piece_action",
            return_value=(True, "sandbox rotated"),
        ) as rotate_action:
            topology_lab_menu._dispatch_key(state, rotate_xw_neg)
        rotate_action.assert_called_once_with(
            state, state.explorer_profile, "rotate_xw_neg"
        )
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_SANDBOX)

    def test_controls_pane_s_shortcut_saves_profile(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        with patch.object(topology_lab_controls_panel, "_save_profile") as save_profile:
            topology_lab_menu._dispatch_key(state, pygame.K_s)
        save_profile.assert_called_once_with(state)

    def test_explorer_entry_space_cycles_piece_immediately(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="explorer",
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        with (
            patch.object(
                topology_lab_controls_panel, "_apply_probe_step"
            ) as apply_probe_step,
            patch.object(
                topology_lab_controls_panel, "_apply_sandbox_shortcut_step"
            ) as apply_sandbox_step,
            patch.object(
                topology_lab_controls_panel,
                "handle_scene_camera_key",
                return_value=True,
            ) as handle_camera,
            patch.object(
                topology_lab_controls_panel, "cycle_sandbox_piece"
            ) as cycle_piece,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_SPACE)
        apply_probe_step.assert_not_called()
        apply_sandbox_step.assert_not_called()
        handle_camera.assert_not_called()
        self.assertEqual(launch.initial_tool, topology_lab_menu.TOOL_SANDBOX)
        cycle_piece.assert_called_once_with(state, 1)

    def test_sandbox_tool_space_cycles_piece_without_mode_leakage(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with (
            patch.object(
                topology_lab_controls_panel, "_apply_probe_step"
            ) as apply_probe_step,
            patch.object(
                topology_lab_controls_panel, "_apply_sandbox_shortcut_step"
            ) as apply_sandbox_step,
            patch.object(
                topology_lab_controls_panel,
                "handle_scene_camera_key",
                return_value=True,
            ) as handle_camera,
            patch.object(
                topology_lab_controls_panel, "cycle_sandbox_piece"
            ) as cycle_piece,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_SPACE)
        apply_probe_step.assert_not_called()
        apply_sandbox_step.assert_not_called()
        handle_camera.assert_not_called()
        cycle_piece.assert_called_once_with(state, 1)

    def test_sandbox_right_click_boundary_stays_in_sandbox(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        target = topology_lab_menu.TopologyLabHitTarget(
            "boundary_pick", 2, pygame.Rect(0, 0, 10, 10)
        )
        with patch.object(
            topology_lab_menu, "apply_boundary_edit_pick", return_value="editing"
        ) as edit_pick:
            handled = topology_lab_menu._dispatch_mouse_target(state, target, 3)
        self.assertTrue(handled)
        edit_pick.assert_not_called()
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_SANDBOX)

    def test_play_tool_does_not_route_bound_translation_to_inspect_step(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        state.active_pane = topology_lab_menu.PANE_SCENE
        with patch.object(
            topology_lab_controls_panel, "_apply_probe_step"
        ) as apply_step:
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
        apply_step.assert_not_called()

    def test_tab_and_shift_tab_cycle_panes(self) -> None:
        state = self._explorer_state(3)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        topology_lab_menu._dispatch_key(state, pygame.K_TAB)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_CONTROLS)
        topology_lab_menu._dispatch_key(state, pygame.K_TAB, pygame.KMOD_SHIFT)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)

    def test_enter_in_play_tool_requests_play_preview(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        state.active_pane = topology_lab_menu.PANE_SCENE
        self.assertFalse(state.play_preview_requested)
        topology_lab_menu._dispatch_key(state, pygame.K_RETURN)
        self.assertTrue(state.play_preview_requested)

    def test_backspace_removes_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        self.assertEqual(len(self._current_explorer_profile(state).gluings), 1)
        topology_lab_menu._dispatch_key(state, pygame.K_BACKSPACE)
        self.assertEqual(len(self._current_explorer_profile(state).gluings), 0)

    def test_apply_explorer_glue_adds_2d_gluing_to_profile(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu._apply_explorer_glue(state)
        profile = self._current_explorer_profile(state)
        self.assertEqual(len(profile.gluings), 1)
        self.assertEqual(profile.dimension, 2)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_2d(self) -> None:
        state = self._explorer_state(2)
        with (
            patch.object(
                topology_lab_controls_panel,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_controls_panel,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(self._current_explorer_profile(state))
        save_legacy.assert_not_called()

    def test_unsafe_explorer_preset_label_is_marked(self) -> None:
        state = self._explorer_state(2)
        presets = topology_lab_menu._explorer_presets(state)
        unsafe_index = next(
            index
            for index, preset in enumerate(presets)
            if preset.preset_id == "projective_2d"
        )
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            presets[unsafe_index].profile,
        )
        label = topology_lab_menu._explorer_preset_value_text(state)
        self.assertIn("[unsafe]", label)

    def test_export_uses_direct_explorer_preview_for_2d_editor(self) -> None:
        state = self._explorer_state(2)
        with (
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_controls_panel,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
        ):
            topology_lab_menu._run_export(state)
        export_preview.assert_called_once()
        export_legacy.assert_not_called()
        self.assertIn("preview exported", state.status)

    def test_editor_rows_drop_diagnostics_and_row_based_seam_editing_for_3d(
        self,
    ) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("explorer_preset", row_keys)
        self.assertNotIn("analysis_transform", row_keys)
        self.assertNotIn("explorer_source", row_keys)
        self.assertNotIn("apply_glue", row_keys)
        self.assertNotIn("topology_mode", row_keys)
        self.assertNotIn("y_neg", row_keys)

    def test_rows_include_play_settings_for_3d_explorer(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("dimension", row_keys)
        self.assertIn("editor_trace", row_keys)
        self.assertIn("editor_probe_neighbors", row_keys)
        self.assertIn("editor_tool", row_keys)
        self.assertIn("board_x", row_keys)
        self.assertIn("board_y", row_keys)
        self.assertIn("board_z", row_keys)
        self.assertIn("explorer_preset", row_keys)
        self.assertNotIn("piece_set", row_keys)
        self.assertNotIn("speed_level", row_keys)
        self.assertNotIn("rigid_play_mode", row_keys)
        self.assertNotIn("sandbox_neighbor_search", row_keys)

    def test_rows_include_play_settings_for_4d_explorer(self) -> None:
        state = self._explorer_state(4)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("dimension", row_keys)
        self.assertIn("editor_trace", row_keys)
        self.assertIn("editor_probe_neighbors", row_keys)
        self.assertIn("board_x", row_keys)
        self.assertIn("board_y", row_keys)
        self.assertIn("board_z", row_keys)
        self.assertIn("board_w", row_keys)
        self.assertIn("explorer_preset", row_keys)
        self.assertNotIn("piece_set", row_keys)
        self.assertNotIn("speed_level", row_keys)
        self.assertNotIn("rigid_play_mode", row_keys)
        self.assertNotIn("sandbox_neighbor_search", row_keys)

    def test_sandbox_rows_expose_neighbors_only_in_sandbox_workspace(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)

        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]

        self.assertIn("dimension", row_keys)
        self.assertIn("editor_trace", row_keys)
        self.assertIn("editor_probe_neighbors", row_keys)
        self.assertIn("piece_set", row_keys)
        self.assertIn("sandbox_neighbor_search", row_keys)
        self.assertNotIn("editor_tool", row_keys)
        self.assertNotIn("board_x", row_keys)
        self.assertNotIn("board_y", row_keys)
        self.assertNotIn("board_z", row_keys)
        self.assertNotIn("explorer_preset", row_keys)
        self.assertNotIn("speed_level", row_keys)
        self.assertNotIn("rigid_play_mode", row_keys)

    def test_play_rows_expose_speed_and_transport_only_in_play_workspace(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)

        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]

        self.assertIn("dimension", row_keys)
        self.assertIn("editor_trace", row_keys)
        self.assertIn("editor_probe_neighbors", row_keys)
        self.assertIn("speed_level", row_keys)
        self.assertIn("rigid_play_mode", row_keys)
        self.assertNotIn("editor_tool", row_keys)
        self.assertNotIn("board_x", row_keys)
        self.assertNotIn("piece_set", row_keys)
        self.assertNotIn("sandbox_neighbor_search", row_keys)

    def test_editor_trace_row_toggles_editor_owned_trace_state(self) -> None:
        state = self._explorer_state(3)
        row = next(
            row
            for row in topology_lab_menu._rows_for_state(state)
            if row.key == "editor_trace"
        )

        self.assertTrue(topology_lab_menu._probe_trace_visible(state))

        handled = topology_lab_menu._adjust_row(state, row, 1)

        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_menu._active_workspace_name(state),
            topology_lab_menu.WORKSPACE_EDITOR,
        )
        self.assertFalse(topology_lab_menu._probe_trace_visible(state))
        self.assertIn("Editor trace hidden", state.status)

    def test_editor_probe_neighbors_row_toggles_editor_owned_probe_overlay(self) -> None:
        state = self._explorer_state(3)
        row = next(
            row
            for row in topology_lab_menu._rows_for_state(state)
            if row.key == "editor_probe_neighbors"
        )

        self.assertFalse(topology_lab_menu._probe_neighbors_visible(state))

        handled = topology_lab_menu._adjust_row(state, row, 1)

        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_menu._active_workspace_name(state),
            topology_lab_menu.WORKSPACE_EDITOR,
        )
        self.assertTrue(topology_lab_menu._probe_neighbors_visible(state))
        self.assertIn("Editor probe neighbors shown", state.status)

    def test_sandbox_neighbors_row_toggles_sandbox_owned_neighbor_state(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.neighbor_search_enabled = False
        row = next(
            row
            for row in topology_lab_menu._rows_for_state(state)
            if row.key == "sandbox_neighbor_search"
        )

        handled = topology_lab_menu._adjust_row(state, row, 1)

        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_menu._active_workspace_name(state),
            topology_lab_menu.WORKSPACE_SANDBOX,
        )
        self.assertTrue(state.sandbox.neighbor_search_enabled)
        self.assertIn("neighbor-search enabled", state.status)

    def test_workspace_layout_keeps_helper_external_to_scene_and_editor_panels(self) -> None:
        (
            tool_rect,
            top_rect,
            editor_rect,
            helper_rect,
            _helper_controls_rect,
            action_rect,
        ) = topology_lab_menu._explorer_workspace_layout(
            panel_x=40,
            panel_y=160,
            panel_w=1040,
            panel_h=620,
            menu_w=460,
        )

        self.assertGreater(helper_rect.left, top_rect.right)
        self.assertEqual(helper_rect.top, top_rect.top)
        self.assertEqual(helper_rect.bottom, editor_rect.bottom)
        self.assertEqual(tool_rect.width, 1040 - 460 - 30)
        self.assertLess(action_rect.right, helper_rect.left)

    def test_draw_menu_keeps_editor_context_rows_visible(self) -> None:
        screen = pygame.Surface((1280, 900))
        fonts = self._fonts()
        state = self._explorer_state(3)

        topology_lab_menu._draw_menu(screen, fonts, state)

        row_targets = {
            target.value: target
            for target in state.mouse_targets
            if target.kind == "row_select"
        }
        self.assertIn("editor_tool", row_targets)
        self.assertIn("editor_trace", row_targets)
        self.assertIn("editor_probe_neighbors", row_targets)
        self.assertGreater(row_targets["editor_trace"].rect.width, 240)
        self.assertLess(row_targets["editor_trace"].rect.bottom, screen.get_height())
        self.assertGreater(row_targets["editor_probe_neighbors"].rect.width, 240)
        self.assertLess(
            row_targets["editor_probe_neighbors"].rect.bottom,
            screen.get_height(),
        )

    def test_draw_menu_keeps_sandbox_context_rows_visible(self) -> None:
        screen = pygame.Surface((1280, 900))
        fonts = self._fonts()
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)

        topology_lab_menu._draw_menu(screen, fonts, state)

        row_targets = {
            target.value: target
            for target in state.mouse_targets
            if target.kind == "row_select"
        }
        self.assertIn("sandbox_neighbor_search", row_targets)
        self.assertGreater(row_targets["sandbox_neighbor_search"].rect.width, 240)
        self.assertLess(
            row_targets["sandbox_neighbor_search"].rect.bottom,
            screen.get_height(),
        )

    def test_compact_shell_layout_keeps_required_top_bar_text_visible(self) -> None:
        fonts = self._fonts()
        layout = topology_lab_shell_layout.build_topology_lab_shell_layout(
            width=1180,
            height=760,
            general_editor=True,
            scene_pane_active=False,
            row_count=18,
            dimension_text_width=fonts.hint_font.size("4D")[0],
            validity_text_width=fonts.hint_font.size("Needs Fix")[0],
            action_count=6,
        )
        assert layout.top_bar is not None

        self.assertTrue(
            text_fits(
                fonts.hint_font,
                "Topology Playground",
                layout.top_bar.title_rect.width,
            )
        )
        button_w = max(
            72,
            (layout.top_bar.ribbon_rect.width - (3 - 1) * 8) // 3,
        )
        for label in ("Editor", "Sandbox", "Play"):
            with self.subTest(label=label):
                self.assertTrue(text_fits(fonts.hint_font, label, button_w - 10))
        for label in ("Valid", "Needs Fix", "Unsafe"):
            with self.subTest(chip=label):
                self.assertTrue(
                    text_fits(
                        fonts.hint_font,
                        label,
                        layout.top_bar.validity_chip_rect.width - 12,
                    )
                )
        self.assertTrue(
            text_fits(
                fonts.hint_font,
                "4D",
                layout.top_bar.dimension_chip_rect.width - 12,
            )
        )

    def test_compact_shell_layout_keeps_footer_actions_visible(self) -> None:
        fonts = self._fonts()
        layout = topology_lab_shell_layout.build_topology_lab_shell_layout(
            width=1180,
            height=760,
            general_editor=True,
            scene_pane_active=False,
            row_count=18,
            dimension_text_width=fonts.hint_font.size("3D")[0],
            validity_text_width=fonts.hint_font.size("Valid")[0],
            action_count=6,
        )
        assert layout.footer is not None
        button_w = max(76, (layout.footer.action_rect.width - (6 - 1) * 8) // 6)
        for label in (
            "Spawn",
            "Prev Piece",
            "Next Piece",
            "Rotate",
            "Show Path",
            "Reset",
        ):
            with self.subTest(label=label):
                self.assertTrue(text_fits(fonts.hint_font, label, button_w - 10))

    def test_compact_shell_layout_keeps_required_top_bar_text_visible_at_960_width(
        self,
    ) -> None:
        fonts = self._fonts()
        layout = topology_lab_shell_layout.build_topology_lab_shell_layout(
            width=960,
            height=760,
            general_editor=True,
            scene_pane_active=False,
            row_count=18,
            dimension_text_width=fonts.hint_font.size("4D")[0],
            validity_text_width=fonts.hint_font.size("Needs Fix")[0],
            action_count=2,
        )
        assert layout.top_bar is not None

        self.assertTrue(
            text_fits(
                fonts.hint_font,
                "Topology Playground",
                layout.top_bar.title_rect.width,
            )
        )
        button_w = max(
            68,
            (layout.top_bar.ribbon_rect.width - (3 - 1) * 8) // 3,
        )
        for label in ("Editor", "Sandbox", "Play"):
            with self.subTest(label=label):
                self.assertTrue(text_fits(fonts.hint_font, label, button_w - 10))

    def test_row_text_budgets_fit_compact_controls_lane(self) -> None:
        budgets = topology_lab_shell_layout.topology_lab_row_text_budgets(
            menu_w=296,
            row_rect_width=268,
        )
        self.assertLessEqual(budgets.label_width + budgets.value_width + 48, 268)
        self.assertGreaterEqual(budgets.value_width, 56)

    def test_workspace_layout_preserves_readable_helper_width_in_compact_shell(self) -> None:
        (
            _tool_rect,
            top_rect,
            _editor_rect,
            helper_rect,
            _helper_controls_rect,
            _action_rect,
        ) = topology_lab_menu._explorer_workspace_layout(
            panel_x=12,
            panel_y=80,
            panel_w=936,
            panel_h=620,
            menu_w=296,
        )

        self.assertGreaterEqual(helper_rect.width, 176)
        self.assertGreaterEqual(top_rect.width, 340)

    def test_shell_layout_stays_within_viewport_on_narrow_supported_width(self) -> None:
        fonts = self._fonts()
        layout = topology_lab_shell_layout.build_topology_lab_shell_layout(
            width=800,
            height=680,
            general_editor=True,
            scene_pane_active=False,
            row_count=18,
            dimension_text_width=fonts.hint_font.size("4D")[0],
            validity_text_width=fonts.hint_font.size("Needs Fix")[0],
            action_count=2,
        )
        self.assertGreaterEqual(layout.panel_rect.left, 0)
        self.assertLessEqual(layout.panel_rect.right, 800)
        self.assertLessEqual(layout.panel_rect.bottom, 680)
        self.assertLessEqual(layout.menu_w, 320)

    def test_workspace_layout_preserves_helper_lane_on_narrow_supported_width(self) -> None:
        (
            _tool_rect,
            top_rect,
            _editor_rect,
            helper_rect,
            _helper_controls_rect,
            _action_rect,
        ) = topology_lab_menu._explorer_workspace_layout(
            panel_x=12,
            panel_y=80,
            panel_w=776,
            panel_h=620,
            menu_w=248,
        )
        self.assertGreater(helper_rect.left, top_rect.right)
        self.assertGreaterEqual(helper_rect.width, 144)

    def test_row_step_target_adjusts_explorer_board_z(self) -> None:
        state = self._explorer_state(3)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(7, 18, 6)),
        )
        initial_dims = topology_lab_menu._board_dims_for_state(state)
        target = topology_lab_menu.TopologyLabHitTarget(
            "row_step", ("board_z", 1), pygame.Rect(0, 0, 10, 10)
        )
        handled = topology_lab_menu._dispatch_mouse_target(state, target, 1)
        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_menu._board_dims_for_state(state),
            (initial_dims[0], initial_dims[1], initial_dims[2] + 1),
        )

    def test_row_step_target_sets_controls_pane_and_supports_minus(self) -> None:
        state = self._explorer_state(3)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.build_explorer_playground_settings(dimension=3),
        )
        state.active_pane = topology_lab_menu.PANE_SCENE
        initial_dims = topology_lab_menu._board_dims_for_state(state)
        target = topology_lab_menu.TopologyLabHitTarget(
            "row_step", ("board_z", -1), pygame.Rect(0, 0, 10, 10)
        )
        handled = topology_lab_menu._dispatch_mouse_target(state, target, 1)
        self.assertTrue(handled)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_CONTROLS)
        self.assertEqual(
            topology_lab_menu._board_dims_for_state(state),
            (initial_dims[0], initial_dims[1], initial_dims[2] - 1),
        )

    def test_explorer_height_row_allows_lowering_minimum_to_six(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(7, 6, 6)),
        )

        topology_lab_menu._set_selected_row_by_key(state, "board_y")
        topology_lab_menu._dispatch_key(state, pygame.K_LEFT)

        self.assertEqual(topology_lab_menu._board_dims_for_state(state), (7, 6, 6))

        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(7, 7, 6)),
        )
        topology_lab_menu._dispatch_key(state, pygame.K_LEFT)

        self.assertEqual(topology_lab_menu._board_dims_for_state(state), (7, 6, 6))

    def test_cycle_dimension_with_invalid_loaded_explorer_profile_does_not_crash(
        self,
    ) -> None:
        state = self._explorer_state(2)
        with (
            patch.object(
                topology_lab_controls_panel,
                "load_runtime_explorer_topology_profile",
                return_value=self._invalid_explorer_profile(3),
            ),
            patch.object(
                topology_lab_controls_panel,
                "build_explorer_playground_settings",
                return_value=topology_lab_menu.ExplorerPlaygroundSettings(
                    board_dims=(7, 18, 6)
                ),
            ),
        ):
            topology_lab_menu._cycle_dimension(state, 1)
        self.assertEqual(state.dimension, 3)
        assert state.canonical_state is not None
        self.assertEqual(
            topology_lab_scene_state.current_probe_coord(state),
            state.canonical_state.probe_state.coord,
        )
        self.assertEqual(
            tuple(topology_lab_scene_state.current_probe_path(state)),
            state.canonical_state.probe_state.path,
        )

    def test_cycle_dimension_resets_stale_sandbox_state_from_previous_dimension(
        self,
    ) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        state.sandbox = TopologyPlaygroundSandboxPieceState(
            enabled=True,
            origin=(1, 2, 3),
            local_blocks=((0, 0, 0),),
        )

        topology_lab_menu._cycle_dimension(state, -1)

        self.assertEqual(state.dimension, 2)
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.dimension, 2)
        assert state.sandbox is not None
        self.assertFalse(state.sandbox.enabled)
        self.assertIsNone(state.sandbox.origin)
        self.assertIsNone(state.sandbox.local_blocks)

    def test_draw_menu_does_not_crash_with_invalid_explorer_profile_for_current_dims(
        self,
    ) -> None:
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
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            self._invalid_explorer_profile(3),
        )
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(7, 18, 6)),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        topology_lab_menu._ensure_probe_state(state)
        topology_lab_menu._draw_menu(screen, fonts, state)
        assert state.canonical_state is not None
        self.assertEqual(
            topology_lab_scene_state.current_probe_coord(state),
            state.canonical_state.probe_state.coord,
        )
        self.assertEqual(
            tuple(topology_lab_scene_state.current_probe_path(state)),
            state.canonical_state.probe_state.path,
        )
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            None,
            "gluing transform is not bijective for the board dimensions",
        )
        self.assertIn("Validity: Invalid", lines)
        self.assertIn("Preview unavailable until the topology validates.", lines)

    def test_apply_probe_step_updates_canonical_probe_state(self) -> None:
        state = self._explorer_state(3)
        with patch.object(
            topology_lab_controls_panel,
            "advance_explorer_probe",
            return_value=(
                (2, 1, 1),
                {
                    "message": "Moved x+",
                    "blocked": False,
                    "traversal": {"glue_id": "glue_123"},
                },
            ),
        ):
            topology_lab_menu._apply_probe_step(state, "x+")
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.probe_state.coord, (2, 1, 1))
        self.assertEqual(
            state.canonical_state.probe_state.highlighted_gluing,
            "glue_123",
        )
        self.assertEqual(
            topology_lab_scene_state.current_highlighted_glue_id(state),
            "glue_123",
        )
        self.assertIn("Moved x+", state.canonical_state.probe_state.trace)

    def test_probe_repeated_diagonal_on_sphere_keeps_progress_across_seam(
        self,
    ) -> None:
        cases = (
            ((8, 8), 4),
            ((9, 9), 5),
        )

        for dims, diagonal_pairs in cases:
            with self.subTest(dims=dims):
                state = self._explorer_state(2)
                topology_lab_controls_panel.replace_explorer_profile(
                    state, sphere_profile_2d()
                )
                topology_lab_controls_panel.replace_play_settings(
                    state,
                    topology_lab_menu.ExplorerPlaygroundSettings(board_dims=dims),
                )
                topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
                state.active_pane = topology_lab_menu.PANE_SCENE
                topology_lab_controls_panel._reset_probe(state)
                expected_coord = topology_lab_scene_state.current_probe_coord(state)

                for _ in range(diagonal_pairs):
                    topology_lab_menu._dispatch_key(state, pygame.K_DOWN)
                    topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
                    expected_coord, _ = topology_lab_controls_panel.advance_explorer_probe(
                        sphere_profile_2d(),
                        dims=dims,
                        coord=expected_coord,
                        step_label="y+",
                    )
                    expected_coord, _ = topology_lab_controls_panel.advance_explorer_probe(
                        sphere_profile_2d(),
                        dims=dims,
                        coord=expected_coord,
                        step_label="x+",
                    )

                self.assertEqual(
                    topology_lab_scene_state.current_probe_coord(state),
                    expected_coord,
                )
                assert state.canonical_state is not None
                self.assertEqual(state.canonical_state.probe_state.coord, expected_coord)

                topology_lab_menu._dispatch_key(state, pygame.K_DOWN)
                expected_coord, _ = topology_lab_controls_panel.advance_explorer_probe(
                    sphere_profile_2d(),
                    dims=dims,
                    coord=expected_coord,
                    step_label="y+",
                )
                self.assertEqual(
                    topology_lab_scene_state.current_probe_coord(state),
                    expected_coord,
                )
                self.assertEqual(state.canonical_state.probe_state.coord, expected_coord)

    def test_apply_explorer_glue_adds_gluing_to_profile_3d(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        self.assertEqual(len(self._current_explorer_profile(state).gluings), 1)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_3d(self) -> None:
        state = self._explorer_state(3)
        with (
            patch.object(
                topology_lab_controls_panel,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_controls_panel,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(self._current_explorer_profile(state))
        save_legacy.assert_not_called()

    def test_export_uses_direct_explorer_preview_for_3d_editor(self) -> None:
        state = self._explorer_state(3)
        with (
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_controls_panel,
                "export_topology_profile_state",
                return_value=(True, "legacy exported", None),
            ) as export_legacy,
        ):
            topology_lab_menu._run_export(state)
        export_preview.assert_called_once()
        export_legacy.assert_not_called()
        self.assertIn("preview exported", state.status)

    def test_editor_rows_drop_diagnostics_and_row_based_seam_editing_for_4d(
        self,
    ) -> None:
        state = self._explorer_state(4)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("explorer_preset", row_keys)
        self.assertNotIn("analysis_transform", row_keys)
        self.assertNotIn("explorer_source", row_keys)
        self.assertNotIn("explorer_sign_2", row_keys)
        self.assertNotIn("apply_glue", row_keys)
        self.assertNotIn("topology_mode", row_keys)
        self.assertNotIn("y_neg", row_keys)

    def test_apply_explorer_glue_adds_4d_gluing_to_profile(self) -> None:
        state = self._explorer_state(4)
        topology_lab_menu._apply_explorer_glue(state)
        profile = self._current_explorer_profile(state)
        self.assertEqual(len(profile.gluings), 1)
        self.assertEqual(profile.dimension, 4)
        self.assertFalse(state.status_error)

    def test_save_profile_uses_explorer_store_for_direct_editor_4d(self) -> None:
        state = self._explorer_state(4)
        with (
            patch.object(
                topology_lab_controls_panel,
                "save_explorer_topology_profile",
                return_value=(True, "saved explorer"),
            ) as save_explorer,
            patch.object(
                topology_lab_controls_panel,
                "save_topology_profile",
                return_value=(True, "saved legacy"),
            ) as save_legacy,
        ):
            ok, _message = topology_lab_menu._save_profile(state)
        self.assertTrue(ok)
        save_explorer.assert_called_once_with(self._current_explorer_profile(state))
        save_legacy.assert_not_called()

    def test_export_uses_direct_explorer_preview_for_4d_editor(self) -> None:
        state = self._explorer_state(4)
        with (
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(
                topology_lab_controls_panel,
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
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="twist",
                        source=BoundaryRef(dimension=3, axis=0, side="-"),
                        target=BoundaryRef(dimension=3, axis=0, side="+"),
                        transform=BoundaryTransform(permutation=(0, 1), signs=(-1, 1)),
                    ),
                ),
            ),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        lines = topology_lab_menu._explorer_sidebar_lines(state)
        self.assertIn("  Warnings", lines)
        self.assertTrue(
            any("orientation-reversing seam transforms" in line for line in lines)
        )

    def test_preview_lines_show_engine_owned_arrow_basis(self) -> None:
        state = self._explorer_state(3)
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            ExplorerTopologyProfile(
                dimension=3,
                gluings=(
                    GluingDescriptor(
                        glue_id="swap",
                        source=BoundaryRef(dimension=3, axis=0, side="-"),
                        target=BoundaryRef(dimension=3, axis=2, side="+"),
                        transform=BoundaryTransform(permutation=(1, 0), signs=(1, -1)),
                    ),
                ),
            ),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        lines = topology_lab_menu._explorer_sidebar_lines(state)
        self.assertIn("  Arrow basis", lines)
        self.assertTrue(any("x- -> z+" in line for line in lines))
        self.assertTrue(any("+y -> +y" in line for line in lines))
        self.assertTrue(any("+z -> -x" in line for line in lines))

    def test_playability_rows_and_preview_lines_show_projective_as_explorer_only(
        self,
    ) -> None:
        state = self._explorer_state(2)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            projective_plane_profile_2d(),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
            state
        )
        topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
            state
        )

        rows = topology_lab_menu._rows_for_state(state)
        rigid_mode_row = next(row for row in rows if row.key == "rigid_play_mode")
        self.assertEqual(
            topology_lab_menu._row_value_text(state, rigid_mode_row),
            "Auto (Cellwise)",
        )

        lines = topology_lab_menu._workspace_preview_lines(
            state,
            state.scene_preview,
            state.scene_preview_error,
        )
        self.assertIn("Validity: Valid", lines)
        self.assertIn("Explorer: Cellwise explorable", lines)
        self.assertIn("Rigid play: Not rigid-playable", lines)
        self.assertIn(
            "Play: Play uses cellwise seam transport automatically for this topology.",
            lines,
        )
        self.assertEqual(
            topology_lab_control_values._playability_shell_chip_text(state),
            "Unsafe",
        )

    def test_playability_preview_lines_show_invalid_topology_state(self) -> None:
        state = self._explorer_state(2)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(5, 4)),
        )
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            sphere_profile_2d(),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)

        lines = topology_lab_menu._workspace_preview_lines(
            state,
            state.scene_preview,
            state.scene_preview_error,
        )
        self.assertIn("Validity: Invalid", lines)
        self.assertIn("Explorer: Not explorable", lines)
        self.assertIn("Rigid play: Not rigid-playable", lines)
        self.assertIn("Preview unavailable until the topology validates.", lines)
        self.assertTrue(
            any("unsupported for current board dimensions" in line for line in lines)
        )
        self.assertEqual(
            topology_lab_control_values._playability_shell_chip_text(state),
            "Needs Fix",
        )

    def test_valid_playability_maps_to_valid_shell_chip(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu._refresh_explorer_scene_state(state)

        self.assertEqual(
            topology_lab_control_values._playability_shell_chip_text(state),
            "Valid",
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
        self.assertEqual(self._current_explorer_profile(state).gluings, ())

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
        self.assertTrue(
            any(target.kind == "workspace_mode" for target in targets)
        )
        self.assertFalse(any(target.kind == "preset_step" for target in targets))
        self.assertTrue(any(target.kind == "glue_slot" for target in targets))
        self.assertTrue(any(target.kind == "perm_select" for target in targets))
        self.assertTrue(any(target.kind == "action" for target in targets))

    def test_draw_menu_skips_row_select_targets_for_analysis_status_rows(self) -> None:
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
        row_select_values = {
            target.value
            for target in state.mouse_targets or []
            if target.kind == "row_select"
        }
        self.assertNotIn("analysis_boundary", row_select_values)
        self.assertNotIn("analysis_glue", row_select_values)
        self.assertNotIn("analysis_transform", row_select_values)

    def test_mouse_click_minus_button_decrements_board_size(self) -> None:
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
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.build_explorer_playground_settings(dimension=3),
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        before = topology_lab_menu._board_dims_for_state(state)
        topology_lab_menu._draw_menu(screen, fonts, state)
        minus_target = next(
            target
            for target in state.mouse_targets or []
            if target.kind == "row_step" and target.value == ("board_z", -1)
        )
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, minus_target.rect.center, 1)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_CONTROLS)
        self.assertEqual(
            topology_lab_menu._board_dims_for_state(state),
            (before[0], before[1], before[2] - 1),
        )

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

    def test_mouse_boundary_pick_stays_scene_driven_when_analysis_view_is_active(
        self,
    ) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu._set_selected_row_by_key(state, "explorer_preset")
        target = topology_lab_menu.TopologyLabHitTarget(
            kind="boundary_pick",
            value=4,
            rect=pygame.Rect(0, 0, 40, 40),
        )
        state.mouse_targets = [target]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        current_draft = self._current_explorer_draft(state)
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertEqual(
            topology_lab_scene_state.current_selected_boundary_index(state),
            4,
        )
        self.assertEqual(current_draft.source_index, 0)

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
        current_draft = self._current_explorer_draft(state)
        self.assertEqual(current_draft.source_index, 1)
        self.assertEqual(current_draft.target_index, 4)
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
        self.assertEqual(len(self._current_explorer_profile(state).gluings), 1)

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
        self.assertIsNotNone(topology_lab_scene_state.current_probe_coord(state))
        self.assertTrue(topology_lab_scene_state.current_probe_trace(state))

    def test_mouse_preset_cycle_updates_explorer_profile(self) -> None:
        state = self._explorer_state(3)
        original = self._current_explorer_profile(state)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="row_step",
                value=("explorer_preset", 1),
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertNotEqual(self._current_explorer_profile(state), original)

    def test_probe_tool_mouse_preset_cycle_updates_explorer_profile(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        original = self._current_explorer_profile(state)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="row_step",
                value=("explorer_preset", 1),
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertNotEqual(self._current_explorer_profile(state), original)

    def test_probe_footer_labels_change_with_active_tool(self) -> None:
        screen = pygame.Surface((640, 480))
        fonts = self._fonts()
        state = self._explorer_state(2)
        area = pygame.Rect(0, 0, 240, 60)
        with patch.object(
            topology_lab_workspace_shell, "draw_probe_controls", return_value=[]
        ) as draw_controls:
            topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
            topology_lab_menu._draw_probe_controls_if_needed(
                screen,
                fonts,
                state=state,
                area=area,
                preview={},
            )
            self.assertEqual(
                draw_controls.call_args.kwargs["title"], "Editor probe moves"
            )
            self.assertEqual(
                draw_controls.call_args.kwargs["active_color"], (56, 92, 130)
            )
            draw_controls.reset_mock()
            topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)
            topology_lab_menu._draw_probe_controls_if_needed(
                screen,
                fonts,
                state=state,
                area=area,
                preview={},
            )
            draw_controls.assert_not_called()
            draw_controls.reset_mock()
            topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
            topology_lab_menu._draw_probe_controls_if_needed(
                screen,
                fonts,
                state=state,
                area=area,
                preview={},
            )
            self.assertEqual(
                draw_controls.call_args.kwargs["title"],
                "Sandbox piece moves",
            )
            self.assertEqual(
                draw_controls.call_args.kwargs["active_color"], (78, 116, 92)
            )

    def test_inspect_mode_right_click_boundary_does_not_start_glue_creation(self) -> None:
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
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)
        self.assertIsNone(state.pending_source_index)
        self.assertEqual(
            topology_lab_scene_state.current_selected_boundary_index(state),
            4,
        )

    def test_inspect_mode_right_click_boundary_does_not_edit_existing_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        topology_lab_menu._apply_explorer_glue(state)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=0,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 3)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)
        self.assertEqual(
            topology_lab_scene_state.current_selected_glue_id(state),
            self._current_explorer_profile(state).gluings[0].glue_id,
        )

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
        current_draft = self._current_explorer_draft(state)
        self.assertEqual(current_draft.slot_index, 0)
        self.assertEqual(current_draft.source_index, 0)

    def test_mouse_workspace_mode_select_preserves_sandbox_state(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        state.sandbox.origin = (0, 0, 0)
        state.sandbox.local_blocks = ((0, 0, 0), (1, 0, 0))
        topology_lab_menu._sync_canonical_playground_state(state)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="workspace_mode",
                value=topology_lab_menu.WORKSPACE_EDITOR,
                rect=pygame.Rect(0, 0, 60, 24),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (4, 4), 1)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_PROBE)
        self.assertEqual(
            topology_lab_menu._active_workspace_name(state),
            topology_lab_menu.WORKSPACE_EDITOR,
        )
        assert state.sandbox is not None
        self.assertEqual(state.sandbox.origin, (0, 0, 0))
        self.assertEqual(state.sandbox.local_blocks, ((0, 0, 0), (1, 0, 0)))

    def test_pick_target_prefers_glue_hit_over_boundary_hit(self) -> None:
        boundary = topology_lab_menu.TopologyLabHitTarget(
            "boundary_pick",
            0,
            pygame.Rect(0, 0, 40, 40),
        )
        glue = topology_lab_menu.TopologyLabHitTarget(
            "glue_pick",
            "glue_001",
            pygame.Rect(0, 0, 40, 40),
        )
        picked = topology_lab_menu.pick_target([boundary, glue], (10, 10))
        self.assertIsNotNone(picked)
        assert picked is not None
        self.assertEqual(picked.kind, "glue_pick")

    def test_pick_target_prefers_smaller_specific_hit_with_same_priority(self) -> None:
        large = topology_lab_menu.TopologyLabHitTarget(
            "row_step",
            ("board_x", 1),
            pygame.Rect(0, 0, 80, 40),
        )
        small = topology_lab_menu.TopologyLabHitTarget(
            "row_step",
            ("board_x", -1),
            pygame.Rect(4, 4, 20, 20),
        )
        picked = topology_lab_menu.pick_target([large, small], (10, 10))
        self.assertIsNotNone(picked)
        assert picked is not None
        self.assertEqual(picked.value, ("board_x", -1))

    def test_mouse_glue_pick_switches_to_editing_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._apply_explorer_glue(state)
        glue_id = self._current_explorer_profile(state).gluings[0].glue_id
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
        self.assertEqual(
            topology_lab_scene_state.current_selected_glue_id(state),
            glue_id,
        )

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

    def test_sandbox_action_buttons_include_spawn(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertIn("sandbox_spawn", labels)

    def test_play_preview_action_sets_request_flag(self) -> None:
        state = self._explorer_state(3)
        self.assertFalse(state.play_preview_requested)
        topology_lab_menu._activate_action(state, "play_preview")
        self.assertTrue(state.play_preview_requested)

    def test_action_buttons_label_play_from_current_topology(self) -> None:
        state = self._explorer_state(3)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertNotIn("play_preview", labels)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertEqual(labels["play_preview"], "Play This Topology")

    def test_action_buttons_drop_duplicate_analysis_commands(self) -> None:
        state = self._explorer_state(3)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertNotIn("save_profile", labels)
        self.assertNotIn("export", labels)
        self.assertNotIn("experiments", labels)
        self.assertNotIn("back", labels)
        self.assertIn("apply_glue", labels)
        self.assertIn("remove_glue", labels)
        self.assertNotIn("editor_trace", labels)
        self.assertNotIn("play_preview", labels)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertIn("editor_probe_reset", labels)
        self.assertNotIn("apply_glue", labels)
        self.assertNotIn("experiments", labels)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))
        self.assertIn("sandbox_spawn", labels)
        self.assertNotIn("sandbox_neighbor_search", labels)
        self.assertNotIn("play_preview", labels)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        labels = dict(topology_lab_menu._action_buttons_for_state(state))

        self.assertIn("play_preview", labels)
        self.assertEqual(labels["play_preview"], "Play This Topology")
        self.assertIn("explore_preview", labels)
        self.assertEqual(labels["explore_preview"], "Explore This Topology")

        self.assertNotIn("save_profile", labels)
        self.assertNotIn("export", labels)
        self.assertNotIn("experiments", labels)
        self.assertNotIn("back", labels)

    def test_launch_play_preview_2d_uses_canonical_playground_state(self) -> None:
        state = self._explorer_state(2)
        profile = topology_lab_menu._explorer_presets(state)[1].profile
        state.explorer_profile = profile
        topology_lab_menu._sync_canonical_playground_state(state)
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ) as launch_game:
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        assert state.canonical_state is not None
        self.assertIs(launch_game.call_args.args[0], state.canonical_state)
        self.assertIs(launch_game.call_args.args[1], screen)
        self.assertIs(launch_game.call_args.args[2], fonts)
        self.assertEqual(
            launch_game.call_args.kwargs["return_caption"],
            topology_lab_menu._display_title_for_state(state),
        )
        self.assertIs(launch_game.call_args.kwargs["fonts_2d"], fonts)
        self.assertIsNone(launch_game.call_args.kwargs["display_settings"])

    def test_launch_play_preview_ignores_stale_shell_profile_and_dims(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        state = self._explorer_state(2)
        topology_lab_menu._sync_canonical_playground_state(state)
        assert state.canonical_state is not None
        stale_runtime_state = state.canonical_state
        expected_profile = projective_plane_profile_2d()
        expected_settings = topology_lab_menu.ExplorerPlaygroundSettings(
            board_dims=(5, 4)
        )
        state.explorer_profile = expected_profile
        state.play_settings = expected_settings
        state.dirty = True
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )

        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ) as launch_game:
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )

        launch_game.assert_called_once()
        runtime_state = launch_game.call_args.args[0]
        self.assertIs(runtime_state, stale_runtime_state)
        self.assertIsNot(runtime_state.explorer_profile, expected_profile)
        self.assertNotEqual(runtime_state.axis_sizes, expected_settings.board_dims)

    def test_probe_state_is_canonical_only_after_sync(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu._sync_canonical_playground_state(state)
        assert state.canonical_state is not None
        state.dirty = True
        state.probe_show_trace = False
        state.probe_frame_permutation = (1, 0)
        state.probe_frame_signs = (-1, 1)

        topology_lab_scene_state.sync_shell_state_from_canonical(state)

        self.assertTrue(state.dirty)
        self.assertNotIn("probe_coord", state.__dict__)
        self.assertNotIn("probe_trace", state.__dict__)
        self.assertNotIn("probe_path", state.__dict__)
        self.assertFalse(state.probe_show_trace)
        self.assertEqual(state.probe_frame_permutation, (1, 0))
        self.assertEqual(state.probe_frame_signs, (-1, 1))
        self.assertFalse(topology_lab_scene_state.current_dirty(state))
        self.assertEqual(
            topology_lab_scene_state.current_probe_coord(state),
            state.canonical_state.probe_state.coord,
        )
        self.assertEqual(
            topology_lab_scene_state.current_probe_trace(state),
            list(state.canonical_state.probe_state.trace),
        )
        self.assertEqual(
            topology_lab_scene_state.current_probe_path(state),
            list(state.canonical_state.probe_state.path),
        )
        self.assertTrue(topology_lab_scene_state.probe_trace_visible(state))
        self.assertEqual(topology_lab_scene_state.current_probe_frame(state), ((0, 1), (1, 1)))

    def test_sync_shell_state_leaves_profile_and_draft_as_fallback_only_storage(
        self,
    ) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._sync_canonical_playground_state(state)
        assert state.canonical_state is not None
        stale_profile = ExplorerTopologyProfile(dimension=3, gluings=())
        stale_draft = topology_lab_menu.ExplorerGlueDraft(
            slot_index=0,
            source_index=4,
            target_index=5,
            permutation_index=0,
            signs=(-1, 1),
        )
        state.explorer_profile = stale_profile
        state.explorer_draft = stale_draft

        topology_lab_scene_state.sync_shell_state_from_canonical(state)

        self.assertIs(state.explorer_profile, stale_profile)
        self.assertIs(state.explorer_draft, stale_draft)
        self.assertIsNot(
            topology_lab_scene_state.current_explorer_profile(state),
            stale_profile,
        )
        self.assertNotEqual(
            topology_lab_scene_state.current_explorer_draft(state),
            stale_draft,
        )

    def test_sync_shell_state_keeps_unsynced_selection_and_highlight_mirrors(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._sync_canonical_playground_state(state)
        assert state.canonical_state is not None
        topology_lab_controls_panel.set_selected_boundary_index(state, 2)
        topology_lab_controls_panel.set_selected_glue_id(state, "glue_live")
        topology_lab_controls_panel.set_highlighted_glue_id(state, "glue_highlight")
        state.selected_boundary_index = 5
        state.selected_glue_id = "glue_stale"
        state.highlighted_glue_id = "glue_stale_highlight"

        topology_lab_scene_state.sync_shell_state_from_canonical(state)

        self.assertEqual(state.selected_boundary_index, 5)
        self.assertEqual(state.selected_glue_id, "glue_stale")
        self.assertEqual(state.highlighted_glue_id, "glue_stale_highlight")
        self.assertEqual(topology_lab_scene_state.current_selected_boundary_index(state), 2)
        self.assertEqual(topology_lab_scene_state.current_selected_glue_id(state), "glue_live")
        self.assertEqual(
            topology_lab_scene_state.current_highlighted_glue_id(state),
            "glue_highlight",
        )

    def test_launch_play_preview_keeps_stale_invalid_preview_blocked_until_canonical_state_changes(
        self,
    ) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        state = self._explorer_state(2)
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            sphere_profile_2d(),
        )
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(5, 4)),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        self.assertIsNotNone(state.scene_preview_error)

        expected_profile = projective_plane_profile_2d()
        expected_settings = topology_lab_menu.ExplorerPlaygroundSettings(
            board_dims=(4, 4)
        )
        state.explorer_profile = expected_profile
        state.play_settings = expected_settings
        state.dirty = True

        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )

        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ) as launch_game:
            returned_screen, returned_display = topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )

        launch_game.assert_not_called()
        self.assertIs(returned_screen, screen)
        self.assertIsNone(returned_display)
        self.assertIsNotNone(state.scene_preview_error)
        self.assertTrue(state.status_error)

    def test_editor_probe_reset_action_restores_center_and_clears_trace(self) -> None:
        state = self._explorer_state(2)
        state.active_tool = topology_lab_menu.TOOL_PROBE
        topology_lab_scene_state.replace_probe_state(
            state,
            coord=(0, 0),
            trace=["x-: [0, 0] -> [5, 0]"],
            path=[(0, 0), (5, 0)],
            highlighted_glue_id=None,
        )
        topology_lab_menu._activate_action(state, "editor_probe_reset")
        dims = topology_lab_menu._board_dims_for_state(state)
        expected_coord = tuple(max(0, size // 2) for size in dims)
        self.assertEqual(topology_lab_scene_state.current_probe_coord(state), expected_coord)
        self.assertEqual(topology_lab_scene_state.current_probe_trace(state), [])
        self.assertEqual(
            topology_lab_scene_state.current_probe_path(state),
            [expected_coord],
        )

    def test_launch_play_preview_3d_uses_canonical_playground_state(self) -> None:
        state = self._explorer_state(3)
        profile = topology_lab_menu._explorer_presets(state)[0].profile
        state.explorer_profile = profile
        topology_lab_menu._sync_canonical_playground_state(state)
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        display_settings = object()
        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, display_settings),
        ) as launch_game:
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=display_settings,
            )
        assert state.canonical_state is not None
        self.assertIs(launch_game.call_args.args[0], state.canonical_state)
        self.assertIs(
            launch_game.call_args.kwargs["display_settings"], display_settings
        )

    def test_launch_play_preview_3d_invalid_preview_blocks_runtime(self) -> None:
        state = self._explorer_state(3)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(4, 5, 6)),
        )
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            self._invalid_explorer_profile(3),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)
        self.assertIsNotNone(state.scene_preview_error)
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ) as launch_game:
            returned_screen, returned_display = topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        launch_game.assert_not_called()
        self.assertIs(returned_screen, screen)
        self.assertIsNone(returned_display)
        self.assertTrue(state.status_error)
        self.assertIn("Cannot play current topology", state.status)

    def test_launch_play_preview_4d_uses_canonical_playground_state(self) -> None:
        state = self._explorer_state(4)
        profile = topology_lab_menu._explorer_presets(state)[0].profile
        state.explorer_profile = profile
        topology_lab_menu._sync_canonical_playground_state(state)
        screen = pygame.Surface((640, 480))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        with patch.object(
            topology_lab_controls_panel,
            "launch_playground_state_gameplay",
            return_value=(screen, None),
        ) as launch_game:
            topology_lab_menu._launch_play_preview(
                state,
                screen,
                fonts,
                fonts_2d=fonts,
                display_settings=None,
            )
        assert state.canonical_state is not None
        self.assertIs(launch_game.call_args.args[0], state.canonical_state)

    def test_camera_shortcut_uses_scene_camera_in_navigate_tool(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_SCENE
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.scene_camera = object()
        with patch.object(
            topology_lab_controls_panel, "handle_scene_camera_key", return_value=True
        ) as handle_camera:
            topology_lab_menu._dispatch_key(state, pygame.K_0)
        handle_camera.assert_called_once_with(3, pygame.K_0, state.scene_camera)

    def test_process_events_uses_scene_camera_mouse_handler(self) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_SCENE
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.scene_camera = object()
        state.scene_mouse_orbit = object()
        event = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1})
        with (
            patch("pygame.event.get", return_value=[event]),
            patch.object(
                topology_lab_menu, "handle_scene_camera_mouse_event", return_value=True
            ) as handle_camera_event,
            patch.object(topology_lab_menu, "step_scene_camera") as step_camera,
        ):
            topology_lab_menu._process_topology_lab_events(state, 16.0)
        handle_camera_event.assert_called_once_with(
            3, event, state.scene_camera, state.scene_mouse_orbit
        )
        step_camera.assert_called_once_with(state.scene_camera, 16.0)

    def test_scene_camera_mouse_handler_ignores_left_clicks_for_projection_selection(
        self,
    ) -> None:
        state = self._explorer_state(3)
        state.active_pane = topology_lab_menu.PANE_SCENE
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_NAVIGATE)
        state.scene_camera = object()
        state.scene_mouse_orbit = SimpleNamespace(dragging=False)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (10, 10)}
        )
        with patch.object(
            topology_lab_menu, "handle_scene_camera_mouse_event", return_value=True
        ) as handle_camera_event:
            handled = topology_lab_menu._handle_scene_camera_event(state, event)
        self.assertFalse(handled)
        handle_camera_event.assert_not_called()

    def test_projection_cell_pick_updates_shared_probe_selection(self) -> None:
        state = self._explorer_state(4)
        state.active_pane = topology_lab_menu.PANE_SCENE
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        target = topology_lab_menu.TopologyLabHitTarget(
            "projection_cell",
            (1, 2, 3, 0),
            pygame.Rect(0, 0, 20, 20),
        )
        handled = topology_lab_menu._dispatch_mouse_target(state, target, 1)
        self.assertTrue(handled)
        self.assertEqual(topology_lab_menu._current_probe_coord(state), (1, 2, 3, 0))
        self.assertEqual(topology_lab_menu._current_probe_path(state), [(1, 2, 3, 0)])
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertEqual(state.status, "Selected cell [1, 2, 3, 0]")

    def test_edit_tool_keeps_editor_movement_safe_and_leaves_sandbox_origin_unchanged(self) -> None:
        state = self._explorer_state(2)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        assert state.sandbox is not None
        sandbox_origin = state.sandbox.origin
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)

        topology_lab_menu._apply_probe_step(state, "x+")

        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertNotEqual(topology_lab_menu._current_probe_path(state), [])
        self.assertEqual(state.sandbox.origin, sandbox_origin)

    def test_edit_tool_keeps_editor_probe_selected_and_trace_visible(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)

        self.assertEqual(
            topology_lab_menu._active_workspace_coord(state),
            topology_lab_menu._current_probe_coord(state),
        )
        self.assertEqual(
            topology_lab_menu._active_workspace_path(state),
            topology_lab_menu._current_probe_path(state),
        )

    def test_explorer_entry_defaults_to_scene_pane_and_sandbox_tool(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertEqual(launch.initial_tool, topology_lab_menu.TOOL_SANDBOX)
        self.assertEqual(state.active_tool, launch.initial_tool)

    def test_launcher_entry_defaults_to_scene_pane_and_sandbox_tool(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="launcher",
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertEqual(launch.initial_tool, topology_lab_menu.TOOL_SANDBOX)
        self.assertEqual(state.active_tool, launch.initial_tool)

    def test_explorer_entry_rows_include_adjustable_board_controls(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        row_keys = [row.key for row in topology_lab_menu._rows_for_state(state)]
        self.assertIn("dimension", row_keys)
        self.assertIn("editor_trace", row_keys)
        self.assertIn("editor_probe_neighbors", row_keys)
        self.assertIn("piece_set", row_keys)
        self.assertIn("sandbox_neighbor_search", row_keys)
        self.assertNotIn("board_x", row_keys)
        self.assertNotIn("speed_level", row_keys)
        self.assertNotIn("rigid_play_mode", row_keys)
        self.assertNotIn("explorer_preset", row_keys)

    def test_explorer_entry_dimension_change_updates_canonical_scene_state(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        old_preview_dims = state.scene_preview_dims
        old_boundary_count = len(state.scene_boundaries)
        topology_lab_menu._set_selected_row_by_key(state, "dimension")
        topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
        assert state.canonical_state is not None
        self.assertEqual(state.dimension, 4)
        self.assertEqual(state.canonical_state.dimension, 4)
        self.assertEqual(
            state.scene_preview_dims, topology_lab_menu._board_dims_for_state(state)
        )
        self.assertEqual(state.canonical_state.axis_sizes, state.scene_preview_dims)
        self.assertEqual(len(state.scene_boundaries), 8)
        self.assertNotEqual(state.scene_preview_dims, old_preview_dims)
        self.assertNotEqual(len(state.scene_boundaries), old_boundary_count)

    def test_explorer_entry_board_size_change_updates_canonical_scene_state(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        old_preview_dims = state.scene_preview_dims
        topology_lab_menu._set_selected_row_by_key(state, "board_z")
        topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
        assert state.play_settings is not None
        assert state.canonical_state is not None
        self.assertEqual(state.play_settings.board_dims, state.scene_preview_dims)
        self.assertEqual(
            state.scene_preview_dims, topology_lab_menu._board_dims_for_state(state)
        )
        self.assertEqual(state.canonical_state.axis_sizes, state.scene_preview_dims)
        self.assertEqual(state.scene_preview_dims[2], old_preview_dims[2] + 1)

    def test_repeated_refresh_reuses_cached_preview_for_same_signature(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        cached_preview = state.scene_preview
        cached_signature = state.scene_preview_signature

        with patch.object(
            topology_lab_controls_panel, "compile_explorer_topology_preview"
        ) as compile_preview:
            topology_lab_menu._refresh_explorer_scene_state(state)
            topology_lab_menu._refresh_explorer_scene_state(state)

        compile_preview.assert_not_called()
        self.assertIs(state.scene_preview, cached_preview)
        self.assertEqual(state.scene_preview_signature, cached_signature)

    def test_speed_change_reuses_cached_preview_and_batch_for_same_signature(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        state.experiment_batch = {"experiment_count": 1, "valid_experiment_count": 1}
        cached_batch = state.experiment_batch
        cached_preview = state.scene_preview
        cached_signature = state.scene_preview_signature
        topology_lab_menu._set_selected_row_by_key(state, "speed_level")

        with (
            patch.object(
                topology_lab_controls_panel, "compile_explorer_topology_preview"
            ) as compile_preview,
            patch.object(
                topology_lab_controls_panel, "_refresh_explorer_scene_state"
            ) as refresh_scene,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)

        compile_preview.assert_not_called()
        refresh_scene.assert_not_called()
        assert state.play_settings is not None
        self.assertEqual(
            state.play_settings.speed_level, launch.settings_snapshot.speed_level + 1
        )
        self.assertIs(state.scene_preview, cached_preview)
        self.assertEqual(state.scene_preview_signature, cached_signature)
        self.assertIs(state.experiment_batch, cached_batch)

    def test_piece_set_change_skips_scene_refresh_for_same_signature(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        cached_preview = state.scene_preview
        cached_signature = state.scene_preview_signature
        topology_lab_menu._set_selected_row_by_key(state, "piece_set")

        with (
            patch.object(
                topology_lab_controls_panel, "compile_explorer_topology_preview"
            ) as compile_preview,
            patch.object(
                topology_lab_controls_panel, "_refresh_explorer_scene_state"
            ) as refresh_scene,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)

        compile_preview.assert_not_called()
        refresh_scene.assert_not_called()
        assert state.play_settings is not None
        self.assertEqual(
            state.play_settings.piece_set_index,
            launch.settings_snapshot.piece_set_index + 1,
        )
        self.assertIs(state.scene_preview, cached_preview)
        self.assertEqual(state.scene_preview_signature, cached_signature)

    def test_rigid_play_mode_change_skips_scene_refresh_for_same_signature(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PLAY)
        cached_preview = state.scene_preview
        cached_signature = state.scene_preview_signature
        topology_lab_menu._set_selected_row_by_key(state, "rigid_play_mode")

        with (
            patch.object(
                topology_lab_controls_panel, "compile_explorer_topology_preview"
            ) as compile_preview,
            patch.object(
                topology_lab_controls_panel, "_refresh_explorer_scene_state"
            ) as refresh_scene,
        ):
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)

        compile_preview.assert_not_called()
        refresh_scene.assert_not_called()
        assert state.play_settings is not None
        self.assertEqual(state.play_settings.rigid_play_mode, "on")
        self.assertIs(state.scene_preview, cached_preview)
        self.assertEqual(state.scene_preview_signature, cached_signature)

    def test_run_export_reuses_live_preview_payload_when_signature_matches(
        self,
    ) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )

        with (
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(topology_lab_controls_panel, "play_sfx"),
        ):
            topology_lab_menu._run_export(state)

        self.assertIs(
            export_preview.call_args.kwargs["preview_payload"],
            state.scene_preview,
        )

    def test_run_export_falls_back_when_live_preview_signature_is_stale(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.scene_preview_signature = None

        with (
            patch.object(
                topology_lab_controls_panel,
                "export_explorer_topology_preview",
                return_value=(True, "preview exported", None),
            ) as export_preview,
            patch.object(topology_lab_controls_panel, "play_sfx"),
        ):
            topology_lab_menu._run_export(state)

        self.assertIsNone(export_preview.call_args.kwargs["preview_payload"])

    def test_board_size_change_recompiles_preview_for_new_signature(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        state.experiment_batch = {"experiment_count": 1, "valid_experiment_count": 1}
        old_preview = state.scene_preview
        old_signature = state.scene_preview_signature
        topology_lab_menu._set_selected_row_by_key(state, "board_z")
        refreshed_preview = {
            "movement_graph": {
                "cell_count": 2,
                "directed_edge_count": 1,
                "boundary_traversal_count": 0,
                "component_count": 1,
            },
            "warnings": (),
            "sample_boundary_traversals": (),
            "basis_arrows": (),
        }

        with patch.object(
            topology_lab_controls_panel,
            "compile_explorer_topology_preview",
            return_value=refreshed_preview,
        ) as compile_preview:
            topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)

        compile_preview.assert_called_once()
        self.assertIs(state.scene_preview, refreshed_preview)
        self.assertIsNot(state.scene_preview, old_preview)
        self.assertNotEqual(state.scene_preview_signature, old_signature)
        self.assertEqual(
            state.scene_preview_dims, topology_lab_menu._board_dims_for_state(state)
        )
        self.assertIsNone(state.experiment_batch)

    def test_explorer_entry_preset_change_updates_canonical_scene_state(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        old_profile = self._current_explorer_profile(state)
        old_preset_id = state.canonical_state.preset_metadata.explorer_preset.preset_id
        old_preview = state.scene_preview
        topology_lab_menu._set_selected_row_by_key(state, "explorer_preset")
        topology_lab_menu._dispatch_key(state, pygame.K_RIGHT)
        assert state.canonical_state is not None
        selected_preset = next(
            preset
            for preset in topology_lab_menu._explorer_presets(state)
            if preset.profile == self._current_explorer_profile(state)
        )
        self.assertNotEqual(self._current_explorer_profile(state), old_profile)
        self.assertEqual(
            state.canonical_state.explorer_profile,
            self._current_explorer_profile(state),
        )
        self.assertEqual(
            state.canonical_state.preset_metadata.explorer_preset.preset_id,
            selected_preset.preset_id,
        )
        self.assertEqual(
            state.canonical_state.preset_metadata.explorer_preset.label,
            selected_preset.label,
        )
        self.assertNotEqual(
            state.canonical_state.preset_metadata.explorer_preset.preset_id,
            old_preset_id,
        )
        self.assertEqual(
            topology_lab_menu._explorer_preset_value_text(state), selected_preset.label
        )
        self.assertTrue(
            state.scene_preview is not None or state.scene_preview_error is not None
        )
        if state.scene_preview is not None:
            self.assertIsNot(state.scene_preview, old_preview)
        else:
            self.assertIsNotNone(state.scene_preview_error)
        self.assertEqual(
            set(state.scene_active_glue_ids),
            {boundary.label for boundary in state.scene_boundaries},
        )

    def test_explorer_entry_mouse_minus_adjusts_board_size(self) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()
        screen = pygame.Surface((1280, 900))
        fonts = SimpleNamespace(
            title_font=pygame.font.Font(None, 36),
            menu_font=pygame.font.Font(None, 28),
            hint_font=pygame.font.Font(None, 22),
        )
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        state.active_pane = topology_lab_menu.PANE_CONTROLS
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        initial_dims = topology_lab_menu._board_dims_for_state(state)
        topology_lab_menu._draw_menu(screen, fonts, state)
        minus_target = next(
            target
            for target in state.mouse_targets
            if target.kind == "row_step" and target.value == ("board_z", -1)
        )
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, minus_target.rect.center, 1)
        self.assertEqual(
            topology_lab_menu._board_dims_for_state(state),
            (initial_dims[0], initial_dims[1], initial_dims[2] - 1),
        )

    def test_explorer_entry_3d_starts_with_scene_camera(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=topology_lab_menu.TOOL_NAVIGATE,
            play_settings=launch.settings_snapshot,
        )
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertIsNotNone(state.scene_camera)

    def test_explorer_entry_4d_starts_with_scene_camera(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=4, entry_source="explorer"
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=topology_lab_menu.TOOL_NAVIGATE,
            play_settings=launch.settings_snapshot,
        )
        self.assertEqual(state.active_pane, topology_lab_menu.PANE_SCENE)
        self.assertIsNotNone(state.scene_camera)

    def test_run_explorer_playground_uses_explicit_launch_contract(self) -> None:
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            explorer_profile=ExplorerTopologyProfile(dimension=3, gluings=()),
            entry_source="explorer",
        )
        with patch.object(
            topology_lab_menu,
            "_run_playground_shell",
            return_value=(True, "ok"),
        ) as run_shell:
            topology_lab_menu.run_explorer_playground(
                object(),
                object(),
                launch=launch,
            )
        self.assertIs(run_shell.call_args.kwargs["resolved_launch"], launch)
        self.assertEqual(
            run_shell.call_args.kwargs["display_settings"], launch.display_settings
        )
        self.assertEqual(run_shell.call_args.kwargs["fonts_2d"], launch.fonts_2d)

    def test_run_explorer_playground_builds_explorer_launch_when_needed(self) -> None:
        with (
            patch.object(
                topology_lab_menu,
                "build_explorer_playground_launch",
                wraps=topology_lab_menu.build_explorer_playground_launch,
            ) as build_launch,
            patch.object(
                topology_lab_menu,
                "_run_playground_shell",
                return_value=(True, "ok"),
            ) as run_shell,
        ):
            topology_lab_menu.run_explorer_playground(
                object(),
                object(),
                dimension=3,
            )
        build_launch.assert_called_once()
        self.assertEqual(build_launch.call_args.kwargs["dimension"], 3)
        self.assertEqual(build_launch.call_args.kwargs["entry_source"], "explorer")
        launch = run_shell.call_args.kwargs["resolved_launch"]
        self.assertEqual(launch.dimension, 3)
        self.assertEqual(launch.entry_source, "explorer")
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_EXPLORER)

    def test_workspace_preview_lines_include_hover_and_selected_glue(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        topology_lab_controls_panel.set_selected_boundary_index(state, 1)
        state.hovered_boundary_index = 4
        topology_lab_controls_panel.set_selected_glue_id(state, "glue_001")
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={
                "movement_graph": {
                    "cell_count": 1,
                    "directed_edge_count": 0,
                    "boundary_traversal_count": 0,
                    "component_count": 1,
                },
                "warnings": (),
                "sample_boundary_traversals": (),
            },
            preview_error=None,
        )
        self.assertIn("Selected boundary: x+", lines)
        self.assertIn("Hover boundary: z-", lines)
        self.assertIn("Selected seam: glue_001", lines)
        self.assertIn("Workspace: Editor", lines)
        self.assertIn("Tool focus: Probe tool", lines)

    def test_workspace_preview_lines_fall_back_to_hovered_glue(self) -> None:
        state = self._explorer_state(3)
        state.hovered_glue_id = "glue_hover"
        topology_lab_controls_panel.set_selected_glue_id(state, None)
        lines = topology_lab_menu._workspace_preview_lines(
            state,
            preview={
                "movement_graph": {
                    "cell_count": 1,
                    "directed_edge_count": 0,
                    "boundary_traversal_count": 0,
                    "component_count": 1,
                },
                "warnings": (),
                "sample_boundary_traversals": (),
            },
            preview_error=None,
        )
        self.assertIn("Hover seam: glue_hover", lines)

    def test_hint_lines_do_not_expose_camera_in_2d(self) -> None:
        state = self._explorer_state(2)
        lines = topology_lab_menu._hint_lines_for_state(state)
        self.assertFalse(any("synced" in line for line in lines))

    def test_sync_explorer_state_populates_canonical_scene_snapshot(self) -> None:
        state = topology_lab_menu._TopologyLabState(
            selected=0,
            gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            dimension=3,
            profile=default_topology_profile_state(
                dimension=3,
                gravity_axis=1,
                gameplay_mode=GAMEPLAY_MODE_EXPLORER,
            ),
        )
        profile = ExplorerTopologyProfile(dimension=3, gluings=())
        with patch.object(
            topology_lab_controls_panel,
            "load_runtime_explorer_topology_profile",
            return_value=profile,
        ):
            topology_lab_menu._sync_explorer_state(state)
        self.assertEqual(
            state.scene_boundaries, topology_lab_menu.boundaries_for_dimension(3)
        )
        self.assertEqual(
            state.scene_preview_dims, topology_lab_menu._board_dims_for_state(state)
        )
        self.assertEqual(state.scene_active_glue_ids.get("x-"), "free")
        self.assertIs(self._current_explorer_profile(state), profile)
        self.assertIsNotNone(state.scene_preview)
        self.assertEqual(
            state.scene_basis_arrows,
            tuple((state.scene_preview or {}).get("basis_arrows", ())),
        )

    def test_apply_explorer_glue_updates_canonical_scene_snapshot(self) -> None:
        state = self._explorer_state(3)
        topology_lab_menu._refresh_explorer_scene_state(state)
        self.assertEqual(state.scene_active_glue_ids.get("x-"), "free")
        topology_lab_menu._apply_explorer_glue(state)
        selected_glue_id = topology_lab_scene_state.current_selected_glue_id(state)
        self.assertEqual(state.scene_active_glue_ids.get("x-"), selected_glue_id)
        self.assertEqual(state.scene_active_glue_ids.get("x+"), selected_glue_id)

    def test_apply_explorer_glue_keeps_invalid_bijection_as_explicit_scene_error(
        self,
    ) -> None:
        state = self._explorer_state(3)
        topology_lab_controls_panel.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(board_dims=(4, 5, 6)),
        )
        topology_lab_menu._refresh_explorer_scene_state(state)

        topology_lab_menu._update_explorer_draft(
            state,
            source_index=0,
            target_index=5,
            permutation_index=0,
            signs=(1, 1),
        )
        topology_lab_menu._apply_explorer_glue(state)

        self.assertEqual(len(self._current_explorer_profile(state).gluings), 1)
        assert state.canonical_state is not None
        self.assertEqual(
            state.canonical_state.explorer_profile,
            self._current_explorer_profile(state),
        )
        self.assertIsNone(state.scene_preview)
        self.assertIsNotNone(state.scene_preview_error)
        self.assertIn(
            "unsupported for current board dimensions",
            state.scene_preview_error,
        )
        glue_id = self._current_explorer_profile(state).gluings[0].glue_id
        self.assertEqual(state.scene_active_glue_ids.get("x-"), glue_id)
        self.assertEqual(state.scene_active_glue_ids.get("z+"), glue_id)
        self.assertTrue(state.status_error)
        self.assertIn("unsupported for current board dimensions", state.status)

    def test_glue_pick_normalizes_and_syncs_canonical_draft(self) -> None:
        state = self._explorer_state(3)
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=2, side="+"),
            transform=BoundaryTransform(permutation=(1, 0), signs=(-1, 1)),
        )
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            ExplorerTopologyProfile(dimension=3, gluings=(glue,)),
        )
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="glue_pick",
                value=glue.glue_id,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]

        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)

        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.selected_gluing, glue.glue_id)
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.permutation,
            glue.transform.permutation,
        )
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.signs,
            glue.transform.signs,
        )

    def test_glue_slot_pick_syncs_canonical_selected_seam(self) -> None:
        state = self._explorer_state(3)
        first_glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=0, side="+"),
            transform=BoundaryTransform(permutation=(0, 1), signs=(1, 1)),
        )
        second_glue = GluingDescriptor(
            glue_id="glue_002",
            source=BoundaryRef(dimension=3, axis=1, side="-"),
            target=BoundaryRef(dimension=3, axis=2, side="+"),
            transform=BoundaryTransform(permutation=(1, 0), signs=(1, -1)),
        )
        topology_lab_controls_panel.replace_explorer_profile(
            state,
            ExplorerTopologyProfile(
                dimension=3,
                gluings=(first_glue, second_glue),
            ),
        )
        topology_lab_menu._normalize_explorer_draft(state)
        target = topology_lab_menu.TopologyLabHitTarget(
            kind="glue_slot",
            value=1,
            rect=pygame.Rect(0, 0, 40, 40),
        )

        handled = topology_lab_menu._dispatch_mouse_target(state, target, 1)

        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_scene_state.current_selected_glue_id(state),
            second_glue.glue_id,
        )
        self.assertEqual(
            topology_lab_scene_state.current_highlighted_glue_id(state),
            second_glue.glue_id,
        )
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.selected_gluing, second_glue.glue_id)
        self.assertEqual(
            state.canonical_state.selected_boundary,
            second_glue.source,
        )
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.permutation,
            second_glue.transform.permutation,
        )
        self.assertEqual(
            state.canonical_state.topology_config.gluing_draft.signs,
            second_glue.transform.signs,
        )

    def test_right_click_existing_glue_selects_clicked_boundary_in_canonical_state(
        self,
    ) -> None:
        state = self._explorer_state(3)
        glue = GluingDescriptor(
            glue_id="glue_001",
            source=BoundaryRef(dimension=3, axis=0, side="-"),
            target=BoundaryRef(dimension=3, axis=2, side="+"),
            transform=BoundaryTransform(permutation=(1, 0), signs=(1, 1)),
        )
        state.explorer_profile = ExplorerTopologyProfile(dimension=3, gluings=(glue,))
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_PROBE)
        topology_lab_menu._sync_canonical_playground_state(state)
        target = topology_lab_menu.TopologyLabHitTarget(
            kind="boundary_pick",
            value=5,
            rect=pygame.Rect(0, 0, 40, 40),
        )

        handled = topology_lab_menu._handle_mouse_boundary_target(state, target, 3)

        self.assertTrue(handled)
        self.assertEqual(
            topology_lab_scene_state.current_selected_boundary_index(state),
            5,
        )
        self.assertIsNone(topology_lab_scene_state.current_selected_glue_id(state))
        assert state.canonical_state is not None
        self.assertEqual(state.canonical_state.selected_boundary, glue.target)
        self.assertIsNone(state.canonical_state.selected_gluing)

    def test_draw_workspace_uses_canonical_scene_snapshot(self) -> None:
        screen = pygame.Surface((1280, 900))
        fonts = self._fonts()
        state = self._explorer_state(3)
        state.scene_boundaries = topology_lab_menu.boundaries_for_dimension(3)
        state.scene_preview_dims = (11, 12, 13)
        state.scene_active_glue_ids = {
            boundary.label: ("glue_001" if boundary.label in {"x-", "x+"} else "free")
            for boundary in state.scene_boundaries
        }
        state.scene_basis_arrows = (
            {"crossing": "x- -> x+", "basis_pairs": ({"from": "y", "to": "y"},)},
        )
        state.scene_preview = {
            "movement_graph": {
                "cell_count": 1,
                "directed_edge_count": 0,
                "boundary_traversal_count": 0,
                "component_count": 1,
            },
            "warnings": (),
            "sample_boundary_traversals": (),
            "basis_arrows": state.scene_basis_arrows,
        }
        state.scene_preview_error = None
        with (
            patch.object(
                topology_lab_controls_panel, "compile_explorer_topology_preview"
            ) as compile_preview,
            patch.object(topology_lab_workspace_shell, "draw_tool_ribbon", return_value=[]),
            patch.object(
                topology_lab_workspace_shell, "_draw_explorer_scene", return_value=[]
            ) as draw_scene,
            patch.object(topology_lab_workspace_shell, "draw_transform_editor", return_value=[]),
            patch.object(topology_lab_workspace_shell, "draw_preview_panel") as draw_preview,
            patch.object(
                topology_lab_menu, "_draw_probe_controls_if_needed", return_value=[]
            ),
        ):
            topology_lab_menu._draw_explorer_workspace(
                screen,
                fonts,
                state,
                panel_x=40,
                panel_y=160,
                panel_w=1040,
                panel_h=620,
                menu_w=460,
                analysis_pane_title=topology_lab_menu._ANALYSIS_PANE_TITLE,
                scene_pane_title=topology_lab_menu._SCENE_PANE_TITLE,
                text_color=topology_lab_menu._TEXT_COLOR,
                muted_color=topology_lab_menu._MUTED_COLOR,
                highlight_color=topology_lab_menu._HIGHLIGHT_COLOR,
            )
        compile_preview.assert_not_called()
        kwargs = draw_scene.call_args.kwargs
        self.assertEqual(kwargs["preview_dims"], state.scene_preview_dims)
        self.assertEqual(kwargs["active_glue_ids"], state.scene_active_glue_ids)
        self.assertEqual(kwargs["basis_arrows"], list(state.scene_basis_arrows))
        preview_kwargs = draw_preview.call_args.kwargs
        self.assertEqual(preview_kwargs["title"], "Keys")
        self.assertTrue(preview_kwargs["lines"])
        self.assertIn(preview_kwargs["lines"][0], {"Edit", "Probe", "Play"})
        self.assertTrue(
            all(
                line.startswith(("Move ", "Turn ", "     "))
                or line in {"Edit", "Probe", "Play"}
                for line in preview_kwargs["lines"]
            )
        )
        self.assertFalse(
            any("Selected boundary:" in line for line in preview_kwargs["lines"])
        )
        self.assertFalse(
            any("Workspace:" in line for line in preview_kwargs["lines"])
        )

    def test_explorer_entry_scene_glue_path_creates_draft_and_enters_edit(self) -> None:
        profile = ExplorerTopologyProfile(dimension=3, gluings=())
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="explorer",
            explorer_profile=profile,
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=0,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertEqual(state.pending_source_index, 0)
        self.assertEqual(
            topology_lab_scene_state.current_selected_boundary_index(state),
            0,
        )

        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=1,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        current_draft = self._current_explorer_draft(state)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertIsNone(state.pending_source_index)
        self.assertEqual(current_draft.source_index, 0)
        self.assertEqual(current_draft.target_index, 1)
        self.assertTrue(state.running)

    def test_explorer_entry_scene_glue_path_edits_transform_and_applies_without_exit(
        self,
    ) -> None:
        profile = ExplorerTopologyProfile(dimension=3, gluings=())
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=3,
            entry_source="explorer",
            explorer_profile=profile,
        )
        state = topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )
        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_EDIT)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=0,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="boundary_pick",
                value=1,
                rect=pygame.Rect(0, 0, 40, 40),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        current_draft = self._current_explorer_draft(state)
        original_permutation = current_draft.permutation_index
        original_signs = current_draft.signs
        valid_permutation = 0

        if original_permutation != valid_permutation:
            state.mouse_targets = [
                topology_lab_menu.TopologyLabHitTarget(
                    kind="perm_select",
                    value=valid_permutation,
                    rect=pygame.Rect(0, 0, 60, 28),
                )
            ]
            with patch.object(topology_lab_menu, "play_sfx"):
                topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
            self.assertEqual(
                self._current_explorer_draft(state).permutation_index,
                valid_permutation,
            )

        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="sign_toggle",
                value=0,
                rect=pygame.Rect(0, 0, 60, 28),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertNotEqual(self._current_explorer_draft(state).signs, original_signs)

        state.mouse_targets = [
            topology_lab_menu.TopologyLabHitTarget(
                kind="action",
                value="apply_glue",
                rect=pygame.Rect(0, 0, 80, 28),
            )
        ]
        with patch.object(topology_lab_menu, "play_sfx"):
            topology_lab_menu._handle_mouse_down(state, (5, 5), 1)
        self.assertEqual(len(self._current_explorer_profile(state).gluings), 1)
        self.assertIsNotNone(topology_lab_scene_state.current_selected_glue_id(state))
        self.assertEqual(state.active_tool, topology_lab_menu.TOOL_EDIT)
        self.assertTrue(state.running)

if __name__ == "__main__":
    unittest.main()
