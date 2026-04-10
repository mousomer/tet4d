from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cli.front as launcher_front

from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings


class TestLauncherFrontSettingsRoutes(unittest.TestCase):
    def test_menu_action_settings_passes_category_to_filtered_hub(self) -> None:
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
        )
        with (
            patch.object(launcher_front, "run_settings_hub_menu", return_value=result) as run_menu,
            patch.object(launcher_front, "_persist_session_status"),
        ):
            should_close = launcher_front._menu_action_settings(
                state,
                session,
                fonts_nd=object(),
                initial_row_key="audio_master",
                category_id="audio",
            )

        self.assertFalse(should_close)
        self.assertEqual(run_menu.call_args.kwargs["initial_row_key"], "audio_master")
        self.assertEqual(run_menu.call_args.kwargs["category_id"], "audio")

    def test_launcher_keyboard_profiles_menu_expands_live_rows(self) -> None:
        original_items = launcher_front._MENU_GRAPH["launcher_settings_profiles"]["items"]
        try:
            with (
                patch(
                    "tet4d.ui.pygame.launch.launcher_profile_menu.list_key_profiles",
                    return_value=["small", "full", "custom_alpha"],
                ),
                patch(
                    "tet4d.ui.pygame.launch.launcher_profile_menu.active_key_profile",
                    return_value="full",
                ),
            ):
                launcher_front._sync_launcher_settings_profile_rows()
                labels = [
                    item["label"]
                    for item in launcher_front._menu_items("launcher_settings_profiles")
                ]
        finally:
            launcher_front._MENU_GRAPH["launcher_settings_profiles"]["items"] = original_items

        self.assertIn("Profile: small", labels)
        self.assertIn("Profile: full (Active)", labels)
        self.assertIn("Profile: custom_alpha", labels)
        self.assertNotIn("Profiles", labels)

    def test_profile_row_activation_sets_active_profile_and_persists_state(self) -> None:
        state = launcher_front.MainMenuState()
        session = launcher_front._LauncherSession(
            screen=object(),
            display_settings=DisplaySettings(),
            audio_settings=AudioSettings(),
        )
        registry = launcher_front.ActionRegistry()

        with (
            patch.object(launcher_front, "set_active_key_profile", return_value=(True, "Active key profile: full")) as set_profile,
            patch.object(launcher_front, "load_active_profile_bindings", return_value=(True, "Loaded")) as load_bindings,
            patch.object(launcher_front, "_persist_session_status"),
            patch.object(launcher_front, "_sync_launcher_settings_profile_rows"),
            patch.object(launcher_front, "_sync_launcher_profile_actions"),
        ):
            should_close = launcher_front._menu_action_activate_profile(
                "full",
                state,
                session,
                registry=registry,
            )

        self.assertFalse(should_close)
        self.assertEqual(state.status, "Loaded")
        self.assertFalse(state.status_error)
        set_profile.assert_called_once_with("full")
        load_bindings.assert_called_once()
