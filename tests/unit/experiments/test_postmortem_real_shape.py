"""End-to-end post-mortem regression over evidence shaped by its real producers.

The trajectory comes from the real C1 Codex adapter, so reads carry C1's real
source classes and null ``authority``/``route``.  The resolver output is a
captured ``gov --json explain`` probe, and G1 artifacts carry roles resolved by
the real G1 role index.  Only the evaluator overlay is judgement.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tools.experiments.governance_manifest_quality.baseline import ROOT
from tools.experiments.governance_manifest_quality.cli import main
from tools.experiments.governance_manifest_quality.codex_rollout import adapt_rollout
from tools.experiments.governance_manifest_quality.postmortem import (
    ACTIVITY_CATEGORIES,
    PROXY_FIELDS,
)
from tools.governance.policy_pack_io import load_policy_pack

FIXTURES = ROOT / "tests/fixtures/governance_postmortem"
SCHEMAS = ROOT / "tools/experiments/governance_manifest_quality/schemas"
VERIFICATION = "docs/governance/VERIFICATION.md"
COMMANDS = (
    ("git status --short", 0),
    ("sed -n '1,40p' docs/ARCHITECTURE_CONTRACT.md", 0),
    (f"sed -n '1,60p' {VERIFICATION}", 0),
    (f"sed -n '61,120p' {VERIFICATION}", 0),
    (f"sed -n '1,60p' {VERIFICATION}", 0),
    ("cat AGENTS.md", 0),
    ("./scripts/verify_focus.sh godot --pytest tests/unit/experiments", 1),
    ("./scripts/verify_focus.sh godot --pytest tests/unit/experiments", 0),
)


TASK_PROMPT = "Stage 56G cockpit scaling"
# Real Codex Desktop structure: harness context arrives with the user role and
# its own content kinds, ahead of the human request (as in rollout 01a0c497).
INJECTED_KINDS = [
    "plugins.recommendations",
    "agents_md.instructions",
    "environments.environment_context",
]
INJECTED_TEXT = (
    "<recommended_plugins>\nplugins\n</recommended_plugins>\n"
    f"# AGENTS.md instructions for {ROOT}\n"
    f"<environment_context>\n  <cwd>{ROOT}</cwd>\n</environment_context>"
)
ENVIRONMENT_REFRESH = "<environment_context>\n  <current_date>2026-09-21</current_date>"


def _response(payload: dict) -> dict:
    return {"type": "response_item", "payload": payload}


def _user(text: str, kinds: list[str]) -> dict:
    return _response(
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
            "internal_chat_message_metadata_passthrough": {"content_item_kinds": kinds},
        }
    )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _rollout_rows() -> list[dict]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    rows = [
        {
            "type": "session_meta",
            "payload": {
                "cwd": str(ROOT),
                "timestamp": "2026-09-20T10:00:00Z",
                "git": {"commit_hash": revision},
            },
        },
        _user(INJECTED_TEXT, INJECTED_KINDS),
        {
            "type": "turn_context",
            "payload": {"cwd": str(ROOT), "model": "gpt-5.6-terra"},
        },
        _user(TASK_PROMPT, ["user.text"]),
    ]
    for index, (command, exit_code) in enumerate(COMMANDS, 1):
        rows += [
            _response(
                {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": json.dumps({"cmd": command}),
                    "call_id": f"call-{index}",
                }
            ),
            _response(
                {
                    "type": "function_call_output",
                    "call_id": f"call-{index}",
                    "output": f"Process exited with code {exit_code}\nOutput:\n",
                }
            ),
        ]
    # An idle poll has no command; the current Codex Desktop exec form quotes
    # its "cmd" key, which C1 does not yet recover, so that RDS read is unseen.
    quoted = "sed -n '1,20p' docs/rds/RDS_TETRIS_GENERAL.md"
    rows += [
        _response(
            {
                "type": "function_call",
                "name": "write_stdin",
                "arguments": json.dumps({"session_id": 7, "chars": ""}),
                "call_id": "call-poll",
            }
        ),
        _response(
            {
                "type": "function_call_output",
                "call_id": "call-poll",
                "output": "Process running with session ID 7",
            }
        ),
        _response(
            {
                "type": "custom_tool_call",
                "name": "exec",
                "call_id": "call-quoted",
                "input": "const r = await tools.exec_command("
                + json.dumps({"cmd": quoted})
                + "); text(r.output);",
            }
        ),
        _response(
            {
                "type": "custom_tool_call_output",
                "call_id": "call-quoted",
                "output": "Script completed\nOutput:\n",
            }
        ),
        {
            "type": "event_msg",
            "payload": {
                "type": "token_count",
                "info": {"total_token_usage": {"total_tokens": 5000}},
            },
        },
        {
            "type": "event_msg",
            "payload": {"type": "task_complete", "duration_ms": 600000},
        },
    ]
    return rows


def _g1_record() -> dict:
    # Roles are the real G1 role-index resolutions for these paths at a262bc31.
    unclassified = {
        "role": "unclassified",
        "role_provenance": "unclassified",
        "role_source": None,
        "compatibility": "unclassified",
    }
    return {
        "schema_version": 1,
        "observer_mode": "log_only",
        "authoritative": False,
        "segment": {
            "segment_id": "stage-56g-fixture",
            "work_type": "Coding",
            "task_id": "stage-56g",
            "session_id": None,
        },
        "start_boundary": {"head": "1" * 40, "observed_at": "2026-09-20T10:00:00Z"},
        "end_boundary": {"head": "2" * 40, "observed_at": "2026-09-20T10:10:00Z"},
        "artifacts": [
            {
                "path": "docs/BACKLOG.md",
                "change_kind": "modified",
                "role": "bookkeeping",
                "role_provenance": "bootstrap_projected",
                "role_source": "config/governance/project.json#/authorities/12 (open-work-backlog)",
                "compatibility": "compatible",
            },
            {
                "path": "godot/Tet4D.Godot/scripts/ui/live_cockpit.gd",
                "change_kind": "modified",
                **unclassified,
            },
            {
                "path": "godot/Tet4D.Godot/tests/test_stage_56g_responsive_cockpit.gd",
                "change_kind": "created",
                **unclassified,
            },
        ],
        "telemetry": {
            "segment_count": 1,
            "files_written": 3,
            "elapsed_seconds": 600.0,
            "tool_call_count": 0,
            "failures": 0,
            "retries": 0,
        },
    }


def _human_turn(text: str) -> dict:
    return _user(text, ["user.text"])


def _call(call_id: str, command: str) -> list[dict]:
    return [
        _response(
            {
                "type": "function_call",
                "name": "exec_command",
                "arguments": json.dumps({"cmd": command}),
                "call_id": call_id,
            }
        ),
        _response(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": "Process exited with code 0\n",
            }
        ),
    ]


def _patch_call(call_id: str, path: str) -> list[dict]:
    patch = f"*** Begin Patch\\n*** Update File: {path}\\n*** End Patch"
    return [
        _response(
            {
                "type": "custom_tool_call",
                "name": "exec",
                "input": f'await tools.apply_patch("{patch}");',
                "call_id": call_id,
            }
        ),
        _response(
            {
                "type": "custom_tool_call_output",
                "call_id": call_id,
                "output": "Process exited with code 0\n",
            }
        ),
    ]


def _two_turn_rollout_rows(
    first: str = "Task A: Godot repair", second: str = "Task B: Python repair"
) -> list[dict]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    rows = [
        {
            "type": "session_meta",
            "payload": {
                "cwd": str(ROOT),
                "timestamp": "2026-09-21T10:00:00Z",
                "git": {"commit_hash": revision},
            },
        },
        _user(INJECTED_TEXT, INJECTED_KINDS),
        {"type": "turn_context", "payload": {"cwd": str(ROOT), "model": "fixture"}},
        _human_turn(first),
    ]
    for call_id, command in (
        ("a-1", "sed -n '1,2p' docs/governance/VERIFICATION.md"),
        ("a-2", "sed -n '1,2p' docs/ARCHITECTURE_CONTRACT.md"),
        ("a-3", "true"),
    ):
        rows.extend(_call(call_id, command))
    rows.extend(_patch_call("a-4", "godot/Tet4D.Godot/project.godot"))
    # Mid-session context refreshes are injected too and open no human turn.
    rows.append(_user(ENVIRONMENT_REFRESH, ["environments.environment_context"]))
    rows.append(_human_turn(second))
    for call_id, command in (
        ("b-1", "sed -n '1,2p' docs/governance/ENGINEERING.md"),
        ("b-2", "sed -n '1,2p' docs/governance/VERIFICATION.md"),
        ("b-3", "true"),
        ("b-4", "true"),
        ("b-5", "true"),
        ("b-6", "true"),
    ):
        rows.extend(_call(call_id, command))
    rows.extend(_patch_call("b-7", "src/tet4d/engine/api.py"))
    return rows


def _projection(task_text: str, route: str, source: str) -> dict:
    return {
        "task_text": task_text,
        "resolver_output": {
            "schema_version": 1,
            "entries": {
                "matched_scenario": {"value": None},
                "routes": {"value": {route: {"dispatch_paths": []}}},
                "authorities": {"value": [{"authority_id": source, "source": source}]},
            },
        },
    }


def _contract(schema_name: str, payload: dict) -> None:
    schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
    assert set(schema["required"]) <= set(payload) <= set(schema["properties"])


def test_real_shaped_evidence_produces_truthful_postmortem(tmp_path: Path) -> None:
    rollout = tmp_path / "rollout.jsonl"
    rollout.write_text(
        "".join(json.dumps(row) + "\n" for row in _rollout_rows()), encoding="utf-8"
    )
    trajectory = adapt_rollout(rollout, ROOT, load_policy_pack())
    assert isinstance(trajectory, dict)
    reads = trajectory["retrieval_events"]
    # Premises come from the real producer, not from fixture assumptions.
    assert [event["path"] for event in reads] == [
        "docs/ARCHITECTURE_CONTRACT.md",
        VERIFICATION,
        VERIFICATION,
        VERIFICATION,
        "AGENTS.md",
    ]
    assert all(event["authority"] is None and event["route"] is None for event in reads)
    assert reads[0]["source_class"] == "non_governance"
    trajectory_id = trajectory["source"]["source_id"]
    (segment,) = trajectory["interaction_segments"]
    segment_id = segment["id"]
    evaluation = {
        "interaction": {
            "description": "cockpit scaling repair (evaluator summary)",
            "task_class": "implementation",
        },
        "activity": {
            "product": {"action_count": 6},
            "meta_required": {"action_count": 2},
            "waste": {"action_count": 1},
        },
        "manifest_effects": [
            {
                "source": VERIFICATION,
                "encountered_at": reads[1]["sequence"],
                "decision": "kept the targeted verify_focus gate already chosen",
                "effect": "confirmatory",
                "outcome_evidence": "the targeted gate failed once and then passed",
                "confidence": "medium",
            }
        ],
    }
    probe = json.loads(
        (FIXTURES / "resolver_stage56g_natural_probe.json").read_text(encoding="utf-8")
    )
    inputs = {
        "trajectory": trajectory,
        "evaluator": {
            "source_trajectory_id": trajectory_id,
            "interaction_segment_id": segment_id,
            "evaluation": evaluation,
        },
        "resolver": {
            "source_trajectory_id": trajectory_id,
            "interaction_segment_id": segment_id,
            "resolver_evidence": probe["resolver_evidence"],
        },
        "segment": {
            "source_trajectory_id": trajectory_id,
            "interaction_segment_id": segment_id,
            "work_segment": _g1_record(),
        },
    }
    for name, payload in inputs.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "postmortem.json"
    arguments = ["postmortem", "--output", str(output)]
    for flag, name in (
        ("--trajectory", "trajectory"),
        ("--evaluator", "evaluator"),
        ("--resolver-evidence", "resolver"),
        ("--segment", "segment"),
    ):
        arguments += [flag, str(tmp_path / f"{name}.json")]
    assert main(arguments) == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    (record,) = result["postmortems"]
    aggregate = result["aggregate"]
    _contract("postmortem.schema.json", record)
    _contract("postmortem_aggregate.schema.json", aggregate)
    _contract("trajectory.schema.json", trajectory)

    # The injected context opens no human turn, so this single-turn session keeps
    # its rollout token and time totals, and no prompt text leaves the source.
    assert (segment["unit"], segment["boundary_evidence"]) == (
        "human_turn",
        "content_item_kinds",
    )
    assert segment["turn_text_sha256"] == _sha256(TASK_PROMPT)
    assert record["activity_total"]["token_count"] == 5000
    assert record["activity_total"]["elapsed_ms"] == 600000
    assert result["diagnostics"] == []
    assert probe["resolver_evidence"]["task_text"] != TASK_PROMPT
    published = json.dumps(trajectory) + output.read_text(encoding="utf-8")
    for text in (
        TASK_PROMPT,
        "recommended_plugins",
        "AGENTS.md instructions",
        str(ROOT),
    ):
        assert text not in published
    assert record["interaction"]["g1_task_id"] == {
        "value": "stage-56g",
        "evidence_state": "recorded",
    }

    # Projected-read matching: a read authority is read whatever its C1 class.
    comparison = record["projected_read_comparison"]
    assert {entry["source"] for entry in comparison["projected_and_read"]} == {
        "docs/ARCHITECTURE_CONTRACT.md",
        VERIFICATION,
    }
    assert {entry["source"] for entry in comparison["projected_not_observed_read"]} == {
        "docs/architecture/authority_map.md",
        "docs/governance/CONFIG_AND_GENERATED_DATA.md",
        "docs/governance/ENGINEERING.md",
        "docs/rds/",
    }
    assert comparison["read_not_projected"] == [
        {"source": "AGENTS.md", "observed_read_sequences": [reads[4]["sequence"]]}
    ]

    # Rereads: one segment, three encounters, segment activity counted once.
    verification = aggregate["by_manifest"][VERIFICATION]
    assert (
        verification["interaction_segment_count"],
        verification["encounter_count"],
    ) == (1, 3)
    assert verification["activity"]["action_count"]["product"] == 6

    # Conservation over C1 totals; G1's unreported 0 tool calls overrides nothing.
    assert record["activity_total"]["action_count"] == 10
    assert record["activity"]["unknown"]["action_count"] == 1
    for proxy in PROXY_FIELDS:
        assert (
            sum(
                record["activity"][category][proxy] or 0
                for category in ACTIVITY_CATEGORIES
            )
            == record["activity_total"][proxy]
        )

    # Yield: one judged encounter with no positive contribution is 0.0, while a
    # source nobody judged has no yield at all.
    assert aggregate["overall"]["judged_encounter_count"] == 1
    assert aggregate["overall"]["decision_yield"] == 0.0
    assert aggregate["by_manifest"]["AGENTS.md"]["decision_yield"] is None

    # No rule/section identity is invented for real reads.
    assert all(
        effect["rule_or_section"] is None for effect in record["manifest_effects"]
    )
    assert all("#" not in key for key in aggregate["by_manifest"])

    # Causal safety: projection, success, and mismatch create no contribution.
    judged = [e for e in record["manifest_effects"] if e["effect"] != "unknown"]
    assert [(e["source"], e["encountered_at"]) for e in judged] == [
        (VERIFICATION, reads[1]["sequence"])
    ]

    # Partial exposure is explicit: the poll and the quoted exec recovered nothing.
    assert (
        record["encounter_coverage"]["execution_events_without_recovered_command"] == 2
    )
    assert "partial exposure: 2 of 10 tool calls" in result["summaries"][0]

    failing = [
        event["sequence"]
        for event in trajectory["execution_events"]
        if event["is_test"] and event["exit_code"] == 1
    ]
    assert record["outcome"]["verification_failures"] == failing != []
    assert record["interaction"]["id"] == {
        "value": segment_id,
        "evidence_state": "derived",
    }
    alignment = record["route_work_alignment"]
    assert alignment["projected_routes"] == ["python_reference_engine"]
    assert alignment["dedicated_routes_not_projected"] == ["godot_product_shell"]
    assert (alignment["state"], alignment["causal_interpretation"]) == (
        "mismatch_observed",
        "unknown",
    )
    assert record["artifact_coverage"] == {
        "observed": 3,
        "classified": 1,
        "unclassified": 2,
        "interpretation": {"state": "migration_limited", "normative": False},
    }


def test_real_adapter_scopes_a_multi_turn_rollout_and_cli_overlays(
    tmp_path: Path,
) -> None:
    rollout = tmp_path / "two-turns.jsonl"
    rollout.write_text(
        "".join(json.dumps(row) + "\n" for row in _two_turn_rollout_rows()),
        encoding="utf-8",
    )
    trajectory = adapt_rollout(rollout, ROOT, load_policy_pack())
    assert isinstance(trajectory, dict)
    # Two human turns; neither injected block (initial or refresh) opens one.
    first, second = trajectory["interaction_segments"]
    source_id = trajectory["source"]["source_id"]
    assert [segment["turn_text_sha256"] for segment in (first, second)] == [
        _sha256("Task A: Godot repair"),
        _sha256("Task B: Python repair"),
    ]
    assert first["end_row_index"] == second["start_row_index"]

    # A sub-agent thread has no human turn: it is reported, and it must not
    # abort the post-mortems of the other trajectory in the same batch.
    subagent_rollout = tmp_path / "subagent.jsonl"
    subagent_rollout.write_text(
        "".join(
            json.dumps(row) + "\n"
            for row in [
                _two_turn_rollout_rows()[0],
                _response(
                    {
                        "type": "message",
                        "role": "developer",
                        "content": [{"type": "input_text", "text": "sub-agent task"}],
                    }
                ),
                *_call("s-1", f"sed -n '1,2p' {VERIFICATION}"),
            ]
        ),
        encoding="utf-8",
    )
    subagent = adapt_rollout(subagent_rollout, ROOT, load_policy_pack())
    assert isinstance(subagent, dict) and subagent["interaction_segments"] == []

    # The resolver's exact input is what the agent passed to gov explain, which
    # need not match the user's prompt.
    inputs = {
        "trajectory": [trajectory, subagent],
        "resolver": [
            {
                "source_trajectory_id": source_id,
                "interaction_segment_id": first["id"],
                "resolver_evidence": _projection(
                    "Godot presentation feature repair",
                    "godot_product_shell",
                    VERIFICATION,
                ),
            },
            {
                "source_trajectory_id": source_id,
                "interaction_segment_id": second["id"],
                "resolver_evidence": _projection(
                    "Python reference engine repair",
                    "python_reference_engine",
                    "docs/governance/ENGINEERING.md",
                ),
            },
        ],
        "evaluator": [
            {
                "source_trajectory_id": source_id,
                "interaction_segment_id": first["id"],
                "evaluation": {"activity": {"product": {"action_count": 4}}},
            },
            {
                "source_trajectory_id": source_id,
                "interaction_segment_id": second["id"],
                "evaluation": {"activity": {"product": {"action_count": 7}}},
            },
        ],
    }
    for name, payload in inputs.items():
        (tmp_path / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    output = tmp_path / "postmortem.json"
    assert (
        main(
            [
                "postmortem",
                "--trajectory",
                str(tmp_path / "trajectory.json"),
                "--resolver-evidence",
                str(tmp_path / "resolver.json"),
                "--evaluator",
                str(tmp_path / "evaluator.json"),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    records = {
        record["interaction"]["segment"]["id"]: record
        for record in json.loads(output.read_text())["postmortems"]
    }
    a, b = records[first["id"]], records[second["id"]]
    assert a["activity_total"]["action_count"] == 4
    assert b["activity_total"]["action_count"] == 7
    assert {effect["source"] for effect in a["manifest_effects"]} == {VERIFICATION}
    assert {effect["source"] for effect in b["manifest_effects"]} == {
        "docs/governance/ENGINEERING.md",
        VERIFICATION,
    }
    assert a["route_work_alignment"]["observed_surfaces"] == ["godot"]
    assert b["route_work_alignment"]["observed_surfaces"] == ["src"]
    result = json.loads(output.read_text())
    aggregate = result["aggregate"]
    assert aggregate["by_manifest"][VERIFICATION]["interaction_segment_count"] == 2
    assert aggregate["by_manifest"][VERIFICATION]["encounter_count"] == 2
    assert result["diagnostics"] == [
        {
            "source_trajectory_id": subagent["source"]["source_id"],
            "status": "interaction_boundary_unavailable",
            "reason": "no_structural_user_turn",
            "postmortem_emitted": False,
        }
    ]
    for text in ("Task A: Godot repair", "Task B: Python repair", "current_date"):
        assert text not in output.read_text()


def test_continuation_turns_are_two_segments_not_two_tasks(tmp_path: Path) -> None:
    """A follow-up turn is its own segment, never counted as its own task.

    Real sessions continue one piece of work across turns ("continue", "pull").
    Segmentation stays per human turn, but no record, summary, or aggregate may
    treat the two turns as two tasks, and an evaluator cannot assert a grouping.
    """
    continuation = "continue"
    rollout = tmp_path / "continuation.jsonl"
    rows = _two_turn_rollout_rows(TASK_PROMPT, continuation)
    rollout.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    trajectory = adapt_rollout(rollout, ROOT, load_policy_pack())
    assert isinstance(trajectory, dict)
    segments = trajectory["interaction_segments"]
    assert [(item["unit"], item["turn_text_sha256"]) for item in segments] == [
        ("human_turn", _sha256(TASK_PROMPT)),
        ("human_turn", _sha256(continuation)),
    ]
    trajectory_path = tmp_path / "trajectory.json"
    trajectory_path.write_text(json.dumps(trajectory), encoding="utf-8")
    output = tmp_path / "postmortem.json"
    arguments = ["postmortem", "--trajectory", str(trajectory_path)]
    assert main([*arguments, "--output", str(output)]) == 0
    text = output.read_text(encoding="utf-8")
    result = json.loads(text)

    records = result["postmortems"]
    assert [record["interaction"]["segment"]["id"] for record in records] == [
        segment["id"] for segment in segments
    ]
    for record in records:
        assert record["interaction"]["task_group_id"] == {
            "value": None,
            "evidence_state": "not_inferable",
        }
    assert all("Task group: not_inferable" in item for item in result["summaries"])
    aggregate = result["aggregate"]
    assert aggregate["interaction_segment_count"] == 2
    assert aggregate["task_group_count"] is None
    assert '"task_count"' not in text
    assert result["diagnostics"] == []

    # Grouping turns into tasks is judgement this version reserves: an evaluator
    # cannot assert a shared task (or separate ones) through the overlay either.
    evaluator = tmp_path / "evaluator.json"
    evaluator.write_text(
        json.dumps(
            [
                {
                    "source_trajectory_id": trajectory["source"]["source_id"],
                    "interaction_segment_id": segment["id"],
                    "evaluation": {"interaction": {"task_group_id": "stage-56g"}},
                }
                for segment in segments
            ]
        ),
        encoding="utf-8",
    )
    rejected = tmp_path / "rejected.json"
    assert (
        main([*arguments, "--evaluator", str(evaluator), "--output", str(rejected)])
        == 2
    )
    error = json.loads(rejected.read_text(encoding="utf-8"))["error"]
    assert "rebind interaction identity" in error and "task_group_id" in error
