#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_SRC_ROOT = REPO_ROOT / "src/tet4d"
FOLDER_BALANCE_BUDGETS_PATH = REPO_ROOT / "config/project/folder_balance_budgets.json"

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

TESTS_FOLDER_BALANCE_TARGET_FILES_MIN = 12
TESTS_FOLDER_BALANCE_TARGET_FILES_MAX = 40
TESTS_FOLDER_BALANCE_FILES_SOFT_MIN = 4
TESTS_FOLDER_BALANCE_FILES_SOFT_MAX = 80
TESTS_FOLDER_BALANCE_FILES_TARGET_MARGIN = 4

TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MIN = 800
TESTS_FOLDER_BALANCE_TARGET_LOC_PER_FOLDER_MAX = 7000
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MIN = 150
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_SOFT_MAX = 15000
TESTS_FOLDER_BALANCE_LOC_PER_FOLDER_TARGET_MARGIN = 500

FOLDER_BALANCE_WEIGHT_FILES = 0.5
FOLDER_BALANCE_WEIGHT_LOC_PER_FILE = 0.3
FOLDER_BALANCE_WEIGHT_LOC_PER_FOLDER = 0.2


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
    if soft_min > target_min or target_max > soft_max:
        raise ValueError("Invalid fuzzy band bounds")
    if target_margin < 0:
        raise ValueError("target_margin must be >= 0")
    if soft_min == target_min == target_max == soft_max:
        return 1.0
    plateau_min = max(soft_min, target_min - target_margin)
    plateau_max = min(soft_max, target_max + target_margin)
    if plateau_min <= value <= plateau_max:
        return 1.0
    if value < plateau_min:
        if value <= soft_min:
            return 0.0
        if plateau_min == soft_min:
            return 0.0
        return _clamp01((value - soft_min) / (plateau_min - soft_min))
    if value >= soft_max:
        return 0.0
    if plateau_max == soft_max:
        return 0.0
    return _clamp01((soft_max - value) / (soft_max - plateau_max))


def _fuzzy_weighted_status(score: float) -> str:
    if score >= 0.85:
        return "balanced"
    if score >= 0.65:
        return "watch"
    if score >= 0.4:
        return "skewed"
    return "rebalance_signal"


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
                "target_band": [FOLDER_BALANCE_TARGET_LOC_PER_FILE_MIN, FOLDER_BALANCE_TARGET_LOC_PER_FILE_MAX],
                "soft_band": [FOLDER_BALANCE_LOC_PER_FILE_SOFT_MIN, FOLDER_BALANCE_LOC_PER_FILE_SOFT_MAX],
                "target_margin": FOLDER_BALANCE_LOC_PER_FILE_TARGET_MARGIN,
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
    src_paths = _py_files(TARGET_SRC_ROOT)
    engine_paths = [p for p in _py_files(REPO_ROOT / "src/tet4d/engine") if "tests" not in p.parts]
    core_paths = _py_files(REPO_ROOT / "src/tet4d/engine/core")
    replay_paths = _py_files(REPO_ROOT / "src/tet4d/replay")
    ai_paths = _py_files(REPO_ROOT / "src/tet4d/ai")
    ui_paths = _py_files(REPO_ROOT / "src/tet4d/ui")
    tools_stability_paths = _py_files(REPO_ROOT / "tools/stability")
    tools_bench_paths = _py_files(REPO_ROOT / "tools/benchmarks")
    playbot_external_paths = _py_files(REPO_ROOT / "cli") + _py_files(REPO_ROOT / "tools") + _py_files(
        REPO_ROOT / "src/tet4d/engine/tests"
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
        "arch_stage": 490,
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
        "folder_balance": _build_folder_balance(src_paths),
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
