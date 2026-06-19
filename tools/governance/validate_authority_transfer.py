from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_REL = "docs/architecture/authority_transfer_protocol.md"
PROTOCOL = ROOT / PROTOCOL_REL

REQUIRED_FILES = (
    PROTOCOL_REL,
    "docs/architecture/authority_map.md",
    "docs/architecture/parity_protocol.md",
    "docs/governance/godot_cpp_policy.md",
    "docs/governance/cpp_safety_policy.md",
    "docs/governance/testing_policy.md",
    "docs/governance/drift_protection_map.md",
    "docs/governance/README.md",
    "docs/governance/review_checklist.md",
    "tools/governance/validate_authority_transfer.py",
    "tools/governance/validate_governance.py",
    "tools/governance/validate_project_contracts.py",
    "tools/governance/validate_drift_protection.py",
)

REQUIRED_COLUMNS = (
    "id",
    "subsystem",
    "current_authority",
    "candidate_authority",
    "scope",
    "python_oracle",
    "golden_fixtures",
    "comparison_command",
    "known_exclusions",
    "fallback_path",
    "authority_map_update",
    "validation",
    "status",
    "notes",
)

ALLOWED_STATUSES = {"candidate", "blocked", "ready", "transferred", "retired"}
TRANSFER_ID_RE = re.compile(r"^AT-\d{4}$")
PLACEHOLDERS = {"tbd", "todo", "none", "n/a", "unknown", "not yet", "deferred"}

DANGEROUS_AUTHORITY_PHRASES = (
    "c++ is authoritative for gameplay",
    "c++ owns tet4d semantics",
    "c++ owns gameplay semantics",
    "gdextension is authoritative for gameplay",
    "native core is the source of truth",
    "godot owns movement rules",
    "godot owns collision rules",
    "godot owns topology",
    "gdscript owns topology",
    "gdscript owns gameplay semantics",
)

AUTHORITY_EXEMPTION_PHRASES = (
    "provisional",
    "candidate",
    "until parity",
    "after parity",
    "after authority transfer",
    "once transferred",
    "completed transfer record",
    "does not transfer authority",
    "necessary but not sufficient",
    "may not claim",
    "must not claim",
    "no policy claims",
)

SCAN_RELS = (
    "AGENTS.md",
    "godot/AGENTS.md",
    "native/AGENTS.md",
)


@dataclass(frozen=True)
class TransferRecord:
    id: str
    subsystem: str
    current_authority: str
    candidate_authority: str
    scope: str
    python_oracle: str
    golden_fixtures: str
    comparison_command: str
    known_exclusions: str
    fallback_path: str
    authority_map_update: str
    validation: str
    status: str
    notes: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    failures: list[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_rel(root: Path, rel: str, failures: list[str] | None = None) -> str:
    path = root / rel
    try:
        return read_text(path)
    except FileNotFoundError:
        if failures is not None:
            failures.append(f"missing required path: {rel}")
        return ""


def _has_any(text: str, options: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(option.lower() in lower for option in options)


def contains_concepts(text: str, concepts: dict[str, tuple[str, ...]]) -> list[str]:
    return [name for name, options in concepts.items() if not _has_any(text, options)]


def _split_table_row(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def _table_lines_after_heading(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if not in_section:
            continue
        if line.startswith("## ") and table:
            break
        if line.strip().startswith("|"):
            table.append(line)
        elif table and line.strip():
            break
    return table


def parse_transfer_records(text: str) -> tuple[list[TransferRecord], list[str]]:
    table = _table_lines_after_heading(text, "## Transfer records")
    if len(table) < 2:
        return [], ["authority transfer protocol must contain a transfer records table"]

    header = _split_table_row(table[0])
    if header != list(REQUIRED_COLUMNS):
        return [], [
            "transfer records table has invalid columns; expected "
            + ", ".join(REQUIRED_COLUMNS)
        ]

    rows = [_split_table_row(line) for line in table[1:]]
    if rows and _is_separator_row(rows[0]):
        rows = rows[1:]

    records: list[TransferRecord] = []
    issues: list[str] = []
    for index, cells in enumerate(rows, start=1):
        if len(cells) != len(REQUIRED_COLUMNS):
            issues.append(f"transfer row {index} has {len(cells)} cells")
            continue
        raw = dict(zip(REQUIRED_COLUMNS, cells, strict=True))
        records.append(TransferRecord(**raw))
    return records, issues


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized in PLACEHOLDERS


def _validate_record_fields(records: list[TransferRecord]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    required_non_notes = [field for field in REQUIRED_COLUMNS if field != "notes"]
    for record in records:
        for field in required_non_notes:
            value = getattr(record, field)
            if _is_placeholder(value):
                failures.append(
                    f"{record.id or '<missing>'} has empty or placeholder `{field}`"
                )
        if not TRANSFER_ID_RE.match(record.id):
            failures.append(f"{record.id or '<missing>'} has invalid transfer id")
        if record.id in seen:
            failures.append(f"{record.id} is duplicated")
        seen.add(record.id)
        if record.status not in ALLOWED_STATUSES:
            failures.append(f"{record.id} has invalid status `{record.status}`")
        if (
            record.status != "retired"
            and "python" not in record.current_authority.lower()
        ):
            failures.append(f"{record.id} current_authority must include Python")
        if record.status == "transferred":
            for field in (
                "golden_fixtures",
                "comparison_command",
                "authority_map_update",
                "validation",
            ):
                if _is_placeholder(getattr(record, field)):
                    failures.append(
                        f"{record.id} transferred row has placeholder `{field}`"
                    )
    return failures


def check_required_files(root: Path = ROOT) -> CheckResult:
    failures = [
        f"missing required file: {rel}"
        for rel in REQUIRED_FILES
        if not (root / rel).exists()
    ]
    return CheckResult("required files", failures)


def check_router_links(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    required_links = {
        "docs/governance/README.md": (
            PROTOCOL_REL,
            "tools/governance/validate_authority_transfer.py",
        ),
        "docs/architecture/authority_map.md": (PROTOCOL_REL,),
        "docs/architecture/parity_protocol.md": (PROTOCOL_REL,),
    }
    for rel, links in required_links.items():
        text = _read_rel(root, rel, failures)
        for link in links:
            if link not in text:
                failures.append(f"{rel} does not link to {link}")

    drift_map = _read_rel(root, "docs/governance/drift_protection_map.md", failures)
    for token in ("authority_transfer_protocol.md", "validate_authority_transfer.py"):
        if token not in drift_map:
            failures.append(
                f"docs/governance/drift_protection_map.md does not mention {token}"
            )
    return CheckResult("router links", failures)


def check_protocol_contents(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    text = _read_rel(root, PROTOCOL_REL, failures)
    concepts = {
        "Python current semantic oracle": ("semantic oracle", "python"),
        "Godot shell/presentation": ("product shell", "presentation", "ui"),
        "C++/GDExtension provisional": ("c++", "gdextension", "provisional"),
        "parity necessary but not sufficient": ("necessary but not sufficient",),
        "only transferred changes authority": ("only `transferred` changes authority",),
        "transfer records table": ("## transfer records",),
        "required fields": ("required transfer record fields",),
        "allowed statuses": ("allowed statuses",),
        "fallback path": ("fallback",),
        "authority map update": ("authority_map_update", "authority map"),
        "comparison command": ("comparison_command", "comparison command"),
        "known exclusions": ("known_exclusions", "known exclusions"),
    }
    for concept in contains_concepts(text, concepts):
        failures.append(f"{PROTOCOL_REL} is missing concept `{concept}`")
    return CheckResult("protocol contents", failures)


def check_transfer_table(root: Path = ROOT) -> tuple[CheckResult, list[TransferRecord]]:
    failures: list[str] = []
    text = _read_rel(root, PROTOCOL_REL, failures)
    records, parse_failures = parse_transfer_records(text)
    failures.extend(parse_failures)
    failures.extend(_validate_record_fields(records))
    return CheckResult("transfer table", failures), records


def _scan_markdown_rels(root: Path) -> list[str]:
    rels = list(SCAN_RELS)
    for directory in ("docs/governance", "docs/architecture", "docs/policies"):
        base = root / directory
        if not base.exists():
            continue
        rels.extend(
            path.relative_to(root).as_posix() for path in sorted(base.glob("*.md"))
        )
    return sorted(set(rels))


def _has_exemption_near(lines: list[str], index: int) -> bool:
    start = max(0, index - 1)
    end = min(len(lines), index + 2)
    window = "\n".join(lines[start:end]).lower()
    return any(exemption in window for exemption in AUTHORITY_EXEMPTION_PHRASES)


def check_dangerous_authority_claims(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    for rel in _scan_markdown_rels(root):
        path = root / rel
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            lower = line.lower()
            if _has_exemption_near(lines, index):
                continue
            for phrase in DANGEROUS_AUTHORITY_PHRASES:
                if phrase in lower:
                    failures.append(
                        f'Dangerous authority claim in {rel}: "{line.strip()}"'
                    )
    return CheckResult("dangerous authority claims", failures)


def check_authority_map_consistency(
    records: list[TransferRecord], root: Path = ROOT
) -> CheckResult:
    failures: list[str] = []
    authority_map = _read_rel(root, "docs/architecture/authority_map.md", failures)
    lower = authority_map.lower()
    transferred = [record for record in records if record.status == "transferred"]
    if not transferred:
        if "python" not in lower or "semantic oracle" not in lower:
            failures.append(
                "authority_map.md must continue saying Python is current semantic oracle"
            )
        return CheckResult("authority-map consistency", failures)

    for record in transferred:
        mentions_id = record.id.lower() in lower
        mentions_transfer = (
            record.subsystem.lower() in lower
            and record.candidate_authority.lower() in lower
        )
        if not (mentions_id or mentions_transfer):
            failures.append(
                f"authority_map.md does not mention transferred record {record.id}"
            )
    return CheckResult("authority-map consistency", failures)


def check_parity_protocol_consistency(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    text = _read_rel(root, "docs/architecture/parity_protocol.md", failures)
    lower = text.lower()
    if PROTOCOL_REL not in text:
        failures.append(
            f"docs/architecture/parity_protocol.md does not link to {PROTOCOL_REL}"
        )
    if "necessary but not sufficient" not in lower or "transfer record" not in lower:
        failures.append(
            "docs/architecture/parity_protocol.md must say parity does not itself transfer authority"
        )
    return CheckResult("parity-protocol consistency", failures)


def check_policy_consistency(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    godot = _read_rel(root, "docs/governance/godot_cpp_policy.md", failures)
    godot_lower = godot.lower()
    if not (
        "gdscript" in godot_lower
        and "semantic" in godot_lower
        and ("must not" in godot_lower or "does not" in godot_lower)
    ):
        failures.append(
            "docs/governance/godot_cpp_policy.md must say GDScript/Godot does not own semantic truth"
        )
    if "authority_transfer_protocol.md" not in godot:
        failures.append(
            "docs/governance/godot_cpp_policy.md must refer to authority transfer protocol"
        )

    cpp = _read_rel(root, "docs/governance/cpp_safety_policy.md", failures)
    cpp_lower = cpp.lower()
    if not ("provisional" in cpp_lower or "parity" in cpp_lower):
        failures.append(
            "docs/governance/cpp_safety_policy.md must say C++ authority is provisional or parity-gated"
        )
    if "authority_transfer_protocol.md" not in cpp:
        failures.append(
            "docs/governance/cpp_safety_policy.md must refer to authority transfer protocol"
        )
    return CheckResult("Godot/C++ policy consistency", failures)


def check_review_checklist(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    text = _read_rel(root, "docs/governance/review_checklist.md", failures)
    concepts = {
        "authority transfer": ("authority transfer",),
        "parity evidence": ("parity evidence", "golden traces"),
        "authority map": ("authority map",),
        "fallback path": ("fallback path",),
        "known exclusions": ("known exclusions",),
    }
    for concept in contains_concepts(text, concepts):
        failures.append(
            f"docs/governance/review_checklist.md is missing concept `{concept}`"
        )
    return CheckResult("review checklist", failures)


def validate(root: Path = ROOT) -> tuple[list[CheckResult], list[TransferRecord]]:
    transfer_table_result, records = check_transfer_table(root)
    results = [
        check_required_files(root),
        check_router_links(root),
        check_protocol_contents(root),
        transfer_table_result,
        check_dangerous_authority_claims(root),
        check_authority_map_consistency(records, root),
        check_parity_protocol_consistency(root),
        check_policy_consistency(root),
        check_review_checklist(root),
    ]
    return results, records


def main() -> int:
    results, records = validate(ROOT)
    failures = [failure for result in results for failure in result.failures]
    if failures:
        print("Authority transfer validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    transferred = [record for record in records if record.status == "transferred"]
    print("Authority transfer validation passed.")
    print(f"Transfer records: {len(records)}")
    print(f"Transferred subsystems: {len(transferred)}")
    print("Checks:")
    for result in results:
        print(f"- {result.name}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
