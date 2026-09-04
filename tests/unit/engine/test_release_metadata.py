from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from tools.release import release_metadata
from tools.release.release_metadata import (
    ARTIFACT_SPECS,
    MANIFEST_SCHEMA,
    generate_manifest,
    manifest_asset_names,
    normalize_tag,
    parse_release_scope,
    release_note_text,
    scope_payload,
    validate_manifest,
    validate_source_sha,
    validate_tag,
)


class TestReleaseMetadata(unittest.TestCase):
    version = "0.9.0"
    source_sha = "a" * 40

    def _artifact_directory(self, scope: str) -> tempfile.TemporaryDirectory[str]:
        temporary = tempfile.TemporaryDirectory()
        selected = set(parse_release_scope(scope))
        artifact_dir = Path(temporary.name)
        for index, spec in enumerate(ARTIFACT_SPECS):
            if spec.consumer_id in selected:
                (
                    artifact_dir / spec.filename_template.format(version=self.version)
                ).write_bytes(f"artifact-{index}".encode())
        return temporary

    def test_tag_normalization_accepts_prefixed_and_plain_versions(self) -> None:
        self.assertEqual("0.9.0", normalize_tag("v0.9.0"))
        self.assertEqual("0.9.0", normalize_tag("0.9.0"))
        self.assertEqual("0.9.0", normalize_tag("refs/tags/v0.9.0"))

    def test_tag_validation_rejects_project_version_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_tag("v0.8.0", self.version)

    def test_source_sha_must_be_exact_lowercase_commit_shape(self) -> None:
        self.assertEqual(self.source_sha, validate_source_sha(self.source_sha))
        for invalid in ("A" * 40, "a" * 39, f" {self.source_sha}", "not-a-commit"):
            with (
                self.subTest(invalid=invalid),
                self.assertRaisesRegex(ValueError, "source SHA"),
            ):
                validate_source_sha(invalid)

    def test_scope_parser_canonicalizes_subset_and_exposes_machine_selection(
        self,
    ) -> None:
        scope = parse_release_scope("godot_game_macos, python_windows")
        self.assertEqual(("python_windows", "godot_game_macos"), scope)
        payload = scope_payload("godot_game_macos, python_windows")
        self.assertEqual(list(scope), payload["release_scope"])
        self.assertTrue(payload["selected"]["python_windows"])
        self.assertFalse(payload["selected"]["python_macos"])

    def test_scope_parser_accepts_current_all_in_registered_order(self) -> None:
        self.assertEqual(
            tuple(spec.consumer_id for spec in ARTIFACT_SPECS),
            parse_release_scope("current_all"),
        )

    def test_scope_parser_rejects_empty_duplicate_unknown_and_ambiguous_all(
        self,
    ) -> None:
        for invalid, expected in (
            ("", "empty"),
            ("python_macos,,python_windows", "empty"),
            ("python_macos,python_macos", "duplicate"),
            ("not_a_consumer", "unknown"),
            ("current_all,python_macos", "sole"),
            (" current_all", "exactly"),
        ):
            with (
                self.subTest(invalid=invalid),
                self.assertRaisesRegex(ValueError, expected),
            ):
                parse_release_scope(invalid)

    def test_scope_and_policy_keep_the_registered_matrix_and_transitional_exception(
        self,
    ) -> None:
        policy_path = (
            Path(__file__).resolve().parents[3] / "config/project/policy_pack.json"
        )
        contract = json.loads(policy_path.read_text(encoding="utf-8"))[
            "product_platform_contract"
        ]
        self.assertEqual(
            {
                "python_tet4d": ["macos", "windows", "linux"],
                "godot_game": ["macos", "windows", "linux", "android", "ipados"],
                "godot_designer": ["macos", "windows"],
            },
            contract["target_platforms"],
        )
        consumers = {
            item["consumer_id"]: item for item in contract["packaging_consumers"]
        }
        self.assertEqual({spec.consumer_id for spec in ARTIFACT_SPECS}, set(consumers))
        self.assertEqual(
            "transitional_mismatch", consumers["legacy_designer_android"]["status"]
        )
        self.assertEqual(
            "transitional_mismatch", consumers["legacy_designer_ipados"]["status"]
        )
        with self.assertRaisesRegex(ValueError, "unknown"):
            parse_release_scope("godot_designer_macos")

    def test_manifest_rejects_duplicate_registered_identity_or_filename_contract(
        self,
    ) -> None:
        duplicate_consumer_specs = (
            *ARTIFACT_SPECS[:-1],
            replace(ARTIFACT_SPECS[-1], consumer_id="legacy_designer_android"),
        )
        with (
            patch.object(release_metadata, "ARTIFACT_SPECS", duplicate_consumer_specs),
            self.assertRaisesRegex(ValueError, "duplicate artifact consumer identity"),
        ):
            generate_manifest(Path("."), self.version, self.source_sha, "current_all")

        duplicate_filename_specs = (
            ARTIFACT_SPECS[0],
            replace(
                ARTIFACT_SPECS[1], filename_template=ARTIFACT_SPECS[0].filename_template
            ),
            *ARTIFACT_SPECS[2:],
        )
        with (
            patch.object(release_metadata, "ARTIFACT_SPECS", duplicate_filename_specs),
            self.assertRaisesRegex(ValueError, "duplicate artifact filenames"),
        ):
            generate_manifest(
                Path("."), self.version, self.source_sha, "python_windows,python_macos"
            )

    def test_manifest_rejects_unknown_product_or_platform_contract(self) -> None:
        for replacement, error_type, expected in (
            (
                replace(ARTIFACT_SPECS[0], product_id="unknown_product"),
                TypeError,
                "unknown product",
            ),
            (
                replace(ARTIFACT_SPECS[0], platform_id="unknown_platform"),
                ValueError,
                "unknown platform",
            ),
        ):
            with (
                self.subTest(replacement=replacement),
                patch.object(
                    release_metadata,
                    "ARTIFACT_SPECS",
                    (replacement, *ARTIFACT_SPECS[1:]),
                ),
                self.assertRaisesRegex(error_type, expected),
            ):
                generate_manifest(
                    Path("."), self.version, self.source_sha, "python_windows"
                )

    def test_manifest_binds_only_selected_artifacts_to_version_and_source_sha(
        self,
    ) -> None:
        scope = "godot_game_macos,godot_designer_windows"
        with self._artifact_directory(scope) as temp_dir:
            artifact_dir = Path(temp_dir)
            manifest = generate_manifest(
                artifact_dir, self.version, self.source_sha, scope
            )

            self.assertEqual(MANIFEST_SCHEMA, manifest["schema"])
            self.assertEqual(self.version, manifest["version"])
            self.assertEqual(self.source_sha, manifest["source_sha"])
            self.assertEqual(
                ["godot_designer_windows", "godot_game_macos"],
                manifest["release_scope"],
            )
            entries = [
                artifact
                for family in manifest["product_families"].values()
                for artifact in family["artifacts"].values()
            ]
            self.assertEqual(2, len(entries))
            self.assertEqual(
                {"godot_designer_windows", "godot_game_macos"},
                {entry["consumer_id"] for entry in entries},
            )
            for entry in entries:
                expected = hashlib.sha256(
                    (artifact_dir / entry["filename"]).read_bytes()
                ).hexdigest()
                self.assertEqual(expected, entry["sha256"])
                self.assertGreater(entry["bytes"], 0)
            self.assertEqual(
                "Tet4D Designer",
                manifest["product_families"]["godot_designer"]["display_name"],
            )
            self.assertEqual(
                ("godot_designer_windows", "godot_game_macos"),
                validate_manifest(manifest, artifact_dir, self.source_sha),
            )

    def test_manifest_rejects_missing_selected_and_extra_unselected_artifacts(
        self,
    ) -> None:
        scope = "godot_game_macos,godot_designer_windows"
        with (
            self._artifact_directory("godot_game_macos") as temp_dir,
            self.assertRaisesRegex(ValueError, "expected exactly one"),
        ):
            generate_manifest(Path(temp_dir), self.version, self.source_sha, scope)
        with (
            self._artifact_directory("godot_game_macos,python_windows") as temp_dir,
            self.assertRaisesRegex(ValueError, "unselected consumer"),
        ):
            generate_manifest(
                Path(temp_dir), self.version, self.source_sha, "godot_game_macos"
            )

    def test_manifest_rejects_wrong_version_filename(self) -> None:
        with self._artifact_directory("godot_game_macos") as temp_dir:
            artifact_dir = Path(temp_dir)
            spec = next(
                spec
                for spec in ARTIFACT_SPECS
                if spec.consumer_id == "godot_game_macos"
            )
            (artifact_dir / spec.filename_template.format(version="0.8.0")).write_bytes(
                b"old"
            )
            with self.assertRaisesRegex(ValueError, "expected '0.9.0'"):
                generate_manifest(
                    artifact_dir, self.version, self.source_sha, "godot_game_macos"
                )

    def test_manifest_validator_rejects_checksum_and_identity_mismatch(self) -> None:
        scope = "legacy_designer_android"
        with self._artifact_directory(scope) as temp_dir:
            artifact_dir = Path(temp_dir)
            manifest = generate_manifest(
                artifact_dir, self.version, self.source_sha, scope
            )
            entry = manifest["product_families"]["godot_designer"]["artifacts"][
                "legacy_designer_android"
            ]
            self.assertEqual("android", entry["platform_id"])
            self.assertIn("transitional mismatch", entry["evidence"]["target_status"])
            checksum_mismatch = deepcopy(manifest)
            checksum_mismatch["product_families"]["godot_designer"]["artifacts"][
                "legacy_designer_android"
            ]["sha256"] = "b" * 64
            with self.assertRaisesRegex(ValueError, "checksum"):
                validate_manifest(checksum_mismatch, artifact_dir, self.source_sha)
            identity_mismatch = deepcopy(manifest)
            identity_mismatch["product_families"]["godot_designer"]["artifacts"][
                "legacy_designer_android"
            ]["platform_id"] = "macos"
            with self.assertRaisesRegex(ValueError, "identity"):
                validate_manifest(identity_mismatch)

    def test_release_notes_and_expected_assets_follow_manifest_scope_only(self) -> None:
        scope = "godot_game_macos,legacy_designer_ipados"
        with self._artifact_directory(scope) as temp_dir:
            manifest = generate_manifest(
                Path(temp_dir), self.version, self.source_sha, scope
            )
            notes = release_note_text(manifest)
            self.assertIn("Tet4D game", notes)
            self.assertIn("Transitional Designer iPadOS artifact", notes)
            self.assertNotIn("Python Tet4D", notes)
            self.assertIn("technical evidence only", notes)
            self.assertEqual(
                [
                    "tet4d-designer-0.9.0-ipados-xcodeproject.zip",
                    "tet4d-godot-game-0.9.0-macos-universal.zip",
                    "tet4d-release-0.9.0-manifest.json",
                ],
                manifest_asset_names(manifest, "tet4d-release-0.9.0-manifest.json"),
            )


if __name__ == "__main__":
    unittest.main()
