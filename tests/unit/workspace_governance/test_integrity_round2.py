from __future__ import annotations

import copy
import importlib.metadata
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from support import PACK, ROOT, build_checkout, write

from tools.workspace_governance.cli.gov import main
from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core

CATALOG = json.loads((PACK / "synthetic-fixtures/contradictions.json").read_text())
USAGE = json.loads((PACK / "field-usage.json").read_text())


def environment(**updates: str) -> dict[str, str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if k
        not in {
            "TET4D_PYTHON",
            "GOVERNANCE_PYTHON",
            "PYTHON_BIN",
            "TET4D_RESOLVED_PYTHON",
        }
    }
    return {**env, **updates}


def run(
    root: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=root,
        env=environment() if env is None else env,
        text=True,
        capture_output=True,
        check=False,
    )


def wrapper(root: Path, *, no_site: bool = False) -> Path:
    path = root / "selected-python"
    path.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" ' + ("-S " if no_site else "") + '"$@"\n'
    )
    path.chmod(0o755)
    return path


def test_packaging_is_an_explicit_installed_runtime_dependency() -> None:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet

    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
        "dependencies"
    ]
    declared = [Requirement(d) for d in deps if Requirement(d).name == "packaging"]
    installed = [Requirement(d) for d in importlib.metadata.requires("tet4d") or []]
    assert len(declared) == 1
    assert any(d.name == "packaging" for d in installed)
    assert importlib.metadata.version("packaging") in declared[0].specifier
    assert str(SpecifierSet(">=3.11")) == ">=3.11"


def test_dependency_light_bootstrap_and_missing_project_dependency(
    checkout: Path,
) -> None:
    selected = wrapper(checkout, no_site=True)
    env = environment(GOVERNANCE_PYTHON=str(selected), TET4D_PYTHON=str(selected))
    checked = run(checkout, "./gov", "check", "--json", env=env)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    for args in (("./gov", "doctor", "--json"), ("./scripts/verify.sh",)):
        result = run(checkout, *args, env=env)
        assert result.returncode != 0
        assert "ENVIRONMENT_MISMATCH" in result.stdout + result.stderr
        assert "Traceback" not in result.stdout + result.stderr
    diagnosed = run(checkout, "./gov", "doctor", "--json", env=env)
    assert json.loads(diagnosed.stdout)["status"] == "ENVIRONMENT_INVALID"


def test_system_bootstrap_diagnoses_missing_environment_without_becoming_project_python(
    checkout: Path,
) -> None:
    # System Python on PATH is not an approved bootstrap: refuse it, never adopt it.
    refused = run(checkout, "./gov", "doctor", "--json")
    assert refused.returncode == 1
    assert "ENVIRONMENT_MISMATCH" in refused.stderr
    assert "bootstrap.interpreter" in refused.stderr
    assert "Traceback" not in refused.stdout + refused.stderr
    # With an approved bootstrap and no project environment, doctor still diagnoses,
    # and that bootstrap is equally incapable of becoming project authority.
    result = run(
        checkout,
        "./gov",
        "doctor",
        "--json",
        env=environment(GOVERNANCE_PYTHON=sys.executable),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "ENVIRONMENT_INVALID"
    assert data["interpreter"] is None
    assert data["diagnostics"][0]["fact"] == "python.interpreter"


def test_bootstrap_floor_is_derived_from_project_metadata(checkout: Path) -> None:
    path = checkout / "pyproject.toml"
    path.write_text('[project]\nrequires-python = ">=99.0"\n')
    result = run(
        checkout, "./gov", "doctor", env=environment(GOVERNANCE_PYTHON=sys.executable)
    )
    assert result.returncode == 1
    assert ">=99.0" in result.stderr and "bootstrap.interpreter" in result.stderr
    assert "Traceback" not in result.stderr


def test_resolver_is_print_only_and_documented_command_executes(checkout: Path) -> None:
    env = environment(TET4D_PYTHON=sys.executable, GOVERNANCE_PYTHON=sys.executable)
    rejected = run(checkout, "./scripts/resolve_python_env.sh", "ignored.py", env=env)
    assert rejected.returncode == 2 and not rejected.stdout
    result = run(
        checkout,
        "bash",
        "-c",
        '"$(./scripts/resolve_python_env.sh)" -c "print(42)"',
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "42"


@pytest.mark.parametrize(
    "error",
    [
        ModuleNotFoundError("packaging"),
        ImportError("dependency"),
        KeyError("requires-python"),
        StopIteration(),
    ],
)
def test_metadata_failure_classes_are_controlled(
    checkout: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    error: Exception,
) -> None:
    def fail(*args: object) -> None:
        raise error

    monkeypatch.setattr(core, "_python_specifier", fail)
    _, project, _ = GovernanceResolver.for_root(checkout).load()
    data, issues = core.doctor(
        checkout, project, None, {"TET4D_PYTHON": sys.executable}
    )
    assert data["status"] == "ENVIRONMENT_INVALID"
    assert {i.code for i in issues} == {"ENVIRONMENT_MISMATCH"}
    assert main(["--root", str(checkout), "doctor", "--json"]) == 1
    assert "Traceback" not in capsys.readouterr().out


@pytest.mark.parametrize("operation", ["unflag", "remove"])
def test_each_canonical_owner_is_protected(checkout: Path, operation: str) -> None:
    resolver = GovernanceResolver.for_root(checkout)
    workspace, project, _ = resolver.load()
    owners = [a for a in project["authorities"] if a["canonical_governance"]]
    assert owners
    for owner in owners:
        changed = copy.deepcopy(project)
        entry = next(
            a
            for a in changed["authorities"]
            if a["authority_id"] == owner["authority_id"]
        )
        if operation == "unflag":
            entry["canonical_governance"] = False
        else:
            changed["authorities"].remove(entry)
        issues = core.validate_manifests(
            checkout,
            workspace,
            changed,
            None,
            pack_root=checkout / "tools/workspace_governance",
        )
        assert any(i.fact.startswith("canonical_owner:") for i in issues), owner


def apply_case(root: Path, mutation: str) -> set[str]:  # noqa: C901 - explicit executable fixture dispatch
    resolver = GovernanceResolver.for_root(root)
    workspace, project, local = resolver.load()
    if mutation == "duplicate-exclusive-authority":
        project["authorities"].append(copy.deepcopy(project["authorities"][0]))
    elif mutation == "cross-layer-semantic-field":
        workspace["verification"] = "not workspace-owned"
    elif mutation == "broken-authority-reference":
        project["routes"]["governance_and_tooling"]["authority_refs"].append("missing")
    elif mutation == "compatibility-facade-drift":
        project["routes"]["governance_and_tooling"]["authority_refs"].append(
            "security-sanitation"
        )
    elif mutation == "modified-pack":
        (root / "tools/workspace_governance/VERSION").write_text("modified\n")
    elif mutation == "tracked-machine-path":
        project["project"]["name"] = str(Path("/") / "Users" / "example" / "private")
    elif mutation == "ambiguous-project-routing":
        workspace["projects"].append(copy.deepcopy(workspace["projects"][0]))
    elif mutation in {
        "missing-interpreter",
        "wrong-python-version",
        "wrong-editable-checkout",
        "valid-local-override",
    }:
        env = {"TET4D_PYTHON": sys.executable}
        if mutation == "missing-interpreter":
            env["TET4D_PYTHON"] = str(root / "missing")
        elif mutation == "wrong-python-version":
            (root / "pyproject.toml").write_text(
                '[project]\nrequires-python = ">=99"\n'
            )
        elif mutation == "wrong-editable-checkout":
            project["environment"]["editable_source"] = "wrong/source"
        else:
            local, env = {"interpreter": sys.executable}, {}
        _, issues = core.doctor(root, project, local, env)
        return {i.code for i in issues}
    elif mutation == "valid-local-fix-resolution":
        assert (
            resolver.resolve(mode="LOCAL_FIX")["entries"]["execution.mode"]["value"]
            == "LOCAL_FIX"
        )
        return set()
    else:
        raise AssertionError(f"Unimplemented fixture: {mutation}")
    write(resolver.workspace_path, workspace)
    write(resolver.project_path, project)
    return {i.code for i in GovernanceResolver.for_root(root).check()}


@pytest.mark.parametrize("case", CATALOG["cases"], ids=lambda c: c["id"])
def test_contradiction_catalog_executes_expected_codes(
    checkout: Path, case: dict
) -> None:
    observed = apply_case(checkout, case["mutation"])
    assert (
        observed == set() if case["expected"] == "ok" else case["expected"] in observed
    )


def test_every_advertised_diagnostic_has_an_executable_emission(tmp_path: Path) -> None:
    # Run the same catalog dispatch, not a second expected-code declaration.
    observed = set()
    for case in CATALOG["cases"]:
        root = tmp_path / case["id"]
        root.mkdir()
        build_checkout(root)
        observed.update(apply_case(root, case["mutation"]))
    manifest = json.loads((PACK / "MANIFEST.json").read_text())
    assert observed == set(manifest["diagnostics"]) == core.DIAGNOSTIC_CLASSES


def test_facade_contract_and_authority_order(checkout: Path) -> None:
    resolver = GovernanceResolver.for_root(checkout)
    _, project, _ = resolver.load()
    for route in project["routes"].values():
        route["authority_refs"].reverse()
    write(resolver.project_path, project)
    assert resolver.check() == []
    project["generated_surfaces"][0]["kind"] = "generated_document"
    write(resolver.project_path, project)
    assert "CONFLICTING_VALUE" in {i.code for i in resolver.check()}


def test_manifest_driven_platform_hash_exclusion(checkout: Path) -> None:
    pack = checkout / "tools/workspace_governance"
    before = core.pack_hash(pack)
    for rel in (".DS_Store", "schemas/.DS_Store"):
        (pack / rel).write_bytes(b"platform metadata")
    assert core.pack_hash(pack) == before
    manifest = json.loads((pack / "MANIFEST.json").read_text())
    manifest["pack_hash_excludes"].remove("**/.DS_Store")
    write(pack / "MANIFEST.json", manifest)
    assert "schemas/.DS_Store" in core.pack_hash(pack)[1]
    assert ".DS_Store" in core.pack_hash(pack)[1]


def test_source_types_and_aliases_are_behavioral(checkout: Path) -> None:
    resolver = GovernanceResolver.for_root(checkout)
    _, project, _ = resolver.load()
    alias = next(a for a in project["authorities"] if a["source_type"] == "alias")
    alias["exclusive"] = True
    assert core._authority_graph_issues(checkout, project)
    alias["exclusive"] = False
    directory = next(
        a for a in project["authorities"] if a["source_type"] == "directory"
    )
    directory["source_type"] = "file"
    assert core._authority_graph_issues(checkout, project)
    directory["source_type"] = "directory"
    item = project["authorities"][0]
    item.update(
        source_type="json_pointer",
        source="config/project/policy_pack.json#/authority_model",
        canonical_governance=False,
    )
    assert not any(
        i.fact == "authority:" + item["authority_id"]
        for i in core._authority_graph_issues(checkout, project)
    )
    item["source"] += "/missing"
    assert any(
        i.fact == "authority:" + item["authority_id"]
        for i in core._authority_graph_issues(checkout, project)
    )


@pytest.fixture
def behavior_trace(family: str):
    """Require execution of the named callable, not a declaration-to-declaration match."""
    expected = set()
    for name in USAGE[family]["handler"].split(" / "):
        owner = GovernanceResolver if name.startswith("GovernanceResolver.") else core
        function = getattr(owner, name.split(".")[-1])
        assert callable(function), name
        expected.add(function.__code__)
    observed = set()
    previous = sys.getprofile()

    def record(frame, event, arg):
        if event == "call" and frame.f_code in expected:
            observed.add(frame.f_code)
        if previous is not None:
            previous(frame, event, arg)

    sys.setprofile(record)
    try:
        yield
    finally:
        sys.setprofile(previous)
    assert expected <= observed, "registered behavior was not executed"


@pytest.mark.parametrize("family", sorted(USAGE))
def test_registered_behavior_paths_have_mutation_evidence(  # noqa: C901 - explicit behavior-family cases
    checkout: Path, family: str, behavior_trace
) -> None:
    """Each registered path has an executed mutation, not a count or AST claim."""
    assert USAGE[family]["test"] == family
    resolver = GovernanceResolver.for_root(checkout)
    workspace, project, _ = resolver.load()
    if family == "schema":
        project["schema_version"] = 99
    elif family == "reserved":
        write(
            checkout / ".governance/workspace.local.json",
            {"schema_version": 1, "cache_locations": {"cache": "."}},
        )
    elif family == "identity":
        before = resolver.resolve()["entries"]["project.name"]
        project["project"]["name"] = "Changed identity"
        write(resolver.project_path, project)
        assert resolver.resolve()["entries"]["project.name"] != before
        return
    elif family == "membership":
        workspace["projects"][0]["manifest"] = "missing-manifest.json"
    elif family == "pack":
        workspace["governance_pack"]["required_schema"] += 1
    elif family == "authority":
        resolver.explain("authority:" + project["authorities"][0]["authority_id"])
        project["authorities"][0]["source"] = "missing-owner.md"
    elif family == "owner_set":
        project["canonical_owner_set"]["json_pointer"] = "/missing"
    elif family == "routes":
        resolver.resolve()
        project["routes"]["governance_and_tooling"]["authority_refs"].append(
            "security-sanitation"
        )
    elif family == "verification":
        before = resolver.resolve()["entries"]["verification.full"]
        project["verification"]["full"]["json_pointer"] = project["verification"][
            "canonical"
        ]["json_pointer"]
        write(resolver.project_path, project)
        assert resolver.resolve()["entries"]["verification.full"] != before
        return
    elif family == "execution":
        before = resolver.resolve(mode="LOCAL_FIX")["entries"]["execution.exploration"]
        project["execution"]["profiles"]["LOCAL_FIX"]["exploration"].append(
            "a changed exploration bound"
        )
        write(resolver.project_path, project)
        assert (
            resolver.resolve(mode="LOCAL_FIX")["entries"]["execution.exploration"]
            != before
        )
        return
    elif family == "facade":
        project["generated_surfaces"][0]["target"] += "/missing"
    elif family == "environment":
        data, issues = core.doctor(
            checkout, project, None, {"TET4D_PYTHON": sys.executable}
        )
        assert data["status"] == "ok" and not issues
        project["environment"]["critical_packages"].append(
            "missing_governance_test_package"
        )
        data, issues = core.doctor(
            checkout, project, None, {"TET4D_PYTHON": sys.executable}
        )
        assert data["status"] == "ENVIRONMENT_INVALID" and issues
        return
    elif family == "sanitation":
        project["sanitation"]["secret_scanner"] = "missing-scanner.py"
    elif family == "local":
        assert not core.doctor(checkout, project, {"interpreter": sys.executable}, {})[
            1
        ]
        a = core.resolve_interpreter(
            checkout, project, {"interpreter": sys.executable}, {}
        )
        b = core.resolve_interpreter(
            checkout, project, {"interpreter": "/missing/local-python"}, {}
        )
        assert not a[2] and b[2] and a[0] != b[0]
        return
    else:
        pytest.fail(f"No executable evidence for registered behavior {family}")
    write(resolver.workspace_path, workspace)
    write(resolver.project_path, project)
    assert GovernanceResolver.for_root(checkout).check()


def test_usage_declarations_cannot_hide_unimplemented_or_unconstrained_fields(
    checkout: Path,
) -> None:
    path = checkout / "tools/workspace_governance/schemas/workspace-local.schema.json"
    schema = json.loads(path.read_text())
    schema["properties"]["checkout_locations"].pop("maxProperties")
    assert core._schema_field_usage_issues(schema, str(path))
    schema = json.loads(path.read_text())
    schema["properties"]["interpreter"]["x-governance-behavior"] = "aspirational"
    assert core._schema_field_usage_issues(schema, str(path))
    schema["properties"]["interpreter"]["x-governance-behavior"] = "schema"
    assert core._schema_field_usage_issues(schema, str(path))


def test_route_tool_fields_and_local_tool_override_are_consumed(checkout: Path) -> None:
    _, project, _ = GovernanceResolver.for_root(checkout).load()
    tool = checkout / "fake-godot"
    tool.write_text('#!/bin/sh\nprintf "test-tool:%s\\n" "$1"\n')
    tool.chmod(0o755)
    env = {"TET4D_PYTHON": sys.executable}
    local = {"tool_paths": {"godot": str(tool)}}
    data, issues = core.doctor(
        checkout, project, local, env, route="godot_product_shell"
    )
    assert not issues and data["route_tools"]["godot"] == "test-tool:--version"
    project["environment"]["route_tools"]["godot"]["version_args"] = ["--changed"]
    data, issues = core.doctor(
        checkout, project, local, env, route="godot_product_shell"
    )
    assert not issues and data["route_tools"]["godot"] == "test-tool:--changed"


def test_verify_and_project_test_use_the_doctor_selected_interpreter(
    checkout: Path,
) -> None:
    # Real verify startup and module checks; stop intentionally at the editable-install
    # shell entrypoint so this regression does not recursively run the full test suite.
    selected = checkout / "traced-python"
    log = checkout / "calls.jsonl"
    selected.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\nexec "{sys.executable}" "$@"\n'
    )
    selected.chmod(0o755)
    stop = checkout / "scripts/check_editable_install.sh"
    stop.write_text("#!/bin/sh\necho intentional-test-boundary >&2\nexit 79\n")
    env = environment(
        TET4D_PYTHON=str(selected),
        GOVERNANCE_PYTHON=sys.executable,
        PYTHON_BIN="/ignored/legacy",
    )
    diagnosed = run(checkout, "./gov", "doctor", "--print-interpreter", env=env)
    assert diagnosed.stdout.strip() == str(selected)
    verified = run(checkout, "./scripts/verify.sh", env=env)
    assert verified.returncode != 0, verified.stdout + verified.stderr
    assert "intentional-test-boundary" in verified.stdout + verified.stderr
    # The project-test invocation uses the same resolved executable.
    test = checkout / "test_interpreter.py"
    test.write_text(
        f"import sys\ndef test_identity():\n    assert sys.executable == {sys.executable!r}\n"
    )
    result = run(
        checkout, diagnosed.stdout.strip(), "-m", "pytest", "-q", str(test), env=env
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = log.read_text()
    assert "import ruff" in calls and "import pytest" in calls
    assert "-m pytest -q" in calls


@pytest.mark.parametrize(
    "malformed", [[], {"route": []}, {"route": {"authority_keys": [1]}}]
)
def test_malformed_facade_target_is_a_diagnostic(
    checkout: Path, malformed: object
) -> None:
    path = checkout / "config/project/policy_pack.json"
    pack = json.loads(path.read_text())
    pack["codex_routing"]["routes"] = malformed
    write(path, pack)
    assert "CONFLICTING_VALUE" in {
        i.code for i in GovernanceResolver.for_root(checkout).check()
    }


@pytest.mark.parametrize(
    "script,override",
    [
        ("bootstrap_env.sh", "PYTHON_BOOTSTRAP_BIN"),
        ("verify_local.sh", "BOOTSTRAP_PYTHON"),
    ],
)
def test_environment_creators_reject_unsupported_bootstrap_before_creating_venv(
    checkout: Path, script: str, override: str
) -> None:
    (checkout / "pyproject.toml").write_text('[project]\nrequires-python = ">=99"\n')
    result = run(
        checkout, "./scripts/" + script, env=environment(**{override: sys.executable})
    )
    assert result.returncode == 1
    assert "bootstrap.interpreter" in result.stderr and ">=99" in result.stderr
    assert not (checkout / ".venv").exists()
    assert "Traceback" not in result.stdout + result.stderr


def test_exclusive_file_identity_normalizes_equivalent_paths(checkout: Path) -> None:
    _, project, _ = GovernanceResolver.for_root(checkout).load()
    duplicate = {
        **project["authorities"][0],
        "authority_id": "second-identity",
        "scope": "another-scope",
        "canonical_governance": False,
    }
    duplicate["source"] = "./" + duplicate["source"]
    project["authorities"].append(duplicate)
    assert any(
        i.code == "AMBIGUOUS_AUTHORITY" and i.fact == "authority.source"
        for i in core._authority_graph_issues(checkout, project)
    )
