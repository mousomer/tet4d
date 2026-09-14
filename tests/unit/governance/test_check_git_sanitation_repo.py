"""Regression coverage for boundary-aware Windows path sanitation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SANITATION_SCRIPT = REPOSITORY_ROOT / "scripts" / "check_git_sanitation_repo.sh"
REQUIRED_ENTRYPOINTS = (
    "gov",
    "scripts/bootstrap_env.sh",
    "scripts/check_architecture_boundaries.sh",
    "scripts/check_architecture_metric_budgets.sh",
    "scripts/check_architecture_metrics_soft_gate.sh",
    "scripts/check_engine_core_purity.sh",
    "scripts/check_git_sanitation.sh",
    "scripts/check_git_sanitation_repo.sh",
    "scripts/check_policy_compliance.sh",
    "scripts/check_policy_compliance_repo.sh",
    "scripts/check_policy_template_drift.sh",
    "scripts/ci_check.sh",
    "scripts/ci_preflight.sh",
    "scripts/install_git_hooks.sh",
    "scripts/resolve_bootstrap_python.sh",
    "scripts/resolve_python_env.sh",
    "scripts/update_policy_template_hashes.sh",
    "scripts/verify.sh",
    "scripts/verify_local.sh",
    "scripts/verify_focus.sh",
    ".githooks/pre-push",
)


def _drive_path(drive: str, suffix: str, separator: str = "\\") -> str:
    return f"{drive}:{separator}{suffix}"


def _sanitation_result(
    tmp_path: Path,
    payload: str,
    *,
    payload_path: str = "payload.txt",
    repository_ignore_rule: str | None = None,
    force_track_payload: bool = False,
    global_exclude_rule: str | None = None,
    info_exclude_rule: str | None = None,
) -> subprocess.CompletedProcess[str]:
    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    shutil.copy2(SANITATION_SCRIPT, scripts_dir / SANITATION_SCRIPT.name)
    for entrypoint in REQUIRED_ENTRYPOINTS:
        path = tmp_path / entrypoint
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        path.chmod(0o755)
    target_path = tmp_path / payload_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(payload, encoding="utf-8")
    if repository_ignore_rule is not None:
        (tmp_path / ".gitignore").write_text(
            f"{repository_ignore_rule}\n", encoding="utf-8"
        )

    env = {
        **os.environ,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "LC_ALL": "C",
    }
    if global_exclude_rule is not None:
        config_dir = tmp_path.parent / f"{tmp_path.name}-git-config"
        config_dir.mkdir()
        excludes_path = config_dir / "global-excludes"
        excludes_path.write_text(f"{global_exclude_rule}\n", encoding="utf-8")
        global_config_path = config_dir / "global-gitconfig"
        global_config_path.write_text(
            f"[core]\n\texcludesFile = {excludes_path}\n", encoding="utf-8"
        )
        env["GIT_CONFIG_GLOBAL"] = str(global_config_path)

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, env=env)
    if info_exclude_rule is not None:
        (tmp_path / ".git" / "info" / "exclude").write_text(
            f"{info_exclude_rule}\n", encoding="utf-8"
        )
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, env=env)
    if force_track_payload:
        subprocess.run(
            ["git", "add", "-f", payload_path], cwd=tmp_path, check=True, env=env
        )
    return subprocess.run(
        ["bash", "scripts/check_git_sanitation_repo.sh"],
        cwd=tmp_path,
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )


@pytest.mark.parametrize(
    "payload",
    [
        _drive_path("C", "Users\\omer"),
        _drive_path("C", "temp\\build"),
        _drive_path("C", "repos\\tet4d"),
        _drive_path("C", "node_modules"),
        _drive_path("D", "tools\\sdk"),
        _drive_path("C", "projects"),
        _drive_path("C", "projects/foo", "/"),
        json.dumps({"workspace": _drive_path("C", "repos\\tet4d")}),
    ],
)
def test_repo_sanitation_rejects_drive_paths_at_token_boundaries(
    tmp_path: Path, payload: str
) -> None:
    result = _sanitation_result(tmp_path, payload)
    assert result.returncode == 2
    assert "Absolute filesystem paths detected." in result.stderr


@pytest.mark.parametrize(
    "payload",
    [
        "Total:" + "\\n" + "Line2",
        "Rate:" + "\\t" + "tab",
        json.dumps(
            {
                "newline": "line1\nline2",
                "carriage_return": "left\rright",
                "tab": "left\tright",
            }
        ),
    ],
)
def test_repo_sanitation_allows_serialized_control_escapes(
    tmp_path: Path, payload: str
) -> None:
    result = _sanitation_result(tmp_path, payload)
    assert result.returncode == 0, result.stderr


def test_repo_sanitation_rejects_tracked_file_matched_by_ignore_rule(
    tmp_path: Path,
) -> None:
    result = _sanitation_result(
        tmp_path,
        "local review output",
        payload_path="design/review/capture.png",
        repository_ignore_rule="design/review/capture.png",
        force_track_payload=True,
    )
    assert result.returncode == 2
    assert "Tracked files matched by repository ignore rules:" in result.stderr
    assert "design/review/capture.png" in result.stderr


def test_repo_sanitation_allows_untracked_file_matched_by_ignore_rule(
    tmp_path: Path,
) -> None:
    result = _sanitation_result(
        tmp_path,
        "local review output",
        payload_path="design/review/capture.png",
        repository_ignore_rule="design/review/capture.png",
    )
    assert result.returncode == 0, result.stderr


def test_repo_sanitation_ignores_global_excludes_for_tracked_files(
    tmp_path: Path,
) -> None:
    result = _sanitation_result(
        tmp_path,
        "local review output",
        payload_path="design/review/capture.png",
        force_track_payload=True,
        global_exclude_rule="*.png",
    )
    assert result.returncode == 0, result.stderr


def test_repo_sanitation_ignores_info_exclude_for_tracked_files(tmp_path: Path) -> None:
    result = _sanitation_result(
        tmp_path,
        "local review output",
        payload_path="design/review/capture.png",
        force_track_payload=True,
        info_exclude_rule="*.png",
    )
    assert result.returncode == 0, result.stderr
