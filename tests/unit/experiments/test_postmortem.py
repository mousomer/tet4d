from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.experiments.governance_manifest_quality import (
    postmortem as postmortem_module,
)
from tools.experiments.governance_manifest_quality.cli import main
from tools.experiments.governance_manifest_quality.measurement import (
    normalize_trajectory,
)
from tools.experiments.governance_manifest_quality.postmortem import (
    ACTIVITY_CATEGORIES,
    CONTRIBUTION_CATEGORIES,
    PROXY_FIELDS,
    PostmortemValidationError,
    build_postmortem_aggregate,
    normalize_postmortem_record,
    plan_interaction_postmortems,
    postmortem_from_trajectory,
    read_json_records,
    render_interaction_summary,
)

VERIFICATION = "docs/governance/VERIFICATION.md"
SEGMENT_ID = "trajectory-1:user-1"


def _read(path: str, source_class: str = "governance") -> dict:
    # Shaped like the real C1 Codex adapter, which never records authority/route.
    return {
        "event_type": "retrieval",
        "path": path,
        "source_class": source_class,
        "access_mode": "bounded",
        "materialized_bytes": None,
        "byte_range": None,
        "content_identity": None,
        "route": None,
        "authority": None,
        "evidence": "shell_read_command",
    }


def _execution(*, is_test: bool = False, exit_code: int | None = 0) -> dict:
    return {
        "event_type": "execution",
        "tool": "exec_command",
        "command_kind": "test" if is_test else "shell",
        "is_search": False,
        "is_test": is_test,
        "exit_code": exit_code,
        "command_identity": "verification" if is_test else "shell",
    }


def _trajectory(
    *,
    source_id: str = "trajectory-1",
    model: str | None = "model-a",
    revision: str | None = "a" * 40,
    successful_test: bool = True,
    reads: tuple[tuple[str, str], ...] = ((VERIFICATION, "governance"),),
    tool_calls: int = 10,
) -> dict:
    """Reads come first, so the n-th read has event sequence n."""
    segment_id = f"{source_id}:user-1"
    events = [_read(path, source_class) for path, source_class in reads]
    events.append(_execution(is_test=True, exit_code=0 if successful_test else 1))
    events.extend(_execution() for _ in range(tool_calls - 1))
    events = [event | {"interaction_segment_id": segment_id} for event in events]
    return {
        "schema_version": 2,
        "source": {
            "source_id": source_id,
            "model": model,
            "repository_revision": revision,
            "elapsed_ms": 1000,
            "token_information": {"total_token_usage": {"total_tokens": 30}},
        },
        "events": events,
        "interaction_segments": [
            {
                "id": segment_id,
                "unit": "human_turn",
                "start_row_index": 1,
                "end_row_index": 100,
                "turn_text_sha256": "f" * 64,
                "boundary_evidence": "content_item_kinds",
            }
        ],
    }


def _effect(encountered_at: int, effect: str, source: str = VERIFICATION) -> dict:
    return {
        "source": source,
        "encountered_at": encountered_at,
        "decision": "ran the source-binding verification command",
        "effect": effect,
        "outcome_evidence": "the source-binding check passed",
        "confidence": "high",
    }


def _evaluation(effect: str, *, model: str = "model-a") -> dict:
    return {
        "interaction": {
            "description": "responsive cockpit scaling",
            "task_class": "implementation",
            "model": model,
        },
        # Reclassifies part of the 10 measured tool calls; unknown keeps the rest.
        "activity": {
            "product": {"action_count": 6, "elapsed_ms": 600, "token_count": 20},
            "meta_required": {"action_count": 2, "elapsed_ms": 200, "token_count": 5},
            "meta_induced": {"action_count": 1, "elapsed_ms": 100, "token_count": 3},
            "waste": {"action_count": 0},
        },
        "manifest_effects": [_effect(1, effect)],
    }


def _resolver_output(
    *, scenario: str | None = None, routes: dict | None = None
) -> dict:
    return {
        "schema_version": 1,
        "entries": {
            "matched_scenario": {
                "owner": "project",
                "source": "config/governance/project.json#/execution/representative_scenarios",
                "value": scenario,
            },
            "routes": {
                "owner": "project",
                "source": "config/governance/project.json#/routes",
                "value": routes
                if routes is not None
                else {
                    "python_reference_engine": {
                        "dispatch_paths": [],
                        "authority_refs": ["verification"],
                    }
                },
            },
            "authorities": {
                "owner": "project",
                "source": "config/governance/project.json#/authorities",
                "value": [
                    {
                        "authority_id": "verification",
                        "source": VERIFICATION,
                    }
                ],
            },
            "verification.full": {
                "owner": "legacy-policy-pack",
                "source": "config/project/policy_pack.json",
                "value": "CODEX_MODE=1 ./scripts/verify.sh",
            },
        },
    }


def _resolver_evidence(
    *, scenario: str | None = None, routes: dict | None = None
) -> dict:
    return {
        "task_text": "responsive cockpit scaling",
        "resolver_output": _resolver_output(scenario=scenario, routes=routes),
    }


def _edge_read(
    path: str,
    *,
    role: str,
    access_mode: str,
    bytes_read: int,
) -> dict:
    return {
        "file_class": "edge_state",
        "registered_on_governance_surface": True,
        "edge_state_role": role,
        "edge_limit_rationale": ["human_reviewability"],
        "access_mode": access_mode,
        "materialized_bytes": bytes_read,
        "byte_range": {"start": 0, "end": bytes_read},
        "content_identity": f"fixture:{path}",
    }


def test_record_serializes_parses_and_preserves_mechanical_segment_binding() -> None:
    record = postmortem_from_trajectory(_trajectory(), evaluator=_evaluation("useful"))
    reparsed = normalize_postmortem_record(json.loads(json.dumps(record)))
    assert reparsed == record
    interaction = record["interaction"]
    assert interaction["id"] == {"value": SEGMENT_ID, "evidence_state": "derived"}
    assert interaction["segment"]["unit"] == "human_turn"
    # A human turn is not asserted to be, or to share, an engineering task.
    assert interaction["task_group_id"] == {
        "value": None,
        "evidence_state": "not_inferable",
    }
    assert interaction["manifest_revision"] == {
        "value": "a" * 40,
        "evidence_state": "derived",
    }
    for field, value, message in (
        ("task_group_id", {"value": "g", "evidence_state": "recorded"}, "reserved"),
        ("id", {"value": "other:user-1", "evidence_state": "derived"}, "its segment"),
    ):
        claimed = json.loads(json.dumps(record))
        claimed["interaction"][field] = value
        with pytest.raises(PostmortemValidationError, match=message):
            normalize_postmortem_record(claimed)


def test_g1_segment_binds_boundaries_without_overriding_c1_totals() -> None:
    segment = {
        "segment": {
            "segment_id": "g1-1",
            "work_type": "Coding",
            "task_id": "declared-task",
            "session_id": "session-1",
        },
        "start_boundary": {"head": "b" * 40, "observed_at": "2026-09-20T10:00:00Z"},
        "end_boundary": {"head": "c" * 40, "observed_at": "2026-09-20T10:00:02Z"},
        "artifacts": [],
        # finish_segment reports 0 tool calls whenever the count was not supplied.
        "telemetry": {"tool_call_count": 0, "elapsed_seconds": 1.5},
    }
    record = postmortem_from_trajectory(_trajectory(), segment=segment)
    assert record["activity"]["unknown"]["action_count"] == 10
    assert record["activity_total"]["elapsed_ms"] == 1000
    # The structural segment is the identity; G1's declared id is provenance.
    assert record["interaction"]["id"]["value"] == "trajectory-1:user-1"
    assert record["interaction"]["g1_task_id"] == {
        "value": "declared-task",
        "evidence_state": "recorded",
    }
    assert record["interaction"]["session_id"]["value"] == "session-1"
    assert record["interaction"]["start_commit"]["value"] == "b" * 40
    assert record["interaction"]["end_commit"]["value"] == "c" * 40


def test_resolver_projection_preserves_exact_input_output_and_fallback_state() -> None:
    record = postmortem_from_trajectory(
        _trajectory(), resolver_evidence=_resolver_evidence()
    )
    projection = record["resolver_projection"]
    assert projection["evidence_state"] == "recorded"
    assert projection["task_text"] == "responsive cockpit scaling"
    assert projection["resolution"] == {
        "scenario_state": "no_matching_scenario",
        "route_state": "fallback_or_default_route",
    }
    assert projection["resolver_output"] == _resolver_output()
    assert projection["projected_sources"] == [
        {
            "source": VERIFICATION,
            "authority_ids": ["verification"],
            "route_ids": [],
        }
    ]


def test_absent_resolver_evidence_stays_unavailable_not_an_empty_projection() -> None:
    record = postmortem_from_trajectory(_trajectory())
    comparison = record["projected_read_comparison"]
    assert comparison["projected_not_observed_read"] is None
    assert comparison["projected_and_read"] is None
    assert comparison["read_not_projected"] is None
    assert comparison["evidence_state"] == "not_recorded"
    assert record["resolver_projection"]["evidence_state"] == "not_recorded"
    assert record["resolver_projection"]["projected_sources"] is None
    assert record["route_work_alignment"]["state"] == "resolver_unavailable"
    assert record["route_work_alignment"]["projected_routes"] is None
    comparison["projected_not_observed_read"] = []
    with pytest.raises(PostmortemValidationError, match="null exactly"):
        normalize_postmortem_record(record)

    no_route = postmortem_from_trajectory(
        _trajectory(), resolver_evidence=_resolver_evidence(routes={})
    )
    assert no_route["resolver_projection"]["resolution"] == {
        "scenario_state": "no_matching_scenario",
        "route_state": "no_projected_route",
    }


def test_recorded_resolver_projection_requires_exact_task_text() -> None:
    with pytest.raises(PostmortemValidationError, match="exact task_text"):
        postmortem_from_trajectory(
            _trajectory(),
            resolver_evidence={
                "task_text": None,
                "resolver_output": _resolver_output(),
            },
        )


def test_large_but_bounded_backlog_read_has_no_raw_size_quality_penalty() -> None:
    trajectory = _trajectory(reads=(("docs/BACKLOG.md", "governance"),))
    trajectory["events"][0].update(
        _edge_read(
            "docs/BACKLOG.md",
            role="conditional_open_work_authority",
            access_mode="bounded",
            bytes_read=42,
        )
    )
    evidence = _resolver_evidence()
    evidence["resolver_output"]["entries"]["authorities"]["value"].append(
        {"authority_id": "open-work", "source": "docs/BACKLOG.md"}
    )
    (assessment,) = postmortem_from_trajectory(trajectory, resolver_evidence=evidence)[
        "edge_state_assessment"
    ]
    assert assessment["operational_role"] == "conditional_open_work_authority"
    assert assessment["registered_on_governance_surface"] is True
    assert assessment["routed_for_segment"] == "routed"
    assert assessment["bounded_reads"] == 1
    assert assessment["repeated_reads"] == 0
    assert assessment["segment_local_materialized_bytes"] == 42
    assert assessment["raw_size_is_quality_penalty"] is False


def test_smaller_whole_file_current_state_read_reports_locality_not_size() -> None:
    trajectory = _trajectory(reads=(("CURRENT_STATE.md", "governance"),))
    trajectory["events"][0].update(
        _edge_read(
            "CURRENT_STATE.md",
            role="restart_handoff_context",
            access_mode="whole_file",
            bytes_read=120,
        )
    )
    (assessment,) = postmortem_from_trajectory(trajectory)["edge_state_assessment"]
    assert assessment["operational_role"] == "restart_handoff_context"
    assert assessment["routed_for_segment"] == "not_recorded"
    assert assessment["whole_file_reads"] == 1
    assert assessment["access_locality"] == "whole_file_observed"
    # Historical/completed material is not called stale merely because it exists.
    assert assessment["staleness"] == "not_recorded"
    assert assessment["raw_size_is_quality_penalty"] is False


def test_registration_routing_and_reading_stay_independent_signals() -> None:
    """Registered, routed, read, and whole-file read are four separate facts."""
    trajectory = _trajectory(reads=(("docs/BACKLOG.md", "governance"),))
    trajectory["events"][0].update(
        _edge_read(
            "docs/BACKLOG.md",
            role="conditional_open_work_authority",
            access_mode="bounded",
            bytes_read=40,
        )
    )
    # Registration does not imply routing: the file sits on the active surface
    # while this segment's resolver evidence projects something else entirely.
    (assessment,) = postmortem_from_trajectory(
        trajectory, resolver_evidence=_resolver_evidence()
    )["edge_state_assessment"]
    assert assessment["registered_on_governance_surface"] is True
    assert assessment["routed_for_segment"] == "not_routed"
    # Reading does not imply whole-file reading.
    assert (assessment["whole_file_reads"], assessment["access_locality"]) == (
        0,
        "bounded_only",
    )

    # Routing does not imply reading: a projected edge file that was never read
    # stays an unobserved projection and gets no access assessment at all.
    evidence = _resolver_evidence()
    evidence["resolver_output"]["entries"]["authorities"]["value"].append(
        {"authority_id": "restart-context", "source": "CURRENT_STATE.md"}
    )
    record = postmortem_from_trajectory(trajectory, resolver_evidence=evidence)
    assert [item["source"] for item in record["edge_state_assessment"]] == [
        "docs/BACKLOG.md"
    ]
    comparison = record["projected_read_comparison"]
    assert "CURRENT_STATE.md" in {
        entry["source"] for entry in comparison["projected_not_observed_read"]
    }


def test_edge_state_overlay_keeps_retention_history_and_contradiction_visible() -> None:
    trajectory = _trajectory(reads=(("docs/BACKLOG.md", "governance"),))
    trajectory["events"][0].update(
        _edge_read(
            "docs/BACKLOG.md",
            role="conditional_open_work_authority",
            access_mode="bounded",
            bytes_read=30,
        )
    )
    record = postmortem_from_trajectory(
        trajectory,
        evaluator={
            "edge_state_assessment": [
                {
                    "source": "docs/BACKLOG.md",
                    "information_retention": "information_loss_observed",
                    "contradictory_active_state": "problem_observed",
                    "staleness": "not_observed",
                }
            ]
        },
    )
    (assessment,) = record["edge_state_assessment"]
    assert assessment["information_retention"] == "information_loss_observed"
    assert assessment["contradictory_active_state"] == "problem_observed"
    assert assessment["staleness"] == "not_observed"
    assert assessment["raw_size_is_quality_penalty"] is False
    # Raw size can never become a penalty, by evaluator overlay or by hand.
    with pytest.raises(PostmortemValidationError, match="unknown fields"):
        postmortem_from_trajectory(
            trajectory,
            evaluator={
                "edge_state_assessment": [
                    {
                        "source": "docs/BACKLOG.md",
                        "raw_size_is_quality_penalty": True,
                    }
                ]
            },
        )
    assessment["raw_size_is_quality_penalty"] = True
    with pytest.raises(PostmortemValidationError, match="class semantics"):
        normalize_postmortem_record(record)


def test_projected_source_counts_as_read_whatever_its_c1_source_class() -> None:
    evidence = _resolver_evidence()
    evidence["resolver_output"]["entries"]["authorities"]["value"] += [
        {"authority_id": "architecture", "source": "docs/ARCHITECTURE_CONTRACT.md"},
        {"authority_id": "product-requirements", "source": "docs/rds/"},
    ]
    trajectory = _trajectory(
        reads=(
            # C1 classes this projected authority as non_governance.
            ("docs/ARCHITECTURE_CONTRACT.md", "non_governance"),
            ("AGENTS.md", "governance"),
            ("docs/design/godot_visual_system.md", "non_governance"),
        )
    )
    comparison = postmortem_from_trajectory(trajectory, resolver_evidence=evidence)[
        "projected_read_comparison"
    ]
    assert [entry["source"] for entry in comparison["projected_and_read"]] == [
        "docs/ARCHITECTURE_CONTRACT.md"
    ]
    assert [entry["source"] for entry in comparison["projected_not_observed_read"]] == [
        VERIFICATION,
        "docs/rds/",
    ]
    # Only governance-classified reads can be governance consumed off-projection.
    assert comparison["read_not_projected"] == [
        {"source": "AGENTS.md", "observed_read_sequences": [2]}
    ]
    assert comparison["causal_interpretation"] == "unknown"


def test_projected_not_observed_read_retains_observation_not_unused_interpretation() -> (
    None
):
    record = postmortem_from_trajectory(
        _trajectory(reads=()), resolver_evidence=_resolver_evidence()
    )
    comparison = record["projected_read_comparison"]
    assert comparison["projected_and_read"] == []
    assert comparison["projected_not_observed_read"] == [
        {
            "source": VERIFICATION,
            "authority_ids": ["verification"],
            "route_ids": [],
            "observed_read_sequences": [],
        }
    ]
    assert comparison["causal_interpretation"] == "unknown"


def test_route_work_alignment_is_advisory_in_both_directions() -> None:
    godot = {"godot_product_shell": {"dispatch_paths": ["godot/AGENTS.md"]}}
    python = {"python_reference_engine": {"dispatch_paths": []}}

    def alignment(routes: dict, *paths: str) -> dict:
        segment = {
            "artifacts": [{"path": path, "role": "unclassified"} for path in paths]
        }
        return postmortem_from_trajectory(
            _trajectory(),
            segment=segment,
            resolver_evidence=_resolver_evidence(routes=routes),
        )["route_work_alignment"]

    projected_but_untouched = alignment(godot, "src/tet4d/engine/api.py")
    assert projected_but_untouched["state"] == "mismatch_observed"
    assert projected_but_untouched["projected_dedicated_routes_unmodified"] == [
        "godot_product_shell"
    ]
    touched_but_unprojected = alignment(
        python,
        "godot/Tet4D.Godot/scripts/ui/live_cockpit.gd",
        "src/tet4d/engine/api.py",
    )
    assert touched_but_unprojected["state"] == "mismatch_observed"
    assert touched_but_unprojected["dedicated_routes_not_projected"] == [
        "godot_product_shell"
    ]
    assert touched_but_unprojected["observed_surfaces"] == ["godot", "src"]
    aligned = alignment(godot, "godot/Tet4D.Godot/scripts/ui/live_cockpit.gd")
    assert aligned["state"] == "no_mismatch_observed"
    assert {
        projected_but_untouched["causal_interpretation"],
        touched_but_unprojected["causal_interpretation"],
        aligned["causal_interpretation"],
    } == {"unknown"}


def test_artifact_coverage_stays_migration_limited_and_non_normative() -> None:
    segment = {
        "artifacts": [
            {
                "path": "godot/Tet4D.Godot/scripts/ui/live_cockpit.gd",
                "role": "unclassified",
            },
            {"path": "docs/BACKLOG.md", "role": "bookkeeping"},
        ]
    }
    record = postmortem_from_trajectory(_trajectory(), segment=segment)
    assert record["artifact_coverage"] == {
        "observed": 2,
        "classified": 1,
        "unclassified": 1,
        "interpretation": {"state": "migration_limited", "normative": False},
    }
    record["artifact_coverage"]["interpretation"]["normative"] = True
    with pytest.raises(PostmortemValidationError, match="non-normative"):
        normalize_postmortem_record(record)


@pytest.mark.parametrize(
    "artifact",
    [
        {"path": "godot/foo.gd"},
        {"path": "godot/foo.gd", "role": "made_up_role"},
    ],
)
def test_g1_artifacts_require_explicit_supported_roles(artifact: dict) -> None:
    with pytest.raises(PostmortemValidationError, match="explicit supported role"):
        postmortem_from_trajectory(_trajectory(), segment={"artifacts": [artifact]})


def test_incomplete_historical_record_is_usable_without_fabricating_evidence() -> None:
    record = postmortem_from_trajectory(_trajectory(model=None, revision=None))
    assert record["interaction"]["id"]["evidence_state"] == "derived"
    assert (
        record["interaction"]["manifest_revision"]["evidence_state"] == "not_recorded"
    )
    assert record["activity"]["unknown"]["action_count"] == 10
    assert record["manifest_effects"][0]["effect"] == "unknown"


def test_c1_normalized_output_is_consumed_not_silently_emptied() -> None:
    raw = _trajectory(reads=((VERIFICATION, "governance"),) * 2)
    # C1's corpus writes this normalized form; C1 cannot re-read it by itself.
    from_normalized = postmortem_from_trajectory(normalize_trajectory(raw))
    assert len(from_normalized["manifest_effects"]) == 2
    assert from_normalized["activity_total"]["action_count"] == 10
    assert from_normalized == postmortem_from_trajectory(raw)
    with pytest.raises(PostmortemValidationError, match="no recognizable event"):
        postmortem_from_trajectory({"schema_version": 1, "source": {"source_id": "t"}})


def test_trajectories_without_human_turns_yield_diagnostics_not_postmortems() -> None:
    legacy = _trajectory(source_id="legacy")
    legacy["schema_version"] = 1
    legacy.pop("interaction_segments")
    for event in legacy["events"]:
        event.pop("interaction_segment_id")
    subagent = _trajectory(source_id="subagent")
    subagent["interaction_segments"] = []
    for event in subagent["events"]:
        event["interaction_segment_id"] = None
    for trajectory, reason in (
        (legacy, "boundaries_not_recorded"),
        (subagent, "no_structural_user_turn"),
    ):
        assert plan_interaction_postmortems(trajectory) == (
            [],
            [
                {
                    "source_trajectory_id": trajectory["source"]["source_id"],
                    "status": "interaction_boundary_unavailable",
                    "reason": reason,
                    "postmortem_emitted": False,
                }
            ],
        )
        with pytest.raises(PostmortemValidationError, match=reason):
            postmortem_from_trajectory(trajectory)

    partial = _trajectory()
    partial["events"][-1]["interaction_segment_id"] = None
    segments, diagnostics = plan_interaction_postmortems(partial)
    assert [segment["id"] for segment in segments] == [SEGMENT_ID]
    assert diagnostics == [
        {
            "source_trajectory_id": "trajectory-1",
            "status": "evidence_outside_interaction_segments",
            "item_count": 1,
            "postmortem_emitted": True,
        }
    ]


def test_repeated_failure_without_command_identity_stays_unknown() -> None:
    trajectory = _trajectory()
    trajectory["events"] += [
        _execution(is_test=True, exit_code=1) | {"interaction_segment_id": SEGMENT_ID},
        _execution(is_test=True, exit_code=1) | {"interaction_segment_id": SEGMENT_ID},
        _execution(exit_code=1)
        | {"command_identity": None, "interaction_segment_id": SEGMENT_ID},
    ]
    normalized = normalize_trajectory(trajectory)
    scoped = postmortem_module._segment_scoped_trajectory(
        normalized, normalized["interaction_segments"][0]
    )
    assert [
        event["repeated_failure"]
        for event in scoped["execution_events"]
        if event["exit_code"] == 1
    ] == [False, True, None]


def test_contribution_categories_are_exact_and_invalid_causal_claim_is_rejected() -> (
    None
):
    assert CONTRIBUTION_CATEGORIES == (
        "decisive",
        "useful",
        "confirmatory",
        "neutral",
        "distracting",
        "harmful",
        "unknown",
    )
    record = postmortem_from_trajectory(_trajectory())
    record["manifest_effects"][0]["effect"] = "decisive"
    with pytest.raises(PostmortemValidationError, match="requires decision"):
        normalize_postmortem_record(record)


def test_activity_annotation_reclassifies_unknown_and_conserves_every_proxy() -> None:
    annotation = {
        "product": {"action_count": 6},
        "meta_required": {"action_count": 2},
        "waste": {"action_count": 1},
    }
    record = postmortem_from_trajectory(
        _trajectory(), evaluator={"activity": annotation}
    )
    assert record["activity"]["unknown"]["action_count"] == 1
    assert record["activity_total"] == {
        "action_count": 10,
        "elapsed_ms": 1000,
        "token_count": 30,
        "evidence_state": "derived",
    }
    for proxy in PROXY_FIELDS:
        assert (
            sum(
                record["activity"][category][proxy] or 0
                for category in ACTIVITY_CATEGORIES
            )
            == record["activity_total"][proxy]
        )
    initial = postmortem_from_trajectory(_trajectory())
    assert initial["activity"]["unknown"] == {
        "action_count": 10,
        "elapsed_ms": 1000,
        "token_count": 30,
        "evidence_state": "derived",
    }


def test_activity_attribution_cannot_exceed_or_invent_measured_totals() -> None:
    with pytest.raises(PostmortemValidationError, match="exceeds"):
        postmortem_from_trajectory(
            _trajectory(), evaluator={"activity": {"product": {"action_count": 11}}}
        )
    unmeasured = _trajectory()
    unmeasured["source"]["token_information"] = None
    with pytest.raises(PostmortemValidationError, match="without a measured total"):
        postmortem_from_trajectory(
            unmeasured, evaluator={"activity": {"product": {"token_count": 5}}}
        )
    with pytest.raises(PostmortemValidationError, match="remainder"):
        postmortem_from_trajectory(
            _trajectory(), evaluator={"activity": {"unknown": {"action_count": 0}}}
        )
    record = postmortem_from_trajectory(_trajectory())
    record["activity"]["product"] = {
        "action_count": 3,
        "elapsed_ms": None,
        "token_count": None,
        "evidence_state": "recorded",
    }
    with pytest.raises(PostmortemValidationError, match="partition"):
        normalize_postmortem_record(record)


def test_burden_ratio_is_null_until_meta_activity_is_attributed() -> None:
    product_only = postmortem_from_trajectory(
        _trajectory(), evaluator={"activity": {"product": {"action_count": 6}}}
    )
    ratio = build_postmortem_aggregate([product_only])["overall"]
    assert ratio["governance_burden_ratio"]["action_count"] is None
    attributed = postmortem_from_trajectory(
        _trajectory(), evaluator=_evaluation("useful")
    )
    burden = build_postmortem_aggregate([attributed])["overall"]
    assert burden["governance_burden_ratio"]["action_count"] == 0.5


def test_rereads_are_encounters_not_segments() -> None:
    record = postmortem_from_trajectory(
        _trajectory(reads=((VERIFICATION, "governance"),) * 3),
        evaluator=_evaluation("useful"),
    )
    aggregate = build_postmortem_aggregate([record])
    (source,) = aggregate["by_manifest"].values()
    assert source["interaction_segment_count"] == 1
    assert source["activity"]["action_count"]["product"] == 6
    assert source["task_classes"] == {"implementation": 1}
    assert source["encounter_count"] == 3
    for group in (
        aggregate["overall"],
        aggregate["by_model"]["model-a"],
        aggregate["by_task_class"]["implementation"],
    ):
        assert group["interaction_segment_count"] == 1
        assert group["activity"]["action_count"]["product"] == 6


def test_aggregate_reports_manifest_model_task_class_and_burden_across_segments() -> (
    None
):
    decisive = postmortem_from_trajectory(
        _trajectory(), evaluator=_evaluation("decisive")
    )
    confirmatory = postmortem_from_trajectory(
        _trajectory(source_id="trajectory-2", model="model-b"),
        evaluator=_evaluation("confirmatory", model="model-b"),
    )
    aggregate = build_postmortem_aggregate([decisive, confirmatory])
    manifest = aggregate["by_manifest"][VERIFICATION]
    assert aggregate["interaction_segment_count"] == 2
    assert aggregate["task_group_count"] is None
    assert manifest["interaction_segment_count"] == 2
    assert manifest["contributions"]["decisive"] == 1
    assert manifest["contributions"]["confirmatory"] == 1
    assert aggregate["by_model"]["model-a"]["interaction_segment_count"] == 1
    assert (
        aggregate["by_task_class"]["implementation"]["interaction_segment_count"] == 2
    )
    assert aggregate["overall"]["governance_burden_ratio"]["action_count"] == 0.5


def test_aggregate_rejects_repeated_segments() -> None:
    record = postmortem_from_trajectory(_trajectory())
    with pytest.raises(PostmortemValidationError, match="repeats interaction segments"):
        build_postmortem_aggregate([record, record])


def test_decision_yield_distinguishes_unevaluated_from_zero_and_positive() -> None:
    reads = ((VERIFICATION, "governance"),) * 2

    def overall(*effects: str) -> dict:
        evaluation = (
            {
                "manifest_effects": [
                    _effect(index, effect) for index, effect in enumerate(effects, 1)
                ]
            }
            if effects
            else None
        )
        record = postmortem_from_trajectory(
            _trajectory(reads=reads), evaluator=evaluation
        )
        return build_postmortem_aggregate([record])["overall"]

    unevaluated = overall()
    assert unevaluated["decision_yield"] is None
    assert unevaluated["confirmatory_fraction"] is None
    assert unevaluated["encounter_count"] == 2
    assert unevaluated["judged_encounter_count"] == 0
    assert overall("useful", "neutral")["decision_yield"] == 0.5
    evaluated_zero = overall("neutral", "confirmatory")
    assert evaluated_zero["decision_yield"] == 0.0
    assert evaluated_zero["confirmatory_fraction"] == 0.5
    assert evaluated_zero["judged_encounter_count"] == 2


def test_real_c1_reads_aggregate_by_source_without_inventing_sections() -> None:
    # Even a uniquely projected authority is not a finer identity than the path.
    record = postmortem_from_trajectory(
        _trajectory(), resolver_evidence=_resolver_evidence()
    )
    assert record["manifest_effects"][0]["rule_or_section"] is None
    assert list(build_postmortem_aggregate([record])["by_manifest"]) == [VERIFICATION]


def test_confirmatory_and_decisive_are_not_collapsed() -> None:
    decisive = postmortem_from_trajectory(
        _trajectory(), evaluator=_evaluation("decisive")
    )
    confirmatory = postmortem_from_trajectory(
        _trajectory(), evaluator=_evaluation("confirmatory")
    )
    assert decisive["manifest_effects"][0]["effect"] == "decisive"
    assert confirmatory["manifest_effects"][0]["effect"] == "confirmatory"


def test_descriptive_evidence_and_success_never_create_contribution() -> None:
    segment = {"artifacts": [{"path": "godot/project.godot", "role": "unclassified"}]}
    record = postmortem_from_trajectory(
        _trajectory(successful_test=True),
        evaluator={"outcome": {"status": "completed"}},
        segment=segment,
        resolver_evidence=_resolver_evidence(),
    )
    assert record["projected_read_comparison"]["projected_and_read"]
    assert record["route_work_alignment"]["state"] == "mismatch_observed"
    assert record["artifact_coverage"]["unclassified"] == 1
    assert record["outcome"]["status"]["value"] == "completed"
    assert record["outcome"]["verification_failures"] == []
    assert all(
        effect["effect"] == "unknown"
        and effect["decision"] is None
        and effect["outcome_evidence"] is None
        for effect in record["manifest_effects"]
    )
    assert (
        build_postmortem_aggregate([record])["overall"]["judged_encounter_count"] == 0
    )


def test_encounter_coverage_declares_partial_exposure() -> None:
    trajectory = _trajectory()
    trajectory["events"].append(
        {
            "event_type": "execution",
            "tool": "write_stdin",
            "command_kind": None,
            "is_search": None,
            "is_test": None,
            "exit_code": None,
            "command_identity": None,
            "interaction_segment_id": SEGMENT_ID,
        }
    )
    record = postmortem_from_trajectory(trajectory)
    assert record["encounter_coverage"] == {
        "channels": {
            "file_reads": "partial",
            "governance_cli_output": "not_observed",
            "injected_instructions": "not_observed",
        },
        "completeness": "partial",
        "execution_events": 11,
        "execution_events_without_recovered_command": 1,
    }
    aggregate = build_postmortem_aggregate([record])
    assert aggregate["encounter_coverage"] == record["encounter_coverage"]
    record["encounter_coverage"]["completeness"] = "complete"
    with pytest.raises(PostmortemValidationError, match="partial"):
        normalize_postmortem_record(record)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_trajectory_id", "trajectory-2"),
        ("id", "trajectory-2:user-9"),
        ("g1_task_id", "another-task"),
        ("task_group_id", "stage-56g"),
        (
            "segment",
            {
                "id": "trajectory-1:user-50",
                "unit": "human_turn",
                "start_row_index": 50,
                "end_row_index": 60,
                "turn_text_sha256": None,
                "boundary_evidence": "user_message_item",
            },
        ),
    ],
)
def test_evaluator_cannot_rebind_interaction_identity_or_provenance(
    field: str, value: object
) -> None:
    rebind = _evaluation("useful")
    rebind["interaction"][field] = value
    with pytest.raises(PostmortemValidationError, match="rebind"):
        postmortem_from_trajectory(_trajectory(), evaluator=rebind)


def test_evaluator_cannot_annotate_an_encounter_twice() -> None:
    twice = _evaluation("useful")
    twice["manifest_effects"].append(_effect(1, "decisive"))
    with pytest.raises(PostmortemValidationError, match="more than once"):
        postmortem_from_trajectory(_trajectory(), evaluator=twice)


def test_missing_guidance_and_compact_summary_remain_optional() -> None:
    evaluator = _evaluation("useful")
    evaluator["missing_guidance"] = [
        {
            "issue": "viewport stretch behavior was not covered",
            "evidence": "runtime probe disagreed with the initial implementation",
            "candidate_scope": "Godot runtime/UI implementation guidance",
        }
    ]
    record = postmortem_from_trajectory(_trajectory(), evaluator=evaluator)
    assert record["missing_guidance"][0]["candidate_scope"] == (
        "Godot runtime/UI implementation guidance"
    )
    summary = render_interaction_summary(record)
    assert "responsive cockpit scaling" in summary
    assert f"{VERIFICATION}: 1 useful" in summary
    assert "partial exposure: 0 of 10 tool calls had no recovered command" in summary
    assert "  product: 6 actions" in summary
    unattributed = render_interaction_summary(postmortem_from_trajectory(_trajectory()))
    assert "  product: not attributed" in unattributed
    assert "  unknown: 10 actions" in unattributed


def _write(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run_postmortem(tmp_path: Path, *overlay_args: str) -> tuple[int, dict]:
    trajectory = _write(tmp_path / "trajectory.json", _trajectory())
    output = tmp_path / "postmortem.json"
    code = main(
        ["postmortem", "--trajectory", str(trajectory), *overlay_args]
        + ["--output", str(output)]
    )
    return code, json.loads(output.read_text(encoding="utf-8"))


def test_cli_reads_historical_jsonl_and_writes_machine_readable_aggregate(
    tmp_path: Path,
) -> None:
    trajectory_path = tmp_path / "trajectories.jsonl"
    trajectory_path.write_text(json.dumps(_trajectory()) + "\n", encoding="utf-8")
    evaluator_path = _write(
        tmp_path / "evaluator.json",
        {
            "source_trajectory_id": "trajectory-1",
            "interaction_segment_id": SEGMENT_ID,
            "evaluation": _evaluation("useful"),
        },
    )
    resolver_path = _write(
        tmp_path / "resolver.json",
        {
            "source_trajectory_id": "trajectory-1",
            "interaction_segment_id": SEGMENT_ID,
            "resolver_evidence": _resolver_evidence(),
        },
    )
    output = tmp_path / "postmortem.json"
    assert (
        main(
            [
                "postmortem",
                "--trajectory",
                str(trajectory_path),
                "--evaluator",
                str(evaluator_path),
                "--resolver-evidence",
                str(resolver_path),
                "--output",
                str(output),
            ]
        )
        == 0
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["aggregate"]["interaction_segment_count"] == 1
    assert (
        payload["postmortems"][0]["resolver_projection"]["evidence_state"] == "recorded"
    )
    assert (
        read_json_records(trajectory_path)[0]["source"]["source_id"] == "trajectory-1"
    )


@pytest.mark.parametrize(
    ("flag", "payload_key", "payload"),
    [
        ("--evaluator", "evaluation", {"interaction": {"description": "judged"}}),
        ("--resolver-evidence", "resolver_evidence", _resolver_evidence()),
        ("--segment", "work_segment", {"artifacts": []}),
    ],
)
def test_cli_fails_on_unmatched_overlay_ids_instead_of_dropping_them(
    tmp_path: Path, flag: str, payload_key: str, payload: dict
) -> None:
    overlay = _write(
        tmp_path / "overlay.json",
        [
            {
                "source_trajectory_id": "trajectory-1 ",
                "interaction_segment_id": SEGMENT_ID,
                payload_key: payload,
            },
            {
                "source_trajectory_id": "missing",
                "interaction_segment_id": SEGMENT_ID,
                payload_key: payload,
            },
        ],
    )
    code, result = _run_postmortem(tmp_path, flag, str(overlay))
    assert code == 2
    assert "unknown interaction segments" in result["error"]


def test_cli_accepts_only_wrapped_overlay_records_bound_once(tmp_path: Path) -> None:
    flat = _write(
        tmp_path / "flat.json",
        {
            "source_trajectory_id": "trajectory-1",
            "interaction_segment_id": SEGMENT_ID,
            **_evaluation("useful"),
        },
    )
    code, result = _run_postmortem(tmp_path, "--evaluator", str(flat))
    assert code == 2
    assert "must contain exactly" in result["error"]
    wrapped = {
        "source_trajectory_id": "trajectory-1",
        "interaction_segment_id": SEGMENT_ID,
        "evaluation": _evaluation("useful"),
    }
    repeated = _write(tmp_path / "repeated.json", [wrapped, wrapped])
    code, result = _run_postmortem(tmp_path, "--evaluator", str(repeated))
    assert code == 2
    assert "repeat interaction segments" in result["error"]
