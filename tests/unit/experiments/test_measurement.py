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
