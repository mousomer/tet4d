from __future__ import annotations

from pathlib import Path

import tools.governance.validate_technical_debt as debt


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _row(
    *,
    debt_id: str = "TD-0001",
    category: str = "tooling-gap",
    classification: str = "deliberate-prudent",
    severity: str = "low",
    minutes: str = "30",
    status: str = "accepted",
    source: str = "Deferred cleanup",
) -> str:
    return (
        f"| {debt_id} | {category} | tools | {source} | {classification} | "
        f"{severity} | {minutes} | Cost of delay | governance | unknown | "
        f"Before strict mode | {status} | notes |"
    )


def _register(rows: list[str] | None = None, *, include_links: bool = True) -> str:
    links = ""
    if include_links:
        links = f"{debt.WORKSPACE_DEBT_POLICY_REL}\n{debt.WORKSPACE_DRIFT_POLICY_REL}\n"
    return "\n".join(
        [
            "# tet4d Technical Debt Register",
            "",
            links,
            "## Debt records",
            "",
            "| " + " | ".join(debt.REQUIRED_COLUMNS) + " |",
            "|---|---|---|---|---|---|---:|---|---|---|---|---|---|",
            *(rows or [_row()]),
            "",
        ]
    )


def _write_valid_files(root: Path, rows: list[str] | None = None) -> None:
    _write(root / debt.WORKSPACE_DEBT_POLICY_REL, "# Technical Debt Policy\n")
    _write(root / debt.WORKSPACE_DRIFT_POLICY_REL, "# Drift Protection Policy\n")
    _write(root / debt.REGISTER_REL, _register(rows))


def test_missing_debt_register_fails(tmp_path: Path, monkeypatch) -> None:
    _write(tmp_path / debt.WORKSPACE_DEBT_POLICY_REL, "# Technical Debt Policy\n")
    _write(tmp_path / debt.WORKSPACE_DRIFT_POLICY_REL, "# Drift Protection Policy\n")
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert any(debt.REGISTER_REL in issue for issue in result.issues)


def test_missing_workspace_debt_policy_fails(tmp_path: Path, monkeypatch) -> None:
    _write_valid_files(tmp_path)
    (tmp_path / debt.WORKSPACE_DEBT_POLICY_REL).unlink()
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert any(debt.WORKSPACE_DEBT_POLICY_REL in issue for issue in result.issues)


def test_missing_workspace_drift_policy_fails(tmp_path: Path, monkeypatch) -> None:
    _write_valid_files(tmp_path)
    (tmp_path / debt.WORKSPACE_DRIFT_POLICY_REL).unlink()
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert any(debt.WORKSPACE_DRIFT_POLICY_REL in issue for issue in result.issues)


def test_register_missing_workspace_debt_policy_link_fails(
    tmp_path: Path, monkeypatch
) -> None:
    _write_valid_files(tmp_path)
    text = _register().replace(debt.WORKSPACE_DEBT_POLICY_REL, "")
    _write(tmp_path / debt.REGISTER_REL, text)
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert any("workspace debt policy" in issue for issue in result.issues)


def test_register_missing_workspace_drift_policy_link_fails(
    tmp_path: Path, monkeypatch
) -> None:
    _write_valid_files(tmp_path)
    text = _register().replace(debt.WORKSPACE_DRIFT_POLICY_REL, "")
    _write(tmp_path / debt.REGISTER_REL, text)
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert any("workspace drift policy" in issue for issue in result.issues)


def test_missing_required_columns_fails() -> None:
    _records, issues = debt.parse_register(
        "## Debt records\n\n| id | category |\n|---|---|\n| TD-0001 | tooling-gap |\n"
    )

    assert any("invalid columns" in issue for issue in issues)


def test_invalid_id_fails() -> None:
    issues = debt.validate_records([_record(debt_id="BAD-1")])

    assert any("invalid id" in issue for issue in issues)


def test_duplicate_id_fails() -> None:
    issues = debt.validate_records([_record(), _record()])

    assert any("duplicated" in issue for issue in issues)


def test_invalid_category_fails() -> None:
    issues = debt.validate_records([_record(category="unknown")])

    assert any("invalid category" in issue for issue in issues)


def test_invalid_classification_fails() -> None:
    issues = debt.validate_records([_record(classification="accidental")])

    assert any("invalid classification" in issue for issue in issues)


def test_invalid_severity_fails() -> None:
    issues = debt.validate_records([_record(severity="minor")])

    assert any("invalid severity" in issue for issue in issues)


def test_invalid_status_fails() -> None:
    issues = debt.validate_records([_record(status="paused")])

    assert any("invalid status" in issue for issue in issues)


def test_empty_required_field_fails() -> None:
    issues = debt.validate_records([_record(source="")])

    assert any("empty required field `source`" in issue for issue in issues)


def test_non_integer_remediation_minutes_fails() -> None:
    records, _issues = debt.parse_register(_register([_row(minutes="many")]))

    issues = debt.validate_records(records)

    assert any("remediation_minutes" in issue for issue in issues)


def test_valid_register_passes(tmp_path: Path, monkeypatch) -> None:
    _write_valid_files(tmp_path)
    monkeypatch.setattr(debt, "collect_advisory_requirements", lambda root: (set(), []))

    result = debt.validate(tmp_path)

    assert result.issues == []


def test_summary_calculation_counts_open_and_accepted_only() -> None:
    records = [
        _record(debt_id="TD-0001", minutes=30, status="open"),
        _record(debt_id="TD-0002", minutes=60, status="accepted"),
        _record(debt_id="TD-0003", minutes=120, status="mitigated"),
        _record(debt_id="TD-0004", minutes=240, status="closed"),
    ]

    assert debt._open_minutes(records) == 90


def test_advisory_integration_requires_config_category(
    tmp_path: Path, monkeypatch
) -> None:
    _write_valid_files(tmp_path)
    monkeypatch.setattr(
        debt,
        "collect_advisory_requirements",
        lambda root: ({"config-authority-advisory"}, []),
    )

    result = debt.validate(tmp_path)

    assert any("config authority advisory" in issue for issue in result.issues)


def test_advisory_integration_requires_utility_category(
    tmp_path: Path, monkeypatch
) -> None:
    _write_valid_files(tmp_path)
    monkeypatch.setattr(
        debt,
        "collect_advisory_requirements",
        lambda root: ({"utility-reuse-advisory"}, []),
    )

    result = debt.validate(tmp_path)

    assert any("utility reuse advisory" in issue for issue in result.issues)


def _record(
    *,
    debt_id: str = "TD-0001",
    category: str = "tooling-gap",
    classification: str = "deliberate-prudent",
    severity: str = "low",
    minutes: int = 30,
    status: str = "accepted",
    source: str = "Deferred cleanup",
) -> debt.DebtRecord:
    return debt.DebtRecord(
        id=debt_id,
        category=category,
        location="tools",
        source=source,
        classification=classification,
        severity=severity,
        remediation_minutes=minutes,
        interest="Cost of delay",
        owner="governance",
        introduced_by="unknown",
        repayment_trigger="Before strict mode",
        status=status,
        notes="notes",
    )
