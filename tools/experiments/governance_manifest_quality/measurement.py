from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from copy import deepcopy
from pathlib import PurePosixPath
from typing import Any

from . import SCHEMA_VERSION

OUTCOME_FIELDS = (
    "required_tests_passed",
    "full_gate_passed",
    "regression_count",
    "scope_violations",
    "authority_violations",
    "unnecessary_files_changed",
    "technical_debt_introduced",
    "technical_debt_removed",
    "acceptance_criteria_completed",
    "review_findings",
)
ACCESS_MODES = {"bounded", "whole_file", "unknown"}
SOURCE_CLASSES = {"governance", "non_governance", "unknown"}
MUTATION_OPERATIONS = {"create", "edit", "delete", "unknown"}


class TrajectoryValidationError(ValueError):
    """The source cannot be represented without inventing evidence."""


def empty_outcome_evidence() -> dict[str, Any]:
    return {field: None for field in OUTCOME_FIELDS}


def _normalized_path(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TrajectoryValidationError("event path must be a non-empty string")
    path = value.replace("\\", "/")
    if path.startswith(("/", "../")) or path == "..":
        raise TrajectoryValidationError("event path must be repository-relative")
    if ".." in PurePosixPath(path).parts:
        raise TrajectoryValidationError("event path must not traverse parents")
    return PurePosixPath(path).as_posix()


def _optional_non_negative_int(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise TrajectoryValidationError(
            f"{field} must be a non-negative integer or null"
        )
    return value


def _normalize_byte_range(value: object) -> dict[str, int] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"start", "end"}:
        raise TrajectoryValidationError(
            "byte_range must contain exactly start and end, or be null"
        )
    start = _optional_non_negative_int(value["start"], "byte_range.start")
    end = _optional_non_negative_int(value["end"], "byte_range.end")
    if start is None or end is None or end < start:
        raise TrajectoryValidationError("byte_range must be a valid half-open range")
    return {"start": start, "end": end}


def _normalize_retrieval(event: dict[str, Any], sequence: int) -> dict[str, Any]:
    source_class = event.get("source_class", "unknown")
    access_mode = event.get("access_mode", "unknown")
    if source_class not in SOURCE_CLASSES:
        raise TrajectoryValidationError(
            f"invalid retrieval source_class: {source_class}"
        )
    if access_mode not in ACCESS_MODES:
        raise TrajectoryValidationError(f"invalid retrieval access_mode: {access_mode}")
    byte_range = _normalize_byte_range(event.get("byte_range"))
    materialized = _optional_non_negative_int(
        event.get("materialized_bytes"), "materialized_bytes"
    )
    content_identity = event.get("content_identity")
    if content_identity is not None and (
        not isinstance(content_identity, str) or not content_identity
    ):
        raise TrajectoryValidationError("content_identity must be a string or null")
    if (
        byte_range is not None
        and materialized is not None
        and byte_range["end"] - byte_range["start"] != materialized
    ):
        raise TrajectoryValidationError(
            "materialized_bytes must equal the evidenced byte-range length"
        )
    return {
        "sequence": sequence,
        "path": _normalized_path(event.get("path")),
        "source_class": source_class,
        "governance_kind": event.get("governance_kind"),
        "access_mode": access_mode,
        "materialized_bytes": materialized,
        "byte_range": byte_range,
        "content_identity": content_identity,
        "route": event.get("route"),
        "authority": event.get("authority"),
        "evidence": event.get("evidence"),
    }


def _normalize_mutation(event: dict[str, Any], sequence: int) -> dict[str, Any]:
    source_class = event.get("source_class", "unknown")
    operation = event.get("operation", "unknown")
    if source_class not in SOURCE_CLASSES:
        raise TrajectoryValidationError(
            f"invalid mutation source_class: {source_class}"
        )
    if operation not in MUTATION_OPERATIONS:
        raise TrajectoryValidationError(f"invalid mutation operation: {operation}")
    generated = event.get("generated_file")
    intentional = event.get("intentional")
    if generated not in {True, False, None}:
        raise TrajectoryValidationError("generated_file must be boolean or null")
    if intentional not in {True, False, None}:
        raise TrajectoryValidationError("intentional must be boolean or null")
    return {
        "sequence": sequence,
        "path": _normalized_path(event.get("path")),
        "source_class": source_class,
        "governance_kind": event.get("governance_kind"),
        "operation": operation,
        "bytes_changed": _optional_non_negative_int(
            event.get("bytes_changed"), "bytes_changed"
        ),
        "lines_added": _optional_non_negative_int(
            event.get("lines_added"), "lines_added"
        ),
        "lines_deleted": _optional_non_negative_int(
            event.get("lines_deleted"), "lines_deleted"
        ),
        "generated_file": generated,
        "intentional": intentional,
        "evidence": event.get("evidence"),
    }


def _normalize_execution(event: dict[str, Any], sequence: int) -> dict[str, Any]:
    exit_code = event.get("exit_code")
    if exit_code is not None and (
        isinstance(exit_code, bool) or not isinstance(exit_code, int)
    ):
        raise TrajectoryValidationError("exit_code must be an integer or null")
    duration_ms = _optional_non_negative_int(event.get("duration_ms"), "duration_ms")
    repeated_failure = event.get("repeated_failure")
    if repeated_failure not in {True, False, None}:
        raise TrajectoryValidationError("repeated_failure must be boolean or null")
    return {
        "sequence": sequence,
        "tool": event.get("tool"),
        "command_kind": event.get("command_kind"),
        "is_search": event.get("is_search"),
        "is_test": event.get("is_test"),
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "repeated_failure": repeated_failure,
        "command_identity": event.get("command_identity"),
    }


def _event_groups(payload: dict[str, Any]) -> tuple[list[Any], list[Any], list[Any]]:
    if "events" in payload:
        events = payload["events"]
        if not isinstance(events, list):
            raise TrajectoryValidationError("events must be an array")
        retrieval: list[Any] = []
        mutation: list[Any] = []
        execution: list[Any] = []
        targets = {
            "retrieval": retrieval,
            "mutation": mutation,
            "execution": execution,
        }
        for input_sequence, event in enumerate(events, 1):
            if not isinstance(event, dict):
                raise TrajectoryValidationError("each event must be an object")
            target = targets.get(event.get("event_type"))
            if target is None:
                raise TrajectoryValidationError(
                    f"unsupported event_type: {event.get('event_type')!r}"
                )
            copied = dict(event)
            copied["_input_sequence"] = input_sequence
            target.append(copied)
        return retrieval, mutation, execution

    groups = (
        payload.get("retrieval_activity", []),
        payload.get("mutation_activity", []),
        payload.get("tool_activity", []),
    )
    if any(not isinstance(group, list) for group in groups):
        raise TrajectoryValidationError("activity groups must be arrays")
    return groups


def normalize_trajectory(  # noqa: C901 - validates all normalized evidence groups
    payload: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TrajectoryValidationError("trajectory must be an object")
    version = payload.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        raise TrajectoryValidationError(f"unsupported schema_version: {version!r}")
    source = payload.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("source_id"), str):
        raise TrajectoryValidationError("source.source_id is required")

    retrieval, mutation, execution = _event_groups(payload)
    sequence = 0

    def numbered(events: Iterable[Any], normalizer: Any) -> list[dict[str, Any]]:
        nonlocal sequence
        normalized = []
        for event in events:
            if not isinstance(event, dict):
                raise TrajectoryValidationError("each activity event must be an object")
            sequence += 1
            event_sequence = event.get(
                "_input_sequence", event.get("sequence", sequence)
            )
            if (
                isinstance(event_sequence, bool)
                or not isinstance(event_sequence, int)
                or event_sequence < 1
            ):
                raise TrajectoryValidationError(
                    "event sequence must be a positive integer"
                )
            normalized.append(normalizer(event, event_sequence))
        return normalized

    outcome = empty_outcome_evidence()
    supplied_outcome = payload.get("outcome_evidence")
    if supplied_outcome is not None:
        if not isinstance(supplied_outcome, dict):
            raise TrajectoryValidationError(
                "outcome_evidence must be an object or null"
            )
        unknown = set(supplied_outcome) - set(OUTCOME_FIELDS)
        if unknown:
            raise TrajectoryValidationError(
                "unknown outcome fields: " + ", ".join(sorted(unknown))
            )
        outcome.update(deepcopy(supplied_outcome))

    limitations = payload.get("evidence_limitations", [])
    if not isinstance(limitations, list) or any(
        not isinstance(item, dict)
        or not isinstance(item.get("kind"), str)
        or set(item) - {"kind", "event_sequence"}
        for item in limitations
    ):
        raise TrajectoryValidationError(
            "evidence_limitations must contain kind/event_sequence objects"
        )
    normalized_limitations = []
    for item in limitations:
        event_sequence = item.get("event_sequence")
        if event_sequence is not None and (
            isinstance(event_sequence, bool)
            or not isinstance(event_sequence, int)
            or event_sequence < 1
        ):
            raise TrajectoryValidationError(
                "limitation event_sequence must be a positive integer or null"
            )
        normalized_limitations.append(
            {"kind": item["kind"], "event_sequence": event_sequence}
        )

    normalized_source = {
        "source_id": source["source_id"],
        "source_format": source.get("source_format"),
        "repository_revision": source.get("repository_revision"),
        "task_identity": source.get("task_identity"),
        "model": source.get("model"),
        "token_information": deepcopy(source.get("token_information")),
        "started_at": source.get("started_at"),
        "elapsed_ms": source.get("elapsed_ms"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "source": normalized_source,
        "retrieval_events": numbered(retrieval, _normalize_retrieval),
        "mutation_events": numbered(mutation, _normalize_mutation),
        "execution_events": numbered(execution, _normalize_execution),
        "outcome_evidence": outcome,
        "evidence_limitations": normalized_limitations,
    }


def _union_length(intervals: Iterable[tuple[int, int]]) -> int:
    merged_end = -1
    total = 0
    for start, end in sorted(intervals):
        if start > merged_end:
            total += end - start
            merged_end = end
        elif end > merged_end:
            total += end - merged_end
            merged_end = end
    return total


def _materialization(events: list[dict[str, Any]], label: str) -> dict[str, Any]:
    known_total = sum(
        event["materialized_bytes"] or 0
        for event in events
        if event["materialized_bytes"] is not None
    )
    total_missing = [
        event["sequence"] for event in events if event["materialized_bytes"] is None
    ]
    total = None if total_missing else known_total

    unique_missing = []
    intervals: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    for event in events:
        byte_range = event["byte_range"]
        identity = event["content_identity"]
        if (
            event["materialized_bytes"] is None
            or byte_range is None
            or identity is None
        ):
            unique_missing.append(event["sequence"])
            continue
        intervals[(event["path"], identity)].append(
            (byte_range["start"], byte_range["end"])
        )
    unique = (
        None
        if unique_missing
        else sum(_union_length(values) for values in intervals.values())
    )
    repeated = None if total is None or unique is None else total - unique
    reasons = []
    if total_missing:
        reasons.append(
            f"{label} materialized bytes unavailable for events {total_missing}"
        )
    if unique_missing:
        reasons.append(
            f"{label} unique ranges/content identity unavailable for events "
            f"{unique_missing}"
        )
    return {
        "known": known_total,
        "total": total,
        "unique": unique,
        "repeated": repeated,
        "reasons": reasons,
    }


def measure_trajectory(record: dict[str, Any]) -> dict[str, Any]:
    if "retrieval_events" not in record:
        record = normalize_trajectory(record)
    governance = [
        event
        for event in record["retrieval_events"]
        if event["source_class"] == "governance"
    ]
    non_governance = [
        event
        for event in record["retrieval_events"]
        if event["source_class"] == "non_governance"
    ]
    governance_materialization = _materialization(governance, "governance")
    non_governance_materialization = _materialization(non_governance, "non-governance")
    total_all = governance_materialization["total"]
    non_total = non_governance_materialization["total"]
    denominator = (
        None if total_all is None or non_total is None else total_all + non_total
    )
    governance_share = total_all / denominator if denominator not in {None, 0} else None
    repeated_ratio = (
        governance_materialization["repeated"] / total_all
        if total_all not in {None, 0}
        and governance_materialization["repeated"] is not None
        else None
    )
    governance_mutations = [
        event
        for event in record["mutation_events"]
        if event["source_class"] == "governance"
    ]
    governance_paths = sorted(
        {event["path"] for event in governance}
        | {event["path"] for event in governance_mutations}
    )
    governance_file_activity = [
        {
            "path": path,
            "read_events": sum(event["path"] == path for event in governance),
            "known_materialized_bytes": sum(
                event["materialized_bytes"] or 0
                for event in governance
                if event["path"] == path and event["materialized_bytes"] is not None
            ),
            "bounded_reads": sum(
                event["path"] == path and event["access_mode"] == "bounded"
                for event in governance
            ),
            "whole_file_reads": sum(
                event["path"] == path and event["access_mode"] == "whole_file"
                for event in governance
            ),
            "mutation_events": sum(
                event["path"] == path for event in governance_mutations
            ),
        }
        for path in governance_paths
    ]
    reasons = (
        governance_materialization["reasons"]
        + non_governance_materialization["reasons"]
    )
    limitations = record.get("evidence_limitations", [])
    if limitations:
        limitation_kinds = sorted({item["kind"] for item in limitations})
        reasons.append(
            "unresolved materialization evidence: " + ", ".join(limitation_kinds)
        )
        governance_materialization["total"] = None
        governance_materialization["unique"] = None
        governance_materialization["repeated"] = None
        non_governance_materialization["total"] = None
        total_all = None
        non_total = None
        governance_share = None
        repeated_ratio = None
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": record["source"]["source_id"],
        "governance_read_events": len(governance),
        "governance_unique_files_read": len({event["path"] for event in governance}),
        "governance_total_materialized_bytes": governance_materialization["total"],
        "governance_known_materialized_bytes": governance_materialization["known"],
        "governance_unique_materialized_bytes": governance_materialization["unique"],
        "governance_repeated_materialized_bytes": governance_materialization[
            "repeated"
        ],
        "governance_whole_file_reads": sum(
            event["access_mode"] == "whole_file" for event in governance
        ),
        "governance_bounded_reads": sum(
            event["access_mode"] == "bounded" for event in governance
        ),
        "governance_unknown_mode_reads": sum(
            event["access_mode"] == "unknown" for event in governance
        ),
        "governance_mutation_events": len(governance_mutations),
        "governance_file_activity": governance_file_activity,
        "non_governance_materialized_bytes": non_governance_materialization["total"],
        "non_governance_known_materialized_bytes": non_governance_materialization[
            "known"
        ],
        "retrieval_events": len(record["retrieval_events"]),
        "mutation_events": len(record["mutation_events"]),
        "tool_calls": len(record["execution_events"]),
        "shell_commands": sum(
            event["command_kind"] in {"shell", "search", "test"}
            for event in record["execution_events"]
        ),
        "searches": sum(
            event["is_search"] is True for event in record["execution_events"]
        ),
        "test_invocations": sum(
            event["is_test"] is True for event in record["execution_events"]
        ),
        "failed_commands": sum(
            event["exit_code"] not in {None, 0} for event in record["execution_events"]
        ),
        "repeated_failed_commands": sum(
            event["repeated_failure"] is True for event in record["execution_events"]
        ),
        "governance_materialization_share": governance_share,
        "governance_repeated_materialization_ratio": repeated_ratio,
        "measurement_complete": not reasons,
        "unavailable_reasons": reasons,
    }


def assert_expected_metrics(metrics: dict[str, Any], expected: dict[str, Any]) -> None:
    mismatches = {
        key: {"expected": value, "actual": metrics.get(key)}
        for key, value in expected.items()
        if metrics.get(key) != value
    }
    if mismatches:
        raise AssertionError(f"metric contract mismatch: {mismatches}")
