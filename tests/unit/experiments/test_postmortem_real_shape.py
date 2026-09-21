"""End-to-end post-mortem regression over evidence shaped by its real producers.

The trajectory comes from the real C1 Codex adapter, so reads carry C1's real
source classes and null ``authority``/``route``.  The resolver output is a
captured ``gov --json explain`` probe, and G1 artifacts carry roles resolved by
the real G1 role index.  Only the evaluator overlay is judgement.
"""

from __future__ import annotations

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


def _response(payload: dict) -> dict:
    return {"type": "response_item", "payload": payload}


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
        {
            "type": "turn_context",
            "payload": {"cwd": str(ROOT), "model": "gpt-5.6-terra"},
        },
        _response(
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Stage 56G cockpit scaling"}
                ],
            }
        ),
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
                "role_source": "config/governance/project.json#/authorities/12 "
                "(open-work-backlog)",
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
        # finish_segment reports 0 tool calls whenever the count was not supplied.
        "telemetry": {
            "segment_count": 1,
            "files_written": 3,
            "elapsed_seconds": 600.0,
            "tool_call_count": 0,
            "failures": 0,
            "retries": 0,
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
    evaluation = {
        "task": {
            "description": "Stage 56G cockpit scaling",
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
        "evaluator": {"source_trajectory_id": trajectory_id, "evaluation": evaluation},
        "resolver": {
            "source_trajectory_id": trajectory_id,
            "resolver_evidence": probe["resolver_evidence"],
        },
        "segment": {
            "source_trajectory_id": trajectory_id,
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

    # Rereads: one task, three encounters, task-level activity counted once.
    verification = aggregate["by_manifest"][VERIFICATION]
    assert (verification["task_count"], verification["encounter_count"]) == (1, 3)
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
    assert record["task"]["id"] == {"value": "stage-56g", "evidence_state": "recorded"}
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
