from __future__ import annotations

import unittest
import io
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pygame

from cli import front
from tet4d.engine.gameplay.topology_designer import (
    GAMEPLAY_MODE_EXPLORER,
    GAMEPLAY_MODE_NORMAL,
)
from tet4d.engine.topology_explorer import ExplorerTopologyProfile
from tet4d.ui.pygame.launch import topology_lab_menu
from tet4d.ui.pygame.menu.menu_runner import ActionRegistry
from tet4d.ui.pygame.topology_lab import entrypoint as topology_lab_entrypoint


class TestFrontLauncherRoutes(unittest.TestCase):
    def test_parse_topology_playground_cli_defaults_dimension_when_flag_has_no_value(
        self,
    ) -> None:
        args = front._parse_cli_args(["--topology-playground"])

        self.assertEqual(args.topology_playground, "2")

    def test_parse_topology_playground_dimension_accepts_supported_values(self) -> None:
        self.assertEqual(topology_lab_entrypoint.parse_topology_playground_dimension("2"), 2)
        self.assertEqual(topology_lab_entrypoint.parse_topology_playground_dimension("3"), 3)
        self.assertEqual(topology_lab_entrypoint.parse_topology_playground_dimension("4"), 4)

    def test_parse_topology_playground_dimension_rejects_invalid_values_cleanly(
        self,
    ) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), self.assertRaises(SystemExit) as raised:
            topology_lab_entrypoint.parse_topology_playground_dimension("foo")
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Unsupported dimension: foo. Use 2, 3, or 4.", buffer.getvalue())

    def test_parse_topology_playground_dimension_rejects_unsupported_numbers_cleanly(
        self,
    ) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer), self.assertRaises(SystemExit) as raised:
            topology_lab_entrypoint.parse_topology_playground_dimension("5")
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("Unsupported dimension: 5. Use 2, 3, or 4.", buffer.getvalue())

    def test_main_can_launch_topology_playground_directly_from_cli_option(self) -> None:
        with patch.object(front, "run_direct_topology_playground") as run_direct:
            front.main(["--topology-playground", "3"])

        run_direct.assert_called_once_with(3)

    def _run_live_topology_lab_launcher_action(
        self,
        *,
        mode: str,
        payload: dict[str, object],
    ) -> tuple[object, topology_lab_menu._TopologyLabState]:
        state = front.MainMenuState(last_mode=mode)
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        captured: dict[str, object] = {}

        def _run_live_entry(_screen, _fonts, *, launch):
            live_state = topology_lab_menu._initial_topology_lab_state(
                launch.dimension,
                gameplay_mode=launch.gameplay_mode,
                initial_explorer_profile=launch.explorer_profile,
                initial_tool=launch.initial_tool,
                play_settings=launch.settings_snapshot,
            )
            captured["launch"] = launch
            captured["state"] = live_state
            return True, "Explorer playground saved"

        with (
            patch.object(front, "_persist_session_status"),
            patch(
                "tet4d.ui.pygame.topology_lab.app.load_app_settings_payload",
                return_value=payload,
            ),
            patch.object(
                front,
                "load_runtime_explorer_topology_profile",
                return_value=ExplorerTopologyProfile(dimension=int(mode[0]), gluings=()),
            ),
            patch.object(
                front,
                "run_explorer_playground",
                side_effect=_run_live_entry,
            ),
        ):
            closed = front._menu_action_topology_lab(
                state,
                session,
                object(),
            )

        self.assertFalse(closed)
        return captured["launch"], captured["state"]

    def test_topology_lab_action_updates_status(self) -> None:
        state = front.MainMenuState(last_mode="3d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with (
            patch.object(front, "_persist_session_status"),
            patch.object(front, "_mode_settings_snapshot", return_value=SimpleNamespace()),
            patch.object(
                front,
                "load_runtime_explorer_topology_profile",
                return_value=ExplorerTopologyProfile(dimension=3, gluings=()),
            ),
            patch.object(
                front,
                "run_explorer_playground",
                return_value=(True, "Explorer playground saved"),
            ) as run_playground,
        ):
            close = front._menu_action_topology_lab(
                state,
                session,
                object(),
            )

        self.assertFalse(close)
        self.assertEqual(state.status, "Explorer playground saved")
        self.assertFalse(state.status_error)
        run_playground.assert_called_once()
        launch = run_playground.call_args.kwargs["launch"]
        self.assertEqual(launch.dimension, 3)
        self.assertEqual(launch.entry_source, "launcher")
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_EXPLORER)

    def test_legacy_topology_editor_action_is_settings_only_legacy_launch(self) -> None:
        state = front.MainMenuState(last_mode="4d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with (
            patch.object(front, "_persist_session_status"),
            patch.object(
                front,
                "run_explorer_playground",
                return_value=(True, "Legacy topology editor closed"),
            ) as run_playground,
        ):
            close = front._menu_action_legacy_topology_editor(
                state,
                session,
                object(),
            )

        self.assertFalse(close)
        self.assertEqual(state.status, "Legacy topology editor closed")
        self.assertFalse(state.status_error)
        run_playground.assert_called_once()
        launch = run_playground.call_args.kwargs["launch"]
        self.assertEqual(launch.dimension, 4)
        self.assertEqual(launch.entry_source, "launcher")
        self.assertEqual(launch.gameplay_mode, GAMEPLAY_MODE_NORMAL)

    def test_topology_lab_launcher_entry_uses_explorer_config_dims_in_live_state(
        self,
    ) -> None:
        launch, live_state = self._run_live_topology_lab_launcher_action(
            mode="3d",
            payload={
                "settings": {
                    "3d": {
                        "width": 7,
                        "height": 19,
                        "depth": 7,
                    }
                }
            },
        )

        self.assertEqual(launch.settings_snapshot.board_dims, (8, 8, 8))
        assert live_state.play_settings is not None
        self.assertEqual(live_state.play_settings.board_dims, (8, 8, 8))
        self.assertEqual(
            topology_lab_menu._board_dims_for_state(live_state),
            (8, 8, 8),
        )
        self.assertEqual(live_state.scene_preview_dims, (8, 8, 8))
        assert live_state.canonical_state is not None
        self.assertEqual(live_state.canonical_state.axis_sizes, (8, 8, 8))

    def test_topology_lab_launcher_probe_footer_steps_reach_true_board_edge(
        self,
    ) -> None:
        _launch, live_state = self._run_live_topology_lab_launcher_action(
            mode="3d",
            payload={
                "settings": {
                    "3d": {
                        "width": 7,
                        "height": 19,
                        "depth": 7,
                    }
                }
            },
        )
        topology_lab_menu.set_active_tool(live_state, topology_lab_menu.TOOL_PROBE)
        live_state.active_pane = topology_lab_menu.PANE_SCENE

        selected = topology_lab_menu._dispatch_mouse_target(
            live_state,
            topology_lab_menu.TopologyLabHitTarget(
                kind="projection_cell",
                value=(0, 0, 0),
                rect=pygame.Rect(0, 0, 20, 20),
            ),
            1,
        )

        self.assertTrue(selected)
        self.assertEqual(topology_lab_menu._current_probe_coord(live_state), (0, 0, 0))
        for _ in range(7):
            handled = topology_lab_menu._dispatch_mouse_target(
                live_state,
                topology_lab_menu.TopologyLabHitTarget(
                    kind="probe_step",
                    value="x+",
                    rect=pygame.Rect(0, 0, 20, 20),
                ),
                1,
            )
            self.assertTrue(handled)

        self.assertEqual(topology_lab_menu._current_probe_coord(live_state), (7, 0, 0))
        assert live_state.canonical_state is not None
        self.assertEqual(live_state.canonical_state.probe_state.coord, (7, 0, 0))

        topology_lab_menu._dispatch_mouse_target(
            live_state,
            topology_lab_menu.TopologyLabHitTarget(
                kind="probe_step",
                value="x+",
                rect=pygame.Rect(0, 0, 20, 20),
            ),
            1,
        )

        self.assertEqual(topology_lab_menu._current_probe_coord(live_state), (7, 0, 0))
        self.assertTrue(live_state.status_error)
        self.assertIn("blocked", live_state.status)

    def test_play_last_custom_topology_uses_direct_playground_launch(self) -> None:
        state = front.MainMenuState(last_mode="3d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        launch = SimpleNamespace(
            dimension=3,
            startup_notice=None,
            explorer_profile=object(),
            settings_snapshot=object(),
        )

        with (
            patch.object(front, "_persist_session_status"),
            patch.object(front, "_mode_settings_snapshot", return_value=SimpleNamespace()),
            patch.object(front, "load_runtime_explorer_topology_profile", return_value=object()),
            patch.object(front, "build_explorer_playground_launch", return_value=launch),
            patch.object(front, "build_explorer_playground_config", return_value=object()),
            patch.object(front, "open_display", side_effect=lambda display_settings, caption=None: object()),
            patch.object(front, "capture_windowed_display_settings", side_effect=lambda display_settings: display_settings),
            patch("tet4d.ui.pygame.front3d_game.run_game_loop", return_value=True) as run_loop,
        ):
            close = front._menu_action_play_last_custom_topology(
                state,
                session,
                object(),
                object(),
            )

        self.assertFalse(close)
        self.assertFalse(state.status_error)
        run_loop.assert_called_once()

    def test_non_tutorial_route_uses_registry_dispatch(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        registry = ActionRegistry()
        handler = Mock(return_value=False)
        registry.register("help", handler)

        with patch.dict(front._LAUNCHER_ROUTE_ACTIONS, {"custom_route": "help"}, clear=False):
            close = front._handle_launcher_route(
                "custom_route",
                state,
                registry,
                session,
                fonts_nd=object(),
                fonts_2d=object(),
            )

        self.assertFalse(close)
        handler.assert_called_once()

    def test_tutorial_action_launches_lesson(self) -> None:
        state = front.MainMenuState(last_mode="3d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with (
            patch.object(
                front,
                "tutorial_lesson_ids_runtime",
                return_value=(
                    "tutorial_2d_core",
                    "tutorial_3d_core",
                    "tutorial_4d_core",
                ),
            ),
            patch.object(front, "_launch_mode") as launch_mode,
        ):
            close = front._menu_action_tutorial_dimension(
                "2d",
                state,
                session,
                fonts_nd=object(),
                fonts_2d=object(),
            )

        self.assertFalse(close)
        launch_mode.assert_called_once()

    def test_unknown_route_sets_error_status(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        session = SimpleNamespace(
            screen=object(),
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )
        registry = ActionRegistry()

        close = front._handle_launcher_route(
            "missing_route",
            state,
            registry,
            session,
            fonts_nd=object(),
            fonts_2d=object(),
        )

        self.assertFalse(close)
        self.assertTrue(state.status_error)
        self.assertIn("No action mapped", state.status)

    def test_leaderboard_action_opens_menu(self) -> None:
        state = front.MainMenuState(last_mode="2d")
        screen = object()
        session = SimpleNamespace(
            screen=screen,
            display_settings=object(),
            audio_settings=object(),
            running=True,
        )

        with patch.object(front, "run_leaderboard_menu", return_value=screen) as run_lb:
            close = front._menu_action_leaderboard(state, session, object())

        self.assertFalse(close)
        run_lb.assert_called_once()


if __name__ == "__main__":
    unittest.main()
