from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections import Counter
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
REGISTER_REL = "docs/governance/technical_debt_register.md"
WORKSPACE_DEBT_POLICY_REL = "docs/governance/workspace_bundle/technical_debt_policy.md"
WORKSPACE_DRIFT_POLICY_REL = (
    "docs/governance/workspace_bundle/drift_protection_policy.md"
)
REQUIRED_COLUMNS = [
    "id",
    "category",
    "location",
    "source",
    "classification",
    "severity",
    "remediation_minutes",
    "interest",
    "owner",
    "introduced_by",
    "repayment_trigger",
    "status",
    "notes",
]
ALLOWED_CATEGORIES = {
    "duplication",
    "config-drift",
    "semantic-drift",
    "test-gap",
    "generated-drift",
    "dependency-risk",
    "unsafe-native",
    "godot-boundary-risk",
    "parity-gap",
    "documentation-drift",
    "tooling-gap",
    "suppression",
    "authority-transfer-gap",
    "config-authority-advisory",
    "utility-reuse-advisory",
    "formatting-drift",
    "native-tooling-gap",
}
ALLOWED_CLASSIFICATIONS = {
    "deliberate-prudent",
    "deliberate-reckless",
    "inadvertent-prudent",
    "inadvertent-reckless",
}
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_STATUSES = {"open", "accepted", "mitigated", "closed"}
OPEN_STATUSES = {"open", "accepted"}
ID_RE = re.compile(r"^TD-\d{4}$")


@dataclass(frozen=True)
class DebtRecord:
    id: str
    category: str
    location: str
    source: str
    classification: str
    severity: str
    remediation_minutes: int
    interest: str
    owner: str
    introduced_by: str
    repayment_trigger: str
    status: str
    notes: str


@dataclass(frozen=True)
class ValidationResult:
    records: list[DebtRecord]
    issues: list[str]
    advisory_warnings: list[str]


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(set(cell.replace(":", "").strip()) <= {"-"} for cell in cells)


def _debt_table_lines(text: str) -> list[str]:
    lines = text.splitlines()
    in_section = False
    table: list[str] = []
    for line in lines:
        if line.strip() == "## Debt records":
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


def parse_register(text: str) -> tuple[list[DebtRecord], list[str]]:
    table = _debt_table_lines(text)
    if len(table) < 2:
        return [], ["technical debt register must contain a debt records table"]

    header = _split_table_row(table[0])
    if header != REQUIRED_COLUMNS:
        return [], [
            "debt records table has invalid columns; expected "
            + ", ".join(REQUIRED_COLUMNS)
        ]

    rows = [_split_table_row(line) for line in table[1:]]
    if rows and _is_separator_row(rows[0]):
        rows = rows[1:]

    issues: list[str] = []
    records: list[DebtRecord] = []
    for index, cells in enumerate(rows, start=1):
        if len(cells) != len(REQUIRED_COLUMNS):
            issues.append(f"debt row {index} has {len(cells)} cells")
            continue
        raw = dict(zip(REQUIRED_COLUMNS, cells, strict=True))
        try:
            minutes = int(raw["remediation_minutes"])
        except ValueError:
            minutes = -1
        records.append(
            DebtRecord(
                id=raw["id"],
                category=raw["category"],
                location=raw["location"],
                source=raw["source"],
                classification=raw["classification"],
                severity=raw["severity"],
                remediation_minutes=minutes,
                interest=raw["interest"],
                owner=raw["owner"],
                introduced_by=raw["introduced_by"],
                repayment_trigger=raw["repayment_trigger"],
                status=raw["status"],
                notes=raw["notes"],
            )
        )
    return records, issues


def validate_records(records: list[DebtRecord]) -> list[str]:
    issues: list[str] = []
    seen_ids: set[str] = set()
    for record in records:
        for field in REQUIRED_COLUMNS:
            if field == "notes":
                continue
            if not str(getattr(record, field)).strip():
                issues.append(
                    f"{record.id or '<missing>'} has empty required field `{field}`"
                )
        if not ID_RE.match(record.id):
            issues.append(f"{record.id or '<missing>'} has invalid id")
        if record.id in seen_ids:
            issues.append(f"{record.id} is duplicated")
        seen_ids.add(record.id)
        if record.category not in ALLOWED_CATEGORIES:
            issues.append(f"{record.id} has invalid category `{record.category}`")
        if record.classification not in ALLOWED_CLASSIFICATIONS:
            issues.append(
                f"{record.id} has invalid classification `{record.classification}`"
            )
        if record.severity not in ALLOWED_SEVERITIES:
            issues.append(f"{record.id} has invalid severity `{record.severity}`")
        if record.status not in ALLOWED_STATUSES:
            issues.append(f"{record.id} has invalid status `{record.status}`")
        if record.status in OPEN_STATUSES and record.remediation_minutes <= 0:
            issues.append(f"{record.id} remediation_minutes must be a positive integer")
        elif (
            record.status in {"mitigated", "closed"} and record.remediation_minutes < 0
        ):
            issues.append(
                f"{record.id} remediation_minutes must be zero or a positive integer"
            )
    return issues


def _run_advisory_validator(root: Path, rel: str) -> tuple[bool, str]:
    path = root / rel
    if not path.exists():
        return False, f"{rel} missing; advisory integration skipped"
    result = subprocess.run(
        [sys.executable, rel],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return True, f"{result.stdout}\n{result.stderr}"


def collect_advisory_requirements(root: Path = ROOT) -> tuple[set[str], list[str]]:
    required: set[str] = set()
    warnings: list[str] = []
    config_present, config_output = _run_advisory_validator(
        root, "tools/governance/validate_config_authority.py"
    )
    if not config_present:
        warnings.append(config_output)
    elif "Config authority advisory warnings:" in config_output or re.search(
        r"Suspicious constants: 0 blocking, [1-9]\d* advisory", config_output
    ):
        required.add("config-authority-advisory")

    utility_present, utility_output = _run_advisory_validator(
        root, "tools/governance/validate_utility_reuse.py"
    )
    if not utility_present:
        warnings.append(utility_output)
    elif "Utility reuse advisory warnings:" in utility_output or re.search(
        r"Duplicate-helper findings: 0 blocking, [1-9]\d* advisory", utility_output
    ):
        required.add("utility-reuse-advisory")
    return required, warnings


def _validate_required_docs(root: Path) -> list[str]:
    issues: list[str] = []
    for rel in (WORKSPACE_DEBT_POLICY_REL, WORKSPACE_DRIFT_POLICY_REL, REGISTER_REL):
        if not (root / rel).exists():
            issues.append(f"missing required path: {rel}")
    return issues


def _validate_register_links(text: str) -> list[str]:
    issues: list[str] = []
    if WORKSPACE_DEBT_POLICY_REL not in text:
        issues.append("technical debt register must link to workspace debt policy")
    if WORKSPACE_DRIFT_POLICY_REL not in text:
        issues.append("technical debt register must link to workspace drift policy")
    return issues


def validate(root: Path = ROOT) -> ValidationResult:
    issues = _validate_required_docs(root)
    register_path = root / REGISTER_REL
    if not register_path.exists():
        return ValidationResult([], issues, [])

    text = register_path.read_text(encoding="utf-8")
    issues.extend(_validate_register_links(text))
    records, parse_issues = parse_register(text)
    issues.extend(parse_issues)
    issues.extend(validate_records(records))

    advisory_requirements, advisory_warnings = collect_advisory_requirements(root)
    categories = {record.category for record in records}
    for category in sorted(advisory_requirements - categories):
        issues.append(
            f"{category.replace('-', ' ')} findings exist but no {category} debt record exists"
        )
    if not records and not advisory_requirements:
        advisory_warnings.append("no debt records found")
    return ValidationResult(records, issues, advisory_warnings)


def _open_minutes(records: list[DebtRecord]) -> int:
    return sum(
        record.remediation_minutes
        for record in records
        if record.status in OPEN_STATUSES
    )


def _print_counter(title: str, counter: Counter[str]) -> None:
    print(f"{title}:")
    for key in sorted(counter):
        print(f"- {key}: {counter[key]}")


def print_summary(records: list[DebtRecord]) -> None:
    minutes = _open_minutes(records)
    print(f"Debt records: {len(records)}")
    print(f"Open/accepted debt: {minutes} minutes = {minutes / 480:.2f} days")
    _print_counter("By status", Counter(record.status for record in records))
    _print_counter("By severity", Counter(record.severity for record in records))
    _print_counter("By category", Counter(record.category for record in records))


def main() -> int:
    result = validate(ROOT)
    if result.issues:
        print("Technical debt validation failed:")
        for issue in result.issues:
            print(f"- {issue}")
        return 1
    for warning in result.advisory_warnings:
        print(f"Technical debt validation warning: {warning}")
    print("Technical debt validation passed.")
    print_summary(result.records)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
