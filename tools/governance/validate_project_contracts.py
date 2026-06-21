from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
POLICY_PACK_REL = "config/project/policy_pack.json"
POLICY_PACK_PATH = PROJECT_ROOT / POLICY_PACK_REL
POLICY_INDEX_PATH = PROJECT_ROOT / "docs/policies/INDEX.md"
POLICY_MANIFEST_DIR = PROJECT_ROOT / "config/project/policy/manifests"
MENU_STRUCTURE_PATH = PROJECT_ROOT / "config/menu/structure.json"
GOVERNANCE_ROUTING_REQUIRED_PATHS: tuple[str, ...] = (
    "AGENTS.md",
    "docs/governance/README.md",
    "docs/governance/codex_policy.md",
    "docs/governance/godot_cpp_policy.md",
    "docs/governance/config_policy.md",
    "docs/governance/secrets_policy.md",
    "docs/governance/testing_policy.md",
    "docs/governance/review_checklist.md",
    "docs/architecture/authority_map.md",
    "docs/architecture/utility_index.md",
    "docs/architecture/trace_metadata_identity_digest_parity.md",
    "docs/architecture/parity_evidence_review_and_third_slice_selection.md",
    "godot/AGENTS.md",
)
AGENTS_LINE_LIMITS: tuple[tuple[str, int], ...] = (
    ("AGENTS.md", 140),
    ("godot/AGENTS.md", 80),
    ("native/AGENTS.md", 80),
)
NATIVE_CPP_EXTENSIONS = {".cpp", ".hpp", ".h", ".cc", ".cxx", ".hh", ".hxx"}
POLICY_LITERAL_SAFETY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"/" + r"Users/"), "unix_users_path"),
    (re.compile(r"/" + r"home/"), "unix_home_path"),
    (re.compile(r"[A-Za-z]:" + r"\\"), "windows_drive_prefix"),
)
GOVERNANCE_LOCAL_PATH_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile("/" + "Users/"), "macOS user path"),
    (re.compile("C:" + r"\\Users\\", flags=re.IGNORECASE), "Windows user path"),
    (re.compile("/" + r"home/[A-Za-z0-9._-]+/"), "Linux user path"),
)
SECRET_PREFIX_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"BEGIN (?:RSA |OPENSSH )?PRIVATE KEY"), "private key block"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bghp_[A-Za-z0-9_]{20,}\b"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "GitHub fine-grained token"),
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "API key token"),
    (re.compile(r"\bxoxb-[A-Za-z0-9-]{10,}\b"), "Slack bot token"),
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(password|api_key|token|secret)\b\s*[:=]\s*([^#\s].*)$"
)
AUTHORITY_INVERSION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"\b(godot|c\+\+|gdextension)\b.{0,40}\bsemantic oracle\b",
            flags=re.IGNORECASE,
        ),
        "non-Python semantic oracle claim",
    ),
    (
        re.compile(
            r"\b(godot|c\+\+|gdextension)\b.{0,40}\bsource of truth\b",
            flags=re.IGNORECASE,
        ),
        "non-Python source-of-truth claim",
    ),
    (
        re.compile(
            r"\b(godot|c\+\+|gdextension)\b.{0,40}\breplaces?\b.{0,20}\bpython\b",
            flags=re.IGNORECASE,
        ),
        "non-Python replacement claim",
    ),
    (
        re.compile(
            r"\b(godot|c\+\+|gdextension)\b.{0,40}\bsupersedes?\b.{0,20}\bpython\b",
            flags=re.IGNORECASE,
        ),
        "non-Python supersession claim",
    ),
)
PARITY_DANGEROUS_PHRASES: tuple[tuple[str, str], ...] = (
    ("c++ is the semantic oracle", "C++ semantic oracle claim"),
    ("godot is the semantic oracle", "Godot semantic oracle claim"),
    ("visual correctness is parity", "visual parity shortcut"),
    ("godot display proves semantics", "Godot display semantic-proof shortcut"),
)
PLACEHOLDER_SECRET_VALUES = {
    "<redacted>",
    "redacted",
    "example",
    "placeholder",
    "your_token_here",
    "your_api_key_here",
    "changeme",
    "change_me",
    "dummy",
}
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


@dataclass(frozen=True)
class ValidationIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class MenuStructureContract:
    required_menus: tuple[str, ...]
    required_submenu_labels: tuple[tuple[str, set[str]], ...]
    required_item_labels: tuple[tuple[str, set[str]], ...]
    required_item_types: set[str]
    banned_literal_rules: tuple[tuple[Path, str, str], ...]


def _git_tracked_paths(issues: list[ValidationIssue]) -> set[str] | None:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown git error"
        issues.append(
            ValidationIssue(
                "git",
                f"git ls-files failed while checking required paths: {detail}",
            )
        )
        return None
    return {rel for rel in result.stdout.split("\0") if rel}


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
        payload = json.loads(POLICY_PACK_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing policy pack: {POLICY_PACK_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {POLICY_PACK_PATH}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{POLICY_PACK_REL} must be a JSON object")
    manifest = payload.get("maintenance_contract")
    if not isinstance(manifest, dict):
        raise SystemExit(f"{POLICY_PACK_REL} missing maintenance_contract object")
    return manifest


def _load_policy_pack_payload(
    issues: list[ValidationIssue],
) -> dict[str, object] | None:
    payload = _load_json_payload(POLICY_PACK_PATH, POLICY_PACK_REL, issues)
    if not isinstance(payload, dict):
        issues.append(
            ValidationIssue("json", f"{POLICY_PACK_REL} must be a JSON object")
        )
        return None
    return payload


def _load_governance(issues: list[ValidationIssue]) -> dict[str, object] | None:
    rel = f"{POLICY_PACK_REL}.governance"
    policy_pack = _load_policy_pack_payload(issues)
    if policy_pack is None:
        return None
    payload = policy_pack.get("governance")
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
    return payload


def _load_governance_subsection(
    issues: list[ValidationIssue], key: str
) -> dict[str, object] | None:
    rel = f"{POLICY_PACK_REL}.governance.{key}"
    governance = _load_governance(issues)
    if governance is None:
        return None
    payload = governance.get(key)
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
    return payload


def _load_code_rules(issues: list[ValidationIssue]) -> dict[str, object] | None:
    rel = f"{POLICY_PACK_REL}.code_rules"
    policy_pack = _load_policy_pack_payload(issues)
    if policy_pack is None:
        return None
    payload = policy_pack.get("code_rules")
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
    return payload


def _load_deprecated_authorities(
    issues: list[ValidationIssue],
) -> dict[str, object] | None:
    rel = f"{POLICY_PACK_REL}.deprecated_authorities"
    policy_pack = _load_policy_pack_payload(issues)
    if policy_pack is None:
        return None
    payload = policy_pack.get("deprecated_authorities")
    if not isinstance(payload, dict):
        issues.append(ValidationIssue("json", f"{rel} must be a JSON object"))
        return None
    return payload


def _validate_required_paths(manifest: dict[str, object]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_paths = manifest.get("required_paths", {})
    if not isinstance(required_paths, dict):
        return [ValidationIssue("schema", "'required_paths' must be an object")]

    tracked_paths = _git_tracked_paths(issues)
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
                continue
            if (
                tracked_paths is not None
                and path.is_file()
                and rel not in tracked_paths
            ):
                issues.append(
                    ValidationIssue(
                        "git", f"required path is not tracked in git: {rel}"
                    )
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
    rel = f"{POLICY_PACK_REL}.governance"
    policy_pack = _load_policy_pack_payload(issues)
    if policy_pack is None:
        return issues
    payload = policy_pack.get("governance")
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
    policy_index_contract = _load_governance_subsection(issues, "policy_index_contract")
    if governance is None or policy_index_contract is None:
        return issues

    index_rel = "docs/policies/INDEX.md"
    if not POLICY_INDEX_PATH.exists():
        return [ValidationIssue("missing", f"missing required path: {index_rel}")]
    index_text = POLICY_INDEX_PATH.read_text(encoding="utf-8")

    required_tokens = _as_string_list(policy_index_contract.get("required_tokens", []))
    if required_tokens is None:
        issues.append(
            ValidationIssue(
                "schema",
                (
                    f"{POLICY_PACK_REL}.governance.policy_index_contract.required_tokens "
                    "must be a list[str]"
                ),
            )
        )
        return issues
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
    rels = [POLICY_PACK_REL]
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


def _validate_blocked_authority_paths(
    blocked_paths: object,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not isinstance(blocked_paths, list):
        return [
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.deprecated_authorities.blocked_paths must be a list",
            )
        ]

    for rel in blocked_paths:
        if not isinstance(rel, str):
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{POLICY_PACK_REL}.deprecated_authorities.blocked_paths includes non-string entry",
                )
            )
            continue
        if (PROJECT_ROOT / rel).exists():
            issues.append(
                ValidationIssue(
                    "deprecated", f"deprecated authority path present: {rel}"
                )
            )
    return issues


def _validate_reference_check(
    *, idx: int, raw: object, issues: list[ValidationIssue]
) -> None:
    if not isinstance(raw, dict):
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.deprecated_authorities.reference_checks[{idx}] must be an object",
            )
        )
        return
    rel = raw.get("file")
    if not isinstance(rel, str) or not rel.strip():
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.deprecated_authorities.reference_checks[{idx}].file must be a non-empty string",
            )
        )
        return
    tokens = raw.get("must_not_contain", [])
    if not isinstance(tokens, list) or any(
        not isinstance(token, str) for token in tokens
    ):
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.deprecated_authorities.reference_checks[{idx}].must_not_contain must be list[str]",
            )
        )
        return
    path = PROJECT_ROOT / rel
    if not path.exists():
        issues.append(ValidationIssue("missing", f"missing required path: {rel}"))
        return
    text = path.read_text(encoding="utf-8")
    for token in tokens:
        if token in text:
            issues.append(
                ValidationIssue(
                    "deprecated",
                    f"{rel} still references deprecated authority token: {token}",
                )
            )


def _validate_deprecated_authorities() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    deprecated = _load_deprecated_authorities(issues)
    if deprecated is None:
        return issues

    issues.extend(
        _validate_blocked_authority_paths(deprecated.get("blocked_paths", []))
    )

    reference_checks = deprecated.get("reference_checks", [])
    if not isinstance(reference_checks, list):
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.deprecated_authorities.reference_checks must be a list",
            )
        )
        return issues

    for idx, raw in enumerate(reference_checks, start=1):
        _validate_reference_check(idx=idx, raw=raw, issues=issues)
    return issues


def _menu_definition(
    menu_payload: dict[str, object], menu_id: str
) -> dict[str, object] | None:
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        return None
    menu = menus.get(menu_id)
    return menu if isinstance(menu, dict) else None


def _menu_items(
    menu_payload: dict[str, object], menu_id: str
) -> list[dict[str, object]]:
    menu = _menu_definition(menu_payload, menu_id)
    if not isinstance(menu, dict):
        return []
    items = menu.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _settings_menu_setting_ids(menu_payload: dict[str, object]) -> set[str]:
    setting_ids: set[str] = set()
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        return setting_ids
    for menu in menus.values():
        if not isinstance(menu, dict):
            continue
        items = menu.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", "")).strip().lower()
            if item_type not in {"toggle", "selector", "slider", "stepper"}:
                continue
            setting_id = item.get("setting_id")
            if isinstance(setting_id, str) and setting_id:
                setting_ids.add(setting_id)
    return setting_ids


def _menu_action_ids(menu_payload: dict[str, object]) -> set[str]:
    action_ids: set[str] = set()
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        return action_ids
    for menu in menus.values():
        if not isinstance(menu, dict):
            continue
        items = menu.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("type", "")).strip().lower() != "action":
                continue
            action_id = str(item.get("action_id", "")).strip().lower()
            if action_id:
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
                f"{POLICY_PACK_REL}.governance.menu_simplification_manifest_rule must be an object",
            )
        )
        return issues

    rule_id = rule.get("rule_id")
    if rule_id != "menu-simplification-common-settings":
        return issues

    required_shared_row_keys = _as_string_list(rule.get("required_shared_row_keys", []))
    if not required_shared_row_keys:
        issues.append(
            ValidationIssue(
                "schema",
                (
                    f"{POLICY_PACK_REL}.governance.menu_simplification_manifest_rule."
                    "required_shared_row_keys must be a non-empty list[str]"
                ),
            )
        )
        return issues

    menu_rel = "config/menu/structure.json"
    menu_payload = _load_json_payload(MENU_STRUCTURE_PATH, menu_rel, issues)
    if not isinstance(menu_payload, dict):
        return issues

    settings_keys = _settings_menu_setting_ids(menu_payload)
    action_ids = _menu_action_ids(menu_payload)
    setup_attrs = _setup_field_attrs(menu_payload)

    for row_key in sorted(required_shared_row_keys):
        if row_key not in settings_keys and row_key not in action_ids:
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


def _validate_menu_control_typing() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    contract = _load_governance_subsection(issues, "menu_control_typing_contract")
    if contract is None:
        return issues

    menu_payload = _load_json_payload(
        MENU_STRUCTURE_PATH, "config/menu/structure.json", issues
    )
    if not isinstance(menu_payload, dict):
        issues.append(
            ValidationIssue("json", "config/menu/structure.json must be a JSON object")
        )
        return issues

    semantic_types = set(
        _as_string_list(contract.get("setting_semantic_types", [])) or []
    )
    menu_control_types = set(
        _as_string_list(contract.get("menu_control_types", [])) or []
    )
    setup_control_types = set(
        _as_string_list(contract.get("setup_control_types", [])) or []
    )
    selector_options_key_required = bool(
        contract.get("selector_options_key_required", False)
    )
    allowed_option_sources = set(
        _as_string_list(contract.get("enum_setup_option_source_tokens", [])) or []
    )
    settings_option_labels = menu_payload.get("settings_option_labels")
    if not isinstance(settings_option_labels, dict):
        settings_option_labels = {}

    _validate_menu_item_control_typing(
        menu_payload=menu_payload,
        semantic_types=semantic_types,
        menu_control_types=menu_control_types,
        selector_options_key_required=selector_options_key_required,
        settings_option_labels=settings_option_labels,
        issues=issues,
    )

    setup_fields = menu_payload.get("setup_fields")
    if not isinstance(setup_fields, dict):
        return issues
    _validate_setup_field_control_typing(
        setup_fields=setup_fields,
        semantic_types=semantic_types,
        setup_control_types=setup_control_types,
        allowed_option_sources=allowed_option_sources,
        issues=issues,
    )
    return issues


def _validate_menu_item_control_typing(
    *,
    menu_payload: dict[str, object],
    semantic_types: set[str],
    menu_control_types: set[str],
    selector_options_key_required: bool,
    settings_option_labels: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        return
    for menu_id, raw_menu in menus.items():
        if not isinstance(raw_menu, dict):
            continue
        items = raw_menu.get("items")
        if not isinstance(items, list):
            continue
        for idx, raw_item in enumerate(items):
            if not isinstance(raw_item, dict):
                continue
            item_type = str(raw_item.get("type", "")).strip().lower()
            if item_type not in menu_control_types:
                continue
            _validate_menu_control_item(
                menu_id=menu_id,
                item_index=idx,
                raw_item=raw_item,
                semantic_types=semantic_types,
                selector_options_key_required=selector_options_key_required,
                settings_option_labels=settings_option_labels,
                issues=issues,
            )


def _menu_control_prefix(
    menu_id: str, item_index: int, raw_item: dict[str, object]
) -> str:
    item_id = str(raw_item.get("id", "")).strip().lower()
    prefix = f"menus.{menu_id}.items[{item_index}]"
    if item_id:
        return f"{prefix} ({item_id})"
    return prefix


def _validate_menu_control_storage_type(
    *,
    prefix: str,
    item_type: str,
    semantic_type: str,
    storage_type: str,
    issues: list[ValidationIssue],
) -> None:
    if storage_type in {"int", "float"}:
        if semantic_type not in {"int", "float"}:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type={storage_type} requires semantic_type=int or float",
                )
            )
    elif storage_type == "bool":
        if semantic_type != "bool":
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type=bool requires semantic_type=bool",
                )
            )
    elif storage_type in {"int_index", "string_id"}:
        if semantic_type != "enum":
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type={storage_type} requires semantic_type=enum",
                )
            )

    if item_type in {"slider", "stepper"} and storage_type not in {"int", "float"}:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} {item_type} controls must use storage_type=int or float",
            )
        )
    if item_type == "toggle" and storage_type != "bool":
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} toggle controls must use storage_type=bool",
            )
        )
    if item_type == "selector" and storage_type not in {"int_index", "string_id"}:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} selector controls must use storage_type=string_id or int_index",
            )
        )


def _validate_menu_control_legacy_storage_type(
    *,
    prefix: str,
    semantic_type: str,
    legacy_storage_type: str,
    issues: list[ValidationIssue],
) -> None:
    if legacy_storage_type == "int_bool" and semantic_type != "bool":
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} legacy_storage_type=int_bool requires semantic_type=bool",
            )
        )
    if legacy_storage_type == "int_index" and semantic_type != "enum":
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} legacy_storage_type=int_index requires semantic_type=enum",
            )
        )


def _validate_menu_control_storage_contract(
    *,
    prefix: str,
    item_type: str,
    semantic_type: str,
    raw_item: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    storage_type = str(raw_item.get("storage_type", "")).strip().lower()
    legacy_storage_type = str(raw_item.get("legacy_storage_type", "")).strip().lower()
    legacy_setting_id = str(raw_item.get("legacy_setting_id", "")).strip().lower()
    if legacy_setting_id and not legacy_storage_type:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} legacy_setting_id requires legacy_storage_type",
            )
        )
    if storage_type:
        _validate_menu_control_storage_type(
            prefix=prefix,
            item_type=item_type,
            semantic_type=semantic_type,
            storage_type=storage_type,
            issues=issues,
        )
    if legacy_storage_type:
        _validate_menu_control_legacy_storage_type(
            prefix=prefix,
            semantic_type=semantic_type,
            legacy_storage_type=legacy_storage_type,
            issues=issues,
        )


def _validate_menu_control_item(
    *,
    menu_id: str,
    item_index: int,
    raw_item: dict[str, object],
    semantic_types: set[str],
    selector_options_key_required: bool,
    settings_option_labels: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    prefix = _menu_control_prefix(menu_id, item_index, raw_item)
    item_type = str(raw_item.get("type", "")).strip().lower()
    semantic_type = str(raw_item.get("semantic_type", "")).strip().lower()
    if semantic_type not in semantic_types:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} must declare semantic_type in {sorted(semantic_types)}",
            )
        )
        return
    _validate_menu_control_storage_contract(
        prefix=prefix,
        item_type=item_type,
        semantic_type=semantic_type,
        raw_item=raw_item,
        issues=issues,
    )
    options_key = str(raw_item.get("options_key", "")).strip().lower()
    if item_type == "toggle":
        if semantic_type != "bool":
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} toggle controls must use semantic_type=bool",
                )
            )
        return
    if item_type == "selector":
        _validate_selector_control_item(
            prefix=prefix,
            semantic_type=semantic_type,
            options_key=options_key,
            selector_options_key_required=selector_options_key_required,
            settings_option_labels=settings_option_labels,
            issues=issues,
        )
        return
    _validate_numeric_control_item(
        prefix=prefix,
        item_type=item_type,
        semantic_type=semantic_type,
        options_key=options_key,
        issues=issues,
    )


def _validate_selector_control_item(
    *,
    prefix: str,
    semantic_type: str,
    options_key: str,
    selector_options_key_required: bool,
    settings_option_labels: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    if semantic_type != "enum":
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} selector controls must use semantic_type=enum",
            )
        )
    if selector_options_key_required and not options_key:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} selector controls must declare options_key",
            )
        )
        return
    if options_key and options_key not in settings_option_labels:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} options_key references unknown settings_option_labels entry: {options_key}",
            )
        )


def _validate_numeric_control_item(
    *,
    prefix: str,
    item_type: str,
    semantic_type: str,
    options_key: str,
    issues: list[ValidationIssue],
) -> None:
    if semantic_type not in {"int", "float"}:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} {item_type} controls must use semantic_type=int or float",
            )
        )
    if options_key:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} numeric controls must not declare options_key",
            )
        )


def _validate_setup_field_control_typing(
    *,
    setup_fields: dict[str, object],
    semantic_types: set[str],
    setup_control_types: set[str],
    allowed_option_sources: set[str],
    issues: list[ValidationIssue],
) -> None:
    for mode_key, raw_fields in setup_fields.items():
        if not isinstance(raw_fields, list):
            continue
        for idx, raw_field in enumerate(raw_fields):
            if not isinstance(raw_field, dict):
                continue
            _validate_setup_control_field(
                mode_key=mode_key,
                field_index=idx,
                raw_field=raw_field,
                semantic_types=semantic_types,
                setup_control_types=setup_control_types,
                allowed_option_sources=allowed_option_sources,
                issues=issues,
            )


def _setup_field_prefix(mode_key: str, field_index: int) -> str:
    return f"setup_fields.{mode_key}[{field_index}]"


def _validate_setup_control_field(
    *,
    mode_key: str,
    field_index: int,
    raw_field: dict[str, object],
    semantic_types: set[str],
    setup_control_types: set[str],
    allowed_option_sources: set[str],
    issues: list[ValidationIssue],
) -> None:
    prefix = _setup_field_prefix(mode_key, field_index)
    semantic_type = str(raw_field.get("semantic_type", "")).strip().lower()
    control = str(raw_field.get("control", "")).strip().lower()
    if semantic_type not in semantic_types:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} must declare semantic_type in {sorted(semantic_types)}",
            )
        )
        return
    if control not in setup_control_types:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} must declare control in {sorted(setup_control_types)}",
            )
        )
        return
    storage_type = str(raw_field.get("storage_type", "")).strip().lower()
    if storage_type:
        if storage_type == "bool" and semantic_type != "bool":
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type=bool requires semantic_type=bool",
                )
            )
        elif storage_type in {"int", "float"} and semantic_type != storage_type:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type={storage_type} requires semantic_type={storage_type}",
                )
            )
        elif storage_type in {"int_index", "string_id"} and semantic_type != "enum":
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} storage_type={storage_type} requires semantic_type=enum",
                )
            )
    if semantic_type == "enum":
        _validate_enum_setup_field(
            prefix=prefix,
            control=control,
            raw_field=raw_field,
            allowed_option_sources=allowed_option_sources,
            issues=issues,
        )
        return
    if semantic_type == "bool":
        _validate_bool_setup_field(
            prefix=prefix, control=control, raw_field=raw_field, issues=issues
        )
        return
    _validate_numeric_setup_field(
        prefix=prefix, control=control, raw_field=raw_field, issues=issues
    )


def _validate_enum_setup_field(
    *,
    prefix: str,
    control: str,
    raw_field: dict[str, object],
    allowed_option_sources: set[str],
    issues: list[ValidationIssue],
) -> None:
    has_min = "min" in raw_field
    has_max = "max" in raw_field
    has_options = "options" in raw_field
    has_options_source = "options_source" in raw_field
    if control != "selector":
        issues.append(
            ValidationIssue(
                "content", f"{prefix} enum fields must use control=selector"
            )
        )
    if has_min or has_max:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} enum fields must not define numeric min/max bounds",
            )
        )
    if has_options == has_options_source:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} enum fields must define exactly one of options or options_source",
            )
        )
    if has_options:
        options = raw_field.get("options")
        if (
            not isinstance(options, list)
            or not options
            or any(not isinstance(value, str) or not value.strip() for value in options)
        ):
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} enum options must be a non-empty list[str]",
                )
            )
    if has_options_source:
        options_source = str(raw_field.get("options_source", "")).strip().lower()
        if options_source not in allowed_option_sources:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{prefix} options_source must be one of {sorted(allowed_option_sources)}",
                )
            )


def _validate_bool_setup_field(
    *,
    prefix: str,
    control: str,
    raw_field: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    if control != "toggle":
        issues.append(
            ValidationIssue("content", f"{prefix} bool fields must use control=toggle")
        )
    if any(key in raw_field for key in ("min", "max", "options", "options_source")):
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} bool fields must not define numeric or enum metadata",
            )
        )


def _validate_numeric_setup_field(
    *,
    prefix: str,
    control: str,
    raw_field: dict[str, object],
    issues: list[ValidationIssue],
) -> None:
    if control not in {"slider", "stepper"}:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} numeric fields must use control=slider or stepper",
            )
        )
    if not ("min" in raw_field and "max" in raw_field):
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} numeric fields must define min and max bounds",
            )
        )
    if "options" in raw_field or "options_source" in raw_field:
        issues.append(
            ValidationIssue(
                "content",
                f"{prefix} numeric fields must not define enum options",
            )
        )


def _parse_menu_label_requirements(
    *,
    field: str,
    raw: object,
    issues: list[ValidationIssue],
) -> list[tuple[str, set[str]]] | None:
    if not isinstance(raw, list):
        issues.append(ValidationIssue("schema", f"{field} must be a list"))
        return None

    parsed: list[tuple[str, set[str]]] = []
    for idx, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            issues.append(
                ValidationIssue("schema", f"{field}[{idx}] must be an object")
            )
            continue
        menu_id = entry.get("menu_id")
        labels = _as_string_list(entry.get("labels", []))
        if not isinstance(menu_id, str) or not menu_id.strip():
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{field}[{idx}].menu_id must be a non-empty string",
                )
            )
            continue
        if not labels:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{field}[{idx}].labels must be a non-empty list[str]",
                )
            )
            continue
        parsed.append((menu_id, set(labels)))
    return parsed


def _parse_menu_literal_rules(
    raw: object, *, field: str, issues: list[ValidationIssue]
) -> list[tuple[Path, str, str]] | None:
    if not isinstance(raw, list):
        issues.append(ValidationIssue("schema", f"{field} must be a list"))
        return None

    rules: list[tuple[Path, str, str]] = []
    for idx, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            issues.append(
                ValidationIssue("schema", f"{field}[{idx}] must be an object")
            )
            continue
        rel = entry.get("file")
        literal = entry.get("literal")
        message = entry.get("message")
        if not isinstance(rel, str) or not rel.strip():
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{field}[{idx}].file must be a non-empty string",
                )
            )
            continue
        if not isinstance(literal, str) or not literal:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{field}[{idx}].literal must be a non-empty string",
                )
            )
            continue
        if not isinstance(message, str) or not message:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{field}[{idx}].message must be a non-empty string",
                )
            )
            continue
        rules.append((PROJECT_ROOT / rel, literal, message))
    return rules


def _validate_menu_structure_banned_literals(
    rules: list[tuple[Path, str, str]],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for path, literal, message in rules:
        if not path.exists():
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            issues.append(ValidationIssue("missing", f"missing required path: {rel}"))
            continue
        text = path.read_text(encoding="utf-8")
        if literal in text:
            issues.append(ValidationIssue("drift", message))
    return issues


def _load_menu_structure_single_source_contract(
    issues: list[ValidationIssue],
) -> MenuStructureContract | None:
    contract = _load_governance_subsection(issues, "menu_structure_single_source")
    if contract is None:
        return None

    required_menus = _as_string_list(contract.get("required_menus", []))
    if not required_menus:
        issues.append(
            ValidationIssue(
                "schema",
                (
                    f"{POLICY_PACK_REL}.governance.menu_structure_single_source."
                    "required_menus must be a non-empty list[str]"
                ),
            )
        )
        return None

    required_submenu_labels = _parse_menu_label_requirements(
        field=(
            f"{POLICY_PACK_REL}.governance.menu_structure_single_source."
            "required_submenu_labels"
        ),
        raw=contract.get("required_submenu_labels", []),
        issues=issues,
    )
    required_item_labels = _parse_menu_label_requirements(
        field=(
            f"{POLICY_PACK_REL}.governance.menu_structure_single_source."
            "required_item_labels"
        ),
        raw=contract.get("required_item_labels", []),
        issues=issues,
    )
    required_item_types = _as_string_list(contract.get("required_item_types", []))
    if not required_item_types:
        issues.append(
            ValidationIssue(
                "schema",
                (
                    f"{POLICY_PACK_REL}.governance.menu_structure_single_source."
                    "required_item_types must be a non-empty list[str]"
                ),
            )
        )
        return None

    banned_literal_rules = _parse_menu_literal_rules(
        contract.get("banned_python_literals", []),
        field=(
            f"{POLICY_PACK_REL}.governance.menu_structure_single_source."
            "banned_python_literals"
        ),
        issues=issues,
    )
    if required_submenu_labels is None or required_item_labels is None:
        return None
    if banned_literal_rules is None:
        return None

    return MenuStructureContract(
        required_menus=tuple(required_menus),
        required_submenu_labels=tuple(required_submenu_labels),
        required_item_labels=tuple(required_item_labels),
        required_item_types=set(required_item_types),
        banned_literal_rules=tuple(banned_literal_rules),
    )


def _missing_submenu_labels(
    menu_payload: dict[str, object],
    *,
    menu_id: str,
    required_labels: set[str],
) -> list[str]:
    labels = {
        str(item.get("label", ""))
        for item in _menu_items(menu_payload, menu_id)
        if str(item.get("type", "")).strip().lower() == "submenu"
    }
    return sorted(required_labels - labels)


def _missing_item_labels(
    menu_payload: dict[str, object],
    *,
    menu_id: str,
    required_labels: set[str],
) -> list[str]:
    labels = {str(item.get("label", "")) for item in _menu_items(menu_payload, menu_id)}
    return sorted(required_labels - labels)


def _missing_required_menu_types(
    menus: dict[str, object], required_types: set[str]
) -> list[str]:
    seen_types: set[str] = set()
    for menu in menus.values():
        if not isinstance(menu, dict):
            continue
        items = menu.get("items")
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type", "")).strip().lower()
            if item_type:
                seen_types.add(item_type)
    return sorted(required_types - seen_types)


def _append_missing_submenu_label_issue(
    issues: list[ValidationIssue],
    *,
    menu_rel: str,
    menu_id: str,
    required_labels: set[str],
    menu_payload: dict[str, object],
) -> None:
    missing_labels = _missing_submenu_labels(
        menu_payload,
        menu_id=menu_id,
        required_labels=required_labels,
    )
    if missing_labels:
        issues.append(
            ValidationIssue(
                "content",
                f"{menu_rel} {menu_id} is missing required submenu labels: {', '.join(missing_labels)}",
            )
        )


def _append_missing_item_label_issue(
    issues: list[ValidationIssue],
    *,
    menu_rel: str,
    menu_id: str,
    required_labels: set[str],
    menu_payload: dict[str, object],
) -> None:
    missing_labels = _missing_item_labels(
        menu_payload,
        menu_id=menu_id,
        required_labels=required_labels,
    )
    if missing_labels:
        issues.append(
            ValidationIssue(
                "content",
                f"{menu_rel} {menu_id} is missing required item labels: {', '.join(missing_labels)}",
            )
        )


def _validate_menu_structure_single_option_menus(
    menu_rel: str,
    menu_payload: dict[str, object],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        issues.append(
            ValidationIssue("schema", f"{menu_rel} must define menus as an object")
        )
        return issues

    try:
        from tet4d.engine.runtime.menu_runtime_graph import (
            detect_redundant_single_option_menus,
        )
    except Exception as exc:
        issues.append(
            ValidationIssue(
                "import",
                f"failed loading single-option menu validator: {exc}",
            )
        )
        return issues

    for message in detect_redundant_single_option_menus(
        menus,
        source_label="authored",
    ):
        issues.append(ValidationIssue("content", f"{menu_rel} {message}"))
    return issues


def _validate_menu_structure_single_source_of_truth() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    contract = _load_menu_structure_single_source_contract(issues)
    if contract is None:
        return issues

    menu_rel = "config/menu/structure.json"
    menu_payload = _load_json_payload(MENU_STRUCTURE_PATH, menu_rel, issues)
    if not isinstance(menu_payload, dict):
        return issues

    issues.extend(_validate_menu_structure_single_option_menus(menu_rel, menu_payload))

    menus = menu_payload.get("menus")
    if not isinstance(menus, dict):
        issues.append(
            ValidationIssue("schema", f"{menu_rel} must define menus as an object")
        )
        return issues
    missing_menus = sorted(set(contract.required_menus) - set(menus))
    if missing_menus:
        issues.append(
            ValidationIssue(
                "schema",
                f"{menu_rel} is missing required canonical menus: {', '.join(missing_menus)}",
            )
        )

    for menu_id, labels in contract.required_submenu_labels:
        _append_missing_submenu_label_issue(
            issues,
            menu_rel=menu_rel,
            menu_id=menu_id,
            required_labels=labels,
            menu_payload=menu_payload,
        )
    for menu_id, labels in contract.required_item_labels:
        _append_missing_item_label_issue(
            issues,
            menu_rel=menu_rel,
            menu_id=menu_id,
            required_labels=labels,
            menu_payload=menu_payload,
        )

    missing_types = _missing_required_menu_types(menus, contract.required_item_types)
    if missing_types:
        issues.append(
            ValidationIssue(
                "content",
                f"{menu_rel} is missing required menu item types: {', '.join(missing_types)}",
            )
        )
    issues.extend(
        _validate_menu_structure_banned_literals(contract.banned_literal_rules)
    )
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


def _is_real_native_tree() -> bool:
    native_root = PROJECT_ROOT / "native"
    if not native_root.is_dir():
        return False
    for path in native_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        if rel != "native/AGENTS.md":
            return True
    return False


def _native_project_cpp_files() -> list[Path]:
    native_root = PROJECT_ROOT / "native"
    if not native_root.is_dir():
        return []
    files: list[Path] = []
    for path in native_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in NATIVE_CPP_EXTENSIONS:
            continue
        rel_parts = path.relative_to(PROJECT_ROOT).parts
        if "third_party" in rel_parts or "build" in rel_parts:
            continue
        files.append(path)
    return sorted(files)


def _has_native_project_cpp_files() -> bool:
    return bool(_native_project_cpp_files())


def _governance_required_paths() -> tuple[str, ...]:
    paths = list(GOVERNANCE_ROUTING_REQUIRED_PATHS)
    if _is_real_native_tree():
        paths.append("native/AGENTS.md")
    return tuple(paths)


def _governance_scan_paths() -> list[str]:
    rels = {
        "AGENTS.md",
        "docs/WORKFLOW_CODEX.md",
        "godot/AGENTS.md",
    }
    if (PROJECT_ROOT / "native/AGENTS.md").exists():
        rels.add("native/AGENTS.md")
    for root in ("docs/governance", "docs/architecture", "docs/policies"):
        root_path = PROJECT_ROOT / root
        if root_path.exists():
            rels.update(
                path.relative_to(PROJECT_ROOT).as_posix()
                for path in root_path.rglob("*.md")
            )
    return sorted(rels)


def _read_text(rel: str, issues: list[ValidationIssue]) -> str | None:
    path = PROJECT_ROOT / rel
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        issues.append(ValidationIssue("missing", f"missing required path: {rel}"))
        return None


def _validate_governance_routing_required_files() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    tracked_paths = _git_tracked_paths(issues)
    for rel in _governance_required_paths():
        path = PROJECT_ROOT / rel
        if not path.exists():
            issues.append(
                ValidationIssue("missing", f"missing governance routing path: {rel}")
            )
            continue
        if tracked_paths is not None and path.is_file() and rel not in tracked_paths:
            issues.append(
                ValidationIssue(
                    "git", f"governance routing path is not tracked in git: {rel}"
                )
            )
    return issues


def _append_missing_concepts(
    *,
    rel: str,
    label: str,
    text: str,
    concept_groups: tuple[tuple[str, tuple[str, ...]], ...],
    issues: list[ValidationIssue],
) -> None:
    lower = text.lower()
    for concept, options in concept_groups:
        if not any(option.lower() in lower for option in options):
            issues.append(
                ValidationIssue(
                    "content", f"{rel} missing governance concept: {label} {concept}"
                )
            )


def _validate_governance_routing_concepts() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    root_text = _read_text("AGENTS.md", issues)
    if root_text is not None:
        _append_missing_concepts(
            rel="AGENTS.md",
            label="root routing",
            text=root_text,
            concept_groups=(
                ("Python", ("python",)),
                ("semantic oracle", ("semantic oracle",)),
                ("Godot", ("godot",)),
                ("C++/GDExtension", ("c++", "gdextension")),
                ("authority", ("authority",)),
                ("parity", ("parity",)),
            ),
            issues=issues,
        )

    authority_text = _read_text("docs/architecture/authority_map.md", issues)
    if authority_text is not None:
        _append_missing_concepts(
            rel="docs/architecture/authority_map.md",
            label="authority map",
            text=authority_text,
            concept_groups=(
                ("Python", ("python",)),
                ("current semantics", ("current semantic", "current gameplay")),
                ("Godot", ("godot",)),
                (
                    "UI/product shell/presentation",
                    ("ui", "product shell", "presentation"),
                ),
                ("C++/GDExtension", ("c++", "gdextension")),
                ("authority", ("authority",)),
                ("parity", ("parity",)),
                ("GDScript", ("gdscript",)),
                ("semantic duplication", ("duplicate", "duplicating")),
            ),
            issues=issues,
        )

    router_text = _read_text("docs/governance/README.md", issues)
    if router_text is not None:
        for token in (
            "codex_policy",
            "godot_cpp_policy",
            "config_policy",
            "secrets_policy",
            "testing_policy",
            "review_checklist",
            "authority_map",
            "utility_index",
            "cpp_safety_policy",
            "parity_protocol",
            "trace_metadata_identity_digest_parity",
            "trace_schema_version_normalization_parity",
            "parity_evidence_review_and_third_slice_selection",
        ):
            if token not in router_text:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"docs/governance/README.md missing routing link token: {token}",
                    )
                )
    return issues


def _validate_agents_line_limits() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel, limit in AGENTS_LINE_LIMITS:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > limit:
            issues.append(
                ValidationIssue(
                    "content", f"{rel} exceeds {limit} lines ({line_count})"
                )
            )
    return issues


def _validate_governance_local_paths() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _governance_scan_paths():
        text = _read_text(rel, issues)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, label in GOVERNANCE_LOCAL_PATH_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        ValidationIssue(
                            "safety",
                            f"{rel}:{lineno} includes local machine path ({label})",
                        )
                    )
    return issues


def _is_placeholder_secret_value(raw_value: str) -> bool:
    value = raw_value.strip().strip("'\"`")
    if not value:
        return True
    normalized = value.lower()
    return normalized in PLACEHOLDER_SECRET_VALUES or "redacted" in normalized


def _validate_governance_secret_patterns() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _governance_scan_paths():
        text = _read_text(rel, issues)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, label in SECRET_PREFIX_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        ValidationIssue(
                            "secret", f"{rel}:{lineno} contains likely {label}"
                        )
                    )
            assignment = SECRET_ASSIGNMENT_PATTERN.search(line)
            if assignment is None:
                continue
            value = assignment.group(2).strip()
            if _is_placeholder_secret_value(value):
                continue
            issues.append(
                ValidationIssue(
                    "secret",
                    f"{rel}:{lineno} contains assignment-like secret value",
                )
            )
    return issues


def _validate_governance_authority_inversion() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _governance_scan_paths():
        text = _read_text(rel, issues)
        if text is None:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern, label in AUTHORITY_INVERSION_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        ValidationIssue(
                            "authority",
                            f"{rel}:{lineno} contains possible {label}",
                        )
                    )
    return issues


def _validate_parity_dangerous_phrases() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in _governance_scan_paths():
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for phrase, label in PARITY_DANGEROUS_PHRASES:
            if phrase in lower:
                issues.append(
                    ValidationIssue(
                        "authority",
                        f"{rel} contains dangerous parity wording: {label}",
                    )
                )
    return issues


def _validate_parity_fixture_readmes() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in ("tests/golden", "tests/replay/golden"):
        fixture_root = PROJECT_ROOT / rel
        if not fixture_root.exists():
            continue
        readme = fixture_root / "README.md"
        if not readme.exists():
            issues.append(
                ValidationIssue(
                    "missing", f"{rel}/ must include README.md linking parity protocol"
                )
            )
            continue
        text = readme.read_text(encoding="utf-8").lower()
        if "parity_protocol" not in text and "parity protocol" not in text:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{rel}/README.md must link to docs/architecture/parity_protocol.md",
                )
            )
    return issues


def _validate_cpp_parity_protocol_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_real_native_tree():
        return issues

    parity_rel = "docs/architecture/parity_protocol.md"
    if not (PROJECT_ROOT / parity_rel).exists():
        issues.append(
            ValidationIssue("missing", f"missing parity protocol: {parity_rel}")
        )

    parity_text = _read_text(parity_rel, issues)
    if parity_text is not None:
        _append_missing_concepts(
            rel=parity_rel,
            label="parity protocol",
            text=parity_text,
            concept_groups=(
                ("Python semantic oracle", ("semantic oracle",)),
                ("C++/GDExtension", ("c++", "gdextension")),
                ("golden evidence", ("golden evidence", "golden traces")),
                ("comparison modes", ("comparison mode",)),
                ("disagreement rule", ("disagreement",)),
                ("fixture location", ("fixture location", "migration/golden_traces")),
                ("authority map transfer", ("authority map", "authority transfer")),
                (
                    "first parity pilot",
                    ("first subsystem parity pilot", "stable_hash_text"),
                ),
                (
                    "parity pilot audit gates",
                    (
                        "parity_pilot_audit_and_promotion_gates",
                        "second parity slice",
                    ),
                ),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/authority_map.md",
            ("parity_protocol", "authority transfer", "subsystem-specific"),
        ),
        (
            "docs/governance/testing_policy.md",
            ("c++ / python parity", "python oracle", "visual godot"),
        ),
        (
            "docs/governance/godot_cpp_policy.md",
            ("parity_protocol", "provisional", "authority map"),
        ),
        (
            "docs/governance/review_checklist.md",
            (
                "parity / authority transfer",
                "python oracle",
                "godot visual",
                "first parity pilot",
            ),
        ),
        (
            "docs/governance/README.md",
            (
                "parity_protocol",
                "testing/parity",
                "first_subsystem_parity_pilot",
                "parity_pilot_audit_and_promotion_gates",
            ),
        ),
    )
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing parity governance token: {token}",
                    )
                )

    issues.extend(_validate_parity_fixture_readmes())
    issues.extend(_validate_parity_dangerous_phrases())
    return issues


def _validate_parity_pilot_audit_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    audit_rel = "docs/architecture/parity_pilot_audit_and_promotion_gates.md"
    if not (PROJECT_ROOT / audit_rel).exists():
        issues.append(
            ValidationIssue("missing", f"missing parity audit doc: {audit_rel}")
        )
        return issues

    audit_text = _read_text(audit_rel, issues)
    if audit_text is not None:
        _append_missing_concepts(
            rel=audit_rel,
            label="parity pilot audit",
            text=audit_text,
            concept_groups=(
                ("Python semantic oracle", ("python remains the semantic oracle",)),
                (
                    "no authority transfer",
                    ("does not transfer authority", "not authority transfer"),
                ),
                ("promotion gates", ("promotion gates", "second parity slice")),
                (
                    "allowed categories",
                    (
                        "coordinate",
                        "topology identifier",
                        "trace metadata",
                        "dimension label",
                    ),
                ),
                (
                    "forbidden categories",
                    ("full topology movement", "rotation semantics", "endgame physics"),
                ),
                (
                    "harness placement decision",
                    (
                        "tools/parity/first_subsystem_parity_pilot.py",
                        "accepted for the first pilot",
                    ),
                ),
                (
                    "strict/default behavior",
                    ("default behaviour", "strict behaviour", "tet4d_strict_parity"),
                ),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (
                "first_subsystem_parity_pilot",
                "parity_pilot_audit_and_promotion_gates",
                "second parity slice",
            ),
        ),
        (
            "docs/architecture/authority_transfer_protocol.md",
            (
                "parity_pilot_audit_and_promotion_gates",
                "not transfer records",
            ),
        ),
        (
            "docs/governance/README.md",
            ("parity_pilot_audit_and_promotion_gates",),
        ),
        (
            "docs/governance/review_checklist.md",
            (
                "first-pilot audit and promotion gates",
                "strict/default parity behavior",
                "second parity slice",
            ),
        ),
        (
            "docs/governance/drift_protection_map.md",
            (
                "parity_pilot_audit_and_promotion_gates.md",
                "tools/parity/first_subsystem_parity_pilot.py",
                "tests/unit/migration/test_first_subsystem_parity_pilot.py",
            ),
        ),
        (
            "docs/DOCUMENTATION_MAP.md",
            ("parity_pilot_audit_and_promotion_gates.md",),
        ),
        (
            "AGENTS.md",
            (
                "parity_pilot_audit_and_promotion_gates.md",
                "second parity slice requires promotion-gate compliance",
            ),
        ),
        (
            "native/AGENTS.md",
            (
                "parity_pilot_audit_and_promotion_gates.md",
                "provisional evidence",
                "strict parity behavior",
            ),
        ),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "parity-pilot-audit",
            issues,
        )
    )
    return issues


def _validate_second_parity_slice_candidate_selection() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    selection_rel = "docs/architecture/second_parity_slice_candidate_selection.md"
    if not (PROJECT_ROOT / selection_rel).exists():
        issues.append(
            ValidationIssue(
                "missing", f"missing second parity slice selection doc: {selection_rel}"
            )
        )
        return issues

    selection_text = _read_text(selection_rel, issues)
    if selection_text is not None:
        _append_missing_concepts(
            rel=selection_rel,
            label="second parity slice selection",
            text=selection_text,
            concept_groups=(
                ("Python semantic oracle", ("python remains the semantic oracle",)),
                (
                    "native provisional status",
                    ("native/c++ remains provisional", "c++ remains provisional"),
                ),
                (
                    "no authority transfer",
                    (
                        "candidate selection does not transfer authority",
                        "will still not transfer authority",
                    ),
                ),
                ("decision status", ("decision status",)),
                ("Stage 18 decision", ("stage 18 implementation allowed",)),
                (
                    "chosen or blocked candidate",
                    ("chosen candidate", "decision status: blocked"),
                ),
                (
                    "explicit exclusions",
                    ("explicit exclusions",),
                ),
                (
                    "trace metadata candidate",
                    ("trace metadata identity/digest", "comparison rule"),
                ),
                (
                    "strict/default behavior",
                    ("default mode", "strict mode", "tet4d_strict_parity"),
                ),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (
                "second_parity_slice_candidate_selection.md",
                "stage 18 may",
                "candidate selection does not transfer authority",
            ),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            ("second_parity_slice_candidate_selection.md", "selected candidate"),
        ),
        (
            "docs/governance/README.md",
            ("second_parity_slice_candidate_selection.md",),
        ),
        (
            "docs/governance/review_checklist.md",
            ("selected candidate", "stage 18", "authority transfer"),
        ),
        (
            "docs/governance/drift_protection_map.md",
            (
                "second_parity_slice_candidate_selection.md",
                "selected candidate",
                "forbidden second-slice areas",
            ),
        ),
        (
            "docs/DOCUMENTATION_MAP.md",
            ("second_parity_slice_candidate_selection.md",),
        ),
        (
            "AGENTS.md",
            (
                "second_parity_slice_candidate_selection.md",
                "stage 18 may",
                "selected candidate",
            ),
        ),
        (
            "native/AGENTS.md",
            (
                "second_parity_slice_candidate_selection.md",
                "selected candidate",
                "native work remains provisional",
            ),
        ),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "second-parity-slice-selection",
            issues,
        )
    )
    return issues


def _validate_parity_evidence_review_and_third_slice_selection() -> list[
    ValidationIssue
]:
    issues: list[ValidationIssue] = []
    doc_rel = "docs/architecture/parity_evidence_review_and_third_slice_selection.md"
    if not (PROJECT_ROOT / doc_rel).exists():
        issues.append(
            ValidationIssue(
                "missing",
                f"missing parity evidence review doc: {doc_rel}",
            )
        )
        return issues

    doc_text = _read_text(doc_rel, issues)
    if doc_text is not None:
        _append_missing_concepts(
            rel=doc_rel,
            label="parity evidence review",
            text=doc_text,
            concept_groups=(
                ("Python semantic oracle", ("python remains the semantic oracle",)),
                (
                    "reviewed evidence",
                    ("first pilot", "stage 18", "trace metadata identity/digest"),
                ),
                (
                    "chosen candidate",
                    ("topology identifier normalization",),
                ),
                (
                    "no authority transfer",
                    ("does not transfer authority",),
                ),
                (
                    "Stage 20 boundary",
                    ("stage 20 implementation may only implement", "stage 20 boundary"),
                ),
                (
                    "explicit exclusions",
                    (
                        "seam traversal",
                        "neighbor lookup",
                        "movement semantics",
                        "rendering/projection/view semantics",
                        "endgame physics",
                    ),
                ),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (doc_rel, "stage 19 evidence review"),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            (doc_rel,),
        ),
        (
            "docs/architecture/authority_map.md",
            (doc_rel, "topology identifier normalization"),
        ),
        ("docs/governance/README.md", (doc_rel,)),
        ("docs/governance/review_checklist.md", (doc_rel,)),
        ("docs/governance/drift_protection_map.md", (doc_rel,)),
        ("docs/DOCUMENTATION_MAP.md", (doc_rel,)),
        ("AGENTS.md", (doc_rel,)),
        ("native/AGENTS.md", (doc_rel,)),
        (
            "docs/governance/codex_policy.md",
            ("parity evidence review and third-slice selection",),
        ),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "parity-evidence-review",
            issues,
        )
    )
    return issues


def _validate_trace_metadata_identity_digest_parity_governance() -> list[
    ValidationIssue
]:
    issues: list[ValidationIssue] = []
    doc_rel = "docs/architecture/trace_metadata_identity_digest_parity.md"
    if not (PROJECT_ROOT / doc_rel).exists():
        issues.append(
            ValidationIssue("missing", f"missing trace metadata parity doc: {doc_rel}")
        )
        return issues

    doc_text = _read_text(doc_rel, issues)
    if doc_text is not None:
        _append_missing_concepts(
            rel=doc_rel,
            label="trace metadata parity",
            text=doc_text,
            concept_groups=(
                ("Python oracle", ("trace_schema.py", "python oracle")),
                ("metadata-only fixture", ("metadata only", "fixture")),
                ("exact identity", ("exact identity", "compact canonical json")),
                ("exact digest", ("exact digest", "sha-256")),
                (
                    "provisional native path",
                    ("provisional native", "native/provisional"),
                ),
                ("default advisory", ("default behavior is advisory", "advisory")),
                ("strict blocking", ("tet4d_strict_parity=1", "blocking")),
                ("no authority transfer", ("does not transfer authority",)),
                ("explicit exclusions", ("explicit exclusions",)),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (doc_rel, "trace metadata identity/digest parity"),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            (doc_rel, "trace metadata identity/digest parity"),
        ),
        (
            "docs/architecture/second_parity_slice_candidate_selection.md",
            (doc_rel, "trace metadata identity/digest"),
        ),
        ("docs/governance/README.md", (doc_rel,)),
        ("docs/governance/review_checklist.md", (doc_rel,)),
        ("docs/governance/drift_protection_map.md", (doc_rel,)),
        ("docs/DOCUMENTATION_MAP.md", (doc_rel,)),
        ("docs/PROJECT_STRUCTURE.md", (doc_rel, "tests/fixtures/parity/")),
        ("AGENTS.md", (doc_rel,)),
        ("native/AGENTS.md", (doc_rel,)),
        ("docs/governance/codex_policy.md", ("stage 18 implementation tasks",)),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "trace-metadata-parity",
            issues,
        )
    )

    drift_text = _read_text("docs/governance/drift_protection_map.md", issues)
    if drift_text is not None:
        for rel in (
            doc_rel,
            "tools/parity/trace_metadata_identity_digest_parity.py",
            "tests/unit/migration/test_trace_metadata_identity_digest_parity.py",
            "native/tet4d_core/tests/trace_metadata_identity_digest_tests.cpp",
            "tests/fixtures/parity/trace_metadata_identity_digest.json",
        ):
            if rel not in drift_text:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"docs/governance/drift_protection_map.md must list {rel}",
                    )
                )
    return issues


def _validate_topology_identifier_normalization_parity_governance() -> list[
    ValidationIssue
]:
    issues: list[ValidationIssue] = []
    doc_rel = "docs/architecture/topology_identifier_normalization_parity.md"
    if not (PROJECT_ROOT / doc_rel).exists():
        issues.append(
            ValidationIssue(
                "missing",
                f"missing topology identifier normalization parity doc: {doc_rel}",
            )
        )
        return issues

    doc_text = _read_text(doc_rel, issues)
    if doc_text is not None:
        _append_missing_concepts(
            rel=doc_rel,
            label="topology identifier normalization parity",
            text=doc_text,
            concept_groups=(
                ("Python oracle", ("python remains the semantic oracle",)),
                ("identifier-only scope", ("identifier-only",)),
                ("no authority transfer", ("does not transfer authority",)),
                (
                    "default advisory",
                    (
                        "default mode is advisory",
                        "advisory when the native/provisional route is unavailable",
                    ),
                ),
                (
                    "strict blocking",
                    (
                        "strict mode",
                        "tet4d_strict_parity",
                        "blocks that unavailability",
                    ),
                ),
                (
                    "explicit exclusions",
                    (
                        "seam traversal",
                        "neighbor lookup",
                        "topology movement",
                        "rendering/projection/view/camera",
                        "endgame physics",
                    ),
                ),
                (
                    "harness and fixture",
                    (
                        "tools/parity/topology_identifier_normalization_parity.py",
                        "tests/fixtures/parity/topology_identifier_normalization.json",
                    ),
                ),
                (
                    "canonical identifiers",
                    ("plain_2d", "wrap_all_4d", "invert_all_4d", "sphere_like_4d"),
                ),
            ),
            issues=issues,
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (
                doc_rel,
                "topology identifier normalization",
                "does not transfer authority",
            ),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            (doc_rel,),
        ),
        (
            "docs/architecture/parity_evidence_review_and_third_slice_selection.md",
            (doc_rel,),
        ),
        (
            "docs/architecture/authority_map.md",
            (doc_rel, "topology identifier normalization"),
        ),
        ("docs/governance/README.md", (doc_rel, "topology identifier normalization")),
        ("docs/governance/review_checklist.md", (doc_rel,)),
        ("docs/governance/drift_protection_map.md", (doc_rel,)),
        ("docs/DOCUMENTATION_MAP.md", (doc_rel,)),
        (
            "docs/PROJECT_STRUCTURE.md",
            (
                doc_rel,
                "tools/parity/topology_identifier_normalization_parity.py",
                "tests/fixtures/parity/topology_identifier_normalization.json",
                "tests/unit/migration/test_topology_identifier_normalization_parity.py",
            ),
        ),
        ("AGENTS.md", (doc_rel,)),
        ("native/AGENTS.md", (doc_rel,)),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "topology-identifier-normalization-parity",
            issues,
        )
    )

    drift_text = _read_text("docs/governance/drift_protection_map.md", issues)
    if drift_text is not None:
        for rel in (
            doc_rel,
            "tools/parity/topology_identifier_normalization_parity.py",
            "tests/fixtures/parity/topology_identifier_normalization.json",
            "tests/unit/migration/test_topology_identifier_normalization_parity.py",
        ):
            if rel not in drift_text:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"docs/governance/drift_protection_map.md must list {rel}",
                    )
                )
    return issues


def _validate_parity_evidence_package_review_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    doc_rel = "docs/architecture/parity_evidence_package_review.md"
    if not (PROJECT_ROOT / doc_rel).exists():
        issues.append(
            ValidationIssue(
                "missing",
                f"missing parity evidence package review doc: {doc_rel}",
            )
        )
        return issues

    doc_text = _read_text(doc_rel, issues)
    if doc_text is not None:
        _append_missing_concepts(
            rel=doc_rel,
            label="parity evidence package review",
            text=doc_text,
            concept_groups=(
                ("first pilot review", ("first subsystem parity pilot", "stage 15")),
                (
                    "trace metadata parity review",
                    ("trace metadata identity/digest", "stage 18"),
                ),
                (
                    "topology identifier parity review",
                    ("topology identifier normalization", "stage 20"),
                ),
                ("Python semantic oracle", ("python remains the semantic oracle",)),
                (
                    "native provisional status",
                    (
                        "native/c++ remains provisional",
                        "c++/gdextension remains provisional",
                    ),
                ),
                (
                    "no authority transfer",
                    ("does not transfer authority", "no authority-transfer record"),
                ),
                (
                    "tooling route decision",
                    ("tooling route decision",),
                ),
                (
                    "tooling route options",
                    ("tools/migration/", "tools/parity/"),
                ),
                (
                    "authority-transfer readiness",
                    ("authority-transfer readiness",),
                ),
                (
                    "next-stage recommendation",
                    ("recommended next stage",),
                ),
                (
                    "explicit forbidden areas",
                    ("explicit forbidden areas",),
                ),
                (
                    "forbidden area list",
                    (
                        "topology movement",
                        "seam traversal",
                        "neighbor lookup",
                        "rendering/projection/view/camera",
                        "endgame physics",
                    ),
                ),
            ),
            issues=issues,
        )
        lower = doc_text.lower()
        forbidden_claims = (
            "this review transfers authority",
            "ready for authority transfer: yes",
            "transferred authority: yes",
            "candidate transfer record created: yes",
        )
        for claim in forbidden_claims:
            if claim in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{doc_rel} must not claim authority transfer: {claim}",
                    )
                )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (doc_rel, "stages 15, 18, and 20", "does not transfer authority"),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            (doc_rel, "future parity slices", "promotion gates"),
        ),
        (
            "docs/architecture/authority_transfer_protocol.md",
            (doc_rel, "not transfer records"),
        ),
        (
            "docs/architecture/authority_map.md",
            (doc_rel, "provisional parity evidence"),
        ),
        ("docs/governance/README.md", (doc_rel,)),
        (
            "docs/governance/review_checklist.md",
            (doc_rel, "further parity expansion", "authority transfer"),
        ),
        (
            "docs/governance/drift_protection_map.md",
            (doc_rel, "tools/migration/", "tools/parity/"),
        ),
        ("docs/governance/codex_policy.md", ("evidence-package status",)),
        ("docs/DOCUMENTATION_MAP.md", (doc_rel, "stages 15, 18, and 20")),
        ("docs/PROJECT_STRUCTURE.md", (doc_rel,)),
        ("AGENTS.md", (doc_rel, "tools/migration/", "tools/parity/")),
        (
            "native/AGENTS.md",
            (doc_rel, "provisional", "forbidden areas"),
        ),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "parity-evidence-package-review",
            issues,
        )
    )
    return issues


def _validate_trace_schema_version_normalization_parity_governance() -> list[
    ValidationIssue
]:
    issues: list[ValidationIssue] = []
    doc_rel = "docs/architecture/trace_schema_version_normalization_parity.md"
    harness_rel = "tools/parity/trace_schema_version_normalization_parity.py"
    fixture_rel = "tests/fixtures/parity/trace_schema_version_normalization.json"
    test_rel = "tests/unit/migration/test_trace_schema_version_normalization_parity.py"
    required_paths = (doc_rel, harness_rel, fixture_rel, test_rel)
    for rel in required_paths:
        if not (PROJECT_ROOT / rel).exists():
            issues.append(
                ValidationIssue(
                    "missing",
                    f"missing trace schema/version normalization parity path: {rel}",
                )
            )
    if not (PROJECT_ROOT / doc_rel).exists():
        return issues

    doc_text = _read_text(doc_rel, issues)
    if doc_text is not None:
        _append_missing_concepts(
            rel=doc_rel,
            label="trace schema/version normalization parity",
            text=doc_text,
            concept_groups=(
                ("Python oracle", ("python remains the semantic oracle",)),
                ("schema/version scope", ("trace schema/version normalization",)),
                ("metadata-only scope", ("schema/version metadata-only",)),
                ("no authority transfer", ("does not transfer authority",)),
                ("native provisional", ("native/c++ remains provisional",)),
                ("no safe native route", ("no safe native/provisional route",)),
                ("default advisory", ("default mode is advisory",)),
                ("strict blocking", ("tet4d_strict_parity=1", "blocks")),
                (
                    "explicit exclusions",
                    (
                        "trace events",
                        "board snapshots",
                        "topology movement",
                        "gameplay",
                        "rendering",
                        "endgame physics",
                    ),
                ),
                (
                    "harness and fixture",
                    (
                        harness_rel,
                        fixture_rel,
                    ),
                ),
            ),
            issues=issues,
        )
        lower = doc_text.lower()
        for claim in (
            "this slice transfers authority",
            "transferred authority: yes",
            "native/c++ is authoritative",
            "fake native output",
        ):
            if claim in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{doc_rel} must not claim invalid Stage 22 status: {claim}",
                    )
                )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/parity_protocol.md",
            (doc_rel, "trace schema/version normalization"),
        ),
        (
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
            (doc_rel, "schema/version metadata"),
        ),
        (
            "docs/architecture/parity_evidence_package_review.md",
            (doc_rel, harness_rel, fixture_rel),
        ),
        (
            "docs/architecture/authority_transfer_protocol.md",
            (doc_rel, "not a transfer record"),
        ),
        (
            "docs/architecture/authority_map.md",
            (doc_rel, "schema/version metadata"),
        ),
        ("docs/governance/README.md", (doc_rel, harness_rel, fixture_rel)),
        ("docs/governance/review_checklist.md", (doc_rel, "stage 22")),
        (
            "docs/governance/drift_protection_map.md",
            (doc_rel, harness_rel, fixture_rel, test_rel),
        ),
        ("docs/governance/codex_policy.md", ("stage 22 implementation tasks",)),
        ("docs/DOCUMENTATION_MAP.md", (doc_rel,)),
        (
            "docs/PROJECT_STRUCTURE.md",
            (doc_rel, harness_rel, fixture_rel, test_rel),
        ),
        ("AGENTS.md", (doc_rel,)),
        ("native/AGENTS.md", (doc_rel, "do not fake native output")),
    )
    issues.extend(
        _validate_governance_doc_tokens(
            required_docs,
            "trace-schema-version-normalization-parity",
            issues,
        )
    )
    return issues


def _validate_godot_semantic_boundary_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not (PROJECT_ROOT / "godot").exists():
        return issues

    validator_rel = "tools/governance/validate_godot_semantic_boundary.py"
    if not (PROJECT_ROOT / validator_rel).exists():
        issues.append(
            ValidationIssue(
                "missing", f"missing Godot semantic-boundary validator: {validator_rel}"
            )
        )

    governance = _read_text("tools/governance/validate_governance.py", issues)
    if governance is not None and "validate_godot_semantic_boundary" not in governance:
        issues.append(
            ValidationIssue(
                "content",
                "tools/governance/validate_governance.py must run Godot semantic-boundary validation",
            )
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/governance/godot_cpp_policy.md",
            ("semantic boundary", "gdscript", "independently compute"),
        ),
        (
            "godot/AGENTS.md",
            ("semantic truth", "gdscript", "adapter"),
        ),
        (
            "docs/governance/review_checklist.md",
            ("godot semantic boundary", "gdscript", "semantic-boundary validator"),
        ),
    )
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing Godot semantic-boundary token: {token}",
                    )
                )
    return issues


def _validate_native_cpp_safety_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not _is_real_native_tree():
        return issues

    _validate_native_cpp_required_paths(issues)
    _validate_native_cpp_policy_contents(issues)
    _validate_native_cpp_routing(issues)
    _validate_native_cpp_tooling_validator(issues)
    _validate_native_cpp_review_routing(issues)
    return issues


def _validate_native_cpp_required_paths(issues: list[ValidationIssue]) -> None:
    required_rels = (
        "docs/governance/cpp_safety_policy.md",
        "docs/governance/native_tooling_ci_policy.md",
    )
    if _has_native_project_cpp_files():
        required_rels = (
            "docs/governance/cpp_safety_policy.md",
            "docs/governance/native_tooling_ci_policy.md",
            ".clang-format",
            ".clang-tidy",
        )
    for rel in required_rels:
        if not (PROJECT_ROOT / rel).exists():
            issues.append(
                ValidationIssue("missing", f"missing native C++ governance path: {rel}")
            )


def _validate_native_cpp_policy_contents(issues: list[ValidationIssue]) -> None:
    cpp_policy = _read_text("docs/governance/cpp_safety_policy.md", issues)
    if cpp_policy is not None:
        _append_missing_concepts(
            rel="docs/governance/cpp_safety_policy.md",
            label="C++ safety policy",
            text=cpp_policy,
            concept_groups=(
                ("Python semantic oracle", ("semantic oracle",)),
                ("RAII", ("raii",)),
                ("raw owning pointers", ("raw owning pointer",)),
                ("new/delete", ("new", "delete")),
                ("GDExtension boundary", ("gdextension",)),
                ("parity", ("parity",)),
                ("authority map", ("authority_map", "authority map")),
            ),
            issues=issues,
        )

    _validate_native_tooling_ci_policy(issues)

    clang_tidy = _read_text(".clang-tidy", issues)
    if clang_tidy is not None:
        _validate_native_clang_tidy_content(clang_tidy, issues)


def _validate_native_tooling_ci_policy(issues: list[ValidationIssue]) -> None:
    tooling_policy = _read_text("docs/governance/native_tooling_ci_policy.md", issues)
    if tooling_policy is not None:
        _append_missing_concepts(
            rel="docs/governance/native_tooling_ci_policy.md",
            label="native tooling CI policy",
            text=tooling_policy,
            concept_groups=(
                ("local advisory mode", ("local advisory",)),
                ("local strict mode", ("local strict",)),
                ("CI strict mode", ("ci strict",)),
                ("strict environment", ("tet4d_strict_native_tools",)),
                ("clang-format", ("clang-format",)),
                ("clang-tidy", ("clang-tidy",)),
                ("compile database", ("compile_commands.json",)),
                ("Python semantic oracle", ("semantic oracle",)),
                ("authority transfer", ("authority_transfer_protocol",)),
                ("technical debt", ("technical_debt_register", "td-0004")),
            ),
            issues=issues,
        )


def _validate_native_cpp_routing(issues: list[ValidationIssue]) -> None:
    native_agents = _read_text("native/AGENTS.md", issues)
    if native_agents is not None and "cpp_safety_policy" not in native_agents:
        issues.append(
            ValidationIssue(
                "content", "native/AGENTS.md must route to cpp_safety_policy"
            )
        )
    if native_agents is not None and "native_tooling_ci_policy" not in native_agents:
        issues.append(
            ValidationIssue(
                "content",
                "native/AGENTS.md must route to native_tooling_ci_policy",
            )
        )


def _validate_native_cpp_tooling_validator(issues: list[ValidationIssue]) -> None:
    tooling_rel = "tools/governance/validate_native_cpp_tooling.py"
    if not (PROJECT_ROOT / tooling_rel).exists():
        issues.append(
            ValidationIssue(
                "missing", f"missing native C++ tooling validator: {tooling_rel}"
            )
        )

    governance = _read_text("tools/governance/validate_governance.py", issues)
    if governance is not None and "validate_native_cpp_tooling" not in governance:
        issues.append(
            ValidationIssue(
                "content",
                "tools/governance/validate_governance.py must run native C++ tooling validation",
            )
        )


def _validate_native_cpp_review_routing(issues: list[ValidationIssue]) -> None:
    router = _read_text("docs/governance/README.md", issues)
    if router is not None and "native_tooling_ci_policy.md" not in router:
        issues.append(
            ValidationIssue(
                "content",
                "docs/governance/README.md must route native_tooling_ci_policy.md",
            )
        )

    checklist = _read_text("docs/governance/review_checklist.md", issues)
    if checklist is not None:
        lower = checklist.lower()
        for token in ("native tooling", "tet4d_strict_native_tools", "ci strict"):
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"docs/governance/review_checklist.md missing native tooling token: {token}",
                    )
                )


def _validate_native_clang_tidy_content(
    clang_tidy: str, issues: list[ValidationIssue]
) -> None:
    if re.search(r"(?im)^\s*WarningsAsErrors\s*:\s*['\"]?\*['\"]?\s*$", clang_tidy):
        issues.append(
            ValidationIssue(
                "content",
                ".clang-tidy must not set WarningsAsErrors: '*' at this stage",
            )
        )
    lower = clang_tidy.lower()
    if "clang-analyzer" not in lower and "cppcoreguidelines" not in lower:
        issues.append(
            ValidationIssue(
                "content",
                ".clang-tidy should include clang-analyzer or cppcoreguidelines",
            )
        )


def _validate_config_authority_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    validator_rel = "tools/governance/validate_config_authority.py"
    if not (PROJECT_ROOT / validator_rel).exists():
        issues.append(
            ValidationIssue(
                "missing", f"missing config authority validator: {validator_rel}"
            )
        )

    governance = _read_text("tools/governance/validate_governance.py", issues)
    if governance is not None and "validate_config_authority" not in governance:
        issues.append(
            ValidationIssue(
                "content",
                "tools/governance/validate_governance.py must run config authority validation",
            )
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/governance/config_policy.md",
            (
                "config authority",
                "policy_no_magic_numbers",
                "config/project/constants.json",
            ),
        ),
        (
            "docs/policies/POLICY_NO_MAGIC_NUMBERS.md",
            ("docs/governance/config_policy.md", "validate_config_authority"),
        ),
        (
            "docs/governance/review_checklist.md",
            ("config-authority validator", "hardcoded constants"),
        ),
        (
            "docs/governance/README.md",
            ("config_policy", "validate_config_authority"),
        ),
    )
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing config authority governance token: {token}",
                    )
                )
    return issues


def _validate_utility_reuse_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    validator_rel = "tools/governance/validate_utility_reuse.py"
    if not (PROJECT_ROOT / validator_rel).exists():
        issues.append(
            ValidationIssue(
                "missing", f"missing utility reuse validator: {validator_rel}"
            )
        )

    governance = _read_text("tools/governance/validate_governance.py", issues)
    if governance is not None and "validate_utility_reuse" not in governance:
        issues.append(
            ValidationIssue(
                "content",
                "tools/governance/validate_governance.py must run utility reuse validation",
            )
        )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/architecture/utility_index.md",
            ("required fields", "owner", "reuse rule", "migration relevance"),
        ),
        (
            "docs/policies/POLICY_NO_REINVENTING_WHEEL.md",
            (
                "docs/architecture/utility_index.md",
                "check_wheel_reuse_rules.py",
                "check_dedup_dead_code_rules.py",
                "validate_utility_reuse.py",
            ),
        ),
        (
            "docs/governance/codex_policy.md",
            ("search", "helpers", "existing", "utility_index"),
        ),
        (
            "docs/governance/review_checklist.md",
            ("dependency / utility reuse", "no-reinvention", "validate_utility_reuse"),
        ),
        (
            "docs/governance/README.md",
            (
                "utility_index",
                "policy_no_reinventing_wheel",
                "validate_utility_reuse",
                "check_wheel_reuse_rules",
                "check_dedup_dead_code_rules",
            ),
        ),
    )
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing utility reuse governance token: {token}",
                    )
                )
    return issues


def _validate_workspace_bundle_governance() -> list[ValidationIssue]:
    from tools.governance import validate_workspace_bundle

    return [
        ValidationIssue(issue.kind, issue.message)
        for issue in validate_workspace_bundle.validate(PROJECT_ROOT)
    ]


def _validate_technical_debt_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    required_paths = (
        "docs/governance/workspace_bundle/technical_debt_policy.md",
        "docs/governance/workspace_bundle/drift_protection_policy.md",
        "docs/governance/technical_debt_register.md",
        "tools/governance/validate_technical_debt.py",
    )
    for rel in required_paths:
        if not (PROJECT_ROOT / rel).exists():
            issues.append(
                ValidationIssue("missing", f"missing technical debt path: {rel}")
            )

    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = (
        (
            "docs/governance/README.md",
            (
                "technical_debt_register.md",
                "technical_debt_policy.md",
                "drift_protection_policy.md",
                "validate_technical_debt.py",
            ),
        ),
        (
            "docs/governance/review_checklist.md",
            ("technical-debt delta", "advisory validator findings", "drift protection"),
        ),
        (
            "docs/governance/workspace_bundle/MANIFEST.md",
            ("technical_debt_policy.md", "drift_protection_policy.md"),
        ),
        (
            "tools/governance/validate_governance.py",
            ("validate_technical_debt",),
        ),
    )
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing technical debt governance token: {token}",
                    )
                )

    register = _read_text("docs/governance/technical_debt_register.md", issues)
    if register is not None and "reusable workspace policy" in register.lower():
        issues.append(
            ValidationIssue(
                "content",
                "technical debt register must not present itself as reusable workspace policy",
            )
        )
    return issues


def _validate_required_governance_paths(
    required_paths: tuple[str, ...], label: str
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for rel in required_paths:
        if not (PROJECT_ROOT / rel).exists():
            issues.append(ValidationIssue("missing", f"missing {label} path: {rel}"))
    return issues


def _validate_governance_doc_tokens(
    required_docs: tuple[tuple[str, tuple[str, ...]], ...],
    label: str,
    issues: list[ValidationIssue],
) -> list[ValidationIssue]:
    content_issues: list[ValidationIssue] = []
    for rel, tokens in required_docs:
        text = _read_text(rel, issues)
        if text is None:
            continue
        lower = text.lower()
        for token in tokens:
            if token not in lower:
                content_issues.append(
                    ValidationIssue(
                        "content",
                        f"{rel} missing {label} governance token: {token}",
                    )
                )
    return content_issues


def _validate_drift_protection_map_uniqueness() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    map_text = _read_text("docs/governance/drift_protection_map.md", issues)
    workspace_text = _read_text(
        "docs/governance/workspace_bundle/drift_protection_policy.md", issues
    )
    if map_text is None or workspace_text is None:
        return issues

    map_body = map_text.lower()
    workspace_body = workspace_text.lower()
    duplicated_workspace_markers = (
        "## general drift risks",
        "## general drift-protection rules",
        "## project-specific drift maps",
    )
    for marker in duplicated_workspace_markers:
        if marker in map_body:
            issues.append(
                ValidationIssue(
                    "content",
                    "docs/governance/drift_protection_map.md must not copy "
                    f"workspace policy section {marker}",
                )
            )
    if map_body == workspace_body:
        issues.append(
            ValidationIssue(
                "content",
                "project drift map must not duplicate workspace drift policy",
            )
        )
    return issues


def _validate_workspace_bundle_authority_transfer_separation() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    bundle_root = PROJECT_ROOT / "docs/governance/workspace_bundle"
    if not bundle_root.exists():
        return issues

    for path in sorted(bundle_root.glob("*.md")):
        text = path.read_text(encoding="utf-8").lower()
        if "tet4d authority-transfer" in text or "transfer record" in text:
            rel = path.relative_to(PROJECT_ROOT).as_posix()
            issues.append(
                ValidationIssue(
                    "content",
                    f"{rel} must not define tet4d authority-transfer records",
                )
            )
    if (bundle_root / "authority_transfer_protocol.md").exists():
        issues.append(
            ValidationIssue(
                "content",
                "authority-transfer protocol must live outside workspace bundle",
            )
        )
    return issues


def _validate_workspace_review_template_neutrality() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    rel = "docs/governance/workspace_bundle/review_checklist_template.md"
    text = _read_text(rel, issues)
    if text is None:
        return issues

    forbidden_terms = (
        "tet4d",
        "python oracle",
        "python semantic oracle",
        "godot shell",
        "w-slice",
        "topology gameplay",
        "config/project",
    )
    lower = text.lower()
    for term in forbidden_terms:
        if term in lower:
            issues.append(
                ValidationIssue(
                    "content",
                    f"{rel} contains project-specific forbidden term: {term}",
                )
            )
    return issues


def _validate_review_template_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(
        _validate_required_governance_paths(
            (
                ".github/pull_request_template.md",
                "docs/governance/review_checklist.md",
                "docs/governance/workspace_bundle/review_checklist_template.md",
            ),
            "review-template",
        )
    )
    issues.extend(
        _validate_governance_doc_tokens(
            (
                (
                    "docs/governance/README.md",
                    (
                        ".github/pull_request_template.md",
                        "docs/governance/review_checklist.md",
                        "docs/governance/workspace_bundle/review_checklist_template.md",
                    ),
                ),
                (
                    "docs/governance/review_checklist.md",
                    (
                        "workspace_bundle/review_checklist_template.md",
                        "authority_map",
                        "parity_protocol",
                        "authority_transfer_protocol",
                        "technical_debt_register",
                        "drift_protection_map",
                        "generated bundle",
                        "staging discipline",
                    ),
                ),
            ),
            "review-template",
            issues,
        )
    )

    pr_template = _read_text(".github/pull_request_template.md", issues)
    if pr_template is not None:
        _append_missing_concepts(
            rel=".github/pull_request_template.md",
            label="PR template",
            text=pr_template,
            concept_groups=(
                ("scope/summary", ("summary", "scope")),
                ("unrelated dirty files", ("unrelated dirty files",)),
                ("Python semantic authority", ("python semantic",)),
                ("Godot/GDScript boundary", ("godot", "gdscript")),
                ("C++/GDExtension provisional", ("provisional", "gdextension")),
                ("authority-transfer protocol", ("authority-transfer",)),
                ("utility reuse/no reinvention", ("utilities", "duplicate")),
                ("config/constants authority", ("config/constants", "constants")),
                ("generated files", ("generated",)),
                ("technical debt", ("technical debt", "technical-debt")),
                ("drift protection", ("drift protection",)),
                ("validation commands", ("validation commands",)),
                (
                    "full verification",
                    ("codex_mode=1 ./scripts/verify.sh",),
                ),
                ("staging discipline", ("git diff --cached --check", "staged diff")),
            ),
            issues=issues,
        )

    issues.extend(_validate_workspace_review_template_neutrality())
    return issues


def _validate_drift_protection_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(
        _validate_required_governance_paths(
            (
                "docs/governance/workspace_bundle/drift_protection_policy.md",
                "docs/governance/drift_protection_map.md",
                "tools/governance/validate_drift_protection.py",
            ),
            "drift-protection",
        )
    )
    issues.extend(
        _validate_governance_doc_tokens(
            (
                (
                    "docs/governance/README.md",
                    (
                        "drift_protection_policy.md",
                        "drift_protection_map.md",
                        "validate_drift_protection.py",
                    ),
                ),
                (
                    "docs/governance/review_checklist.md",
                    ("drift protection", "validate_governance.py", "generated outputs"),
                ),
                (
                    "tools/governance/validate_governance.py",
                    ("validate_drift_protection",),
                ),
                (
                    "docs/governance/drift_protection_map.md",
                    (
                        "workspace_bundle/drift_protection_policy.md",
                        "tet4d-specific",
                        "governance routing drift",
                        "authority drift",
                        "config/generated drift",
                    ),
                ),
            ),
            "drift-protection",
            issues,
        )
    )
    issues.extend(_validate_drift_protection_map_uniqueness())
    return issues


def _validate_authority_transfer_governance() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(
        _validate_required_governance_paths(
            (
                "docs/architecture/authority_transfer_protocol.md",
                "tools/governance/validate_authority_transfer.py",
            ),
            "authority-transfer",
        )
    )
    authority_transfer_protocol = _read_text(
        "docs/architecture/authority_transfer_protocol.md", issues
    )
    if authority_transfer_protocol is not None:
        _append_missing_concepts(
            rel="docs/architecture/authority_transfer_protocol.md",
            label="authority transfer protocol",
            text=authority_transfer_protocol,
            concept_groups=(
                ("candidate status", ("candidate",)),
                ("blocked status", ("blocked",)),
                ("evidence-only pilot", ("first subsystem parity pilot",)),
                ("no transfer wording", ("evidence only", "must not be recorded")),
            ),
            issues=issues,
        )
    issues.extend(
        _validate_governance_doc_tokens(
            (
                (
                    "docs/governance/README.md",
                    (
                        "authority_transfer_protocol.md",
                        "validate_authority_transfer.py",
                    ),
                ),
                (
                    "docs/architecture/authority_map.md",
                    ("authority_transfer_protocol.md",),
                ),
                (
                    "docs/architecture/parity_protocol.md",
                    ("authority_transfer_protocol.md", "first_subsystem_parity_pilot"),
                ),
                (
                    "docs/governance/drift_protection_map.md",
                    (
                        "authority_transfer_protocol.md",
                        "validate_authority_transfer.py",
                    ),
                ),
                (
                    "tools/governance/validate_governance.py",
                    ("validate_authority_transfer",),
                ),
                (
                    "docs/governance/review_checklist.md",
                    ("authority transfer", "transfer record", "fallback path"),
                ),
            ),
            "authority-transfer",
            issues,
        )
    )
    issues.extend(_validate_workspace_bundle_authority_transfer_separation())
    return issues


def _validate_governance_routing_overlay() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues.extend(_validate_governance_routing_required_files())
    issues.extend(_validate_governance_routing_concepts())
    issues.extend(_validate_agents_line_limits())
    issues.extend(_validate_governance_local_paths())
    issues.extend(_validate_governance_secret_patterns())
    issues.extend(_validate_governance_authority_inversion())
    issues.extend(_validate_native_cpp_safety_governance())
    issues.extend(_validate_cpp_parity_protocol_governance())
    issues.extend(_validate_parity_pilot_audit_governance())
    issues.extend(_validate_second_parity_slice_candidate_selection())
    issues.extend(_validate_parity_evidence_review_and_third_slice_selection())
    issues.extend(_validate_trace_metadata_identity_digest_parity_governance())
    issues.extend(_validate_topology_identifier_normalization_parity_governance())
    issues.extend(_validate_parity_evidence_package_review_governance())
    issues.extend(_validate_trace_schema_version_normalization_parity_governance())
    issues.extend(_validate_godot_semantic_boundary_governance())
    issues.extend(_validate_config_authority_governance())
    issues.extend(_validate_utility_reuse_governance())
    issues.extend(_validate_workspace_bundle_governance())
    issues.extend(_validate_technical_debt_governance())
    issues.extend(_validate_drift_protection_governance())
    issues.extend(_validate_authority_transfer_governance())
    issues.extend(_validate_review_template_governance())
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
    issues.extend(_validate_deprecated_authorities())
    issues.extend(_validate_menu_control_typing())
    issues.extend(_validate_menu_simplification_rule())
    issues.extend(_validate_menu_structure_single_source_of_truth())
    issues.extend(_validate_keybinding_single_source_of_truth())
    issues.extend(_validate_governance_routing_overlay())
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
