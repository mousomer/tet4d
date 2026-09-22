from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tools.experiments.governance_manifest_quality.baseline import ROOT
from tools.experiments.governance_manifest_quality.codex_rollout import (
    RejectedTrajectory,
    adapt_rollout,
    classify_repository_path,
)
from tools.experiments.governance_manifest_quality.measurement import measure_trajectory
from tools.governance.policy_pack_io import load_policy_pack


def _revision() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _session_meta() -> dict:
    return {
        "timestamp": "2026-09-01T00:00:00Z",
        "type": "session_meta",
        "payload": {
            "cwd": str(ROOT),
            "timestamp": "2026-09-01T00:00:00Z",
            "git": {"commit_hash": _revision()},
        },
    }


def _legacy_rows() -> list[dict]:
    command = "sed -n '1,2p' docs/governance/ENGINEERING.md"
    return [
        _session_meta(),
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps({"cmd": command}),
                "call_id": "call-1",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "call-1",
                "output": "Process exited with code 0\nFinal output:\nignored raw text",
            },
        },
    ]


def _custom_rows() -> list[dict]:
    tool_input = (
        "const r = await tools.exec_command({cmd:\"sed -n '1,2p' "
        'docs/governance/ENGINEERING.md"}); text(r.output);'
    )
    return [
        _session_meta(),
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "exec",
                "input": tool_input,
                "call_id": "call-2",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "call_id": "call-2",
                "output": [{"type": "text", "text": "exit_code: 0"}],
            },
        },
    ]


def test_legacy_and_custom_rollouts_normalize_to_same_metrics(tmp_path: Path) -> None:
    policy = load_policy_pack()
    legacy_path = tmp_path / "legacy.jsonl"
    custom_path = tmp_path / "custom.jsonl"
    _write_rows(legacy_path, _legacy_rows())
    _write_rows(custom_path, _custom_rows())
    legacy = adapt_rollout(legacy_path, ROOT, policy)
    custom = adapt_rollout(custom_path, ROOT, policy)
    assert not isinstance(legacy, RejectedTrajectory)
    assert not isinstance(custom, RejectedTrajectory)
    legacy_metrics = measure_trajectory(legacy)
    custom_metrics = measure_trajectory(custom)
    for key in legacy_metrics:
        if key != "source_id":
            assert legacy_metrics[key] == custom_metrics[key]
    assert legacy["source"]["source_format"] == "codex_rollout_legacy"
    assert custom["source"]["source_format"] == "codex_rollout_custom_tool"


def test_rollout_output_is_sanitized_and_repository_relative(tmp_path: Path) -> None:
    path = tmp_path / "rollout.jsonl"
    _write_rows(path, _legacy_rows())
    record = adapt_rollout(path, ROOT, load_policy_pack())
    assert not isinstance(record, RejectedTrajectory)
    serialized = json.dumps(record, sort_keys=True)
    assert str(ROOT) not in serialized
    assert "ignored raw text" not in serialized
    assert record["retrieval_events"][0]["path"] == ("docs/governance/ENGINEERING.md")


def test_apply_patch_is_mutation_not_retrieval(tmp_path: Path) -> None:
    patch_input = (
        'await tools.apply_patch("*** Begin Patch\\n*** Update File: '
        'config/project/policy_pack.json\\n*** End Patch");'
    )
    rows = [
        _session_meta(),
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call",
                "name": "exec",
                "input": patch_input,
                "call_id": "patch-1",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "custom_tool_call_output",
                "call_id": "patch-1",
                "output": [{"type": "text", "text": "ok"}],
            },
        },
    ]
    path = tmp_path / "patch.jsonl"
    _write_rows(path, rows)
    record = adapt_rollout(path, ROOT, load_policy_pack())
    assert not isinstance(record, RejectedTrajectory)
    metrics = measure_trajectory(record)
    assert metrics["governance_read_events"] == 0
    assert metrics["governance_mutation_events"] == 1
    assert metrics["governance_total_materialized_bytes"] == 0


def test_malformed_and_other_repository_rollouts_are_rejected(tmp_path: Path) -> None:
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{not json}\n", encoding="utf-8")
    rejected = adapt_rollout(malformed, ROOT, load_policy_pack())
    assert isinstance(rejected, RejectedTrajectory)
    assert rejected.status == "rejected_during_ingestion"
    assert rejected.reason.startswith("malformed_json_line:")

    other = tmp_path / "other.jsonl"
    rows = _legacy_rows()
    rows[0]["payload"]["cwd"] = "/redacted/other-repository"
    rows[0]["payload"]["git"]["commit_hash"] = "0" * 40
    _write_rows(other, rows)
    rejected = adapt_rollout(other, ROOT, load_policy_pack())
    assert isinstance(rejected, RejectedTrajectory)
    assert rejected.status == "excluded"
    assert rejected.reason == "different_repository"


def test_unaccountable_rollout_states_have_explicit_statuses(tmp_path: Path) -> None:
    missing = tmp_path / "missing.jsonl"
    _write_rows(
        missing,
        [{"type": "response_item", "payload": {"type": "message", "role": "user"}}],
    )
    result = adapt_rollout(missing, ROOT, load_policy_pack())
    assert isinstance(result, RejectedTrajectory)
    assert (result.status, result.reason) == (
        "missing_required_provenance",
        "repository_identity_unavailable",
    )

    unsupported = tmp_path / "unsupported.jsonl"
    _write_rows(
        unsupported,
        [_session_meta(), {"type": "event_msg", "payload": {"type": "unknown"}}],
    )
    result = adapt_rollout(unsupported, ROOT, load_policy_pack())
    assert isinstance(result, RejectedTrajectory)
    assert (result.status, result.reason) == (
        "unsupported_format",
        "no_supported_response_envelope",
    )

    incomplete = tmp_path / "incomplete.jsonl"
    _write_rows(
        incomplete,
        [
            _session_meta(),
            {
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps({"cmd": "pwd"}),
                    "call_id": "unfinished",
                },
            },
        ],
    )
    result = adapt_rollout(incomplete, ROOT, load_policy_pack())
    assert isinstance(result, RejectedTrajectory)
    assert (result.status, result.reason) == (
        "excluded_after_normalization",
        "incomplete_tool_calls",
    )


def test_path_classifier_separates_governance_and_ordinary_code() -> None:
    active = {"AGENTS.md", "docs/BACKLOG.md"}
    assert classify_repository_path("AGENTS.md", active) == (
        "governance",
        "active_governance",
    )
    assert classify_repository_path("tools/governance/check.py", active) == (
        "governance",
        "governance_mechanism",
    )
    assert classify_repository_path("src/tet4d/engine/model.py", active) == (
        "non_governance",
        None,
    )


def test_search_materialization_is_explicitly_incomplete(tmp_path: Path) -> None:
    command = 'rg -n "Canonical owner" docs/governance/ENGINEERING.md'
    rows = [
        _session_meta(),
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps({"cmd": command}),
                "call_id": "search-1",
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": "search-1",
                "output": "Process exited with code 0\nFinal output:\n1:Canonical owner",
            },
        },
    ]
    path = tmp_path / "search.jsonl"
    _write_rows(path, rows)
    record = adapt_rollout(path, ROOT, load_policy_pack())
    assert not isinstance(record, RejectedTrajectory)
    metrics = measure_trajectory(record)
    assert metrics["governance_read_events"] == 1
    assert metrics["governance_total_materialized_bytes"] is None
    assert metrics["governance_known_materialized_bytes"] == 0
    assert metrics["measurement_complete"] is False
    assert record["evidence_limitations"] == [
        {
            "kind": "search_materialization_unresolved",
            "event_sequence": None,
            "interaction_segment_id": None,
        }
    ]


def test_recorded_model_tokens_and_duration_are_preserved(tmp_path: Path) -> None:
    rows = _legacy_rows()
    rows.insert(
        1,
        {
            "type": "turn_context",
            "payload": {"cwd": str(ROOT), "model": "recorded-model"},
        },
    )
    rows.extend(
        [
            {
                "type": "event_msg",
                "payload": {
                    "type": "token_count",
                    "info": {
                        "total_token_usage": {
                            "input_tokens": 10,
                            "output_tokens": 4,
                            "total_tokens": 14,
                        },
                        "model_context_window": 1000,
                    },
                },
            },
            {
                "type": "event_msg",
                "payload": {"type": "task_complete", "duration_ms": 250},
            },
        ]
    )
    path = tmp_path / "metadata.jsonl"
    _write_rows(path, rows)
    record = adapt_rollout(path, ROOT, load_policy_pack())
    assert not isinstance(record, RejectedTrajectory)
    assert record["source"]["model"] == "recorded-model"
    assert record["source"]["elapsed_ms"] == 250
    assert record["source"]["token_information"] == {
        "total_token_usage": {
            "input_tokens": 10,
            "output_tokens": 4,
            "total_tokens": 14,
        },
        "model_context_window": 1000,
    }


# Shapes below are copied from real Codex rollouts: the harness sends its own
# context blocks with the user role, ahead of the human request, and names the
# absolute repository root in them.
INJECTED_CONTEXT = (
    "<recommended_plugins>\nplugins\n</recommended_plugins>\n"
    f"# AGENTS.md instructions for {ROOT}\n"
    f"<environment_context>\n  <cwd>{ROOT}</cwd>\n</environment_context>"
)
HUMAN_REQUEST = "Stage 56G repair: keep this prompt text out of C1 output"


def _user(text: str | list[str], kinds: list[str] | None = None) -> dict:
    parts = [text] if isinstance(text, str) else text
    payload: dict = {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": part} for part in parts],
    }
    if kinds is not None:
        payload["internal_chat_message_metadata_passthrough"] = {
            "content_item_kinds": kinds
        }
    return {"type": "response_item", "payload": payload}


def _user_message_item(text: str) -> dict:
    return {
        "type": "event_msg",
        "payload": {
            "type": "item_completed",
            "item": {
                "type": "UserMessage",
                "content": [{"type": "text", "text": text}, {"type": "local_image"}],
            },
        },
    }


def _read_call(call_id: str) -> list[dict]:
    return [
        {
            "type": "response_item",
            "payload": {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps(
                    {"cmd": "sed -n '1,2p' docs/governance/ENGINEERING.md"}
                ),
                "call_id": call_id,
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "function_call_output",
                "call_id": call_id,
                "output": "Process exited with code 0",
            },
        },
    ]


def _adapt(tmp_path: Path, rows: list[dict]) -> dict:
    path = tmp_path / "rollout.jsonl"
    _write_rows(path, rows)
    record = adapt_rollout(path, ROOT, load_policy_pack())
    assert not isinstance(record, RejectedTrajectory)
    return record


def test_human_turns_use_content_kinds_and_keep_prompts_out_of_output(
    tmp_path: Path,
) -> None:
    record = _adapt(
        tmp_path,
        [
            _session_meta(),
            _user(
                INJECTED_CONTEXT,
                [
                    "plugins.recommendations",
                    "agents_md.instructions",
                    "environments.environment_context",
                ],
            ),
            _user(HUMAN_REQUEST, ["user.text"]),
            *_read_call("call-1"),
        ],
    )
    (segment,) = record["interaction_segments"]
    assert segment == {
        "id": f"{record['source']['source_id']}:user-3",
        "unit": "human_turn",
        "start_row_index": 3,
        "end_row_index": 6,
        "turn_text_sha256": hashlib.sha256(HUMAN_REQUEST.encode()).hexdigest(),
        "boundary_evidence": "content_item_kinds",
    }
    labelled = record["retrieval_events"] + record["execution_events"]
    assert {event["interaction_segment_id"] for event in labelled} == {segment["id"]}
    serialized = json.dumps(record, sort_keys=True)
    for text in ("Stage 56G repair", "recommended_plugins", "AGENTS.md", str(ROOT)):
        assert text not in serialized


def test_human_turns_fall_back_to_harness_user_message_items(
    tmp_path: Path,
) -> None:
    request = (
        "\n# Files mentioned by the user:\n\n## shot.png\n\n## My request:\nfix it"
    )
    record = _adapt(
        tmp_path,
        [
            _session_meta(),
            _user(
                "# AGENTS.md instructions for /repo\n\n<INSTRUCTIONS>x</INSTRUCTIONS>"
            ),
            _user("<environment_context>\n  <cwd>/repo</cwd>\n</environment_context>"),
            # An image input splits the text around it; the item keeps one part.
            _user([request, "<image name=[Image #1]>", "</image>"]),
            _user_message_item(request),
            *_read_call("call-1"),
        ],
    )
    (segment,) = record["interaction_segments"]
    assert (segment["start_row_index"], segment["boundary_evidence"]) == (
        4,
        "user_message_item",
    )


def test_known_injected_forms_are_only_the_last_resort(tmp_path: Path) -> None:
    record = _adapt(
        tmp_path,
        [
            _session_meta(),
            _user("<recommended_plugins>\nplugins\n</recommended_plugins>"),
            _user("commit and push"),
            *_read_call("call-1"),
        ],
    )
    (segment,) = record["interaction_segments"]
    assert (segment["start_row_index"], segment["boundary_evidence"]) == (
        3,
        "known_injected_forms",
    )


def test_rollout_without_a_human_turn_keeps_unsegmented_c1_evidence(
    tmp_path: Path,
) -> None:
    developer_task = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "developer",
            "content": [{"type": "input_text", "text": "You are a sub-agent"}],
        },
    }
    record = _adapt(tmp_path, [_session_meta(), developer_task, *_read_call("c-1")])
    assert record["schema_version"] == 2
    assert record["interaction_segments"] == []
    assert record["retrieval_events"][0]["interaction_segment_id"] is None
    assert measure_trajectory(record)["governance_read_events"] == 1
