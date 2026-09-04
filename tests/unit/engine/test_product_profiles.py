from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.governance import validate_product_platform_matrix as matrix

ROOT = Path(__file__).resolve().parents[3]
PROJECT = ROOT / "godot/Tet4D.Godot"
STAGING_PATH = ROOT / "packaging/godot/stage_product_profile.py"


def _staging_module():
    spec = importlib.util.spec_from_file_location("stage_product_profile", STAGING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


staging = _staging_module()


class TestProductProfiles(unittest.TestCase):
    def test_profiles_are_distinct_and_reference_existing_resources(self) -> None:
        products = json.loads((ROOT / "config/project/policy_pack.json").read_text())["product_platform_contract"]["products"]
        game = products["godot_game"]
        designer = products["godot_designer"]
        for key in ("application_identity", "main_scene", "icon", "artifact_name_token"):
            self.assertNotEqual(game[key], designer[key])
        for profile in (game, designer):
            self.assertTrue((PROJECT / profile["main_scene"].removeprefix("res://")).is_file())
            self.assertTrue((PROJECT / profile["icon"].removeprefix("res://")).is_file())

    def test_staging_selects_each_profile_without_mutating_source(self) -> None:
        before_project = (PROJECT / "project.godot").read_bytes()
        before_presets = (PROJECT / "export_presets.cfg").read_bytes()
        with tempfile.TemporaryDirectory() as temporary:
            for product_id, scene, icon, identity in (
                ("godot_game", "game_bootstrap.tscn", "tet4d_game.svg", "io.github.mousomer.tet4d"),
                ("godot_designer", "designer_bootstrap.tscn", "tet4d_designer.svg", "io.github.mousomer.tet4d.designer"),
            ):
                staged = Path(temporary) / product_id
                shutil.copytree(PROJECT, staged, ignore=shutil.ignore_patterns(".godot"))
                staging.apply_profile(ROOT, staged, product_id)
                project = (staged / "project.godot").read_text(encoding="utf-8")
                presets = (staged / "export_presets.cfg").read_text(encoding="utf-8")
                self.assertIn(f'run/main_scene="res://scenes/{scene}"', project)
                self.assertIn(f'config/icon="res://assets/icons/{icon}"', project)
                self.assertIn(f'config/tet4d_product_id="{product_id}"', project)
                self.assertIn(identity, presets)
        self.assertEqual(before_project, (PROJECT / "project.godot").read_bytes())
        self.assertEqual(before_presets, (PROJECT / "export_presets.cfg").read_bytes())

    def test_unknown_and_ambiguous_profiles_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary) / "project"
            shutil.copytree(PROJECT, staged, ignore=shutil.ignore_patterns(".godot"))
            with self.assertRaisesRegex(staging.ProfileError, "unknown"):
                staging.apply_profile(ROOT, staged, "unknown")
            project = staged / "project.godot"
            project.write_text(project.read_text(encoding="utf-8") + '\nrun/main_scene="res://scenes/game_bootstrap.tscn"\n', encoding="utf-8")
            with self.assertRaisesRegex(staging.ProfileError, "ambiguous"):
                staging.apply_profile(ROOT, staged, "godot_game")

    def test_profiles_reject_cross_product_identity(self) -> None:
        policy = json.loads((ROOT / "config/project/policy_pack.json").read_text())
        altered = copy.deepcopy(policy)
        altered["product_platform_contract"]["products"]["godot_game"]["application_identity"] = altered["product_platform_contract"]["products"]["godot_designer"]["application_identity"]
        issues = matrix.validate_contract(
            altered,
            (ROOT / ".github/workflows/release-packaging.yml").read_text(),
            (PROJECT / "export_presets.cfg").read_text(),
            (ROOT / "docs/governance/CHANGE_GOVERNANCE.md").read_text(),
            (ROOT / "docs/rds/RDS_PACKAGING.md").read_text(),
            (ROOT / "docs/BACKLOG.md").read_text(),
        )
        self.assertIn("Godot product profiles must use distinct application_identity", issues)


if __name__ == "__main__":
    unittest.main()
