from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "config/project/canonical_maintenance.json"


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    message: str


def _load_manifest() -> dict[str, object]:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {MANIFEST_PATH}: {exc}") from exc
    return payload


def _validate_required_paths(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_paths = manifest.get("required_paths", {})
    if not isinstance(required_paths, dict):
        return [ValidationIssue("schema", "'required_paths' must be an object")]

    seen: set[str] = set()
    for group, rel_paths in required_paths.items():
        if not isinstance(rel_paths, list):
            issues.append(ValidationIssue("schema", f"required_paths.{group} must be a list"))
            continue
        for rel in rel_paths:
            if not isinstance(rel, str):
                issues.append(ValidationIssue("schema", f"required_paths.{group} includes non-string entry"))
                continue
            if rel in seen:
                issues.append(ValidationIssue("duplicate", f"path appears in multiple groups: {rel}"))
                continue
            seen.add(rel)
            path = PROJECT_ROOT / rel
            if not path.exists():
                issues.append(ValidationIssue("missing", f"missing required path: {rel}"))
    return issues


def _iter_required_paths(manifest: dict[str, object]) -> list[str]:
    required_paths = manifest.get("required_paths", {})
    if not isinstance(required_paths, dict):
        return []
    rels: list[str] = []
    for rel_paths in required_paths.values():
        if not isinstance(rel_paths, list):
            continue
        for rel in rel_paths:
            if isinstance(rel, str):
                rels.append(rel)
    return rels


def _load_json_payload(path: Path, rel: str, issues: list[ValidationIssue]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(ValidationIssue("json", f"{rel} is not valid JSON: {exc}"))
        return None


def _validate_schema_payload(rel: str, payload: object, issues: list[ValidationIssue]) -> None:
    if rel.endswith(".schema.json") and (not isinstance(payload, dict) or "$schema" not in payload):
        issues.append(ValidationIssue("json", f"{rel} must contain a top-level '$schema'"))


def _validate_replay_manifest_payload(rel: str, payload: object, issues: list[ValidationIssue]) -> None:
    if rel != "tests/replay/manifest.json":
        return
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return
    if not isinstance(payload.get("version"), int):
        issues.append(ValidationIssue("json", f"{rel} must define integer 'version'"))
    if not isinstance(payload.get("suites"), list):
        issues.append(ValidationIssue("json", f"{rel} must define list 'suites'"))


def _validate_required_json_files(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _iter_required_paths(manifest):
        if not rel.endswith(".json"):
            continue
        path = PROJECT_ROOT / rel
        if not path.exists() or not path.is_file():
            continue
        payload = _load_json_payload(path, rel, issues)
        if payload is None:
            continue

        _validate_schema_payload(rel, payload, issues)
        _validate_replay_manifest_payload(rel, payload, issues)
    return issues


def _validate_canonical_candidates(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    candidates = manifest.get("canonical_candidates", [])
    if not isinstance(candidates, list):
        return [ValidationIssue("schema", "'canonical_candidates' must be a list")]

    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, dict):
            issues.append(ValidationIssue("schema", f"canonical_candidates[{index}] must be an object"))
            continue
        name = item.get("name")
        status = item.get("status")
        paths = item.get("paths", [])
        if not isinstance(name, str) or not name:
            issues.append(ValidationIssue("schema", f"canonical_candidates[{index}].name must be a string"))
        if not isinstance(status, str) or status not in {"planned", "connected"}:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"canonical_candidates[{index}].status must be 'planned' or 'connected'",
                )
            )
        if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
            issues.append(ValidationIssue("schema", f"canonical_candidates[{index}].paths must be a list[str]"))
            continue
        for rel in paths:
            path = PROJECT_ROOT / rel
            if not path.exists():
                issues.append(ValidationIssue("missing", f"canonical candidate path missing: {rel}"))
    return issues


def _validate_content_rules(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    content_rules = manifest.get("content_rules", [])
    if not isinstance(content_rules, list):
        return [ValidationIssue("schema", "'content_rules' must be a list")]

    for index, rule in enumerate(content_rules, start=1):
        parsed = _parse_content_rule(index, rule)
        if isinstance(parsed, ValidationIssue):
            issues.append(parsed)
            continue
        rel, tokens, forbidden_tokens, required_regexes, forbidden_regexes = parsed
        path = PROJECT_ROOT / rel
        if not path.exists():
            issues.append(ValidationIssue("missing", f"content rule file does not exist: {rel}"))
            continue
        _validate_text_rules(
            path,
            rel,
            tokens,
            forbidden_tokens,
            required_regexes,
            forbidden_regexes,
            issues,
        )
    return issues


def _as_string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or any(not isinstance(token, str) for token in value):
        return None
    return value


def _parse_content_rule(
    index: int,
    rule: object,
) -> tuple[str, list[str], list[str], list[str], list[str]] | ValidationIssue:
    if not isinstance(rule, dict):
        return ValidationIssue("schema", f"content_rules[{index}] must be an object")

    rel = rule.get("file")
    if not isinstance(rel, str):
        return ValidationIssue("schema", f"content_rules[{index}].file must be a string")

    tokens = _as_string_list(rule.get("must_contain", []))
    if tokens is None:
        return ValidationIssue("schema", f"content_rules[{index}].must_contain must be a list[str]")

    forbidden_tokens = _as_string_list(rule.get("must_not_contain", []))
    if forbidden_tokens is None:
        return ValidationIssue("schema", f"content_rules[{index}].must_not_contain must be a list[str]")

    required_regexes = _as_string_list(rule.get("must_match_regex", []))
    if required_regexes is None:
        return ValidationIssue("schema", f"content_rules[{index}].must_match_regex must be a list[str]")

    forbidden_regexes = _as_string_list(rule.get("must_not_match_regex", []))
    if forbidden_regexes is None:
        return ValidationIssue("schema", f"content_rules[{index}].must_not_match_regex must be a list[str]")

    return rel, tokens, forbidden_tokens, required_regexes, forbidden_regexes


def _validate_text_rules(
    path: Path,
    rel: str,
    tokens: list[str],
    forbidden_tokens: list[str],
    required_regexes: list[str],
    forbidden_regexes: list[str],
    issues: list[ValidationIssue],
) -> None:
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in text:
            issues.append(ValidationIssue("content", f"{rel} missing token: {token!r}"))
    for token in forbidden_tokens:
        if token in text:
            issues.append(ValidationIssue("content", f"{rel} contains forbidden token: {token!r}"))
    _validate_regex_rules(rel, text, required_regexes, forbidden_regexes, issues)


def _validate_regex_rules(
    rel: str,
    text: str,
    required_regexes: list[str],
    forbidden_regexes: list[str],
    issues: list[ValidationIssue],
) -> None:
    for pattern in required_regexes:
        compiled = _compile_pattern(rel, pattern, issues)
        if compiled is None:
            continue
        if compiled.search(text) is None:
            issues.append(ValidationIssue("content", f"{rel} missing regex match: {pattern!r}"))

    for pattern in forbidden_regexes:
        compiled = _compile_pattern(rel, pattern, issues)
        if compiled is None:
            continue
        if compiled.search(text) is not None:
            issues.append(ValidationIssue("content", f"{rel} matched forbidden regex: {pattern!r}"))


def _compile_pattern(rel: str, pattern: str, issues: list[ValidationIssue]) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern, flags=re.MULTILINE)
    except re.error as exc:
        issues.append(ValidationIssue("schema", f"invalid regex in content rule for {rel}: {pattern!r} ({exc})"))
        return None


def validate_manifest() -> list[ValidationIssue]:
    manifest = _load_manifest()
    issues: list[ValidationIssue] = []
    issues.extend(_validate_required_paths(manifest))
    issues.extend(_validate_required_json_files(manifest))
    issues.extend(_validate_canonical_candidates(manifest))
    issues.extend(_validate_content_rules(manifest))
    return issues


def main() -> int:
    issues = validate_manifest()
    if issues:
        print("Project contract validation failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1

    manifest = _load_manifest()
    required_paths = manifest.get("required_paths", {})
    total_paths = 0
    if isinstance(required_paths, dict):
        for rel_paths in required_paths.values():
            if isinstance(rel_paths, list):
                total_paths += len(rel_paths)
    print(f"Project contract validation passed ({total_paths} required paths checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
