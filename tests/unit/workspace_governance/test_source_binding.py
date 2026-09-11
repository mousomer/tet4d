"""The invoking checkout decides which source is imported.

One shared environment can hold exactly one distribution named `tet4d`, so an
editable install makes a single checkout authoritative for every other. Source
mode replaces that ownership with a binding derived from the invoking checkout.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support import scrubbed_environment

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core


def own_source(checkout: Path) -> Path:
    """Give a checkout its own importable source instead of the shared symlink.

    `build_checkout` links `src` at the repository's, which would make "bound to
    this checkout" and "bound to the repository" indistinguishable.
    """
    link = checkout / "src"
    if link.is_symlink():
        link.unlink()
    package = checkout / "src/tet4d"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text('"""Stub for binding tests."""\n')
    return package


def project_of(checkout: Path) -> dict:
    return GovernanceResolver.for_root(checkout).load()[1]


def test_binding_is_derived_from_the_declared_editable_source(checkout: Path) -> None:
    project = project_of(checkout)
    assert core.source_binding_path(checkout, project) == (checkout / "src").resolve()


def test_installed_mode_injects_no_binding(checkout: Path) -> None:
    project = project_of(checkout)
    assert core.binding_environment(checkout, project, {}) == {}


def test_source_mode_prepends_and_never_replaces(checkout: Path) -> None:
    project = project_of(checkout)
    expected = str((checkout / "src").resolve())

    bare = core.binding_environment(
        checkout, project, {"TET4D_ENVIRONMENT_MODE": "source"}
    )
    assert bare == {"PYTHONPATH": expected}

    inherited = core.binding_environment(
        checkout,
        project,
        {"TET4D_ENVIRONMENT_MODE": "source", "PYTHONPATH": "/outer"},
    )
    assert inherited == {"PYTHONPATH": f"{expected}:/outer"}


def test_an_unimplemented_mode_binds_nothing(checkout: Path) -> None:
    project = project_of(checkout)
    assert (
        core.binding_environment(
            checkout, project, {"TET4D_ENVIRONMENT_MODE": "sideways"}
        )
        == {}
    )


def test_installed_mode_still_observes_a_foreign_editable_install(
    checkout: Path,
) -> None:
    """The check that injection would otherwise silence must keep its teeth.

    A binding injected in every mode would make import origin equal the
    expectation by construction, and this diagnostic could never fire again.
    """
    own_source(checkout)
    project = project_of(checkout)
    _, issues = core.doctor(checkout, project, None, {"TET4D_PYTHON": sys.executable})
    assert "editable_install" in {item.fact for item in issues}


def test_source_mode_binds_the_invoking_checkout(checkout: Path) -> None:
    own_source(checkout)
    project = project_of(checkout)
    data, issues = core.doctor(
        checkout,
        project,
        None,
        {"TET4D_PYTHON": sys.executable, "TET4D_ENVIRONMENT_MODE": "source"},
    )
    assert not issues, [item.to_dict() for item in issues]
    assert data["source_binding"] == str((checkout / "src").resolve())
    assert Path(data["package"]).parent == (checkout / "src/tet4d").resolve()


def test_gov_env_is_the_one_interface_for_non_python_callers(
    checkout: Path, isolated_user_overlay: Path
) -> None:
    own_source(checkout)

    def emitted(**updates: str) -> dict[str, str]:
        result = subprocess.run(
            ["./gov", "env", "--json"],
            cwd=checkout,
            env=scrubbed_environment(GOVERNANCE_PYTHON=sys.executable, **updates),
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    installed = emitted(TET4D_PYTHON=sys.executable)
    assert installed["PYTHON_BIN"] == str(Path(sys.executable).absolute())
    assert "PYTHONPATH" not in installed

    source = emitted(TET4D_PYTHON=sys.executable, TET4D_ENVIRONMENT_MODE="source")
    assert source["PYTHONPATH"] == str((checkout / "src").resolve())
