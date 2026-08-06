from __future__ import annotations

import json
from pathlib import Path

VALIDATOR_PATH = Path("tools/governance/validate_project_contracts.py")
POLICY_PATH = Path("config/project/policy_pack.json")
START = "def _validate_codex_routing_model() -> list[ValidationIssue]:\n"
END = "\ndef validate_manifest() -> list[ValidationIssue]:\n"

REPLACEMENT = '''def _validate_codex_authority_model(
    payload: dict[str, object], issues: list[ValidationIssue]
) -> tuple[dict[str, object] | None, set[str] | None]:
    authority_model = payload.get("authority_model")
    if not isinstance(authority_model, dict):
        issues.append(
            ValidationIssue(
                "schema", f"{POLICY_PACK_REL}.authority_model must be an object"
            )
        )
        return None, None

    tracked_paths = _git_tracked_paths(issues)
    for key, expected_path in CODEX_AUTHORITY_POINTERS.items():
        field = f"{POLICY_PACK_REL}.authority_model.{key}"
        value = authority_model.get(key)
        if value != expected_path:
            issues.append(
                ValidationIssue("schema", f"{field} must equal {expected_path!r}")
            )
        _validate_codex_routing_path(
            field=field,
            value=value,
            tracked_paths=tracked_paths,
            issues=issues,
        )
    return authority_model, tracked_paths


def _validate_codex_routing_header(
    routing: dict[str, object], issues: list[ValidationIssue]
) -> None:
    if routing.get("schema_version") != 1:
        issues.append(
            ValidationIssue(
                "schema", f"{POLICY_PACK_REL}.codex_routing.schema_version must equal 1"
            )
        )
    _append_exact_identifier_set_issues(
        field=f"{POLICY_PACK_REL}.codex_routing.workflow_modifiers",
        raw=routing.get("workflow_modifiers"),
        expected=SUPPORTED_CODEX_WORKFLOW_MODIFIERS,
        issues=issues,
    )
    _append_exact_identifier_set_issues(
        field=f"{POLICY_PACK_REL}.codex_routing.verification_requirements",
        raw=routing.get("verification_requirements"),
        expected=SUPPORTED_CODEX_VERIFICATION_REQUIREMENTS,
        issues=issues,
    )


def _validate_codex_task_authority_keys(
    *,
    task: dict[str, object],
    field: str,
    known_authority_keys: set[str],
    issues: list[ValidationIssue],
) -> None:
    if "authority_keys" not in task:
        return
    authority_field = f"{field}.authority_keys"
    values = _codex_string_list(task.get("authority_keys"))
    if values is None or not values:
        issues.append(
            ValidationIssue(
                "schema", f"{authority_field} must be a non-empty list[str]"
            )
        )
        return
    if len(values) != len(set(values)):
        issues.append(
            ValidationIssue("schema", f"{authority_field} must not contain duplicates")
        )
    for authority_key in values:
        if authority_key not in known_authority_keys:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{authority_field} references unknown authority key: {authority_key}",
                )
            )


def _validate_codex_task_dispatch_paths(
    *,
    task: dict[str, object],
    field: str,
    tracked_paths: set[str] | None,
    issues: list[ValidationIssue],
) -> None:
    if "dispatch_paths" not in task:
        return
    _validate_optional_codex_path_list(
        field=f"{field}.dispatch_paths",
        raw=task.get("dispatch_paths"),
        tracked_paths=tracked_paths,
        issues=issues,
    )


def _validate_codex_task_typical_requirements(
    *,
    task: dict[str, object],
    field: str,
    issues: list[ValidationIssue],
) -> None:
    typical_field = f"{field}.typical_verification_requirements"
    values = _codex_string_list(task.get("typical_verification_requirements"))
    if values is None or not values:
        issues.append(
            ValidationIssue(
                "schema", f"{typical_field} must be a non-empty list[str]"
            )
        )
        return
    if len(values) != len(set(values)):
        issues.append(
            ValidationIssue("schema", f"{typical_field} must not contain duplicates")
        )
    for requirement in values:
        if requirement not in SUPPORTED_CODEX_VERIFICATION_REQUIREMENTS:
            issues.append(
                ValidationIssue(
                    "schema",
                    f"{typical_field} references unknown verification requirement: {requirement}",
                )
            )


def _validate_codex_task_entry(
    *,
    task_id: str,
    task: object,
    known_authority_keys: set[str],
    tracked_paths: set[str] | None,
    issues: list[ValidationIssue],
) -> None:
    field = f"{POLICY_PACK_REL}.codex_routing.task_types.{task_id}"
    if not isinstance(task, dict):
        issues.append(ValidationIssue("schema", f"{field} must be an object"))
        return
    if "authority_keys" not in task and "dispatch_paths" not in task:
        issues.append(
            ValidationIssue(
                "schema", f"{field} must define authority_keys or dispatch_paths"
            )
        )
    _validate_codex_task_authority_keys(
        task=task,
        field=field,
        known_authority_keys=known_authority_keys,
        issues=issues,
    )
    _validate_codex_task_dispatch_paths(
        task=task,
        field=field,
        tracked_paths=tracked_paths,
        issues=issues,
    )
    _validate_codex_task_typical_requirements(task=task, field=field, issues=issues)


def _validate_codex_task_types(
    *,
    routing: dict[str, object],
    authority_model: dict[str, object],
    tracked_paths: set[str] | None,
    issues: list[ValidationIssue],
) -> None:
    task_types = routing.get("task_types")
    if not isinstance(task_types, dict):
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.codex_routing.task_types must be an object",
            )
        )
        return
    actual_task_types = set(task_types)
    missing = sorted(SUPPORTED_CODEX_TASK_TYPES - actual_task_types)
    unknown = sorted(actual_task_types - SUPPORTED_CODEX_TASK_TYPES)
    if missing:
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.codex_routing.task_types is missing identifiers: {', '.join(missing)}",
            )
        )
    if unknown:
        issues.append(
            ValidationIssue(
                "schema",
                f"{POLICY_PACK_REL}.codex_routing.task_types contains unknown identifiers: {', '.join(unknown)}",
            )
        )
    for task_id in sorted(actual_task_types & SUPPORTED_CODEX_TASK_TYPES):
        _validate_codex_task_entry(
            task_id=task_id,
            task=task_types[task_id],
            known_authority_keys=set(authority_model),
            tracked_paths=tracked_paths,
            issues=issues,
        )


def _validate_codex_routing_model() -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    payload = _load_policy_pack_payload(issues)
    if payload is None:
        return issues
    authority_model, tracked_paths = _validate_codex_authority_model(payload, issues)
    if authority_model is None:
        return issues
    routing = payload.get("codex_routing")
    if not isinstance(routing, dict):
        issues.append(
            ValidationIssue(
                "schema", f"{POLICY_PACK_REL}.codex_routing must be an object"
            )
        )
        return issues
    _validate_codex_routing_header(routing, issues)
    _validate_codex_task_types(
        routing=routing,
        authority_model=authority_model,
        tracked_paths=tracked_paths,
        issues=issues,
    )
    return issues
'''

WORKFLOW_TOKEN_REPLACEMENTS = {
    "## Task profiles": "## Machine-readable task routing and composable verification",
    "Narrow review": "`review_only`",
    "Python engine": "`python_reference_engine`",
    "Godot product shell": "`godot_product_shell`",
    "Native C++/GDExtension": "`native_deterministic_core`",
    "Topology explorer": "`topology_and_explorer`",
    "Staged migration/handoff": "`staged_handoff`",
}
AGENTS_TOKEN_REPLACEMENTS = {
    "docs/DOCUMENTATION_MAP.md": "`codex_routing`",
    "docs/plans/topology_playground_current_authority.md": "docs/architecture/authority_map.md",
}


def _replace_validator() -> None:
    text = VALIDATOR_PATH.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start)
    VALIDATOR_PATH.write_text(text[:start] + REPLACEMENT + text[end:], encoding="utf-8")


def _replace_rule_tokens(rule: dict[str, object], replacements: dict[str, str]) -> None:
    tokens = rule.get("must_contain")
    if not isinstance(tokens, list):
        return
    rule["must_contain"] = [replacements.get(token, token) for token in tokens]


def _update_policy_content_rules() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    rules = payload["maintenance_contract"]["content_rules"]
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        if rule.get("file") == "docs/WORKFLOW_CODEX.md":
            _replace_rule_tokens(rule, WORKFLOW_TOKEN_REPLACEMENTS)
        elif rule.get("file") == "AGENTS.md":
            _replace_rule_tokens(rule, AGENTS_TOKEN_REPLACEMENTS)
    POLICY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    _replace_validator()
    _update_policy_content_rules()


if __name__ == "__main__":
    main()
