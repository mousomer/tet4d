from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools.workspace_governance.cli.gov import _sync
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core

ROOT = Path(__file__).resolve().parents[3]
PACK_ROOT = ROOT / "tools/workspace_governance"


def manifests() -> tuple[dict[str, object], dict[str, object]]:
    workspace = json.loads((ROOT / ".governance/workspace.json").read_text())
    project = json.loads((ROOT / "config/governance/project.json").read_text())
    return workspace, project


def validate(
    workspace: dict, project: dict, local: dict | None = None
) -> list[core.Diagnostic]:
    return core.validate_manifests(ROOT, workspace, project, local, pack_root=PACK_ROOT)


def codes(issues: list[core.Diagnostic]) -> set[str]:
    return {issue.code for issue in issues}


def test_repository_manifests_and_pack_are_valid() -> None:
    assert GovernanceResolver.for_root(ROOT).check() == []


def test_resolution_entries_have_uniform_and_truthful_provenance() -> None:
    resolver = GovernanceResolver.for_root(ROOT)
    local_fix = resolver.resolve(mode="LOCAL_FIX")
    structural = resolver.resolve(mode="STRUCTURAL_CHANGE")
    for resolved in (local_fix, structural):
        assert resolved["entries"]
        assert all(
            set(item) == {"value", "owner", "source"}
            for item in resolved["entries"].values()
        )
    local_entries = local_fix["entries"]
    structural_entries = structural["entries"]
    assert local_entries["execution.mode"]["value"] == "LOCAL_FIX"
    assert local_entries["execution.mode"]["source"].endswith("#/execution")
    assert (
        local_entries["execution.exploration"]
        != structural_entries["execution.exploration"]
    )
    assert local_entries["verification.full"] == structural_entries["verification.full"]
    assert (
        local_entries["verification.rule"]["value"]
        == manifests()[1]["verification"]["rule"]
    )
    assert local_entries["verification.full"]["source"].endswith(
        "#/governance/godot_toolchain/canonical_commands/full_repository"
    )


@pytest.mark.parametrize(
    ("field", "resolved_key", "replacement"),
    [
        ("rule", "verification.rule", "mutated evidence rule"),
        ("targeted", "verification.targeted", "./scripts/another_targeted_gate.sh"),
    ],
)
def test_manifest_values_cannot_be_replaced_by_hardcoded_claims(
    monkeypatch: pytest.MonkeyPatch, field: str, resolved_key: str, replacement: str
) -> None:
    workspace, project = manifests()
    project["verification"][field] = replacement
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])
    monkeypatch.setattr(
        GovernanceResolver, "load", lambda self: (workspace, project, None)
    )
    entry = GovernanceResolver.for_root(ROOT).resolve()["entries"][resolved_key]
    assert entry["value"] == replacement
    assert entry["source"].endswith(f"#/verification/{field}")


@pytest.mark.parametrize(
    "authority_id", ["godot-runtime", "native-and-platform", "authority-transfer"]
)
def test_explain_stable_authority_identity(authority_id: str) -> None:
    explained = GovernanceResolver.for_root(ROOT).explain(f"authority:{authority_id}")
    value = explained["entries"][f"authority:{authority_id}"]["value"]
    assert value["authority_id"] == authority_id


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
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert route in entries["routes"]["value"]


def test_authority_identity_ambiguity_and_structured_reachability() -> None:
    workspace, project = manifests()
    duplicate = copy.deepcopy(project["authorities"][0])
    project["authorities"].append(duplicate)
    assert "DUPLICATE_AUTHORITY" in codes(validate(workspace, project))
    project["authorities"][-1]["authority_id"] = "another-owner"
    ambiguity = next(
        issue
        for issue in validate(workspace, project)
        if issue.code == "AMBIGUOUS_AUTHORITY"
    )
    assert ambiguity.fact == duplicate["scope"]
    project = manifests()[1]
    project["authorities"].append(
        {
            "authority_id": "orphan",
            "source_type": "file",
            "authority_type": "human",
            "scope": "orphan-scope",
            "source": "docs/BACKLOG.md",
            "exclusive": True,
            "canonical_governance": False,
        }
    )
    assert any("unreachable" in issue.reason for issue in validate(workspace, project))


def test_every_declared_route_is_selectable_from_an_execution_path() -> None:
    workspace, project = manifests()
    assert not [
        issue
        for issue in validate(workspace, project)
        if issue.fact.startswith("route:")
    ]
    reachable = {
        route
        for profile in project["execution"]["profiles"].values()
        for route in profile["routes"]
    } | {
        route
        for scenario in project["execution"]["representative_scenarios"]
        for route in scenario["routes"]
    }
    orphan = min(reachable)
    for profile in project["execution"]["profiles"].values():
        profile["routes"] = [item for item in profile["routes"] if item != orphan] or [
            "governance_and_tooling"
        ]
    project["execution"]["representative_scenarios"] = [
        scenario
        for scenario in project["execution"]["representative_scenarios"]
        if orphan not in scenario["routes"]
    ]
    unreachable = next(
        issue
        for issue in validate(workspace, project)
        if issue.fact == f"route:{orphan}"
    )
    assert unreachable.code == "BROKEN_REFERENCE"
    assert "unreachable" in unreachable.reason


def test_schema_is_structural_source_and_reserved_fields_are_rejected() -> None:
    workspace, project = manifests()
    workspace["undeclared"] = True
    project["undeclared"] = True
    local = {"schema_version": 1, "checkout_locations": {"tet4d": "."}}
    issues = validate(workspace, project, local)
    assert "CONFLICTING_VALUE" in codes(issues)
    assert any(issue.fact == "checkout_locations" for issue in issues)


def test_workspace_project_membership_and_route_facade_parity_are_enforced() -> None:
    workspace, project = manifests()
    workspace["projects"].append(copy.deepcopy(workspace["projects"][0]))
    assert "AMBIGUOUS_AUTHORITY" in codes(validate(workspace, project))
    workspace, project = manifests()
    project["routes"]["governance_and_tooling"]["authority_refs"].append(
        "security-sanitation"
    )
    assert any(
        issue.fact == "legacy-route-facade" and issue.code == "CONFLICTING_VALUE"
        for issue in validate(workspace, project)
    )


def test_environment_priority_is_override_then_local_then_repository_and_never_python_bin(
    tmp_path: Path,
) -> None:
    _, project = manifests()
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    preferred = tmp_path / ".venv/bin/python"
    preferred.parent.mkdir(parents=True)
    preferred.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    os.chmod(preferred, 0o755)
    interpreter, reason, issues = core.resolve_interpreter(
        tmp_path, project, None, {"PYTHON_BIN": "/invalid/legacy"}
    )
    assert interpreter == preferred.absolute()
    assert reason == "repository-local environment"
    assert issues == []
    interpreter, reason, issues = core.resolve_interpreter(
        tmp_path, project, {"interpreter": sys.executable}, {}
    )
    assert interpreter == Path(sys.executable).absolute()
    assert reason == "approved local overlay"
    assert issues == []
    interpreter, _, issues = core.resolve_interpreter(
        tmp_path,
        project,
        {"interpreter": sys.executable},
        {"TET4D_PYTHON": "/invalid/explicit"},
    )
    assert interpreter is None
    assert codes(issues) == {"ENVIRONMENT_MISMATCH"}


def test_shell_and_doctor_share_explicit_and_default_resolution() -> None:
    expected_default = subprocess.check_output(
        [str(ROOT / "gov"), "doctor", "--print-interpreter"], cwd=ROOT, text=True
    ).strip()
    shell_default = subprocess.check_output(
        [str(ROOT / "scripts/resolve_python_env.sh")], cwd=ROOT, text=True
    ).strip()
    assert shell_default == expected_default
    env = {
        **os.environ,
        "TET4D_PYTHON": sys.executable,
        "PYTHON_BIN": "/invalid/legacy",
    }
    expected_override = subprocess.check_output(
        [str(ROOT / "gov"), "doctor", "--print-interpreter"],
        cwd=ROOT,
        env=env,
        text=True,
    ).strip()
    shell_override = subprocess.check_output(
        [str(ROOT / "scripts/resolve_python_env.sh")], cwd=ROOT, env=env, text=True
    ).strip()
    assert shell_override == expected_override == str(Path(sys.executable).absolute())


def test_workspace_local_override_is_used_by_cli_and_shell(tmp_path: Path) -> None:
    (tmp_path / ".governance").mkdir()
    (tmp_path / "config/governance").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "tools").mkdir()
    shutil.copytree(PACK_ROOT, tmp_path / "tools/workspace_governance")
    shutil.copy2(ROOT / "gov", tmp_path / "gov")
    for name in ("resolve_python_env.sh", "resolve_bootstrap_python.sh"):
        shutil.copy2(ROOT / "scripts" / name, tmp_path / "scripts" / name)
    workspace, project = manifests()
    (tmp_path / ".governance/workspace.json").write_text(json.dumps(workspace))
    invocation_log = tmp_path / "interpreter-invocations.log"
    wrapper = tmp_path / "approved-python"
    wrapper.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$*\" >> {invocation_log!s}\n"
        f'exec {sys.executable!s} "$@"\n'
    )
    wrapper.chmod(0o755)
    (tmp_path / ".governance/workspace.local.json").write_text(
        json.dumps({"schema_version": 1, "interpreter": str(wrapper)})
    )
    (tmp_path / "config/governance/project.json").write_text(json.dumps(project))
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    (tmp_path / "src").mkdir()
    (tmp_path / "src/tet4d").symlink_to(ROOT / "src/tet4d", target_is_directory=True)
    env = {**os.environ, "GOVERNANCE_PYTHON": sys.executable}
    doctor_value = subprocess.check_output(
        [str(tmp_path / "gov"), "doctor", "--print-interpreter"],
        cwd=tmp_path,
        env=env,
        text=True,
    ).strip()
    shell_value = subprocess.check_output(
        [str(tmp_path / "scripts/resolve_python_env.sh")],
        cwd=tmp_path,
        env=env,
        text=True,
    ).strip()
    assert doctor_value == shell_value == str(wrapper.absolute())
    invocations = invocation_log.read_text().splitlines()
    assert (
        sum(
            "from packaging.specifiers import SpecifierSet" in line
            for line in invocations
        )
        == 2
    )


def test_doctor_detects_wrong_checkout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _, project = manifests()
    fake = tmp_path / ".venv/bin/python"
    fake.parent.mkdir(parents=True)
    shutil.copy2(sys.executable, fake)
    os.chmod(fake, 0o755)
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')

    def fake_run(command: list[str], **_: object) -> SimpleNamespace:
        if "from packaging.specifiers import SpecifierSet" in command[-1]:
            return SimpleNamespace(returncode=0, stdout="3.14.0\n", stderr="")
        payload = {
            "version": "3.14.0",
            "package": str(tmp_path / "elsewhere/tet4d/__init__.py"),
            "critical_packages": ["tet4d"],
        }
        return SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(core.subprocess, "run", fake_run)
    _, issues = core.doctor(tmp_path, project, None, {})
    assert any(
        issue.fact == "editable_install" and issue.code == "ENVIRONMENT_MISMATCH"
        for issue in issues
    )


def test_pack_hash_policy_excludes_declared_files_and_lock_identity_is_manifest_owned(
    tmp_path: Path,
) -> None:
    pack = tmp_path / "pack"
    (pack / "nested").mkdir(parents=True)
    (pack / "VERSION").write_text("0.1.0\n")
    manifest = {
        "schema_version": 1,
        "name": "workspace-governance",
        "version": "0.1.0",
        "revision": "test-revision",
        "version_file": "VERSION",
        "lock_algorithm": "sha256-path-and-content-v1",
        "pack_hash_excludes": ["**/*.pyc"],
        "commands": sorted(core.SUPPORTED_COMMANDS),
        "diagnostics": sorted(core.DIAGNOSTIC_CLASSES),
    }
    manifest["field_usage"] = {key: "consumed" for key in (*manifest, "field_usage")}
    (pack / "MANIFEST.json").write_text(json.dumps(manifest))
    (pack / "nested/cache.pyc").write_text("ignored")
    first, files = core.pack_hash(pack)
    (pack / "nested/cache.pyc").write_text("changed")
    assert core.pack_hash(pack)[0] == first
    assert "nested/cache.pyc" not in files
    workspace = {"governance_pack": {"required_schema": 1, "lock": "lock.json"}}
    lock = {
        "pack_path": "pack",
        "pack_name": manifest["name"],
        "version": manifest["version"],
        "revision": manifest["revision"],
        "content_sha256": first,
        "files": files,
        "lock_algorithm": manifest["lock_algorithm"],
    }
    (tmp_path / "lock.json").write_text(json.dumps(lock))
    assert core.validate_pack(tmp_path, workspace) == []


def test_sync_refuses_to_invent_a_missing_pack_path(tmp_path: Path) -> None:
    (tmp_path / "lock.json").write_text(json.dumps({"pack_path": "missing"}))
    resolver = SimpleNamespace(
        load=lambda: ({"governance_pack": {"lock": "lock.json"}}, {}, None)
    )
    with pytest.raises(ValueError, match="locked pack path does not exist"):
        _sync(tmp_path, resolver)  # type: ignore[arg-type]


def test_cli_accepts_json_in_both_positions_and_missing_explain_is_usage_error() -> (
    None
):
    for args in (["--json", "resolve"], ["resolve", "--json"]):
        result = subprocess.run(
            [str(ROOT / "gov"), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["schema_version"] == 1
    missing = subprocess.run(
        [str(ROOT / "gov"), "explain"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode == 2
    assert missing.stderr.startswith("usage:")
    assert "BROKEN_REFERENCE" not in missing.stdout + missing.stderr
