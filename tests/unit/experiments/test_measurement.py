from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tools.experiments.governance_manifest_quality.measurement import (
    TrajectoryValidationError,
    assert_expected_metrics,
    measure_trajectory,
    normalize_trajectory,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "tools/experiments/governance_manifest_quality/fixtures/semantic_cases.json"
)


def _cases() -> dict[str, dict]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return {case["id"]: case for case in payload["cases"]}


@pytest.mark.parametrize(
    "case_id",
    [
        "bounded_governance_read",
        "whole_file_governance_read",
        "repeated_identical_read",
        "overlapping_range_reads",
        "governance_edit_after_read",
        "governance_edit_without_read",
        "non_governance_source_read",
        "missing_byte_and_range_metadata",
        "equivalent_grouped_format",
    ],
)
def test_synthetic_semantic_cases(case_id: str) -> None:
    case = _cases()[case_id]
    normalized = normalize_trajectory(case["trajectory"])
    metrics = measure_trajectory(normalized)
    assert_expected_metrics(metrics, case["expected"])


def test_malformed_fixture_is_rejected_without_partial_measurement() -> None:
    case = _cases()["malformed_incomplete_trajectory"]
    with pytest.raises(TrajectoryValidationError, match=case["expected_error"]):
        normalize_trajectory(case["trajectory"])


def test_supported_source_variations_have_identical_semantics() -> None:
    cases = _cases()
    event_stream = measure_trajectory(
        normalize_trajectory(cases["bounded_governance_read"]["trajectory"])
    )
    grouped = measure_trajectory(
        normalize_trajectory(cases["equivalent_grouped_format"]["trajectory"])
    )
    assert event_stream == grouped


def test_event_stream_preserves_read_before_edit_sequence() -> None:
    record = normalize_trajectory(_cases()["governance_edit_after_read"]["trajectory"])
    assert record["retrieval_events"][0]["sequence"] == 1
    assert record["mutation_events"][0]["sequence"] == 2


def test_normalization_and_measurement_are_deterministic() -> None:
    trajectory = _cases()["overlapping_range_reads"]["trajectory"]
    first = measure_trajectory(normalize_trajectory(deepcopy(trajectory)))
    second = measure_trajectory(normalize_trajectory(deepcopy(trajectory)))
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_negative_control_rejects_collapsed_repeated_bytes() -> None:
    case = _cases()["repeated_identical_read"]
    actual = measure_trajectory(normalize_trajectory(case["trajectory"]))
    broken = dict(actual)
    broken["governance_unique_materialized_bytes"] = broken[
        "governance_total_materialized_bytes"
    ]
    broken["governance_repeated_materialized_bytes"] = 0
    with pytest.raises(AssertionError, match="metric contract mismatch"):
        assert_expected_metrics(broken, case["expected"])


def test_negative_control_rejects_naive_overlap_sum() -> None:
    case = _cases()["overlapping_range_reads"]
    actual = measure_trajectory(normalize_trajectory(case["trajectory"]))
    broken = dict(actual)
    broken["governance_unique_materialized_bytes"] = 200
    broken["governance_repeated_materialized_bytes"] = 0
    with pytest.raises(AssertionError, match="metric contract mismatch"):
        assert_expected_metrics(broken, case["expected"])


def test_negative_control_rejects_mutation_counted_as_retrieval() -> None:
    case = _cases()["governance_edit_without_read"]
    actual = measure_trajectory(normalize_trajectory(case["trajectory"]))
    broken = dict(actual)
    broken["governance_read_events"] = 1
    broken["governance_total_materialized_bytes"] = 10
    with pytest.raises(AssertionError, match="metric contract mismatch"):
        assert_expected_metrics(broken, case["expected"])


def test_negative_control_rejects_missing_evidence_fabricated_as_zero() -> None:
    case = _cases()["missing_byte_and_range_metadata"]
    actual = measure_trajectory(normalize_trajectory(case["trajectory"]))
    broken = dict(actual)
    broken["governance_total_materialized_bytes"] = 0
    broken["governance_unique_materialized_bytes"] = 0
    broken["governance_repeated_materialized_bytes"] = 0
    broken["measurement_complete"] = True
    with pytest.raises(AssertionError, match="metric contract mismatch"):
        assert_expected_metrics(broken, case["expected"])


def test_file_class_metrics_keep_stable_size_measurement_and_edge_access_separate() -> (
    None
):
    trajectory = {
        "source": {"source_id": "classes"},
        "events": [
            {
                "event_type": "retrieval",
                "path": "config/project/policy_pack.json",
                "source_class": "governance",
                "file_class": "stable_authoritative",
                "access_mode": "whole_file",
                "materialized_bytes": 800,
                "byte_range": {"start": 0, "end": 800},
                "content_identity": "policy-v1",
            },
            {
                "event_type": "retrieval",
                "path": "docs/BACKLOG.md",
                "source_class": "governance",
                "file_class": "edge_state",
                "access_mode": "bounded",
                "materialized_bytes": 40,
                "byte_range": {"start": 0, "end": 40},
                "content_identity": "backlog-v1",
            },
        ],
    }
    metrics = measure_trajectory(normalize_trajectory(trajectory))
    # Stable manifests retain ordinary materialization telemetry.
    assert metrics["governance_total_materialized_bytes"] == 840
    assert metrics["governance_whole_file_reads"] == 1
    # Edge-state access is reported separately and rejects a raw-size penalty.
    assert metrics["edge_state_file_activity"] == [
        {
            "path": "docs/BACKLOG.md",
            "read_events": 1,
            "repeated_reads": 0,
            "known_materialized_bytes": 40,
            "bounded_reads": 1,
            "whole_file_reads": 0,
            "unknown_mode_reads": 0,
            "raw_size_is_quality_penalty": False,
        }
    ]


def test_trajectory_versions_keep_human_turn_capture_explicit() -> None:
    legacy = {"schema_version": 1, "source": {"source_id": "legacy"}, "events": []}
    upgraded = normalize_trajectory(legacy)
    # Version 1 never captured human turns: null, not an empty list.
    assert (upgraded["schema_version"], upgraded["interaction_segments"]) == (2, None)
    with pytest.raises(TrajectoryValidationError, match="schema_version 2"):
        normalize_trajectory(legacy | {"interaction_segments": []})
    with pytest.raises(
        TrajectoryValidationError, match="requires interaction_segments"
    ):
        normalize_trajectory(
            {"schema_version": 2, "source": {"source_id": "v2"}, "events": []}
        )
    with pytest.raises(TrajectoryValidationError, match="known interaction segment"):
        normalize_trajectory(
            {
                "schema_version": 2,
                "source": {"source_id": "v2"},
                "interaction_segments": [],
                "events": [
                    {
                        "event_type": "execution",
                        "tool": "exec_command",
                        "interaction_segment_id": "v2:user-9",
                    }
                ],
            }
        )
    # The unit is explicit: a segment is a human turn, never declared a task.
    task_unit = {
        "id": "v2:user-1",
        "unit": "engineering_task",
        "start_row_index": 1,
        "end_row_index": 2,
        "turn_text_sha256": None,
        "boundary_evidence": "content_item_kinds",
    }
    with pytest.raises(TrajectoryValidationError, match="invalid unit"):
        normalize_trajectory(
            {
                "schema_version": 2,
                "source": {"source_id": "v2"},
                "interaction_segments": [task_unit],
                "events": [],
            }
        )
