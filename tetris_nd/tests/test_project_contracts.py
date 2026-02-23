from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = PROJECT_ROOT / "tools" / "validate_project_contracts.py"


class TestProjectContracts(unittest.TestCase):
    def test_contract_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            details = (result.stdout + "\n" + result.stderr).strip()
            self.fail(f"project contract validator failed.\n{details}")


if __name__ == "__main__":
    unittest.main()
