from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from tet4d.engine.runtime import project_config as project_config_module
from tet4d.engine.runtime.project_config import (
    PROJECT_ROOT,
    WRITABLE_ROOT,
    _writable_root,
    explorer_topology_experiments_file_default_path,
    explorer_topology_profiles_file_default_path,
    keybindings_defaults_path,
    keybindings_dir_path,
    keybindings_dir_relative,
    keybindings_profiles_dir_path,
    explorer_topology_preview_cache_dir_path,
    explorer_topology_preview_cache_dir_relative,
    explorer_topology_preview_dims,
    explorer_topology_preview_file_default_path,
    explorer_topology_preview_file_default_relative,
    leaderboard_file_default_path,
    leaderboard_file_default_relative,
    menu_settings_file_path,
    menu_settings_file_relative,
    playbot_history_file_default_path,
    project_constant_color,
    project_constant_int,
    project_root_path,
    resolve_state_relative_path,
    sanitize_state_relative_path,
    score_events_file_default_path,
    score_events_file_default_relative,
    score_summary_file_default_path,
    state_dir_path,
    state_dir_relative,
    topology_profile_export_file_default_relative,
    topology_profile_export_file_default_path,
    topology_profiles_file_default_path,
    tutorial_progress_file_default_path,
)


class TestProjectConfig(unittest.TestCase):
    def test_writable_root_matches_project_root_when_not_frozen(self) -> None:
        self.assertFalse(project_config_module._FROZEN)
        self.assertEqual(WRITABLE_ROOT, PROJECT_ROOT)
        self.assertEqual(_writable_root(), PROJECT_ROOT)

    def test_writable_root_uses_platform_user_data_when_frozen(self) -> None:
        with (
            mock.patch.object(project_config_module, "_FROZEN", True),
            mock.patch("sys.platform", "win32"),
            mock.patch.dict(os.environ, {"APPDATA": "AppData/Roaming"}),
        ):
            self.assertEqual(
                _writable_root(),
                Path("AppData/Roaming/tet4d"),
            )

        with (
            mock.patch.object(project_config_module, "_FROZEN", True),
            mock.patch("sys.platform", "darwin"),
            mock.patch.object(Path, "home", return_value=Path("Users/tester")),
        ):
            self.assertEqual(
                _writable_root(),
                Path("Users/tester/Library/Application Support/tet4d"),
            )

        with (
            mock.patch.object(project_config_module, "_FROZEN", True),
            mock.patch("sys.platform", "linux"),
            mock.patch.dict(os.environ, {"XDG_DATA_HOME": "xdg-data"}),
        ):
            self.assertEqual(_writable_root(), Path("xdg-data/tet4d"))

    def test_state_path_sanitization_rejects_unsafe_values(self) -> None:
        default_rel = "state/analytics/events.jsonl"
        self.assertEqual(
            sanitize_state_relative_path(
                "../../outside.jsonl", default_relative=default_rel
            ),
            default_rel,
        )
        self.assertEqual(
            sanitize_state_relative_path(
                "/tmp/absolute.jsonl", default_relative=default_rel
            ),
            default_rel,
        )
        self.assertEqual(
            sanitize_state_relative_path(
                "state/analytics/custom.jsonl", default_relative=default_rel
            ),
            "state/analytics/custom.jsonl",
        )

    def test_state_path_resolution_stays_in_repo_state_root(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            resolved = resolve_state_relative_path(
                "../../outside.jsonl",
                default_relative="state/menu_settings.json",
            )
        expected = (PROJECT_ROOT / "state/menu_settings.json").resolve()
        self.assertEqual(resolved, expected)

    def test_state_root_override_repoints_state_backed_paths(self) -> None:
        override_root = "state/test_runs/project_config_override"
        expected_root = (PROJECT_ROOT / override_root).resolve()
        with mock.patch.dict(os.environ, {"TET4D_STATE_ROOT": override_root}):
            self.assertEqual(state_dir_path(), expected_root)
            self.assertEqual(
                menu_settings_file_path(),
                expected_root / "menu_settings.json",
            )
            self.assertEqual(
                tutorial_progress_file_default_path(),
                expected_root / "tutorial/progress.json",
            )
            self.assertEqual(
                leaderboard_file_default_path(),
                expected_root / "analytics/leaderboard.json",
            )
            self.assertEqual(
                score_events_file_default_path(),
                expected_root / "analytics/score_events.jsonl",
            )
            self.assertEqual(
                score_summary_file_default_path(),
                expected_root / "analytics/score_summary.json",
            )
            self.assertEqual(
                explorer_topology_profiles_file_default_path(),
                expected_root / "topology/explorer_profiles.json",
            )
            self.assertEqual(
                explorer_topology_preview_file_default_path(),
                expected_root / "topology/explorer_preview.json",
            )
            self.assertEqual(
                explorer_topology_preview_cache_dir_path(),
                expected_root / "topology/cache/explorer_preview",
            )
            self.assertEqual(
                resolve_state_relative_path(
                    "state/analytics/custom.jsonl",
                    default_relative="state/analytics/score_events.jsonl",
                ),
                expected_root / "analytics/custom.jsonl",
            )

    def test_state_root_override_uses_default_suffix_for_custom_state_dir(self) -> None:
        override_root = "state/test_runs/project_config_custom_state_dir"
        expected_root = (PROJECT_ROOT / override_root).resolve()
        with (
            mock.patch.dict(os.environ, {"TET4D_STATE_ROOT": override_root}),
            mock.patch.object(
                project_config_module,
                "io_paths_payload",
                return_value={"paths": {"state_dir": "data"}},
            ),
        ):
            self.assertEqual(state_dir_relative(), "data")
            self.assertEqual(menu_settings_file_path(), expected_root / "menu_settings.json")

    def test_default_state_backed_paths_use_writable_root(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            expected_root = WRITABLE_ROOT.resolve()
            self.assertEqual(state_dir_path(), expected_root / "state")
            self.assertEqual(
                menu_settings_file_path(),
                expected_root / "state/menu_settings.json",
            )
            self.assertEqual(
                playbot_history_file_default_path(),
                expected_root / "state/bench/playbot_latency_history.jsonl",
            )
            self.assertEqual(
                score_events_file_default_path(),
                expected_root / "state/analytics/score_events.jsonl",
            )
            self.assertEqual(
                score_summary_file_default_path(),
                expected_root / "state/analytics/score_summary.json",
            )
            self.assertEqual(
                leaderboard_file_default_path(),
                expected_root / "state/analytics/leaderboard.json",
            )
            self.assertEqual(
                topology_profile_export_file_default_path(),
                expected_root / "state/topology/selected_profile.json",
            )
            self.assertEqual(
                topology_profiles_file_default_path(),
                expected_root / "state/topology/profiles.json",
            )
            self.assertEqual(
                explorer_topology_profiles_file_default_path(),
                expected_root / "state/topology/explorer_profiles.json",
            )
            self.assertEqual(
                explorer_topology_preview_file_default_path(),
                expected_root / "state/topology/explorer_preview.json",
            )
            self.assertEqual(
                explorer_topology_preview_cache_dir_path(),
                expected_root / "state/topology/cache/explorer_preview",
            )
            self.assertEqual(
                explorer_topology_experiments_file_default_path(),
                expected_root / "state/topology/explorer_experiments.json",
            )
            self.assertEqual(
                tutorial_progress_file_default_path(),
                expected_root / "state/tutorial/progress.json",
            )
            self.assertEqual(
                resolve_state_relative_path(
                    "state/analytics/custom.jsonl",
                    default_relative=score_events_file_default_relative(),
                ),
                expected_root / "state/analytics/custom.jsonl",
            )

    def test_read_only_project_paths_stay_under_project_root(self) -> None:
        self.assertEqual(project_root_path(), PROJECT_ROOT)
        self.assertEqual(
            keybindings_dir_path(),
            (PROJECT_ROOT / keybindings_dir_relative()).resolve(),
        )
        self.assertEqual(
            keybindings_defaults_path(),
            (PROJECT_ROOT / "config/keybindings/defaults.json").resolve(),
        )
        self.assertEqual(
            keybindings_profiles_dir_path(),
            (WRITABLE_ROOT / "keybindings/profiles").resolve(),
        )

    def test_state_root_override_ignores_out_of_repo_paths(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"TET4D_STATE_ROOT": "../../outside_state_root"},
        ):
            self.assertEqual(state_dir_path(), (PROJECT_ROOT / "state").resolve())

    def test_project_constant_int_uses_externalized_values(self) -> None:
        self.assertGreater(
            project_constant_int(("cache_limits", "text_surface_max"), 0), 0
        )
        self.assertGreater(
            project_constant_int(("rendering", "3d", "side_panel"), 0), 0
        )
        self.assertGreater(
            project_constant_int(("layout", "menu_slider", "track_height"), 0), 0
        )
        self.assertGreater(
            project_constant_int(("layout", "menu_slider", "track_preferred_width"), 0),
            0,
        )
        self.assertGreater(
            project_constant_int(
                ("animation", "endgame", "path_family_weights", "ellipse"), 0
            ),
            0,
        )
        self.assertGreater(
            project_constant_int(("animation", "endgame", "collision_max_relics"), 0),
            0,
        )
        self.assertGreater(
            project_constant_int(("animation", "endgame", "seed_salt"), 0),
            0,
        )
        soft_drop_delay = project_constant_int(
            ("tutorial", "action_delay_ms", "soft_drop"),
            0,
        )
        hard_drop_delay = project_constant_int(
            ("tutorial", "action_delay_ms", "hard_drop"),
            0,
        )
        self.assertGreater(soft_drop_delay, 0)
        self.assertGreaterEqual(hard_drop_delay, soft_drop_delay)
        self.assertEqual(project_constant_int(("rendering", "missing"), 123), 123)

    def test_project_constant_color_uses_theme_values(self) -> None:
        project_config_module.ui_theme_payload.cache_clear()
        try:
            with mock.patch.object(
                project_config_module,
                "_read_json_object",
                return_value={"button": {"bg": [1, 2, 3]}},
            ):
                self.assertEqual(
                    project_constant_color(("button", "bg"), (9, 9, 9)),
                    (1, 2, 3),
                )
        finally:
            project_config_module.ui_theme_payload.cache_clear()

    def test_project_constant_color_falls_back_for_invalid_values(self) -> None:
        project_config_module.ui_theme_payload.cache_clear()
        try:
            with mock.patch.object(
                project_config_module,
                "_read_json_object",
                return_value={"button": {"bg": [1, 2, 999]}},
            ):
                self.assertEqual(
                    project_constant_color(("button", "bg"), (9, 9, 9)),
                    (9, 9, 9),
                )
        finally:
            project_config_module.ui_theme_payload.cache_clear()

    def test_project_constant_color_falls_back_for_missing_path(self) -> None:
        project_config_module.ui_theme_payload.cache_clear()
        try:
            with mock.patch.object(
                project_config_module,
                "_read_json_object",
                return_value={"panel": {"bg": [4, 5, 6]}},
            ):
                self.assertEqual(
                    project_constant_color(("button", "border"), (7, 8, 9)),
                    (7, 8, 9),
                )
        finally:
            project_config_module.ui_theme_payload.cache_clear()

    def test_externalized_relative_paths_keep_expected_prefixes(self) -> None:
        self.assertTrue(
            menu_settings_file_relative().startswith(state_dir_relative() + "/")
        )
        self.assertTrue(keybindings_dir_relative().startswith("keybindings"))
        self.assertTrue(
            topology_profile_export_file_default_relative().startswith(
                state_dir_relative() + "/"
            )
        )
        self.assertTrue(
            explorer_topology_preview_file_default_relative().startswith(
                state_dir_relative() + "/"
            )
        )
        self.assertTrue(
            explorer_topology_preview_cache_dir_relative().startswith(
                state_dir_relative() + "/"
            )
        )
        self.assertEqual(explorer_topology_preview_dims(2), (4, 4))
        self.assertEqual(explorer_topology_preview_dims(3), (4, 4, 4))
        self.assertEqual(explorer_topology_preview_dims(4), (4, 4, 4, 4))
        self.assertTrue(
            leaderboard_file_default_relative().startswith(state_dir_relative() + "/")
        )


if __name__ == "__main__":
    unittest.main()
