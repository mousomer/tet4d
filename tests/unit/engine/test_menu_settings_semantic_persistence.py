from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch

from tet4d.engine.runtime import menu_settings_state


@dataclass
class _ModeSettings:
    random_mode_index: int = 0
    topology_mode: int = 0
    topology_advanced: bool = False
    kick_level_index: int = 0
    bot_mode_index: int = 0
    bot_algorithm_index: int = 0
    bot_profile_index: int = 1
    exploration_mode: bool = False


@dataclass
class _MenuState:
    settings: _ModeSettings = field(default_factory=_ModeSettings)
    active_profile: str = "small"


class TestMenuSettingsSemanticPersistence(unittest.TestCase):
    def test_load_legacy_index_bools_populates_semantic_ids_and_bools(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            payload = menu_settings_state._default_settings_payload()
            # Simulate legacy file: int-backed toggles + missing semantic ids.
            for mode_key in ("2d", "3d", "4d"):
                mode = payload["settings"][mode_key]
                mode.pop("random_mode_id", None)
                mode.pop("topology_mode_id", None)
                mode.pop("kick_level_id", None)
                mode.pop("bot_mode_id", None)
                mode.pop("bot_algorithm_id", None)
                mode.pop("bot_profile_id", None)
                mode["random_mode_index"] = 1
                mode["topology_mode"] = 2
                mode["kick_level_index"] = 3
                mode["bot_mode_index"] = 4
                mode["bot_algorithm_index"] = 2
                mode["bot_profile_index"] = 0
                mode["topology_advanced"] = 1
                mode["exploration_mode"] = 0
                mode["auto_speedup_enabled"] = 0

            state_file.write_text(json.dumps(payload), encoding="utf-8")
            loaded = menu_settings_state.load_app_settings_payload()

            for mode_key in ("2d", "3d", "4d"):
                mode = loaded["settings"][mode_key]
                self.assertEqual(mode["random_mode_id"], "true_random")
                self.assertEqual(mode["random_mode_index"], 1)
                self.assertEqual(mode["topology_mode_id"], "invert_all")
                self.assertEqual(mode["topology_mode"], 2)
                self.assertEqual(mode["kick_level_id"], "forgiving")
                self.assertEqual(mode["kick_level_index"], 3)
                self.assertEqual(mode["bot_mode_id"], "step")
                self.assertEqual(mode["bot_mode_index"], 4)
                self.assertEqual(mode["bot_algorithm_id"], "greedy_layer")
                self.assertEqual(mode["bot_algorithm_index"], 2)
                self.assertEqual(mode["bot_profile_id"], "fast")
                self.assertEqual(mode["bot_profile_index"], 0)
                self.assertIsInstance(mode["topology_advanced"], bool)
                self.assertIsInstance(mode["exploration_mode"], bool)
                self.assertIsInstance(mode["auto_speedup_enabled"], bool)
                self.assertTrue(mode["topology_advanced"])
                self.assertFalse(mode["exploration_mode"])
                self.assertFalse(mode["auto_speedup_enabled"])

    def test_semantic_id_wins_over_legacy_index(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            payload = menu_settings_state._default_settings_payload()
            mode = payload["settings"]["2d"]
            mode["random_mode_index"] = 0
            mode["random_mode_id"] = "true_random"
            state_file.write_text(json.dumps(payload), encoding="utf-8")

            loaded = menu_settings_state.load_app_settings_payload()
            mode = loaded["settings"]["2d"]
            self.assertEqual(mode["random_mode_id"], "true_random")
            self.assertEqual(mode["random_mode_index"], 1)

    def test_invalid_semantic_id_falls_back_to_legacy_index(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            payload = menu_settings_state._default_settings_payload()
            mode = payload["settings"]["2d"]
            mode["random_mode_index"] = 0
            mode["random_mode_id"] = "not_a_real_rng_mode"
            state_file.write_text(json.dumps(payload), encoding="utf-8")

            loaded = menu_settings_state.load_app_settings_payload()
            mode = loaded["settings"]["2d"]
            self.assertEqual(mode["random_mode_index"], 0)
            self.assertEqual(mode["random_mode_id"], "fixed_seed")

    def test_invalid_integer_settings_are_clamped_on_load(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            payload = menu_settings_state._default_settings_payload()
            mode = payload["settings"]["2d"]
            mode["speed_level"] = -5
            mode["lines_per_level"] = 0
            mode["rotation_animation_duration_ms_2d"] = -10
            mode["endgame_relic_speed_percent"] = -1
            state_file.write_text(json.dumps(payload), encoding="utf-8")

            loaded = menu_settings_state.load_app_settings_payload()
            mode = loaded["settings"]["2d"]
            self.assertEqual(mode["speed_level"], 1)
            self.assertGreaterEqual(mode["lines_per_level"], 1)
            self.assertGreaterEqual(mode["rotation_animation_duration_ms_2d"], 0)
            self.assertGreaterEqual(mode["endgame_relic_speed_percent"], 1)

    def test_load_menu_settings_applies_semantic_ids_as_runtime_indices(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            payload = menu_settings_state._default_settings_payload()
            mode = payload["settings"]["2d"]
            mode["random_mode_index"] = 0
            mode["random_mode_id"] = "true_random"
            mode["bot_mode_index"] = 0
            mode["bot_mode_id"] = "learn"
            mode["topology_advanced"] = 1
            state_file.write_text(json.dumps(payload), encoding="utf-8")

            state = _MenuState()
            ok, _ = menu_settings_state.load_menu_settings(state, 2)
            self.assertTrue(ok)
            self.assertEqual(state.settings.random_mode_index, 1)
            self.assertEqual(state.settings.bot_mode_index, 3)
            self.assertIs(state.settings.topology_advanced, True)

    def test_save_menu_settings_writes_semantic_ids_and_bool_toggles(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        state_dir = root / "state"
        state_file = state_dir / "menu_settings.json"
        state_dir.mkdir(parents=True, exist_ok=True)

        with (
            patch.object(menu_settings_state, "STATE_DIR", state_dir),
            patch.object(menu_settings_state, "STATE_FILE", state_file),
        ):
            state = _MenuState()
            state.settings.random_mode_index = 1
            state.settings.topology_mode = 2
            state.settings.kick_level_index = 3
            state.settings.bot_mode_index = 4
            state.settings.bot_algorithm_index = 2
            state.settings.bot_profile_index = 0
            state.settings.topology_advanced = True
            state.settings.exploration_mode = False
            ok, _ = menu_settings_state.save_menu_settings(state, 2)
            self.assertTrue(ok)

            persisted = json.loads(state_file.read_text(encoding="utf-8"))
            mode = persisted["settings"]["2d"]
            self.assertEqual(mode["random_mode_id"], "true_random")
            self.assertEqual(mode["topology_mode_id"], "invert_all")
            self.assertEqual(mode["kick_level_id"], "forgiving")
            self.assertEqual(mode["bot_mode_id"], "step")
            self.assertEqual(mode["bot_algorithm_id"], "greedy_layer")
            self.assertEqual(mode["bot_profile_id"], "fast")
            self.assertIs(mode["topology_advanced"], True)
            self.assertIs(mode["exploration_mode"], False)
            self.assertIsInstance(mode["auto_speedup_enabled"], bool)
