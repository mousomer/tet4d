from __future__ import annotations

import copy
import itertools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from support import scrubbed_environment

from tools.workspace_governance.cli.gov import _sync
from tools.workspace_governance.resolver.core import GovernanceError, GovernanceResolver
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


def test_work_type_and_artifact_role_schema_is_additive_until_migration() -> None:
    workspace, project = manifests()
    project["work_types"] = ["Planning", "Coding", "Manifest"]
    project["artifact_roles"] = {
        "docs/ARCHITECTURE_CONTRACT.md": "product_authority",
        "CURRENT_STATE.md": "bookkeeping",
    }
    assert validate(workspace, project) == []

    project["work_types"] = ["Planning", "Coding", "Verification"]
    assert any(issue.fact == "work_types[2]" for issue in validate(workspace, project))

    project["work_types"] = ["Planning", "Coding", "Manifest"]
    project["artifact_roles"]["CURRENT_STATE.md"] = "route_membership"
    assert any(
        issue.fact == "artifact_roles.CURRENT_STATE.md"
        for issue in validate(workspace, project)
    )


@pytest.mark.parametrize(
    ("path", "role", "code"),
    [
        ("../outside.md", "planning_document", "CONFLICTING_VALUE"),
        ("docs/**/*.md", "planning_document", "CONFLICTING_VALUE"),
        ("/docs/BACKLOG.md", "bookkeeping", "CONFLICTING_VALUE"),
        ("does/not/exist.md", "planning_document", "BROKEN_REFERENCE"),
        (
            "tools/workspace_governance/policies/ownership.md",
            "executable_machinery",
            "CONFLICTING_VALUE",
        ),
        ("config/governance/project.json", "executable_machinery", "CONFLICTING_VALUE"),
        ("config/governance/workspace.lock.json", "bookkeeping", "CONFLICTING_VALUE"),
        ("AGENTS.md", "bookkeeping", "CONFLICTING_VALUE"),
        ("AGENTS.md", "governance_treatment", None),
    ],
)
def test_project_role_declarations_cannot_escape_relabel_roots_or_claim_the_pack(
    path: str, role: str, code: str | None
) -> None:
    workspace, project = manifests()
    project["artifact_roles"] = {path: role}
    issues = [
        i for i in validate(workspace, project) if i.fact == f"artifact_roles.{path}"
    ]
    assert [i.code for i in issues] == ([code] if code else [])


def test_role_bootstrap_paths_are_single_existing_files_outside_fixed_roots() -> None:
    workspace, project = manifests()
    assert validate(workspace, project) == []

    duplicated = copy.deepcopy(project)
    duplicated["role_bootstrap"]["bookkeeping"].append("AGENTS.md")
    assert any(
        i.fact.startswith("role_bootstrap.bookkeeping")
        and i.code == "CONFLICTING_VALUE"
        for i in validate(workspace, duplicated)
    )
    root_as_record = copy.deepcopy(project)
    root_as_record["role_bootstrap"]["bookkeeping"].append(
        "config/governance/project.json"
    )
    assert any(
        i.fact.startswith("role_bootstrap.bookkeeping") and "fixed role" in i.reason
        for i in validate(workspace, root_as_record)
    )
    missing = copy.deepcopy(project)
    missing["role_bootstrap"]["instruction_roots"].append("missing/AGENTS.md")
    assert any(
        i.fact.startswith("role_bootstrap.instruction_roots")
        and i.code == "BROKEN_REFERENCE"
        for i in validate(workspace, missing)
    )


def test_pack_metadata_is_complete_and_directional() -> None:
    manifest = json.loads((PACK_ROOT / "MANIFEST.json").read_text())
    _, files = core.pack_hash(PACK_ROOT)
    assert core._pack_metadata_issues(manifest, files) == []

    weakened = copy.deepcopy(manifest)
    weakened["obligation_comparators"]["required_all_of"] = "set_subset"
    assert any(
        issue.fact == "MANIFEST.obligation_comparators"
        for issue in core._pack_metadata_issues(weakened, files)
    )

    missing_role = copy.deepcopy(manifest)
    missing_role["artifact_roles"].pop()
    assert any(
        issue.fact == "MANIFEST.artifact_roles"
        for issue in core._pack_metadata_issues(missing_role, files)
    )

    relaxed = copy.deepcopy(manifest)
    relaxed["write_compatibility"]["Coding"]["governance_treatment"] = "allowed"
    assert any(
        issue.fact == "MANIFEST.write_compatibility"
        for issue in core._pack_metadata_issues(relaxed, files)
    )

    for roots in (
        [root for root in manifest["bootstrap_roots"] if root != "validators/core.py"],
        [*manifest["bootstrap_roots"], "not/packed.py"],
        [*manifest["bootstrap_roots"], manifest["bootstrap_roots"][0]],
    ):
        unrooted = copy.deepcopy(manifest)
        unrooted["bootstrap_roots"] = roots
        assert any(
            issue.fact == "MANIFEST.bootstrap_roots"
            for issue in core._pack_metadata_issues(unrooted, files)
        )


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


@pytest.mark.parametrize(
    ("task", "mode", "routes"),
    [
        (
            (
                "Fix the validation-label styling regression in the Godot shell. "
                "This is a small presentation bug. Reproduce it, patch the owning "
                "scene/script, and run focused Godot tests."
            ),
            "LOCAL_FIX",
            {"godot_product_shell"},
        ),
        (
            (
                "Add a bounded Godot presentation feature for the setup flow. "
                "It must not change gameplay semantics."
            ),
            "FEATURE",
            {"godot_product_shell"},
        ),
        (
            (
                "Repair product/platform routing so CI classification selects "
                "the correct platform checks and conservative fallback."
            ),
            "STRUCTURAL_CHANGE",
            {"governance_and_tooling", "packaging_and_release"},
        ),
        (
            "CI/product-platform routing repair",
            "STRUCTURAL_CHANGE",
            {"governance_and_tooling", "packaging_and_release"},
        ),
    ],
    ids=(
        "godot-local-fix",
        "godot-feature",
        "ci-routing-repair",
        "product-platform-routing-repair",
    ),
)
def test_corrected_representative_scenarios(
    task: str, mode: str, routes: set[str]
) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert set(entries["routes"]["value"]) == routes


@pytest.mark.parametrize(
    ("task", "mode", "routes", "scenario"),
    [
        (
            "Add a small Godot debug overlay presentation feature",
            "FEATURE",
            {"godot_product_shell"},
            "godot-presentation-feature",
        ),
        (
            "Cross-layer change to the decision platform routing",
            "STRUCTURAL_CHANGE",
            {
                "python_reference_engine",
                "godot_product_shell",
                "native_deterministic_core",
            },
            "cross-layer-change",
        ),
        (
            "Governance change: specific platform routing table",
            "STRUCTURAL_CHANGE",
            {"governance_and_tooling"},
            "governance-change",
        ),
        (
            "Small Python bug fix in godot export notes",
            "LOCAL_FIX",
            {"python_reference_engine"},
            "python-bug-fix",
        ),
        (
            "Cross-layer CI classification repair for platform routing",
            "STRUCTURAL_CHANGE",
            {
                "python_reference_engine",
                "godot_product_shell",
                "native_deterministic_core",
            },
            "cross-layer-change",
        ),
    ],
    ids=(
        "debug-not-bug",
        "decision-not-ci",
        "specific-not-ci",
        "python-not-godot",
        "cross-layer-precedence",
    ),
)
def test_representative_scenario_shadowing_regressions(
    task: str, mode: str, routes: set[str], scenario: str
) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert set(entries["routes"]["value"]) == routes
    assert entries["matched_scenario"]["value"] == scenario


@pytest.mark.parametrize(
    ("task", "mode", "routes", "scenario"),
    [
        (
            "Cross-layer Python bug fix",
            "STRUCTURAL_CHANGE",
            {
                "python_reference_engine",
                "godot_product_shell",
                "native_deterministic_core",
            },
            "cross-layer-change",
        ),
        (
            "Cross-layer Godot presentation feature",
            "STRUCTURAL_CHANGE",
            {
                "python_reference_engine",
                "godot_product_shell",
                "native_deterministic_core",
            },
            "cross-layer-change",
        ),
        (
            "Small Godot defect in the presentation feature for setup",
            "LOCAL_FIX",
            {"godot_product_shell"},
            "small-godot-ui-defect",
        ),
        (
            "Moderate Godot presentation feature for the setup flow",
            "FEATURE",
            {"godot_product_shell"},
            "godot-presentation-feature",
        ),
        (
            "Governance change for the packaging release pipeline",
            "STRUCTURAL_CHANGE",
            {"packaging_and_release"},
            "packaging-release-change",
        ),
        (
            "Python bug fix in scoring",
            "LOCAL_FIX",
            {"python_reference_engine"},
            "python-bug-fix",
        ),
        (
            "Godot presentation feature for setup",
            "FEATURE",
            {"godot_product_shell"},
            "godot-presentation-feature",
        ),
    ],
    ids=(
        "cross-layer-python-bug-fix",
        "cross-layer-godot-presentation-feature",
        "small-godot-defect-over-presentation-feature",
        "godot-presentation-feature-over-moderate-feature",
        "packaging-release-over-governance",
        "ordinary-python-bug-fix",
        "ordinary-godot-presentation-feature",
    ),
)
def test_scenario_priority_matrix(
    task: str, mode: str, routes: set[str], scenario: str
) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert set(entries["routes"]["value"]) == routes
    assert entries["matched_scenario"]["value"] == scenario


@pytest.mark.parametrize(
    ("task", "expected_scenario", "decision"),
    [
        (
            "Fix the small godot defect in validation-label styling",
            "godot-validation-label-regression",
            "named validation-label repair over generic Godot defect",
        ),
        (
            "Small godot defect: fix the live 4d rosette seam",
            "live-4d-rosette-fix",
            "named rosette repair over generic Godot defect",
        ),
        (
            "CI classification and platform routing repair for product-platform routing",
            "ci-platform-routing-repair",
            "CI classification repair over broader product-platform routing repair",
        ),
        (
            "Small python defect; this is a python bug fix",
            "python-bug-fix",
            "explicit Python bug-fix contract over generic Python defect",
        ),
        (
            "Product planning for the topology explorer",
            "topology-explorer-change",
            "named topology subsystem over generic product planning",
        ),
        (
            "Godot presentation feature for the topology explorer",
            "topology-explorer-change",
            "named topology subsystem over generic Godot presentation feature",
        ),
    ],
    ids=(
        "validation-label-over-generic-godot",
        "rosette-over-generic-godot",
        "ci-over-product-platform-routing",
        "python-bug-over-generic-python",
        "topology-over-product-planning",
        "topology-over-godot-presentation",
    ),
)
def test_deliberately_reviewed_overlap_policy(
    task: str, expected_scenario: str, decision: str
) -> None:
    del decision  # Documents why the expected winner is policy, not arithmetic.
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["matched_scenario"]["value"] == expected_scenario


def test_packaging_and_godot_presentation_overlap_is_intentionally_ambiguous() -> None:
    task = "Godot presentation feature for the packaging release bundle"

    with pytest.raises(GovernanceError) as error:
        GovernanceResolver.for_root(ROOT).resolve(task=task)

    diagnostic = error.value.diagnostics[0]
    assert diagnostic.code == "AMBIGUOUS_AUTHORITY"
    assert "godot-presentation-feature" in diagnostic.reason
    assert "packaging-release-change" in diagnostic.reason


def test_every_declared_scenario_resolves_standalone() -> None:
    resolver = GovernanceResolver.for_root(ROOT)
    scenarios = manifests()[1]["execution"]["representative_scenarios"]
    for scenario in scenarios:
        task = " ".join(scenario["match_all"])
        entries = resolver.resolve(task=task)["entries"]
        assert entries["matched_scenario"]["value"] == scenario["id"]
        assert entries["execution.mode"]["value"] == scenario["mode"]
        assert set(entries["routes"]["value"]) == set(scenario["routes"])


def test_all_declared_scenario_pairs_have_explicit_overlap_outcomes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = manifests()
    scenarios = project["execution"]["representative_scenarios"]
    resolver = GovernanceResolver.for_root(ROOT)
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])

    for left, right in itertools.combinations(scenarios, 2):
        pair_project = copy.deepcopy(project)
        pair_project["execution"]["representative_scenarios"] = [left, right]
        monkeypatch.setattr(
            GovernanceResolver,
            "load",
            lambda self, pair_project=pair_project: (workspace, pair_project, None),
        )
        representative = " ".join(dict.fromkeys(left["match_all"] + right["match_all"]))

        if left["priority"] == right["priority"]:
            with pytest.raises(GovernanceError) as error:
                resolver.resolve(task=representative)
            assert error.value.diagnostics[0].code == "AMBIGUOUS_AUTHORITY"
        else:
            winner = max((left, right), key=lambda scenario: scenario["priority"])
            entries = resolver.resolve(task=representative)["entries"]
            assert entries["matched_scenario"]["value"] == winner["id"]
            assert entries["matched_scenario_priority"]["value"] == winner["priority"]


def test_flattened_priorities_break_representative_overlap_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = manifests()
    flattened = copy.deepcopy(project)
    for scenario in flattened["execution"]["representative_scenarios"]:
        scenario["priority"] = 100
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])
    monkeypatch.setattr(
        GovernanceResolver, "load", lambda self: (workspace, flattened, None)
    )

    overlaps = (
        "Cross-layer Python bug fix",
        "Cross-layer Godot presentation feature",
        "Small Godot defect in the presentation feature for setup",
        "Moderate Godot presentation feature for the setup flow",
        "Governance change for the packaging release pipeline",
    )
    resolver = GovernanceResolver.for_root(ROOT)
    for task in overlaps:
        with pytest.raises(GovernanceError) as error:
            resolver.resolve(task=task)
        assert error.value.diagnostics[0].code == "AMBIGUOUS_AUTHORITY"


def test_scenario_declaration_reordering_does_not_change_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolver = GovernanceResolver.for_root(ROOT)
    task = "Cross-layer Godot presentation feature"
    expected = resolver.resolve(task=task)
    workspace, project, local = resolver.load()
    project["execution"]["representative_scenarios"].reverse()
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])
    monkeypatch.setattr(
        GovernanceResolver, "load", lambda self: (workspace, project, local)
    )
    assert resolver.resolve(task=task) == expected


def test_equal_highest_scenario_priorities_are_ambiguous(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace, project = manifests()
    project["execution"]["representative_scenarios"].extend(
        [
            {
                "id": "tie-a",
                "match_all": ["deliberate tie"],
                "mode": "LOCAL_FIX",
                "priority": 999,
                "routes": ["python_reference_engine"],
            },
            {
                "id": "tie-b",
                "match_all": ["deliberate tie"],
                "mode": "FEATURE",
                "priority": 999,
                "routes": ["godot_product_shell"],
            },
        ]
    )
    monkeypatch.setattr(GovernanceResolver, "check", lambda self: [])
    monkeypatch.setattr(
        GovernanceResolver, "load", lambda self: (workspace, project, None)
    )

    with pytest.raises(GovernanceError) as error:
        GovernanceResolver.for_root(ROOT).resolve(task="A deliberate tie")

    assert error.value.diagnostics[0].code == "AMBIGUOUS_AUTHORITY"
    assert "tie-a, tie-b" in error.value.diagnostics[0].reason


@pytest.mark.parametrize("priority", [-1, True, "high", None])
def test_scenario_priority_schema_rejects_invalid_values(priority: object) -> None:
    workspace, project = manifests()
    project["execution"]["representative_scenarios"][0]["priority"] = priority
    issues = validate(workspace, project)
    assert any(
        issue.fact.endswith("representative_scenarios[0].priority")
        and issue.code == "CONFLICTING_VALUE"
        for issue in issues
    )


def _normalized_markdown(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_dispatcher_points_to_canonical_impact_driven_documentation_rule() -> None:
    dispatcher = _normalized_markdown(ROOT / "AGENTS.md")
    governance = _normalized_markdown(ROOT / "docs/governance/CHANGE_GOVERNANCE.md")

    assert (
        "Update the owning design source and `docs/BACKLOG.md` for repository changes."
        not in dispatcher
    )
    assert "defined canonically in `docs/governance/CHANGE_GOVERNANCE.md`" in dispatcher
    assert (
        "A behaviour change requires appropriate regression or behavioural evidence in every execution mode"
        in governance
    )
    assert "documented behaviour changes, update that authority" in governance
    assert (
        "does not require an authority rewrite solely because its implementation changed"
        in governance
    )
    assert (
        "Update documentation, design authorities, RDS material, and the backlog when the patch changes documented behaviour"
        in governance
    )
    assert (
        "does not require documentation or backlog churn solely because source changed"
        in governance
    )
    assert "Execution mode controls discovery and exploration cost" in governance


def test_dispatcher_treats_resolved_stable_facts_as_sufficient() -> None:
    dispatcher = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    assert "Resolved stable facts with provenance are sufficient" in dispatcher
    assert "ambiguity/conflict" in dispatcher
    assert "boundary/escalation" in dispatcher
    assert "provenance audit" in dispatcher
    assert "authority edits" in dispatcher


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


def test_shell_and_doctor_share_explicit_and_default_resolution(
    isolated_user_overlay: Path,
) -> None:
    # Declare the inherited tier this case treats as "default". The suite
    # isolates the host overlay, and a worktree need no longer carry a `.venv`,
    # so without a declaration here there is no tier left to resolve and the
    # comparison would have nothing to compare.
    overlay = isolated_user_overlay / "workspace-governance/tet4d-workspace.local.json"
    overlay.parent.mkdir(parents=True, exist_ok=True)
    overlay.write_text(
        json.dumps({"schema_version": 1, "interpreter": sys.executable}) + "\n"
    )

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
    # Scrubbed: this asserts the overlay tier, which an ambient TET4D_PYTHON
    # would outrank.
    env = scrubbed_environment(GOVERNANCE_PYTHON=sys.executable)
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
    for enforcement in ("resolver/roles.py", "validators/core.py"):
        (pack / enforcement).parent.mkdir(parents=True, exist_ok=True)
        (pack / enforcement).write_text("")
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
        "work_types": ["Planning", "Coding", "Manifest"],
        "artifact_roles": [
            {"path": "MANIFEST.json", "role": "executable_machinery"},
            {"path": "VERSION", "role": "executable_machinery"},
            {"path": "resolver/roles.py", "role": "executable_machinery"},
            {"path": "validators/core.py", "role": "executable_machinery"},
        ],
        "bootstrap_roots": sorted(core.REQUIRED_PACK_ROOTS),
        "obligation_comparators": core.OBLIGATION_COMPARATORS,
        "write_compatibility": core.WRITE_COMPATIBILITY,
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
    # `resolve` needs no project environment, but `gov` still needs something to
    # start under, and a worktree need no longer carry a `.venv`.
    env = scrubbed_environment(GOVERNANCE_PYTHON=sys.executable)
    for args in (["--json", "resolve"], ["resolve", "--json"]):
        result = subprocess.run(
            [str(ROOT / "gov"), *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)["schema_version"] == 1
    missing = subprocess.run(
        [str(ROOT / "gov"), "explain"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert missing.returncode == 2
    assert missing.stderr.startswith("usage:")
    assert "BROKEN_REFERENCE" not in missing.stdout + missing.stderr
