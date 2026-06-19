from __future__ import annotations

from pathlib import Path

import tools.governance.validate_authority_transfer as validator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _table(rows: list[str] | None = None) -> str:
    return "\n".join(
        [
            "| " + " | ".join(validator.REQUIRED_COLUMNS) + " |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
            *(rows or []),
            "",
        ]
    )


def _protocol(rows: list[str] | None = None) -> str:
    return "\n".join(
        [
            "# tet4d Authority Transfer Protocol",
            "",
            "Python remains the semantic oracle.",
            "Godot remains product shell presentation UI.",
            "C++/GDExtension remains provisional.",
            "Parity evidence is necessary but not sufficient.",
            "Only `transferred` changes authority.",
            "## Relationship to other documents",
            "docs/architecture/authority_map.md",
            "docs/architecture/parity_protocol.md",
            "tools/governance/validate_authority_transfer.py",
            "## Required transfer record fields",
            "fallback_path authority_map_update comparison_command known_exclusions",
            "allowed statuses",
            "## Transfer records",
            "",
            _table(rows),
        ]
    )


def _row(
    *,
    transfer_id: str = "AT-0001",
    subsystem: str = "trace parser",
    current_authority: str = "Python",
    candidate_authority: str = "C++",
    golden_fixtures: str = "migration/golden_traces/trace.json",
    comparison_command: str = "tools/migration/compare_trace.py",
    authority_map_update: str = "docs/architecture/authority_map.md",
    validation: str = "tools/governance/validate_authority_transfer.py",
    status: str = "candidate",
) -> str:
    return (
        f"| {transfer_id} | {subsystem} | {current_authority} | "
        f"{candidate_authority} | exact parser behavior | src/tet4d/trace.py | "
        f"{golden_fixtures} | {comparison_command} | no topology behavior | "
        f"route back to Python | {authority_map_update} | {validation} | "
        f"{status} | notes |"
    )


def _valid_fixture(root: Path, rows: list[str] | None = None) -> None:
    _write(root / "AGENTS.md", "Python semantic oracle.\n")
    _write(root / "godot" / "AGENTS.md", "Godot product shell.\n")
    _write(root / "native" / "AGENTS.md", "Native provisional.\n")
    _write(root / validator.PROTOCOL_REL, _protocol(rows))
    _write(
        root / "docs" / "architecture" / "authority_map.md",
        "Python remains the current semantic oracle. "
        "docs/architecture/authority_transfer_protocol.md\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_protocol.md",
        "Parity evidence is necessary but not sufficient for authority transfer. "
        "A transfer record in docs/architecture/authority_transfer_protocol.md is required.\n",
    )
    _write(
        root / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript must not own semantic truth. "
        "See docs/architecture/authority_transfer_protocol.md.\n",
    )
    _write(
        root / "docs" / "governance" / "cpp_safety_policy.md",
        "C++ authority is provisional and parity-gated. "
        "See docs/architecture/authority_transfer_protocol.md.\n",
    )
    _write(root / "docs" / "governance" / "testing_policy.md", "Testing.\n")
    _write(
        root / "docs" / "governance" / "drift_protection_map.md",
        "authority_transfer_protocol.md validate_authority_transfer.py\n",
    )
    _write(
        root / "docs" / "governance" / "README.md",
        "docs/architecture/authority_transfer_protocol.md\n"
        "tools/governance/validate_authority_transfer.py\n",
    )
    _write(
        root / "docs" / "governance" / "review_checklist.md",
        "authority transfer parity evidence authority map fallback path known exclusions\n",
    )
    for rel in (
        "tools/governance/validate_authority_transfer.py",
        "tools/governance/validate_governance.py",
        "tools/governance/validate_project_contracts.py",
        "tools/governance/validate_drift_protection.py",
    ):
        _write(root / rel, "def main():\n    return 0\n")


def _failures(root: Path) -> list[str]:
    results, _records = validator.validate(root)
    return [failure for result in results for failure in result.failures]


def test_missing_authority_transfer_protocol_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    (tmp_path / validator.PROTOCOL_REL).unlink()

    assert any(validator.PROTOCOL_REL in failure for failure in _failures(tmp_path))


def test_missing_transfer_table_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(tmp_path / validator.PROTOCOL_REL, "# Protocol\n")

    assert any("transfer records table" in failure for failure in _failures(tmp_path))


def test_missing_required_columns_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / validator.PROTOCOL_REL,
        "## Transfer records\n\n| id | status |\n|---|---|\n",
    )

    assert any("invalid columns" in failure for failure in _failures(tmp_path))


def test_empty_transfer_table_passes_with_required_concepts(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)

    assert _failures(tmp_path) == []


def test_invalid_transfer_id_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_row(transfer_id="BAD")])

    assert any("invalid transfer id" in failure for failure in _failures(tmp_path))


def test_duplicate_transfer_id_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_row(), _row()])

    assert any("duplicated" in failure for failure in _failures(tmp_path))


def test_invalid_status_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_row(status="done")])

    assert any("invalid status" in failure for failure in _failures(tmp_path))


def test_transferred_row_with_placeholder_golden_fixtures_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path, [_row(status="transferred", golden_fixtures="TBD")])

    assert any("golden_fixtures" in failure for failure in _failures(tmp_path))


def test_transferred_row_with_placeholder_comparison_command_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path, [_row(status="transferred", comparison_command="none")])

    assert any("comparison_command" in failure for failure in _failures(tmp_path))


def test_transferred_row_without_authority_map_update_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_row(status="transferred", authority_map_update="n/a")])

    assert any("authority_map_update" in failure for failure in _failures(tmp_path))


def test_dangerous_authority_claim_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "extra.md",
        "Godot owns movement rules.\n",
    )

    assert any(
        "Dangerous authority claim" in failure for failure in _failures(tmp_path)
    )


def test_conditional_provisional_authority_wording_does_not_fail(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "extra.md",
        "C++ owns gameplay semantics after authority transfer.\n",
    )

    assert not any(
        "Dangerous authority claim" in failure for failure in _failures(tmp_path)
    )


def test_authority_map_missing_protocol_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python remains the semantic oracle.\n",
    )

    assert any(
        "authority_map.md does not link" in failure for failure in _failures(tmp_path)
    )


def test_parity_protocol_missing_protocol_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "parity_protocol.md",
        "Parity evidence is necessary but not sufficient.\n",
    )

    assert any(
        "parity_protocol.md does not link" in failure for failure in _failures(tmp_path)
    )


def test_godot_policy_missing_transfer_protocol_reference_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript must not own semantic truth.\n",
    )

    assert any(
        "godot_cpp_policy.md must refer" in failure for failure in _failures(tmp_path)
    )


def test_cpp_policy_missing_transfer_protocol_reference_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "cpp_safety_policy.md",
        "C++ authority is provisional and parity-gated.\n",
    )

    assert any(
        "cpp_safety_policy.md must refer" in failure for failure in _failures(tmp_path)
    )


def test_review_checklist_missing_fallback_known_exclusions_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "review_checklist.md",
        "authority transfer parity evidence authority map\n",
    )

    failures = _failures(tmp_path)

    assert any("fallback path" in failure for failure in failures)
    assert any("known exclusions" in failure for failure in failures)


def test_valid_transferred_row_requires_authority_map_reference(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path, [_row(status="transferred")])

    assert any("AT-0001" in failure for failure in _failures(tmp_path))

    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python remains the semantic oracle for other systems. "
        "AT-0001 transferred trace parser to C++. "
        "docs/architecture/authority_transfer_protocol.md\n",
    )

    assert _failures(tmp_path) == []
