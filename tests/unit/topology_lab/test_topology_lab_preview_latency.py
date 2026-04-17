from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pygame

from tet4d.engine.runtime.topology_playground_state import (
    PLAYABILITY_STATUS_ANALYZING,
    PLAYABILITY_STATUS_PLAYABLE,
    TopologyPlaygroundPlayabilityAnalysis,
)
from tet4d.engine.topology_explorer.presets import sphere_profile_2d
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.topology_lab import controls_panel as topology_lab_controls_panel
from tet4d.ui.pygame.topology_lab import scene_preview_state as topology_lab_scene_preview_state
from tet4d.ui.pygame.topology_lab import scene_state as topology_lab_scene_state


class TestTopologyLabPreviewLatency(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def _state(self, dimension: int = 3):
        launch = topology_lab_menu.build_explorer_playground_launch(
            dimension=dimension,
            entry_source="explorer",
        )
        return topology_lab_menu._initial_topology_lab_state(
            launch.dimension,
            gameplay_mode=launch.gameplay_mode,
            initial_explorer_profile=launch.explorer_profile,
            initial_tool=launch.initial_tool,
            play_settings=launch.settings_snapshot,
        )

    def _playable_analysis(
        self,
        *,
        summary: str = "cached playability",
    ) -> TopologyPlaygroundPlayabilityAnalysis:
        return TopologyPlaygroundPlayabilityAnalysis(
            status=PLAYABILITY_STATUS_PLAYABLE,
            validity="valid",
            explorer_usability="cellwise_explorable",
            rigid_playability="rigid_playable",
            summary=summary,
        )

    def _fake_update(self, calls: list[bool]):
        def _impl(runtime_state, **kwargs):
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
                    "rigid-ready analysis"
                    if include_rigid_scan
                    else "rigid-pending analysis"
                ),
            )
            runtime_state.playability_analysis = analysis
            return analysis

        return _impl

    def test_preview_signature_ignores_non_topological_settings_and_ui_state(
        self,
    ) -> None:
        state = self._state(2)
        baseline = topology_lab_scene_preview_state.preview_signature_for_state(state)
        settings = topology_lab_scene_state.current_play_settings(state)
        assert baseline is not None
        assert settings is not None

        topology_lab_scene_state.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=settings.board_dims,
                piece_set_index=settings.piece_set_index + 1,
                speed_level=settings.speed_level + 1,
                random_mode_index=settings.random_mode_index + 1,
                game_seed=settings.game_seed + 99,
                rigid_play_mode="on",
            ),
        )
        self.assertEqual(
            topology_lab_scene_preview_state.preview_signature_for_state(state),
            baseline,
        )

        topology_lab_scene_state.set_probe_trace_visible(state, False)
        topology_lab_scene_state.set_probe_neighbors_visible(state, True)
        topology_lab_scene_state.select_projection_coord(state, (1, 1))
        self.assertEqual(
            topology_lab_scene_preview_state.preview_signature_for_state(state),
            baseline,
        )

        topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
        topology_lab_menu.ensure_piece_sandbox(state)
        profile = topology_lab_scene_state.current_explorer_profile(state)
        assert profile is not None
        ok, message = topology_lab_menu.move_sandbox_piece(state, profile, "x+")
        self.assertTrue(ok, message)
        self.assertEqual(
            topology_lab_scene_preview_state.preview_signature_for_state(state),
            baseline,
        )

    def test_preview_signature_changes_for_board_dims_and_topology_edits(self) -> None:
        state = self._state(3)
        baseline = topology_lab_scene_preview_state.preview_signature_for_state(state)
        settings = topology_lab_scene_state.current_play_settings(state)
        assert baseline is not None
        assert settings is not None

        topology_lab_scene_state.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=(
                    settings.board_dims[0],
                    settings.board_dims[1],
                    settings.board_dims[2] + 1,
                ),
                piece_set_index=settings.piece_set_index,
                speed_level=settings.speed_level,
                random_mode_index=settings.random_mode_index,
                game_seed=settings.game_seed,
                rigid_play_mode=settings.rigid_play_mode,
            ),
        )
        resized = topology_lab_scene_preview_state.preview_signature_for_state(state)
        self.assertNotEqual(resized, baseline)

        current_profile = topology_lab_scene_state.current_explorer_profile(state)
        next_profile = next(
            preset.profile
            for preset in topology_lab_controls_panel._explorer_presets(state)
            if preset.profile != current_profile
        )
        topology_lab_scene_state.replace_explorer_profile(state, next_profile)
        self.assertNotEqual(
            topology_lab_scene_preview_state.preview_signature_for_state(state),
            resized,
        )

    def test_invalid_preview_does_not_queue_deferred_rigid_analysis(self) -> None:
        state = self._state(2)
        settings = topology_lab_scene_state.current_play_settings(state)
        assert settings is not None
        topology_lab_scene_state.replace_explorer_profile(state, sphere_profile_2d())
        topology_lab_scene_state.replace_play_settings(
            state,
            topology_lab_menu.ExplorerPlaygroundSettings(
                board_dims=(5, 4),
                piece_set_index=settings.piece_set_index,
                speed_level=settings.speed_level,
                random_mode_index=settings.random_mode_index,
                game_seed=settings.game_seed,
                rigid_play_mode=settings.rigid_play_mode,
            ),
        )

        with (
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                side_effect=AssertionError(
                    "invalid preview should not read rigid-playability cache"
                ),
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                wraps=topology_lab_scene_preview_state.update_topology_playability_analysis,
            ) as update_analysis,
        ):
            topology_lab_scene_preview_state.refresh_explorer_scene_state(state)
            self.assertIsNotNone(state.scene_preview_error)
            self.assertIsNone(state.scene_pending_playability_signature)
            self.assertEqual(
                [bool(call.kwargs["include_rigid_scan"]) for call in update_analysis.call_args_list],
                [False],
            )

            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            self.assertEqual(
                [bool(call.kwargs["include_rigid_scan"]) for call in update_analysis.call_args_list],
                [False],
            )

    def test_matching_persistent_cache_is_restored_without_full_scan(self) -> None:
        analysis = self._playable_analysis(summary="persistent cached playability")

        with (
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                return_value=analysis,
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=AssertionError(
                    "matching persistent cache should avoid recompute"
                ),
            ),
        ):
            state = self._state(2)

        runtime_state = topology_lab_scene_state.canonical_playground_state(state)
        assert runtime_state is not None
        self.assertEqual(
            runtime_state.playability_analysis.status,
            PLAYABILITY_STATUS_PLAYABLE,
        )
        self.assertEqual(runtime_state.playability_analysis.summary, analysis.summary)
        self.assertIsNone(state.scene_pending_playability_signature)
        self.assertIsNotNone(state.scene_playability_cache)

    def test_ui_only_probe_and_sandbox_changes_reuse_cached_full_analysis(
        self,
    ) -> None:
        calls: list[bool] = []
        with (
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=self._fake_update(calls),
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                return_value=None,
            ),
        ):
            state = self._state(2)
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            baseline = state.scene_preview_signature

            topology_lab_scene_state.set_probe_trace_visible(state, False)
            topology_lab_scene_state.set_probe_neighbors_visible(state, True)
            topology_lab_scene_state.select_projection_coord(state, (1, 1))
            topology_lab_menu.set_active_tool(state, topology_lab_menu.TOOL_SANDBOX)
            topology_lab_menu.ensure_piece_sandbox(state)
            profile = topology_lab_scene_state.current_explorer_profile(state)
            assert profile is not None
            ok, message = topology_lab_menu.move_sandbox_piece(state, profile, "x+")
            self.assertTrue(ok, message)

            with patch.object(
                topology_lab_controls_panel,
                "compile_explorer_topology_preview",
                side_effect=AssertionError(
                    "ui-only state change should not force preview recompile"
                ),
            ):
                topology_lab_scene_preview_state.refresh_explorer_scene_state(state)

        self.assertEqual(calls, [False, True])
        self.assertEqual(state.scene_preview_signature, baseline)

    def test_signature_change_invalidates_full_analysis_and_restarts_pending_path(
        self,
    ) -> None:
        calls: list[bool] = []
        with (
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=self._fake_update(calls),
            ),
            patch.object(
                topology_lab_scene_preview_state,
                "read_cached_playability_analysis",
                return_value=None,
            ),
        ):
            state = self._state(3)
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            topology_lab_scene_preview_state.advance_pending_explorer_playability_analysis(
                state
            )
            previous_signature = state.scene_preview_signature
            self.assertIsNotNone(state.scene_playability_cache)

            settings = topology_lab_scene_state.current_play_settings(state)
            assert settings is not None
            topology_lab_scene_state.replace_play_settings(
                state,
                topology_lab_menu.ExplorerPlaygroundSettings(
                    board_dims=(
                        settings.board_dims[0],
                        settings.board_dims[1],
                        settings.board_dims[2] + 1,
                    ),
                    piece_set_index=settings.piece_set_index,
                    speed_level=settings.speed_level,
                    random_mode_index=settings.random_mode_index,
                    game_seed=settings.game_seed,
                    rigid_play_mode=settings.rigid_play_mode,
                ),
            )
            topology_lab_scene_preview_state.refresh_explorer_scene_state(state)

        self.assertEqual(calls, [False, True, False])
        self.assertNotEqual(state.scene_preview_signature, previous_signature)
        self.assertIsNone(state.scene_playability_cache)
        self.assertEqual(
            state.scene_pending_playability_signature,
            state.scene_preview_signature,
        )

    def test_repeat_play_launch_reuses_completed_full_analysis(self) -> None:
        calls: list[bool] = []
        screen = pygame.Surface((32, 32))

        with (
            patch.object(
                topology_lab_scene_preview_state,
                "update_topology_playability_analysis",
                side_effect=self._fake_update(calls),
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
            state = self._state(2)
            topology_lab_controls_panel._launch_play_preview(
                state,
                screen,
                SimpleNamespace(),
            )
            topology_lab_controls_panel._launch_play_preview(
                state,
                screen,
                SimpleNamespace(),
            )

        self.assertEqual(calls, [False, True])
        self.assertEqual(launch_gameplay.call_count, 2)


if __name__ == "__main__":
    unittest.main()
