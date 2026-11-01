"""Advisory exceptions must never grant immunity to changed or additional paths."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.governance.filter_sanitation_findings import (
    REFERENCE_REGISTER,
    filter_findings,
    reviewed_references,
)

REPOSITORY = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.canonical_gate_environment


def _register(root: Path, source: str, warning_class: str = "parent-traversal") -> Path:
    register = root / REFERENCE_REGISTER
    register.parent.mkdir(parents=True, exist_ok=True)
    register.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "references": [
                    {
                        "path": "reference.txt",
                        "warning_class": warning_class,
                        "line_sha256": [hashlib.sha256(source.encode()).hexdigest()],
                        "reason": "Synthetic negative-path fixture.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return register


def test_exception_preserves_changed_moved_and_additional_findings(
    tmp_path: Path,
) -> None:
    source = ".." + "/negative-input"
    _register(tmp_path, source)
    reviewed = reviewed_references(tmp_path, "parent-traversal")
    assert filter_findings(f"reference.txt:20:{source}", reviewed) == ""
    unmatched = [
        f"other.txt:1:{source}",
        f"reference.txt:21:{source}-changed",
        f"reference.txt:22:{source}",
        "unexpected diagnostic",
    ]
    assert filter_findings(
        "\n".join([f"reference.txt:20:{source}", *unmatched]), reviewed
    ) == "\n".join(unmatched)
    assert not reviewed_references(tmp_path, "absolute-unix")


@pytest.mark.parametrize(
    "field,value",
    [
        ("reason", ""),
        ("line_sha256", ["bad"]),
        ("path", "/outside"),
        ("warning_class", "all"),
    ],
)
def test_invalid_exceptions_fail_closed(
    tmp_path: Path, field: str, value: object
) -> None:
    register = _register(tmp_path, "fixture")
    data = json.loads(register.read_text(encoding="utf-8"))
    data["references"][0][field] = value
    register.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        reviewed_references(tmp_path, "parent-traversal")


def test_shell_baseline_warns_on_unreviewed_references(tmp_path: Path) -> None:
    for relative in (
        "scripts/check_git_sanitation.sh",
        "tools/governance/filter_sanitation_findings.py",
    ):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPOSITORY / relative, destination)
    resolver = tmp_path / "scripts/resolve_python_env.sh"
    resolver.write_text(
        f"#!/bin/sh\nprintf '%s\\n' '{sys.executable}'\n", encoding="utf-8"
    )
    resolver.chmod(0o755)
    source = ".." + "/reviewed-negative-input"
    _register(tmp_path, source)
    payload = tmp_path / "reference.txt"
    payload.write_text(source + "\n", encoding="utf-8")
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, env=env, check=True)

    def run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", "scripts/check_git_sanitation.sh"],
            cwd=tmp_path,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    clean = run()
    assert clean.returncode == 0, clean.stderr
    assert "WARN:" not in clean.stdout
    payload.write_text(
        "\n".join(
            [source, source, "/" + "home/synthetic", "C:" + chr(92) + "synthetic"]
        ),
        encoding="utf-8",
    )
    warning = run()
    assert warning.returncode == 0, warning.stderr
    assert "reported 3 issue class(es)" in warning.stdout
    assert "reference.txt:2:" in warning.stdout

    (tmp_path / REFERENCE_REGISTER).write_text("{}", encoding="utf-8")
    assert run().returncode != 0
