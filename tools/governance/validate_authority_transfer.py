from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_REL = "docs/architecture/authority_transfer_protocol.md"
PROTOCOL = ROOT / PROTOCOL_REL

REQUIRED_FILES = (
    PROTOCOL_REL,
    "docs/architecture/authority_map.md",
    "docs/architecture/parity_protocol.md",
    "docs/plans/professional_godot_game_programme.md",
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

TRANSFER_COLUMNS = (
    "id",
    "operation",
    "subsystem",
    "current_authority",
    "candidate_authority",
    "scope",
    "reference_implementation",
    "golden_fixtures",
    "comparison_command",
    "known_exclusions",
    "fallback_path",
    "authority_map_update",
    "validation",
    "status",
    "notes",
)

ESTABLISHMENT_COLUMNS = (
    "id",
    "operation",
    "subsystem",
    "normative_contract",
    "implementation_authority",
    "data_authority",
    "scope",
    "semantic_boundaries",
    "conformance_evidence",
    "compatibility_rules",
    "known_exclusions",
    "safe_failure_or_fallback",
    "authority_map_update",
    "validation",
    "status",
    "notes",
)

# Compatibility alias for older callers and tests that imported REQUIRED_COLUMNS.
REQUIRED_COLUMNS = TRANSFER_COLUMNS

TRANSFER_STATUSES = {"candidate", "blocked", "ready", "transferred", "retired"}
ESTABLISHMENT_STATUSES = {
    "proposed",
    "blocked",
    "ready",
    "established",
    "retired",
}
TRANSFER_ID_RE = re.compile(r"^AT-\d{4}$")
ESTABLISHMENT_ID_RE = re.compile(r"^AE-\d{4}$")
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
    "authority establishment",
    "established record",
    "when established",
    "without a predecessor",
)

SCAN_RELS = (
    "AGENTS.md",
    "godot/AGENTS.md",
    "native/AGENTS.md",
)


@dataclass(frozen=True)
class TransferRecord:
    id: str
    operation: str
    subsystem: str
    current_authority: str
    candidate_authority: str
    scope: str
    reference_implementation: str
    golden_fixtures: str
    comparison_command: str
    known_exclusions: str
    fallback_path: str
    authority_map_update: str
    validation: str
    status: str
    notes: str


@dataclass(frozen=True)
class EstablishmentRecord:
    id: str
    operation: str
    subsystem: str
    normative_contract: str
    implementation_authority: str
    data_authority: str
    scope: str
    semantic_boundaries: str
    conformance_evidence: str
    compatibility_rules: str
    known_exclusions: str
    safe_failure_or_fallback: str
    authority_map_update: str
    validation: str
    status: str
    notes: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    failures: list[str]


RecordT = TypeVar("RecordT", TransferRecord, EstablishmentRecord)


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


def _parse_records(
    text: str,
    *,
    heading: str,
    columns: tuple[str, ...],
    record_type: type[RecordT],
    label: str,
) -> tuple[list[RecordT], list[str]]:
    table = _table_lines_after_heading(text, heading)
    if len(table) < 2:
        return [], [f"authority protocol must contain an active {label} records table"]

    header = _split_table_row(table[0])
    if header != list(columns):
        return [], [
            f"{label} records table has invalid columns; expected "
            + ", ".join(columns)
        ]

    rows = [_split_table_row(line) for line in table[1:]]
    if rows and _is_separator_row(rows[0]):
        rows = rows[1:]

    records: list[RecordT] = []
    issues: list[str] = []
    for index, cells in enumerate(rows, start=1):
        if len(cells) != len(columns):
            issues.append(f"{label} row {index} has {len(cells)} cells")
            continue
        raw = dict(zip(columns, cells, strict=True))
        records.append(record_type(**raw))
    return records, issues


def parse_transfer_records(text: str) -> tuple[list[TransferRecord], list[str]]:
    return _parse_records(
        text,
        heading="### Active transfer records",
        columns=TRANSFER_COLUMNS,
        record_type=TransferRecord,
        label="transfer",
    )


def parse_establishment_records(
    text: str,
) -> tuple[list[EstablishmentRecord], list[str]]:
    return _parse_records(
        text,
        heading="### Active establishment records",
        columns=ESTABLISHMENT_COLUMNS,
        record_type=EstablishmentRecord,
        label="establishment",
    )


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return not normalized or normalized in PLACEHOLDERS


def _validate_required_fields(
    record: TransferRecord | EstablishmentRecord,
    columns: tuple[str, ...],
    *,
    optional: frozenset[str] = frozenset({"notes"}),
) -> list[str]:
    failures: list[str] = []
    for field in columns:
        if field in optional:
            continue
        if _is_placeholder(getattr(record, field)):
            failures.append(
                f"{record.id or '<missing>'} has empty or placeholder `{field}`"
            )
    return failures


def _validate_identity(
    record_id: str,
    *,
    pattern: re.Pattern[str],
    kind: str,
    seen: set[str],
) -> list[str]:
    failures: list[str] = []
    if not pattern.match(record_id):
        failures.append(f"{record_id or '<missing>'} has invalid {kind} id")
    if record_id in seen:
        failures.append(f"{record_id} is duplicated")
    seen.add(record_id)
    return failures


def _validate_transfer_records(records: list[TransferRecord]) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    for record in records:
        failures.extend(_validate_required_fields(record, TRANSFER_COLUMNS))
        failures.extend(
            _validate_identity(
                record.id,
                pattern=TRANSFER_ID_RE,
                kind="transfer",
                seen=seen,
            )
        )
        if record.operation != "transfer":
            failures.append(f"{record.id} operation must be `transfer`")
        if record.status not in TRANSFER_STATUSES:
            failures.append(f"{record.id} has invalid transfer status `{record.status}`")
        if record.current_authority == record.candidate_authority:
            failures.append(f"{record.id} current and candidate authority are identical")
        if record.status == "transferred":
            for field in (
                "reference_implementation",
                "golden_fixtures",
                "comparison_command",
                "fallback_path",
                "authority_map_update",
                "validation",
            ):
                if _is_placeholder(getattr(record, field)):
                    failures.append(
                        f"{record.id} transferred row has placeholder `{field}`"
                    )
    return failures


def _validate_establishment_records(
    records: list[EstablishmentRecord],
) -> list[str]:
    failures: list[str] = []
    seen: set[str] = set()
    optional = frozenset({"notes"})
    for record in records:
        failures.extend(
            _validate_required_fields(
                record,
                ESTABLISHMENT_COLUMNS,
                optional=optional,
            )
        )
        failures.extend(
            _validate_identity(
                record.id,
                pattern=ESTABLISHMENT_ID_RE,
                kind="establishment",
                seen=seen,
            )
        )
        if record.operation != "establishment":
            failures.append(f"{record.id} operation must be `establishment`")
        if record.status not in ESTABLISHMENT_STATUSES:
            failures.append(
                f"{record.id} has invalid establishment status `{record.status}`"
            )
        if record.status == "established":
            for field in (
                "normative_contract",
                "implementation_authority",
                "semantic_boundaries",
                "conformance_evidence",
                "compatibility_rules",
                "safe_failure_or_fallback",
                "authority_map_update",
                "validation",
            ):
                if _is_placeholder(getattr(record, field)):
                    failures.append(
                        f"{record.id} established row has placeholder `{field}`"
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
        "docs/plans/professional_godot_game_programme.md": (
            "docs/architecture/authority_map.md",
            PROTOCOL_REL,
        ),
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
        "subsystem-specific authority": ("subsystem", "authority"),
        "inherited transfer": ("authority transfer", "inherited behaviour"),
        "new authority establishment": ("authority establishment", "new behaviour"),
        "Godot presentation": ("presentation", "godot"),
        "native deterministic authority": ("native", "deterministic"),
        "parity not sufficient": ("not sufficient", "parity"),
        "only transferred changes authority": (
            "only `transferred` changes authority",
        ),
        "only established creates authority": (
            "only `established` creates authority",
        ),
        "active transfer records": ("### active transfer records",),
        "active establishment records": (
            "### active establishment records",
        ),
        "transfer required fields": ("required transfer record fields",),
        "establishment required fields": (
            "required establishment record fields",
        ),
        "fallback": ("fallback",),
        "authority map update": ("authority_map_update", "authority map"),
        "comparison command": ("comparison_command", "comparison command"),
        "known exclusions": ("known_exclusions", "known exclusions"),
        "normative contract": ("normative_contract", "normative contract"),
        "conformance evidence": (
            "conformance_evidence",
            "conformance evidence",
        ),
    }
    for concept in contains_concepts(text, concepts):
        failures.append(f"{PROTOCOL_REL} is missing concept `{concept}`")
    return CheckResult("protocol contents", failures)


def check_record_tables(
    root: Path = ROOT,
) -> tuple[CheckResult, list[TransferRecord], list[EstablishmentRecord]]:
    failures: list[str] = []
    text = _read_rel(root, PROTOCOL_REL, failures)
    transfers, transfer_parse_failures = parse_transfer_records(text)
    establishments, establishment_parse_failures = parse_establishment_records(text)
    failures.extend(transfer_parse_failures)
    failures.extend(establishment_parse_failures)
    failures.extend(_validate_transfer_records(transfers))
    failures.extend(_validate_establishment_records(establishments))
    return CheckResult("authority record tables", failures), transfers, establishments


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
    transfers: list[TransferRecord],
    establishments: list[EstablishmentRecord],
    root: Path = ROOT,
) -> CheckResult:
    failures: list[str] = []
    authority_map = _read_rel(root, "docs/architecture/authority_map.md", failures)
    lower = authority_map.lower()

    if not (
        "python" in lower
        and "reference authority" in lower
        and "inherited" in lower
    ):
        failures.append(
            "authority_map.md must describe Python as reference authority for "
            "inherited behaviour"
        )

    for record in transfers:
        if record.status != "transferred":
            continue
        mentions_id = record.id.lower() in lower
        mentions_transfer = (
            record.subsystem.lower() in lower
            and record.candidate_authority.lower() in lower
        )
        if not (mentions_id or mentions_transfer):
            failures.append(
                f"authority_map.md does not mention transferred record {record.id}"
            )

    for record in establishments:
        if record.status != "established":
            continue
        mentions_id = record.id.lower() in lower
        mentions_establishment = (
            record.subsystem.lower() in lower
            and record.implementation_authority.lower() in lower
        )
        if not (mentions_id or mentions_establishment):
            failures.append(
                f"authority_map.md does not mention established record {record.id}"
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
            "docs/architecture/parity_protocol.md must say parity does not itself "
            "transfer authority"
        )
    return CheckResult("parity-protocol consistency", failures)


def check_policy_consistency(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    godot = _read_rel(root, "docs/governance/godot_cpp_policy.md", failures)
    godot_lower = godot.lower()
    if not (
        "gdscript" in godot_lower
        and "inherited" in godot_lower
        and ("must not" in godot_lower or "does not" in godot_lower)
    ):
        failures.append(
            "docs/governance/godot_cpp_policy.md must prevent GDScript from "
            "duplicating inherited semantic truth"
        )
    if "authority_transfer_protocol.md" not in godot:
        failures.append(
            "docs/governance/godot_cpp_policy.md must refer to authority protocol"
        )
    if "establish" not in godot_lower:
        failures.append(
            "docs/governance/godot_cpp_policy.md must route new authority "
            "establishment"
        )

    cpp = _read_rel(root, "docs/governance/cpp_safety_policy.md", failures)
    cpp_lower = cpp.lower()
    if not ("provisional" in cpp_lower or "parity" in cpp_lower):
        failures.append(
            "docs/governance/cpp_safety_policy.md must keep inherited C++ "
            "authority provisional or parity-gated"
        )
    if "authority_transfer_protocol.md" not in cpp:
        failures.append(
            "docs/governance/cpp_safety_policy.md must refer to authority protocol"
        )
    if "establish" not in cpp_lower:
        failures.append(
            "docs/governance/cpp_safety_policy.md must define new authority "
            "establishment"
        )
    return CheckResult("Godot/C++ policy consistency", failures)


def check_review_checklist(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    text = _read_rel(root, "docs/governance/review_checklist.md", failures)
    concepts = {
        "authority transfer": ("authority transfer",),
        "authority establishment": ("authority establishment",),
        "parity evidence": ("parity evidence", "golden traces"),
        "authority map": ("authority map",),
        "fallback path": ("fallback path", "safe-failure"),
        "known exclusions": ("known exclusions",),
        "normative contract": ("normative contract",),
        "conformance evidence": ("conformance",),
    }
    for concept in contains_concepts(text, concepts):
        failures.append(
            f"docs/governance/review_checklist.md is missing concept `{concept}`"
        )
    return CheckResult("review checklist", failures)


def validate(
    root: Path = ROOT,
) -> tuple[list[CheckResult], list[TransferRecord], list[EstablishmentRecord]]:
    table_result, transfers, establishments = check_record_tables(root)
    results = [
        check_required_files(root),
        check_router_links(root),
        check_protocol_contents(root),
        table_result,
        check_dangerous_authority_claims(root),
        check_authority_map_consistency(transfers, establishments, root),
        check_parity_protocol_consistency(root),
        check_policy_consistency(root),
        check_review_checklist(root),
    ]
    return results, transfers, establishments


def main() -> int:
    results, transfers, establishments = validate(ROOT)
    failures = [failure for result in results for failure in result.failures]
    if failures:
        print("Authority validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    transferred = [record for record in transfers if record.status == "transferred"]
    established = [
        record for record in establishments if record.status == "established"
    ]
    print("Authority transfer and establishment validation passed.")
    print(f"Transfer records: {len(transfers)}")
    print(f"Transferred subsystems: {len(transferred)}")
    print(f"Establishment records: {len(establishments)}")
    print(f"Established subsystems: {len(established)}")
    print("Checks:")
    for result in results:
        print(f"- {result.name}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
