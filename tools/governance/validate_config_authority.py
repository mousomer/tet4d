from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

SOURCE_ROOTS = ("tet4d", "src", "tools", "godot", "native", "tests")
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
    ".venv312",
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
    "exported_bundle",
    "tet4d_bundle",
    "golden_traces",
}
VALID_SUPPRESSIONS = {
    "trivial-index",
    "test-fixture",
    "display-label",
    "version-string",
    "file-extension",
    "generated-marker",
    "legacy-existing",
    "external-api",
    "schema-example",
}
REQUIRED_POLICY_DOCS = (
    "docs/governance/config_policy.md",
    "docs/policies/POLICY_NO_MAGIC_NUMBERS.md",
    "docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md",
    "docs/policies/INDEX.md",
)
STANDARD_CONFIG_REFS = (
    "config/project/policy_pack.json",
    "config/project/constants.json",
    "config/gameplay/tuning.json",
    "config/menu/defaults.json",
    "docs/CONFIGURATION_REFERENCE.md",
)
GENERATED_REFERENCE_DOCS = (
    "docs/CONFIGURATION_REFERENCE.md",
    "docs/USER_SETTINGS_REFERENCE.md",
)
SUSPICIOUS_CONTEXT_TERMS = (
    "speed",
    "duration",
    "timeout",
    "interval",
    "alpha",
    "opacity",
    "fade",
    "camera",
    "zoom",
    "margin",
    "cell",
    "grid",
    "board",
    "width",
    "height",
    "depth",
    "score",
    "gravity",
    "trace",
    "trail",
    "projection",
    "w_slice",
    "slice",
    "layer",
    "topology",
    "rotation",
    "collision",
    "limit",
    "threshold",
    "radius",
    "scale",
    "size",
    "fps",
)
ALLOWED_NUMBERS = {"-1", "0", "1", "2"}

SUPPRESSION_RE = re.compile("tet4d-config-authority:" + r"\s*allow\s+([a-z0-9-]+)")
NUMBER_RE = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w.])")
CONFIG_PATH_RE = re.compile(
    r"""["'](?:config|docs)/(?:[^"']+)\.(?:json|md|toml|yaml|yml)["']"""
)


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    severity: str
    message: str


def _is_strict() -> bool:
    return os.environ.get("TET4D_STRICT_CONFIG_AUTHORITY") == "1"


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def _is_test_path(path: Path) -> bool:
    return "tests" in path.parts or path.name.startswith("test_")


def discover_source_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for rel in SOURCE_ROOTS:
        directory = root / rel
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SOURCE_EXTS:
                continue
            relative = path.relative_to(root)
            if _is_excluded(relative):
                continue
            files.append(path)
    return sorted(files)


def suppression_reason(line: str) -> str | None:
    match = SUPPRESSION_RE.search(line)
    if match is None:
        return None
    return match.group(1)


def has_valid_suppression(line: str) -> bool:
    return suppression_reason(line) in VALID_SUPPRESSIONS


def has_invalid_suppression(line: str) -> bool:
    reason = suppression_reason(line)
    return reason is not None and reason not in VALID_SUPPRESSIONS


def _strip_strings_and_comments(line: str, suffix: str) -> str:
    comment_prefix = "#" if suffix in {".py", ".gd"} else "//"
    result: list[str] = []
    quote: str | None = None
    escape = False
    index = 0
    while index < len(line):
        char = line[index]
        if quote is not None:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            result.append(" ")
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            index += 1
            continue
        if line.startswith(comment_prefix, index):
            break
        result.append(char)
        index += 1
    return "".join(result)


def _strip_strings(line: str) -> str:
    result: list[str] = []
    quote: str | None = None
    escape = False
    for char in line:
        if quote is not None:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
            result.append(" ")
            continue
        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            continue
        result.append(char)
    return "".join(result)


def _has_suspicious_context(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in SUSPICIOUS_CONTEXT_TERMS)


def _is_allowed_number(raw: str, line: str) -> bool:
    if raw in ALLOWED_NUMBERS:
        return True
    if raw.startswith("-") and raw[1:] in ALLOWED_NUMBERS:
        return True
    if re.search(r"\b(version|schema_version|trace_version|format_version)\b", line):
        return True
    return False


def _line_findings(
    path: Path, line_number: int, line: str, previous: str
) -> list[Finding]:
    suppression_line = _strip_strings(line)
    previous_suppression_line = _strip_strings(previous)
    if has_invalid_suppression(suppression_line):
        reason = suppression_reason(suppression_line) or ""
        return [
            Finding(
                path,
                line_number,
                "error",
                f"invalid config-authority suppression reason `{reason}`",
            )
        ]
    if has_valid_suppression(suppression_line) or has_valid_suppression(
        previous_suppression_line
    ):
        return []
    if _is_test_path(path):
        return []

    findings: list[Finding] = []
    clean = _strip_strings_and_comments(line, path.suffix.lower())
    if _has_suspicious_context(clean):
        for match in NUMBER_RE.finditer(clean):
            raw = match.group(0)
            if _is_allowed_number(raw, clean):
                continue
            findings.append(
                Finding(
                    path,
                    line_number,
                    "advisory",
                    f"suspicious literal {raw} near config-owned context",
                )
            )
    if CONFIG_PATH_RE.search(line) and "tools/governance" not in path.as_posix():
        findings.append(
            Finding(
                path,
                line_number,
                "advisory",
                "hardcoded config/reference path; consider standard config authority access",
            )
        )
    return findings


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        previous = lines[index - 1] if index > 0 else ""
        findings.extend(_line_findings(path, index + 1, line, previous))
    return findings


def _read_text(root: Path, rel: str, findings: list[Finding]) -> str:
    path = root / rel
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        findings.append(
            Finding(path, 1, "error", f"missing required config policy doc: {rel}")
        )
        return ""


def validate_policy_links(root: Path = ROOT) -> list[Finding]:
    findings: list[Finding] = []
    docs = {rel: _read_text(root, rel, findings) for rel in REQUIRED_POLICY_DOCS}

    config_policy = docs.get("docs/governance/config_policy.md", "")
    lower_config = config_policy.lower()
    for token in (
        "config authority",
        "docs/policies/policy_no_magic_numbers.md",
        "config/project/constants.json",
        "config/gameplay/tuning.json",
        "config/menu/defaults.json",
    ):
        if token not in lower_config:
            findings.append(
                Finding(
                    root / "docs/governance/config_policy.md",
                    1,
                    "error",
                    f"config policy missing standard config authority reference: {token}",
                )
            )
    if "python configuration remains authoritative" not in lower_config:
        findings.append(
            Finding(
                root / "docs/governance/config_policy.md",
                1,
                "error",
                "config policy must preserve Python configuration authority",
            )
        )

    no_magic = docs.get("docs/policies/POLICY_NO_MAGIC_NUMBERS.md", "").lower()
    if "docs/governance/config_policy.md" not in no_magic:
        findings.append(
            Finding(
                root / "docs/policies/POLICY_NO_MAGIC_NUMBERS.md",
                1,
                "error",
                "no-magic-number policy must refer to governance config policy",
            )
        )

    config_docs = docs.get("docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md", "")
    for token in STANDARD_CONFIG_REFS:
        if token not in config_docs:
            findings.append(
                Finding(
                    root / "docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md",
                    1,
                    "error",
                    f"configuration documentation policy missing authority reference: {token}",
                )
            )

    for rel in GENERATED_REFERENCE_DOCS:
        text = (root / rel).read_text(encoding="utf-8") if (root / rel).exists() else ""
        lower = text.lower()
        if text and (
            "generated from repo config sources" not in lower
            or "do not edit" not in lower
        ):
            findings.append(
                Finding(
                    root / rel,
                    1,
                    "error",
                    f"{rel} must identify itself as generated, not hand-authored authority",
                )
            )
    return findings


def validate(root: Path = ROOT) -> tuple[list[Finding], int]:
    findings = validate_policy_links(root)
    files = discover_source_files(root)
    for path in files:
        findings.extend(scan_file(path))
    return findings, len(files)


def main() -> int:
    strict = _is_strict()
    findings, scanned = validate(ROOT)
    errors = [finding for finding in findings if finding.severity == "error"]
    advisories = [finding for finding in findings if finding.severity == "advisory"]
    blocking = errors + (advisories if strict else [])

    if blocking:
        print("Config authority validation failed:")
        for finding in blocking[:25]:
            rel = finding.path.relative_to(ROOT).as_posix()
            print(f"- {rel}:{finding.line} {finding.message}")
        if len(blocking) > 25:
            print(f"- ... {len(blocking) - 25} more blocking findings")
        return 1

    if advisories:
        print("Config authority advisory warnings:")
        for finding in advisories[:25]:
            rel = finding.path.relative_to(ROOT).as_posix()
            print(f"- {rel}:{finding.line} {finding.message}")
        if len(advisories) > 25:
            print(f"- ... {len(advisories) - 25} more advisory findings")

    print("Config authority validation passed.")
    print(f"Scanned {scanned} source-like files.")
    print(f"Suspicious constants: 0 blocking, {len(advisories)} advisory.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
