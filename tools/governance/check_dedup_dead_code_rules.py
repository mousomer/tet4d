from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "config/project/policy/manifests/dedup_dead_code_rules.json"


@dataclass(frozen=True)
class DedupIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class DedupWarning:
    kind: str
    message: str


def _load_rules() -> dict[str, Any]:
    rel = "config/project/policy/manifests/dedup_dead_code_rules.json"
    try:
        payload = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing required file: {rel}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {rel}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{rel} must be a JSON object")
    return payload


def _repo_files() -> list[str]:
    files: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(".git/"):
            continue
        files.append(rel)
    return sorted(files)


def _matches_any(rel: str, globs: list[str]) -> bool:
    return any(fnmatch(rel, pattern) for pattern in globs)


def _check_forbidden_paths(payload: dict[str, Any]) -> list[DedupIssue]:
    issues: list[DedupIssue] = []
    forbidden_paths = payload.get("forbidden_paths", [])
    if not isinstance(forbidden_paths, list) or any(
        not isinstance(item, str) for item in forbidden_paths
    ):
        return [DedupIssue("schema", "forbidden_paths must be list[str]")]
    repo_files = _repo_files()
    for rel in repo_files:
        if any(rel.startswith(prefix) for prefix in forbidden_paths):
            issues.append(
                DedupIssue("dead_code", f"forbidden legacy path present: {rel}")
            )
    return issues


def _check_todo_backlog_rule(payload: dict[str, Any]) -> list[DedupIssue]:
    rule = payload.get("todo_backlog_rule", {})
    if not isinstance(rule, dict):
        return [DedupIssue("schema", "todo_backlog_rule must be object")]
    scope_globs = rule.get("scope_globs", [])
    if not isinstance(scope_globs, list) or any(
        not isinstance(item, str) for item in scope_globs
    ):
        return [DedupIssue("schema", "todo_backlog_rule.scope_globs must be list[str]")]
    ignore_globs = rule.get("ignore_globs", [])
    if not isinstance(ignore_globs, list) or any(
        not isinstance(item, str) for item in ignore_globs
    ):
        return [
            DedupIssue("schema", "todo_backlog_rule.ignore_globs must be list[str]")
        ]
    token_regex = str(rule.get("token_regex", r"\b(?:TODO|FIXME)\b"))
    backlog_regex = str(rule.get("required_backlog_regex", r"\[BKL-[^\]]+\]"))
    token_pattern = re.compile(token_regex)
    backlog_pattern = re.compile(backlog_regex)

    issues: list[DedupIssue] = []
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if not _matches_any(rel, scope_globs):
            continue
        if _matches_any(rel, ignore_globs):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if token_pattern.search(line) and not backlog_pattern.search(line):
                issues.append(
                    DedupIssue(
                        "dedup_todo",
                        f"{rel}:{lineno} TODO/FIXME missing backlog id token",
                    )
                )
    return issues


def _function_signature_hash(
    func: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    if not func.body:
        return None
    body_src = [ast.dump(stmt, include_attributes=False) for stmt in func.body]
    normalized = "\n".join(body_src).strip()
    if not normalized:
        return None
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def _parse_duplicate_rule(
    payload: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[DedupIssue]]:
    rule = payload.get("duplicate_functions", {})
    if not isinstance(rule, dict):
        return None, [DedupIssue("schema", "duplicate_functions must be object")]
    if not bool(rule.get("enabled", False)):
        return None, []

    strict_scope_globs = rule.get("strict_scope_globs", [])
    advisory_scope_globs = rule.get("advisory_scope_globs", [])
    if not isinstance(strict_scope_globs, list) or any(
        not isinstance(item, str) for item in strict_scope_globs
    ):
        return None, [
            DedupIssue(
                "schema", "duplicate_functions.strict_scope_globs must be list[str]"
            )
        ]
    if not isinstance(advisory_scope_globs, list) or any(
        not isinstance(item, str) for item in advisory_scope_globs
    ):
        return None, [
            DedupIssue(
                "schema", "duplicate_functions.advisory_scope_globs must be list[str]"
            )
        ]
    exclude_names = rule.get("exclude_function_names", [])
    if not isinstance(exclude_names, list) or any(
        not isinstance(item, str) for item in exclude_names
    ):
        return None, [
            DedupIssue(
                "schema", "duplicate_functions.exclude_function_names must be list[str]"
            )
        ]
    parsed = {
        "strict_scope_globs": strict_scope_globs,
        "advisory_scope_globs": advisory_scope_globs,
        "min_body_lines": int(rule.get("min_body_lines", 10)),
        "max_allowed": int(rule.get("max_allowed_duplicates_per_signature", 1)),
        "exclude_names": exclude_names,
    }
    return parsed, []


def _collect_duplicate_signatures(
    *,
    scope_globs: list[str],
    min_body_lines: int,
    exclude_names: list[str],
) -> dict[str, list[str]]:
    signatures: dict[str, list[str]] = {}
    for path in ROOT.rglob("*.py"):
        rel = path.relative_to(ROOT).as_posix()
        if not _matches_any(rel, scope_globs):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name in exclude_names:
                continue
            body_len = max(
                0,
                (node.end_lineno or node.lineno) - node.lineno,
            )
            if body_len < min_body_lines:
                continue
            signature = _function_signature_hash(node)
            if signature is None:
                continue
            signatures.setdefault(signature, []).append(
                f"{rel}:{node.lineno}:{node.name}"
            )
    return signatures


def _duplicate_signature_messages(
    signatures: dict[str, list[str]], *, max_allowed: int
) -> list[str]:
    messages: list[str] = []
    for locations in signatures.values():
        if len(locations) <= max_allowed:
            continue
        messages.append("duplicate function bodies detected: " + ", ".join(locations))
    return messages


def _check_duplicate_functions(
    payload: dict[str, Any],
) -> tuple[list[DedupIssue], list[DedupWarning]]:
    parsed, parse_issues = _parse_duplicate_rule(payload)
    if parse_issues or parsed is None:
        return parse_issues, []

    strict_signatures = _collect_duplicate_signatures(
        scope_globs=parsed["strict_scope_globs"],
        min_body_lines=parsed["min_body_lines"],
        exclude_names=parsed["exclude_names"],
    )
    advisory_signatures = _collect_duplicate_signatures(
        scope_globs=parsed["advisory_scope_globs"],
        min_body_lines=parsed["min_body_lines"],
        exclude_names=parsed["exclude_names"],
    )
    strict_messages = _duplicate_signature_messages(
        strict_signatures, max_allowed=parsed["max_allowed"]
    )
    advisory_messages = _duplicate_signature_messages(
        advisory_signatures, max_allowed=parsed["max_allowed"]
    )
    issues = [DedupIssue("dedup_function", msg) for msg in strict_messages]
    warnings = [DedupWarning("dedup_function", msg) for msg in advisory_messages]
    return issues, warnings


def main() -> int:
    payload = _load_rules()
    issues: list[DedupIssue] = []
    warnings: list[DedupWarning] = []
    issues.extend(_check_forbidden_paths(payload))
    issues.extend(_check_todo_backlog_rule(payload))
    duplicate_issues, duplicate_warnings = _check_duplicate_functions(payload)
    issues.extend(duplicate_issues)
    warnings.extend(duplicate_warnings)

    if issues:
        print("Dedup/dead-code check failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    if warnings:
        print("Dedup/dead-code warnings (non-blocking):")
        for warning in warnings:
            print(f"- [{warning.kind}] {warning.message}")
    print("Dedup/dead-code check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
