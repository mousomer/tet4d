"""Thin, evidence-preserving post-mortems for production governance work.

This module deliberately separates mechanically recovered exposure from evaluator
judgement.  A read produces an encounter with an ``unknown`` contribution; only
an evaluator can link that encounter to a decision and observable outcome.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.workspace_governance.resolver.roles import ARTIFACT_ROLES

from .measurement import (
    TrajectoryValidationError,
    normalize_interaction_segments,
    normalize_trajectory,
)

POSTMORTEM_SCHEMA_VERSION = 3
ACTIVITY_CATEGORIES = (
    "product",
    "meta_required",
    "meta_induced",
    "waste",
    "unknown",
)
CONTRIBUTION_CATEGORIES = (
    "decisive",
    "useful",
    "confirmatory",
    "neutral",
    "distracting",
    "harmful",
    "unknown",
)
CONFIDENCE_LEVELS = ("high", "medium", "low", "unknown")
EVIDENCE_STATES = ("recorded", "derived", "not_recorded", "not_inferable")
PROXY_FIELDS = ("action_count", "elapsed_ms", "token_count")
# C1 observes governance only through recognized file reads.  Governance CLI
# output and harness-injected instructions can reach the agent unobserved, so
# encounter evidence is never exhaustive exposure evidence.
ENCOUNTER_CHANNELS = {
    "file_reads": "partial",
    "governance_cli_output": "not_observed",
    "injected_instructions": "not_observed",
}
ROUTE_ALIGNMENT_STATES = (
    "resolver_unavailable",
    "no_observed_modified_surface",
    "mismatch_observed",
    "no_mismatch_observed",
)
_ROUTE_SURFACE_HINTS = {
    "godot": "godot_product_shell",
    "native": "native_deterministic_core",
    "packaging": "packaging_and_release",
}
_G1_ARTIFACT_ROLES = {*ARTIFACT_ROLES, "unclassified"}
# Identity and provenance are bound mechanically; an evaluator cannot move a
# judgement onto another trajectory, segment, task group, or declared G1 task.
_INTERACTION_IDENTITY_FIELDS = {
    "id",
    "task_group_id",
    "g1_task_id",
    "source_trajectory_id",
    "segment",
}
# A post-mortem covers one human-turn interaction segment, which is not
# necessarily an engineering task.  The engineering task a segment belongs to
# is reserved for a future grouping of segments; this version asserts none.
_UNASSIGNED_TASK_GROUP = {"value": None, "evidence_state": "not_inferable"}


class PostmortemValidationError(ValueError):
    """A post-mortem attempted to imply evidence it does not contain."""


def _value_state(value: object, *, derived: bool = False) -> str:
    if value is not None:
        return "derived" if derived else "recorded"
    return "not_recorded"


def _optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PostmortemValidationError(f"{field} must be a non-empty string or null")
    return value


def _optional_count(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise PostmortemValidationError(
            f"{field} must be a non-negative integer or null"
        )
    return value


def _field(value: object, *, derived: bool = False) -> dict[str, object]:
    return {"value": value, "evidence_state": _value_state(value, derived=derived)}


def _normalize_field(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"value", "evidence_state"}:
        raise PostmortemValidationError(
            f"{field} must contain exactly value and evidence_state"
        )
    if value["evidence_state"] not in EVIDENCE_STATES:
        raise PostmortemValidationError(f"{field}.evidence_state is invalid")
    return {"value": value["value"], "evidence_state": value["evidence_state"]}


def _token_count(source: dict[str, Any]) -> int | None:
    information = source.get("token_information")
    if not isinstance(information, dict):
        return None
    total = information.get("total_token_usage")
    if not isinstance(total, dict):
        return None
    value = total.get("total_tokens")
    return (
        value
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0
        else None
    )


def _empty_measure() -> dict[str, object]:
    return {
        "action_count": None,
        "elapsed_ms": None,
        "token_count": None,
        "evidence_state": "not_inferable",
    }


def _normalize_measure(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        *PROXY_FIELDS,
        "evidence_state",
    }:
        raise PostmortemValidationError(
            f"{label} must contain proxy fields and evidence_state"
        )
    evidence_state = value["evidence_state"]
    if evidence_state not in EVIDENCE_STATES:
        raise PostmortemValidationError(f"{label}.evidence_state is invalid")
    return {
        proxy: _optional_count(value[proxy], f"{label}.{proxy}")
        for proxy in PROXY_FIELDS
    } | {"evidence_state": evidence_state}


def _activity_total(trajectory: dict[str, Any]) -> dict[str, object]:
    """Measure each burden proxy once over the scoped normalized trajectory."""
    source = trajectory["source"]
    return {
        # C1's canonical tool-call proxy: one execution event per completed call.
        "action_count": len(trajectory["execution_events"]),
        "elapsed_ms": source["elapsed_ms"],
        "token_count": _token_count(source),
        "evidence_state": "derived",
    }


def _unattributed_remainder(
    total: dict[str, object], activity: dict[str, dict[str, object]]
) -> dict[str, object]:
    """Return ``unknown`` as whatever measured activity remains unattributed."""
    remainder: dict[str, object] = {}
    for proxy in PROXY_FIELDS:
        measured = total[proxy]
        attributed = [
            value
            for category in ACTIVITY_CATEGORIES
            if category != "unknown"
            and isinstance(value := activity[category][proxy], int)
        ]
        if not isinstance(measured, int):
            if attributed:
                raise PostmortemValidationError(
                    f"activity {proxy} cannot be attributed without a measured total"
                )
            remainder[proxy] = None
        elif sum(attributed) > measured:
            raise PostmortemValidationError(
                f"attributed activity {proxy} exceeds the measured total"
            )
        else:
            remainder[proxy] = measured - sum(attributed)
    return remainder | {"evidence_state": "derived"}


def _empty_activity(total: dict[str, object]) -> dict[str, dict[str, object]]:
    activity = {category: _empty_measure() for category in ACTIVITY_CATEGORIES}
    activity["unknown"] = _unattributed_remainder(total, activity)
    return activity


def _normalize_activity(
    value: object, total: dict[str, object]
) -> dict[str, dict[str, object]]:
    if not isinstance(value, dict) or set(value) != set(ACTIVITY_CATEGORIES):
        raise PostmortemValidationError(
            "activity must provide every supported category exactly once"
        )
    activity = {
        category: _normalize_measure(value[category], f"activity.{category}")
        for category in ACTIVITY_CATEGORIES
    }
    # Categories partition each measured proxy: T = P + Mr + Mi + W + U.
    if activity["unknown"] != _unattributed_remainder(total, activity):
        raise PostmortemValidationError(
            "activity categories must partition activity_total for every proxy"
        )
    return activity


def _encounter(event: dict[str, Any]) -> dict[str, object]:
    section = event.get("authority") or event.get("route")
    return {
        "source": event["path"],
        "rule_or_section": section,
        "encountered_at": event["sequence"],
        "decision": None,
        "effect": "unknown",
        "outcome_evidence": None,
        "confidence": "unknown",
        "exposure_evidence": event.get("evidence"),
    }


_EDGE_QUALITATIVE_FIELDS = {
    "structural_navigability": {"not_recorded", "adequate", "problem_observed"},
    "staleness": {"not_recorded", "not_observed", "problem_observed"},
    "contradictory_active_state": {
        "not_recorded",
        "not_observed",
        "problem_observed",
    },
    "authority_duplication": {"not_recorded", "not_observed", "problem_observed"},
    "information_retention": {
        "not_recorded",
        "retained",
        "information_loss_observed",
    },
    "size_related_friction": {"not_recorded", "not_observed", "observed"},
}


def _edge_state_assessment(
    trajectory: dict[str, Any], projection: dict[str, object]
) -> list[dict[str, object]]:
    """Report edge-state access separately from raw file-size interpretation."""
    reads = [
        event
        for event in trajectory["retrieval_events"]
        if event["source_class"] == "governance" and event["file_class"] == "edge_state"
    ]
    result: list[dict[str, object]] = []
    for path in sorted({event["path"] for event in reads}):
        path_reads = [event for event in reads if event["path"] == path]
        bounded = sum(event["access_mode"] == "bounded" for event in path_reads)
        whole = sum(event["access_mode"] == "whole_file" for event in path_reads)
        unknown = sum(event["access_mode"] == "unknown" for event in path_reads)
        locality = (
            "whole_file_observed"
            if whole and not bounded
            else "mixed"
            if whole and bounded
            else "bounded_only"
            if bounded and not unknown
            else "unknown"
        )
        known = [event["materialized_bytes"] for event in path_reads]
        registrations = {
            event["registered_on_governance_surface"] for event in path_reads
        }
        roles = {event["edge_state_role"] for event in path_reads}
        rationales = {
            tuple(event["edge_limit_rationale"] or []) for event in path_reads
        }
        projected = projection.get("projected_sources")
        routed = (
            "not_recorded"
            if not isinstance(projected, list)
            else "routed"
            if any(
                isinstance(item, dict)
                and isinstance(item.get("source"), str)
                and _source_matches_path(item["source"], path)
                for item in projected
            )
            else "not_routed"
        )
        result.append(
            {
                "source": path,
                "file_class": "edge_state",
                "operational_role": next(iter(roles)) if len(roles) == 1 else None,
                "registered_on_governance_surface": (
                    next(iter(registrations)) if len(registrations) == 1 else None
                ),
                "routed_for_segment": routed,
                "limit_rationale": list(next(iter(rationales)))
                if len(rationales) == 1
                else None,
                "read_events": len(path_reads),
                "repeated_reads": max(0, len(path_reads) - 1),
                "bounded_reads": bounded,
                "whole_file_reads": whole,
                "unknown_mode_reads": unknown,
                "segment_local_materialized_bytes": (
                    sum(value for value in known if isinstance(value, int))
                    if all(isinstance(value, int) for value in known)
                    else None
                ),
                "access_locality": locality,
                "raw_size_is_quality_penalty": False,
                **{field: "not_recorded" for field in _EDGE_QUALITATIVE_FIELDS},
            }
        )
    return result


def _normalize_edge_state_assessment(  # noqa: C901 - one record is validated atomically
    value: object,
) -> list[dict[str, object]]:
    required = {
        "source",
        "file_class",
        "operational_role",
        "registered_on_governance_surface",
        "routed_for_segment",
        "limit_rationale",
        "read_events",
        "repeated_reads",
        "bounded_reads",
        "whole_file_reads",
        "unknown_mode_reads",
        "segment_local_materialized_bytes",
        "access_locality",
        "raw_size_is_quality_penalty",
        *_EDGE_QUALITATIVE_FIELDS,
    }
    if not isinstance(value, list):
        raise PostmortemValidationError("edge_state_assessment must be an array")
    normalized: list[dict[str, object]] = []
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != required:
            raise PostmortemValidationError(
                "edge-state assessment has an invalid shape"
            )
        source = _optional_text(entry["source"], "edge-state source")
        counts = {
            key: _optional_count(entry[key], f"edge-state {key}")
            for key in (
                "read_events",
                "repeated_reads",
                "bounded_reads",
                "whole_file_reads",
                "unknown_mode_reads",
            )
        }
        if source is None or any(item is None for item in counts.values()):
            raise PostmortemValidationError(
                "edge-state assessment requires source/counts"
            )
        if (
            entry["file_class"] != "edge_state"
            or entry["raw_size_is_quality_penalty"] is not False
        ):
            raise PostmortemValidationError(
                "edge-state assessment has invalid class semantics"
            )
        if entry["operational_role"] not in {
            "conditional_open_work_authority",
            "restart_handoff_context",
            None,
        } or entry["registered_on_governance_surface"] not in {True, False, None}:
            raise PostmortemValidationError(
                "edge-state operational metadata is invalid"
            )
        if entry["routed_for_segment"] not in {"routed", "not_routed", "not_recorded"}:
            raise PostmortemValidationError("edge-state routing state is invalid")
        if entry["limit_rationale"] is not None and (
            not isinstance(entry["limit_rationale"], list)
            or any(not isinstance(item, str) for item in entry["limit_rationale"])
        ):
            raise PostmortemValidationError("edge-state limit rationale is invalid")
        if (
            counts["bounded_reads"]
            + counts["whole_file_reads"]
            + counts["unknown_mode_reads"]
            != counts["read_events"]
        ):
            raise PostmortemValidationError(
                "edge-state access counts must partition reads"
            )
        if counts["repeated_reads"] != max(0, counts["read_events"] - 1):
            raise PostmortemValidationError("edge-state repeated read count is invalid")
        if entry["access_locality"] not in {
            "bounded_only",
            "whole_file_observed",
            "mixed",
            "unknown",
        }:
            raise PostmortemValidationError("edge-state access locality is invalid")
        _optional_count(
            entry["segment_local_materialized_bytes"],
            "edge-state segment_local_materialized_bytes",
        )
        for field, allowed in _EDGE_QUALITATIVE_FIELDS.items():
            if entry[field] not in allowed:
                raise PostmortemValidationError(f"edge-state {field} is invalid")
        normalized.append(deepcopy(entry))
    if len({item["source"] for item in normalized}) != len(normalized):
        raise PostmortemValidationError("edge-state assessments must be one per source")
    return normalized


def _normalize_effect(value: object) -> dict[str, object]:
    required = {
        "source",
        "rule_or_section",
        "encountered_at",
        "decision",
        "effect",
        "outcome_evidence",
        "confidence",
        "exposure_evidence",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PostmortemValidationError("manifest effect has an invalid shape")
    source = _optional_text(value["source"], "manifest effect source")
    encountered_at = _optional_count(
        value["encountered_at"], "manifest effect encountered_at"
    )
    if source is None or encountered_at is None:
        raise PostmortemValidationError(
            "manifest effect requires source and encountered_at"
        )
    if value["effect"] not in CONTRIBUTION_CATEGORIES:
        raise PostmortemValidationError("manifest effect category is invalid")
    if value["confidence"] not in CONFIDENCE_LEVELS:
        raise PostmortemValidationError("manifest effect confidence is invalid")
    for field in (
        "rule_or_section",
        "decision",
        "outcome_evidence",
        "exposure_evidence",
    ):
        _optional_text(value[field], f"manifest effect {field}")
    if value["effect"] != "unknown" and (
        value["decision"] is None or value["outcome_evidence"] is None
    ):
        raise PostmortemValidationError(
            "a non-unknown manifest effect requires decision and outcome_evidence"
        )
    return deepcopy(value)


def _normalize_missing_guidance(value: object) -> list[dict[str, str | None]]:
    if not isinstance(value, list):
        raise PostmortemValidationError("missing_guidance must be an array")
    normalized: list[dict[str, str | None]] = []
    for entry in value:
        if not isinstance(entry, dict) or set(entry) != {
            "issue",
            "evidence",
            "candidate_scope",
        }:
            raise PostmortemValidationError(
                "missing guidance entry has an invalid shape"
            )
        issue = _optional_text(entry["issue"], "missing guidance issue")
        evidence = _optional_text(entry["evidence"], "missing guidance evidence")
        scope = _optional_text(
            entry["candidate_scope"], "missing guidance candidate_scope"
        )
        if issue is None:
            raise PostmortemValidationError("missing guidance issue is required")
        normalized.append(
            {"issue": issue, "evidence": evidence, "candidate_scope": scope}
        )
    return normalized


def _default_outcome(trajectory: dict[str, Any]) -> dict[str, object]:
    failed_tests = [
        event["sequence"]
        for event in trajectory["execution_events"]
        if event["is_test"] is True and event["exit_code"] not in {None, 0}
    ]
    repeated_failures = sum(
        event["repeated_failure"] is True for event in trajectory["execution_events"]
    )
    return {
        "status": _field(None),
        "verification_failures": failed_tests,
        "rework": _field(repeated_failures, derived=True),
        "review_findings": _field(None),
    }


def _normalize_outcome(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "status",
        "verification_failures",
        "rework",
        "review_findings",
    }:
        raise PostmortemValidationError("outcome has an invalid shape")
    if not isinstance(value["verification_failures"], list) or any(
        not isinstance(item, int) or isinstance(item, bool) or item < 1
        for item in value["verification_failures"]
    ):
        raise PostmortemValidationError(
            "verification_failures must contain event sequences"
        )
    return {
        "status": _normalize_field(value["status"], "outcome.status"),
        "verification_failures": list(value["verification_failures"]),
        "rework": _normalize_field(value["rework"], "outcome.rework"),
        "review_findings": _normalize_field(
            value["review_findings"], "outcome.review_findings"
        ),
    }


def _default_interaction(
    trajectory: dict[str, Any],
    interaction_segment: dict[str, object],
    segment: dict[str, Any] | None,
) -> dict[str, object]:
    source = trajectory["source"]
    segment_data = segment.get("segment") if isinstance(segment, dict) else None
    start_boundary = (
        segment.get("start_boundary") if isinstance(segment, dict) else None
    )
    end_boundary = segment.get("end_boundary") if isinstance(segment, dict) else None
    segment_data = segment_data if isinstance(segment_data, dict) else {}
    start_boundary = start_boundary if isinstance(start_boundary, dict) else {}
    end_boundary = end_boundary if isinstance(end_boundary, dict) else {}
    start_commit = start_boundary.get("head") or source.get("repository_revision")
    end_commit = end_boundary.get("head")
    return {
        # The structural C1 human-turn segment is the record identity.  Which
        # engineering task it serves is not inferable yet; a G1-declared task id
        # is kept beside it as provenance, never promoted to a task group.
        "id": _field(interaction_segment["id"], derived=True),
        "task_group_id": dict(_UNASSIGNED_TASK_GROUP),
        "g1_task_id": _field(segment_data.get("task_id")),
        "description": _field(None),
        "task_class": _field(None),
        "model": _field(source.get("model")),
        "model_version": _field(None),
        "session_id": _field(segment_data.get("session_id")),
        "branch": _field(None),
        "start_commit": _field(
            start_commit, derived=start_commit == source.get("repository_revision")
        ),
        "end_commit": _field(end_commit),
        # A repository commit is an auditable snapshot binding, not a claim that
        # every manifest has a separate version number.
        "manifest_revision": _field(
            source.get("repository_revision"),
            derived=source.get("repository_revision") is not None,
        ),
        "source_trajectory_id": source["source_id"],
        "segment": deepcopy(interaction_segment),
    }


def _normalize_interaction(value: object) -> dict[str, object]:
    fields = {
        "id",
        "task_group_id",
        "g1_task_id",
        "description",
        "task_class",
        "model",
        "model_version",
        "session_id",
        "branch",
        "start_commit",
        "end_commit",
        "manifest_revision",
        "source_trajectory_id",
        "segment",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise PostmortemValidationError("interaction has an invalid shape")
    result = {
        field: _normalize_field(value[field], f"interaction.{field}")
        for field in fields - {"source_trajectory_id", "segment"}
    }
    if result["task_group_id"] != _UNASSIGNED_TASK_GROUP:
        raise PostmortemValidationError(
            "interaction.task_group_id is reserved: a human-turn segment is not "
            "asserted to be, or to share, an engineering task"
        )
    source_id = _optional_text(
        value["source_trajectory_id"], "interaction.source_trajectory_id"
    )
    if source_id is None:
        raise PostmortemValidationError("interaction.source_trajectory_id is required")
    result["source_trajectory_id"] = source_id
    result["segment"] = _normalize_interaction_segment(value["segment"])
    if result["id"]["value"] != result["segment"]["id"]:
        raise PostmortemValidationError("interaction.id must name its segment")
    return {field: result[field] for field in value}


def _normalize_interaction_segment(value: object) -> dict[str, object]:
    """Validate with C1's own segment contract, so the two cannot drift."""
    try:
        segments = normalize_interaction_segments([value])
    except TrajectoryValidationError as exc:
        raise PostmortemValidationError(f"interaction.segment: {exc}") from exc
    assert segments is not None
    return segments[0]


def _entry_value(entries: dict[str, Any], name: str) -> object:
    entry = entries.get(name)
    return entry.get("value") if isinstance(entry, dict) else None


def _add_projected_source(
    sources: dict[str, dict[str, set[str]]],
    source: object,
    *,
    authority: object = None,
    route: object = None,
) -> None:
    if not isinstance(source, str) or not source:
        return
    item = sources.setdefault(source, {"authority_ids": set(), "route_ids": set()})
    if isinstance(authority, str):
        item["authority_ids"].add(authority)
    if isinstance(route, str):
        item["route_ids"].add(route)


def _add_authority_sources(
    sources: dict[str, dict[str, set[str]]], authorities: object
) -> None:
    if not isinstance(authorities, list):
        return
    for authority in authorities:
        if isinstance(authority, dict):
            _add_projected_source(
                sources,
                authority.get("source"),
                authority=authority.get("authority_id"),
            )


def _add_route_dispatch_sources(
    sources: dict[str, dict[str, set[str]]], routes: object
) -> None:
    if not isinstance(routes, dict):
        return
    for route_id, route in routes.items():
        if isinstance(route, dict):
            for dispatch_path in route.get("dispatch_paths", []):
                _add_projected_source(sources, dispatch_path, route=route_id)


def _projected_sources(resolver_output: dict[str, Any]) -> list[dict[str, object]]:
    """Index canonical resolver sources without introducing rule identifiers."""
    entries = resolver_output.get("entries")
    if not isinstance(entries, dict):
        return []
    sources: dict[str, dict[str, set[str]]] = {}
    _add_authority_sources(sources, _entry_value(entries, "authorities"))
    _add_route_dispatch_sources(sources, _entry_value(entries, "routes"))
    return [
        {
            "source": source,
            "authority_ids": sorted(item["authority_ids"]),
            "route_ids": sorted(item["route_ids"]),
        }
        for source, item in sorted(sources.items())
    ]


def _resolver_resolution_state(resolver_output: dict[str, Any]) -> dict[str, str]:
    entries = resolver_output.get("entries")
    if not isinstance(entries, dict):
        raise PostmortemValidationError(
            "resolver output must contain an entries object"
        )
    scenario = _entry_value(entries, "matched_scenario")
    routes = _entry_value(entries, "routes")
    if scenario is not None:
        scenario_state = "matched_scenario"
    else:
        scenario_state = "no_matching_scenario"
    route_state = (
        "scenario_routes"
        if scenario is not None
        else "fallback_or_default_route"
        if isinstance(routes, dict) and routes
        else "no_projected_route"
    )
    return {"scenario_state": scenario_state, "route_state": route_state}


def _unavailable_resolver_projection() -> dict[str, object]:
    return {
        "evidence_state": "not_recorded",
        "task_text": None,
        "resolution": {"scenario_state": "not_recorded", "route_state": "not_recorded"},
        "resolver_output": None,
        "projected_sources": None,
    }


def _resolver_projection(value: object) -> dict[str, object]:
    if value is None:
        return _unavailable_resolver_projection()
    if not isinstance(value, dict) or set(value) != {"task_text", "resolver_output"}:
        raise PostmortemValidationError(
            "resolver evidence must contain exactly task_text and resolver_output"
        )
    task_text = _optional_text(value["task_text"], "resolver task_text")
    resolver_output = value["resolver_output"]
    if task_text is None or not isinstance(resolver_output, dict):
        raise PostmortemValidationError(
            "recorded resolver evidence requires exact task_text and object output"
        )
    if resolver_output.get("schema_version") != 1:
        raise PostmortemValidationError("unsupported resolver output schema version")
    return {
        "evidence_state": "recorded",
        "task_text": task_text,
        "resolution": _resolver_resolution_state(resolver_output),
        "resolver_output": deepcopy(resolver_output),
        "projected_sources": _projected_sources(resolver_output),
    }


def _normalize_resolver_projection(value: object) -> dict[str, object]:
    required = {
        "evidence_state",
        "task_text",
        "resolution",
        "resolver_output",
        "projected_sources",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PostmortemValidationError("resolver_projection has an invalid shape")
    if value["evidence_state"] == "not_recorded":
        if value != _unavailable_resolver_projection():
            raise PostmortemValidationError(
                "unavailable resolver_projection must preserve explicit absence"
            )
        return deepcopy(value)
    if value["evidence_state"] != "recorded":
        raise PostmortemValidationError("resolver_projection evidence_state is invalid")
    normalized = _resolver_projection(
        {"task_text": value["task_text"], "resolver_output": value["resolver_output"]}
    )
    if value != normalized:
        raise PostmortemValidationError(
            "resolver_projection derived fields must match captured resolver output"
        )
    return normalized


def _source_matches_path(source: str, path: str) -> bool:
    return path == source or (source.endswith("/") and path.startswith(source))


def _projected_read_comparison(
    projection: dict[str, object], trajectory: dict[str, Any]
) -> dict[str, object]:
    limitations = [item["kind"] for item in trajectory["evidence_limitations"]]
    if projection["evidence_state"] != "recorded":
        return {
            "evidence_state": "not_recorded",
            "projected_and_read": None,
            "projected_not_observed_read": None,
            "read_not_projected": None,
            "read_evidence_limitations": limitations,
            "causal_interpretation": "unknown",
        }
    # Deliberately asymmetric: a projected source is read when any observed read
    # matches it, whatever its C1 source_class (C1 classes some projected
    # authorities, such as docs/ARCHITECTURE_CONTRACT.md, as non_governance).
    # read_not_projected reports only governance-classified reads.
    reads = trajectory["retrieval_events"]
    governance_reads = [
        event for event in reads if event["source_class"] == "governance"
    ]
    projected_and_read: list[dict[str, object]] = []
    projected_not_observed_read: list[dict[str, object]] = []
    sources = projection["projected_sources"]
    assert isinstance(sources, list)
    for projected in sources:
        source = projected["source"]
        assert isinstance(source, str)
        matching_reads = [
            event for event in reads if _source_matches_path(source, event["path"])
        ]
        entry = {
            "source": source,
            "authority_ids": projected["authority_ids"],
            "route_ids": projected["route_ids"],
            "observed_read_sequences": [event["sequence"] for event in matching_reads],
        }
        (projected_and_read if matching_reads else projected_not_observed_read).append(
            entry
        )
    read_not_projected = [
        {"source": path, "observed_read_sequences": sequences}
        for path, sequences in sorted(
            {
                path: [
                    event["sequence"]
                    for event in governance_reads
                    if event["path"] == path
                ]
                for path in {event["path"] for event in governance_reads}
                if not any(
                    _source_matches_path(item["source"], path) for item in sources
                )
            }.items()
        )
    ]
    return {
        "evidence_state": "recorded",
        "projected_and_read": projected_and_read,
        "projected_not_observed_read": projected_not_observed_read,
        "read_not_projected": read_not_projected,
        "read_evidence_limitations": limitations,
        "causal_interpretation": "unknown",
    }


def _normalize_projected_read_comparison(value: object) -> dict[str, object]:
    required = {
        "evidence_state",
        "projected_and_read",
        "projected_not_observed_read",
        "read_not_projected",
        "read_evidence_limitations",
        "causal_interpretation",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PostmortemValidationError(
            "projected_read_comparison has an invalid shape"
        )
    if value["evidence_state"] not in {"recorded", "not_recorded"}:
        raise PostmortemValidationError(
            "projected_read_comparison evidence_state is invalid"
        )
    if value["causal_interpretation"] != "unknown":
        raise PostmortemValidationError(
            "projected_read_comparison must not imply causal interpretation"
        )
    fields = ("projected_and_read", "projected_not_observed_read", "read_not_projected")
    if value["evidence_state"] == "recorded":
        lists_valid = all(isinstance(value[field], list) for field in fields)
    else:
        lists_valid = all(value[field] is None for field in fields)
    if not lists_valid or not isinstance(value["read_evidence_limitations"], list):
        raise PostmortemValidationError(
            "projected_read_comparison lists must be null exactly when resolver "
            "evidence is absent"
        )
    return deepcopy(value)


def _observed_modified_paths(
    trajectory: dict[str, Any], segment: dict[str, Any] | None
) -> tuple[list[str], str]:
    artifacts = segment.get("artifacts") if isinstance(segment, dict) else None
    if isinstance(artifacts, list):
        return (
            sorted(
                item["path"]
                for item in artifacts
                if isinstance(item, dict) and isinstance(item.get("path"), str)
            ),
            "g1_segment",
        )
    return sorted(
        {event["path"] for event in trajectory["mutation_events"]}
    ), "c1_mutation"


def _validate_work_segment(segment: dict[str, Any] | None) -> dict[str, Any] | None:
    """Accept only G1 artifacts carrying explicit, canonical role evidence."""
    if segment is None:
        return None
    if not isinstance(segment, dict):
        raise PostmortemValidationError("work_segment must be an object")
    artifacts = segment.get("artifacts")
    if not isinstance(artifacts, list):
        raise PostmortemValidationError("work_segment.artifacts must be an array")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise PostmortemValidationError("G1 artifact must be an object")
        path = artifact.get("path")
        role = artifact.get("role")
        if not isinstance(path, str) or not path or role not in _G1_ARTIFACT_ROLES:
            raise PostmortemValidationError(
                "G1 artifact requires a non-empty path and explicit supported role"
            )
    return deepcopy(segment)


def _artifact_coverage(segment: dict[str, Any] | None) -> dict[str, object]:
    artifacts = segment.get("artifacts") if isinstance(segment, dict) else None
    if not isinstance(artifacts, list):
        return {
            "observed": None,
            "classified": None,
            "unclassified": None,
            "interpretation": {"state": "unavailable", "normative": False},
        }
    classified = sum(item["role"] in ARTIFACT_ROLES for item in artifacts)
    return {
        "observed": len(artifacts),
        "classified": classified,
        "unclassified": len(artifacts) - classified,
        "interpretation": {"state": "migration_limited", "normative": False},
    }


def _route_work_alignment(
    projection: dict[str, object],
    trajectory: dict[str, Any],
    segment: dict[str, Any] | None,
) -> dict[str, object]:
    paths, source = _observed_modified_paths(trajectory, segment)
    surfaces = sorted({path.split("/", 1)[0] for path in paths if "/" in path})
    alignment: dict[str, object] = {
        "state": "resolver_unavailable",
        "projected_routes": None,
        "observed_surfaces": surfaces,
        "modified_path_evidence": source,
        "dedicated_routes_not_projected": None,
        "projected_dedicated_routes_unmodified": None,
        "causal_interpretation": "unknown",
    }
    if projection["evidence_state"] != "recorded":
        return alignment
    output = projection["resolver_output"]
    assert isinstance(output, dict)
    route_value = _entry_value(output["entries"], "routes")
    routes = sorted(route_value) if isinstance(route_value, dict) else []
    # Compared in both directions, but only for surfaces with a dedicated route.
    not_projected = sorted(
        {
            route
            for surface, route in _ROUTE_SURFACE_HINTS.items()
            if surface in surfaces and route not in routes
        }
    )
    unmodified = sorted(
        {
            route
            for surface, route in _ROUTE_SURFACE_HINTS.items()
            if route in routes and surface not in surfaces
        }
    )
    alignment |= {
        "state": "no_observed_modified_surface"
        if not surfaces
        else "mismatch_observed"
        if not_projected or unmodified
        else "no_mismatch_observed",
        "projected_routes": routes,
        "dedicated_routes_not_projected": not_projected,
        "projected_dedicated_routes_unmodified": unmodified,
    }
    return alignment


def _normalize_route_work_alignment(value: object) -> dict[str, object]:
    route_fields = (
        "projected_routes",
        "dedicated_routes_not_projected",
        "projected_dedicated_routes_unmodified",
    )
    required = {
        "state",
        "observed_surfaces",
        "modified_path_evidence",
        "causal_interpretation",
        *route_fields,
    }
    if not isinstance(value, dict) or set(value) != required:
        raise PostmortemValidationError("route_work_alignment has an invalid shape")
    if value["causal_interpretation"] != "unknown":
        raise PostmortemValidationError("route_work_alignment must remain advisory")
    if value["state"] not in ROUTE_ALIGNMENT_STATES or value[
        "modified_path_evidence"
    ] not in {"g1_segment", "c1_mutation"}:
        raise PostmortemValidationError("route_work_alignment state is invalid")
    if value["state"] == "resolver_unavailable":
        routes_valid = all(value[field] is None for field in route_fields)
    else:
        routes_valid = all(isinstance(value[field], list) for field in route_fields)
    if not routes_valid or not isinstance(value["observed_surfaces"], list):
        raise PostmortemValidationError(
            "route_work_alignment routes must be null exactly when resolver "
            "evidence is absent"
        )
    return deepcopy(value)


def _normalize_artifact_coverage(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "observed",
        "classified",
        "unclassified",
        "interpretation",
    }:
        raise PostmortemValidationError("artifact_coverage has an invalid shape")
    interpretation = value["interpretation"]
    if not isinstance(interpretation, dict) or set(interpretation) != {
        "state",
        "normative",
    }:
        raise PostmortemValidationError("artifact_coverage interpretation is invalid")
    if interpretation["normative"] is not False or interpretation["state"] not in {
        "migration_limited",
        "unavailable",
    }:
        raise PostmortemValidationError("artifact_coverage must remain non-normative")
    for field in ("observed", "classified", "unclassified"):
        _optional_count(value[field], f"artifact_coverage.{field}")
    counts = (value["observed"], value["classified"], value["unclassified"])
    if counts == (None, None, None):
        return deepcopy(value)
    if not all(isinstance(count, int) for count in counts) or (
        value["observed"] != value["classified"] + value["unclassified"]
    ):
        raise PostmortemValidationError(
            "artifact_coverage counts must partition observed"
        )
    return deepcopy(value)


def _coverage_block(execution_events: int, unrecovered: int) -> dict[str, object]:
    return {
        "channels": dict(ENCOUNTER_CHANNELS),
        "completeness": "partial",
        "execution_events": execution_events,
        # Tool calls with no recovered shell command: any reads they made are
        # invisible, so few encounters is not evidence of little exposure.
        "execution_events_without_recovered_command": unrecovered,
    }


def _encounter_coverage(trajectory: dict[str, Any]) -> dict[str, object]:
    executions = trajectory["execution_events"]
    return _coverage_block(
        len(executions),
        sum(event["command_identity"] is None for event in executions),
    )


def _normalize_encounter_coverage(value: object) -> dict[str, object]:
    counts = (
        (
            value.get("execution_events"),
            value.get("execution_events_without_recovered_command"),
        )
        if isinstance(value, dict)
        else (None, None)
    )
    total, unrecovered = (
        _optional_count(count, "encounter_coverage") for count in counts
    )
    if (
        total is None
        or unrecovered is None
        or unrecovered > total
        or value != _coverage_block(total, unrecovered)
    ):
        raise PostmortemValidationError(
            "encounter_coverage must declare partial governance exposure"
        )
    return deepcopy(value)


def normalize_postmortem_record(payload: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version",
        "interaction",
        "outcome",
        "activity_total",
        "activity",
        "manifest_effects",
        "edge_state_assessment",
        "missing_guidance",
        "evidence_limitations",
        "encounter_coverage",
        "resolver_projection",
        "projected_read_comparison",
        "route_work_alignment",
        "artifact_coverage",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise PostmortemValidationError("post-mortem has an invalid top-level shape")
    if payload["schema_version"] != POSTMORTEM_SCHEMA_VERSION:
        raise PostmortemValidationError("unsupported post-mortem schema version")
    effects = [_normalize_effect(effect) for effect in payload["manifest_effects"]]
    keys = [(effect["source"], effect["encountered_at"]) for effect in effects]
    if len(keys) != len(set(keys)):
        raise PostmortemValidationError(
            "manifest encounters must be unique by source and sequence"
        )
    limitations = payload["evidence_limitations"]
    if not isinstance(limitations, list) or any(
        not isinstance(value, str) for value in limitations
    ):
        raise PostmortemValidationError("evidence_limitations must contain strings")
    total = _normalize_measure(payload["activity_total"], "activity_total")
    return {
        "schema_version": POSTMORTEM_SCHEMA_VERSION,
        "interaction": _normalize_interaction(payload["interaction"]),
        "outcome": _normalize_outcome(payload["outcome"]),
        "activity_total": total,
        "activity": _normalize_activity(payload["activity"], total),
        "manifest_effects": effects,
        "edge_state_assessment": _normalize_edge_state_assessment(
            payload["edge_state_assessment"]
        ),
        "missing_guidance": _normalize_missing_guidance(payload["missing_guidance"]),
        "evidence_limitations": list(limitations),
        "encounter_coverage": _normalize_encounter_coverage(
            payload["encounter_coverage"]
        ),
        "resolver_projection": _normalize_resolver_projection(
            payload["resolver_projection"]
        ),
        "projected_read_comparison": _normalize_projected_read_comparison(
            payload["projected_read_comparison"]
        ),
        "route_work_alignment": _normalize_route_work_alignment(
            payload["route_work_alignment"]
        ),
        "artifact_coverage": _normalize_artifact_coverage(payload["artifact_coverage"]),
    }


def _merge_fields(target: dict[str, Any], updates: object, label: str) -> None:
    if updates is None:
        return
    if not isinstance(updates, dict):
        raise PostmortemValidationError(f"{label} overlay must be an object")
    unknown = set(updates) - set(target)
    if unknown:
        raise PostmortemValidationError(
            f"unknown {label} overlay fields: {sorted(unknown)}"
        )
    for field, value in updates.items():
        if field == "verification_failures":
            target[field] = deepcopy(value)
        elif isinstance(target[field], dict) and "value" in target[field]:
            target[field] = _field(value)
        else:
            target[field] = deepcopy(value)


def _apply_activity_overlay(record: dict[str, Any], supplied: object) -> None:
    """Reclassify measured activity; ``unknown`` keeps only the remainder."""
    if not isinstance(supplied, dict):
        raise PostmortemValidationError("activity overlay must be an object")
    for category, measure in supplied.items():
        if category == "unknown":
            raise PostmortemValidationError(
                "activity.unknown is the unattributed remainder and cannot be set"
            )
        if category not in ACTIVITY_CATEGORIES:
            raise PostmortemValidationError(f"unknown activity category: {category}")
        if not isinstance(measure, dict) or not set(measure) <= set(PROXY_FIELDS):
            raise PostmortemValidationError(
                "activity measure overlay may only set proxy fields"
            )
        merged = dict(record["activity"][category])
        for proxy, value in measure.items():
            merged[proxy] = _optional_count(value, f"activity.{category}.{proxy}")
        merged["evidence_state"] = "recorded"
        record["activity"][category] = merged
    record["activity"]["unknown"] = _unattributed_remainder(
        record["activity_total"], record["activity"]
    )


def _apply_effect_overlay(record: dict[str, Any], supplied_effects: object) -> None:
    if not isinstance(supplied_effects, list):
        raise PostmortemValidationError("manifest_effects overlay must be an array")
    encounters = {
        (effect["source"], effect["encountered_at"]): effect
        for effect in record["manifest_effects"]
    }
    annotated: set[tuple[object, object]] = set()
    for supplied in supplied_effects:
        if not isinstance(supplied, dict):
            raise PostmortemValidationError("manifest effect overlay must be an object")
        key = (supplied.get("source"), supplied.get("encountered_at"))
        if key in annotated:
            raise PostmortemValidationError(
                f"manifest effect overlay annotates encounter {key} more than once"
            )
        annotated.add(key)
        if key not in encounters:
            raise PostmortemValidationError(
                "manifest effect overlay must refer to an observed encounter"
            )
        merged = dict(encounters[key])
        if set(supplied) - set(merged):
            raise PostmortemValidationError(
                "manifest effect overlay has unknown fields"
            )
        merged.update(supplied)
        encounters[key].update(merged)


def _apply_edge_state_overlay(record: dict[str, Any], supplied: object) -> None:
    if not isinstance(supplied, list):
        raise PostmortemValidationError(
            "edge_state_assessment overlay must be an array"
        )
    assessments = {entry["source"]: entry for entry in record["edge_state_assessment"]}
    for update in supplied:
        if not isinstance(update, dict) or not isinstance(update.get("source"), str):
            raise PostmortemValidationError("edge-state overlay requires a source")
        source = update["source"]
        if source not in assessments:
            raise PostmortemValidationError(
                "edge-state overlay must refer to an observed edge-state read"
            )
        allowed = {"source", *_EDGE_QUALITATIVE_FIELDS}
        if set(update) - allowed:
            raise PostmortemValidationError("edge-state overlay has unknown fields")
        for field, value in update.items():
            if field != "source":
                assessments[source][field] = value


def _apply_evaluator_overlay(
    record: dict[str, Any], evaluator: dict[str, Any] | None
) -> None:
    if evaluator is None:
        return
    if not isinstance(evaluator, dict):
        raise PostmortemValidationError("evaluator overlay must be an object")
    allowed = {
        "interaction",
        "outcome",
        "activity",
        "manifest_effects",
        "edge_state_assessment",
        "missing_guidance",
    }
    unknown = set(evaluator) - allowed
    if unknown:
        raise PostmortemValidationError(f"unknown evaluator fields: {sorted(unknown)}")
    overlay = evaluator.get("interaction")
    if isinstance(overlay, dict) and set(overlay) & _INTERACTION_IDENTITY_FIELDS:
        raise PostmortemValidationError(
            "evaluator overlay cannot rebind interaction identity or provenance: "
            f"{sorted(set(overlay) & _INTERACTION_IDENTITY_FIELDS)}"
        )
    _merge_fields(record["interaction"], overlay, "interaction")
    _merge_fields(record["outcome"], evaluator.get("outcome"), "outcome")
    if "activity" in evaluator:
        _apply_activity_overlay(record, evaluator["activity"])
    if "manifest_effects" in evaluator:
        _apply_effect_overlay(record, evaluator["manifest_effects"])
    if "edge_state_assessment" in evaluator:
        _apply_edge_state_overlay(record, evaluator["edge_state_assessment"])
    if "missing_guidance" in evaluator:
        record["missing_guidance"] = deepcopy(evaluator["missing_guidance"])


_NORMALIZED_EVENT_GROUPS = {
    "retrieval_events": "retrieval",
    "mutation_events": "mutation",
    "execution_events": "execution",
}
_C1_INPUT_EVENT_KEYS = (
    "events",
    "retrieval_activity",
    "mutation_activity",
    "tool_activity",
)


def _c1_input(trajectory: dict[str, Any]) -> dict[str, Any]:
    """Return a payload C1 can normalize, including C1's own normalized output.

    ``normalize_trajectory`` reads raw ``events`` or legacy activity groups and
    silently finds no events in its own normalized groups, so those groups are
    re-expanded in sequence order rather than dropped.
    """
    if not isinstance(trajectory, dict) or any(
        key in trajectory for key in _C1_INPUT_EVENT_KEYS
    ):
        return trajectory
    if not any(key in trajectory for key in _NORMALIZED_EVENT_GROUPS):
        raise PostmortemValidationError("trajectory has no recognizable event groups")
    events: list[dict[str, Any]] = []
    for key, event_type in _NORMALIZED_EVENT_GROUPS.items():
        group = trajectory.get(key, [])
        if not isinstance(group, list) or not all(
            isinstance(event, dict) and isinstance(event.get("sequence"), int)
            for event in group
        ):
            raise PostmortemValidationError(f"{key} must contain sequenced events")
        events += [event | {"event_type": event_type} for event in group]
    events.sort(key=lambda event: event["sequence"])
    payload = {
        key: value
        for key, value in trajectory.items()
        if key not in _NORMALIZED_EVENT_GROUPS
    }
    return payload | {"events": events}


def plan_interaction_postmortems(
    trajectory: dict[str, Any],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Return a trajectory's human-turn interaction segments plus diagnostics.

    A trajectory without an interaction segment yields a diagnostic and no
    post-mortem, so every emitted post-mortem names an identified human turn.
    """
    normalized = normalize_trajectory(_c1_input(trajectory))
    source_id = normalized["source"]["source_id"]
    segments = normalized["interaction_segments"]
    if not segments:
        return [], [
            {
                "source_trajectory_id": source_id,
                "status": "interaction_boundary_unavailable",
                "reason": "boundaries_not_recorded"
                if segments is None
                else "no_structural_user_turn",
                "postmortem_emitted": False,
            }
        ]
    outside = sum(
        item["interaction_segment_id"] is None
        for group in (
            "retrieval_events",
            "mutation_events",
            "execution_events",
            "evidence_limitations",
        )
        for item in normalized[group]
    )
    diagnostics = [
        {
            "source_trajectory_id": source_id,
            "status": "evidence_outside_interaction_segments",
            "item_count": outside,
            "postmortem_emitted": True,
        }
    ]
    return deepcopy(segments), diagnostics if outside else []


def interaction_segments_from_trajectory(
    trajectory: dict[str, Any],
) -> list[dict[str, object]]:
    """Return structural C1 interaction segments, never a guessed whole rollout."""
    segments, diagnostics = plan_interaction_postmortems(trajectory)
    if not segments:
        (diagnostic,) = diagnostics
        raise PostmortemValidationError(
            f"trajectory {diagnostic['source_trajectory_id']} has no interaction "
            f"segment: {diagnostic['reason']}"
        )
    return segments


def _selected_interaction_segment(
    normalized: dict[str, Any], segment_id: str | None
) -> dict[str, object]:
    segments = interaction_segments_from_trajectory(normalized)
    source_id = normalized["source"]["source_id"]
    if segment_id is None:
        if len(segments) != 1:
            raise PostmortemValidationError(
                f"trajectory {source_id} contains {len(segments)} interaction "
                "segments; a post-mortem requires an explicit interaction_segment_id"
            )
        return segments[0]
    for segment in segments:
        if segment["id"] == segment_id:
            return segment
    raise PostmortemValidationError(
        f"trajectory {source_id} has no interaction segment {segment_id!r}"
    )


def _segment_scoped_trajectory(
    normalized: dict[str, Any], interaction_segment: dict[str, object]
) -> dict[str, Any]:
    """Slice every C1 event group to one structural human-turn segment."""
    segment_id = interaction_segment["id"]
    scoped = deepcopy(normalized)
    for group_name in (
        "retrieval_events",
        "mutation_events",
        "execution_events",
        "evidence_limitations",
    ):
        scoped[group_name] = [
            item
            for item in scoped[group_name]
            if item["interaction_segment_id"] == segment_id
        ]
    # C1's token/duration values are rollout totals.  They are only segment-local
    # when one human turn spans the entire source; multi-turn values stay
    # unavailable rather than being duplicated into each post-mortem.
    if len(normalized["interaction_segments"]) != 1:
        scoped["source"]["elapsed_ms"] = None
        scoped["source"]["token_information"] = None
    failed: set[str] = set()
    for event in scoped["execution_events"]:
        identity = event["command_identity"]
        if event["exit_code"] in {None, 0} or not isinstance(identity, str):
            # As in C1: without a failure and a command identity, repetition is
            # unknown, never asserted false.
            event["repeated_failure"] = None
        else:
            event["repeated_failure"] = identity in failed
            failed.add(identity)
    return scoped


def postmortem_from_trajectory(
    trajectory: dict[str, Any],
    *,
    interaction_segment_id: str | None = None,
    evaluator: dict[str, Any] | None = None,
    segment: dict[str, Any] | None = None,
    resolver_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Post-mortem one human-turn segment, deriving only evidenced facts.

    ``segment`` is an optional G1 work segment bound to that human turn.
    """
    normalized = normalize_trajectory(_c1_input(trajectory))
    interaction_segment = _selected_interaction_segment(
        normalized, interaction_segment_id
    )
    normalized = _segment_scoped_trajectory(normalized, interaction_segment)
    segment = _validate_work_segment(segment)
    projection = _resolver_projection(resolver_evidence)
    # Burden totals are C1 measurements of the scoped segment.  A G1 segment adds
    # its declared boundary and changed artifacts, not totals: its
    # tool_call_count defaults to 0 when unreported, like a measured zero.
    total = _activity_total(normalized)
    record: dict[str, Any] = {
        "schema_version": POSTMORTEM_SCHEMA_VERSION,
        "interaction": _default_interaction(normalized, interaction_segment, segment),
        "outcome": _default_outcome(normalized),
        "activity_total": total,
        "activity": _empty_activity(total),
        "manifest_effects": [
            _encounter(event)
            for event in normalized["retrieval_events"]
            if event["source_class"] == "governance"
        ],
        "edge_state_assessment": _edge_state_assessment(normalized, projection),
        "missing_guidance": [],
        "evidence_limitations": [
            limitation["kind"] for limitation in normalized["evidence_limitations"]
        ],
        "encounter_coverage": _encounter_coverage(normalized),
        "resolver_projection": projection,
        "projected_read_comparison": _projected_read_comparison(projection, normalized),
        "route_work_alignment": _route_work_alignment(projection, normalized, segment),
        "artifact_coverage": _artifact_coverage(segment),
    }
    _apply_evaluator_overlay(record, evaluator)
    return normalize_postmortem_record(record)


def _manifest_key(effect: dict[str, Any]) -> str:
    """Aggregate by source path; add a rule/section only when evidence records one."""
    section = effect["rule_or_section"]
    return effect["source"] if section is None else f"{effect['source']}#{section}"


def _sum_proxy(records: list[dict[str, Any]], proxy: str) -> dict[str, int | None]:
    values: dict[str, int | None] = {}
    for category in ACTIVITY_CATEGORIES:
        observed = [record["activity"][category][proxy] for record in records]
        values[category] = (
            sum(value for value in observed if isinstance(value, int))
            if any(isinstance(value, int) for value in observed)
            else None
        )
    return values


def _burden_ratio(values: dict[str, int | None]) -> float | None:
    """Meta over product activity, or null until both have been attributed."""
    product = values["product"]
    meta = [
        value
        for category in ("meta_required", "meta_induced")
        if (value := values[category]) is not None
    ]
    if not isinstance(product, int) or product <= 0 or not meta:
        return None
    return sum(meta) / product


def _group_summary(
    records: list[dict[str, Any]], effects: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Summarize unique segment records; ``effects`` narrows encounters to one key."""
    if effects is None:
        effects = [
            effect for record in records for effect in record["manifest_effects"]
        ]
    counts = Counter(effect["effect"] for effect in effects)
    contributions = {category: counts[category] for category in CONTRIBUTION_CATEGORIES}
    judged = len(effects) - contributions["unknown"]
    activity = {proxy: _sum_proxy(records, proxy) for proxy in PROXY_FIELDS}
    manifest_contributions: dict[str, Counter[str]] = defaultdict(Counter)
    for effect in effects:
        manifest_contributions[_manifest_key(effect)][effect["effect"]] += 1
    task_classes = Counter(
        str(record["interaction"]["task_class"]["value"] or "not_recorded")
        for record in records
    )
    return {
        "interaction_segment_count": len(records),
        "encounter_count": len(effects),
        "judged_encounter_count": judged,
        "contributions": contributions,
        # Null means not evaluated; 0.0 means judged with no positive contribution.
        "decision_yield": (
            (contributions["decisive"] + contributions["useful"]) / judged
            if judged
            else None
        ),
        "confirmatory_fraction": contributions["confirmatory"] / judged
        if judged
        else None,
        "activity": activity,
        "governance_burden_ratio": {
            proxy: _burden_ratio(values) for proxy, values in activity.items()
        },
        "task_classes": dict(sorted(task_classes.items())),
        "manifest_contributions": {
            key: {category: counts[category] for category in CONTRIBUTION_CATEGORIES}
            for key, counts in sorted(manifest_contributions.items())
        },
    }


def _segment_key(record: dict[str, Any]) -> tuple[str, str]:
    interaction = record["interaction"]
    return interaction["source_trajectory_id"], interaction["segment"]["id"]


def build_postmortem_aggregate(records: list[dict[str, Any]]) -> dict[str, Any]:
    normalized = [normalize_postmortem_record(record) for record in records]
    segment_keys = Counter(_segment_key(record) for record in normalized)
    repeated = sorted(key for key, count in segment_keys.items() if count > 1)
    if repeated:
        raise PostmortemValidationError(
            f"aggregate repeats interaction segments: {repeated}"
        )
    # A source key holds each interaction segment once plus only that key's
    # encounters, so rereads add encounters without adding segment activity.
    by_manifest: dict[
        str, tuple[dict[tuple[str, str], dict[str, Any]], list[dict[str, Any]]]
    ] = {}
    by_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_task_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    missing_guidance: Counter[tuple[str, str | None]] = Counter()
    for record in normalized:
        model = record["interaction"]["model"]["value"] or "not_recorded"
        task_class = record["interaction"]["task_class"]["value"] or "not_recorded"
        by_model[str(model)].append(record)
        by_task_class[str(task_class)].append(record)
        for effect in record["manifest_effects"]:
            segments, effects = by_manifest.setdefault(_manifest_key(effect), ({}, []))
            segments[_segment_key(record)] = record
            effects.append(effect)
        for item in record["missing_guidance"]:
            missing_guidance[(item["issue"], item["candidate_scope"])] += 1
    coverage = [record["encounter_coverage"] for record in normalized]
    return {
        "schema_version": POSTMORTEM_SCHEMA_VERSION,
        "interpretation": "descriptive_postmortem_evidence_not_causal_estimate",
        "interaction_segment_count": len(normalized),
        # Segments are human turns, not engineering tasks.  No record assigns a
        # task group yet, so the aggregate claims no task count at all.
        "task_group_count": None,
        "encounter_coverage": _coverage_block(
            sum(item["execution_events"] for item in coverage),
            sum(
                item["execution_events_without_recovered_command"] for item in coverage
            ),
        ),
        "overall": _group_summary(normalized),
        "by_manifest": {
            key: _group_summary(list(segments.values()), effects)
            for key, (segments, effects) in sorted(by_manifest.items())
        },
        "by_model": {
            key: _group_summary(value) for key, value in sorted(by_model.items())
        },
        "by_task_class": {
            key: _group_summary(value) for key, value in sorted(by_task_class.items())
        },
        "missing_guidance": [
            {"issue": issue, "candidate_scope": scope, "count": count}
            for (issue, scope), count in sorted(
                missing_guidance.items(),
                key=lambda item: (item[0][0], item[0][1] or ""),
            )
        ],
    }


def render_interaction_summary(record: dict[str, Any]) -> str:
    record = normalize_postmortem_record(record)
    interaction = record["interaction"]
    identity = interaction["description"]["value"] or interaction["id"]["value"]
    group = interaction["task_group_id"]
    revision = interaction["manifest_revision"]["value"]
    status = record["outcome"]["status"]
    coverage = record["encounter_coverage"]
    lines = [
        f"Interaction (human turn): {identity}",
        f"Task group: {group['value'] or group['evidence_state']}",
        f"Model: {interaction['model']['value'] or 'not_recorded'}",
        f"Manifest revision: {revision or 'not_recorded'}",
        "",
        f"Outcome: {status['value'] or status['evidence_state']}",
        "Manifest contribution (observed encounters by source):",
    ]
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for effect in record["manifest_effects"]:
        grouped[_manifest_key(effect)][effect["effect"]] += 1
    lines.extend(
        f"  {key}: "
        + ", ".join(
            f"{counts[category]} {category}"
            for category in CONTRIBUTION_CATEGORIES
            if counts[category]
        )
        for key, counts in sorted(grouped.items())
    )
    if not grouped:
        lines.append("  no observed manifest encounter")
    lines.append(
        f"  partial exposure: {coverage['execution_events_without_recovered_command']}"
        f" of {coverage['execution_events']} tool calls had no recovered command;"
        " governance CLI output and injected instructions are not observed"
    )
    lines.append(f"Activity ({record['activity_total']['action_count']} tool calls):")
    for category in ACTIVITY_CATEGORIES:
        count = record["activity"][category]["action_count"]
        # An unattributed category is unknown, not zero.
        shown = "not attributed" if count is None else f"{count} actions"
        lines.append(f"  {category}: {shown}")
    lines.append("Missing guidance:")
    lines.extend(f"  {item['issue']}" for item in record["missing_guidance"])
    if not record["missing_guidance"]:
        lines.append("  none recorded")
    return "\n".join(lines)


def bind_overlay_records(
    records: list[dict[str, Any]],
    payload_key: str,
    segment_keys: set[tuple[str, str]],
) -> dict[tuple[str, str], dict[str, Any]]:
    """Bind records to a structural ``(source_trajectory_id, interaction_segment_id)``.

    Supplied evidence is never silently dropped: a malformed, unmatched, or
    repeated binding fails and names every offending segment identity.
    """
    bound: dict[tuple[str, str], dict[str, Any]] = {}
    unmatched: set[tuple[str, str]] = set()
    repeated: set[tuple[str, str]] = set()
    fields = {"source_trajectory_id", "interaction_segment_id", payload_key}
    for record in records:
        if (
            set(record) != fields
            or not isinstance(record["source_trajectory_id"], str)
            or not isinstance(record["interaction_segment_id"], str)
            or not isinstance(record[payload_key], dict)
        ):
            raise PostmortemValidationError(
                f"{payload_key} records must contain exactly a string "
                "source_trajectory_id, string interaction_segment_id, and object "
                f"{payload_key}"
            )
        key = (record["source_trajectory_id"], record["interaction_segment_id"])
        if key not in segment_keys:
            unmatched.add(key)
        elif key in bound:
            repeated.add(key)
        else:
            bound[key] = record[payload_key]
    if unmatched:
        raise PostmortemValidationError(
            f"{payload_key} records reference unknown interaction segments: "
            f"{sorted(unmatched)}"
        )
    if repeated:
        raise PostmortemValidationError(
            f"{payload_key} records repeat interaction segments: {sorted(repeated)}"
        )
    return bound


def read_json_records(path: Path) -> list[dict[str, Any]]:
    """Read one JSON object, a JSON array, or newline-delimited JSON records."""
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = [json.loads(line) for line in text.splitlines() if line.strip()]
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise PostmortemValidationError("record file must contain JSON objects")
