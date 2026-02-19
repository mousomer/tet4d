from __future__ import annotations

import unittest

from tetris_nd.project_config import (
    PROJECT_ROOT,
    keybindings_dir_relative,
    menu_settings_file_relative,
    project_constant_int,
    topology_profile_export_file_default_relative,
    resolve_state_relative_path,
    sanitize_state_relative_path,
    state_dir_relative,
)


class TestProjectConfig(unittest.TestCase):
    def test_state_path_sanitization_rejects_unsafe_values(self) -> None:
        default_rel = "state/analytics/events.jsonl"
        self.assertEqual(
            sanitize_state_relative_path("../../outside.jsonl", default_relative=default_rel),
            default_rel,
        )
        self.assertEqual(
            sanitize_state_relative_path("/tmp/absolute.jsonl", default_relative=default_rel),
            default_rel,
        )
        self.assertEqual(
            sanitize_state_relative_path("state/analytics/custom.jsonl", default_relative=default_rel),
            "state/analytics/custom.jsonl",
        )

    def test_state_path_resolution_stays_in_repo_state_root(self) -> None:
        resolved = resolve_state_relative_path(
            "../../outside.jsonl",
            default_relative="state/menu_settings.json",
        )
        expected = (PROJECT_ROOT / "state/menu_settings.json").resolve()
        self.assertEqual(resolved, expected)

    def test_project_constant_int_uses_externalized_values(self) -> None:
        self.assertGreater(project_constant_int(("cache_limits", "text_surface_max"), 0), 0)
        self.assertGreater(project_constant_int(("rendering", "3d", "side_panel"), 0), 0)
        self.assertEqual(project_constant_int(("rendering", "missing"), 123), 123)

    def test_externalized_relative_paths_keep_expected_prefixes(self) -> None:
        self.assertTrue(menu_settings_file_relative().startswith(state_dir_relative() + "/"))
        self.assertTrue(keybindings_dir_relative().startswith("keybindings"))
        self.assertTrue(
            topology_profile_export_file_default_relative().startswith(state_dir_relative() + "/")
        )


if __name__ == "__main__":
    unittest.main()
