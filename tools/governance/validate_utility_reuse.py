from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re


ROOT = Path(__file__).resolve().parents[2]

VALID_SUPPRESSIONS = {
    "test-fixture",
    "local-one-off",
    "legacy-existing",
    "external-api",
    "godot-lifecycle",
    "adapter-boundary",
    "generated-marker",
}

SOURCE_EXTS = {
    ".py",
    ".gd",
    ".cs",
    ".cpp",
    ".cc",
    ".cxx",
    ".hpp",
    ".hh",
    ".hxx",
    ".h",
}

EXCLUDED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".godot",
    "addons",
    "third_party",
    "vendor",
    "external",
    "build",
    "dist",
    "htmlcov",
}

SCAN_ROOTS = ("tet4d", "src", "tools", "godot", "native", "tests")
SUPPRESSION_RE = re.compile("tet4d-utility-reuse:" + r"\s*allow\s+([a-z0-9-]+)")
PY_DEF_RE = re.compile(r"^\s*(?:async\s+def|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
GD_DEF_RE = re.compile(r"^\s*func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CPP_DEF_RE = re.compile(
    r"^\s*(?:[A-Za-z_][\w:<>,~*&\s]+\s+)+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:const\s*)?(?:\{|$)"
)

IGNORED_NAMES = {
    "main",
    "setUp",
    "tearDown",
    "_ready",
    "_process",
    "_physics_process",
    "_input",
    "_unhandled_input",
    "_notification",
    "_init",
    "_enter_tree",
    "_exit_tree",
}

HIGH_RISK_PREFIXES = (
    "load_",
    "read_",
    "write_",
    "parse_",
    "serialize_",
    "deserialize_",
    "validate_",
    "check_",
    "find_",
    "resolve_",
    "build_",
    "export_",
    "import_",
    "convert_",
    "map_",
    "normalize_",
    "canonicalize_",
    "get_",
    "compute_",
)

HIGH_RISK_CONCEPTS = {
    "config",
    "policy",
    "trace",
    "replay",
    "topology",
    "neighbor",
    "neighbour",
    "seam",
    "wrap",
    "boundary",
    "projection",
    "camera",
    "grid",
    "cell",
    "piece",
    "rotation",
    "gravity",
    "bundle",
    "manifest",
    "schema",
    "path",
    "subprocess",
    "command",
    "json",
}

MINI_FRAMEWORK_NAMES = {
    "run_command",
    "run_cmd",
    "execute_command",
    "call_command",
    "walk_files",
    "iter_files",
    "load_json",
    "read_json",
    "write_json",
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    severity: str
    message: str


@dataclass(frozen=True)
class Symbol:
    name: str
    path: Path
    line: int


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _has_excluded_part(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def discover_source_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for base in SCAN_ROOTS:
        base_path = root / base
        if not base_path.exists():
            continue
        for path in base_path.rglob("*"):
            if not path.is_file() or path.suffix not in SOURCE_EXTS:
                continue
            rel_path = path.relative_to(root)
            if _has_excluded_part(rel_path):
                continue
            files.append(path)
    return sorted(files)


def _suppressed_lines(lines: list[str], issues: list[Finding], path: Path) -> set[int]:
    suppressed: set[int] = set()
    for idx, line in enumerate(lines, start=1):
        match = SUPPRESSION_RE.search(line)
        if match is None:
            continue
        reason = match.group(1)
        if reason not in VALID_SUPPRESSIONS:
            issues.append(
                Finding(
                    path,
                    idx,
                    "blocking",
                    f"invalid utility-reuse suppression reason `{reason}`",
                )
            )
            continue
        suppressed.add(idx)
        suppressed.add(idx + 1)
    return suppressed


def _symbol_name(line: str, suffix: str) -> str | None:
    if suffix == ".py":
        match = PY_DEF_RE.match(line)
    elif suffix == ".gd":
        match = GD_DEF_RE.match(line)
    elif suffix in {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".h"}:
        match = CPP_DEF_RE.match(line)
    else:
        match = None
    return match.group(1) if match else None


def scan_symbols(path: Path) -> tuple[list[Symbol], list[Finding]]:
    issues: list[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [], []
    suppressed = _suppressed_lines(lines, issues, path)
    symbols: list[Symbol] = []
    for lineno, line in enumerate(lines, start=1):
        name = _symbol_name(line, path.suffix)
        if name is None or lineno in suppressed:
            continue
        if name in IGNORED_NAMES or name.startswith("test_"):
            continue
        if name.startswith("_") and name not in MINI_FRAMEWORK_NAMES:
            continue
        if not _is_suspicious_name(name):
            continue
        symbols.append(Symbol(name=name, path=path, line=lineno))
    return symbols, issues


def _is_suspicious_name(name: str) -> bool:
    lower = name.lower()
    if lower in MINI_FRAMEWORK_NAMES:
        return True
    if not lower.startswith(HIGH_RISK_PREFIXES):
        return False
    return any(concept in lower for concept in HIGH_RISK_CONCEPTS)


def _subsystem(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    if not parts:
        return ""
    if parts[0] in {"src", "tests"} and len(parts) >= 3:
        return "/".join(parts[:3])
    if parts[0] in {"tools", "godot", "native"} and len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def _duplicate_findings(symbols: list[Symbol], *, strict: bool) -> list[Finding]:
    by_name: dict[str, list[Symbol]] = {}
    for symbol in symbols:
        by_name.setdefault(symbol.name, []).append(symbol)

    findings: list[Finding] = []
    for name, occurrences in sorted(by_name.items()):
        files = {symbol.path for symbol in occurrences}
        subsystems = {_subsystem(symbol.path) for symbol in occurrences}
        if len(files) < 2 or len(subsystems) < 2:
            continue
        first = sorted(occurrences, key=lambda item: (_rel(item.path), item.line))[0]
        also = ", ".join(
            f"{_rel(symbol.path)}:{symbol.line}"
            for symbol in sorted(
                occurrences, key=lambda item: (_rel(item.path), item.line)
            )[1:4]
        )
        severity = "blocking" if strict else "advisory"
        findings.append(
            Finding(
                first.path,
                first.line,
                severity,
                f"possible duplicate helper name `{name}`; also seen in {also}",
            )
        )
    return findings


def _contains_all(text: str, tokens: tuple[str, ...]) -> bool:
    lower = text.lower()
    return all(token.lower() in lower for token in tokens)


def _read_required(rel: str, issues: list[Finding]) -> str | None:
    path = ROOT / rel
    if not path.exists():
        issues.append(Finding(path, 0, "blocking", f"{rel} missing"))
        return None
    return path.read_text(encoding="utf-8")


def validate_policy_links() -> list[Finding]:
    issues: list[Finding] = []
    utility_index = _read_required("docs/architecture/utility_index.md", issues)
    router = _read_required("docs/governance/README.md", issues)
    checklist = _read_required("docs/governance/review_checklist.md", issues)
    codex_policy = _read_required("docs/governance/codex_policy.md", issues)
    wheel_policy = _read_required(
        "docs/policies/POLICY_NO_REINVENTING_WHEEL.md", issues
    )
    governance_validator = _read_required(
        "tools/governance/validate_governance.py", issues
    )

    if utility_index is not None and not _contains_all(
        utility_index,
        ("Required fields", "Owner", "Reuse rule", "Migration relevance"),
    ):
        issues.append(
            Finding(
                ROOT / "docs/architecture/utility_index.md",
                0,
                "blocking",
                "docs/architecture/utility_index.md missing required utility-index fields",
            )
        )
    if router is not None:
        required = (
            "utility_index",
            "POLICY_NO_REINVENTING_WHEEL",
            "validate_utility_reuse",
            "check_wheel_reuse_rules",
            "check_dedup_dead_code_rules",
        )
        for token in required:
            if token.lower() not in router.lower():
                issues.append(
                    Finding(
                        ROOT / "docs/governance/README.md",
                        0,
                        "blocking",
                        f"docs/governance/README.md missing dependency/reuse token: {token}",
                    )
                )
    if checklist is not None and not _contains_all(
        checklist, ("reuse", "no-reinvention", "utility")
    ):
        issues.append(
            Finding(
                ROOT / "docs/governance/review_checklist.md",
                0,
                "blocking",
                "docs/governance/review_checklist.md lacks reuse/no-reinvention checks",
            )
        )
    if codex_policy is not None and not _contains_all(
        codex_policy, ("search", "helpers", "existing")
    ):
        issues.append(
            Finding(
                ROOT / "docs/governance/codex_policy.md",
                0,
                "blocking",
                "docs/governance/codex_policy.md must require search before adding helpers",
            )
        )
    if wheel_policy is not None and not _contains_all(
        wheel_policy, ("utility index", "existing project utilities")
    ):
        issues.append(
            Finding(
                ROOT / "docs/policies/POLICY_NO_REINVENTING_WHEEL.md",
                0,
                "blocking",
                "docs/policies/POLICY_NO_REINVENTING_WHEEL.md must link dependency and utility reuse policy",
            )
        )
    if (
        governance_validator is not None
        and "validate_utility_reuse" not in governance_validator
    ):
        issues.append(
            Finding(
                ROOT / "tools/governance/validate_governance.py",
                0,
                "blocking",
                "tools/governance/validate_governance.py must run utility reuse validation",
            )
        )
    return issues


def main() -> int:
    strict = os.environ.get("TET4D_STRICT_UTILITY_REUSE") == "1"
    findings = validate_policy_links()
    symbols: list[Symbol] = []
    scanned_files = discover_source_files(ROOT)
    for path in scanned_files:
        path_symbols, path_findings = scan_symbols(path)
        symbols.extend(path_symbols)
        findings.extend(path_findings)
    findings.extend(_duplicate_findings(symbols, strict=strict))

    blocking = [finding for finding in findings if finding.severity == "blocking"]
    advisory = [finding for finding in findings if finding.severity == "advisory"]

    if blocking:
        print("Utility reuse validation failed:")
        for finding in blocking:
            location = _rel(finding.path)
            if finding.line:
                location = f"{location}:{finding.line}"
            print(f"- {location} {finding.message}")
        return 1

    if advisory:
        print("Utility reuse advisory warnings:")
        for finding in advisory[:25]:
            print(f"- {_rel(finding.path)}:{finding.line} {finding.message}")
        if len(advisory) > 25:
            print(f"- ... {len(advisory) - 25} additional advisory findings omitted")

    print("Utility reuse validation passed.")
    print(f"Scanned {len(scanned_files)} source-like files.")
    print(
        "Duplicate-helper findings: "
        f"{sum(1 for finding in findings if finding.severity == 'blocking')} blocking, "
        f"{len(advisory)} advisory."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
