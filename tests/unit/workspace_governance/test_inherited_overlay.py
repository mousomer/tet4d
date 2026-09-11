"""One machine-wide interpreter serves every checkout of a workspace.

A repository overlay is gitignored and therefore per checkout, which does not
survive `git worktree add`. These tests pin the inherited tier that sits
between it and the repository `.venv`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support import build_checkout, scrubbed_environment, write

from tools.workspace_governance.resolver.core import (
    GovernanceResolver,
    user_overlay_path,
)
from tools.workspace_governance.validators import core

WORKSPACE_ID = "tet4d-workspace"


def inherited(config_root: Path) -> Path:
    return user_overlay_path(WORKSPACE_ID, {"XDG_CONFIG_HOME": str(config_root)})


def declare(config_root: Path, payload: dict[str, object]) -> Path:
    path = inherited(config_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, payload)
    return path


def repository(checkout: Path, payload: dict[str, object]) -> None:
    write(checkout / ".governance/workspace.local.json", payload)


def test_inherited_overlay_supplies_the_interpreter(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    declare(isolated_user_overlay, {"schema_version": 1, "interpreter": sys.executable})
    resolver = GovernanceResolver.for_root(checkout)
    merged, tiers = resolver.local_overlay()
    assert merged is not None and merged["interpreter"] == sys.executable
    assert tiers["interpreter"] == "workspace"

    _, project, local = resolver.load()
    interpreter, reason, issues = core.resolve_interpreter(
        checkout, project, local, {}, local_tiers=tiers
    )
    assert interpreter == Path(sys.executable).absolute()
    assert reason == "inherited workspace overlay"
    assert issues == []


def test_repository_overlay_overrides_the_inherited_one_per_key(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    declare(isolated_user_overlay, {"schema_version": 1, "interpreter": sys.executable})

    # Naming only tool_paths must not discard the inherited interpreter.
    repository(checkout, {"schema_version": 1, "tool_paths": {"godot": "/tmp/godot"}})
    merged, tiers = GovernanceResolver.for_root(checkout).local_overlay()
    assert merged is not None and merged["interpreter"] == sys.executable
    assert tiers["interpreter"] == "workspace"
    assert tiers["tool_paths"] == "local"

    repository(checkout, {"schema_version": 1, "interpreter": "/repository/python"})
    merged, tiers = GovernanceResolver.for_root(checkout).local_overlay()
    assert merged is not None and merged["interpreter"] == "/repository/python"
    assert tiers["interpreter"] == "local"


def test_inherited_overlay_is_keyed_by_identity_not_checkout_path(
    tmp_path: Path, isolated_user_overlay: Path
) -> None:
    declare(isolated_user_overlay, {"schema_version": 1, "interpreter": sys.executable})
    for name in ("first-worktree", "second-worktree"):
        merged, tiers = GovernanceResolver.for_root(
            build_checkout(tmp_path / name)
        ).local_overlay()
        assert merged is not None and merged["interpreter"] == sys.executable
        assert tiers["interpreter"] == "workspace"


def test_absent_inherited_overlay_leaves_the_repository_venv_in_charge(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    resolver = GovernanceResolver.for_root(checkout)
    assert resolver.user_local_path is None
    merged, tiers = resolver.local_overlay()
    assert merged is None and tiers == {}

    _, project, local = resolver.load()
    _, reason, _ = core.resolve_interpreter(checkout, project, local, {})
    assert reason == "repository-local environment"


def test_malformed_inherited_overlay_names_its_own_file(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    path = inherited(isolated_user_overlay)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{ not json\n")
    issues = GovernanceResolver.for_root(checkout).check()
    assert {item.code for item in issues} == {"BROKEN_REFERENCE"}
    assert any(str(path) in source for source in issues[0].sources)


def test_inherited_overlay_schema_violation_is_attributed_to_it(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    path = declare(isolated_user_overlay, {"schema_version": 1, "unsupported": True})
    issues = GovernanceResolver.for_root(checkout).check()
    assert issues
    assert any(str(path) in source for item in issues for source in item.sources)


def executable(path: Path) -> Path:
    """A distinguishable interpreter that still behaves like the real one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    path.chmod(0o755)
    return path


def bootstrap(checkout: Path, **updates: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["./scripts/resolve_bootstrap_python.sh"],
        cwd=checkout,
        env=scrubbed_environment(**updates),
        text=True,
        capture_output=True,
        check=False,
    )


def gov(checkout: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["./gov", *args],
        cwd=checkout,
        env=scrubbed_environment(),
        text=True,
        capture_output=True,
        check=False,
    )


def test_inherited_overlay_bootstraps_a_genuinely_fresh_worktree(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    # No .venv, no repository overlay, no bootstrap variables: the inherited
    # overlay is the only approved interpreter in reach.
    assert not (checkout / ".venv").exists()
    assert not (checkout / ".governance/workspace.local.json").exists()
    declare(isolated_user_overlay, {"schema_version": 1, "interpreter": sys.executable})

    checked = gov(checkout, "check", "--json")
    assert checked.returncode == 0, checked.stdout + checked.stderr

    # Starting is the contract here, so assert governance got past bootstrap and
    # that the overlay is what answered, rather than the project environment's
    # health.
    diagnosed = gov(checkout, "doctor", "--json")
    combined = diagnosed.stdout + diagnosed.stderr
    assert "bootstrap.interpreter" not in combined
    assert "Traceback" not in combined
    assert json.loads(diagnosed.stdout)["selection_reason"] == (
        "inherited workspace overlay"
    )


def test_bootstrap_precedence_is_override_then_workspace_then_inherited_then_venv(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    override = executable(checkout / "candidates/override/bin/python")
    workspace = executable(checkout / "candidates/workspace/bin/python")
    inherited_python = executable(checkout / "candidates/inherited/bin/python")
    repository = executable(checkout / ".venv/bin/python")
    declare(
        isolated_user_overlay,
        {"schema_version": 1, "interpreter": str(inherited_python)},
    )

    selected = bootstrap(checkout, GOVERNANCE_PYTHON=str(override))
    assert selected.stdout.strip() == str(override)

    selected = bootstrap(checkout, WORKSPACE_VENV=str(workspace.parents[1]))
    assert selected.stdout.strip() == str(workspace)

    selected = bootstrap(checkout)
    assert selected.stdout.strip() == str(inherited_python)

    inherited(isolated_user_overlay).unlink()
    selected = bootstrap(checkout)
    assert selected.stdout.strip() == str(repository)


def test_bootstrap_never_selects_an_interpreter_nested_under_tool_paths(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    # `tool_paths` may legally carry a key named `interpreter`. Matching it would
    # start governance under a tool rather than the declared interpreter.
    decoy = executable(checkout / "candidates/decoy/bin/python")
    declared = executable(checkout / "candidates/declared/bin/python")
    declare(
        isolated_user_overlay,
        {
            "schema_version": 1,
            "tool_paths": {"interpreter": str(decoy)},
            "interpreter": str(declared),
        },
    )
    assert bootstrap(checkout).stdout.strip() == str(declared)

    declare(
        isolated_user_overlay,
        {"schema_version": 1, "tool_paths": {"interpreter": str(decoy)}},
    )
    refused = bootstrap(checkout)
    assert refused.returncode == 1
    assert "bootstrap.interpreter" in refused.stderr
    assert str(decoy) not in refused.stdout


def test_an_unsafe_workspace_identity_addresses_no_overlay(
    isolated_user_overlay: Path,
) -> None:
    """The identity becomes a filename, so it may not address another directory.

    `resolve_bootstrap_python.sh` applies the same rule; the two resolvers derive
    one path and must agree on what is addressable.
    """
    env = {"XDG_CONFIG_HOME": str(isolated_user_overlay)}
    assert user_overlay_path(WORKSPACE_ID, env) is not None
    for unsafe in ("../../../tmp/evil", "a/b", "", "we..ird/../x"):
        assert user_overlay_path(unsafe, env) is None


def test_an_unsafe_workspace_identity_does_not_inherit(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    declare(isolated_user_overlay, {"schema_version": 1, "interpreter": sys.executable})
    manifest = checkout / ".governance/workspace.json"
    payload = json.loads(manifest.read_text())
    payload["workspace_id"] = "../../../tmp/evil"
    write(manifest, payload)
    resolver = GovernanceResolver.for_root(checkout)
    assert resolver.user_local_path is None
    assert resolver.local_overlay() == (None, {})
