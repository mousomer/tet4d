"""One machine-wide interpreter serves every checkout of a workspace.

A repository overlay is gitignored and therefore per checkout, which does not
survive `git worktree add`. These tests pin the inherited tier that sits
between it and the repository `.venv`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from support import build_checkout, write

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
