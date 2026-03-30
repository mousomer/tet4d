from __future__ import annotations

import re
import ast
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
import sys
from typing import Any

if __package__:
    from ._common import iter_python_files, load_unified_code_rules
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    from _common import iter_python_files, load_unified_code_rules


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class WheelIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class WheelRule:
    rule_id: str
    scope_globs: list[str]
    forbidden_regex: list[str]
    ast_detectors: list[str]
    prefer_symbols: list[str]


def _load_rules() -> dict[str, Any]:
    unified = load_unified_code_rules(ROOT)
    if isinstance(unified, dict):
        wheel_rules = unified.get("wheel_reuse")
        if isinstance(wheel_rules, dict):
            return wheel_rules
    raise SystemExit("missing required file: config/project/policy/code_rules.json")


def _tracked_python_files() -> list[str]:
    return iter_python_files(ROOT, roots=("src", "tools", "scripts"))


def _list_str(value: Any, field: str, issues: list[WheelIssue]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        issues.append(WheelIssue("schema", f"{field} must be list[str]"))
        return []
    return value


def _matches_scope(path: str, globs: list[str]) -> bool:
    return any(fnmatch(path, pattern) for pattern in globs)


def _violates_rule(
    *,
    text: str,
    forbidden_regex: list[str],
    ast_detectors: list[str],
    prefer_symbols: list[str],
    exception_marker: str,
) -> list[str]:
    matched = [
        pat for pat in forbidden_regex if re.search(pat, text, flags=re.MULTILINE)
    ]
    matched.extend(_match_ast_detectors(text, ast_detectors))
    if not matched:
        return []
    if exception_marker in text:
        return []
    if any(symbol in text for symbol in prefer_symbols):
        return []
    return matched


def _function_nodes(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    out: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node)
    return out


def _has_lower_and_bool_literals(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    has_lower = False
    has_bool_lits = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "lower":
                has_lower = True
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value.lower() in {"true", "false", "yes", "no", "on", "off"}:
                has_bool_lits = True
    return has_lower and has_bool_lits


def _has_isdigit_and_int(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    has_isdigit = False
    has_int_call = False
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"isdigit", "isnumeric"}:
                has_isdigit = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "int":
                has_int_call = True
    return has_isdigit and has_int_call


def _is_max_min_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "max":
        return False
    for arg in node.args:
        if (
            isinstance(arg, ast.Call)
            and isinstance(arg.func, ast.Name)
            and arg.func.id == "min"
        ):
            return True
    return False


def _match_ast_detectors(text: str, detectors: list[str]) -> list[str]:
    if not detectors:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    functions = _function_nodes(tree)
    matched: list[str] = []
    for detector in detectors:
        if detector == "custom_bool_parser":
            if any(
                "bool" in func.name.lower() and _has_lower_and_bool_literals(func)
                for func in functions
            ):
                matched.append("ast:custom_bool_parser")
        elif detector == "custom_numeric_text_parser":
            if any(_has_isdigit_and_int(func) for func in functions):
                matched.append("ast:custom_numeric_text_parser")
        elif detector == "custom_clamp_helper":
            if any(
                "clamp" in func.name.lower()
                and any(_is_max_min_call(node) for node in ast.walk(func))
                for func in functions
            ):
                matched.append("ast:custom_clamp_helper")
    return matched


def _parse_rules(payload: dict[str, Any], issues: list[WheelIssue]) -> list[WheelRule]:
    rules = payload.get("rules")
    if not isinstance(rules, list):
        issues.append(WheelIssue("schema", "rules must be a list"))
        return []

    parsed: list[WheelRule] = []
    for idx, raw in enumerate(rules, start=1):
        if not isinstance(raw, dict):
            issues.append(WheelIssue("schema", f"rules[{idx}] must be object"))
            continue
        rule_id = raw.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            issues.append(
                WheelIssue("schema", f"rules[{idx}].id must be non-empty str")
            )
            continue
        scope_globs = _list_str(
            raw.get("scope_globs"), f"rules[{idx}].scope_globs", issues
        )
        forbidden_regex = _list_str(
            raw.get("forbidden_regex"), f"rules[{idx}].forbidden_regex", issues
        )
        ast_detectors = _list_str(
            raw.get("ast_detectors", []), f"rules[{idx}].ast_detectors", issues
        )
        prefer_symbols = _list_str(
            raw.get("prefer_symbols"), f"rules[{idx}].prefer_symbols", issues
        )
        if not scope_globs or not forbidden_regex:
            continue
        parsed.append(
            WheelRule(
                rule_id=rule_id,
                scope_globs=scope_globs,
                forbidden_regex=forbidden_regex,
                ast_detectors=ast_detectors,
                prefer_symbols=prefer_symbols,
            )
        )
    return parsed


def _evaluate_rules(
    *,
    rules: list[WheelRule],
    python_files: list[str],
    exception_marker: str,
    issues: list[WheelIssue],
) -> None:
    for rule in rules:
        for rel in python_files:
            if not _matches_scope(rel, rule.scope_globs):
                continue
            text = (ROOT / rel).read_text(encoding="utf-8")
            matched = _violates_rule(
                text=text,
                forbidden_regex=rule.forbidden_regex,
                ast_detectors=rule.ast_detectors,
                prefer_symbols=rule.prefer_symbols,
                exception_marker=exception_marker,
            )
            if not matched:
                continue
            issues.append(
                WheelIssue(
                    "reinvented_wheel",
                    f"{rel} violates {rule.rule_id}; matched patterns: {', '.join(matched)}",
                )
            )


def main() -> int:
    payload = _load_rules()
    issues: list[WheelIssue] = []
    rules = _parse_rules(payload, issues)
    _evaluate_rules(
        rules=rules,
        python_files=_tracked_python_files(),
        exception_marker=str(payload.get("exception_marker", "Wheel Exception:")),
        issues=issues,
    )
    if issues:
        print("Wheel reuse check failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    print("Wheel reuse check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
