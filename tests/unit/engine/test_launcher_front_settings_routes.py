from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cli.front as launcher_front

from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings


class TestLauncherFrontSettingsRoutes(unittest.TestCase):
    def test_menu_action_settings_passes_initial_page_and_item_to_settings_hub(self) -> None:
        state = launcher_front.MainMenuState()
        session = launcher_front._LauncherSession(
            screen=object(),
            display_settings=DisplaySettings(),
            audio_settings=AudioSettings(),
        )
        result = SimpleNamespace(
            screen=session.screen,
            audio_settings=session.audio_settings,
            display_settings=session.display_settings,
            keep_running=True,
            dispatched_action_id="",
        )
        with (
            patch.object(
                launcher_front, "run_settings_hub_menu", return_value=result
            ) as run_menu,
            patch.object(launcher_front, "_persist_session_status"),
        ):
            should_close = launcher_front._menu_action_settings(
                state,
                session,
                fonts_nd=object(),
                initial_page_id="settings_audio",
                initial_item_id="audio_master",
            )

        self.assertFalse(should_close)
        self.assertEqual(run_menu.call_args.kwargs["initial_page_id"], "settings_audio")
        self.assertEqual(run_menu.call_args.kwargs["initial_item_id"], "audio_master")

    def test_menu_action_settings_routes_legacy_dispatch_back_to_launcher_handler(
        self,
    ) -> None:
        state = launcher_front.MainMenuState()
        session = launcher_front._LauncherSession(
            screen=object(),
            display_settings=DisplaySettings(),
            audio_settings=AudioSettings(),
        )
        result = SimpleNamespace(
            screen=session.screen,
            audio_settings=session.audio_settings,
            display_settings=session.display_settings,
            keep_running=True,
            dispatched_action_id="settings_legacy_topology_editor",
        )
        with (
            patch.object(
                launcher_front, "run_settings_hub_menu", return_value=result
            ),
            patch.object(
                launcher_front,
                "_menu_action_legacy_topology_editor",
                return_value=False,
            ) as legacy_handler,
        ):
            should_close = launcher_front._menu_action_settings(
                state,
                session,
                fonts_nd=object(),
                initial_page_id="settings_legacy",
                initial_item_id="settings_legacy_topology_editor",
            )

        self.assertFalse(should_close)
        legacy_handler.assert_called_once()
