#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_SRC_ROOT = REPO_ROOT / "src/tet4d"
SRC_LAYOUT_ROOT = REPO_ROOT / "src"
FOLDER_BALANCE_BUDGETS_PATH = REPO_ROOT / "config/project/folder_balance_budgets.json"
TECH_DEBT_BUDGETS_PATH = REPO_ROOT / "config/project/tech_debt_budgets.json"
BACKLOG_PATH = REPO_ROOT / "docs/BACKLOG.md"
MENU_STRUCTURE_PATH = REPO_ROOT / "config/menu/structure.json"
ARCH_METRICS_CONFIG_PATH = REPO_ROOT / "config/project/architecture_metrics.json"
POLICY_KIT_DIR = Path(__import__("os").environ.get("POLICY_KIT_DIR", str(Path.home() / "workspace/policy-kit")))
OPTIONAL_ARCH_METRICS_PATH = POLICY_KIT_DIR / "optional/architecture_metrics"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SRC_LAYOUT_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_LAYOUT_ROOT))
if OPTIONAL_ARCH_METRICS_PATH.exists() and str(OPTIONAL_ARCH_METRICS_PATH) not in sys.path:
    sys.path.insert(0, str(OPTIONAL_ARCH_METRICS_PATH))

from tools.governance.architecture_metric_budget import (  # noqa: E402
    evaluate_architecture_metric_budget_overages,
)
from tools.governance.folder_balance_budget import evaluate_folder_balance_gate  # noqa: E402

from architecture_metrics import classify_folder_path  # noqa: E402
from architecture_metrics import fuzzy_band_score as shared_fuzzy_band_score  # noqa: E402
from architecture_metrics import fuzzy_weighted_status as shared_fuzzy_weighted_status  # noqa: E402

# Folder-balance heuristic mirrors the documented architecture-contract guidance.
FOLDER_BALANCE_TARGET_FILES_MIN = 6
FOLDER_BALANCE_TARGET_FILES_MAX = 15
FOLDER_BALANCE_SPLIT_SIGNAL_FILES_GT = 20
FOLDER_BALANCE_TOO_SMALL_FILES_MAX = 3
FOLDER_BALANCE_FILES_SOFT_MIN = 2
FOLDER_BALANCE_FILES_SOFT_MAX = 28
FOLDER_BALANCE_FILES_TARGET_MARGIN = 1

# LOC heuristics are intentionally broad and fuzzy. They guide refactor triage and are
# not used as strict CI budgets.
FOLDER_BALANCE_TARGET_LOC_PER_FILE_MIN = 40
FOLDER_BALANCE_TARGET_LOC_PER_FILE_MAX = 220
FOLDER_BALANCE_LOC_PER_FILE_SOFT_MIN = 10
FOLDER_BALANCE_LOC_PER_FILE_SOFT_MAX = 420
FOLDER_BALANCE_LOC_PER_FILE_TARGET_MARGIN = 20

FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN = 250
FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX = 2500
FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN = 40
FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX = 8000
FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN = 250

TESTS_FOLDER_BALANCE_TARGET_FILES_MIN = 2
TESTS_FOLDER_BALANCE_TARGET_FILES_MAX = 80
TESTS_FOLDER_BALANCE_FILES_SOFT_MIN = 1
TESTS_FOLDER_BALANCE_FILES_SOFT_MAX = 180
TESTS_FOLDER_BALANCE_FILES_TARGET_MARGIN = 8

TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN = 80
TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX = 15000
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN = 1
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX = 50000
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN = 1200

FOLDER_BALANCE_WEIGHT_FILES = 0.5
FOLDER_BALANCE_WEIGHT_LOC_PER_FILE = 0.3
FOLDER_BALANCE_WEIGHT_LOC_PER_FOLDER = 0.2

TECH_DEBT_STATUS_ORDER = {
    "low": 0,
    "moderate": 1,
    "high": 2,
    "critical": 3,
}
ARCH_STAGE = 534


def _py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        p
        for p in sorted(root.rglob("*.py"))
        if ".git" not in p.parts and ".venv" not in p.parts and "__pycache__" not in p.parts
    ]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _python_loc(path: Path) -> int:
    count = 0
    for line in _read(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        count += 1
    return count


def _match_lines(paths: list[Path], pattern: str) -> list[str]:
    rx = re.compile(pattern)
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def _match_engine_deep_import_lines(paths: list[Path]) -> list[str]:
    rx = re.compile(r"^\s*(?:from|import)\s+tet4d\.engine(?:\.|\b)")
    allow_rx = re.compile(
        r"^\s*(?:from|import)\s+tet4d\.engine\.api(?:\.|\b)|^\s*from\s+tet4d\.engine\s+import\s+api(?:\s|,|$)"
    )
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line) and not allow_rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def _match_core_to_non_core_engine_imports(paths: list[Path]) -> list[str]:
    rx = re.compile(r"^\s*(?:from|import)\s+tet4d\.engine(?:\.|\b)")
    allow_rx = re.compile(
        r"^\s*(?:from|import)\s+tet4d\.engine\.core(?:\.|\b)|^\s*from\s+tet4d\.engine\s+import\s+core(?:\s|,|$)"
    )
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line) and not allow_rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def _classify_folder_balance(file_count: int) -> str:
    if file_count > FOLDER_BALANCE_SPLIT_SIGNAL_FILES_GT:
        return "split_signal"
    if file_count > FOLDER_BALANCE_TARGET_FILES_MAX:
        return "large"
    if file_count < FOLDER_BALANCE_TARGET_FILES_MIN:
        if file_count <= FOLDER_BALANCE_TOO_SMALL_FILES_MAX:
            return "too_small"
        return "small"
    return "balanced"


def _round2(value: float) -> float:
    return round(value, 2)


def _clamp01(value: float) -> float:
    if value <= 0:
        return 0.0
    if value >= 1:
        return 1.0
    return value


def _fuzzy_band_score(
    *,
    value: float,
    target_min: float,
    target_max: float,
    soft_min: float,
    soft_max: float,
    target_margin: float = 0.0,
) -> float:
    return shared_fuzzy_band_score(
        value=value,
        target_min=target_min,
        target_max=target_max,
        soft_min=soft_min,
        soft_max=soft_max,
        target_margin=target_margin,
    )


def _fuzzy_weighted_status(score: float) -> str:
    return shared_fuzzy_weighted_status(score)


def _folder_balance_profiles() -> dict[str, dict[str, Any]]:
    common_weights = {
        "py_files": FOLDER_BALANCE_WEIGHT_FILES,
        "avg_loc_per_file": FOLDER_BALANCE_WEIGHT_LOC_PER_FILE,
        "py_loc_total": FOLDER_BALANCE_WEIGHT_LOC_PER_FOLDER,
    }
    return {
        "default_leaf": {
            "py_files": {
                "target_band": [FOLDER_BALANCE_TARGET_FILES_MIN, FOLDER_BALANCE_TARGET_FILES_MAX],
                "soft_band": [FOLDER_BALANCE_FILES_SOFT_MIN, FOLDER_BALANCE_FILES_SOFT_MAX],
                "target_margin": FOLDER_BALANCE_FILES_TARGET_MARGIN,
            },
            "avg_loc_per_file": {
                "target_band": [FOLDER_BALANCE_TARGET_LOC_PER_FILE_MIN, FOLDER_BALANCE_TARGET_LOC_PER_FILE_MAX],
                "soft_band": [FOLDER_BALANCE_LOC_PER_FILE_SOFT_MIN, FOLDER_BALANCE_LOC_PER_FILE_SOFT_MAX],
                "target_margin": FOLDER_BALANCE_LOC_PER_FILE_TARGET_MARGIN,
            },
            "py_loc_total": {
                "target_band": [FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN, FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX],
                "soft_band": [FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN, FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX],
                "target_margin": FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN,
            },
            "weights": common_weights,
        },
        "tests_leaf": {
            "py_files": {
                "target_band": [TESTS_FOLDER_BALANCE_TARGET_FILES_MIN, TESTS_FOLDER_BALANCE_TARGET_FILES_MAX],
                "soft_band": [TESTS_FOLDER_BALANCE_FILES_SOFT_MIN, TESTS_FOLDER_BALANCE_FILES_SOFT_MAX],
                "target_margin": TESTS_FOLDER_BALANCE_FILES_TARGET_MARGIN,
            },
            "avg_loc_per_file": {
                "target_band": [10, 420],
                "soft_band": [1, 1000],
                "target_margin": 60,
            },
            "py_loc_total": {
                "target_band": [TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN, TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX],
                "soft_band": [TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN, TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX],
                "target_margin": TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN,
            },
            "weights": common_weights,
        },
    }


def _folder_balance_profile_for_folder(folder_path: str, *, leaf_folder: bool) -> str | None:
    if not leaf_folder:
        return None
    parts = folder_path.split("/")
    return "tests_leaf" if "tests" in parts else "default_leaf"


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _folder_balance_gate_config() -> dict[str, Any] | None:
    return _read_json_if_exists(FOLDER_BALANCE_BUDGETS_PATH)


def _tech_debt_gate_config() -> dict[str, Any] | None:
    return _read_json_if_exists(TECH_DEBT_BUDGETS_PATH)


def _architecture_metrics_config() -> dict[str, Any]:
    data = _read_json_if_exists(ARCH_METRICS_CONFIG_PATH)
    return data if isinstance(data, dict) else {}


def _metric_source_roots() -> list[Path]:
    cfg = _architecture_metrics_config()
    raw = cfg.get("source_roots", ["src/tet4d", "tests", "tools", "scripts"])
    roots: list[Path] = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, str) and item.strip():
                roots.append(REPO_ROOT / item.strip())
    return roots if roots else [TARGET_SRC_ROOT]


def _folder_policy_context(gate_config: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, bool], dict[str, bool], dict[str, dict[str, Any]]]:
    cfg = _architecture_metrics_config()
    class_cfg = cfg.get("classification", {}) if isinstance(cfg.get("classification"), dict) else {}
    class_gate = cfg.get("class_gate_eligibility", {}) if isinstance(cfg.get("class_gate_eligibility"), dict) else {}
    gate_overrides_raw = class_cfg.get("gate_overrides", {}) if isinstance(class_cfg.get("gate_overrides"), dict) else {}

    defaults = {"code_default": True, "tests_lenient": True, "non_code_exempt": False}
    for key, value in class_gate.items():
        if isinstance(key, str) and isinstance(value, bool):
            defaults[key] = value

    gate_overrides: dict[str, bool] = {}
    for key, value in gate_overrides_raw.items():
        if isinstance(key, str) and isinstance(value, bool):
            gate_overrides[key] = value

    tracked_cfg: dict[str, dict[str, Any]] = {}
    tracked = gate_config.get("tracked_leaf_folders", []) if isinstance(gate_config, dict) else []
    if isinstance(tracked, list):
        for item in tracked:
            if isinstance(item, dict) and isinstance(item.get("path"), str):
                tracked_cfg[item["path"]] = item

    return class_cfg, defaults, gate_overrides, tracked_cfg


def _apply_folder_policy_row(
    row: dict[str, Any],
    *,
    class_cfg: dict[str, Any],
    defaults: dict[str, bool],
    gate_overrides: dict[str, bool],
    tracked_cfg: dict[str, dict[str, Any]],
) -> bool:
    path = str(row.get("path", ""))
    folder_class = classify_folder_path(path, class_cfg)
    if folder_class == "tests_lenient":
        row["folder_profile"] = "tests_leaf"
    elif folder_class == "non_code_exempt":
        row["folder_profile"] = "non_code_exempt"

    gate_eligible = bool(defaults.get(folder_class, True))
    if path in gate_overrides:
        gate_eligible = gate_overrides[path]
    tracked_item = tracked_cfg.get(path, {})
    if bool(tracked_item.get("allow_non_code", False)):
        gate_eligible = True

    row["folder_class"] = folder_class
    row["gate_eligible"] = gate_eligible
    row["exclude_from_code_balance"] = not gate_eligible
    return bool(row.get("leaf_folder")) and gate_eligible


def _update_folder_policy_summary(summary: dict[str, Any], folder_class_counts: dict[str, int], eligible_leaf_rows: list[dict[str, Any]]) -> None:
    summary["folder_class_counts"] = folder_class_counts
    summary["gate_eligible_leaf_folder_count"] = len(eligible_leaf_rows)
    summary["gate_eligible_leaf_python_file_count"] = sum(int(r.get("py_files", 0)) for r in eligible_leaf_rows)
    summary["gate_eligible_leaf_python_loc_total"] = sum(int(r.get("py_loc_total", 0)) for r in eligible_leaf_rows)
    if eligible_leaf_rows:
        summary["gate_eligible_leaf_fuzzy_weighted_balance_score_avg"] = _round2(
            sum(float(r.get("balancer", {}).get("fuzzy_weighted_score", 0.0)) for r in eligible_leaf_rows)
            / len(eligible_leaf_rows)
        )
    else:
        summary["gate_eligible_leaf_fuzzy_weighted_balance_score_avg"] = 0.0


def _filter_rebalance_priority(balancer: dict[str, Any], row_index: dict[str, dict[str, Any]]) -> None:
    rebalance = balancer.get("rebalance_priority_folders", [])
    if not isinstance(rebalance, list):
        return
    balancer["rebalance_priority_folders"] = [
        item
        for item in rebalance
        if isinstance(item, dict) and bool(row_index.get(str(item.get("path", "")), {}).get("gate_eligible", False))
    ]


def _annotate_tracked_gate_rows(gate: dict[str, Any], row_index: dict[str, dict[str, Any]]) -> None:
    tracked_rows = gate.get("tracked_folders", [])
    if not isinstance(tracked_rows, list):
        return
    for item in tracked_rows:
        if not isinstance(item, dict):
            continue
        row = row_index.get(str(item.get("path", "")))
        if row is None:
            continue
        item["folder_class"] = row.get("folder_class")
        item["gate_eligible"] = row.get("gate_eligible")


def _apply_folder_class_policy(balance: dict[str, Any], gate_config: dict[str, Any] | None) -> dict[str, Any]:
    rows = balance.get("folders", [])
    if not isinstance(rows, list):
        return balance

    class_cfg, defaults, gate_overrides, tracked_cfg = _folder_policy_context(gate_config)

    folder_class_counts: dict[str, int] = {}
    eligible_leaf_rows: list[dict[str, Any]] = []
    row_index: dict[str, dict[str, Any]] = {}

    for row in rows:
        if not isinstance(row, dict):
            continue
        is_eligible_leaf = _apply_folder_policy_row(
            row,
            class_cfg=class_cfg,
            defaults=defaults,
            gate_overrides=gate_overrides,
            tracked_cfg=tracked_cfg,
        )
        folder_class = str(row.get("folder_class", "code_default"))
        folder_class_counts[folder_class] = folder_class_counts.get(folder_class, 0) + 1
        path = str(row.get("path", ""))
        row_index[path] = row
        if is_eligible_leaf:
            eligible_leaf_rows.append(row)

    summary = balance.get("summary", {})
    if isinstance(summary, dict):
        _update_folder_policy_summary(summary, folder_class_counts, eligible_leaf_rows)

    balancer = balance.get("balancer", {})
    if isinstance(balancer, dict):
        _filter_rebalance_priority(balancer, row_index)

    gate = balance.get("gate", {})
    if isinstance(gate, dict):
        _annotate_tracked_gate_rows(gate, row_index)

    return balance


def _active_backlog_rows(backlog_text: str) -> list[tuple[str, str, str]]:
    section_match = re.search(
        r"^## 3\. Active Open Backlog / TODO.*?(?=^## |\Z)",
        backlog_text,
        flags=re.MULTILINE | re.DOTALL,
    )
    if section_match is None:
        return []
    section = section_match.group(0)
    item_rx = re.compile(
        r"^\d+\.\s+`?\[(P[1-3])\]\[(BKL-[A-Z0-9-]+)\]\s+(.+?)`?\s*$",
        flags=re.MULTILINE,
    )
    return [(match.group(1), match.group(2), match.group(3)) for match in item_rx.finditer(section)]


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _tech_debt_scoring_config(tech_debt_cfg: dict[str, Any]) -> dict[str, Any]:
    scoring_cfg = _as_dict(tech_debt_cfg.get("scoring"))
    weight_cfg = _as_dict(scoring_cfg.get("component_weights"))
    priority_weight_cfg = _as_dict(scoring_cfg.get("priority_weights"))
    normalization_cfg = _as_dict(scoring_cfg.get("normalization"))
    raw_bug_keywords = scoring_cfg.get("bug_keywords", [])
    if not isinstance(raw_bug_keywords, list):
        raw_bug_keywords = []

    component_weights = {
        "backlog_priority": float(weight_cfg.get("backlog_priority", 0.27)),
        "backlog_bug": float(weight_cfg.get("backlog_bug", 0.16)),
        "ci_gate": float(weight_cfg.get("ci_gate", 0.2)),
        "code_balance": float(weight_cfg.get("code_balance", 0.12)),
        "keybinding_retention": float(weight_cfg.get("keybinding_retention", 0.2)),
        "menu_simplification": float(weight_cfg.get("menu_simplification", 0.05)),
    }
    weight_total = sum(component_weights.values())
    if weight_total <= 0:
        raise ValueError("tech debt component weights must sum to > 0")
    normalized_component_weights = {
        key: value / weight_total for key, value in component_weights.items()
    }
    priority_weights = {
        "P1": float(priority_weight_cfg.get("P1", 5.0)),
        "P2": float(priority_weight_cfg.get("P2", 3.0)),
        "P3": float(priority_weight_cfg.get("P3", 1.0)),
    }
    priority_points_cap = float(normalization_cfg.get("priority_points_cap", 40.0))
    bug_items_cap = float(normalization_cfg.get("bug_items_cap", 6.0))
    ci_issue_cap = float(normalization_cfg.get("ci_issue_cap", 6.0))
    if priority_points_cap <= 0 or bug_items_cap <= 0 or ci_issue_cap <= 0:
        raise ValueError("tech debt normalization caps must be > 0")
    bug_keywords = [
        token.strip().lower() for token in raw_bug_keywords if isinstance(token, str) and token.strip()
    ]
    return {
        "component_weights": normalized_component_weights,
        "priority_weights": priority_weights,
        "priority_points_cap": priority_points_cap,
        "bug_items_cap": bug_items_cap,
        "ci_issue_cap": ci_issue_cap,
        "bug_keywords": bug_keywords,
    }


def _active_backlog_debt_stats(
    *,
    backlog_rows: list[tuple[str, str, str]],
    priority_weights: dict[str, float],
    bug_keywords: list[str],
) -> dict[str, Any]:
    backlog_priority_counts = {"P1": 0, "P2": 0, "P3": 0}
    weighted_priority_points = 0.0
    bug_rows: list[dict[str, str]] = []
    for priority, issue_id, title in backlog_rows:
        backlog_priority_counts[priority] = backlog_priority_counts.get(priority, 0) + 1
        weighted_priority_points += priority_weights.get(priority, 0.0)
        lowered_title = title.lower()
        if any(keyword in lowered_title for keyword in bug_keywords):
            bug_rows.append({"priority": priority, "id": issue_id, "title": title})
    return {
        "priority_counts": backlog_priority_counts,
        "weighted_priority_points": weighted_priority_points,
        "bug_rows": bug_rows,
    }


def _ci_gate_violations(metrics: dict[str, Any]) -> tuple[list[str], list[str]]:
    folder_gate_cfg = _folder_balance_gate_config()
    folder_gate_violations = (
        evaluate_folder_balance_gate(metrics, folder_gate_cfg)
        if isinstance(folder_gate_cfg, dict)
        else []
    )
    budget_violations = evaluate_architecture_metric_budget_overages(metrics)
    return budget_violations, folder_gate_violations


def _tech_debt_status(score: float) -> str:
    if score <= 25:
        return "low"
    if score <= 50:
        return "moderate"
    if score <= 75:
        return "high"
    return "critical"


def _normalized_status_order(tech_debt_cfg: dict[str, Any]) -> dict[str, int]:
    raw = tech_debt_cfg.get("status_order", TECH_DEBT_STATUS_ORDER)
    status_order = raw if isinstance(raw, dict) else TECH_DEBT_STATUS_ORDER
    normalized: dict[str, int] = {}
    for key, value in status_order.items():
        if isinstance(key, str) and isinstance(value, int):
            normalized[key] = value
    return normalized if normalized else dict(TECH_DEBT_STATUS_ORDER)


def _expected_keybinding_scope_bindings(
    scope: str, runtime_binding_groups_for_dimension: Any
) -> set[tuple[int, str, str]]:
    expected: set[tuple[int, str, str]] = set()
    if scope == "general":
        for action in runtime_binding_groups_for_dimension(2).get("system", {}):
            expected.add((2, "system", action))
        return expected
    if scope == "all":
        for action in runtime_binding_groups_for_dimension(2).get("system", {}):
            expected.add((2, "system", action))
        for dimension in (2, 3, 4):
            groups = runtime_binding_groups_for_dimension(dimension)
            for group in ("game", "camera"):
                for action in groups.get(group, {}):
                    expected.add((dimension, group, action))
        return expected
    dimension = int(scope[0])
    groups = runtime_binding_groups_for_dimension(dimension)
    for group in ("game", "camera"):
        for action in groups.get(group, {}):
            expected.add((dimension, group, action))
    return expected


def _format_binding_triplet(entry: tuple[int, str, str]) -> dict[str, Any]:
    dimension, group, action = entry
    return {
        "dimension": dimension,
        "group": group,
        "action": action,
    }


def _purge_keybinding_retention_modules() -> None:
    import sys

    module_names = (
        "tet4d.ui.pygame.keybindings",
        "tet4d.ui.pygame.menu.keybindings_menu_model",
        "tet4d.ui.pygame.input.keybindings_defaults",
        "tet4d.ui.pygame.input.key_display",
    )
    for module_name in module_names:
        sys.modules.pop(module_name, None)


def _install_pygame_stub() -> None:
    import sys
    import types

    existing = sys.modules.get("pygame")
    if existing is not None:
        return

    key_name_by_code: dict[int, str] = {}
    key_code_by_name: dict[str, int] = {}
    next_code = 1000

    def _code_for_name(name: str) -> int:
        nonlocal next_code
        if name in key_code_by_name:
            return key_code_by_name[name]
        value = next_code
        next_code += 1
        key_code_by_name[name] = value
        key_name_by_code[value] = name
        return value

    def _key_name(value: int) -> str:
        return key_name_by_code.get(int(value), str(value))

    def _key_code(token: str) -> int:
        normalized = token.strip().lower()
        if not normalized:
            raise ValueError("empty key token")
        return _code_for_name(normalized)

    key_module = types.ModuleType("pygame.key")
    key_module.name = _key_name  # type: ignore[attr-defined]
    key_module.key_code = _key_code  # type: ignore[attr-defined]

    pygame_module = types.ModuleType("pygame")
    pygame_module.key = key_module  # type: ignore[attr-defined]
    pygame_module.SRCALPHA = 1  # type: ignore[attr-defined]
    pygame_module.init = lambda: None  # type: ignore[attr-defined]
    pygame_module.quit = lambda: None  # type: ignore[attr-defined]

    def _pygame_getattr(name: str) -> Any:
        if name.startswith("K_"):
            return _code_for_name(name.lower())
        raise AttributeError(name)

    pygame_module.__getattr__ = _pygame_getattr  # type: ignore[attr-defined]

    sys.modules["pygame"] = pygame_module
    sys.modules["pygame.key"] = key_module


def _load_keybinding_retention_imports() -> tuple[Any, Any, str]:
    import contextlib
    import io
    import os

    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            from tet4d.ui.pygame.keybindings import runtime_binding_groups_for_dimension
            from tet4d.ui.pygame.menu.keybindings_menu_model import rows_for_scope
        except ModuleNotFoundError as exc:
            if exc.name != "pygame":
                raise
            _purge_keybinding_retention_modules()
            _install_pygame_stub()
            from tet4d.ui.pygame.keybindings import runtime_binding_groups_for_dimension
            from tet4d.ui.pygame.menu.keybindings_menu_model import rows_for_scope
            return runtime_binding_groups_for_dimension, rows_for_scope, "pygame_stub"
    return runtime_binding_groups_for_dimension, rows_for_scope, "pygame_runtime"


def _build_keybinding_retention_signal() -> dict[str, Any]:
    import contextlib
    import io

    goals_cfg = _as_dict(
        _as_dict(_architecture_metrics_config().get("long_term_goals")).get(
            "keybinding_retention"
        )
    )
    default_scopes = ("general", "2d", "3d", "4d", "all")
    raw_scopes = goals_cfg.get("required_scopes")
    scopes: tuple[str, ...] = default_scopes
    if isinstance(raw_scopes, list):
        parsed = tuple(
            item.strip().lower()
            for item in raw_scopes
            if isinstance(item, str) and item.strip()
        )
        if parsed:
            scopes = parsed
    target_pressure_max = float(goals_cfg.get("target_pressure_max", 0.0))

    try:
        (
            runtime_binding_groups_for_dimension,
            rows_for_scope,
            source,
        ) = _load_keybinding_retention_imports()
    except Exception as exc:  # pragma: no cover - environment/import guard
        return {
            "available": False,
            "pressure": 1.0,
            "status": "unavailable",
            "coverage_ratio": 0.0,
            "missing_count": 0,
            "unexpected_count": 0,
            "expected_count": 0,
            "error": f"{type(exc).__name__}: {exc}",
            "scopes": {},
            "source": "unavailable",
        }

    scope_rows: dict[str, Any] = {}
    expected_total = 0
    missing_total = 0
    unexpected_total = 0
    for scope in scopes:
        with contextlib.redirect_stdout(io.StringIO()):
            _, bindings = rows_for_scope(scope)
        rendered = {(row.dimension, row.group, row.action) for row in bindings}
        expected = _expected_keybinding_scope_bindings(
            scope, runtime_binding_groups_for_dimension
        )
        missing = sorted(expected - rendered)
        unexpected = sorted(rendered - expected)
        expected_total += len(expected)
        missing_total += len(missing)
        unexpected_total += len(unexpected)
        scope_rows[scope] = {
            "expected_count": len(expected),
            "rendered_count": len(rendered),
            "missing_count": len(missing),
            "unexpected_count": len(unexpected),
            "missing_sample": [_format_binding_triplet(item) for item in missing[:10]],
            "unexpected_sample": [
                _format_binding_triplet(item) for item in unexpected[:10]
            ],
        }

    retained = max(0, expected_total - missing_total)
    coverage_ratio = retained / expected_total if expected_total else 1.0
    drift_ratio = (
        (missing_total + unexpected_total) / expected_total if expected_total else 0.0
    )
    pressure = _clamp01(max(1.0 - coverage_ratio, drift_ratio))
    goal_met = pressure <= target_pressure_max
    if goal_met:
        status = "aligned"
    elif pressure <= 0.2:
        status = "watch"
    elif pressure <= 0.5:
        status = "degraded"
    else:
        status = "broken"

    return {
        "available": True,
        "pressure": _round2(pressure),
        "status": status,
        "goal_target_pressure_max": _round2(target_pressure_max),
        "goal_met": goal_met,
        "coverage_ratio": _round2(coverage_ratio),
        "expected_count": expected_total,
        "missing_count": missing_total,
        "unexpected_count": unexpected_total,
        "scopes": scope_rows,
        "source": source,
    }


def _menu_item_count(menus: dict[str, Any], menu_id: str) -> int:
    menu = menus.get(menu_id)
    if not isinstance(menu, dict):
        return 0
    items = menu.get("items")
    return len(items) if isinstance(items, list) else 0


def _build_menu_simplification_signal() -> dict[str, Any]:
    goals_cfg = _as_dict(
        _as_dict(_architecture_metrics_config().get("long_term_goals")).get(
            "menu_simplification"
        )
    )
    target_simplification_score_min = float(
        goals_cfg.get("target_simplification_score_min", 0.65)
    )

    payload = _read_json_if_exists(MENU_STRUCTURE_PATH)
    if not isinstance(payload, dict):
        return {
            "available": False,
            "pressure": 1.0,
            "status": "unavailable",
            "goal_target_simplification_score_min": _round2(
                target_simplification_score_min
            ),
            "goal_met": False,
            "error": "missing_or_invalid_config/menu/structure.json",
        }

    menu_entrypoints = _as_dict(payload.get("menu_entrypoints"))
    menus = _as_dict(payload.get("menus"))
    settings_split_rules = _as_dict(payload.get("settings_split_rules"))
    settings_category_metrics = _as_dict(payload.get("settings_category_metrics"))
    settings_hub_rows = (
        payload.get("settings_hub_rows")
        if isinstance(payload.get("settings_hub_rows"), list)
        else []
    )

    launcher_id = menu_entrypoints.get("launcher")
    pause_id = menu_entrypoints.get("pause")
    launcher_root_count = (
        _menu_item_count(menus, launcher_id) if isinstance(launcher_id, str) else 0
    )
    pause_root_count = _menu_item_count(menus, pause_id) if isinstance(pause_id, str) else 0
    settings_hub_count = len(settings_hub_rows)

    max_fields = int(settings_split_rules.get("max_top_level_fields", 5))
    max_actions = int(settings_split_rules.get("max_top_level_actions", 2))
    split_when_mode_specific = bool(settings_split_rules.get("split_when_mode_specific", True))

    top_level_categories = [
        category_id
        for category_id, item in settings_category_metrics.items()
        if isinstance(category_id, str)
        and isinstance(item, dict)
        and bool(item.get("top_level"))
    ]
    oversized_top_level_categories: list[str] = []
    for category_id in top_level_categories:
        metrics = _as_dict(settings_category_metrics.get(category_id))
        field_count = int(metrics.get("field_count", 0))
        action_count = int(metrics.get("action_count", 0))
        mode_specific = bool(metrics.get("mode_specific", False))
        if (
            field_count > max_fields
            or action_count > max_actions
            or (split_when_mode_specific and mode_specific)
        ):
            oversized_top_level_categories.append(category_id)

    launcher_score = _fuzzy_band_score(
        value=float(launcher_root_count),
        target_min=6,
        target_max=8,
        soft_min=4,
        soft_max=12,
        target_margin=1,
    )
    pause_score = _fuzzy_band_score(
        value=float(pause_root_count),
        target_min=6,
        target_max=8,
        soft_min=4,
        soft_max=12,
        target_margin=1,
    )
    settings_hub_score = _fuzzy_band_score(
        value=float(settings_hub_count),
        target_min=3,
        target_max=5,
        soft_min=2,
        soft_max=8,
        target_margin=1,
    )
    top_level_score = _fuzzy_band_score(
        value=float(len(top_level_categories)),
        target_min=3,
        target_max=5,
        soft_min=1,
        soft_max=8,
        target_margin=1,
    )
    policy_score = 1.0 - _clamp01(len(oversized_top_level_categories) / 3.0)
    root_score = (launcher_score + pause_score) / 2.0
    simplification_score = (
        0.45 * root_score
        + 0.2 * settings_hub_score
        + 0.2 * top_level_score
        + 0.15 * policy_score
    )
    pressure = _clamp01(1.0 - simplification_score)
    goal_met = simplification_score >= target_simplification_score_min
    if simplification_score >= 0.85:
        status = "streamlined"
    elif simplification_score >= 0.65:
        status = "manageable"
    elif simplification_score >= 0.45:
        status = "crowded"
    else:
        status = "overloaded"

    return {
        "available": True,
        "pressure": _round2(pressure),
        "status": status,
        "simplification_score": _round2(simplification_score),
        "goal_target_simplification_score_min": _round2(
            target_simplification_score_min
        ),
        "goal_met": goal_met,
        "counts": {
            "launcher_root_items": launcher_root_count,
            "pause_root_items": pause_root_count,
            "settings_hub_rows": settings_hub_count,
            "top_level_settings_categories": len(top_level_categories),
            "oversized_top_level_settings_categories": len(
                oversized_top_level_categories
            ),
            "oversized_top_level_category_ids": oversized_top_level_categories,
        },
        "policy": {
            "max_top_level_fields": max_fields,
            "max_top_level_actions": max_actions,
            "split_when_mode_specific": split_when_mode_specific,
        },
    }


def _build_tech_debt(metrics: dict[str, Any]) -> dict[str, Any]:
    tech_debt_cfg = _tech_debt_gate_config() or {}
    scoring_cfg = _tech_debt_scoring_config(tech_debt_cfg)
    backlog_text = _read(BACKLOG_PATH) if BACKLOG_PATH.exists() else ""
    backlog_rows = _active_backlog_rows(backlog_text)
    backlog_stats = _active_backlog_debt_stats(
        backlog_rows=backlog_rows,
        priority_weights=scoring_cfg["priority_weights"],
        bug_keywords=scoring_cfg["bug_keywords"],
    )
    budget_violations, folder_gate_violations = _ci_gate_violations(metrics)
    ci_issue_count = len(budget_violations) + len(folder_gate_violations)
    keybinding_retention = _build_keybinding_retention_signal()
    menu_simplification = _build_menu_simplification_signal()

    folder_summary = _as_dict(_as_dict(metrics.get("folder_balance")).get("summary"))
    leaf_balance_score = float(folder_summary.get("gate_eligible_leaf_fuzzy_weighted_balance_score_avg", folder_summary.get("leaf_fuzzy_weighted_balance_score_avg", 0.0)))
    code_balance_pressure = _clamp01(1.0 - leaf_balance_score)
    backlog_priority_pressure = _clamp01(
        backlog_stats["weighted_priority_points"] / scoring_cfg["priority_points_cap"]
    )
    bug_pressure = _clamp01(len(backlog_stats["bug_rows"]) / scoring_cfg["bug_items_cap"])
    ci_gate_pressure = _clamp01(ci_issue_count / scoring_cfg["ci_issue_cap"])
    keybinding_retention_pressure = _clamp01(
        float(keybinding_retention.get("pressure", 1.0))
    )
    menu_simplification_pressure = _clamp01(
        float(menu_simplification.get("pressure", 1.0))
    )

    overall_pressure = (
        scoring_cfg["component_weights"]["backlog_priority"] * backlog_priority_pressure
        + scoring_cfg["component_weights"]["backlog_bug"] * bug_pressure
        + scoring_cfg["component_weights"]["ci_gate"] * ci_gate_pressure
        + scoring_cfg["component_weights"]["code_balance"] * code_balance_pressure
        + scoring_cfg["component_weights"]["keybinding_retention"]
        * keybinding_retention_pressure
        + scoring_cfg["component_weights"]["menu_simplification"]
        * menu_simplification_pressure
    )
    score = _round2(overall_pressure * 100.0)
    status = _tech_debt_status(score)

    return {
        "score": score,
        "status": status,
        "direction": "down",
        "formula": "weighted_pressure_x100",
        "components": {
            "backlog_priority": {
                "weight": _round2(scoring_cfg["component_weights"]["backlog_priority"]),
                "pressure": _round2(backlog_priority_pressure),
                "weighted_open_points": _round2(backlog_stats["weighted_priority_points"]),
                "priority_weights": {
                    "P1": scoring_cfg["priority_weights"]["P1"],
                    "P2": scoring_cfg["priority_weights"]["P2"],
                    "P3": scoring_cfg["priority_weights"]["P3"],
                },
                "open_counts": backlog_stats["priority_counts"],
                "open_issue_count": len(backlog_rows),
                "normalization_cap": scoring_cfg["priority_points_cap"],
            },
            "backlog_bug": {
                "weight": _round2(scoring_cfg["component_weights"]["backlog_bug"]),
                "pressure": _round2(bug_pressure),
                "bug_issue_count": len(backlog_stats["bug_rows"]),
                "keywords": scoring_cfg["bug_keywords"],
                "sample_issue_ids": [item["id"] for item in backlog_stats["bug_rows"][:10]],
                "normalization_cap": scoring_cfg["bug_items_cap"],
            },
            "ci_gate": {
                "weight": _round2(scoring_cfg["component_weights"]["ci_gate"]),
                "pressure": _round2(ci_gate_pressure),
                "issue_count": ci_issue_count,
                "architecture_budget_overages": budget_violations,
                "folder_balance_gate_violations": folder_gate_violations,
                "normalization_cap": scoring_cfg["ci_issue_cap"],
            },
            "code_balance": {
                "weight": _round2(scoring_cfg["component_weights"]["code_balance"]),
                "pressure": _round2(code_balance_pressure),
                "gate_eligible_leaf_fuzzy_weighted_balance_score_avg": _round2(leaf_balance_score),
            },
            "keybinding_retention": {
                "weight": _round2(
                    scoring_cfg["component_weights"]["keybinding_retention"]
                ),
                "pressure": _round2(keybinding_retention_pressure),
                "signal": keybinding_retention,
            },
            "menu_simplification": {
                "weight": _round2(
                    scoring_cfg["component_weights"]["menu_simplification"]
                ),
                "pressure": _round2(menu_simplification_pressure),
                "signal": menu_simplification,
            },
        },
        "gate_context": {
            "mode": tech_debt_cfg.get("gate_mode"),
            "score_epsilon": tech_debt_cfg.get("score_epsilon"),
            "status_order": _normalized_status_order(tech_debt_cfg),
            "baseline": tech_debt_cfg.get("baseline"),
        },
    }


def _build_stage_loc_logger(src_paths: list[Path], *, arch_stage: int) -> dict[str, object]:
    package_loc: dict[str, int] = {}
    unique_folders: set[str] = set()
    total_loc = 0
    for path in src_paths:
        loc = _python_loc(path)
        total_loc += loc
        unique_folders.add(path.parent.relative_to(REPO_ROOT).as_posix())
        rel_parts = path.relative_to(REPO_ROOT).parts
        if len(rel_parts) >= 4 and rel_parts[0] == "src" and rel_parts[1] == "tet4d":
            top_package = rel_parts[2]
        elif len(rel_parts) >= 3 and rel_parts[0] == "src" and rel_parts[1] == "tet4d":
            top_package = "root"
        else:
            top_package = "other"
        package_loc[top_package] = package_loc.get(top_package, 0) + loc
    ordered_packages = dict(sorted(package_loc.items(), key=lambda item: item[0]))
    return {
        "arch_stage": arch_stage,
        "overall_python_loc": total_loc,
        "overall_python_file_count": len(src_paths),
        "overall_python_folder_count": len(unique_folders),
        "by_top_package_loc": ordered_packages,
        "log_entry": (
            f"stage={arch_stage} loc={total_loc} "
            f"files={len(src_paths)} folders={len(unique_folders)}"
        ),
    }


def _build_folder_balance(src_paths: list[Path]) -> dict[str, object]:
    profiles = _folder_balance_profiles()
    gate_config = _folder_balance_gate_config()
    tracked_leaf_folders_raw = gate_config.get("tracked_leaf_folders", []) if gate_config else []
    tracked_leaf_folder_index: dict[str, dict[str, Any]] = {}
    if isinstance(tracked_leaf_folders_raw, list):
        for item in tracked_leaf_folders_raw:
            if not isinstance(item, dict):
                continue
            raw_path = item.get("path")
            if isinstance(raw_path, str) and raw_path:
                tracked_leaf_folder_index[raw_path] = item

    folders: dict[str, dict[str, object]] = {}
    python_folders: set[str] = set()

    for path in src_paths:
        folder_rel = path.parent.relative_to(REPO_ROOT).as_posix()
        python_folders.add(folder_rel)
        loc = _python_loc(path)
        entry = folders.setdefault(
            folder_rel,
            {
                "path": folder_rel,
                "py_files": 0,
                "py_loc_total": 0,
            },
        )
        entry["py_files"] = int(entry["py_files"]) + 1
        entry["py_loc_total"] = int(entry["py_loc_total"]) + loc

    sorted_folder_paths = sorted(python_folders)
    leaf_folders = [
        folder
        for folder in sorted_folder_paths
        if not any(other.startswith(f"{folder}/") for other in sorted_folder_paths if other != folder)
    ]

    folder_rows: list[dict[str, object]] = []
    status_counts: dict[str, int] = {}
    for folder in sorted_folder_paths:
        row = dict(folders[folder])
        py_files = int(row["py_files"])
        py_loc_total = int(row["py_loc_total"])
        avg_loc_per_file = _round2(py_loc_total / py_files) if py_files else 0.0
        leaf_folder = folder in leaf_folders
        folder_profile = _folder_balance_profile_for_folder(folder, leaf_folder=leaf_folder)
        profile_def = profiles.get(folder_profile) if folder_profile else profiles["default_leaf"]
        status = _classify_folder_balance(py_files)

        py_files_cfg = profile_def["py_files"]
        loc_per_file_cfg = profile_def["avg_loc_per_file"]
        py_loc_total_cfg = profile_def["py_loc_total"]
        weights_cfg = profile_def["weights"]

        files_score = _fuzzy_band_score(
            value=float(py_files),
            target_min=float(py_files_cfg["target_band"][0]),
            target_max=float(py_files_cfg["target_band"][1]),
            soft_min=float(py_files_cfg["soft_band"][0]),
            soft_max=float(py_files_cfg["soft_band"][1]),
            target_margin=float(py_files_cfg["target_margin"]),
        )
        loc_per_file_score = _fuzzy_band_score(
            value=float(avg_loc_per_file),
            target_min=float(loc_per_file_cfg["target_band"][0]),
            target_max=float(loc_per_file_cfg["target_band"][1]),
            soft_min=float(loc_per_file_cfg["soft_band"][0]),
            soft_max=float(loc_per_file_cfg["soft_band"][1]),
            target_margin=float(loc_per_file_cfg["target_margin"]),
        )
        loc_per_folder_score = _fuzzy_band_score(
            value=float(py_loc_total),
            target_min=float(py_loc_total_cfg["target_band"][0]),
            target_max=float(py_loc_total_cfg["target_band"][1]),
            soft_min=float(py_loc_total_cfg["soft_band"][0]),
            soft_max=float(py_loc_total_cfg["soft_band"][1]),
            target_margin=float(py_loc_total_cfg["target_margin"]),
        )
        fuzzy_weighted_score = (
            files_score * float(weights_cfg["py_files"])
            + loc_per_file_score * float(weights_cfg["avg_loc_per_file"])
            + loc_per_folder_score * float(weights_cfg["py_loc_total"])
        )
        fuzzy_weighted_status = _fuzzy_weighted_status(fuzzy_weighted_score)
        status_counts[status] = status_counts.get(status, 0) + 1
        row["avg_loc_per_file"] = avg_loc_per_file
        row["leaf_folder"] = leaf_folder
        row["folder_profile"] = folder_profile
        row["gate_candidate"] = bool(leaf_folder and folder in tracked_leaf_folder_index)
        row["balancer"] = {
            "status": status,
            "target_file_band": [FOLDER_BALANCE_TARGET_FILES_MIN, FOLDER_BALANCE_TARGET_FILES_MAX],
            "delta_from_target_min": max(0, FOLDER_BALANCE_TARGET_FILES_MIN - py_files),
            "delta_from_target_max": max(0, py_files - FOLDER_BALANCE_TARGET_FILES_MAX),
            "fuzzy_weighted_score": _round2(fuzzy_weighted_score),
            "fuzzy_weighted_status": fuzzy_weighted_status,
            "weights": {
                "py_files": float(weights_cfg["py_files"]),
                "avg_loc_per_file": float(weights_cfg["avg_loc_per_file"]),
                "py_loc_total": float(weights_cfg["py_loc_total"]),
            },
            "fuzzy_components": {
                "py_files": {
                    "value": py_files,
                    "score": _round2(files_score),
                    "target_band": list(py_files_cfg["target_band"]),
                    "soft_band": list(py_files_cfg["soft_band"]),
                    "target_margin": py_files_cfg["target_margin"],
                },
                "avg_loc_per_file": {
                    "value": avg_loc_per_file,
                    "score": _round2(loc_per_file_score),
                    "target_band": list(loc_per_file_cfg["target_band"]),
                    "soft_band": list(loc_per_file_cfg["soft_band"]),
                    "target_margin": loc_per_file_cfg["target_margin"],
                },
                "py_loc_total": {
                    "value": py_loc_total,
                    "score": _round2(loc_per_folder_score),
                    "target_band": list(py_loc_total_cfg["target_band"]),
                    "soft_band": list(py_loc_total_cfg["soft_band"]),
                    "target_margin": py_loc_total_cfg["target_margin"],
                },
            },
        }
        folder_rows.append(row)

    total_files = sum(int(row["py_files"]) for row in folder_rows)
    total_loc = sum(int(row["py_loc_total"]) for row in folder_rows)
    leaf_rows = [row for row in folder_rows if bool(row["leaf_folder"])]
    leaf_total_files = sum(int(row["py_files"]) for row in leaf_rows)
    leaf_total_loc = sum(int(row["py_loc_total"]) for row in leaf_rows)
    leaf_folder_count = len(leaf_folders)
    folder_count = len(folder_rows)
    leaf_status_counts: dict[str, int] = {}
    leaf_fuzzy_status_counts: dict[str, int] = {}
    for row in leaf_rows:
        status = str(row["balancer"]["status"])
        leaf_status_counts[status] = leaf_status_counts.get(status, 0) + 1
        fuzzy_status = str(row["balancer"]["fuzzy_weighted_status"])
        leaf_fuzzy_status_counts[fuzzy_status] = leaf_fuzzy_status_counts.get(fuzzy_status, 0) + 1

    split_candidates = [
        row["path"]
        for row in sorted(leaf_rows, key=lambda item: int(item["py_files"]), reverse=True)
        if row["balancer"]["status"] == "split_signal"
    ][:10]
    thin_folder_candidates = [
        row["path"]
        for row in sorted(leaf_rows, key=lambda item: int(item["py_files"]))
        if row["balancer"]["status"] in {"too_small", "small"}
    ][:10]
    top_loc_folders = [
        {
            "path": row["path"],
            "py_files": row["py_files"],
            "py_loc_total": row["py_loc_total"],
            "avg_loc_per_file": row["avg_loc_per_file"],
        }
        for row in sorted(folder_rows, key=lambda item: int(item["py_loc_total"]), reverse=True)[:10]
    ]
    rebalance_priority_folders = [
        {
            "path": row["path"],
            "py_files": row["py_files"],
            "py_loc_total": row["py_loc_total"],
            "avg_loc_per_file": row["avg_loc_per_file"],
            "fuzzy_weighted_score": row["balancer"]["fuzzy_weighted_score"],
            "fuzzy_weighted_status": row["balancer"]["fuzzy_weighted_status"],
        }
        for row in sorted(
            leaf_rows,
            key=lambda item: (
                float(item["balancer"]["fuzzy_weighted_score"]),
                -int(item["py_files"]),
                -int(item["py_loc_total"]),
            ),
        )[:10]
    ]
    leaf_fuzzy_avg_score = (
        _round2(sum(float(row["balancer"]["fuzzy_weighted_score"]) for row in leaf_rows) / leaf_folder_count)
        if leaf_folder_count
        else 0.0
    )
    tracked_gate_records: list[dict[str, object]] = []
    if tracked_leaf_folder_index:
        row_index = {str(row["path"]): row for row in folder_rows}
        for tracked_path in sorted(tracked_leaf_folder_index):
            tracked_cfg = tracked_leaf_folder_index[tracked_path]
            row = row_index.get(tracked_path)
            tracked_gate_records.append(
                {
                    "path": tracked_path,
                    "configured_profile": tracked_cfg.get("profile"),
                    "baseline_score": tracked_cfg.get("baseline_score"),
                    "baseline_status": tracked_cfg.get("baseline_status"),
                    "found": row is not None,
                    "leaf_folder": bool(row["leaf_folder"]) if row else False,
                    "folder_profile": row.get("folder_profile") if row else None,
                    "gate_candidate": bool(row.get("gate_candidate")) if row else False,
                    "current_score": (
                        row.get("balancer", {}).get("fuzzy_weighted_score")
                        if isinstance(row.get("balancer"), dict)
                        else None
                    )
                    if row
                    else None,
                    "current_status": (
                        row.get("balancer", {}).get("fuzzy_weighted_status")
                        if isinstance(row.get("balancer"), dict)
                        else None
                    )
                    if row
                    else None,
                }
            )

    summary = {
        "python_folder_count": folder_count,
        "leaf_python_folder_count": leaf_folder_count,
        "python_file_count": total_files,
        "leaf_python_file_count": leaf_total_files,
        "python_loc_total": total_loc,
        "leaf_python_loc_total": leaf_total_loc,
        "fuzzy_files_to_leaf_folder_ratio": _round2(leaf_total_files / leaf_folder_count) if leaf_folder_count else 0.0,
        "avg_loc_per_file": _round2(total_loc / total_files) if total_files else 0.0,
        "avg_loc_per_folder": _round2(total_loc / folder_count) if folder_count else 0.0,
        "leaf_avg_loc_per_file": _round2(leaf_total_loc / leaf_total_files) if leaf_total_files else 0.0,
        "leaf_avg_loc_per_folder": _round2(leaf_total_loc / leaf_folder_count) if leaf_folder_count else 0.0,
        "leaf_fuzzy_weighted_balance_score_avg": leaf_fuzzy_avg_score,
    }

    return {
        "heuristic": {
            "target_files_per_leaf_folder_min": FOLDER_BALANCE_TARGET_FILES_MIN,
            "target_files_per_leaf_folder_max": FOLDER_BALANCE_TARGET_FILES_MAX,
            "split_signal_files_gt": FOLDER_BALANCE_SPLIT_SIGNAL_FILES_GT,
            "too_small_files_max": FOLDER_BALANCE_TOO_SMALL_FILES_MAX,
            "target_loc_per_file_min": FOLDER_BALANCE_TARGET_LOC_PER_FILE_MIN,
            "target_loc_per_file_max": FOLDER_BALANCE_TARGET_LOC_PER_FILE_MAX,
            "loc_per_file_soft_min": FOLDER_BALANCE_LOC_PER_FILE_SOFT_MIN,
            "loc_per_file_soft_max": FOLDER_BALANCE_LOC_PER_FILE_SOFT_MAX,
            "loc_per_file_target_margin": FOLDER_BALANCE_LOC_PER_FILE_TARGET_MARGIN,
            "target_loc_per_folder_min": FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN,
            "target_loc_per_folder_max": FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX,
            "loc_per_folder_soft_min": FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN,
            "loc_per_folder_soft_max": FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX,
            "loc_per_folder_target_margin": FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN,
            "files_target_margin": FOLDER_BALANCE_FILES_TARGET_MARGIN,
            "fuzzy_weights": {
                "py_files": FOLDER_BALANCE_WEIGHT_FILES,
                "avg_loc_per_file": FOLDER_BALANCE_WEIGHT_LOC_PER_FILE,
                "py_loc_total": FOLDER_BALANCE_WEIGHT_LOC_PER_FOLDER,
            },
            "profiles": profiles,
            "loc_counting": "nonblank_noncomment_lines",
        },
        "summary": summary,
        "balancer": {
            "status_counts_all_python_folders": status_counts,
            "status_counts_leaf_python_folders": leaf_status_counts,
            "fuzzy_weighted_status_counts_leaf_python_folders": leaf_fuzzy_status_counts,
            "split_signal_folders": split_candidates,
            "small_folder_candidates": thin_folder_candidates,
            "rebalance_priority_folders": rebalance_priority_folders,
            "top_folders_by_loc": top_loc_folders,
        },
        "gate": {
            "mode": gate_config.get("gate_mode") if gate_config else None,
            "scope": gate_config.get("scope") if gate_config else None,
            "profile_names": sorted({str(row["folder_profile"]) for row in leaf_rows if row.get("folder_profile")}),
            "tracked_folders": tracked_gate_records,
        },
        "folders": folder_rows,
    }


def main() -> int:
    src_paths: list[Path] = []
    seen_paths: set[Path] = set()
    for root in _metric_source_roots():
        for candidate in _py_files(root):
            if candidate in seen_paths:
                continue
            seen_paths.add(candidate)
            src_paths.append(candidate)
    engine_paths = [p for p in _py_files(REPO_ROOT / "src/tet4d/engine") if "tests" not in p.parts]
    core_paths = _py_files(REPO_ROOT / "src/tet4d/engine/core")
    replay_paths = _py_files(REPO_ROOT / "src/tet4d/replay")
    ai_paths = _py_files(REPO_ROOT / "src/tet4d/ai")
    ui_paths = _py_files(REPO_ROOT / "src/tet4d/ui")
    tools_stability_paths = _py_files(REPO_ROOT / "tools/stability")
    tools_bench_paths = _py_files(REPO_ROOT / "tools/benchmarks")
    playbot_external_paths = _py_files(REPO_ROOT / "cli") + _py_files(REPO_ROOT / "tools") + _py_files(
        REPO_ROOT / "tests/unit/engine"
    )

    ui_deep_engine = _match_engine_deep_import_lines(ui_paths)
    replay_deep_engine = _match_engine_deep_import_lines(replay_paths)
    ai_deep_engine = _match_engine_deep_import_lines(ai_paths)
    core_non_core_engine = _match_core_to_non_core_engine_imports(core_paths)
    tools_stability_deep_engine = _match_engine_deep_import_lines(tools_stability_paths)
    tools_bench_deep_engine = _match_engine_deep_import_lines(tools_bench_paths)
    legacy_engine_playbot_external = _match_lines(
        playbot_external_paths,
        r"^\s*(?:from|import)\s+tet4d\.engine\.playbot(?:\.|\b)",
    )

    core_random_imports = [
        line
        for line in _match_lines(core_paths, r"^\s*(?:from|import)\s+random(?:\.|\b)")
        if not line.startswith("src/tet4d/engine/core/rng/")
    ]
    core_purity_hits = {
        "pygame_ui_tools_imports": _match_lines(
            core_paths,
            r"^\s*(?:from|import)\s+(?:pygame(?:\.|\b)|tet4d\.ui(?:\.|\b)|tet4d\.tools(?:\.|\b)|tools(?:\.|\b))",
        ),
        "time_logging_imports": _match_lines(core_paths, r"^\s*(?:from|import)\s+(?:time(?:\.|\b)|logging(?:\.|\b))"),
        "random_imports_outside_rng": core_random_imports,
        "io_or_print_calls": _match_lines(
            core_paths,
            r"\bprint\s*\(|\blogging\.|\bopen\s*\(|\.open\s*\(|\.read_text\s*\(|\.write_text\s*\(|\.read_bytes\s*\(|\.write_bytes\s*\(",
        ),
    }

    engine_side_effect_signals = {
        "pygame_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+pygame(?:\.|\b)"),
        "time_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+time(?:\.|\b)"),
        "random_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+random(?:\.|\b)"),
        "core_step_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\.step\s*\(",
        ),
        "core_step_private_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\._[A-Za-z]\w*\s*\(",
        ),
        "core_step_state_field_assignments": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\bstate\.[A-Za-z]\w*\s*=",
        ),
        "core_rules_private_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/rules"),
            r"\._[A-Za-z]\w*\s*\(",
        ),
        "file_io_calls_non_test": _match_lines(
            engine_paths,
            r"\bopen\s*\(|\.open\s*\(|\.read_text\s*\(|\.write_text\s*\(|\.read_bytes\s*\(|\.write_bytes\s*\(",
        ),
    }

    metrics = {
        "arch_stage": ARCH_STAGE,
        "paths": {
            "engine": "src/tet4d/engine",
            "engine_core": "src/tet4d/engine/core",
            "replay": "src/tet4d/replay",
            "ai": "src/tet4d/ai",
            "ui": "src/tet4d/ui",
        },
        "deep_imports": {
            "engine_core_to_engine_non_core_imports": {
                "count": len(core_non_core_engine),
                "samples": core_non_core_engine[:20],
            },
            "ui_to_engine_non_api": {"count": len(ui_deep_engine), "samples": ui_deep_engine[:20]},
            "replay_to_engine_non_api": {"count": len(replay_deep_engine), "samples": replay_deep_engine[:20]},
            "ai_to_engine_non_api": {"count": len(ai_deep_engine), "samples": ai_deep_engine[:20]},
            "tools_stability_to_engine_non_api": {
                "count": len(tools_stability_deep_engine),
                "samples": tools_stability_deep_engine[:20],
            },
            "tools_benchmarks_to_engine_non_api": {
                "count": len(tools_bench_deep_engine),
                "samples": tools_bench_deep_engine[:20],
            },
            "external_callers_to_engine_playbot": {
                "count": len(legacy_engine_playbot_external),
                "samples": legacy_engine_playbot_external[:20],
            },
        },
        "engine_core_purity": {
            "violation_count": sum(len(v) for v in core_purity_hits.values()),
            "checks": {k: {"count": len(v), "samples": v[:20]} for k, v in core_purity_hits.items()},
        },
        "migration_debt_signals": {
            k: {"count": len(v), "samples": v[:20]}
            for k, v in engine_side_effect_signals.items()
        },
        "folder_balance": _apply_folder_class_policy(_build_folder_balance(src_paths), _folder_balance_gate_config()),
        "stage_loc_logger": _build_stage_loc_logger(src_paths, arch_stage=ARCH_STAGE),
    }
    metrics["tech_debt"] = _build_tech_debt(metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
