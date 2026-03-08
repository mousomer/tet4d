from __future__ import annotations

import os
import unittest
from unittest import mock

from tet4d.engine.runtime.project_config import (
    PROJECT_ROOT,
    keybindings_dir_relative,
    explorer_topology_preview_dims,
    explorer_topology_preview_file_default_path,
    explorer_topology_preview_file_default_relative,
    explorer_topology_profiles_file_default_path,
    leaderboard_file_default_path,
    leaderboard_file_default_relative,
    menu_settings_file_path,
    menu_settings_file_relative,
    project_constant_int,
    resolve_state_relative_path,
    sanitize_state_relative_path,
    score_events_file_default_path,
    score_summary_file_default_path,
    state_dir_path,
    state_dir_relative,
    topology_profile_export_file_default_relative,
    tutorial_progress_file_default_path,
)


class TestProjectConfig(unittest.TestCase):
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
                resolve_state_relative_path(
                    "state/analytics/custom.jsonl",
                    default_relative="state/analytics/score_events.jsonl",
                ),
                expected_root / "analytics/custom.jsonl",
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
        self.assertEqual(explorer_topology_preview_dims(3), (4, 4, 4))
        self.assertEqual(explorer_topology_preview_dims(4), (4, 4, 4, 4))
        self.assertTrue(
            leaderboard_file_default_relative().startswith(state_dir_relative() + "/")
        )


if __name__ == "__main__":
    unittest.main()
