"""First-hand `gov` telemetry: recorded only when enabled, never interpreted."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from support import scrubbed_environment, write

from tools.workspace_governance import telemetry
from tools.workspace_governance.resolver.core import GovernanceResolver

TASK = "governance change to the telemetry core"


def _gov(checkout: Path, *args: str, **env: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["./gov", *args],
        cwd=checkout,
        env=scrubbed_environment(GOVERNANCE_PYTHON=sys.executable, **env),
        text=True,
        capture_output=True,
        check=False,
    )


def _enable(checkout: Path) -> Path:
    write(
        checkout / ".governance/workspace.local.json",
        {"schema_version": 1, "telemetry": {"enabled": True}},
    )
    settings = GovernanceResolver.for_root(checkout).telemetry_settings()
    assert settings.enabled and settings.directory is not None
    return settings.directory


def _events(directory: Path) -> list[dict]:
    return list(telemetry.iter_events(directory))


def test_nothing_is_recorded_unless_the_machine_enables_it(checkout: Path) -> None:
    settings = GovernanceResolver.for_root(checkout).telemetry_settings()
    assert settings.enabled is False
    assert _gov(checkout, "check").returncode == 0
    assert _events(settings.directory) == []
    state = Path(os.environ["XDG_STATE_HOME"])
    assert not any(state.rglob("*.jsonl"))


def test_an_enabled_checkout_records_one_valid_event_per_invocation(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    assert _gov(checkout, "check").returncode == 0
    assert _gov(checkout, "explain", "--task", TASK).returncode == 0

    check, explain = _events(directory)
    for event in (check, explain):
        assert telemetry.event_issues(event) == []
        assert event["source"] == {
            "kind": "gov_command",
            "producer": "workspace-governance",
            "producer_version": telemetry.producer_version(),
        }
        assert event["attribution"] == {"basis": "first_hand"}
        assert event["context"] == {"status": "absent", "labels": {}}
        assert set(event["checkout"]) >= {"path_sha256"}
    assert check["payload"]["command"] == "check"
    assert check["payload"]["exit_status"] == 0
    assert "resolution" not in check["payload"]

    resolution = explain["payload"]["resolution"]
    assert resolution["matched_scenario"] == "governance-change"
    assert resolution["routes"] == ["governance_and_tooling"]
    assert {item["authority_id"] for item in resolution["authorities"]}
    # Directory permissions keep the record private to its owner.
    assert directory.stat().st_mode & 0o077 == 0


def test_free_text_and_machine_paths_are_recorded_only_as_hashes(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    assert _gov(checkout, "explain", "--task", TASK).returncode == 0
    (event,) = _events(directory)
    arguments = event["payload"]["arguments"]
    assert set(arguments["task"]) == {"sha256", "length"}
    assert arguments["task"]["length"] == len(TASK)
    assert set(arguments["root"]) == {"sha256", "length"}
    raw = "".join(path.read_text() for path in directory.glob("*.jsonl"))
    assert TASK not in raw
    assert str(checkout) not in raw


def test_a_failing_command_records_its_status_and_diagnostic_identities(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    project_path = checkout / "config/governance/project.json"
    project = json.loads(project_path.read_text())
    project["routes"]["governance_and_tooling"]["authority_refs"].append("missing")
    write(project_path, project)

    assert _gov(checkout, "check").returncode == 1
    (event,) = _events(directory)
    assert event["payload"]["exit_status"] == 1
    diagnostics = event["payload"]["diagnostics"]
    assert {"code", "fact", "owner"} == set(diagnostics[0])
    assert "BROKEN_REFERENCE" in {item["code"] for item in diagnostics}


def test_recording_can_never_change_the_command_outcome(checkout: Path) -> None:
    _enable(checkout)
    blocked = checkout / "not-a-directory"
    blocked.write_text("")
    result = _gov(checkout, "check", XDG_STATE_HOME=str(blocked))
    assert result.returncode == 0
    assert json.loads(result.stdout) == {"status": "ok"}
    assert "telemetry not recorded" in result.stderr


def test_run_context_is_carried_and_malformed_context_is_marked() -> None:
    variable = telemetry.CONTEXT_VARIABLE
    supplied = telemetry.run_context(
        {variable: json.dumps({"agent": "a", "model": "m", "labels": {"arm": "B"}})}
    )
    assert supplied == {
        "status": "supplied",
        "agent": "a",
        "model": "m",
        "labels": {"arm": "B"},
    }
    for malformed in (
        "not json",
        json.dumps(["a"]),
        json.dumps({"agnet": "typo"}),
        json.dumps({"labels": {"arm": 2}}),
        json.dumps({"session_id": ""}),
    ):
        assert telemetry.run_context({variable: malformed}) == {
            "status": "invalid",
            "labels": {},
        }
    assert telemetry.run_context({}) == {"status": "absent", "labels": {}}


def test_the_store_is_keyed_by_a_safe_workspace_identity() -> None:
    state = {"XDG_STATE_HOME": "/state"}
    assert telemetry.store_directory("demo-workspace", state) == Path(
        "/state/workspace-governance/demo-workspace/telemetry"
    )
    assert telemetry.store_directory("../escape", state) is None
    assert not telemetry.resolve_settings(
        {"telemetry": {"enabled": True}}, "../escape", state
    ).enabled


def test_an_event_that_breaks_the_schema_is_refused(tmp_path: Path) -> None:
    event = telemetry.build_command_event(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        command="check",
        arguments={},
        exit_status=0,
        duration_ms=1,
        diagnostics=[],
    )
    assert telemetry.event_issues(event) == []
    del event["attribution"]
    with pytest.raises(telemetry.TelemetryError, match="attribution"):
        telemetry.append_event(tmp_path / "store", event)
    assert not (tmp_path / "store").exists()
