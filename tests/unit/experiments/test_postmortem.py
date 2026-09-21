from __future__ import annotations

import json
from pathlib import Path

import pytest

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
    postmortem_from_trajectory,
    read_json_records,
    render_task_summary,
)

VERIFICATION = "docs/governance/VERIFICATION.md"


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
    task_identity: str | None = "task-1",
    model: str | None = "model-a",
    revision: str | None = "a" * 40,
    successful_test: bool = True,
    reads: tuple[tuple[str, str], ...] = ((VERIFICATION, "governance"),),
    tool_calls: int = 10,
) -> dict:
    """Reads come first, so the n-th read has event sequence n."""
    events = [_read(path, source_class) for path, source_class in reads]
    events.append(_execution(is_test=True, exit_code=0 if successful_test else 1))
    events.extend(_execution() for _ in range(tool_calls - 1))
    return {
        "schema_version": 1,
        "source": {
            "source_id": source_id,
            "task_identity": task_identity,
            "model": model,
            "repository_revision": revision,
            "elapsed_ms": 1000,
            "token_information": {"total_token_usage": {"total_tokens": 30}},
        },
        "events": events,
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
        "task": {
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


def test_record_serializes_parses_and_preserves_mechanical_task_binding() -> None:
    record = postmortem_from_trajectory(_trajectory(), evaluator=_evaluation("useful"))
    reparsed = normalize_postmortem_record(json.loads(json.dumps(record)))
    assert reparsed == record
    assert record["task"]["id"] == {"value": "task-1", "evidence_state": "derived"}
    assert record["task"]["manifest_revision"] == {
        "value": "a" * 40,
        "evidence_state": "derived",
    }


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
    assert record["task"]["id"]["value"] == "declared-task"
    assert record["task"]["session_id"]["value"] == "session-1"
    assert record["task"]["start_commit"]["value"] == "b" * 40
    assert record["task"]["end_commit"]["value"] == "c" * 40


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


def test_incomplete_historical_record_is_usable_without_fabricating_evidence() -> None:
    record = postmortem_from_trajectory(
        _trajectory(task_identity=None, model=None, revision=None)
    )
    assert record["task"]["id"]["evidence_state"] == "not_recorded"
    assert record["task"]["manifest_revision"]["evidence_state"] == "not_recorded"
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


def test_rereads_are_encounters_not_tasks() -> None:
    record = postmortem_from_trajectory(
        _trajectory(reads=((VERIFICATION, "governance"),) * 3),
        evaluator=_evaluation("useful"),
    )
    aggregate = build_postmortem_aggregate([record])
    (source,) = aggregate["by_manifest"].values()
    assert source["task_count"] == 1
    assert source["activity"]["action_count"]["product"] == 6
    assert source["task_classes"] == {"implementation": 1}
    assert source["encounter_count"] == 3
    for group in (
        aggregate["overall"],
        aggregate["by_model"]["model-a"],
        aggregate["by_task_class"]["implementation"],
    ):
        assert group["task_count"] == 1
        assert group["activity"]["action_count"]["product"] == 6


def test_aggregate_reports_manifest_model_task_class_and_burden_across_tasks() -> None:
    decisive = postmortem_from_trajectory(
        _trajectory(), evaluator=_evaluation("decisive")
    )
    confirmatory = postmortem_from_trajectory(
        _trajectory(source_id="trajectory-2", task_identity="task-2", model="model-b"),
        evaluator=_evaluation("confirmatory", model="model-b"),
    )
    aggregate = build_postmortem_aggregate([decisive, confirmatory])
    manifest = aggregate["by_manifest"][VERIFICATION]
    assert aggregate["task_count"] == 2
    assert manifest["task_count"] == 2
    assert manifest["contributions"]["decisive"] == 1
    assert manifest["contributions"]["confirmatory"] == 1
    assert aggregate["by_model"]["model-a"]["task_count"] == 1
    assert aggregate["by_task_class"]["implementation"]["task_count"] == 2
    assert aggregate["overall"]["governance_burden_ratio"]["action_count"] == 0.5


def test_aggregate_rejects_repeated_trajectories() -> None:
    record = postmortem_from_trajectory(_trajectory())
    with pytest.raises(PostmortemValidationError, match="repeats trajectories"):
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


def test_evaluator_cannot_rebind_trajectory_or_annotate_an_encounter_twice() -> None:
    rebind = _evaluation("useful")
    rebind["task"]["source_trajectory_id"] = "trajectory-2"
    with pytest.raises(PostmortemValidationError, match="rebind"):
        postmortem_from_trajectory(_trajectory(), evaluator=rebind)
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
    summary = render_task_summary(record)
    assert "responsive cockpit scaling" in summary
    assert f"{VERIFICATION}: 1 useful" in summary
    assert "partial exposure: 0 of 10 tool calls had no recovered command" in summary
    assert "  product: 6 actions" in summary
    unattributed = render_task_summary(postmortem_from_trajectory(_trajectory()))
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
        {"source_trajectory_id": "trajectory-1", "evaluation": _evaluation("useful")},
    )
    resolver_path = _write(
        tmp_path / "resolver.json",
        {
            "source_trajectory_id": "trajectory-1",
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
    assert payload["aggregate"]["task_count"] == 1
    assert (
        payload["postmortems"][0]["resolver_projection"]["evidence_state"] == "recorded"
    )
    assert (
        read_json_records(trajectory_path)[0]["source"]["source_id"] == "trajectory-1"
    )


@pytest.mark.parametrize(
    ("flag", "payload_key", "payload"),
    [
        ("--evaluator", "evaluation", {"task": {"description": "judged"}}),
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
            {"source_trajectory_id": "trajectory-1 ", payload_key: payload},
            {"source_trajectory_id": "missing", payload_key: payload},
        ],
    )
    code, result = _run_postmortem(tmp_path, flag, str(overlay))
    assert code == 2
    assert "unknown trajectories: ['missing', 'trajectory-1 ']" in result["error"]


def test_cli_accepts_only_wrapped_overlay_records_bound_once(tmp_path: Path) -> None:
    flat = _write(
        tmp_path / "flat.json",
        {"source_trajectory_id": "trajectory-1", **_evaluation("useful")},
    )
    code, result = _run_postmortem(tmp_path, "--evaluator", str(flat))
    assert code == 2
    assert "must contain exactly" in result["error"]
    wrapped = {
        "source_trajectory_id": "trajectory-1",
        "evaluation": _evaluation("useful"),
    }
    repeated = _write(tmp_path / "repeated.json", [wrapped, wrapped])
    code, result = _run_postmortem(tmp_path, "--evaluator", str(repeated))
    assert code == 2
    assert "repeat trajectories: ['trajectory-1']" in result["error"]
