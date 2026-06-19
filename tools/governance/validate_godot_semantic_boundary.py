from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
GODOT_ROOT = ROOT / "godot"

SCRIPT_EXTS = {".gd", ".cs"}
EXCLUDED_PARTS = {
    ".godot",
    "addons",
    "third_party",
    "vendor",
    "external",
    "build",
    ".import",
}
VALID_SUPPRESSIONS = {
    "display-only",
    "adapter-routing",
    "trace-presentation",
    "replay-presentation",
    "diagnostic-presentation",
    "test-fixture",
    "legacy-existing",
}

SEMANTIC_TERMS = (
    "legal",
    "valid",
    "move",
    "collision",
    "gravity",
    "drop",
    "rotation",
    "rotate",
    "score",
    "clear",
    "topology",
    "seam",
    "wrap",
    "neighbor",
    "neighbour",
    "boundary",
    "trace",
    "replay",
)
COORD_TERMS = (
    "move",
    "legal",
    "valid",
    "collision",
    "boundary",
    "seam",
    "wrap",
    "topology",
    "gravity",
    "drop",
    "rotate",
    "rotation",
)
ADAPTER_TOKENS = (
    "core.",
    "adapter.",
    "api.",
    "gdextension.",
    "native.",
    "trace_player.",
    "replay_player.",
)
PRESENTATION_PARTS = {"presentation", "rendering", "traces", "ui", "bundle", "tests"}

SUPPRESSION_RE = re.compile(r"tet4d-semantic-boundary:\s*allow\s+([a-z0-9-]+)")
FUNC_RE = re.compile(r"^\s*func\s+([A-Za-z0-9_]+)")
ASSIGNMENT_RE = re.compile(
    r"^\s*(?:var|const)\s+.*(?:legal|valid|collision|gravity|topology|seam|wrap|boundary|neighbor|neighbour|score)\w*\s*=",
    flags=re.IGNORECASE,
)
DIRECT_STRUCTURE_RE = re.compile(
    r"\b(legal_moves|valid_moves|collision_map|topology_map|neighbor_map|neighbour_map|seam_map|gravity_rules|score_rules)\b",
    flags=re.IGNORECASE,
)
BRANCH_RE = re.compile(
    r"^\s*(?:if|elif|while)\s+.*\b(?:legal|valid|collision|gravity|topology|seam|wrap|boundary|neighbor|neighbour|occupied|score|can_move|is_legal)\b",
    flags=re.IGNORECASE,
)
MANUAL_LOOP_RE = re.compile(
    r"^\s*for\s+.*\bin\s+.*\b(neighbors|neighbours|cells|blocks|pieces)\b",
    flags=re.IGNORECASE,
)
COORD_COMPARE_RE = re.compile(r"\b[xyzw]\b\s*(?:<|>|<=|>=|==)")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


def _is_presentation_path(path: Path) -> bool:
    return any(part in PRESENTATION_PARTS for part in path.parts)


def discover_script_files(root: Path = GODOT_ROOT) -> list[Path]:
    if not root.exists():
        return []
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCRIPT_EXTS:
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
    reason = suppression_reason(line)
    return reason in VALID_SUPPRESSIONS


def has_invalid_suppression(line: str) -> bool:
    reason = suppression_reason(line)
    return reason is not None and reason not in VALID_SUPPRESSIONS


def _strip_strings_and_comments(line: str) -> str:
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
        if char == "#":
            break
        result.append(char)
    return "".join(result)


def _has_semantic_term(text: str, terms: tuple[str, ...] = SEMANTIC_TERMS) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _has_adapter_call(text: str) -> bool:
    lower = text.lower()
    return any(token in lower for token in ADAPTER_TOKENS)


def _function_finding(line: str) -> str | None:
    match = FUNC_RE.search(line)
    if match is None:
        return None
    name = match.group(1).lower()
    if name.startswith("test_"):
        return None
    high_risk_prefixes = (
        "can_",
        "is_",
        "has_",
        "compute_",
        "resolve_",
        "apply_",
        "validate_",
        "check_",
        "find_",
        "get_",
    )
    if name.startswith(high_risk_prefixes) and _has_semantic_term(name):
        return f"suspicious semantic computation: function name `{match.group(1)}`"
    if _has_semantic_term(name) and any(
        verb in name
        for verb in (
            "compute",
            "resolve",
            "validate",
            "check",
            "legal",
            "collision",
            "gravity",
            "score",
        )
    ):
        return f"suspicious semantic computation: function name `{match.group(1)}`"
    return None


def _line_finding(clean_line: str, path: Path, window: str) -> str | None:
    if _has_adapter_call(clean_line):
        return None
    if _is_presentation_path(path):
        return None
    if DIRECT_STRUCTURE_RE.search(clean_line):
        return "suspicious semantic data structure"
    if ASSIGNMENT_RE.search(clean_line):
        return "suspicious semantic assignment"
    if BRANCH_RE.search(clean_line) and not _is_presentation_path(path):
        return "suspicious semantic branch"
    if MANUAL_LOOP_RE.search(clean_line) and _has_semantic_term(window):
        return "suspicious manual rule loop"
    if COORD_COMPARE_RE.search(clean_line) and _has_semantic_term(window, COORD_TERMS):
        return "suspicious boundary logic near coordinate comparison"
    return None


def scan_file(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        line_number = index + 1
        if has_invalid_suppression(line):
            findings.append(
                Finding(
                    path, line_number, "invalid semantic-boundary suppression reason"
                )
            )
            continue
        previous_line = lines[index - 1] if index > 0 else ""
        if has_valid_suppression(line) or has_valid_suppression(previous_line):
            continue

        clean_line = _strip_strings_and_comments(line)
        message = _function_finding(clean_line)
        if message is None:
            start = max(0, index - 2)
            end = min(len(lines), index + 3)
            window = "\n".join(
                _strip_strings_and_comments(item) for item in lines[start:end]
            )
            message = _line_finding(clean_line, path, window)
        if message is not None:
            findings.append(Finding(path, line_number, message))
    return findings


def validate(root: Path = GODOT_ROOT) -> tuple[list[Finding], int]:
    files = discover_script_files(root)
    findings: list[Finding] = []
    for path in files:
        findings.extend(scan_file(path))
    return findings, len(files)


def main() -> int:
    findings, scanned = validate(GODOT_ROOT)
    if scanned == 0:
        print("No Godot scripts found; semantic-boundary validation skipped.")
        return 0
    if findings:
        print("Godot semantic-boundary validation failed:")
        for finding in findings:
            rel = finding.path.relative_to(ROOT).as_posix()
            print(f"- {rel}:{finding.line} {finding.message}")
        return 1
    print("Godot semantic-boundary validation passed.")
    print(f"Scanned {scanned} Godot script files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
