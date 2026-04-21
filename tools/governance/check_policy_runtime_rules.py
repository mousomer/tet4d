from __future__ import annotations

import ast
import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

if __package__:
    from ._common import as_str_list, iter_python_files, load_unified_code_rules
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    from _common import as_str_list, iter_python_files, load_unified_code_rules


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RuntimeRuleIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class RuntimeRuleWarning:
    kind: str
    message: str


@dataclass(frozen=True)
class SelectedFileBan:
    path: str
    name_regex: str
    message: str


@dataclass(frozen=True)
class ConfigBackedRuntimeConstantsRule:
    authoritative_sources: tuple[str, ...]
    source_roots: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    target_module_globs: tuple[str, ...]
    allowed_loader_modules: tuple[str, ...]
    allowed_loader_symbols: tuple[str, ...]
    constant_like_name_regex: str
    runtime_owned_name_regex: str
    selected_file_bans: tuple[SelectedFileBan, ...]
    third_party_import_roots: tuple[str, ...]
    schema_version_name_regexes: tuple[str, ...]
    schema_version_module_globs: tuple[str, ...]
    protocol_dunder_name_regexes: tuple[str, ...]
    sentinel_name_regexes: tuple[str, ...]
    test_path_globs: tuple[str, ...]
    invariant_name_regexes: tuple[str, ...]
    invariant_module_globs: tuple[str, ...]


def _load_rules() -> dict[str, Any]:
    unified = load_unified_code_rules(ROOT)
    if isinstance(unified, dict):
        return unified
    raise SystemExit("missing required file: config/project/policy_pack.json")


def _validate_entry_shape(
    *,
    entry: Any,
    section: str,
    idx: int,
    issues: list[RuntimeRuleIssue],
) -> tuple[Path, str, str, list[str], list[str], list[str]] | None:
    if not isinstance(entry, dict):
        issues.append(RuntimeRuleIssue("schema", f"{section}[{idx}] must be object"))
        return None
    raw_path = entry.get("path")
    if not isinstance(raw_path, str) or not raw_path:
        issues.append(
            RuntimeRuleIssue("schema", f"{section}[{idx}].path must be non-empty str")
        )
        return None
    severity = str(entry.get("severity", "error")).strip().lower()
    if severity not in {"error", "warning"}:
        issues.append(
            RuntimeRuleIssue(
                "schema", f"{section}[{idx}].severity must be 'error' or 'warning'"
            )
        )
        return None
    try:
        required_any_tokens = as_str_list(
            entry.get("required_any_tokens", []),
            field=f"{section}[{idx}].required_any_tokens",
        )
        required_all_tokens = as_str_list(
            entry.get("required_all_tokens", []),
            field=f"{section}[{idx}].required_all_tokens",
        )
        forbidden_regex = as_str_list(
            entry.get("forbidden_regex", []),
            field=f"{section}[{idx}].forbidden_regex",
        )
    except ValueError as exc:
        issues.append(RuntimeRuleIssue("schema", str(exc)))
        return None
    return (
        ROOT / raw_path,
        raw_path,
        severity,
        required_any_tokens,
        required_all_tokens,
        forbidden_regex,
    )


def _check_text_entrypoints(
    entries: Any,
    *,
    section: str,
) -> tuple[list[RuntimeRuleIssue], list[RuntimeRuleWarning]]:
    issues: list[RuntimeRuleIssue] = []
    warnings: list[RuntimeRuleWarning] = []
    if not isinstance(entries, list):
        return [RuntimeRuleIssue("schema", f"{section} must be a list")], []

    for idx, entry in enumerate(entries, start=1):
        parsed = _validate_entry_shape(
            entry=entry, section=section, idx=idx, issues=issues
        )
        if parsed is None:
            continue
        (
            path,
            rel_path,
            severity,
            required_any_tokens,
            required_all_tokens,
            forbidden_regex,
        ) = parsed
        add = issues.append if severity == "error" else warnings.append
        if not path.exists():
            add(
                RuntimeRuleIssue("missing", f"missing text-entrypoint file: {rel_path}")
                if severity == "error"
                else RuntimeRuleWarning(
                    "missing", f"missing text-entrypoint file: {rel_path}"
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        if required_any_tokens and not any(tok in text for tok in required_any_tokens):
            add(
                RuntimeRuleIssue(
                    "sanitation",
                    (
                        f"{rel_path} missing at least one sanitization token: "
                        + ", ".join(required_any_tokens)
                    ),
                )
                if severity == "error"
                else RuntimeRuleWarning(
                    "sanitation",
                    (
                        f"{rel_path} missing at least one sanitization token: "
                        + ", ".join(required_any_tokens)
                    ),
                )
            )
        for token in required_all_tokens:
            if token not in text:
                add(
                    RuntimeRuleIssue(
                        "sanitation",
                        f"{rel_path} missing required sanitization token: {token}",
                    )
                    if severity == "error"
                    else RuntimeRuleWarning(
                        "sanitation",
                        f"{rel_path} missing required sanitization token: {token}",
                    )
                )
        for pattern in forbidden_regex:
            if re.search(pattern, text, flags=re.MULTILINE):
                add(
                    RuntimeRuleIssue(
                        "sanitation",
                        f"{rel_path} matched forbidden sanitization regex: {pattern}",
                    )
                    if severity == "error"
                    else RuntimeRuleWarning(
                        "sanitation",
                        f"{rel_path} matched forbidden sanitization regex: {pattern}",
                    )
                )
    return issues, warnings


def _check_numeric_entrypoints(
    entries: Any,
    *,
    section: str,
) -> tuple[list[RuntimeRuleIssue], list[RuntimeRuleWarning]]:
    issues: list[RuntimeRuleIssue] = []
    warnings: list[RuntimeRuleWarning] = []
    if not isinstance(entries, list):
        return [RuntimeRuleIssue("schema", f"{section} must be a list")], []

    for idx, entry in enumerate(entries, start=1):
        parsed = _validate_entry_shape(
            entry=entry, section=section, idx=idx, issues=issues
        )
        if parsed is None:
            continue
        (
            path,
            rel_path,
            severity,
            _required_any_tokens,
            required_all_tokens,
            forbidden_regex,
        ) = parsed
        add = issues.append if severity == "error" else warnings.append
        if not path.exists():
            add(
                RuntimeRuleIssue(
                    "missing", f"missing numeric-entrypoint file: {rel_path}"
                )
                if severity == "error"
                else RuntimeRuleWarning(
                    "missing", f"missing numeric-entrypoint file: {rel_path}"
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        for token in required_all_tokens:
            if token not in text:
                add(
                    RuntimeRuleIssue(
                        "magic_numbers",
                        f"{rel_path} missing required config-backed token: {token}",
                    )
                    if severity == "error"
                    else RuntimeRuleWarning(
                        "magic_numbers",
                        f"{rel_path} missing required config-backed token: {token}",
                    )
                )
        for pattern in forbidden_regex:
            if re.search(pattern, text, flags=re.MULTILINE):
                add(
                    RuntimeRuleIssue(
                        "magic_numbers",
                        f"{rel_path} matched forbidden numeric regex: {pattern}",
                    )
                    if severity == "error"
                    else RuntimeRuleWarning(
                        "magic_numbers",
                        f"{rel_path} matched forbidden numeric regex: {pattern}",
                    )
                )
    return issues, warnings


def _read_str_list_field(
    payload: dict[str, Any],
    key: str,
    *,
    field: str,
) -> list[str]:
    return as_str_list(payload.get(key, []), field=field)


def _read_str_field(payload: dict[str, Any], key: str, *, field: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty str")
    return value.strip()


def _parse_selected_file_bans(
    raw: Any,
    *,
    field: str,
) -> tuple[SelectedFileBan, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"{field} must be list[object]")
    bans: list[SelectedFileBan] = []
    for idx, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"{field}[{idx}] must be object")
        path = _read_str_field(entry, "path", field=f"{field}[{idx}].path")
        name_regex = _read_str_field(
            entry, "name_regex", field=f"{field}[{idx}].name_regex"
        )
        message = _read_str_field(entry, "message", field=f"{field}[{idx}].message")
        bans.append(SelectedFileBan(path=path, name_regex=name_regex, message=message))
    return tuple(bans)


def _parse_authoritative_sources(
    raw: Any,
    *,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(raw, list):
        raise ValueError(f"{field} must be list[object]")
    sources: list[str] = []
    for idx, entry in enumerate(raw, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"{field}[{idx}] must be object")
        path = _read_str_field(entry, "path", field=f"{field}[{idx}].path")
        sources.append(path)
    return tuple(sources)


def _read_runtime_constant_top_level_fields(
    payload: dict[str, Any],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    return (
        _parse_authoritative_sources(
            payload.get("authoritative_sources", []),
            field="config_backed_runtime_constants.authoritative_sources",
        ),
        tuple(
            _read_str_list_field(
                payload,
                "source_roots",
                field="config_backed_runtime_constants.source_roots",
            )
        ),
        tuple(
            _read_str_list_field(
                payload,
                "exclude_globs",
                field="config_backed_runtime_constants.exclude_globs",
            )
        ),
        tuple(
            _read_str_list_field(
                payload,
                "target_module_globs",
                field="config_backed_runtime_constants.target_module_globs",
            )
        ),
        tuple(
            _read_str_list_field(
                payload,
                "allowed_loader_modules",
                field="config_backed_runtime_constants.allowed_loader_modules",
            )
        ),
        tuple(
            _read_str_list_field(
                payload,
                "allowed_loader_symbols",
                field="config_backed_runtime_constants.allowed_loader_symbols",
            )
        ),
    )


def _read_runtime_constant_enforcement(
    payload: dict[str, Any],
) -> tuple[str, str, tuple[SelectedFileBan, ...]]:
    enforcement = payload.get("enforcement")
    if not isinstance(enforcement, dict):
        raise ValueError("config_backed_runtime_constants.enforcement must be object")
    module_level_assignments_only = enforcement.get(
        "module_level_assignments_only", True
    )
    if not isinstance(module_level_assignments_only, bool):
        raise ValueError(
            "config_backed_runtime_constants.enforcement.module_level_assignments_only must be bool"
        )
    if not module_level_assignments_only:
        raise ValueError(
            "config_backed_runtime_constants.enforcement.module_level_assignments_only must be true"
        )
    name_patterns = enforcement.get("name_patterns")
    if not isinstance(name_patterns, dict):
        raise ValueError(
            "config_backed_runtime_constants.enforcement.name_patterns must be object"
        )
    return (
        _read_str_field(
            name_patterns,
            "constant_like",
            field=(
                "config_backed_runtime_constants.enforcement.name_patterns.constant_like"
            ),
        ),
        _read_str_field(
            name_patterns,
            "runtime_owned",
            field=(
                "config_backed_runtime_constants.enforcement.name_patterns.runtime_owned"
            ),
        ),
        _parse_selected_file_bans(
            enforcement.get("selected_file_bans", []),
            field="config_backed_runtime_constants.enforcement.selected_file_bans",
        ),
    )


def _read_exception_category(
    payload: dict[str, Any], key: str, *, field: str
) -> dict[str, Any]:
    category = payload.get(key)
    if not isinstance(category, dict):
        raise ValueError(f"{field} must be object")
    return category


def _read_runtime_constant_exception_categories(
    payload: dict[str, Any],
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
]:
    exception_categories = payload.get("exception_categories")
    if not isinstance(exception_categories, dict):
        raise ValueError(
            "config_backed_runtime_constants.exception_categories must be object"
        )

    third_party = _read_exception_category(
        exception_categories,
        "third_party_constants_enums",
        field=(
            "config_backed_runtime_constants.exception_categories."
            "third_party_constants_enums"
        ),
    )
    schema_versions = _read_exception_category(
        exception_categories,
        "schema_versions",
        field="config_backed_runtime_constants.exception_categories.schema_versions",
    )
    protocol_dunder = _read_exception_category(
        exception_categories,
        "protocol_dunder",
        field="config_backed_runtime_constants.exception_categories.protocol_dunder",
    )
    sentinels = _read_exception_category(
        exception_categories,
        "sentinels",
        field="config_backed_runtime_constants.exception_categories.sentinels",
    )
    tests = _read_exception_category(
        exception_categories,
        "tests",
        field="config_backed_runtime_constants.exception_categories.tests",
    )

    return (
        tuple(
            _read_str_list_field(
                third_party,
                "allowed_import_roots",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "third_party_constants_enums.allowed_import_roots"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                schema_versions,
                "allowed_name_regexes",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "schema_versions.allowed_name_regexes"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                schema_versions,
                "allowed_module_globs",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "schema_versions.allowed_module_globs"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                protocol_dunder,
                "allowed_name_regexes",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "protocol_dunder.allowed_name_regexes"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                sentinels,
                "allowed_name_regexes",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "sentinels.allowed_name_regexes"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                tests,
                "path_globs",
                field=(
                    "config_backed_runtime_constants.exception_categories.tests.path_globs"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                exception_categories,
                "allowed_invariant_name_regex",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "allowed_invariant_name_regex"
                ),
            )
        ),
        tuple(
            _read_str_list_field(
                exception_categories,
                "allowed_invariant_module_globs",
                field=(
                    "config_backed_runtime_constants.exception_categories."
                    "allowed_invariant_module_globs"
                ),
            )
        ),
    )


def _append_runtime_constant_rule_shape_issues(
    *,
    authoritative_sources: tuple[str, ...],
    source_roots: tuple[str, ...],
    target_module_globs: tuple[str, ...],
    allowed_loader_modules: tuple[str, ...],
    allowed_loader_symbols: tuple[str, ...],
    issues: list[RuntimeRuleIssue],
) -> None:
    if not authoritative_sources:
        issues.append(
            RuntimeRuleIssue(
                "schema",
                "config_backed_runtime_constants.authoritative_sources must not be empty",
            )
        )
    if not source_roots:
        issues.append(
            RuntimeRuleIssue(
                "schema",
                "config_backed_runtime_constants.source_roots must not be empty",
            )
        )
    if not target_module_globs:
        issues.append(
            RuntimeRuleIssue(
                "schema",
                "config_backed_runtime_constants.target_module_globs must not be empty",
            )
        )
    if not allowed_loader_modules and not allowed_loader_symbols:
        issues.append(
            RuntimeRuleIssue(
                "schema",
                (
                    "config_backed_runtime_constants must define allowed_loader_modules "
                    "or allowed_loader_symbols"
                ),
            )
        )


def _append_runtime_constant_authority_issues(
    authoritative_sources: tuple[str, ...], issues: list[RuntimeRuleIssue]
) -> None:
    for path in authoritative_sources:
        if not (ROOT / path).exists():
            issues.append(
                RuntimeRuleIssue(
                    "missing",
                    (
                        "config_backed_runtime_constants authoritative source missing: "
                        f"{path}"
                    ),
                )
            )


def _parse_config_backed_runtime_constants_rule(
    payload: Any,
) -> tuple[ConfigBackedRuntimeConstantsRule | None, list[RuntimeRuleIssue]]:
    issues: list[RuntimeRuleIssue] = []
    if not isinstance(payload, dict):
        return (
            None,
            [
                RuntimeRuleIssue(
                    "schema", "config_backed_runtime_constants must be object"
                )
            ],
        )

    try:
        (
            authoritative_sources,
            source_roots,
            exclude_globs,
            target_module_globs,
            allowed_loader_modules,
            allowed_loader_symbols,
        ) = _read_runtime_constant_top_level_fields(payload)
        (
            constant_like_name_regex,
            runtime_owned_name_regex,
            selected_file_bans,
        ) = _read_runtime_constant_enforcement(payload)
        (
            third_party_import_roots,
            schema_version_name_regexes,
            schema_version_module_globs,
            protocol_dunder_name_regexes,
            sentinel_name_regexes,
            test_path_globs,
            invariant_name_regexes,
            invariant_module_globs,
        ) = _read_runtime_constant_exception_categories(payload)
    except ValueError as exc:
        issues.append(RuntimeRuleIssue("schema", str(exc)))
        return None, issues

    _append_runtime_constant_rule_shape_issues(
        authoritative_sources=authoritative_sources,
        source_roots=source_roots,
        target_module_globs=target_module_globs,
        allowed_loader_modules=allowed_loader_modules,
        allowed_loader_symbols=allowed_loader_symbols,
        issues=issues,
    )
    _append_runtime_constant_authority_issues(authoritative_sources, issues)

    if issues:
        return None, issues

    return (
        ConfigBackedRuntimeConstantsRule(
            authoritative_sources=authoritative_sources,
            source_roots=source_roots,
            exclude_globs=exclude_globs,
            target_module_globs=target_module_globs,
            allowed_loader_modules=allowed_loader_modules,
            allowed_loader_symbols=allowed_loader_symbols,
            constant_like_name_regex=constant_like_name_regex,
            runtime_owned_name_regex=runtime_owned_name_regex,
            selected_file_bans=selected_file_bans,
            third_party_import_roots=third_party_import_roots,
            schema_version_name_regexes=schema_version_name_regexes,
            schema_version_module_globs=schema_version_module_globs,
            protocol_dunder_name_regexes=protocol_dunder_name_regexes,
            sentinel_name_regexes=sentinel_name_regexes,
            test_path_globs=test_path_globs,
            invariant_name_regexes=invariant_name_regexes,
            invariant_module_globs=invariant_module_globs,
        ),
        [],
    )


def _path_matches_any(rel_path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(rel_path, pattern) for pattern in patterns)


def _module_name_for_rel_path(rel_path: str) -> str:
    module = rel_path.removesuffix(".py").replace("/", ".")
    if module.startswith("src."):
        return module[len("src.") :]
    return module


def _resolve_import_from_module(rel_path: str, node: ast.ImportFrom) -> str:
    if node.level <= 0:
        return node.module or ""
    module_name = _module_name_for_rel_path(rel_path)
    package_parts = module_name.split(".")[:-1]
    trim = max(node.level - 1, 0)
    if trim > len(package_parts):
        base_parts: list[str] = []
    else:
        base_parts = package_parts[: len(package_parts) - trim]
    if node.module:
        return ".".join((*base_parts, node.module))
    return ".".join(base_parts)


def _collect_import_aliases(tree: ast.Module, rel_path: str) -> dict[str, str]:
    imports: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".", 1)[0]
                imports[local] = alias.name if alias.asname else local
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_import_from_module(rel_path, node)
            for alias in node.names:
                if alias.name == "*":
                    continue
                local = alias.asname or alias.name
                imports[local] = (
                    f"{module_name}.{alias.name}" if module_name else alias.name
                )
    return imports


def _expr_qualname(node: ast.AST, imports: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return imports.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        base = _expr_qualname(node.value, imports)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return ""


def _qualname_matches_allowed(
    qualname: str,
    rule: ConfigBackedRuntimeConstantsRule,
) -> bool:
    if not qualname:
        return False
    for module in rule.allowed_loader_modules:
        if qualname == module or qualname.startswith(f"{module}."):
            return True
    terminal = qualname.rsplit(".", 1)[-1]
    return terminal in rule.allowed_loader_symbols


def _expr_uses_approved_loader(
    node: ast.AST,
    *,
    imports: dict[str, str],
    rule: ConfigBackedRuntimeConstantsRule,
    config_bound_names: set[str],
) -> bool:
    for subnode in ast.walk(node):
        if isinstance(subnode, ast.Name) and subnode.id in config_bound_names:
            return True
        qualname = ""
        if isinstance(subnode, ast.Call):
            qualname = _expr_qualname(subnode.func, imports)
        elif isinstance(subnode, (ast.Name, ast.Attribute)):
            qualname = _expr_qualname(subnode, imports)
        if _qualname_matches_allowed(qualname, rule):
            return True
    return False


def _assignment_target_names(node: ast.AST) -> tuple[list[str], ast.AST | None]:
    if isinstance(node, ast.Assign):
        names = [target.id for target in node.targets if isinstance(target, ast.Name)]
        return names, node.value
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return [node.target.id], node.value
    return [], None


def _is_literal_backed(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, int, float, bool)) or node.value is None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_literal_backed(node.operand)
    return False


def _is_numericish_literal(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float, bool)) or node.value is None
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        return _is_numericish_literal(node.operand)
    return False


def _matches_name_regexes(name: str, patterns: tuple[str, ...]) -> bool:
    return any(re.match(pattern, name) for pattern in patterns)


def _is_target_constant_assignment(
    name: str,
    value: ast.AST | None,
    rule: ConfigBackedRuntimeConstantsRule,
) -> bool:
    return bool(
        (
            re.match(rule.constant_like_name_regex, name)
            and _is_numericish_literal(value)
        )
        or re.search(rule.runtime_owned_name_regex, name, flags=re.IGNORECASE)
    )


def _is_schema_version_exception(
    name: str,
    rel_path: str,
    rule: ConfigBackedRuntimeConstantsRule,
) -> bool:
    return _matches_name_regexes(name, rule.schema_version_name_regexes) or (
        bool(rule.schema_version_module_globs)
        and _path_matches_any(rel_path, rule.schema_version_module_globs)
    )


def _is_protocol_dunder_exception(
    name: str, rule: ConfigBackedRuntimeConstantsRule
) -> bool:
    return _matches_name_regexes(name, rule.protocol_dunder_name_regexes)


def _is_sentinel_exception(name: str, rule: ConfigBackedRuntimeConstantsRule) -> bool:
    return _matches_name_regexes(name, rule.sentinel_name_regexes)


def _is_invariant_exception(
    name: str,
    rel_path: str,
    rule: ConfigBackedRuntimeConstantsRule,
) -> bool:
    return _matches_name_regexes(name, rule.invariant_name_regexes) or (
        bool(rule.invariant_module_globs)
        and _path_matches_any(rel_path, rule.invariant_module_globs)
    )


def _selected_file_ban_for(
    rel_path: str,
    name: str,
    rule: ConfigBackedRuntimeConstantsRule,
) -> SelectedFileBan | None:
    for ban in rule.selected_file_bans:
        if rel_path == ban.path and re.match(ban.name_regex, name):
            return ban
    return None


def _candidate_python_files(rule: ConfigBackedRuntimeConstantsRule) -> list[str]:
    rel_paths = iter_python_files(ROOT, roots=rule.source_roots)
    selected: list[str] = []
    for rel_path in rel_paths:
        if _path_matches_any(rel_path, rule.test_path_globs):
            continue
        if _path_matches_any(rel_path, rule.exclude_globs):
            continue
        if not _path_matches_any(rel_path, rule.target_module_globs):
            continue
        selected.append(rel_path)
    return selected


def _load_runtime_constants_tree(
    rel_path: str,
) -> tuple[ast.Module | None, list[RuntimeRuleIssue]]:
    path = ROOT / rel_path
    if not path.exists():
        return (
            None,
            [
                RuntimeRuleIssue(
                    "missing", f"missing runtime-constants scan target: {rel_path}"
                )
            ],
        )
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
    except SyntaxError as exc:
        return (
            None,
            [
                RuntimeRuleIssue(
                    "syntax",
                    f"{rel_path} failed to parse for runtime-constants scan: {exc}",
                )
            ],
        )
    return tree, []


def _issue_for_runtime_constant_name(
    *,
    rel_path: str,
    lineno: int,
    name: str,
    value: ast.AST | None,
    rule: ConfigBackedRuntimeConstantsRule,
) -> RuntimeRuleIssue | None:
    if _is_protocol_dunder_exception(name, rule):
        return None
    if _is_schema_version_exception(name, rel_path, rule):
        return None
    if _is_sentinel_exception(name, rule):
        return None
    if _is_invariant_exception(name, rel_path, rule):
        return None

    selected_ban = _selected_file_ban_for(rel_path, name, rule)
    if selected_ban is not None:
        return RuntimeRuleIssue(
            "runtime_constants",
            f"{rel_path}:{lineno}: {selected_ban.message}",
        )

    if not _is_target_constant_assignment(name, value, rule):
        return None

    authority = ", ".join(rule.authoritative_sources)
    return RuntimeRuleIssue(
        "runtime_constants",
        (
            f"{rel_path}:{lineno}: repo-owned runtime constant '{name}' must be "
            f"config-backed via {authority}"
        ),
    )


def _scan_runtime_constant_assignment(
    *,
    rel_path: str,
    node: ast.AST,
    imports: dict[str, str],
    rule: ConfigBackedRuntimeConstantsRule,
    config_bound_names: set[str],
) -> list[RuntimeRuleIssue]:
    target_names, value = _assignment_target_names(node)
    if not target_names:
        return []

    if value is not None and _expr_uses_approved_loader(
        value,
        imports=imports,
        rule=rule,
        config_bound_names=config_bound_names,
    ):
        config_bound_names.update(target_names)
        return []

    if not _is_literal_backed(value):
        return []

    lineno = getattr(node, "lineno", 1)
    issues: list[RuntimeRuleIssue] = []
    for name in target_names:
        issue = _issue_for_runtime_constant_name(
            rel_path=rel_path,
            lineno=lineno,
            name=name,
            value=value,
            rule=rule,
        )
        if issue is not None:
            issues.append(issue)
    return issues


def _scan_runtime_constants_file(
    rel_path: str,
    rule: ConfigBackedRuntimeConstantsRule,
) -> list[RuntimeRuleIssue]:
    tree, issues = _load_runtime_constants_tree(rel_path)
    if tree is None:
        return issues

    imports = _collect_import_aliases(tree, rel_path)
    config_bound_names: set[str] = set()
    for node in tree.body:
        issues.extend(
            _scan_runtime_constant_assignment(
                rel_path=rel_path,
                node=node,
                imports=imports,
                rule=rule,
                config_bound_names=config_bound_names,
            )
        )

    return issues


def _check_config_backed_runtime_constants(
    payload: Any,
) -> tuple[list[RuntimeRuleIssue], list[RuntimeRuleWarning]]:
    rule, issues = _parse_config_backed_runtime_constants_rule(payload)
    if rule is None:
        return issues, []

    warnings: list[RuntimeRuleWarning] = []
    for rel_path in _candidate_python_files(rule):
        issues.extend(_scan_runtime_constants_file(rel_path, rule))
    return issues, warnings


def evaluate_runtime_rules(
    payload: dict[str, Any] | None = None,
) -> tuple[list[RuntimeRuleIssue], list[RuntimeRuleWarning]]:
    code_rules = payload if payload is not None else _load_rules()
    issues: list[RuntimeRuleIssue] = []
    warnings: list[RuntimeRuleWarning] = []

    sanitation = code_rules.get("sanitation", {})
    if not isinstance(sanitation, dict):
        issues.append(RuntimeRuleIssue("schema", "sanitation must be object"))
    else:
        text_issues, text_warnings = _check_text_entrypoints(
            sanitation.get("entrypoints", sanitation.get("text_entrypoints")),
            section="sanitation.entrypoints",
        )
        issues.extend(text_issues)
        warnings.extend(text_warnings)

    magic_numbers = code_rules.get("magic_numbers", {})
    if not isinstance(magic_numbers, dict):
        issues.append(RuntimeRuleIssue("schema", "magic_numbers must be object"))
    else:
        number_issues, number_warnings = _check_numeric_entrypoints(
            magic_numbers.get(
                "entrypoints", magic_numbers.get("config_backed_entrypoints")
            ),
            section="magic_numbers.entrypoints",
        )
        issues.extend(number_issues)
        warnings.extend(number_warnings)

    runtime_constants_issues, runtime_constants_warnings = (
        _check_config_backed_runtime_constants(
            code_rules.get("config_backed_runtime_constants")
        )
    )
    issues.extend(runtime_constants_issues)
    warnings.extend(runtime_constants_warnings)

    return issues, warnings


def main() -> int:
    issues, warnings = evaluate_runtime_rules()

    if issues:
        print("Policy runtime rules check failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    if warnings:
        print("Policy runtime rules warnings (non-blocking):")
        for warning in warnings:
            print(f"- [{warning.kind}] {warning.message}")
    print("Policy runtime rules check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
