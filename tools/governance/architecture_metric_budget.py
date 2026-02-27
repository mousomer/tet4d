from __future__ import annotations

from typing import Any


ARCHITECTURE_METRIC_BUDGETS = {
    "engine_core_purity.violation_count": 0,
    "deep_imports.engine_core_to_engine_non_core_imports.count": 0,
    "deep_imports.ui_to_engine_non_api.count": 0,
    "deep_imports.replay_to_engine_non_api.count": 0,
    "deep_imports.ai_to_engine_non_api.count": 0,
    "deep_imports.tools_stability_to_engine_non_api.count": 0,
    "deep_imports.tools_benchmarks_to_engine_non_api.count": 0,
    "deep_imports.external_callers_to_engine_playbot.count": 0,
    "migration_debt_signals.core_step_state_method_calls.count": 0,
    "migration_debt_signals.core_step_private_state_method_calls.count": 0,
    "migration_debt_signals.core_step_state_field_assignments.count": 0,
    "migration_debt_signals.core_rules_private_state_method_calls.count": 0,
    "migration_debt_signals.pygame_imports_non_test.count": 39,
    "migration_debt_signals.file_io_calls_non_test.count": 16,
    "migration_debt_signals.random_imports_non_test.count": 11,
    "migration_debt_signals.time_imports_non_test.count": 3,
}


def _metric_int(metrics: dict[str, Any], metric_path: str) -> int:
    node: Any = metrics
    for part in metric_path.split("."):
        if not isinstance(node, dict):
            raise TypeError(f"{metric_path} does not resolve to a dict node")
        node = node.get(part)
    if not isinstance(node, int):
        raise TypeError(f"{metric_path} is not an int: {node!r}")
    return node


def evaluate_architecture_metric_budget_overages(
    metrics: dict[str, Any],
    *,
    budgets: dict[str, int] | None = None,
) -> list[str]:
    selected = budgets if budgets is not None else ARCHITECTURE_METRIC_BUDGETS
    violations: list[str] = []
    for metric_path, budget in selected.items():
        value = _metric_int(metrics, metric_path)
        if value > int(budget):
            violations.append(f"{metric_path}: {value} > budget {budget}")
    return violations

