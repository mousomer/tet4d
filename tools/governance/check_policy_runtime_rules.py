from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

if __package__:
    from ._common import as_str_list, load_json_object
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    from _common import as_str_list, load_json_object


ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "config/project/policy/manifests/policy_runtime_rules.json"


@dataclass(frozen=True)
class RuntimeRuleIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class RuntimeRuleWarning:
    kind: str
    message: str


def _load_rules() -> dict[str, Any]:
    rel = "config/project/policy/manifests/policy_runtime_rules.json"
    return load_json_object(RULES_PATH, rel)


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


def main() -> int:
    payload = _load_rules()
    issues: list[RuntimeRuleIssue] = []
    warnings: list[RuntimeRuleWarning] = []

    sanitation = payload.get("sanitation", {})
    if not isinstance(sanitation, dict):
        issues.append(RuntimeRuleIssue("schema", "sanitation must be object"))
    else:
        text_issues, text_warnings = _check_text_entrypoints(
            sanitation.get("text_entrypoints"),
            section="sanitation.text_entrypoints",
        )
        issues.extend(text_issues)
        warnings.extend(text_warnings)

    magic_numbers = payload.get("magic_numbers", {})
    if not isinstance(magic_numbers, dict):
        issues.append(RuntimeRuleIssue("schema", "magic_numbers must be object"))
    else:
        number_issues, number_warnings = _check_numeric_entrypoints(
            magic_numbers.get("config_backed_entrypoints"),
            section="magic_numbers.config_backed_entrypoints",
        )
        issues.extend(number_issues)
        warnings.extend(number_warnings)

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
