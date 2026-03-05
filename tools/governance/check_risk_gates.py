from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
RISK_GATES_PATH = ROOT / "config/project/policy/manifests/risk_gates.json"
DIRECTIVES_PATH = ROOT / "config/project/policy/manifests/contributor_directives.json"


@dataclass(frozen=True)
class GateIssue:
    kind: str
    message: str


@dataclass(frozen=True)
class GateWarning:
    kind: str
    message: str


def _load_json(path: Path, rel: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing required file: {rel}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {rel}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"{rel} must be a JSON object")
    return payload


def _is_ci_enforced(token: str) -> bool:
    return token.startswith("scripts/") or token.startswith("tools/")


def _check_contributor_directives(
    risk_payload: dict[str, Any], directives_payload: dict[str, Any]
) -> list[GateIssue]:
    issues: list[GateIssue] = []
    required_ids = risk_payload.get("contributor_directives", {}).get(
        "required_ci_enforced_ids", []
    )
    if not isinstance(required_ids, list):
        return [
            GateIssue("schema", "risk_gates contributor_directives ids must be list")
        ]
    directives = directives_payload.get("directives", [])
    if not isinstance(directives, list):
        return [GateIssue("schema", "contributor_directives.directives must be list")]

    by_id: dict[str, dict[str, Any]] = {
        str(item.get("id")): item for item in directives if isinstance(item, dict)
    }
    for directive_id in required_ids:
        if not isinstance(directive_id, str):
            issues.append(
                GateIssue("schema", "required_ci_enforced_ids must contain strings")
            )
            continue
        directive = by_id.get(directive_id)
        if directive is None:
            issues.append(GateIssue("missing", f"missing directive id: {directive_id}"))
            continue
        enforced_by = directive.get("enforced_by", [])
        if not isinstance(enforced_by, list):
            issues.append(
                GateIssue(
                    "schema", f"directive {directive_id} enforced_by must be list[str]"
                )
            )
            continue
        if not any(
            isinstance(token, str) and _is_ci_enforced(token) for token in enforced_by
        ):
            issues.append(
                GateIssue(
                    "enforcement",
                    f"directive {directive_id} has no CI/script enforcement token",
                )
            )
    return issues


def _normalize_dep_name(raw: str) -> str:
    match = re.match(r"^[A-Za-z0-9_.-]+", raw.strip())
    if not match:
        return ""
    return match.group(0).lower().replace("_", "-")


def _add_normalized_dependencies(raw_values: Any, out: set[str]) -> None:
    if not isinstance(raw_values, list):
        return
    for raw in raw_values:
        if not isinstance(raw, str):
            continue
        dep = _normalize_dep_name(raw)
        if dep:
            out.add(dep)


def _iter_optional_dependency_groups(optional: Any) -> list[Any]:
    if not isinstance(optional, dict):
        return []
    return list(optional.values())


def _read_pyproject_dependencies(pyproject_path: Path) -> set[str]:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    out: set[str] = set()
    project = payload.get("project", {})
    if not isinstance(project, dict):
        return out

    _add_normalized_dependencies(project.get("dependencies", []), out)
    optional = project.get("optional-dependencies", {})
    for group_values in _iter_optional_dependency_groups(optional):
        _add_normalized_dependencies(group_values, out)
    return out


def _check_dependency_policy(risk_payload: dict[str, Any]) -> list[GateIssue]:
    issues: list[GateIssue] = []
    dependency_policy = risk_payload.get("dependency_policy", {})
    if not isinstance(dependency_policy, dict):
        return [GateIssue("schema", "dependency_policy must be object")]

    pyproject_rel = str(dependency_policy.get("pyproject_path", "pyproject.toml"))
    pyproject_path = ROOT / pyproject_rel
    if not pyproject_path.exists():
        return [GateIssue("missing", f"missing dependency source: {pyproject_rel}")]

    blocked = dependency_policy.get("blocked_dependencies", [])
    if not isinstance(blocked, list) or any(
        not isinstance(item, str) for item in blocked
    ):
        issues.append(GateIssue("schema", "blocked_dependencies must be list[str]"))
    else:
        deps = _read_pyproject_dependencies(pyproject_path)
        blocked_normalized = {
            _normalize_dep_name(item) for item in blocked if _normalize_dep_name(item)
        }
        violated = sorted(dep for dep in deps if dep in blocked_normalized)
        if violated:
            issues.append(
                GateIssue(
                    "dependency_policy",
                    f"blocked dependencies present: {', '.join(violated)}",
                )
            )

    require_pip_check = bool(dependency_policy.get("require_pip_check", True))
    if require_pip_check:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            detail = (
                result.stdout.strip() or result.stderr.strip() or "pip check failed"
            )
            issues.append(GateIssue("dependency_policy", detail))
    return issues


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _match_sensitive_files(globs: list[str]) -> list[str]:
    tracked = _git_lines("ls-files")
    if not globs:
        return []
    matched = [
        path for path in tracked if any(fnmatch(path, pattern) for pattern in globs)
    ]
    return sorted(set(matched))


def _distinct_authors_for_file(path: str) -> int:
    authors = _git_lines("log", "--format=%ae", "--", path)
    return len(set(authors))


def _ownership_config(
    ownership: dict[str, Any],
) -> tuple[int, int, int, int]:
    min_authors = max(1, int(ownership.get("min_distinct_authors_per_file", 1)))
    max_below = max(0, int(ownership.get("max_files_below_min_authors", 0)))
    target_min_authors = max(
        min_authors,
        int(ownership.get("target_min_distinct_authors_per_file", min_authors)),
    )
    max_below_target_warn = max(
        0, int(ownership.get("max_files_below_target_authors_warn", 0))
    )
    return min_authors, max_below, target_min_authors, max_below_target_warn


def _scope_size_issue(
    matched_files: list[str], *, min_sensitive_files: int
) -> list[GateIssue]:
    if len(matched_files) >= min_sensitive_files:
        return []
    return [
        GateIssue(
            "security_ownership",
            (
                f"sensitive ownership scope too small: matched={len(matched_files)} "
                f"< min_sensitive_files={min_sensitive_files}"
            ),
        )
    ]


def _ownership_counts(
    matched_files: list[str], *, min_authors: int, target_min_authors: int
) -> tuple[list[str], list[str]]:
    below_min: list[str] = []
    below_target: list[str] = []
    for path in matched_files:
        authors = _distinct_authors_for_file(path)
        if authors < min_authors:
            below_min.append(path)
        if authors < target_min_authors:
            below_target.append(path)
    return below_min, below_target


def _check_security_ownership(
    risk_payload: dict[str, Any],
) -> tuple[list[GateIssue], list[GateWarning]]:
    ownership = risk_payload.get("security_ownership", {})
    if not isinstance(ownership, dict):
        return [GateIssue("schema", "security_ownership must be object")], []
    if not bool(ownership.get("enabled", True)):
        return [], []

    sensitive_globs = ownership.get("sensitive_globs", [])
    if not isinstance(sensitive_globs, list) or any(
        not isinstance(item, str) for item in sensitive_globs
    ):
        return [
            GateIssue("schema", "security_ownership.sensitive_globs must be list[str]")
        ], []

    min_authors, max_below, target_min_authors, max_below_target_warn = (
        _ownership_config(ownership)
    )

    matched_files = _match_sensitive_files(sensitive_globs)
    min_sensitive_files = int(ownership.get("min_sensitive_files", 1))
    min_sensitive_files = max(1, min_sensitive_files)
    scope_issues = _scope_size_issue(
        matched_files, min_sensitive_files=min_sensitive_files
    )
    if scope_issues:
        return scope_issues, []
    if not matched_files:
        return [], []

    below_min, below_target = _ownership_counts(
        matched_files, min_authors=min_authors, target_min_authors=target_min_authors
    )
    if len(below_min) > max_below:
        sample = ", ".join(below_min[:8])
        return [
            GateIssue(
                "security_ownership",
                (
                    f"sensitive files below ownership threshold: {len(below_min)} > {max_below} "
                    f"(min_authors={min_authors}); sample: {sample}"
                ),
            )
        ], []

    warnings: list[GateWarning] = []
    if len(below_target) > max_below_target_warn:
        sample = ", ".join(below_target[:8])
        warnings.append(
            GateWarning(
                "security_ownership",
                (
                    f"warning: sensitive files below target ownership threshold: "
                    f"{len(below_target)} > {max_below_target_warn} "
                    f"(target_min_authors={target_min_authors}); sample: {sample}"
                ),
            )
        )
    return [], warnings


def main() -> int:
    risk_payload = _load_json(
        RISK_GATES_PATH, "config/project/policy/manifests/risk_gates.json"
    )
    directives_payload = _load_json(
        DIRECTIVES_PATH,
        "config/project/policy/manifests/contributor_directives.json",
    )

    issues: list[GateIssue] = []
    warnings: list[GateWarning] = []
    issues.extend(_check_contributor_directives(risk_payload, directives_payload))
    issues.extend(_check_dependency_policy(risk_payload))
    security_issues, security_warnings = _check_security_ownership(risk_payload)
    issues.extend(security_issues)
    warnings.extend(security_warnings)

    if issues:
        print("Risk gate check failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    if warnings:
        print("Risk gate warnings (non-blocking):")
        for warning in warnings:
            print(f"- [{warning.kind}] {warning.message}")
    print("Risk gate check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
