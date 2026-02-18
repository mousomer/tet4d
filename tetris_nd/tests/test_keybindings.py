from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without pygame-ce
    pygame = None

if pygame is None:  # pragma: no cover - exercised in environments without pygame-ce
    raise unittest.SkipTest("pygame-ce is required for keybinding runtime tests")

from tetris_nd import keybindings, menu_settings_state


@dataclass
class _Settings2D:
    width: int = 10
    height: int = 20
    speed_level: int = 1


@dataclass
class _MenuState2D:
    settings: _Settings2D = field(default_factory=_Settings2D)
    active_profile: str = keybindings.PROFILE_SMALL


class _TempKeybindingRoot:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.keybindings_dir = self.root / "keybindings"
        self.state_dir = self.root / "state"
        self.files = {
            2: self.keybindings_dir / "2d.json",
            3: self.keybindings_dir / "3d.json",
            4: self.keybindings_dir / "4d.json",
        }
        self.patches = [
            patch.object(keybindings, "KEYBINDINGS_DIR", self.keybindings_dir),
            patch.object(keybindings, "KEYBINDINGS_PROFILES_DIR", self.keybindings_dir / "profiles"),
            patch.object(keybindings, "KEYBINDING_FILES", self.files),
            patch.object(menu_settings_state, "STATE_DIR", self.state_dir),
            patch.object(menu_settings_state, "STATE_FILE", self.state_dir / "menu_settings.json"),
        ]

    def start(self) -> None:
        for p in self.patches:
            p.start()
        keybindings.ACTIVE_KEY_PROFILE = keybindings.PROFILE_SMALL
        keybindings._KEYBINDINGS_INITIALIZED = False
        keybindings.initialize_keybinding_files()

    def stop(self) -> None:
        for p in reversed(self.patches):
            p.stop()
        self._tmp.cleanup()


class TestKeybindingProfiles(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.tmp_root = _TempKeybindingRoot()
        self.tmp_root.start()
        self.addCleanup(self.tmp_root.stop)

    def test_initialize_writes_builtin_profile_files(self) -> None:
        for profile in keybindings.BUILTIN_PROFILES:
            for dimension in (2, 3, 4):
                path = keybindings.profile_keybinding_file_path(dimension, profile)
                self.assertTrue(path.exists(), f"missing file: {path}")
                payload = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(payload.get("dimension"), dimension)
                self.assertEqual(payload.get("profile"), profile)

    def test_create_and_activate_custom_profile(self) -> None:
        ok, msg, profile = keybindings.create_auto_profile()
        self.assertTrue(ok, msg)
        self.assertIsNotNone(profile)
        profile_name = str(profile)

        ok, msg = keybindings.set_active_key_profile(profile_name)
        self.assertTrue(ok, msg)
        ok, msg = keybindings.load_active_profile_bindings()
        self.assertTrue(ok, msg)

        self.assertEqual(keybindings.active_key_profile(), profile_name)
        active_path = keybindings.keybinding_file_path(4)
        self.assertEqual(active_path, keybindings.profile_keybinding_file_path(4, profile_name))
        self.assertTrue(active_path.exists())

    def test_save_rejects_path_outside_keybindings_dir(self) -> None:
        outside = self.tmp_root.root.parent / "outside-bindings.json"
        ok, msg = keybindings.save_keybindings_file(2, file_path=str(outside))
        self.assertFalse(ok)
        self.assertIn("within keybindings directory", msg)

    def test_invalid_profile_name_is_rejected(self) -> None:
        ok, msg = keybindings.set_active_key_profile("not a valid profile name!")
        self.assertFalse(ok)
        self.assertIn("invalid profile name", msg)

    def test_rebind_conflict_modes_work(self) -> None:
        original_move_left = keybindings.KEYS_2D["move_x_neg"][0]
        target_key = keybindings.KEYS_2D["move_x_pos"][0]

        ok, msg = keybindings.rebind_action_key(
            2,
            "game",
            "move_x_neg",
            target_key,
            conflict_mode=keybindings.REBIND_CONFLICT_CANCEL,
        )
        self.assertFalse(ok, msg)
        self.assertEqual(keybindings.KEYS_2D["move_x_neg"][0], original_move_left)

        ok, msg = keybindings.rebind_action_key(
            2,
            "game",
            "move_x_neg",
            target_key,
            conflict_mode=keybindings.REBIND_CONFLICT_SWAP,
        )
        self.assertTrue(ok, msg)
        self.assertEqual(keybindings.KEYS_2D["move_x_neg"][0], target_key)
        self.assertEqual(keybindings.KEYS_2D["move_x_pos"][0], original_move_left)

    def test_reset_active_profile_bindings_restores_defaults(self) -> None:
        custom_key = pygame.K_v
        ok, msg = keybindings.rebind_action_key(2, "game", "move_x_neg", custom_key)
        self.assertTrue(ok, msg)
        self.assertEqual(keybindings.KEYS_2D["move_x_neg"][0], custom_key)

        ok, msg = keybindings.reset_active_profile_bindings(2)
        self.assertTrue(ok, msg)
        self.assertNotEqual(keybindings.KEYS_2D["move_x_neg"][0], custom_key)

    def test_camera_rebind_cannot_override_4d_gameplay_key(self) -> None:
        rotation_key = keybindings.KEYS_4D["rotate_zw_neg"][0]
        ok, msg = keybindings.rebind_action_key(4, "camera", "reset", rotation_key)
        self.assertFalse(ok)
        self.assertIn("cannot override", msg.lower())
        self.assertIn(rotation_key, keybindings.KEYS_4D["rotate_zw_neg"])


class TestMenuSettingsPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.tmp_root = _TempKeybindingRoot()
        self.tmp_root.start()
        self.addCleanup(self.tmp_root.stop)

    def test_save_and_load_menu_settings_round_trip(self) -> None:
        ok, msg = keybindings.set_active_key_profile(keybindings.PROFILE_FULL)
        self.assertTrue(ok, msg)
        ok, msg = keybindings.load_active_profile_bindings()
        self.assertTrue(ok, msg)

        state = _MenuState2D()
        state.settings.width = 13
        state.settings.height = 24
        state.settings.speed_level = 4

        ok, msg = menu_settings_state.save_menu_settings(state, 2)
        self.assertTrue(ok, msg)

        ok, msg = keybindings.set_active_key_profile(keybindings.PROFILE_SMALL)
        self.assertTrue(ok, msg)
        ok, msg = keybindings.load_active_profile_bindings()
        self.assertTrue(ok, msg)

        restored = _MenuState2D()
        ok, msg = menu_settings_state.load_menu_settings(restored, 2)
        self.assertTrue(ok, msg)

        self.assertEqual(restored.settings.width, 13)
        self.assertEqual(restored.settings.height, 24)
        self.assertEqual(restored.settings.speed_level, 4)
        self.assertEqual(restored.active_profile, keybindings.PROFILE_FULL)
        self.assertEqual(keybindings.active_key_profile(), keybindings.PROFILE_FULL)

    def test_reset_menu_settings_restores_defaults(self) -> None:
        state = _MenuState2D()
        state.settings.width = 16
        state.settings.height = 29
        state.settings.speed_level = 9

        ok, msg = keybindings.set_active_key_profile(keybindings.PROFILE_FULL)
        self.assertTrue(ok, msg)
        ok, msg = keybindings.load_active_profile_bindings()
        self.assertTrue(ok, msg)

        ok, msg = menu_settings_state.reset_menu_settings_to_defaults(state, 2)
        self.assertTrue(ok, msg)

        self.assertEqual(state.settings.width, 10)
        self.assertEqual(state.settings.height, 20)
        self.assertEqual(state.settings.speed_level, 1)
        self.assertEqual(state.active_profile, keybindings.PROFILE_SMALL)
        self.assertEqual(keybindings.active_key_profile(), keybindings.PROFILE_SMALL)

    def test_load_menu_settings_sanitizes_invalid_profile_and_mode(self) -> None:
        payload = menu_settings_state._default_settings_payload()
        payload["active_profile"] = "../bad profile"
        payload["last_mode"] = "invalid"
        menu_settings_state.STATE_DIR.mkdir(parents=True, exist_ok=True)
        menu_settings_state.STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")

        state = _MenuState2D()
        ok, msg = menu_settings_state.load_menu_settings(state, 2)
        self.assertTrue(ok, msg)
        self.assertEqual(state.active_profile, keybindings.PROFILE_SMALL)
        self.assertEqual(keybindings.active_key_profile(), keybindings.PROFILE_SMALL)
