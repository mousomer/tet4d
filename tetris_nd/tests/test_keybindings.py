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

from tetris_nd import keybindings, menu_config, menu_settings_state


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

    def test_strict_hjkl_camera_defaults(self) -> None:
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("yaw_fine_neg"), (pygame.K_h,))
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("yaw_neg"), (pygame.K_j,))
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("yaw_pos"), (pygame.K_k,))
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("yaw_fine_pos"), (pygame.K_l,))
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("pitch_pos"), (pygame.K_u,))
        self.assertEqual(keybindings.CAMERA_KEYS_3D.get("pitch_neg"), (pygame.K_o,))
        self.assertEqual(keybindings.CAMERA_KEYS_4D.get("view_xw_neg"), (pygame.K_F5,))
        self.assertEqual(keybindings.CAMERA_KEYS_4D.get("view_xw_pos"), (pygame.K_F6,))
        self.assertEqual(keybindings.CAMERA_KEYS_4D.get("view_zw_neg"), (pygame.K_F7,))
        self.assertEqual(keybindings.CAMERA_KEYS_4D.get("view_zw_pos"), (pygame.K_F8,))

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

    def test_rename_custom_profile(self) -> None:
        ok, msg, profile = keybindings.create_auto_profile()
        self.assertTrue(ok, msg)
        self.assertIsNotNone(profile)
        created_profile = str(profile)

        ok, msg = keybindings.set_active_key_profile(created_profile)
        self.assertTrue(ok, msg)
        ok, msg = keybindings.load_active_profile_bindings()
        self.assertTrue(ok, msg)

        renamed = "custom_renamed"
        ok, msg = keybindings.rename_key_profile(created_profile, renamed)
        self.assertTrue(ok, msg)
        self.assertEqual(keybindings.active_key_profile(), renamed)
        self.assertIn(renamed, keybindings.list_key_profiles())
        self.assertNotIn(created_profile, keybindings.list_key_profiles())
        self.assertTrue(keybindings.profile_keybinding_file_path(2, renamed).exists())

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

    def test_small_profile_rotation_ladder_defaults(self) -> None:
        self.assertEqual(keybindings.KEYS_2D["rotate_xy_pos"], (pygame.K_q,))
        self.assertEqual(keybindings.KEYS_2D["rotate_xy_neg"], (pygame.K_w,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xy_pos"], (pygame.K_q,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xy_neg"], (pygame.K_w,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xz_pos"], (pygame.K_a,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xz_neg"], (pygame.K_s,))
        self.assertEqual(keybindings.KEYS_4D["rotate_yz_pos"], (pygame.K_z,))
        self.assertEqual(keybindings.KEYS_4D["rotate_yz_neg"], (pygame.K_x,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xw_pos"], (pygame.K_r,))
        self.assertEqual(keybindings.KEYS_4D["rotate_xw_neg"], (pygame.K_t,))
        self.assertEqual(keybindings.KEYS_4D["rotate_yw_pos"], (pygame.K_f,))
        self.assertEqual(keybindings.KEYS_4D["rotate_yw_neg"], (pygame.K_g,))
        self.assertEqual(keybindings.KEYS_4D["rotate_zw_pos"], (pygame.K_v,))
        self.assertEqual(keybindings.KEYS_4D["rotate_zw_neg"], (pygame.K_b,))

    def test_system_defaults_are_deconflicted_from_rotation_ladder(self) -> None:
        self.assertEqual(keybindings.SYSTEM_KEYS["restart"], (pygame.K_y,))
        self.assertEqual(keybindings.SYSTEM_KEYS["toggle_grid"], (pygame.K_c,))
        gameplay_keys_4d = {key for keys in keybindings.KEYS_4D.values() for key in keys}
        self.assertNotIn(keybindings.SYSTEM_KEYS["restart"][0], gameplay_keys_4d)
        self.assertNotIn(keybindings.SYSTEM_KEYS["toggle_grid"][0], gameplay_keys_4d)


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

    def test_load_payload_backfills_missing_mode_fields(self) -> None:
        menu_settings_state.STATE_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "active_profile": keybindings.PROFILE_FULL,
            "last_mode": "4d",
            "settings": {
                "2d": {
                    "width": 12,
                    "height": 21,
                }
            },
        }
        menu_settings_state.STATE_FILE.write_text(json.dumps(payload), encoding="utf-8")

        loaded = menu_settings_state.load_app_settings_payload()
        settings_2d = loaded["settings"]["2d"]
        self.assertEqual(settings_2d["width"], 12)
        self.assertEqual(settings_2d["height"], 21)
        self.assertEqual(settings_2d["bot_mode_index"], 0)
        self.assertEqual(settings_2d["bot_profile_index"], 1)
        self.assertEqual(loaded["settings"]["3d"]["bot_budget_ms"], 20)
        self.assertEqual(loaded["settings"]["4d"]["bot_budget_ms"], 32)
        self.assertEqual(loaded["active_profile"], keybindings.PROFILE_FULL)

    def test_save_app_settings_payload_preserves_default_nested_fields(self) -> None:
        ok, msg = menu_settings_state.save_app_settings_payload(
            {
                "active_profile": keybindings.PROFILE_FULL,
                "settings": {"2d": {"width": 11}},
            }
        )
        self.assertTrue(ok, msg)

        loaded = menu_settings_state.load_app_settings_payload()
        self.assertEqual(loaded["active_profile"], keybindings.PROFILE_FULL)
        self.assertEqual(loaded["settings"]["2d"]["width"], 11)
        self.assertEqual(loaded["settings"]["2d"]["bot_algorithm_index"], 0)
        self.assertEqual(loaded["settings"]["2d"]["bot_profile_index"], 1)

    def test_missing_state_file_loads_external_defaults(self) -> None:
        defaults = menu_config.default_settings_payload()
        loaded = menu_settings_state.load_app_settings_payload()

        self.assertEqual(loaded["version"], defaults["version"])
        self.assertEqual(loaded["active_profile"], defaults["active_profile"])
        self.assertEqual(loaded["settings"]["2d"]["width"], defaults["settings"]["2d"]["width"])
        self.assertEqual(loaded["settings"]["3d"]["depth"], defaults["settings"]["3d"]["depth"])
        self.assertEqual(loaded["settings"]["4d"]["fourth"], defaults["settings"]["4d"]["fourth"])

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
