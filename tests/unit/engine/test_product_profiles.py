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
    def _isolated_repository(self, temporary: str) -> tuple[Path, Path]:
        repository_root = Path(temporary) / "repository"
        canonical_project = repository_root / "godot/Tet4D.Godot"
        canonical_project.parent.mkdir(parents=True)
        shutil.copytree(PROJECT, canonical_project, ignore=shutil.ignore_patterns(".godot"))
        policy_path = repository_root / "config/project/policy_pack.json"
        policy_path.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "config/project/policy_pack.json", policy_path)
        return repository_root, canonical_project

    def _assert_rejected_without_canonical_mutation(
        self, repository_root: Path, canonical_project: Path, staged_root: Path
    ) -> None:
        before_project = (canonical_project / "project.godot").read_bytes()
        before_presets = (canonical_project / "export_presets.cfg").read_bytes()
        with self.assertRaisesRegex(staging.ProfileError, "outside the canonical Godot project"):
            staging.apply_profile(repository_root, staged_root, "godot_game")
        self.assertEqual(before_project, (canonical_project / "project.godot").read_bytes())
        self.assertEqual(before_presets, (canonical_project / "export_presets.cfg").read_bytes())

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
                marker = staging.identity_marker_resource(product_id)
                self.assertIn(f'config/tet4d_product_identity_marker="{marker}"', project)
                self.assertTrue((staged / marker.removeprefix("res://")).is_file())
                self.assertIn(identity, presets)
        self.assertEqual(before_project, (PROJECT / "project.godot").read_bytes())
        self.assertEqual(before_presets, (PROJECT / "export_presets.cfg").read_bytes())

    def test_staging_rejects_incorrect_product_id_or_main_scene_before_export(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary) / "project"
            shutil.copytree(PROJECT, staged, ignore=shutil.ignore_patterns(".godot"))
            staging.apply_profile(ROOT, staged, "godot_designer")
            project = staged / "project.godot"
            project.write_text(
                project.read_text(encoding="utf-8").replace(
                    'config/tet4d_product_id="godot_designer"',
                    'config/tet4d_product_id="godot_game"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(staging.ProfileError, "identity does not match"):
                staging.validate_staged_profile(ROOT, staged, "godot_designer")
            project.write_text(
                project.read_text(encoding="utf-8").replace(
                    'config/tet4d_product_id="godot_game"',
                    'config/tet4d_product_id="godot_designer"',
                ).replace(
                    'run/main_scene="res://scenes/designer_bootstrap.tscn"',
                    'run/main_scene="res://scenes/game_bootstrap.tscn"',
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(staging.ProfileError, "identity does not match"):
                staging.validate_staged_profile(ROOT, staged, "godot_designer")

    def test_game_staging_does_not_acquire_designer_identity_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary) / "project"
            shutil.copytree(PROJECT, staged, ignore=shutil.ignore_patterns(".godot"))
            staging.apply_profile(ROOT, staged, "godot_game")
            self.assertTrue(
                (staged / staging.identity_marker_resource("godot_game").removeprefix("res://")).is_file()
            )
            self.assertFalse(
                (staged / staging.identity_marker_resource("godot_designer").removeprefix("res://")).exists()
            )

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

    def test_staging_rejects_canonical_root_and_every_descendant(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository_root, canonical_project = self._isolated_repository(temporary)
            targets = (
                canonical_project,
                canonical_project / "staged-copy",
                canonical_project / "tmp/release/staged-copy",
                canonical_project / "tmp/../staged-copy",
            )
            for target in targets:
                self._assert_rejected_without_canonical_mutation(repository_root, canonical_project, target)
            self.assertFalse((canonical_project / "staged-copy").exists())
            self.assertFalse((canonical_project / "tmp").exists())

    def test_staging_rejects_partial_copy_and_symlink_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository_root, canonical_project = self._isolated_repository(temporary)
            partial_copy = canonical_project / "partial-copy"
            shutil.copytree(canonical_project, partial_copy, ignore=shutil.ignore_patterns(".godot"))
            self._assert_rejected_without_canonical_mutation(repository_root, canonical_project, partial_copy)

            symlink_target = canonical_project / "symlink-target"
            symlink_target.mkdir()
            descendant_link = Path(temporary) / "descendant-link"
            root_link = Path(temporary) / "root-link"
            try:
                descendant_link.symlink_to(symlink_target, target_is_directory=True)
                root_link.symlink_to(canonical_project, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            self._assert_rejected_without_canonical_mutation(repository_root, canonical_project, descendant_link)
            self._assert_rejected_without_canonical_mutation(repository_root, canonical_project, root_link)

    def test_staging_allows_prefixed_sibling_and_external_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository_root, canonical_project = self._isolated_repository(temporary)
            before_project = (canonical_project / "project.godot").read_bytes()
            before_presets = (canonical_project / "export_presets.cfg").read_bytes()
            for staged_root in (
                canonical_project.with_name("Tet4D.Godot-staged"),
                Path(temporary) / "external-project",
            ):
                shutil.copytree(canonical_project, staged_root, ignore=shutil.ignore_patterns(".godot"))
                staging.apply_profile(repository_root, staged_root, "godot_game")
                self.assertIn('config/tet4d_product_id="godot_game"', (staged_root / "project.godot").read_text())
            self.assertEqual(before_project, (canonical_project / "project.godot").read_bytes())
            self.assertEqual(before_presets, (canonical_project / "export_presets.cfg").read_bytes())

    def test_rejected_target_diagnostics_are_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository_root, canonical_project = self._isolated_repository(temporary)
            target = canonical_project / "staged-copy"
            with self.assertRaises(staging.ProfileError) as raised:
                staging.apply_profile(repository_root, target, "godot_game")
            message = str(raised.exception)
            self.assertIn("outside the canonical Godot project", message)
            self.assertNotIn(str(repository_root), message)
            self.assertNotIn(str(target), message)

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
