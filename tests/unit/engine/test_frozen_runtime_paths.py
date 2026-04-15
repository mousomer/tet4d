from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tet4d.engine.runtime import keybinding_store
from tet4d.engine.runtime import project_config as project_config_module
from tet4d.engine.runtime.project_config import (
    PROJECT_ROOT,
    keybindings_defaults_path,
    keybindings_dir_path,
    keybindings_profiles_dir_path,
    menu_settings_file_path,
    score_events_file_default_path,
    state_dir_path,
)


class TestFrozenRuntimePathContracts(unittest.TestCase):
    def test_frozen_runtime_paths_keep_read_only_and_writable_roots_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writable_root = Path(tmp) / "AppData" / "Roaming" / "tet4d"
            with (
                mock.patch.dict(os.environ, {"TET4D_STATE_ROOT": ""}),
                mock.patch.object(project_config_module, "WRITABLE_ROOT", writable_root),
            ):
                expected_root = writable_root.resolve()
                self.assertEqual(keybindings_dir_path(), (PROJECT_ROOT / "keybindings").resolve())
                self.assertEqual(
                    keybindings_defaults_path(),
                    (PROJECT_ROOT / "config/keybindings/defaults.json").resolve(),
                )
                self.assertEqual(
                    keybindings_profiles_dir_path(),
                    expected_root / "keybindings/profiles",
                )
                self.assertEqual(state_dir_path(), expected_root / "state")
                self.assertEqual(
                    menu_settings_file_path(),
                    expected_root / "state/menu_settings.json",
                )
                self.assertEqual(
                    score_events_file_default_path(),
                    expected_root / "state/analytics/score_events.jsonl",
                )

    def test_frozen_keybinding_store_accepts_project_and_user_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            writable_root = Path(tmp) / "AppData" / "Roaming" / "tet4d"
            with (
                mock.patch.dict(os.environ, {"TET4D_STATE_ROOT": ""}),
                mock.patch.object(project_config_module, "WRITABLE_ROOT", writable_root),
            ):
                bundled_keybindings = keybindings_dir_path()
                writable_profiles = keybindings_profiles_dir_path()
                files = {
                    2: bundled_keybindings / "2d.json",
                    3: bundled_keybindings / "3d.json",
                    4: bundled_keybindings / "4d.json",
                }
                with (
                    mock.patch.object(
                        keybinding_store, "KEYBINDINGS_DIR", bundled_keybindings
                    ),
                    mock.patch.object(
                        keybinding_store, "KEYBINDINGS_PROFILES_DIR", writable_profiles
                    ),
                    mock.patch.object(keybinding_store, "KEYBINDING_FILES", files),
                ):
                    self.assertEqual(
                        keybinding_store.profile_keybinding_file_path(
                            2, keybinding_store.PROFILE_SMALL
                        ),
                        (bundled_keybindings / "2d.json").resolve(),
                    )
                    self.assertEqual(
                        keybinding_store.profile_keybinding_file_path(
                            4, keybinding_store.PROFILE_FULL
                        ),
                        (writable_profiles / "full" / "4d.json").resolve(),
                    )
                    with self.assertRaisesRegex(
                        ValueError, "within keybindings directories"
                    ):
                        keybinding_store.safe_resolve_keybinding_path(
                            writable_root.parent / "outside.json"
                        )


if __name__ == "__main__":
    unittest.main()
