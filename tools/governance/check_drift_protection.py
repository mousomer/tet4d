from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
import sys
from tokenize import COMMENT, generate_tokens
from typing import Any

if __package__:
    from ._common import (
        as_str_list,
        iter_python_files,
        load_json_object,
        load_unified_governance,
    )
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    from _common import (
        as_str_list,
        iter_python_files,
        load_json_object,
        load_unified_governance,
    )


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "config/project/policy/governance.json"


@dataclass(frozen=True)
class DriftIssue:
    kind: str
    message: str


def _load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH != ROOT / "config/project/policy/governance.json":
        return load_json_object(MANIFEST_PATH, str(MANIFEST_PATH))
    unified = load_unified_governance(ROOT)
    if isinstance(unified, dict):
        drift_protection = unified.get("drift_protection")
        if isinstance(drift_protection, dict):
            return drift_protection
    raise SystemExit("missing required file: config/project/policy/governance.json")


def _comment_line_numbers(text: str) -> set[int]:
    comment_lines: set[int] = set()
    try:
        for token in generate_tokens(io.StringIO(text).readline):
            if token.type == COMMENT:
                for line_no in range(token.start[0], token.end[0] + 1):
                    comment_lines.add(line_no)
    except Exception:
        return set()
    return comment_lines


def count_real_loc(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    comment_lines = _comment_line_numbers(text)
    count = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.strip() and line_no not in comment_lines:
            count += 1
    return count


def _validate_hotspot_scan(payload: Any, issues: list[DriftIssue]) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        issues.append(DriftIssue("schema", "hotspot_scan must be object"))
        return ("src", "cli", "tests", "tools", "scripts")
    try:
        roots = tuple(as_str_list(payload.get("roots", []), field="hotspot_scan.roots"))
    except ValueError as exc:
        issues.append(DriftIssue("schema", str(exc)))
        roots = ("src", "cli", "tests", "tools", "scripts")
    top_n = payload.get("top_n", 0)
    if not isinstance(top_n, int) or top_n <= 0:
        issues.append(DriftIssue("schema", "hotspot_scan.top_n must be positive int"))
    return roots


def collect_top_hotspots(
    *, roots: tuple[str, ...], top_n: int
) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    for rel_path in iter_python_files(ROOT, roots=roots):
        path = ROOT / rel_path
        rows.append((count_real_loc(path), rel_path))
    rows.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return rows[:top_n]


def _check_wrapper_budgets(entries: Any) -> list[DriftIssue]:
    issues: list[DriftIssue] = []
    if not isinstance(entries, list):
        return [DriftIssue("schema", "thin_wrapper_budgets must be a list")]
    for idx, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            issues.append(
                DriftIssue("schema", f"thin_wrapper_budgets[{idx}] must be object")
            )
            continue
        raw_path = entry.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            issues.append(
                DriftIssue(
                    "schema", f"thin_wrapper_budgets[{idx}].path must be non-empty str"
                )
            )
            continue
        max_real_loc = entry.get("max_real_loc")
        if not isinstance(max_real_loc, int) or max_real_loc <= 0:
            issues.append(
                DriftIssue(
                    "schema",
                    f"thin_wrapper_budgets[{idx}].max_real_loc must be positive int",
                )
            )
            continue
        role = entry.get("role")
        if not isinstance(role, str) or not role:
            issues.append(
                DriftIssue(
                    "schema", f"thin_wrapper_budgets[{idx}].role must be non-empty str"
                )
            )
            continue
        path = ROOT / raw_path
        if not path.exists():
            issues.append(
                DriftIssue("missing", f"missing wrapper budget file: {raw_path}")
            )
            continue
        current = count_real_loc(path)
        if current > max_real_loc:
            issues.append(
                DriftIssue(
                    "wrapper_budget",
                    f"{raw_path} exceeds drift budget for {role}: {current} > {max_real_loc}",
                )
            )
    return issues


def _tutorial_copy_paths(
    payload: dict[str, Any],
) -> tuple[str | None, str | None, list[DriftIssue]]:
    issues: list[DriftIssue] = []
    lessons_path_raw = payload.get("lessons_path")
    overlay_path_raw = payload.get("overlay_path")
    if not isinstance(lessons_path_raw, str) or not lessons_path_raw:
        issues.append(
            DriftIssue(
                "schema", "tutorial_copy_contract.lessons_path must be non-empty str"
            )
        )
    if not isinstance(overlay_path_raw, str) or not overlay_path_raw:
        issues.append(
            DriftIssue(
                "schema", "tutorial_copy_contract.overlay_path must be non-empty str"
            )
        )
    if issues:
        return None, None, issues
    return lessons_path_raw, overlay_path_raw, []


def _tutorial_copy_tokens(
    payload: dict[str, Any],
) -> tuple[list[str], list[str], list[DriftIssue]]:
    try:
        forbidden_prefixes = as_str_list(
            payload.get("forbidden_prefixes", []),
            field="tutorial_copy_contract.forbidden_prefixes",
        )
        required_overlay_tokens = as_str_list(
            payload.get("required_overlay_tokens", []),
            field="tutorial_copy_contract.required_overlay_tokens",
        )
    except ValueError as exc:
        return [], [], [DriftIssue("schema", str(exc))]
    return forbidden_prefixes, required_overlay_tokens, []


def _check_step_copy_fields(
    *,
    lessons_path_raw: str,
    lesson_id: str,
    step_id: str,
    ui: dict[str, Any],
    forbidden_prefixes: list[str],
) -> list[DriftIssue]:
    issues: list[DriftIssue] = []
    for field_name in ("text", "hint"):
        raw_value = ui.get(field_name)
        if not isinstance(raw_value, str):
            continue
        trimmed = raw_value.strip()
        for prefix in forbidden_prefixes:
            if trimmed.startswith(prefix):
                issues.append(
                    DriftIssue(
                        "tutorial_copy",
                        f"{lessons_path_raw}:{lesson_id}/{step_id} {field_name} starts with forbidden prefix {prefix!r}",
                    )
                )
    return issues


def _check_lessons_copy(
    *, lessons_path: Path, lessons_path_raw: str, forbidden_prefixes: list[str]
) -> list[DriftIssue]:
    issues: list[DriftIssue] = []
    lessons_payload = load_json_object(lessons_path, lessons_path_raw)
    lessons = lessons_payload.get("lessons", [])
    if not isinstance(lessons, list):
        return [
            DriftIssue("schema", "tutorial lessons payload must contain list[lessons]")
        ]

    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        lesson_id = str(lesson.get("lesson_id", "<unknown>"))
        steps = lesson.get("steps", [])
        if not isinstance(steps, list):
            continue
        for step in steps:
            if not isinstance(step, dict):
                continue
            ui = step.get("ui", {})
            if not isinstance(ui, dict):
                continue
            issues.extend(
                _check_step_copy_fields(
                    lessons_path_raw=lessons_path_raw,
                    lesson_id=lesson_id,
                    step_id=str(step.get("id", "<unknown>")),
                    ui=ui,
                    forbidden_prefixes=forbidden_prefixes,
                )
            )
    return issues


def _check_overlay_tokens(
    *, overlay_path: Path, overlay_path_raw: str, required_overlay_tokens: list[str]
) -> list[DriftIssue]:
    issues: list[DriftIssue] = []
    overlay_text = overlay_path.read_text(encoding="utf-8")
    for token in required_overlay_tokens:
        if token not in overlay_text:
            issues.append(
                DriftIssue(
                    "tutorial_overlay",
                    f"{overlay_path_raw} missing required tutorial overlay token: {token}",
                )
            )
    return issues


def _check_tutorial_copy_contract(payload: Any) -> list[DriftIssue]:
    if not isinstance(payload, dict):
        return [DriftIssue("schema", "tutorial_copy_contract must be object")]

    lessons_path_raw, overlay_path_raw, issues = _tutorial_copy_paths(payload)
    if issues:
        return issues
    forbidden_prefixes, required_overlay_tokens, issues = _tutorial_copy_tokens(payload)
    if issues:
        return issues
    assert lessons_path_raw is not None
    assert overlay_path_raw is not None

    lessons_path = ROOT / lessons_path_raw
    overlay_path = ROOT / overlay_path_raw
    if not lessons_path.exists():
        return [DriftIssue("missing", f"missing lessons file: {lessons_path_raw}")]
    if not overlay_path.exists():
        return [DriftIssue("missing", f"missing overlay file: {overlay_path_raw}")]

    issues = _check_lessons_copy(
        lessons_path=lessons_path,
        lessons_path_raw=lessons_path_raw,
        forbidden_prefixes=forbidden_prefixes,
    )
    issues.extend(
        _check_overlay_tokens(
            overlay_path=overlay_path,
            overlay_path_raw=overlay_path_raw,
            required_overlay_tokens=required_overlay_tokens,
        )
    )
    return issues


def evaluate_drift_protection() -> list[DriftIssue]:
    payload = _load_manifest()
    issues: list[DriftIssue] = []
    hotspot_scan = payload.get("hotspot_scan", {})
    roots = _validate_hotspot_scan(hotspot_scan, issues)
    top_n = hotspot_scan.get("top_n", 8) if isinstance(hotspot_scan, dict) else 8
    if not issues:
        collect_top_hotspots(roots=roots, top_n=int(top_n))
    issues.extend(_check_wrapper_budgets(payload.get("thin_wrapper_budgets", [])))
    issues.extend(
        _check_tutorial_copy_contract(payload.get("tutorial_copy_contract", {}))
    )
    return issues


def main() -> int:
    issues = evaluate_drift_protection()
    if issues:
        print("Drift protection check failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    print("Drift protection check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
