from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
PACK_PATH = PROJECT_ROOT / "config/project/policy/pack.json"
MANIFEST_PATH = (
    PROJECT_ROOT / "config/project/policy/manifests/canonical_maintenance.json"
)
CONTEXT_ROUTER_PATH = (
    PROJECT_ROOT / "config/project/policy/manifests/context_router_manifest.json"
)
ALLOWED_CONTEXT_IDS = {
    "code",
    "tests",
    "build_packaging",
    "policy_contracts",
    "docs_design",
    "assets_fixtures",
    "environment",
    "git_state",
    "git_history",
    "runtime_evidence",
    "session_decisions",
    "planning",
}
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    message: str


def _load_pack() -> dict[str, object]:
    try:
        payload = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing policy pack: {PACK_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {PACK_PATH}: {exc}") from exc
    return payload


def _validate_pack_components(pack: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    components = pack.get("components")
    if not isinstance(components, list):
        return [ValidationIssue("schema", "'components' must be a list")]

    seen_ids: set[str] = set()
    for idx, comp in enumerate(components):
        if not isinstance(comp, dict):
            issues.append(
                ValidationIssue("schema", f"components[{idx}] must be an object")
            )
            continue
        comp_id = comp.get("id")
        comp_path = comp.get("path")
        context_id = comp.get("context_id")
        if not isinstance(comp_id, str) or not comp_id:
            issues.append(
                ValidationIssue(
                    "schema", f"components[{idx}].id must be a non-empty string"
                )
            )
        elif comp_id in seen_ids:
            issues.append(
                ValidationIssue("duplicate", f"duplicate component id: {comp_id}")
            )
        else:
            seen_ids.add(comp_id)
        if not isinstance(comp_path, str) or not comp_path:
            issues.append(
                ValidationIssue(
                    "schema", f"components[{idx}].path must be a non-empty string"
                )
            )
        if not isinstance(context_id, str) or context_id not in ALLOWED_CONTEXT_IDS:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"components[{idx}].context_id must be one of {sorted(ALLOWED_CONTEXT_IDS)}",
                )
            )
    return issues


def _load_component_payloads(
    pack: dict[str, object], issues: list[ValidationIssue]
) -> dict[str, object]:
    payloads: dict[str, object] = {}
    components = pack.get("components")
    if not isinstance(components, list):
        return payloads
    for comp in components:
        if not isinstance(comp, dict):
            continue
        rel = comp.get("path")
        if not isinstance(rel, str):
            continue
        path = PROJECT_ROOT / rel
        if not path.exists():
            issues.append(
                ValidationIssue("missing_component", f"missing component file: {rel}")
            )
            continue
        payload = _load_json_payload(path, rel, issues)
        if payload is None:
            continue
        payloads[rel] = payload
    return payloads


def _walk_strings(
    obj: object, rel: str, issues: list[ValidationIssue], forbidden_tokens: list[str]
) -> None:
    stack: list[object] = [obj]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            for token in forbidden_tokens:
                if token and token in current:
                    issues.append(
                        ValidationIssue(
                            "forbidden",
                            f"{rel} contains forbidden token: {token!r}",
                        )
                    )


def _validate_pack_constraints(
    pack: dict[str, object], payloads: dict[str, object]
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    constraints = pack.get("constraints", {})
    if not isinstance(constraints, dict):
        return [ValidationIssue("schema", "'constraints' must be an object")]

    forbidden_tokens: list[str] = []
    forbidden_tokens.extend(constraints.get("forbidden_module_prefixes", []) or [])
    forbidden_tokens.extend(constraints.get("forbidden_paths", []) or [])
    forbidden_tokens = [t for t in forbidden_tokens if isinstance(t, str) and t]

    if not forbidden_tokens:
        return issues

    for rel, payload in payloads.items():
        if rel.endswith("canonical_maintenance.json"):
            continue
        _walk_strings(payload, rel, issues, forbidden_tokens)
    return issues


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
            issues.append(
                ValidationIssue("schema", f"required_paths.{group} must be a list")
            )
            continue
        for rel in rel_paths:
            if not isinstance(rel, str):
                issues.append(
                    ValidationIssue(
                        "schema", f"required_paths.{group} includes non-string entry"
                    )
                )
                continue
            if rel in seen:
                issues.append(
                    ValidationIssue(
                        "duplicate", f"path appears in multiple groups: {rel}"
                    )
                )
                continue
            seen.add(rel)
            path = PROJECT_ROOT / rel
            if not path.exists():
                issues.append(
                    ValidationIssue("missing", f"missing required path: {rel}")
                )
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


def _load_json_payload(
    path: Path, rel: str, issues: list[ValidationIssue]
) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(ValidationIssue("json", f"{rel} is not valid JSON: {exc}"))
        return None


def _validate_schema_payload(
    rel: str, payload: object, issues: list[ValidationIssue]
) -> None:
    if rel.endswith(".schema.json") and (
        not isinstance(payload, dict) or "$schema" not in payload
    ):
        issues.append(
            ValidationIssue("json", f"{rel} must contain a top-level '$schema'")
        )


def _validate_replay_manifest_payload(
    rel: str, payload: object, issues: list[ValidationIssue]
) -> None:
    if rel != "config/project/policy/manifests/replay_manifest.json":
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
        issues.append(
            ValidationIssue("json", f"{topics_rel} must define non-empty list 'topics'")
        )
        return {}

    topic_lanes: dict[str, str] = {}
    for idx, raw_topic in enumerate(raw_topics):
        if not isinstance(raw_topic, dict):
            issues.append(
                ValidationIssue("json", f"{topics_rel}.topics[{idx}] must be an object")
            )
            continue
        topic_id = raw_topic.get("id")
        if not isinstance(topic_id, str) or not topic_id.strip():
            issues.append(
                ValidationIssue(
                    "json", f"{topics_rel}.topics[{idx}].id must be a non-empty string"
                )
            )
            continue
        lane = raw_topic.get("lane")
        if not isinstance(lane, str) or not lane.strip():
            issues.append(
                ValidationIssue(
                    "json",
                    f"{topics_rel}.topics[{idx}].lane must be a non-empty string",
                )
            )
            continue
        if topic_id in topic_lanes:
            issues.append(
                ValidationIssue("json", f"{topics_rel} duplicate topic id: {topic_id}")
            )
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
        issues.append(
            ValidationIssue(
                "json", f"{map_rel}.default_topic must be a non-empty string"
            )
        )
    elif default_topic not in topic_ids:
        issues.append(
            ValidationIssue(
                "json",
                f"{map_rel}.default_topic references unknown topic id: {default_topic}",
            )
        )

    raw_action_topics = map_payload.get("action_topics")
    if not isinstance(raw_action_topics, dict) or not raw_action_topics:
        issues.append(
            ValidationIssue(
                "json", f"{map_rel}.action_topics must be a non-empty object"
            )
        )
        return {}

    action_topics: dict[str, str] = {}
    for action, topic_id in raw_action_topics.items():
        if not isinstance(action, str) or not action.strip():
            issues.append(
                ValidationIssue(
                    "json", f"{map_rel}.action_topics includes non-string action key"
                )
            )
            continue
        if not isinstance(topic_id, str) or not topic_id.strip():
            issues.append(
                ValidationIssue(
                    "json",
                    f"{map_rel}.action_topics.{action} must be a non-empty string",
                )
            )
            continue
        if topic_id not in topic_ids:
            issues.append(
                ValidationIssue(
                    "json",
                    f"{map_rel}.action_topics.{action} references unknown topic id: {topic_id}",
                )
            )
        action_topics[action] = topic_id
    return action_topics


def _validate_action_topics_coverage(
    *,
    map_rel: str,
    action_topics: dict[str, str],
    issues: list[ValidationIssue],
) -> None:
    from tet4d.engine.ui_logic.keybindings_catalog import binding_action_ids

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

    payloads = _load_help_payloads(
        topics_rel=topics_rel, map_rel=map_rel, issues=issues
    )
    if payloads is None:
        return issues
    topics_payload, map_payload = payloads

    topic_lanes = _collect_topic_lanes(
        topics_payload, topics_rel=topics_rel, issues=issues
    )
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
    from tet4d.engine.ui_logic.menu_graph_linter import lint_menu_graph

    issues: list[ValidationIssue] = []
    for issue in lint_menu_graph():
        issues.append(ValidationIssue("menu_graph", issue.message))
    return issues


def _validate_canonical_candidates(
    manifest: dict[str, object],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    candidates = manifest.get("canonical_candidates", [])
    if not isinstance(candidates, list):
        return [ValidationIssue("schema", "'canonical_candidates' must be a list")]

    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, dict):
            issues.append(
                ValidationIssue(
                    "schema", f"canonical_candidates[{index}] must be an object"
                )
            )
            continue
        name = item.get("name")
        status = item.get("status")
        paths = item.get("paths", [])
        if not isinstance(name, str) or not name:
            issues.append(
                ValidationIssue(
                    "schema", f"canonical_candidates[{index}].name must be a string"
                )
            )
        if not isinstance(status, str) or status not in {"planned", "connected"}:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"canonical_candidates[{index}].status must be 'planned' or 'connected'",
                )
            )
        if not isinstance(paths, list) or any(
            not isinstance(path, str) for path in paths
        ):
            issues.append(
                ValidationIssue(
                    "schema", f"canonical_candidates[{index}].paths must be a list[str]"
                )
            )
            continue
        for rel in paths:
            path = PROJECT_ROOT / rel
            if not path.exists():
                issues.append(
                    ValidationIssue(
                        "missing", f"canonical candidate path missing: {rel}"
                    )
                )
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
            issues.append(
                ValidationIssue("missing", f"content rule file does not exist: {rel}")
            )
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


def _validate_backlog_id_uniqueness() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = "docs/BACKLOG.md"
    path = PROJECT_ROOT / rel
    if not path.exists():
        issues.append(ValidationIssue("missing", f"missing required path: {rel}"))
        return issues

    text = path.read_text(encoding="utf-8")
    ids = re.findall(r"\[(BKL-[A-Z0-9-]+)\]", text)
    seen: dict[str, int] = {}
    duplicates: dict[str, int] = {}
    for backlog_id in ids:
        seen[backlog_id] = seen.get(backlog_id, 0) + 1
        if seen[backlog_id] > 1:
            duplicates[backlog_id] = seen[backlog_id]
    for backlog_id in sorted(duplicates):
        issues.append(
            ValidationIssue(
                "duplicate",
                f"{rel} has duplicated backlog id {backlog_id} "
                f"({duplicates[backlog_id]} occurrences)",
            )
        )
    return issues


def _validate_context_entry(
    idx: int, raw_context: object, issues: list[ValidationIssue], seen_ids: set[str]
) -> None:
    if not isinstance(raw_context, dict):
        issues.append(ValidationIssue("schema", f"contexts[{idx}] must be an object"))
        return
    context_id = raw_context.get("id")
    if not isinstance(context_id, str) or context_id not in ALLOWED_CONTEXT_IDS:
        issues.append(
            ValidationIssue(
                "schema",
                f"contexts[{idx}].id must be one of {sorted(ALLOWED_CONTEXT_IDS)}",
            )
        )
        return
    if context_id in seen_ids:
        issues.append(
            ValidationIssue("duplicate", f"duplicate context id: {context_id}")
        )
    seen_ids.add(context_id)

    for field_name in ("include_globs", "exclude_globs"):
        value = raw_context.get(field_name)
        if not isinstance(value, list) or any(
            not isinstance(token, str) for token in value
        ):
            issues.append(
                ValidationIssue(
                    "schema", f"contexts[{idx}].{field_name} must be a list[str]"
                )
            )
    priority = raw_context.get("priority")
    if isinstance(priority, bool) or not isinstance(priority, int) or priority < 1:
        issues.append(
            ValidationIssue(
                "schema", f"contexts[{idx}].priority must be an integer >= 1"
            )
        )
    tool_required = raw_context.get("tool_required", False)
    if not isinstance(tool_required, bool):
        issues.append(
            ValidationIssue(
                "schema", f"contexts[{idx}].tool_required must be a boolean"
            )
        )
    tool_hints = raw_context.get("tool_hints", [])
    if not isinstance(tool_hints, list) or any(
        not isinstance(hint, str) for hint in tool_hints
    ):
        issues.append(
            ValidationIssue("schema", f"contexts[{idx}].tool_hints must be list[str]")
        )


def _collect_context_router_ids(
    payload: dict[str, object], issues: list[ValidationIssue]
) -> set[str]:
    contexts = payload.get("contexts")
    if not isinstance(contexts, list) or not contexts:
        issues.append(
            ValidationIssue(
                "schema", "context_router_manifest.contexts must be a non-empty list"
            )
        )
        return set()
    seen_ids: set[str] = set()
    for idx, raw_context in enumerate(contexts, start=1):
        _validate_context_entry(idx, raw_context, issues, seen_ids)
    return seen_ids


def _validate_context_router_rule(
    idx: int,
    raw_rule: object,
    known_context_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    if not isinstance(raw_rule, dict):
        issues.append(
            ValidationIssue("schema", f"routing_rules[{idx}] must be an object")
        )
        return
    tags = raw_rule.get("when_task_tags_any")
    if (
        not isinstance(tags, list)
        or not tags
        or any(not isinstance(tag, str) for tag in tags)
    ):
        issues.append(
            ValidationIssue(
                "schema",
                f"routing_rules[{idx}].when_task_tags_any must be a non-empty list[str]",
            )
        )
    include_contexts = raw_rule.get("include_contexts_ordered")
    if (
        not isinstance(include_contexts, list)
        or not include_contexts
        or any(not isinstance(context_id, str) for context_id in include_contexts)
    ):
        issues.append(
            ValidationIssue(
                "schema",
                f"routing_rules[{idx}].include_contexts_ordered must be a non-empty list[str]",
            )
        )
        return
    unknown = [
        context_id
        for context_id in include_contexts
        if context_id not in known_context_ids
    ]
    if unknown:
        issues.append(
            ValidationIssue(
                "schema",
                f"routing_rules[{idx}] references unknown contexts: {', '.join(sorted(set(unknown)))}",
            )
        )


def _validate_context_router_rules(
    payload: dict[str, object],
    *,
    known_context_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    routing_rules = payload.get("routing_rules")
    if not isinstance(routing_rules, list) or not routing_rules:
        issues.append(
            ValidationIssue(
                "schema",
                "context_router_manifest.routing_rules must be a non-empty list",
            )
        )
        return
    for idx, raw_rule in enumerate(routing_rules, start=1):
        _validate_context_router_rule(idx, raw_rule, known_context_ids, issues)


def _validate_context_router_manifest() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = "config/project/policy/manifests/context_router_manifest.json"
    path = CONTEXT_ROUTER_PATH
    if not path.exists():
        return [ValidationIssue("missing", f"missing required path: {rel}")]
    payload = _load_json_payload(path, rel, issues)
    if not isinstance(payload, dict):
        return issues
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version.strip():
        issues.append(
            ValidationIssue("schema", "context_router_manifest.schema_version required")
        )
    context_ids = _collect_context_router_ids(payload, issues)
    _validate_context_router_rules(
        payload, known_context_ids=context_ids, issues=issues
    )
    return issues


def _as_string_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or any(
        not isinstance(token, str) for token in value
    ):
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
        return ValidationIssue(
            "schema", f"content_rules[{index}].file must be a string"
        )

    tokens = _as_string_list(rule.get("must_contain", []))
    if tokens is None:
        return ValidationIssue(
            "schema", f"content_rules[{index}].must_contain must be a list[str]"
        )

    forbidden_tokens = _as_string_list(rule.get("must_not_contain", []))
    if forbidden_tokens is None:
        return ValidationIssue(
            "schema", f"content_rules[{index}].must_not_contain must be a list[str]"
        )

    required_regexes = _as_string_list(rule.get("must_match_regex", []))
    if required_regexes is None:
        return ValidationIssue(
            "schema", f"content_rules[{index}].must_match_regex must be a list[str]"
        )

    forbidden_regexes = _as_string_list(rule.get("must_not_match_regex", []))
    if forbidden_regexes is None:
        return ValidationIssue(
            "schema", f"content_rules[{index}].must_not_match_regex must be a list[str]"
        )

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
            issues.append(
                ValidationIssue("content", f"{rel} contains forbidden token: {token!r}")
            )
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
            issues.append(
                ValidationIssue("content", f"{rel} missing regex match: {pattern!r}")
            )

    for pattern in forbidden_regexes:
        compiled = _compile_pattern(rel, pattern, issues)
        if compiled is None:
            continue
        if compiled.search(text) is not None:
            issues.append(
                ValidationIssue(
                    "content", f"{rel} matched forbidden regex: {pattern!r}"
                )
            )


def _compile_pattern(
    rel: str, pattern: str, issues: list[ValidationIssue]
) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern, flags=re.MULTILINE)
    except re.error as exc:
        issues.append(
            ValidationIssue(
                "schema",
                f"invalid regex in content rule for {rel}: {pattern!r} ({exc})",
            )
        )
        return None


def validate_manifest() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    pack = _load_pack()
    issues.extend(_validate_pack_components(pack))
    component_payloads = _load_component_payloads(pack, issues)
    issues.extend(_validate_pack_constraints(pack, component_payloads))

    manifest = _load_manifest()
    issues.extend(_validate_required_paths(manifest))
    issues.extend(_validate_required_json_files(manifest))
    issues.extend(_validate_help_topic_contract(manifest))
    issues.extend(_validate_menu_graph_contract())
    issues.extend(_validate_canonical_candidates(manifest))
    issues.extend(_validate_content_rules(manifest))
    issues.extend(_validate_backlog_id_uniqueness())
    issues.extend(_validate_context_router_manifest())
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
