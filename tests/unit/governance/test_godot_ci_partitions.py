"""Exercise the real GDScript selector with isolated synthetic test resources."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "godot/Tet4D.Godot/tests/run_tests.gd"
GODOT = os.environ.get("GODOT_BIN") or shutil.which("godot")


@pytest.fixture
def selector_project(tmp_path: Path) -> Path:
    (tmp_path / "project.godot").write_text(
        '[application]\nconfig/name="CI selector"\n'
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    names = [
        "explorer_first",
        "ordinary_a",
        "ordinary_b",
        "ordinary_c",
        "explorer_last",
        "ordinary_d",
        "ordinary_e",
    ]
    paths = [f"res://tests/test_{name}.gd" for name in names]
    source = re.sub(
        r"const TEST_SCRIPTS := \[.*?\n\]",
        "const TEST_SCRIPTS := [\n"
        + "\n".join(f'\t"{path}",' for path in paths)
        + "\n]",
        RUNNER.read_text(),
        count=1,
        flags=re.DOTALL,
    )
    (tests / "run_tests.gd").write_text(source)
    for name in names:
        (tests / f"test_{name}.gd").write_text(
            "extends RefCounted\nfunc run() -> Array:\n\treturn []\n"
        )
    return tmp_path


def _run(
    project: Path, shard: str = "0", count: str = "1", group: str = ""
) -> subprocess.CompletedProcess[str]:
    if not GODOT:
        pytest.skip("Godot executable required for selector execution")
    env = dict(
        os.environ,
        TET4D_GODOT_SHARD=shard,
        TET4D_GODOT_SHARD_COUNT=count,
        TET4D_GODOT_TEST_GROUP=group,
    )
    return subprocess.run(
        [GODOT, "--headless", "--path", str(project), "--script", "tests/run_tests.gd"],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _executed(result: subprocess.CompletedProcess[str]) -> list[str]:
    assert result.returncode == 0, result.stdout + result.stderr
    return re.findall(r"Godot replay test \d+/\d+: (res://[^\n]+)", result.stdout)


def test_shards_are_disjoint_and_cover_unsharded_suite(selector_project: Path) -> None:
    whole = _executed(_run(selector_project))
    shards = [_executed(_run(selector_project, str(i), "4")) for i in range(4)]
    combined = [path for shard in shards for path in shard]
    assert len(combined) == len(set(combined))
    assert set(combined) == set(whole)
    assert all(shards)


def test_focused_checks_ignore_partition_and_propagate_failure(
    selector_project: Path,
) -> None:
    focused = _executed(_run(selector_project, "3", "4", "explorer"))
    assert len(focused) == 2 and all("explorer" in path for path in focused)
    (selector_project / "tests/test_explorer_first.gd").write_text(
        'extends RefCounted\nfunc run() -> Array:\n\treturn ["injected regression"]\n'
    )
    result = _run(selector_project, group="explorer")
    assert result.returncode != 0
    assert "injected regression" in result.stdout + result.stderr


@pytest.mark.parametrize(
    "shard,count", [("-1", "4"), ("4", "4"), ("bad", "4"), ("0", "0"), ("0", "8")]
)
def test_invalid_partition_fails(
    selector_project: Path, shard: str, count: str
) -> None:
    result = _run(selector_project, shard, count)
    assert result.returncode != 0
    assert "Invalid Godot test selection" in result.stdout + result.stderr


def test_unregistered_test_still_fails(selector_project: Path) -> None:
    (selector_project / "tests/test_unregistered.gd").write_text("extends RefCounted\n")
    result = _run(selector_project, "0", "4")
    assert result.returncode != 0
    assert "not registered" in result.stdout + result.stderr
