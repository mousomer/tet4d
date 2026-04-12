from __future__ import annotations

from pathlib import Path
import unittest


class TestWindowsPackagingScript(unittest.TestCase):
    @staticmethod
    def _windows_script() -> str:
        script_path = (
            Path(__file__).resolve().parents[3]
            / "packaging"
            / "scripts"
            / "build_windows.ps1"
        )
        return script_path.read_text(encoding="utf-8")

    @staticmethod
    def _release_workflow() -> str:
        workflow_path = (
            Path(__file__).resolve().parents[3]
            / ".github"
            / "workflows"
            / "release-packaging.yml"
        )
        return workflow_path.read_text(encoding="utf-8")

    def test_windows_msi_embeds_wix_cab_payload(self) -> None:
        script = self._windows_script()

        self.assertIn('<MediaTemplate EmbedCab="yes" />', script)

    def test_windows_packaging_script_cleans_stale_artifacts_and_builds_via_temp_output(self) -> None:
        script = self._windows_script()

        self.assertIn('$TempOutputDir = Join-Path $BuildDir "out"', script)
        self.assertIn("Remove-PackagingArtifacts -Paths @($ArtifactDir, $BuildDir)", script)
        self.assertIn("Remove-Item $TempOutputDir -Recurse -Force", script)
        self.assertIn("New-Item -ItemType Directory -Path $TempOutputDir -Force", script)
        self.assertIn('$TempArtifactPath = Join-Path $TempOutputDir "tet4d-$Version-windows-x64.msi"', script)
        self.assertIn("-out $TempArtifactPath", script)
        self.assertIn("Move-Item -Path $TempArtifactPath -Destination $ArtifactPath -Force", script)

    def test_windows_packaging_script_fails_on_external_cab_output(self) -> None:
        script = self._windows_script()

        self.assertIn("Get-ChildItem -Path $BuildDir -Filter *.cab -File -Recurse", script)
        self.assertIn("Unexpected external CAB output detected", script)
        self.assertIn("must not contain CAB sidecars", script)
        self.assertIn("expected MSI", script)

    def test_release_workflow_uploads_windows_only_as_msi(self) -> None:
        workflow = self._release_workflow()

        self.assertIn("name: Upload Windows installer artifacts", workflow)
        self.assertIn("path: artifacts/installers/*.msi", workflow)
        self.assertIn("name: Upload Linux installer artifacts", workflow)
        self.assertIn("path: artifacts/installers/*.deb", workflow)
        self.assertIn("name: Upload macOS installer artifacts", workflow)
        self.assertIn("path: artifacts/installers/*.dmg", workflow)
        stripped_lines = {line.strip() for line in workflow.splitlines()}
        self.assertNotIn("path: artifacts/installers/*", stripped_lines)


if __name__ == "__main__":
    unittest.main()
