from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


def _detect_project_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "tools" / "governance" / "validate_project_contracts.py").exists():
            return candidate
        if (candidate / "tools" / "validate_project_contracts.py").exists():
            return candidate
    return here.parents[2]


PROJECT_ROOT = _detect_project_root()
_NEW_VALIDATOR = PROJECT_ROOT / "tools" / "governance" / "validate_project_contracts.py"
_OLD_VALIDATOR = PROJECT_ROOT / "tools" / "validate_project_contracts.py"
VALIDATOR = _NEW_VALIDATOR if _NEW_VALIDATOR.exists() else _OLD_VALIDATOR


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
