from __future__ import annotations

import os
import re
import shutil
import tempfile
from collections.abc import Iterator, MutableMapping
from pathlib import Path
from uuid import uuid4

import pytest

from tet4d.engine.runtime.project_config import state_dir_path

_USE_TMP_WORKAROUND = (
    os.environ.get("CODEX_MODE") == "1"
    or os.environ.get("TET4D_PYTEST_TMP_WORKAROUND") == "1"
)


# Git exports GIT_DIR and friends into hook environments, and .githooks/pre-push
# runs this suite. A test that spawns git while they are still set operates on the
# host repository instead of its own temporary one: from a linked worktree an
# inherited GIT_DIR makes `git init` write core.bare into the shared config and
# every worktree stops resolving. No test needs git's ambient repository location,
# so the session refuses to inherit it.
GIT_LOCATION_ENV_VARS = (
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CEILING_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_NAMESPACE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_PREFIX",
    "GIT_WORK_TREE",
)


@pytest.fixture(scope="session")
def git_location_env_vars() -> tuple[str, ...]:
    """Expose the scrubbed names; conftest is reachable as fixtures, not imports."""
    return GIT_LOCATION_ENV_VARS


@pytest.fixture(scope="session", autouse=True)
def _sandboxed_git_location() -> None:
    """Refuse an inherited git repository location for the whole session."""
    scrub_git_location_env(os.environ)


@pytest.fixture(scope="session", autouse=True)
def _sandboxed_state_home() -> Iterator[None]:
    """Keep every test's governance telemetry out of the machine's record.

    A machine that enables telemetry records its real `gov` invocations under
    XDG_STATE_HOME. Tests spawn `gov` against synthetic checkouts, and those
    invocations must not land in that record.
    """
    previous = os.environ.get("XDG_STATE_HOME")
    sandbox = tempfile.mkdtemp(prefix="tet4d-test-state-")
    os.environ["XDG_STATE_HOME"] = sandbox
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("XDG_STATE_HOME", None)
        else:
            os.environ["XDG_STATE_HOME"] = previous
        shutil.rmtree(sandbox, ignore_errors=True)


def scrub_git_location_env(
    env: MutableMapping[str, str],
) -> MutableMapping[str, str]:
    """Drop git's repository-location variables from ``env`` and return it."""
    for name in GIT_LOCATION_ENV_VARS:
        env.pop(name, None)
    return env


def _pytest_tmp_root() -> Path:
    return state_dir_path() / "pytest_temp"


def _sanitize_node_name(node_name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", node_name).strip("_") or "test"


if _USE_TMP_WORKAROUND:

    @pytest.fixture
    def tmp_path(request: pytest.FixtureRequest) -> Path:
        tmp_root = _pytest_tmp_root()
        tmp_root.mkdir(parents=True, exist_ok=True)
        leaf = f"{_sanitize_node_name(request.node.name)}_{uuid4().hex}"
        path = tmp_root / leaf
        path.mkdir(parents=True, exist_ok=False)
        try:
            yield path
        finally:
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def _canonical_gate_environment_contract(request: pytest.FixtureRequest) -> None:
    """Prove classified repository-sensitive tests use the gate temp topology."""
    if (
        request.node.get_closest_marker("canonical_gate_environment") is None
        or os.environ.get("CODEX_MODE") != "1"
    ):
        return
    path = request.getfixturevalue("tmp_path").resolve()
    expected_root = _pytest_tmp_root().resolve()
    assert path == expected_root or expected_root in path.parents
