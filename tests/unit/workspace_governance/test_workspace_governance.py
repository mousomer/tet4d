from __future__ import annotations

import copy
import itertools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from support import scrubbed_environment

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


@pytest.mark.canonical_gate_environment
def test_git_visible_checkout_preserves_declared_adapters(checkout: Path) -> None:
    shutil.copy2(ROOT / ".gitignore", checkout / ".gitignore")
    subprocess.run(["git", "init", "-q"], cwd=checkout, check=True)
    private = checkout / ".claude/settings.local.json"
    private.write_text('{"private": true}\n')
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.excludesFile=/dev/null",
            "ls-files",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=checkout,
        capture_output=True,
        text=True,
        check=True,
    )
    visible = set(result.stdout.split("\0"))
    manifest = json.loads((checkout / "config/governance/project.json").read_text())
    adapters = {adapter["path"] for adapter in manifest["skill_adapters"]}
    # The export boundary must be checked before builder-provided adapters can
    # hide ignored inputs from ordinary context validation.
    assert adapters <= visible
    assert private.relative_to(checkout).as_posix() not in visible
    for path in checkout.rglob("*"):
        if (
            path.is_file()
            and not path.is_symlink()
            and ".git" not in path.parts
            and path.relative_to(checkout).as_posix() not in visible
        ):
            path.unlink()
    assert GovernanceResolver.for_root(checkout).check() == []


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
        ("moderate feature", "FEATURE", "godot_product_shell"),
        ("cross-layer change", "STRUCTURAL_CHANGE", "native_deterministic_core"),
        ("governance change", "STRUCTURAL_CHANGE", "governance_and_tooling"),
        ("packaging release change", "STRUCTURAL_CHANGE", "packaging_and_release"),
    ],
)
def test_representative_scenarios(task: str, mode: str, route: str) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert route in entries["routes"]["value"]


# Routing boundary: unqualified product work defaults to the shipped Godot
# product; work for the Python reference engine or oracle must name that surface.
# The old Python fallback was never pinned ("moderate feature" matches its own
# scenario), so these tests pin the boundary itself.
@pytest.mark.parametrize(
    "task",
    [
        "fix(godot): make Live-4D right-drag follow the pointer under reflection",
        "Repair Stage 56G real-window responsive acceptance",
        "Complete Stage 56G responsive cockpit acceptance",
        "Harden the Godot test harness and eliminate test-fixture teardown leaks",
        (
            "Stage 56H: sustained playability, key/action legibility, and "
            "HOLD/NEXT emphasis"
        ),
        "Stage 56I bounded cockpit polish",
        "improve topology replay parity",
    ],
)
def test_unqualified_product_work_routes_to_the_godot_product(task: str) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert list(entries["routes"]["value"]) == ["godot_product_shell"]


@pytest.mark.parametrize(
    "task",
    [
        "improve Python oracle topology replay parity",
        "Fix a rotation bug in the reference engine",
        "Tighten the oracle trace comparison",
        "Harden the Python reference engine oracle boundary",
    ],
)
def test_naming_the_python_surface_routes_to_the_reference_engine(task: str) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert list(entries["routes"]["value"]) == ["python_reference_engine"]


def test_local_fix_without_a_scenario_routes_to_the_godot_product() -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(mode="LOCAL_FIX")["entries"]
    assert list(entries["routes"]["value"]) == ["godot_product_shell"]


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


def test_frozen_manifest_repair_acceptance_cases() -> None:
    cases = json.loads(
        (
            ROOT / "docs/experiments/governance_repair_acceptance_2026_10.json"
        ).read_text()
    )
    for case in cases["routing"]:
        entries = GovernanceResolver.for_root(ROOT).resolve(task=case["task"])[
            "entries"
        ]
        actual = set(entries["routes"]["value"])
        if "expected_routes" in case:
            assert actual == set(case["expected_routes"]), case["id"]
        else:
            assert set(case["required_routes"]) <= actual, case["id"]


def test_named_real_godot_file_cannot_be_hidden_by_python_only_wording() -> None:
    # Additional post-discovery regression, not an independent behavioral holdout.
    path = "godot/Tet4D.Godot/scripts/presentation/presentation_profile.gd"
    assert (ROOT / path).is_file()
    entries = GovernanceResolver.for_root(ROOT).resolve(
        task=f"Python-only change in {path}"
    )["entries"]
    assert "godot_product_shell" in entries["routes"]["value"]


def test_named_file_preserves_explicit_cross_layer_provider_consumer_routes() -> None:
    # Post-discovery overlap regression; not an independent holdout.
    entries = GovernanceResolver.for_root(ROOT).resolve(
        task="Cross-layer change in godot/Tet4D.Godot/scripts/presentation/presentation_profile.gd"
    )["entries"]
    assert set(entries["routes"]["value"]) == {
        "godot_product_shell",
        "python_reference_engine",
        "native_deterministic_core",
    }


# Post-review regressions (2026-10-28), not independent holdouts: an owner path
# must not capture another tree's "godot/" segment, must not widen a small fix's
# mode, and mixed runtime/path evidence must keep every owner's route.
@pytest.mark.parametrize(
    ("task", "mode", "routes"),
    [
        (
            "Packaging release change for packaging/godot/export_presets.cfg",
            "STRUCTURAL_CHANGE",
            {"packaging_and_release"},
        ),
        (
            "Fix a small Godot defect in godot/Tet4D.Godot/scripts/presentation/presentation_profile.gd",
            "LOCAL_FIX",
            {"godot_product_shell"},
        ),
        (
            "Add a moderate feature to src/tet4d/engine/board.py",
            "FEATURE",
            {"python_reference_engine"},
        ),
        (
            "Moderate feature in native/tet4d_core/",
            "FEATURE",
            {"native_deterministic_core"},
        ),
        (
            "Small Godot defect in src/tet4d/engine/board.py",
            "FEATURE",
            {
                "godot_product_shell",
                "python_reference_engine",
                "native_deterministic_core",
            },
        ),
        (
            "Small Python defect in godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd",
            "FEATURE",
            {
                "godot_product_shell",
                "python_reference_engine",
                "native_deterministic_core",
            },
        ),
    ],
)
def test_named_owner_paths_compose_without_capturing_other_routes(
    task: str, mode: str, routes: set[str]
) -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    assert entries["execution.mode"]["value"] == mode
    assert set(entries["routes"]["value"]) == routes


_CODE_ROUTES = {
    "godot_product_shell",
    "python_reference_engine",
    "native_deterministic_core",
}
_OWNER_PATHS = {
    "godot/Tet4D.Godot/export_presets.cfg": "godot_product_shell",
    "src/tet4d/engine/board.py": "python_reference_engine",
    "native/tet4d_core/src/board.cpp": "native_deterministic_core",
}
_NON_CODE_SCENARIOS = [
    scenario
    for scenario in json.loads((ROOT / "config/governance/project.json").read_text())[
        "execution"
    ]["representative_scenarios"]
    if not set(scenario["routes"]) & _CODE_ROUTES
]


# Post-review overlap regressions (2026-10-28): a named owner path adds its
# route to a non-code scenario and keeps that scenario's mode, including when
# the brief also names a runtime.
@pytest.mark.parametrize(
    ("scenario", "path", "wording"),
    [
        (scenario, path, wording)
        for scenario in _NON_CODE_SCENARIOS
        for path in _OWNER_PATHS
        for wording in ("", " python", " godot")
    ],
    ids=lambda value: value["id"] if isinstance(value, dict) else value,
)
def test_named_owner_path_composes_with_non_code_scenarios(
    scenario: dict[str, object], path: str, wording: str
) -> None:
    task = f"{' '.join(scenario['match_all'])}{wording} for {path}"
    entries = GovernanceResolver.for_root(ROOT).resolve(task=task)["entries"]
    routes = set(entries["routes"]["value"])
    assert entries["execution.mode"]["value"] == scenario["mode"], task
    assert set(scenario["routes"]) <= routes, task
    assert _OWNER_PATHS[path] in routes, task


def test_reported_packaging_overlap_keeps_packaging_and_godot() -> None:
    entries = GovernanceResolver.for_root(ROOT).resolve(
        task="Packaging release change for godot/Tet4D.Godot/export_presets.cfg"
    )["entries"]
    assert entries["execution.mode"]["value"] == "STRUCTURAL_CHANGE"
    assert set(entries["routes"]["value"]) == {
        "packaging_and_release",
        "godot_product_shell",
    }
