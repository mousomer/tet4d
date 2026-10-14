"""Real contract boundaries for consumers with no Python application."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
from support import PACK, ROOT, write

from tools.workspace_governance.cli.gov import _sync
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core


@pytest.fixture
def native_consumer(tmp_path: Path) -> Path:
    root = tmp_path
    shutil.copytree(PACK, root / "tools/workspace_governance")
    for directory in (".governance", "docs", "scripts"):
        (root / directory).mkdir()
    (root / "AGENTS.md").write_text("Use the project's resolved governance.\n")
    (root / "docs/governance.md").write_text("Run declared checks before completion.\n")
    (root / "scripts/check.py").write_text("raise SystemExit(0)\n")
    (root / ".governance/python").symlink_to(sys.executable)
    project = {
        "schema_version": 1,
        "project": {"id": "native-demo", "name": "Native demo"},
        "authorities": [
            {
                "authority_id": "engineering",
                "authority_type": "human",
                "scope": "engineering",
                "source": "docs/governance.md",
                "exclusive": True,
                "canonical_governance": True,
                "source_type": "file",
            }
        ],
        "routes": {
            "development": {
                "authority_refs": ["engineering"],
                "dispatch_paths": ["AGENTS.md"],
                "typical_verification_requirements": ["project checks"],
            }
        },
        "verification": {
            "canonical": {"command": "python scripts/check.py"},
            "full": {"command": "python scripts/check.py --full"},
            "targeted": "python scripts/check.py",
            "rule": "Select evidence from impact.",
        },
        "execution": {
            "default_mode": "FEATURE",
            "profiles": {
                mode: {
                    "exploration": ["inspect owner"],
                    "routes": ["development"],
                    "final_evidence_rule": "Report verification evidence.",
                }
                for mode in ("LOCAL_FIX", "FEATURE", "STRUCTURAL_CHANGE")
            },
            "representative_scenarios": [],
        },
        "role_bootstrap": {"instruction_roots": ["AGENTS.md"]},
        "generated_surfaces": [],
        "environment": {
            "profile": "tools",
            "preferred": ".governance/python",
            "interpreter_override": "DEMO_GOVERNANCE_PYTHON",
            "route_tools": {},
        },
        "sanitation": {
            "secret_scanner": "scripts/check.py",
            "repository_check": "scripts/check.py",
            "bounded_diagnostics": 10,
        },
        "canonical_owner_set": {"owners": {"engineering": "docs/governance.md"}},
    }
    workspace = {
        "schema_version": 1,
        "workspace_id": "native-demo-workspace",
        "governance_pack": {"required_schema": 1, "lock": ".governance/lock.json"},
        "projects": [
            {
                "id": "native-demo",
                "repository": ".",
                "manifest": ".governance/project.json",
            }
        ],
        "relationships": [],
        "defaults": {"project": "native-demo"},
    }
    write(root / ".governance/project.json", project)
    write(root / ".governance/workspace.json", workspace)
    write(root / ".governance/lock.json", {"pack_path": "tools/workspace_governance"})
    _sync(root, GovernanceResolver.for_root(root))
    return root


def test_legacy_application_certification_and_facade_remain_valid() -> None:
    workspace = json.loads((ROOT / ".governance/workspace.json").read_text())
    project = json.loads((ROOT / "config/governance/project.json").read_text())
    assert core.validate_manifests(ROOT, workspace, project, None, pack_root=PACK) == []
    assert core._python_specifier(ROOT, project) == (">=3.11", "pyproject.toml")
    assert core._generated_surface_issues(ROOT, project) == []


def _renderer(root: Path, body: str) -> GovernanceResolver:
    (root / "docs/generated.md").write_text("current\n")
    (root / "scripts/render.py").write_text(body)
    path = root / ".governance/project.json"
    project = json.loads(path.read_text())
    project["generated_surfaces"] = [
        {
            "surface_id": "reference",
            "kind": "generated_output",
            "source": "scripts/render.py",
            "target": "docs/generated.md",
            "check_command": ["{python}", "scripts/render.py", "--check"],
        }
    ]
    write(path, project)
    return GovernanceResolver.for_root(root)


def test_mandatory_repository_gate_requests_generated_evidence() -> None:
    runner = (ROOT / "scripts/verify.sh").read_text()
    if "./gov check --generated" not in runner:
        # Existing consumers preserve their verifier body and adopt the
        # generated-evidence gate through a mandatory managed hook.
        assert '"$GOVERNANCE_REPO_ROOT/scripts/verify-governance.sh"' in runner
        helper = (ROOT / "scripts/verify-governance.sh").read_text()
        assert helper.index("./gov doctor") < helper.index("./gov check --generated")
    # The original owning family stays active throughout the additive pilot.
    assert 'run_governance_step "config_reference"' in runner
