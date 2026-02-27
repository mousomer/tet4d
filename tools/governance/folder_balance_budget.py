from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_STATUS_ORDER = {
    "balanced": 0,
    "watch": 1,
    "skewed": 2,
    "rebalance_signal": 3,
}


def _require_dict(value: Any, *, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be a JSON object")
    return value


def _require_list(value: Any, *, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"{label} must be a JSON array")
    return value


def _folder_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    folder_balance = _require_dict(
        metrics.get("folder_balance"), label="folder_balance"
    )
    rows = _require_list(folder_balance.get("folders"), label="folder_balance.folders")
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(_require_dict(row, label="folder_balance.folders[*]"))
    return normalized


def folder_row_index(metrics: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("path")): row
        for row in _folder_rows(metrics)
        if isinstance(row.get("path"), str)
    }


def _status_order(gate_config: dict[str, Any]) -> dict[str, int]:
    raw = gate_config.get("status_order", DEFAULT_STATUS_ORDER)
    order = _require_dict(raw, label="status_order")
    parsed: dict[str, int] = {}
    for key, value in order.items():
        if not isinstance(key, str) or not isinstance(value, int):
            raise TypeError("status_order entries must be string->int")
        parsed[key] = value
    return parsed


def _tracked_leaf_folders(gate_config: dict[str, Any]) -> list[dict[str, Any]]:
    raw = gate_config.get("tracked_leaf_folders", [])
    tracked = _require_list(raw, label="tracked_leaf_folders")
    out: list[dict[str, Any]] = []
    for item in tracked:
        out.append(_require_dict(item, label="tracked_leaf_folders[*]"))
    return out


def _status_regression_reason(
    *,
    current_status: Any,
    baseline_status: Any,
    order: dict[str, int],
) -> str | None:
    if not isinstance(current_status, str):
        return "missing current fuzzy_weighted_status"
    if not isinstance(baseline_status, str):
        return "missing baseline_status"
    if current_status not in order:
        return f"unknown current status {current_status!r}"
    if baseline_status not in order:
        return f"unknown baseline status {baseline_status!r}"
    if order[current_status] > order[baseline_status]:
        return f"status worsened ({current_status} > {baseline_status})"
    return None


def _score_regression_reason(
    *,
    current_score_raw: Any,
    baseline_score_raw: Any,
    epsilon: float,
) -> str | None:
    try:
        current_score = float(current_score_raw)
    except (TypeError, ValueError):
        return "missing current fuzzy_weighted_score"
    try:
        baseline_score = float(baseline_score_raw)
    except (TypeError, ValueError):
        return "missing baseline_score"
    if current_score < (baseline_score - epsilon):
        return f"score regressed ({current_score:.2f} < {baseline_score:.2f} - epsilon {epsilon:.2f})"
    return None


def _tracked_folder_current_state(row: dict[str, Any] | None) -> tuple[Any, Any]:
    if not row:
        return None, None
    balancer = row.get("balancer")
    if not isinstance(balancer, dict):
        return None, None
    return balancer.get("fuzzy_weighted_score"), balancer.get("fuzzy_weighted_status")


def _evaluate_tracked_folder(
    *,
    tracked: dict[str, Any],
    row: dict[str, Any] | None,
    epsilon: float,
    order: dict[str, int],
) -> list[str]:
    reasons: list[str] = []
    if row is None:
        return ["folder missing from folder_balance.folders"]

    if not bool(row.get("leaf_folder")):
        reasons.append("folder is not a leaf_folder")
    expected_profile = tracked.get("profile")
    actual_profile = row.get("folder_profile")
    if expected_profile != actual_profile:
        reasons.append(f"profile mismatch ({actual_profile!r} != {expected_profile!r})")

    balancer = row.get("balancer")
    if not isinstance(balancer, dict):
        reasons.append("missing balancer object")
        return reasons

    status_reason = _status_regression_reason(
        current_status=balancer.get("fuzzy_weighted_status"),
        baseline_status=tracked.get("baseline_status"),
        order=order,
    )
    if status_reason:
        reasons.append(status_reason)

    score_reason = _score_regression_reason(
        current_score_raw=balancer.get("fuzzy_weighted_score"),
        baseline_score_raw=tracked.get("baseline_score"),
        epsilon=epsilon,
    )
    if score_reason:
        reasons.append(score_reason)
    return reasons


def evaluate_folder_balance_gate(
    metrics: dict[str, Any], gate_config: dict[str, Any]
) -> list[str]:
    violations: list[str] = []
    index = folder_row_index(metrics)
    epsilon = float(gate_config.get("score_epsilon", 0.0))
    order = _status_order(gate_config)

    for tracked in _tracked_leaf_folders(gate_config):
        path = tracked.get("path")
        if not isinstance(path, str) or not path:
            violations.append("tracked_leaf_folders entry has invalid path")
            continue

        row = index.get(path)
        reasons = _evaluate_tracked_folder(
            tracked=tracked, row=row, epsilon=epsilon, order=order
        )
        if not reasons:
            continue
        current_score, current_status = _tracked_folder_current_state(row)
        violations.append(
            f"folder_balance_gate[{path}] baseline(score={tracked.get('baseline_score')}, "
            f"status={tracked.get('baseline_status')}) current(score={current_score}, "
            f"status={current_status}): " + "; ".join(reasons)
        )

    return violations


def refresh_folder_balance_budgets(
    metrics: dict[str, Any], gate_config: dict[str, Any]
) -> dict[str, Any]:
    updated = deepcopy(gate_config)
    index = folder_row_index(metrics)
    tracked = _tracked_leaf_folders(updated)
    for item in tracked:
        path = item.get("path")
        if not isinstance(path, str) or not path:
            raise ValueError("tracked_leaf_folders entry has invalid path")
        row = index.get(path)
        if row is None:
            raise ValueError(f"tracked folder not found: {path}")
        if not bool(row.get("leaf_folder")):
            raise ValueError(f"tracked folder is not a leaf folder: {path}")
        expected_profile = item.get("profile")
        actual_profile = row.get("folder_profile")
        if expected_profile != actual_profile:
            raise ValueError(
                f"tracked folder profile mismatch for {path}: {actual_profile!r} != {expected_profile!r}"
            )
        balancer = _require_dict(row.get("balancer"), label=f"{path}.balancer")
        item["baseline_score"] = float(balancer["fuzzy_weighted_score"])
        item["baseline_status"] = str(balancer["fuzzy_weighted_status"])
    updated["tracked_leaf_folders"] = tracked
    return updated
