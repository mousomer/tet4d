from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
GOVERNANCE_PATH = PROJECT_ROOT / "config/project/policy/governance.json"
CODE_RULES_PATH = PROJECT_ROOT / "config/project/policy/code_rules.json"
MANIFEST_PATH = (
    PROJECT_ROOT / "config/project/policy/manifests/canonical_maintenance.json"
)
POLICY_INDEX_PATH = PROJECT_ROOT / "docs/policies/INDEX.md"
POLICY_MANIFEST_DIR = PROJECT_ROOT / "config/project/policy/manifests"
MENU_STRUCTURE_PATH = PROJECT_ROOT / "config/menu/structure.json"
POLICY_LITERAL_SAFETY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"/" + r"Users/"), "unix_users_path"),
    (re.compile(r"/" + r"home/"), "unix_home_path"),
    (re.compile(r"[A-Za-z]:" + r"\\"), "windows_drive_prefix"),
)
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    message: str


def _load_json_payload(
    path: Path, rel: str, issues: list[ValidationIssue]
) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        issues.append(ValidationIssue("json", f"{rel} is not valid JSON: {exc}"))
        return None


def _load_manifest() -> dict[str, object]:
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing manifest: {MANIFEST_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {MANIFEST_PATH}: {exc}") from exc
    return payload


def _load_governance(issues: list[ValidationIssue]) -> dict[str, object] | None:
    rel = "config/project/policy/governance.json"
    payload = _load_json_payload(GOVERNANCE_PATH, rel, issues)
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
    return payload


def _load_code_rules(issues: list[ValidationIssue]) -> dict[str, object] | None:
    rel = "config/project/policy/code_rules.json"
    payload = _load_json_payload(CODE_RULES_PATH, rel, issues)
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
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


def _is_non_empty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_str_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(token, str) and bool(token.strip()) for token in value)
    )


def _validate_contributor_directive_entry(
    *,
    rel: str,
    idx: int,
    raw: object,
    seen_ids: set[str],
    issues: list[ValidationIssue],
) -> None:
    required_fields = ("id", "category", "statement", "source_docs", "enforced_by")
    if not isinstance(raw, dict):
        issues.append(
            ValidationIssue("schema", f"{rel}.directives[{idx}] must be an object")
        )
        return

    for field in required_fields:
        if field not in raw:
            issues.append(
                ValidationIssue(
                    "schema", f"{rel}.directives[{idx}] missing field: {field}"
                )
            )

    directive_id = raw.get("id")
    if not _is_non_empty_str(directive_id):
        issues.append(
            ValidationIssue(
                "schema", f"{rel}.directives[{idx}].id must be a non-empty string"
            )
        )
    elif directive_id in seen_ids:
        issues.append(
            ValidationIssue(
                "duplicate", f"{rel} duplicate directive id: {directive_id}"
            )
        )
    else:
        seen_ids.add(directive_id)

    for field in ("category", "statement"):
        if not _is_non_empty_str(raw.get(field)):
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{rel}.directives[{idx}].{field} must be a non-empty string",
                )
            )

    for field in ("source_docs", "enforced_by"):
        if not _is_non_empty_str_list(raw.get(field)):
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{rel}.directives[{idx}].{field} must be a non-empty list[str]",
                )
            )


def _validate_governance_directives() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = "config/project/policy/governance.json"
    payload = _load_json_payload(GOVERNANCE_PATH, rel, issues)
    if not isinstance(payload, dict):
        return issues

    directives_block = payload.get("contributor_directives")
    if not isinstance(directives_block, dict):
        issues.append(
            ValidationIssue("schema", f"{rel}.contributor_directives must be an object")
        )
        return issues

    directives = directives_block.get("directives")
    if not isinstance(directives, list) or not directives:
        issues.append(
            ValidationIssue(
                "schema",
                f"{rel}.contributor_directives.directives must be a non-empty list",
            )
        )
        return issues

    seen_ids: set[str] = set()
    for idx, raw in enumerate(directives, start=1):
        _validate_contributor_directive_entry(
            rel=f"{rel}.contributor_directives",
            idx=idx,
            raw=raw,
            seen_ids=seen_ids,
            issues=issues,
        )
    return issues


def _validate_policy_index_sync() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    governance = _load_governance(issues)
    if governance is None:
        return issues

    index_rel = "docs/policies/INDEX.md"
    if not POLICY_INDEX_PATH.exists():
        return [ValidationIssue("missing", f"missing required path: {index_rel}")]
    index_text = POLICY_INDEX_PATH.read_text(encoding="utf-8")

    required_tokens = [
        "config/project/policy/governance.json",
        "config/project/policy/code_rules.json",
        "config/project/policy/manifests/canonical_maintenance.json",
        "config/project/policy/manifests/secret_scan.json",
        "docs/policies/CI_COMPLIANCE_RUNBOOK.md",
        "docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md",
    ]
    contracts = governance.get("contracts")
    if isinstance(contracts, dict):
        required_tokens.extend(
            value for value in contracts.values() if isinstance(value, str)
        )

    for token in sorted(set(required_tokens)):
        if token not in index_text:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{index_rel} missing contract path token: {token}",
                )
            )
    return issues


def _iter_string_nodes(
    value: object, *, path_prefix: str = ""
) -> list[tuple[str, str]]:
    nodes: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_prefix = f"{path_prefix}.{key_text}" if path_prefix else key_text
            nodes.extend(_iter_string_nodes(nested, path_prefix=nested_prefix))
        return nodes
    if isinstance(value, list):
        for idx, nested in enumerate(value):
            nested_prefix = f"{path_prefix}[{idx}]"
            nodes.extend(_iter_string_nodes(nested, path_prefix=nested_prefix))
        return nodes
    if isinstance(value, str):
        nodes.append((path_prefix or "$", value))
    return nodes


def _policy_manifest_rel_paths() -> list[str]:
    rels = [
        "config/project/policy/governance.json",
        "config/project/policy/code_rules.json",
    ]
    if POLICY_MANIFEST_DIR.exists():
        rels.extend(
            sorted(
                f"config/project/policy/manifests/{path.name}"
                for path in POLICY_MANIFEST_DIR.glob("*.json")
            )
        )
    return rels


def _validate_policy_manifest_string_safety() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _policy_manifest_rel_paths():
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        payload = _load_json_payload(path, rel, issues)
        if payload is None:
            continue
        for key_path, text in _iter_string_nodes(payload):
            for pattern, label in POLICY_LITERAL_SAFETY_PATTERNS:
                if pattern.search(text) is None:
                    continue
                issues.append(
                    ValidationIssue(
                        "safety",
                        (
                            f"{rel}:{key_path} includes path-like literal "
                            f"'{label}' that can break sanitation gates"
                        ),
                    )
                )
                break
    return issues


def _settings_hub_row_keys(menu_payload: dict[str, object]) -> set[str]:
    keys: set[str] = set()
    layout = menu_payload.get("settings_hub_layout_rows")
    if not isinstance(layout, list):
        return keys
    for entry in layout:
        if not isinstance(entry, dict):
            continue
        row_key = entry.get("row_key")
        if isinstance(row_key, str) and row_key:
            keys.add(row_key)
    return keys


def _settings_hub_header_labels(menu_payload: dict[str, object]) -> set[str]:
    labels: set[str] = set()
    layout = menu_payload.get("settings_hub_layout_rows")
    if not isinstance(layout, list):
        return labels
    for entry in layout:
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") != "header":
            continue
        label = entry.get("label")
        if isinstance(label, str) and label:
            labels.add(label)
    return labels


def _launcher_settings_action_ids(menu_payload: dict[str, object]) -> set[str]:
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        return set()
    launcher_settings = menus.get("launcher_settings_root")
    if not isinstance(launcher_settings, dict):
        return set()
    items = launcher_settings.get("items")
    if not isinstance(items, list):
        return set()
    action_ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "action":
            continue
        action_id = item.get("action_id")
        if isinstance(action_id, str) and action_id:
            action_ids.add(action_id)
    return action_ids


def _setup_field_attrs(menu_payload: dict[str, object]) -> set[str]:
    attrs: set[str] = set()
    setup_fields = menu_payload.get("setup_fields")
    if not isinstance(setup_fields, dict):
        return attrs
    for fields in setup_fields.values():
        if not isinstance(fields, list):
            continue
        for field in fields:
            if not isinstance(field, dict):
                continue
            attr = field.get("attr")
            if isinstance(attr, str) and attr:
                attrs.add(attr)
    return attrs


def _validate_menu_simplification_rule() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    governance = _load_governance(issues)
    if governance is None:
        return issues

    rule = governance.get("menu_simplification_manifest_rule")
    if not isinstance(rule, dict):
        issues.append(
            ValidationIssue(
                "schema",
                "config/project/policy/governance.json.menu_simplification_manifest_rule must be an object",
            )
        )
        return issues

    rule_id = rule.get("rule_id")
    if rule_id != "menu-simplification-common-settings":
        return issues

    menu_rel = "config/menu/structure.json"
    menu_payload = _load_json_payload(MENU_STRUCTURE_PATH, menu_rel, issues)
    if not isinstance(menu_payload, dict):
        return issues

    required_shared_row_keys = {
        "game_seed",
        "game_random_mode",
        "rotation_animation_mode",
        "kick_level_index",
        "rotation_animation_duration_ms_2d",
        "rotation_animation_duration_ms_nd",
        "translation_animation_duration_ms",
        "auto_speedup_enabled",
        "lines_per_level",
        "topology_cache_measure",
        "topology_cache_clear",
    }
    hub_keys = _settings_hub_row_keys(menu_payload)
    setup_attrs = _setup_field_attrs(menu_payload)

    for row_key in sorted(required_shared_row_keys):
        if row_key not in hub_keys:
            issues.append(
                ValidationIssue(
                    "content",
                    (
                        f"{menu_rel} missing shared gameplay settings row: {row_key} "
                        f"(required by menu_simplification_manifest_rule)"
                    ),
                )
            )
        if row_key in setup_attrs:
            issues.append(
                ValidationIssue(
                    "content",
                    (
                        f"{menu_rel} setup_fields must not contain shared gameplay row: {row_key} "
                        f"(must be centralized in settings hub)"
                    ),
                )
            )
    return issues


def _menu_structure_banned_literals() -> tuple[tuple[Path, str, str], ...]:
    return (
        (
            PROJECT_ROOT / "cli/front.py",
            "_SETTINGS_HUB_ROUTE =",
            "cli/front.py must not hardcode launcher settings routes; use config/menu/structure.json",
        ),
        (
            PROJECT_ROOT / "src/tet4d/ui/pygame/launch/settings_hub_model.py",
            "_CATEGORY_ID_BY_HEADER_LABEL =",
            "settings_hub_model.py must not hardcode settings section header ownership; use config/menu/structure.json",
        ),
        (
            PROJECT_ROOT / "src/tet4d/ui/pygame/launch/settings_hub_model.py",
            "_CATEGORY_IDS_BY_FILTER =",
            "settings_hub_model.py must not hardcode settings section filters; use config/menu/structure.json",
        ),
        (
            PROJECT_ROOT / "src/tet4d/ui/pygame/launch/settings_hub_model.py",
            "_FOOTER_ROW_KEYS =",
            "settings_hub_model.py must not hardcode settings footer row ownership; use config/menu/structure.json",
        ),
        (
            PROJECT_ROOT / "src/tet4d/ui/pygame/launch/settings_hub_model.py",
            "_TOP_LEVEL_HEADER_LABELS =",
            "settings_hub_model.py must not hardcode top-level settings headers; use config/menu/structure.json",
        ),
    )


def _validate_settings_section_membership(
    *,
    menu_rel: str,
    settings_sections: dict[str, object],
    hub_headers: set[str],
    hub_row_keys: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for section_id, raw_section in settings_sections.items():
        if not isinstance(raw_section, dict):
            continue
        headers = raw_section.get("headers")
        if isinstance(headers, list):
            for header in headers:
                if isinstance(header, str) and header and header not in hub_headers:
                    issues.append(
                        ValidationIssue(
                            "content",
                            f"{menu_rel} settings_sections.{section_id}.headers references unknown hub header: {header}",
                        )
                    )
        row_keys = raw_section.get("row_keys")
        if isinstance(row_keys, list):
            for row_key in row_keys:
                if isinstance(row_key, str) and row_key and row_key not in hub_row_keys:
                    issues.append(
                        ValidationIssue(
                            "content",
                            f"{menu_rel} settings_sections.{section_id}.row_keys references unknown hub row: {row_key}",
                        )
                    )
    return issues


def _validate_launcher_settings_routes_contract(
    *,
    menu_rel: str,
    settings_sections: dict[str, object],
    launcher_settings_routes: dict[str, object],
    launcher_settings_action_ids: set[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for action_id, raw_route in launcher_settings_routes.items():
        if action_id not in launcher_settings_action_ids:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{menu_rel} launcher_settings_routes.{action_id} must match an action in launcher_settings_root",
                )
            )
            continue
        if not isinstance(raw_route, dict):
            continue
        section_id = raw_route.get("section_id")
        if not isinstance(section_id, str) or section_id not in settings_sections:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{menu_rel} launcher_settings_routes.{action_id}.section_id must reference an existing settings section",
                )
            )
            continue
        initial_row_key = raw_route.get("initial_row_key")
        section = settings_sections.get(section_id)
        section_row_keys = (
            set(section.get("row_keys", [])) if isinstance(section, dict) else set()
        )
        if (
            not isinstance(initial_row_key, str)
            or initial_row_key not in section_row_keys
        ):
            issues.append(
                ValidationIssue(
                    "content",
                    f"{menu_rel} launcher_settings_routes.{action_id}.initial_row_key must belong to section {section_id}",
                )
            )
    return issues


def _validate_menu_structure_banned_literals() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, literal, message in _menu_structure_banned_literals():
        text = path.read_text(encoding="utf-8")
        if literal in text:
            issues.append(ValidationIssue("drift", message))
    return issues


def _validate_menu_structure_single_source_of_truth() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    menu_rel = "config/menu/structure.json"
    menu_payload = _load_json_payload(MENU_STRUCTURE_PATH, menu_rel, issues)
    if not isinstance(menu_payload, dict):
        return issues

    settings_sections = menu_payload.get("settings_sections")
    if not isinstance(settings_sections, dict) or not settings_sections:
        issues.append(
            ValidationIssue(
                "schema",
                f"{menu_rel} must define non-empty settings_sections",
            )
        )

    launcher_settings_routes = menu_payload.get("launcher_settings_routes")
    if not isinstance(launcher_settings_routes, dict) or not launcher_settings_routes:
        issues.append(
            ValidationIssue(
                "schema",
                f"{menu_rel} must define non-empty launcher_settings_routes",
            )
        )

    hub_headers = _settings_hub_header_labels(menu_payload)
    hub_row_keys = _settings_hub_row_keys(menu_payload)
    launcher_settings_action_ids = _launcher_settings_action_ids(menu_payload)
    if isinstance(settings_sections, dict):
        issues.extend(
            _validate_settings_section_membership(
                menu_rel=menu_rel,
                settings_sections=settings_sections,
                hub_headers=hub_headers,
                hub_row_keys=hub_row_keys,
            )
        )
    if isinstance(launcher_settings_routes, dict) and isinstance(
        settings_sections, dict
    ):
        issues.extend(
            _validate_launcher_settings_routes_contract(
                menu_rel=menu_rel,
                settings_sections=settings_sections,
                launcher_settings_routes=launcher_settings_routes,
                launcher_settings_action_ids=launcher_settings_action_ids,
            )
        )
    issues.extend(_validate_menu_structure_banned_literals())
    return issues


def _validate_keybinding_single_source_of_truth() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    try:
        from tet4d.engine.runtime.keybinding_store import (
            load_keybinding_defaults_payload,
        )
        from tet4d.engine.ui_logic.keybindings_catalog import binding_action_ids
    except Exception as exc:
        issues.append(
            ValidationIssue(
                "import",
                f"failed loading keybinding contract validators: {exc}",
            )
        )
        return issues

    try:
        load_keybinding_defaults_payload()
    except Exception as exc:
        issues.append(
            ValidationIssue(
                "content",
                f"config/keybindings/defaults.json must satisfy the keybinding catalog contract: {exc}",
            )
        )

    try:
        binding_action_ids()
    except Exception as exc:
        issues.append(
            ValidationIssue(
                "content",
                f"config/keybindings/catalog.json must be a valid keybinding catalog: {exc}",
            )
        )
    return issues


def validate_manifest() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    manifest = _load_manifest()
    issues.extend(_validate_required_paths(manifest))
    issues.extend(_validate_required_json_files(manifest))
    issues.extend(_validate_help_topic_contract(manifest))
    issues.extend(_validate_menu_graph_contract())
    issues.extend(_validate_canonical_candidates(manifest))
    issues.extend(_validate_content_rules(manifest))
    issues.extend(_validate_backlog_id_uniqueness())
    issues.extend(_validate_governance_directives())
    issues.extend(_validate_policy_index_sync())
    issues.extend(_validate_policy_manifest_string_safety())
    issues.extend(_validate_menu_simplification_rule())
    issues.extend(_validate_menu_structure_single_source_of_truth())
    issues.extend(_validate_keybinding_single_source_of_truth())
    _load_code_rules(issues)
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
