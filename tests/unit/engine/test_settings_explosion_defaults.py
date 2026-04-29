from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

import pygame

from tet4d.engine.runtime import menu_config, menu_settings_state
from tet4d.engine.runtime.project_config import state_dir_path
from tet4d.ui.pygame.launch import settings_hub_actions, settings_hub_model
from tet4d.ui.pygame.locked_cell_explosion import defaults_store
from tet4d.ui.pygame.runtime_ui.app_runtime import DisplaySettings
from tet4d.ui.pygame.runtime_ui.audio import AudioSettings


def _new_workspace_temp_dir(prefix: str) -> Path:
    root = state_dir_path() / "pytest_temp"
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / f"{prefix}_{uuid4().hex}"
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate


class _TempMenuSettingsRoot:
    def __init__(self) -> None:
        self.root = _new_workspace_temp_dir("explosion_defaults")
        self.state_dir = self.root / "state"
        self.patches = [
            patch.object(menu_settings_state, "STATE_DIR", self.state_dir),
            patch.object(menu_settings_state, "STATE_FILE", self.state_dir / "menu_settings.json"),
        ]

    def start(self) -> None:
        for p in self.patches:
            p.start()

    def stop(self) -> None:
        for p in reversed(self.patches):
            p.stop()
        shutil.rmtree(self.root, ignore_errors=True)


class TestExplosionDefaultsSettingsCoverage(unittest.TestCase):
    @staticmethod
    def _defaults_payload() -> dict[str, object]:
        path = (
            Path(__file__).resolve().parents[3] / "config" / "menu" / "defaults.json"
        )
        return json.loads(path.read_text(encoding="utf-8"))

    def test_explosion_defaults_settings_cover_all_persisted_fields(self) -> None:
        payload = self._defaults_payload()
        defaults_root = payload.get("explosion_defaults")
        self.assertIsInstance(defaults_root, dict)

        for mode_key in ("2d", "3d", "4d"):
            with self.subTest(mode_key=mode_key):
                mode_defaults = defaults_root.get(mode_key)
                self.assertIsInstance(mode_defaults, dict)
                expected_fields = set(mode_defaults.keys())

                menu_id = f"settings_explosion_defaults_{mode_key}"
                menu = menu_config.authored_menu_definition(menu_id)
                observed: set[str] = set()
                for item in menu["items"]:
                    item_type = str(item.get("type", "")).lower()
                    if item_type not in {"toggle", "selector", "slider", "stepper"}:
                        continue
                    setting_id = str(item.get("setting_id", "")).strip().lower()
                    prefix = f"explosion_defaults.{mode_key}."
                    self.assertTrue(
                        setting_id.startswith(prefix),
                        f"{menu_id}:{item.get('id')} setting_id must start with {prefix}",
                    )
                    remainder = setting_id[len(prefix) :]
                    field = remainder.split("[", 1)[0]
                    observed.add(field)

                self.assertEqual(observed, expected_fields)

    def test_explosion_defaults_control_types_match_semantic_families(self) -> None:
        bool_fields = {
            "trace_enabled",
            "sound_enabled",
        }
        enum_fields = {
            "topology_preset_id",
            "snapshot_source_id",
            "piece_set_id",
            "piece_shape_name",
            "view_mode",
            "boundary_response",
            "particle_collisions",
            "mass_mode",
            "diagnostics_mode",
            "grid_mode",
            "shadow_mode",
            "speed_preset",
            "w_movement_animation_style",
        }
        numeric_fields = {
            "base_mass",
            "random_mass_min",
            "random_mass_max",
            "collision_elasticity",
            "trace_retention_ms",
            "endgame_live_cell_fraction",
            "seed",
            "cell_origin",
        }

        for mode_key in ("2d", "3d", "4d"):
            menu_id = f"settings_explosion_defaults_{mode_key}"
            menu = menu_config.authored_menu_definition(menu_id)
            for item in menu["items"]:
                item_type = str(item.get("type", "")).lower()
                if item_type not in {"toggle", "selector", "slider", "stepper"}:
                    continue
                setting_id = str(item.get("setting_id", "")).strip().lower()
                prefix = f"explosion_defaults.{mode_key}."
                if not setting_id.startswith(prefix):
                    continue
                remainder = setting_id[len(prefix) :]
                field = remainder.split("[", 1)[0]
                if field in bool_fields:
                    self.assertEqual(
                        item_type,
                        "toggle",
                        f"{menu_id}:{item.get('id')} should be toggle for bool field {field}",
                    )
                    continue
                if field in enum_fields:
                    self.assertEqual(
                        item_type,
                        "selector",
                        f"{menu_id}:{item.get('id')} should be selector for enum field {field}",
                    )
                    continue
                if field in numeric_fields:
                    self.assertIn(
                        item_type,
                        {"slider", "stepper"},
                        f"{menu_id}:{item.get('id')} should be slider/stepper for numeric field {field}",
                    )
                    continue
                self.fail(f"{menu_id}:{item.get('id')} unknown explosion field {field}")


class TestExplosionDefaultsSettingsPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if not pygame.font.get_init():
            pygame.font.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def test_settings_save_persists_explosion_defaults_under_explosion_defaults_payload(
        self,
    ) -> None:
        tmp_root = _TempMenuSettingsRoot()
        tmp_root.start()
        self.addCleanup(tmp_root.stop)

        state = settings_hub_model.build_unified_settings_state(
            audio_settings=AudioSettings(),
            display_settings=DisplaySettings(),
        )
        # Exercise enum/bool/numeric writes via the same model Settings uses.
        state.explosion_defaults_2d = defaults_store.ExplosionDefaults(
            topology_preset_id=str(state.explosion_defaults_2d.topology_preset_id),
            snapshot_source_id="single_cell",
            piece_set_id="",
            piece_shape_name="",
            cell_origin=state.explosion_defaults_2d.cell_origin,
            view_mode=str(state.explosion_defaults_2d.view_mode),
            boundary_response="bounce",
            particle_collisions=str(state.explosion_defaults_2d.particle_collisions),
            mass_mode=str(state.explosion_defaults_2d.mass_mode),
            base_mass=1.15,
            random_mass_min=float(state.explosion_defaults_2d.random_mass_min),
            random_mass_max=float(state.explosion_defaults_2d.random_mass_max),
            collision_elasticity=float(state.explosion_defaults_2d.collision_elasticity),
            diagnostics_mode=str(state.explosion_defaults_2d.diagnostics_mode),
            grid_mode=str(state.explosion_defaults_2d.grid_mode),
            shadow_mode=str(state.explosion_defaults_2d.shadow_mode),
            trace_enabled=True,
            trace_retention_ms=float(state.explosion_defaults_2d.trace_retention_ms),
            speed_preset=str(state.explosion_defaults_2d.speed_preset),
            w_movement_animation_style="box_size",
            endgame_live_cell_fraction=0.5,
            sound_enabled=False,
            seed=4242,
        )

        screen = pygame.Surface((16, 16), pygame.SRCALPHA)
        with (
            patch.object(settings_hub_actions, "apply_display_mode", side_effect=lambda *_a, **_k: screen),
            patch.object(settings_hub_actions, "save_audio_settings", return_value=(True, "ok")),
            patch.object(settings_hub_actions, "save_display_settings", return_value=(True, "ok")),
            patch.object(settings_hub_actions, "save_analytics_settings", return_value=(True, "ok")),
            patch.object(settings_hub_actions, "save_global_game_seed", return_value=(True, "ok")),
            patch.object(settings_hub_actions, "save_shared_gameplay_settings", return_value=(True, "ok")),
            patch.object(settings_hub_actions, "play_sfx", return_value=None),
        ):
            settings_hub_actions._save_unified_settings(screen, state)

        persisted = defaults_store.mode_explosion_defaults("2d")
        self.assertEqual(persisted.snapshot_source_id, "single_cell")
        self.assertEqual(persisted.boundary_response, "bounce")
        self.assertTrue(persisted.trace_enabled)
        self.assertAlmostEqual(persisted.base_mass, 1.15, places=3)
        self.assertEqual(persisted.w_movement_animation_style, "box_size")
        self.assertAlmostEqual(persisted.endgame_live_cell_fraction, 0.5, places=6)
        self.assertFalse(persisted.sound_enabled)
        self.assertEqual(persisted.seed, 4242)

