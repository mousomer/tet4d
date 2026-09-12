"""Two checkouts, one interpreter, no crossover.

Consolidation is only safe if the interpreter carries no opinion about which
source it belongs to. These cases run real checkouts against one interpreter and
assert that the invoking checkout decides, sequentially and concurrently, and
that neither operation mutates the shared environment.
"""

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from support import build_checkout, scrubbed_environment


def worktree(root: Path, name: str) -> Path:
    """A checkout with its own identifiable source, as a real worktree has."""
    checkout = build_checkout(root / name)
    link = checkout / "src"
    if link.is_symlink():
        link.unlink()
    package = checkout / "src/tet4d"
    package.mkdir(parents=True, exist_ok=True)
    (package / "__init__.py").write_text(f'WORKTREE = "{name}"\n')
    return checkout


def doctor(checkout: Path) -> dict:
    result = subprocess.run(
        ["./gov", "doctor", "--json"],
        cwd=checkout,
        env=scrubbed_environment(
            TET4D_PYTHON=sys.executable,
            GOVERNANCE_PYTHON=sys.executable,
            TET4D_ENVIRONMENT_MODE="source",
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def installed_distributions() -> list[str]:
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.metadata as m, json;"
                "print(json.dumps(sorted((d.metadata['Name'] or '')"
                " for d in m.distributions())))"
            ),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(probe.stdout)


def test_two_worktrees_alternate_without_mutating_the_environment(
    tmp_path: Path,
) -> None:
    first, second = worktree(tmp_path, "first"), worktree(tmp_path, "second")
    before = installed_distributions()

    for checkout in (first, second, first):
        data = doctor(checkout)
        assert Path(data["package"]).parent == (checkout / "src/tet4d").resolve()
        assert data["source_binding"] == str((checkout / "src").resolve())
        # Switching checkouts must cost nothing: the previous arrangement
        # required an editable reinstall to change which source answered.
        assert data["distribution"] is False

    assert installed_distributions() == before


def test_concurrent_worktrees_do_not_cross(tmp_path: Path) -> None:
    first, second = worktree(tmp_path, "first"), worktree(tmp_path, "second")
    before = installed_distributions()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(doctor, [first, second, first, second]))

    for checkout, data in zip([first, second, first, second], results, strict=True):
        assert Path(data["package"]).parent == (checkout / "src/tet4d").resolve()

    assert installed_distributions() == before


def test_one_environment_serves_only_a_compatible_dependency_set(
    tmp_path: Path,
) -> None:
    """The limit of consolidation, asserted rather than only documented.

    Sharing an interpreter shares its installed versions, so two checkouts agree
    only while they declare compatible dependencies. Nothing detects divergence
    today; this pins the property that makes divergence a real risk, so a future
    fingerprint-keyed environment has something to contradict.
    """
    first, second = worktree(tmp_path, "first"), worktree(tmp_path, "second")
    versions = [doctor(checkout)["version"] for checkout in (first, second)]
    assert versions[0] == versions[1]
