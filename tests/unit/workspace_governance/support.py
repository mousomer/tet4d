"""Shared helpers for the workspace-governance suites.

Fixtures live in `conftest.py`; this module holds the plain callables that both
the fixture and tests building their own roots need.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "tools/workspace_governance"

# Every variable that can decide an interpreter. A test exercising a lower tier
# must scrub them: CI exports TET4D_PYTHON and GOVERNANCE_PYTHON for the whole
# job, so an inherited environment would otherwise answer instead of the tier
# under test.
INTERPRETER_SELECTORS = (
    "TET4D_PYTHON",
    "GOVERNANCE_PYTHON",
    "WORKSPACE_VENV",
    "PYTHON_BIN",
    "TET4D_RESOLVED_PYTHON",
)


def scrubbed_environment(**updates: str) -> dict[str, str]:
    """Ambient environment with every interpreter selector removed."""
    env = {k: v for k, v in os.environ.items() if k not in INTERPRETER_SELECTORS}
    return {**env, **updates}


def write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


def build_checkout(root: Path) -> Path:
    """Independent mutable manifests/pack; read-only authority trees are linked."""
    shutil.copytree(ROOT / "config", root / "config")
    shutil.copytree(ROOT / ".governance", root / ".governance")
    (root / ".governance/workspace.local.json").unlink(missing_ok=True)
    shutil.copytree(PACK, root / "tools/workspace_governance")
    shutil.copytree(ROOT / "scripts", root / "scripts")
    for name in ("gov", "pyproject.toml", "AGENTS.md"):
        shutil.copy2(ROOT / name, root / name)
    for name in ("docs", "godot", "native", "src"):
        (root / name).symlink_to(ROOT / name, target_is_directory=True)
    # Non-pack tools are referenced by sanitation policy, not executed by check.
    (root / "tools/governance").symlink_to(
        ROOT / "tools/governance", target_is_directory=True
    )
    return root
