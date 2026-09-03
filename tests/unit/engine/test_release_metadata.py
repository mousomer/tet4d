from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.release.release_metadata import (
    ARTIFACT_SPECS,
    generate_manifest,
    normalize_tag,
    validate_tag,
)


class TestReleaseMetadata(unittest.TestCase):
    def test_tag_normalization_accepts_prefixed_and_plain_versions(self) -> None:
        self.assertEqual("0.7.5", normalize_tag("v0.7.5"))
        self.assertEqual("0.7.5", normalize_tag("0.7.5"))
        self.assertEqual("0.7.5", normalize_tag("refs/tags/v0.7.5"))

    def test_tag_validation_rejects_project_version_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "does not match"):
            validate_tag("v0.8.0", "0.7.5")

    def test_manifest_binds_all_artifacts_to_version_and_source_sha(self) -> None:
        version = "0.7.5"
        source_sha = "a" * 40
        with tempfile.TemporaryDirectory() as temp_dir:
            artifact_dir = Path(temp_dir)
            for index, spec in enumerate(ARTIFACT_SPECS):
                path = artifact_dir / spec.filename_template.format(version=version)
                path.write_bytes(f"artifact-{index}".encode())

            manifest = generate_manifest(artifact_dir, version, source_sha)

            self.assertEqual("tet4d.release-manifest.v1", manifest["schema"])
            self.assertEqual(version, manifest["version"])
            self.assertEqual(source_sha, manifest["source_sha"])
            entries = [
                artifact
                for family in manifest["product_families"].values()
                for artifact in family["artifacts"].values()
            ]
            self.assertEqual(7, len(entries))
            for entry in entries:
                expected = hashlib.sha256(
                    (artifact_dir / entry["filename"]).read_bytes()
                ).hexdigest()
                self.assertEqual(expected, entry["sha256"])
                self.assertGreater(entry["bytes"], 0)
            self.assertEqual(
                "Python Tet4D",
                manifest["product_families"]["python_tet4d"]["display_name"],
            )
            self.assertEqual(
                "Tet4D",
                manifest["product_families"]["godot_game"]["display_name"],
            )
            ipados = manifest["product_families"]["godot_designer"]["artifacts"][
                "ipados_xcodeproject"
            ]
            self.assertEqual("unsigned", ipados["evidence"]["signing"])
            self.assertIn("simulator", ipados["evidence"]["build_status"])
            self.assertIn("not installed", ipados["evidence"]["device_acceptance"])
            self.assertIn("not a supported", ipados["evidence"]["target_status"])

    def test_manifest_rejects_missing_artifact(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertRaisesRegex(ValueError, "expected exactly one"),
        ):
            generate_manifest(Path(temp_dir), "0.7.5", "b" * 40)

    def test_manifest_rejects_non_commit_source_identity(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            self.assertRaisesRegex(ValueError, "source SHA"),
        ):
            generate_manifest(Path(temp_dir), "0.7.5", "not-a-commit")


if __name__ == "__main__":
    unittest.main()
