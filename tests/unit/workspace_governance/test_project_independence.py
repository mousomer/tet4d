"""The pack carries no project's semantic values; the project declares them."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support import PACK, ROOT, scrubbed_environment, write

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core


def _project_tokens() -> set[str]:
    """Values only this project's manifests could have taught the pack."""
    workspace = json.loads((ROOT / ".governance/workspace.json").read_text())
    project = json.loads((ROOT / "config/governance/project.json").read_text())
    environment = project["environment"]
    tokens = {
        workspace["workspace_id"],
        project["project"]["id"],
        project["project"]["name"],
        *(member["manifest"] for member in workspace["projects"]),
        environment["interpreter_override"],
        environment["execution_mode"]["override"],
        *(tool["override"] for tool in environment["route_tools"].values()),
        *project["required_authorities"],
    }
    # Hyphenated authority IDs are distinctive; single words such as
    # "engineering" also occur in ordinary prose.
    tokens.update(
        a["authority_id"] for a in project["authorities"] if "-" in a["authority_id"]
    )
    return tokens


def test_pack_names_no_project_value() -> None:
    tokens = {token.lower() for token in _project_tokens()}
    offenders = []
    for path in sorted(PACK.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8").lower()
        offenders.extend(
            f"{path.relative_to(PACK)}: {token}"
            for token in sorted(tokens)
            if token in text
        )
    assert offenders == []


def test_required_authorities_are_declared_by_the_project() -> None:
    workspace = json.loads((ROOT / ".governance/workspace.json").read_text())
    project = json.loads((ROOT / "config/governance/project.json").read_text())

    def required_issues(value: list[str]) -> list[str]:
        changed = {**project, "required_authorities": value}
        return [
            issue.fact
            for issue in core.validate_manifests(
                ROOT, workspace, changed, None, pack_root=PACK
            )
            if issue.reason == "required stable authority ID is missing"
        ]

    assert required_issues(project["required_authorities"]) == []
    assert required_issues(["undeclared-authority"]) == [
        "authority:undeclared-authority"
    ]
    assert required_issues([]) == []


def test_gov_env_exports_the_mode_under_the_declared_variable(checkout: Path) -> None:
    project_path = checkout / "config/governance/project.json"
    project = json.loads(project_path.read_text())
    mode = project["environment"]["execution_mode"]["default"]
    project["environment"]["execution_mode"]["override"] = "DEMO_ENVIRONMENT_MODE"
    write(project_path, project)
    env = scrubbed_environment(
        GOVERNANCE_PYTHON=sys.executable,
        **{project["environment"]["interpreter_override"]: sys.executable},
        DEMO_ENVIRONMENT_MODE=mode,
    )
    result = subprocess.run(
        ["./gov", "env", "--json"],
        cwd=checkout,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    exported = json.loads(result.stdout)
    assert exported["DEMO_ENVIRONMENT_MODE"] == mode
    assert "TET4D_ENVIRONMENT_MODE" not in exported


def test_the_project_manifest_location_comes_from_the_workspace(checkout: Path) -> None:
    moved = "config/manifests/demo.json"
    old = "config/governance/project.json"
    (checkout / moved).parent.mkdir(parents=True)
    text = (checkout / old).read_text().replace(f'"{old}#', f'"{moved}#')
    (checkout / moved).write_text(text)
    (checkout / old).unlink()
    workspace_path = checkout / ".governance/workspace.json"
    workspace = json.loads(workspace_path.read_text())
    workspace["projects"][0]["manifest"] = moved
    write(workspace_path, workspace)

    resolver = GovernanceResolver.for_root(checkout)
    assert resolver.check() == []
    assert resolver.role_index().resolve(moved).role == "governance_treatment"
    assert resolver.role_index().is_root(moved)

    project = json.loads((checkout / moved).read_text())
    project["routes"]["governance_and_tooling"]["authority_refs"].append("missing")
    write(checkout / moved, project)
    issues = GovernanceResolver.for_root(checkout).check()
    assert issues and all(old not in issue.sources for issue in issues)
    assert any(moved in issue.sources for issue in issues)


def test_a_workspace_without_a_default_project_is_reported_not_guessed(
    checkout: Path,
) -> None:
    workspace_path = checkout / ".governance/workspace.json"
    workspace = json.loads(workspace_path.read_text())
    workspace["defaults"]["project"] = "absent-project"
    write(workspace_path, workspace)

    resolver = GovernanceResolver.for_root(checkout)
    assert resolver.project_path is None
    issues = resolver.check()
    assert [issue.code for issue in issues] == ["BROKEN_REFERENCE"]
    assert "no default project manifest" in issues[0].reason
