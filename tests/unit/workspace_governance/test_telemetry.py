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
from tools.workspace_governance.cli import gov
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
        assert "/" not in event["payload"]["program"]
        assert event["payload"]["phase"] == "completion"
        assert event["payload"]["exit_status"] == 0
        assert isinstance(event["observed_at"], str)
        assert isinstance(event["recorded_at"], str)
        assert event["source"] == {
            "kind": "self_instrumented",
            "producer": "workspace-governance",
            "producer_version": telemetry.producer_version(),
        }
        assert event["attribution"] == {"basis": "first_hand"}
        assert event["context"] == {"status": "absent", "labels": {}}
        assert set(event["checkout"]) >= {"path"}
        assert set(event["checkout"]["path"]) == {
            "hmac_sha256",
            "key_id",
            "normalization",
        }
        assert set(event["payload"]["invocation"]) == {
            "process_id",
            "parent_process_id",
        }
    assert check["observation_id"] != explain["observation_id"]
    assert check["payload"]["arguments"] == [{"value": "check"}]
    assert check["payload"]["exit_status"] == 0
    assert check["payload"]["governance"] == {"subcommand": "check", "diagnostics": []}

    resolution = explain["payload"]["governance"]["resolution"]
    assert resolution["matched_scenario"] == "governance-change"
    assert resolution["routes"] == ["governance_and_tooling"]
    assert {item["authority_id"] for item in resolution["authorities"]}
    # Directory permissions keep the record private to its owner.
    assert directory.stat().st_mode & 0o077 == 0
    # The key sits beside the events, so copying them never carries it along.
    assert not (directory / telemetry.KEY_FILENAME).exists()
    assert (directory.parent / telemetry.KEY_FILENAME).stat().st_mode & 0o077 == 0


def test_free_text_and_machine_paths_are_keyed_private_identities(
    checkout: Path,
) -> None:
    directory = _enable(checkout)
    assert (
        _gov(checkout, "--root", str(checkout), "explain", "--task", TASK).returncode
        == 0
    )
    assert _gov(checkout, "explain", f"--task={TASK}").returncode == 0
    # The query is deliberately unknown, but failed invocations are observations
    # too and must not retain its free-form value.
    assert _gov(checkout, "explain", "arbitrary positional text").returncode == 1
    separate, joined, positional = _events(directory)

    literal, root, subcommand, option, task = separate["payload"]["arguments"]
    assert (literal, subcommand, option) == (
        {"value": "--root"},
        {"value": "explain"},
        {"value": "--task"},
    )
    assert (
        set(root)
        == set(task)
        == {
            "hmac_sha256",
            "key_id",
            "normalization",
            "length",
        }
    )
    assert task["length"] == len(TASK)
    assert task["key_id"] == root["key_id"]
    assert task["normalization"] == root["normalization"] == "gov-argv-1"
    assert joined["payload"]["arguments"][1] == {"prefix": "--task=", **task}
    positional_token = positional["payload"]["arguments"][1]
    assert positional_token["normalization"] == "gov-argv-1"
    assert positional_token["length"] == len("arbitrary positional text")
    raw = "".join(path.read_text() for path in directory.glob("*.jsonl"))
    assert TASK not in raw
    assert str(checkout) not in raw
    assert "arbitrary positional text" not in raw


def test_gov_argument_tokens_are_structural_literals_or_keyed_identities(
    tmp_path: Path,
) -> None:
    key = telemetry.telemetry_key(tmp_path / "telemetry")
    tokens = telemetry.recorded_gov_arguments(
        ["--root", "/machine/path", "resolve", "--mode", "FEATURE"], key
    )
    assert tokens[0] == {"value": "--root"}
    assert set(tokens[1]) == {"hmac_sha256", "key_id", "normalization", "length"}
    assert tokens[2:] == [
        {"value": "resolve"},
        {"value": "--mode"},
        {"value": "FEATURE"},
    ]
    event = telemetry.build_command_execution(
        root=Path.cwd(),
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[{"value": "a", "sha256": "0" * 64, "length": 1}],
        key=key,
        exit_status=0,
        duration_ms=0,
    )
    assert any(
        "payload.arguments[0]: not a literal or keyed private identity" == issue
        for issue in telemetry.event_issues(event)
    )


def test_completion_observations_allow_future_producers_to_omit_results(
    tmp_path: Path,
) -> None:
    key = telemetry.telemetry_key(tmp_path / "telemetry")
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[],
        key=key,
    )
    assert event["payload"]["phase"] == "completion"
    assert "exit_status" not in event["payload"]
    assert "duration_ms" not in event["payload"]
    assert telemetry.event_issues(event) == []


def test_private_identities_correlate_only_with_the_same_telemetry_key(
    tmp_path: Path,
) -> None:
    first = telemetry.telemetry_key(tmp_path / "first")
    second = telemetry.telemetry_key(tmp_path / "second")
    value = "free-form task text"
    first_identity = telemetry.private_identity(
        value, first, normalization=telemetry.GOV_ARGV_NORMALIZATION
    )
    assert first_identity == telemetry.private_identity(
        value, first, normalization=telemetry.GOV_ARGV_NORMALIZATION
    )
    second_identity = telemetry.private_identity(
        value, second, normalization=telemetry.GOV_ARGV_NORMALIZATION
    )
    assert first_identity["key_id"] != second_identity["key_id"]
    assert first_identity["hmac_sha256"] != second_identity["hmac_sha256"]


def test_an_interrupted_key_creation_leaves_no_partial_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def interrupted(*_args: object) -> None:
        raise OSError("interrupted before the key was published")

    with monkeypatch.context() as patch:
        patch.setattr(telemetry.os, "link", interrupted)
        with pytest.raises(OSError, match="interrupted"):
            telemetry.telemetry_key(tmp_path)
    # Neither a partial key nor the staging file remains to block recording.
    assert list(tmp_path.iterdir()) == []
    key = telemetry.telemetry_key(tmp_path)
    assert len(key.secret) == telemetry.KEY_BYTES


def test_a_process_that_loses_the_key_race_uses_the_published_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    winner = bytes(range(telemetry.KEY_BYTES))
    link = os.link

    def published_first(source: str, destination: Path) -> None:
        Path(destination).write_bytes(winner)
        link(source, destination)

    monkeypatch.setattr(telemetry.os, "link", published_first)
    assert telemetry.telemetry_key(tmp_path).secret == winner
    assert [path.name for path in tmp_path.iterdir()] == [telemetry.KEY_FILENAME]


def test_the_reader_refuses_unsupported_schema_versions(tmp_path: Path) -> None:
    key = telemetry.telemetry_key(tmp_path)
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[],
        key=key,
    )
    # A later v1 revision may add event types; this reader still yields them.
    future = {**event, "event_type": "future_observation"}
    store = tmp_path / "store"
    store.mkdir()
    (store / "events-2026-09-25.jsonl").write_text(
        json.dumps(future) + "\n" + json.dumps({**event, "schema_version": 2}) + "\n"
    )
    events = telemetry.iter_events(store)
    assert next(events)["event_type"] == "future_observation"
    with pytest.raises(telemetry.TelemetryError, match=r":2: unsupported .* 2"):
        next(events)


def test_optional_source_and_evidence_references_validate(tmp_path: Path) -> None:
    key = telemetry.telemetry_key(tmp_path / "telemetry")
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="/machine-local/bin/gov",
        arguments=[],
        key=key,
    )
    event["source"].update(
        {"source_ref": "call_abc", "evidence_ref": "transcript-item-42"}
    )
    assert event["payload"]["program"] == "gov"
    assert telemetry.event_issues(event) == []


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
                    "labels": {"arm": "B"},
                }
            )
        }
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
        json.dumps({"tool_call_id": "call-1"}),
    ):
        assert telemetry.run_context({variable: malformed}) == {
            "status": "invalid",
            "labels": {},
        }
    assert telemetry.run_context({}) == {"status": "absent", "labels": {}}


def test_unexpected_telemetry_exception_cannot_change_command_status(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(gov, "_dispatch", lambda *_args: 23)

    def fail_record(*_args: object) -> None:
        raise RuntimeError("unexpected telemetry failure")

    monkeypatch.setattr(gov, "_record", fail_record)
    assert gov.main(["check"]) == 23
    assert (
        "telemetry not recorded: unexpected telemetry failure"
        in capsys.readouterr().err
    )


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
    key = telemetry.telemetry_key(tmp_path / "telemetry")
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[],
        key=key,
        exit_status=0,
        duration_ms=1,
    )
    assert telemetry.event_issues(event) == []
    del event["attribution"]
    with pytest.raises(telemetry.TelemetryError, match="attribution"):
        telemetry.append_event(tmp_path / "store", event)
    assert not (tmp_path / "store").exists()


def test_append_uses_recorded_time_not_the_time_an_observation_describes(
    tmp_path: Path,
) -> None:
    key = telemetry.telemetry_key(tmp_path / "telemetry")
    event = telemetry.build_command_execution(
        root=tmp_path,
        workspace_id="demo",
        project_id=None,
        producer_version="0.0.0",
        program="demo",
        arguments=[],
        key=key,
        observed_at="2026-09-20T12:00:00Z",
        recorded_at="2026-09-25T12:00:00Z",
    )
    path = telemetry.append_event(tmp_path / "store", event)
    assert path.name == "events-2026-09-25.jsonl"
