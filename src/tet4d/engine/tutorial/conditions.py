from __future__ import annotations

from collections.abc import Mapping

from .schema import TutorialCompletionCondition


def evaluate_completion(
    condition: TutorialCompletionCondition,
    *,
    events_seen: Mapping[str, int],
    predicate_values: Mapping[str, bool] | None = None,
) -> bool:
    predicate_state = predicate_values or {}
    checks: list[bool] = []
    for event_name in condition.events:
        checks.append(int(events_seen.get(event_name, 0)) > 0)
    for predicate_name in condition.predicates:
        checks.append(bool(predicate_state.get(predicate_name, False)))
    if not checks:
        return False
    if condition.logic == "all":
        return all(checks)
    return any(checks)
