from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "config/project/canonical_maintenance.json"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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


def _help_contract_paths(manifest: dict[str, object]) -> tuple[str, str] | None:
    required = set(_iter_required_paths(manifest))
    topics_rel = "config/help/topics.json"
    map_rel = "config/help/action_map.json"
    if topics_rel not in required or map_rel not in required:
        return None
    return topics_rel, map_rel


def _load_help_payloads(
    *,
    topics_rel: str,
    map_rel: str,
    issues: list[ValidationIssue],
) -> tuple[dict[str, object], dict[str, object]] | None:
    topics_path = PROJECT_ROOT / topics_rel
    map_path = PROJECT_ROOT / map_rel
    if not topics_path.exists() or not map_path.exists():
        return None
    topics_payload = _load_json_payload(topics_path, topics_rel, issues)
    map_payload = _load_json_payload(map_path, map_rel, issues)
    if not isinstance(topics_payload, dict) or not isinstance(map_payload, dict):
        return None
    return topics_payload, map_payload


def _collect_topic_lanes(
    topics_payload: dict[str, object],
    *,
    topics_rel: str,
    issues: list[ValidationIssue],
) -> dict[str, str]:
    raw_topics = topics_payload.get("topics")
    if not isinstance(raw_topics, list) or not raw_topics:
        issues.append(ValidationIssue("json", f"{topics_rel} must define non-empty list 'topics'"))
        return {}

    topic_lanes: dict[str, str] = {}
    for idx, raw_topic in enumerate(raw_topics):
        if not isinstance(raw_topic, dict):
            issues.append(ValidationIssue("json", f"{topics_rel}.topics[{idx}] must be an object"))
            continue
        topic_id = raw_topic.get("id")
        if not isinstance(topic_id, str) or not topic_id.strip():
            issues.append(ValidationIssue("json", f"{topics_rel}.topics[{idx}].id must be a non-empty string"))
            continue
        lane = raw_topic.get("lane")
        if not isinstance(lane, str) or not lane.strip():
            issues.append(ValidationIssue("json", f"{topics_rel}.topics[{idx}].lane must be a non-empty string"))
            continue
        if topic_id in topic_lanes:
            issues.append(ValidationIssue("json", f"{topics_rel} duplicate topic id: {topic_id}"))
            continue
        topic_lanes[topic_id] = lane.strip().lower()
    return topic_lanes


def _collect_action_topics(
    map_payload: dict[str, object],
    *,
    map_rel: str,
    topic_ids: set[str],
    issues: list[ValidationIssue],
) -> dict[str, str]:
    default_topic = map_payload.get("default_topic")
    if not isinstance(default_topic, str) or not default_topic.strip():
        issues.append(ValidationIssue("json", f"{map_rel}.default_topic must be a non-empty string"))
    elif default_topic not in topic_ids:
        issues.append(ValidationIssue("json", f"{map_rel}.default_topic references unknown topic id: {default_topic}"))

    raw_action_topics = map_payload.get("action_topics")
    if not isinstance(raw_action_topics, dict) or not raw_action_topics:
        issues.append(ValidationIssue("json", f"{map_rel}.action_topics must be a non-empty object"))
        return {}

    action_topics: dict[str, str] = {}
    for action, topic_id in raw_action_topics.items():
        if not isinstance(action, str) or not action.strip():
            issues.append(ValidationIssue("json", f"{map_rel}.action_topics includes non-string action key"))
            continue
        if not isinstance(topic_id, str) or not topic_id.strip():
            issues.append(ValidationIssue("json", f"{map_rel}.action_topics.{action} must be a non-empty string"))
            continue
        if topic_id not in topic_ids:
            issues.append(ValidationIssue("json", f"{map_rel}.action_topics.{action} references unknown topic id: {topic_id}"))
        action_topics[action] = topic_id
    return action_topics


def _validate_action_topics_coverage(
    *,
    map_rel: str,
    action_topics: dict[str, str],
    issues: list[ValidationIssue],
) -> None:
    from tetris_nd.keybindings_catalog import binding_action_ids

    known_actions = set(binding_action_ids())
    mapped_actions = set(action_topics.keys())

    unknown_actions = sorted(mapped_actions - known_actions)
    if unknown_actions:
        issues.append(
            ValidationIssue(
                "json",
                f"{map_rel}.action_topics includes unknown action ids: {', '.join(unknown_actions)}",
            )
        )

    missing_actions = sorted(known_actions - mapped_actions)
    if missing_actions:
        issues.append(
            ValidationIssue(
                "json",
                f"{map_rel}.action_topics missing action ids: {', '.join(missing_actions)}",
            )
        )


def _validate_action_topic_lanes(
    *,
    map_rel: str,
    action_topics: dict[str, str],
    topic_lanes: dict[str, str],
    issues: list[ValidationIssue],
) -> None:
    allowed_lanes = {"quick", "full"}
    invalid_actions = [
        f"{action}->{topic_id}({topic_lanes.get(topic_id, 'unknown')})"
        for action, topic_id in sorted(action_topics.items())
        if topic_lanes.get(topic_id) not in allowed_lanes
    ]
    if invalid_actions:
        issues.append(
            ValidationIssue(
                "json",
                f"{map_rel}.action_topics should map to quick/full help lanes only: {', '.join(invalid_actions)}",
            )
        )


def _validate_help_topic_contract(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    paths = _help_contract_paths(manifest)
    if paths is None:
        return issues
    topics_rel, map_rel = paths

    payloads = _load_help_payloads(topics_rel=topics_rel, map_rel=map_rel, issues=issues)
    if payloads is None:
        return issues
    topics_payload, map_payload = payloads

    topic_lanes = _collect_topic_lanes(topics_payload, topics_rel=topics_rel, issues=issues)
    if not topic_lanes:
        return issues

    action_topics = _collect_action_topics(
        map_payload,
        map_rel=map_rel,
        topic_ids=set(topic_lanes.keys()),
        issues=issues,
    )
    if not action_topics:
        return issues

    _validate_action_topics_coverage(
        map_rel=map_rel,
        action_topics=action_topics,
        issues=issues,
    )
    _validate_action_topic_lanes(
        map_rel=map_rel,
        action_topics=action_topics,
        topic_lanes=topic_lanes,
        issues=issues,
    )
    return issues


def _validate_menu_graph_contract() -> list[ValidationIssue]:
    from tetris_nd.menu_graph_linter import lint_menu_graph

    issues: list[ValidationIssue] = []
    for issue in lint_menu_graph():
        issues.append(ValidationIssue("menu_graph", issue.message))
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
    issues.extend(_validate_help_topic_contract(manifest))
    issues.extend(_validate_menu_graph_contract())
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
