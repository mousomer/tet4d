from __future__ import annotations

import copy
import json
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core

ROOT = Path(__file__).resolve().parents[3]


def manifests() -> tuple[dict[str, object], dict[str, object]]:
    workspace = json.loads((ROOT / ".governance/workspace.json").read_text())
    project = json.loads((ROOT / "config/governance/project.json").read_text())
    return workspace, project


def codes(issues: list[core.Diagnostic]) -> set[str]:
    return {issue.code for issue in issues}


def test_repository_manifests_and_pack_are_valid() -> None:
    assert GovernanceResolver.for_root(ROOT).check() == []


def test_resolution_retains_provenance_and_mode_does_not_change_evidence() -> None:
    resolver = GovernanceResolver.for_root(ROOT)
    local_fix = resolver.resolve(mode="LOCAL_FIX")
    structural = resolver.resolve(mode="STRUCTURAL_CHANGE")
    assert local_fix["execution.mode"]["value"] == "LOCAL_FIX"
    assert local_fix["execution.mode"]["source"] == "config/governance/project.json"
    assert local_fix["execution.exploration"] != structural["execution.exploration"]
    assert local_fix["verification.full"] == structural["verification.full"]
    assert local_fix["verification.rule"] == structural["verification.rule"]


def test_explain_stable_authority_identity() -> None:
    explained = GovernanceResolver.for_root(ROOT).explain("authority:godot-runtime")
    assert explained["resolved"]["authority_id"] == "godot-runtime"
    assert explained["resolved"]["source"] == "docs/architecture/authority_map.md"


@pytest.mark.parametrize(
    ("task", "mode", "route"),
    [
        ("small Godot UI defect", "LOCAL_FIX", "godot_product_shell"),
        ("small Python defect", "LOCAL_FIX", "python_reference_engine"),
        ("moderate feature", "FEATURE", "python_reference_engine"),
        ("cross-layer change", "STRUCTURAL_CHANGE", "native_deterministic_core"),
        ("governance change", "STRUCTURAL_CHANGE", "governance_and_tooling"),
        ("packaging release change", "STRUCTURAL_CHANGE", "packaging_and_release"),
    ],
)
def test_representative_scenarios(task: str, mode: str, route: str) -> None:
    result = GovernanceResolver.for_root(ROOT).resolve(task=task)
    assert result["execution.mode"]["value"] == mode
    assert route in result["routes"]["value"]


def test_duplicate_and_ambiguous_authorities_are_deterministic() -> None:
    workspace, project = manifests()
    duplicate = copy.deepcopy(project["authorities"][0])
    project["authorities"].append(duplicate)
    assert "DUPLICATE_AUTHORITY" in codes(
        core.validate_manifests(ROOT, workspace, project, None)
    )
    project["authorities"][-1]["authority_id"] = "another-owner"
    issues = core.validate_manifests(ROOT, workspace, project, None)
    ambiguity = next(issue for issue in issues if issue.code == "AMBIGUOUS_AUTHORITY")
    assert "another-owner" in ambiguity.reason
    assert ambiguity.sources
    assert ambiguity.owner == "human/project"


def test_ownership_broken_reference_and_machine_path_diagnostics() -> None:
    workspace, project = manifests()
    workspace["verification"] = {"full": "wrong layer"}
    workspace["defaults"]["checkout"] = "/" + "home/example/project"
    project["routes"]["python_reference_engine"]["authority_refs"].append("missing")
    issues = core.validate_manifests(ROOT, workspace, project, None)
    assert {"CONFLICTING_VALUE", "BROKEN_REFERENCE"} <= codes(issues)


def test_ambiguous_workspace_project_routing_fails() -> None:
    workspace, project = manifests()
    workspace["projects"].append(copy.deepcopy(workspace["projects"][0]))
    issues = core.validate_manifests(ROOT, workspace, project, None)
    assert "AMBIGUOUS_AUTHORITY" in codes(issues)


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("generated", "STALE_GENERATED_SURFACE"),
        ("compatibility_facade", "CONFLICTING_VALUE"),
    ],
)
def test_stale_surface_repair_class(tmp_path: Path, kind: str, expected: str) -> None:
    workspace, project = manifests()
    (tmp_path / "source").write_text("new")
    (tmp_path / "target").write_text("old")
    project["generated_surfaces"] = [
        {
            "kind": kind,
            "source": "source",
            "target": "target",
            "source_sha256": "0" * 64,
        }
    ]
    issues = core.validate_manifests(tmp_path, workspace, project, None)
    assert expected in codes(issues)


def test_pack_drift_is_detected(tmp_path: Path) -> None:
    workspace, _ = manifests()
    pack = tmp_path / "pack"
    pack.mkdir()
    (pack / "VERSION").write_text("0.1.0\n")
    (pack / "MANIFEST.json").write_text('{"version": "0.1.0"}\n')
    digest, files = core.pack_hash(pack)
    lock = {
        "pack_path": "pack",
        "version": "0.1.0",
        "content_sha256": digest,
        "files": files,
    }
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock))
    workspace["governance_pack"]["lock"] = "lock.json"
    assert core.validate_pack(tmp_path, workspace) == []
    (pack / "VERSION").write_text("modified\n")
    assert codes(core.validate_pack(tmp_path, workspace)) == {"PACK_DRIFT"}


def test_missing_and_valid_interpreter_resolution(tmp_path: Path) -> None:
    _, project = manifests()
    project["environment"]["preferred"] = "missing/python"
    interpreter, _, issues = core.resolve_interpreter(tmp_path, project, None, {})
    assert interpreter is None
    assert codes(issues) == {"ENVIRONMENT_MISMATCH"}
    interpreter, reason, issues = core.resolve_interpreter(
        tmp_path, project, {"interpreter": sys.executable}, {}
    )
    assert interpreter == Path(sys.executable).absolute()
    assert reason == "approved local overlay"
    assert issues == []


@pytest.mark.parametrize(
    ("version", "package", "fact"),
    [
        ([3, 10, 9], "src/tet4d/__init__.py", "python.version"),
        ([3, 11, 9], "elsewhere/tet4d/__init__.py", "editable_install"),
    ],
)
def test_doctor_detects_version_and_wrong_checkout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    version: list[int],
    package: str,
    fact: str,
) -> None:
    _, project = manifests()
    fake = tmp_path / ".venv/bin/python"
    fake.parent.mkdir(parents=True)
    shutil.copy2(sys.executable, fake)
    os.chmod(fake, 0o755)
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    payload = json.dumps(
        {
            "version": version,
            "package": str(tmp_path / package),
            "critical_packages": ["tet4d"],
        }
    )
    monkeypatch.setattr(
        core.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0, stdout=payload, stderr=""
        ),
    )
    _, issues = core.doctor(tmp_path, project, None, {})
    assert any(
        issue.fact == fact and issue.code == "ENVIRONMENT_MISMATCH" for issue in issues
    )


def test_fixture_catalog_covers_required_cases() -> None:
    fixture = json.loads(
        (
            ROOT / "tools/workspace_governance/synthetic-fixtures/contradictions.json"
        ).read_text()
    )
    assert len(fixture["cases"]) == 13
