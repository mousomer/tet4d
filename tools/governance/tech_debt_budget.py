from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_STATUS_ORDER = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "critical": 3,
}
DEFAULT_GATE_MODE = "strict_stage_decrease"


def _require_dict(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    return value


def _status_order(gate_config: dict[str, Any]) -> dict[str, int]:
    raw = gate_config.get("status_order", DEFAULT_STATUS_ORDER)
    order = _require_dict(raw, label="status_order")
    parsed: dict[str, int] = {}
    for key, value in order.items():
        if not isinstance(key, str) or not isinstance(value, int):
            raise TypeError("status_order entries must be string->int")
        parsed[key] = value
    return parsed


def _gate_mode(gate_config: dict[str, Any]) -> str:
    mode = gate_config.get("gate_mode", DEFAULT_GATE_MODE)
    if not isinstance(mode, str) or not mode.strip():
        raise TypeError("gate_mode must be a non-empty string")
    normalized = mode.strip()
    if normalized not in {"strict_stage_decrease", "non_regression_baseline"}:
        raise ValueError(f"unsupported gate_mode: {normalized}")
    return normalized


def _current_state(
    metrics: dict[str, Any],
) -> tuple[int | None, float | None, str | None]:
    stage_raw = metrics.get("arch_stage")
    stage = stage_raw if isinstance(stage_raw, int) else None
    tech_debt = metrics.get("tech_debt")
    if not isinstance(tech_debt, dict):
        return stage, None, None
    score_raw = tech_debt.get("score")
    status_raw = tech_debt.get("status")
    try:
        score = float(score_raw)
    except (TypeError, ValueError):
        score = None
    status = status_raw if isinstance(status_raw, str) else None
    return stage, score, status


def _baseline_state(gate_config: dict[str, Any]) -> tuple[int, float, str]:
    baseline = _require_dict(gate_config.get("baseline"), label="baseline")
    baseline_stage_raw = baseline.get("arch_stage")
    baseline_score_raw = baseline.get("score")
    baseline_status = baseline.get("status")
    if not isinstance(baseline_stage_raw, int):
        raise TypeError("baseline.arch_stage must be an int")
    try:
        baseline_score = float(baseline_score_raw)
    except (TypeError, ValueError) as exc:
        raise TypeError("baseline.score must be numeric") from exc
    if not isinstance(baseline_status, str):
        raise TypeError("baseline.status must be a string")
    return baseline_stage_raw, baseline_score, baseline_status


def _missing_state_violations(
    stage: int | None,
    score: float | None,
    status: str | None,
) -> list[str]:
    violations: list[str] = []
    if stage is None:
        violations.append("missing arch_stage")
    if score is None:
        violations.append("missing tech_debt.score")
    if status is None:
        violations.append("missing tech_debt.status")
    return violations


def _status_violations(
    *,
    current_status: str,
    baseline_status: str,
    order: dict[str, int],
) -> list[str]:
    violations: list[str] = []
    if current_status not in order:
        violations.append(f"unknown current status {current_status!r}")
    if baseline_status not in order:
        violations.append(f"unknown baseline status {baseline_status!r}")
    if violations:
        return violations
    if order[current_status] > order[baseline_status]:
        violations.append(f"status worsened ({current_status} > {baseline_status})")
    return violations


def _score_violations(
    *,
    mode: str,
    stage: int,
    current_score: float,
    baseline_stage: int,
    baseline_score: float,
    epsilon: float,
) -> list[str]:
    if mode == "non_regression_baseline":
        ceiling = baseline_score + epsilon
        if current_score > ceiling:
            return [
                "score regressed above baseline ceiling "
                f"({current_score:.2f} > {baseline_score:.2f} + epsilon {epsilon:.2f})"
            ]
        return []

    if stage > baseline_stage:
        threshold = baseline_score - epsilon
        if current_score >= threshold:
            return [
                "score must strictly decrease for stage advance "
                f"({current_score:.2f} >= {baseline_score:.2f} - epsilon {epsilon:.2f})"
            ]
        return []
    ceiling = baseline_score + epsilon
    if current_score > ceiling:
        return [
            "score regressed within baseline stage "
            f"({current_score:.2f} > {baseline_score:.2f} + epsilon {epsilon:.2f})"
        ]
    return []


def evaluate_tech_debt_gate(
    metrics: dict[str, Any], gate_config: dict[str, Any]
) -> list[str]:
    baseline_stage, baseline_score, baseline_status = _baseline_state(gate_config)

    stage, score, status = _current_state(metrics)
    mode = _gate_mode(gate_config)
    epsilon = float(gate_config.get("score_epsilon", 0.0))
    order = _status_order(gate_config)
    violations = _missing_state_violations(stage, score, status)
    if violations:
        return violations

    assert stage is not None
    assert score is not None
    assert status is not None

    if stage < baseline_stage:
        violations.append(f"arch_stage regressed ({stage} < baseline {baseline_stage})")
    if violations:
        return violations

    violations.extend(
        _status_violations(
            current_status=status,
            baseline_status=baseline_status,
            order=order,
        )
    )
    if violations:
        return violations

    violations.extend(
        _score_violations(
            mode=mode,
            stage=stage,
            current_score=score,
            baseline_stage=baseline_stage,
            baseline_score=baseline_score,
            epsilon=epsilon,
        )
    )
    return violations


def refresh_tech_debt_budgets(
    metrics: dict[str, Any], gate_config: dict[str, Any]
) -> dict[str, Any]:
    stage, score, status = _current_state(metrics)
    if stage is None:
        raise ValueError("metrics missing arch_stage")
    if score is None or status is None:
        raise ValueError("metrics missing tech_debt score/status")
    updated = deepcopy(gate_config)
    baseline = _require_dict(updated.get("baseline", {}), label="baseline")
    baseline["arch_stage"] = stage
    baseline["score"] = round(float(score), 2)
    baseline["status"] = status
    updated["baseline"] = baseline
    return updated
