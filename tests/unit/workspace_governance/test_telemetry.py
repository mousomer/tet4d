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


def test_a_gov_run_is_observed_as_a_command_execution_with_enrichment(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    assert _gov(checkout, "check").returncode == 0
    assert _gov(checkout, "explain", "--task", TASK).returncode == 0

    check, explain = _events(directory)
    for event in (check, explain):
        assert telemetry.event_issues(event) == []
        # What happened is generic; how it was observed is provenance.
        assert event["event_type"] == "command_execution"
        assert event["payload"]["program"] == "gov"
        assert event["source"] == {
            "kind": "self_instrumented",
            "producer": "workspace-governance",
            "producer_version": telemetry.producer_version(),
        }
        assert event["attribution"] == {"basis": "first_hand"}
        assert event["context"] == {"status": "absent", "labels": {}}
        assert set(event["checkout"]) >= {"path_sha256"}
        assert set(event["payload"]["invocation"]) == {
            "process_id",
            "parent_process_id",
        }
    assert check["event_id"] != explain["event_id"]
    assert check["payload"]["arguments"] == [{"value": "check"}]
    assert check["payload"]["exit_status"] == 0
    assert check["payload"]["governance"] == {"subcommand": "check", "diagnostics": []}

    resolution = explain["payload"]["governance"]["resolution"]
    assert resolution["matched_scenario"] == "governance-change"
    assert resolution["routes"] == ["governance_and_tooling"]
    assert {item["authority_id"] for item in resolution["authorities"]}
    # Directory permissions keep the record private to its owner.
    assert directory.stat().st_mode & 0o077 == 0


def test_free_text_and_machine_paths_are_recorded_only_as_hashes(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    assert (
        _gov(checkout, "--root", str(checkout), "explain", "--task", TASK).returncode
        == 0
    )
    assert _gov(checkout, "explain", f"--task={TASK}").returncode == 0
    separate, joined = _events(directory)

    literal, root, subcommand, option, task = separate["payload"]["arguments"]
    assert (literal, subcommand, option) == (
        {"value": "--root"},
        {"value": "explain"},
        {"value": "--task"},
    )
    assert set(root) == set(task) == {"sha256", "length"}
    assert task["length"] == len(TASK)
    assert joined["payload"]["arguments"][1] == {"prefix": "--task=", **task}
    raw = "".join(path.read_text() for path in directory.glob("*.jsonl"))
    assert TASK not in raw
    assert str(checkout) not in raw


def test_argument_tokens_are_either_literal_or_hashed() -> None:
    sensitive = frozenset({"--secret"})
    tokens = telemetry.recorded_arguments(
        ["run", "--secret", "x", "--secret=y"], sensitive
    )
    assert tokens[:2] == [{"value": "run"}, {"value": "--secret"}]
    assert set(tokens[2]) == {"sha256", "length"}
    assert tokens[3]["prefix"] == "--secret="
    event = telemetry.build_command_execution(
        root=Path.cwd(),
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[{"value": "a", "sha256": "0" * 64, "length": 1}],
        exit_status=0,
        duration_ms=0,
    )
    assert telemetry.event_issues(event) == [
        "payload.arguments[0]: not a literal or a hash"
    ]


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
    diagnostics = event["payload"]["governance"]["diagnostics"]
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
        {
            variable: json.dumps(
                {
                    "agent": "a",
                    "model": "m",
                    "tool_call_id": "call-1",
                    "labels": {"arm": "B"},
                }
            )
        }
    )
    assert supplied == {
        "status": "supplied",
        "agent": "a",
        "model": "m",
        "tool_call_id": "call-1",
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
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[],
        exit_status=0,
        duration_ms=1,
    )
    assert telemetry.event_issues(event) == []
    del event["attribution"]
    with pytest.raises(telemetry.TelemetryError, match="attribution"):
        telemetry.append_event(tmp_path / "store", event)
    assert not (tmp_path / "store").exists()
