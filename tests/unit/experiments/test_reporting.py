from __future__ import annotations

import json
from pathlib import Path

from tools.experiments.governance_manifest_quality.measurement import (
    normalize_trajectory,
)
from tools.experiments.governance_manifest_quality.reporting import (
    build_aggregate,
    write_outputs,
)


def _record(source_id: str, size: int) -> dict:
    return normalize_trajectory(
        {
            "schema_version": 1,
            "source": {"source_id": source_id, "source_format": "test"},
            "events": [
                {
                    "event_type": "retrieval",
                    "path": "AGENTS.md",
                    "source_class": "governance",
                    "access_mode": "bounded",
                    "materialized_bytes": size,
                    "byte_range": {"start": 0, "end": size},
                    "content_identity": f"content-{source_id}",
                }
            ],
        }
    )


def test_aggregate_reports_distributions_rejections_and_outliers() -> None:
    metrics = []
    from tools.experiments.governance_manifest_quality.measurement import (
        measure_trajectory,
    )

    for index, size in enumerate([10, 20, 30, 1000]):
        metrics.append(measure_trajectory(_record(str(index), size)))
    aggregate = build_aggregate(
        metrics,
        [
            {"status": "rejected_during_ingestion", "reason": "malformed"},
            {"status": "rejected_during_ingestion", "reason": "malformed"},
            {"status": "excluded", "reason": "other"},
        ],
    )
    assert aggregate["discovered"] == 7
    assert aggregate["successfully_measured"] == 4
    assert aggregate["rejected_during_ingestion"] == 2
    assert aggregate["excluded"] == 1
    assert aggregate["status_reasons"] == {
        "excluded": {"other": 1},
        "rejected_during_ingestion": {"malformed": 2},
    }
    assert aggregate["status_reconciled"] is True
    assert aggregate["governance_materialized_bytes"] == {
        "count": 4,
        "minimum": 10,
        "q1": 17.5,
        "median": 25.0,
        "q3": 272.5,
        "maximum": 1000,
    }
    assert (
        aggregate["governance_known_materialized_bytes"]
        == aggregate["governance_materialized_bytes"]
    )
    assert aggregate["incomplete_reason_counts"] == {}
    assert aggregate["conspicuous_outliers"] == [
        {
            "source_id": "3",
            "governance_known_materialized_bytes": 1000,
            "measurement_complete": True,
        }
    ]


def test_output_artifacts_are_deterministic_and_sanitized(tmp_path: Path) -> None:
    fingerprint = {"schema_version": 1, "repository_commit": "abc"}
    records = [
        _record("d", 1000),
        _record("b", 20),
        _record("a", 10),
        _record("c", 30),
    ]
    first = tmp_path / "first"
    second = tmp_path / "second"
    dispositions = [{"status": "rejected_during_ingestion", "reason": "malformed"}]
    write_outputs(first, fingerprint, records, dispositions)
    write_outputs(second, fingerprint, list(reversed(records)), dispositions)
    for name in (
        "baseline_fingerprint.json",
        "trajectories.jsonl",
        "aggregate.json",
        "aggregate.csv",
        "run_metadata.json",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()
    metadata = json.loads((first / "run_metadata.json").read_text(encoding="utf-8"))
    assert metadata["raw_sources_copied"] is False
    assert metadata["machine_paths_emitted"] is False
