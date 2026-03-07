from __future__ import annotations

from collections.abc import Mapping

from .schema import TutorialCompletionCondition


def evaluate_completion(
    condition: TutorialCompletionCondition,
    *,
    events_seen: Mapping[str, int],
    predicate_values: Mapping[str, bool] | None = None,
    event_first_seen_ms: Mapping[str, int] | None = None,
    event_last_seen_ms: Mapping[str, int] | None = None,
) -> bool:
    predicate_state = predicate_values or {}
    first_seen = event_first_seen_ms or {}
    last_seen = event_last_seen_ms or {}
    checks: list[bool] = []
    event_required = max(1, int(condition.event_count_required))
    event_span_required = max(0, int(condition.event_span_min_ms))
    for event_name in condition.events:
        count_ok = int(events_seen.get(event_name, 0)) >= event_required
        span_ok = True
        if event_span_required > 0:
            start_ms = first_seen.get(event_name)
            end_ms = last_seen.get(event_name)
            span_ok = (
                isinstance(start_ms, int)
                and isinstance(end_ms, int)
                and (end_ms - start_ms) >= event_span_required
            )
        checks.append(count_ok and span_ok)
    for predicate_name in condition.predicates:
        checks.append(bool(predicate_state.get(predicate_name, False)))
    if not checks:
        return False
    if condition.logic == "all":
        return all(checks)
    return any(checks)
