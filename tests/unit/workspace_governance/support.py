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

# Every variable that can decide an interpreter or the source it imports. A test
# exercising a lower tier must scrub them: CI exports TET4D_PYTHON and
# GOVERNANCE_PYTHON for the whole job, and the gate exports PYTHONPATH in source
# mode, so an inherited environment would otherwise answer instead of the tier
# under test. PYTHONPATH matters most: a checkout under test must resolve its own
# binding, not inherit the one belonging to the worktree running the suite.
INTERPRETER_SELECTORS = (
    "TET4D_PYTHON",
    "GOVERNANCE_PYTHON",
    "WORKSPACE_VENV",
    "PYTHON_BIN",
    "TET4D_RESOLVED_PYTHON",
    "PYTHONPATH",
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
    for name in ("gov", "pyproject.toml", "AGENTS.md", "CLAUDE.md", "CURRENT_STATE.md"):
        shutil.copy2(ROOT / name, root / name)
    # Generated-output checkers execute checkout-local renderers and protect
    # their outputs; sharing writable renderer/target files with ROOT would
    # make this fixture violate the actual consumer boundary.
    shutil.copytree(ROOT / "docs", root / "docs")
    for name in ("godot", "native", "src"):
        (root / name).symlink_to(ROOT / name, target_is_directory=True)
    shutil.copytree(ROOT / "tools/governance", root / "tools/governance")
    # Consumer integration copies only its versioned discovery adapter contract.
    manifest = json.loads((root / "config/governance/project.json").read_text())
    for adapter in manifest.get("skill_adapters", []):
        source = ROOT / adapter["path"]
        target = root / adapter["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return root
