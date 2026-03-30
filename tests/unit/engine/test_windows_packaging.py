from __future__ import annotations

from pathlib import Path
import unittest


class TestWindowsPackagingScript(unittest.TestCase):
    def test_windows_msi_embeds_wix_cab_payload(self) -> None:
        script_path = (
            Path(__file__).resolve().parents[3]
            / "packaging"
            / "scripts"
            / "build_windows.ps1"
        )
        script = script_path.read_text(encoding="utf-8")

        self.assertIn('<MediaTemplate EmbedCab="yes" />', script)


if __name__ == "__main__":
    unittest.main()
