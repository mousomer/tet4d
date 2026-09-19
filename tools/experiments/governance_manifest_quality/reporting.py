from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .measurement import measure_trajectory


def _percentile(sorted_values: list[int], fraction: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    position = fraction * (len(sorted_values) - 1)
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _distribution(values: Iterable[int]) -> dict[str, Any]:
    ordered = sorted(values)
    if not ordered:
        return {
            "count": 0,
            "minimum": None,
            "q1": None,
            "median": None,
            "q3": None,
            "maximum": None,
        }
    return {
        "count": len(ordered),
        "minimum": ordered[0],
        "q1": _percentile(ordered, 0.25),
        "median": _percentile(ordered, 0.5),
        "q3": _percentile(ordered, 0.75),
        "maximum": ordered[-1],
    }


def _incomplete_reason_category(reason: str) -> str:
    if " for events " in reason:
        return reason.split(" for events ", 1)[0]
    return reason


def build_aggregate(
    metrics: list[dict[str, Any]], dispositions: Iterable[dict[str, str]]
) -> dict[str, Any]:
    disposition_list = list(dispositions)
    status_counts = Counter(item["status"] for item in disposition_list)
    status_reasons = {
        status: dict(
            sorted(
                Counter(
                    item["reason"]
                    for item in disposition_list
                    if item["status"] == status
                ).items()
            )
        )
        for status in sorted(status_counts)
    }
    totals = [
        value
        for metric in metrics
        if (value := metric["governance_total_materialized_bytes"]) is not None
    ]
    known = [metric["governance_known_materialized_bytes"] for metric in metrics]
    unique = [
        value
        for metric in metrics
        if (value := metric["governance_unique_materialized_bytes"]) is not None
    ]
    repeated = [
        value
        for metric in metrics
        if (value := metric["governance_repeated_materialized_bytes"]) is not None
    ]
    non_governance = [
        value
        for metric in metrics
        if (value := metric["non_governance_materialized_bytes"]) is not None
    ]
    file_activity: dict[str, Counter[str]] = {}
    for metric in metrics:
        for entry in metric["governance_file_activity"]:
            counters = file_activity.setdefault(entry["path"], Counter())
            for key in (
                "read_events",
                "known_materialized_bytes",
                "bounded_reads",
                "whole_file_reads",
                "mutation_events",
            ):
                counters[key] += entry[key]
    total_distribution = _distribution(totals)
    known_distribution = _distribution(known)
    q1 = known_distribution["q1"]
    q3 = known_distribution["q3"]
    outliers: list[dict[str, Any]] = []
    if q1 is not None and q3 is not None:
        upper = q3 + 1.5 * (q3 - q1)
        outliers = [
            {
                "source_id": metric["source_id"],
                "governance_known_materialized_bytes": metric[
                    "governance_known_materialized_bytes"
                ],
                "measurement_complete": metric["measurement_complete"],
            }
            for metric in metrics
            if metric["governance_known_materialized_bytes"] > upper
        ]
        outliers.sort(
            key=lambda item: (
                -item["governance_known_materialized_bytes"],
                item["source_id"],
            )
        )
    incomplete_reason_counts = Counter(
        _incomplete_reason_category(reason)
        for metric in metrics
        if not metric["measurement_complete"]
        for reason in metric["unavailable_reasons"]
    )
    discovered = len(metrics) + len(disposition_list)
    return {
        "schema_version": 1,
        "discovered": discovered,
        "successfully_measured": len(metrics),
        "incomplete_measurements": sum(
            not metric["measurement_complete"] for metric in metrics
        ),
        "incomplete_reason_counts": dict(sorted(incomplete_reason_counts.items())),
        "rejected_during_ingestion": status_counts["rejected_during_ingestion"],
        "excluded": status_counts["excluded"],
        "excluded_after_normalization": status_counts["excluded_after_normalization"],
        "unsupported_format": status_counts["unsupported_format"],
        "missing_required_provenance": status_counts["missing_required_provenance"],
        "other_unprocessed": status_counts["other_unprocessed"],
        "status_reasons": status_reasons,
        "status_reconciled": discovered == len(metrics) + sum(status_counts.values()),
        "governance_materialized_bytes": total_distribution,
        "governance_known_materialized_bytes": known_distribution,
        "governance_unique_materialized_bytes": _distribution(unique),
        "governance_repeated_materialized_bytes": _distribution(repeated),
        "non_governance_materialized_bytes": _distribution(non_governance),
        "read_modes": {
            "bounded": sum(metric["governance_bounded_reads"] for metric in metrics),
            "whole_file": sum(
                metric["governance_whole_file_reads"] for metric in metrics
            ),
            "unknown": sum(
                metric["governance_unknown_mode_reads"] for metric in metrics
            ),
        },
        "governance_read_events": sum(
            metric["governance_read_events"] for metric in metrics
        ),
        "governance_mutation_events": sum(
            metric["governance_mutation_events"] for metric in metrics
        ),
        "governance_mutation_trajectories": sum(
            metric["governance_mutation_events"] > 0 for metric in metrics
        ),
        "governance_file_activity": [
            {"path": path, **dict(counts)}
            for path, counts in sorted(
                file_activity.items(),
                key=lambda item: (
                    -item[1]["known_materialized_bytes"],
                    -item[1]["read_events"],
                    item[0],
                ),
            )
        ],
        "non_governance_known_materialized_bytes": sum(
            metric["non_governance_known_materialized_bytes"] for metric in metrics
        ),
        "tool_calls": sum(metric["tool_calls"] for metric in metrics),
        "shell_commands": sum(metric["shell_commands"] for metric in metrics),
        "searches": sum(metric["searches"] for metric in metrics),
        "test_invocations": sum(metric["test_invocations"] for metric in metrics),
        "failed_commands": sum(metric["failed_commands"] for metric in metrics),
        "repeated_failed_commands": sum(
            metric["repeated_failed_commands"] for metric in metrics
        ),
        "conspicuous_outliers": outliers,
        "interpretation": "observational_baseline_only",
    }


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_outputs(
    output_dir: Path,
    fingerprint: dict[str, Any],
    trajectories: list[dict[str, Any]],
    dispositions: list[dict[str, str]],
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics = [measure_trajectory(record) for record in trajectories]
    aggregate = build_aggregate(metrics, dispositions)
    _write_json(output_dir / "baseline_fingerprint.json", fingerprint)
    with (output_dir / "trajectories.jsonl").open("w", encoding="utf-8") as stream:
        for record in sorted(
            trajectories, key=lambda item: item["source"]["source_id"]
        ):
            stream.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    _write_json(output_dir / "aggregate.json", aggregate)

    columns = sorted({key for metric in metrics for key in metric})
    with (output_dir / "aggregate.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for metric in sorted(metrics, key=lambda item: item["source_id"]):
            writer.writerow(
                {
                    key: json.dumps(value, sort_keys=True)
                    if isinstance(value, (list, dict))
                    else value
                    for key, value in metric.items()
                }
            )

    provenance = {
        "fingerprint_sha256": hashlib.sha256(
            json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest(),
        "source_ids": sorted(record["source"]["source_id"] for record in trajectories),
        "disposition_counts": dict(
            sorted(Counter(item["status"] for item in dispositions).items())
        ),
        "adapter": "codex_rollout_stage_c1_v1",
        "raw_sources_copied": False,
        "machine_paths_emitted": False,
    }
    provenance["run_id"] = hashlib.sha256(
        json.dumps(provenance, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    _write_json(output_dir / "run_metadata.json", provenance)
    return aggregate
