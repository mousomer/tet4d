from __future__ import annotations

from pathlib import Path

import tools.governance.validate_authority_transfer as validator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _table(columns: tuple[str, ...], rows: list[str] | None = None) -> str:
    separator = "|" + "---|" * len(columns)
    return "\n".join(
        [
            "| " + " | ".join(columns) + " |",
            separator,
            *(rows or []),
            "",
        ]
    )


def _protocol(
    transfer_rows: list[str] | None = None,
    establishment_rows: list[str] | None = None,
    *,
    include_transfer_table: bool = True,
    include_establishment_table: bool = True,
) -> str:
    lines = [
        "# tet4d Authority Transfer and Establishment Protocol",
        "",
        "Authority is assigned per subsystem.",
        "Authority transfer applies to inherited behaviour.",
        "Authority establishment applies to new behaviour.",
        "Godot owns product shell presentation.",
        "Native C++ may own deterministic behaviour through the protocol.",
        "Parity evidence is necessary but not sufficient for transfer.",
        "Only `transferred` changes authority.",
        "Only `established` creates authority.",
        "## Relationship to other documents",
        "docs/architecture/authority_map.md",
        "docs/architecture/parity_protocol.md",
        "tools/governance/validate_authority_transfer.py",
        "## 1. Authority transfer",
        "## Required transfer record fields",
        "fallback_path authority_map_update comparison_command known_exclusions",
        "## 2. Authority establishment",
        "## Required establishment record fields",
        "normative_contract conformance_evidence authority_map_update",
        "## 5. Transfer and establishment records",
    ]
    if include_transfer_table:
        lines.extend(
            [
                "### Active transfer records",
                "",
                _table(validator.TRANSFER_COLUMNS, transfer_rows),
            ]
        )
    if include_establishment_table:
        lines.extend(
            [
                "### Active establishment records",
                "",
                _table(
                    validator.ESTABLISHMENT_COLUMNS,
                    establishment_rows,
                ),
            ]
        )
    return "\n".join(lines)


def _transfer_row(
    *,
    transfer_id: str = "AT-0001",
    subsystem: str = "trace parser",
    current_authority: str = "Python reference",
    candidate_authority: str = "C++",
    reference_implementation: str = "src/tet4d/trace.py",
    golden_fixtures: str = "migration/golden_traces/trace.json",
    comparison_command: str = "tools/migration/compare_trace.py",
    authority_map_update: str = "docs/architecture/authority_map.md",
    validation: str = "tools/governance/validate_authority_transfer.py",
    status: str = "candidate",
    operation: str = "transfer",
) -> str:
    return (
        f"| {transfer_id} | {operation} | {subsystem} | {current_authority} | "
        f"{candidate_authority} | exact parser behaviour | "
        f"{reference_implementation} | {golden_fixtures} | "
        f"{comparison_command} | no topology behaviour | route back to Python | "
        f"{authority_map_update} | {validation} | {status} | notes |"
    )


def _establishment_row(
    *,
    establishment_id: str = "AE-0001",
    subsystem: str = "hold gameplay",
    normative_contract: str = "docs/rds/RDS_TETRIS_GENERAL.md",
    implementation_authority: str = "Native C++",
    data_authority: str = "not applicable",
    conformance_evidence: str = "native/tet4d_core/tests/hold_tests.cpp",
    authority_map_update: str = "docs/architecture/authority_map.md",
    validation: str = "tools/governance/validate_authority_transfer.py",
    status: str = "proposed",
    operation: str = "establishment",
) -> str:
    return (
        f"| {establishment_id} | {operation} | {subsystem} | "
        f"{normative_contract} | {implementation_authority} | {data_authority} | "
        "single hold slot transitions | native deterministic; Godot presentation | "
        f"{conformance_evidence} | snapshot version 1 | no campaign rules | "
        "reject invalid state | "
        f"{authority_map_update} | {validation} | {status} | notes |"
    )


def _valid_fixture(
    root: Path,
    transfer_rows: list[str] | None = None,
    establishment_rows: list[str] | None = None,
) -> None:
    _write(
        root / "AGENTS.md",
        "Python is reference authority for inherited behaviour.\n",
    )
    _write(root / "godot" / "AGENTS.md", "Godot product shell.\n")
    _write(root / "native" / "AGENTS.md", "Native provisional.\n")
    _write(
        root / validator.PROTOCOL_REL,
        _protocol(transfer_rows, establishment_rows),
    )
    _write(
        root / "docs" / "architecture" / "authority_map.md",
        "Python remains reference authority for inherited behaviour. "
        "docs/architecture/authority_transfer_protocol.md\n",
    )
    _write(
        root / "docs" / "architecture" / "parity_protocol.md",
        "Parity evidence is necessary but not sufficient for authority transfer. "
        "A transfer record in docs/architecture/authority_transfer_protocol.md "
        "is required.\n",
    )
    _write(
        root / "docs" / "plans" / "professional_godot_game_programme.md",
        "docs/architecture/authority_map.md "
        "docs/architecture/authority_transfer_protocol.md\n",
    )
    _write(
        root / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript must not duplicate inherited semantic truth. "
        "New authority may be established. "
        "See docs/architecture/authority_transfer_protocol.md.\n",
    )
    _write(
        root / "docs" / "governance" / "cpp_safety_policy.md",
        "Inherited C++ authority is provisional and parity-gated. "
        "New authority may be established. "
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
        "authority transfer authority establishment parity evidence authority map "
        "fallback path known exclusions normative contract conformance evidence\n",
    )
    for rel in (
        "tools/governance/validate_authority_transfer.py",
        "tools/governance/validate_governance.py",
        "tools/governance/validate_project_contracts.py",
        "tools/governance/validate_drift_protection.py",
    ):
        _write(root / rel, "def main():\n    return 0\n")


def _failures(root: Path) -> list[str]:
    results, _transfers, _establishments = validator.validate(root)
    return [failure for result in results for failure in result.failures]


def test_missing_authority_protocol_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    (tmp_path / validator.PROTOCOL_REL).unlink()

    assert any(validator.PROTOCOL_REL in failure for failure in _failures(tmp_path))


def test_missing_transfer_table_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / validator.PROTOCOL_REL,
        _protocol(include_transfer_table=False),
    )

    assert any("active transfer records table" in failure for failure in _failures(tmp_path))


def test_missing_establishment_table_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / validator.PROTOCOL_REL,
        _protocol(include_establishment_table=False),
    )

    assert any(
        "active establishment records table" in failure
        for failure in _failures(tmp_path)
    )


def test_missing_transfer_columns_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    text = _protocol().replace(
        _table(validator.TRANSFER_COLUMNS),
        "| id | status |\n|---|---|\n",
    )
    _write(tmp_path / validator.PROTOCOL_REL, text)

    assert any("transfer records table has invalid columns" in failure for failure in _failures(tmp_path))


def test_empty_record_tables_pass_with_required_concepts(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)

    assert _failures(tmp_path) == []


def test_invalid_transfer_id_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_transfer_row(transfer_id="BAD")])

    assert any("invalid transfer id" in failure for failure in _failures(tmp_path))


def test_invalid_establishment_id_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, establishment_rows=[_establishment_row(establishment_id="BAD")])

    assert any("invalid establishment id" in failure for failure in _failures(tmp_path))


def test_duplicate_transfer_id_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_transfer_row(), _transfer_row()])

    assert any("duplicated" in failure for failure in _failures(tmp_path))


def test_duplicate_establishment_id_fails(tmp_path: Path) -> None:
    _valid_fixture(
        tmp_path,
        establishment_rows=[_establishment_row(), _establishment_row()],
    )

    assert any("duplicated" in failure for failure in _failures(tmp_path))


def test_invalid_transfer_status_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path, [_transfer_row(status="done")])

    assert any("invalid transfer status" in failure for failure in _failures(tmp_path))


def test_invalid_establishment_status_fails(tmp_path: Path) -> None:
    _valid_fixture(
        tmp_path,
        establishment_rows=[_establishment_row(status="done")],
    )

    assert any(
        "invalid establishment status" in failure for failure in _failures(tmp_path)
    )


def test_transferred_row_with_placeholder_fixture_fails(tmp_path: Path) -> None:
    _valid_fixture(
        tmp_path,
        [_transfer_row(status="transferred", golden_fixtures="TBD")],
    )

    assert any("golden_fixtures" in failure for failure in _failures(tmp_path))


def test_established_row_with_placeholder_conformance_fails(tmp_path: Path) -> None:
    _valid_fixture(
        tmp_path,
        establishment_rows=[
            _establishment_row(
                status="established",
                conformance_evidence="none",
            )
        ],
    )

    assert any("conformance_evidence" in failure for failure in _failures(tmp_path))


def test_dangerous_authority_claim_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "extra.md",
        "Godot owns movement rules.\n",
    )

    assert any(
        "Dangerous authority claim" in failure for failure in _failures(tmp_path)
    )


def test_established_authority_wording_does_not_fail(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "extra.md",
        "C++ owns gameplay semantics when established by an established record.\n",
    )

    assert not any(
        "Dangerous authority claim" in failure for failure in _failures(tmp_path)
    )


def test_authority_map_missing_protocol_link_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python remains reference authority for inherited behaviour.\n",
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


def test_godot_policy_missing_establishment_route_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "godot_cpp_policy.md",
        "GDScript must not duplicate inherited semantic truth. "
        "See docs/architecture/authority_transfer_protocol.md.\n",
    )

    assert any("route new authority establishment" in failure for failure in _failures(tmp_path))


def test_cpp_policy_missing_establishment_route_fails(tmp_path: Path) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "cpp_safety_policy.md",
        "C++ authority is provisional and parity-gated. "
        "See docs/architecture/authority_transfer_protocol.md.\n",
    )

    assert any("define new authority establishment" in failure for failure in _failures(tmp_path))


def test_review_checklist_missing_establishment_concepts_fails(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path)
    _write(
        tmp_path / "docs" / "governance" / "review_checklist.md",
        "authority transfer parity evidence authority map fallback path "
        "known exclusions\n",
    )

    failures = _failures(tmp_path)

    assert any("authority establishment" in failure for failure in failures)
    assert any("normative contract" in failure for failure in failures)
    assert any("conformance evidence" in failure for failure in failures)


def test_valid_transferred_row_requires_authority_map_reference(
    tmp_path: Path,
) -> None:
    _valid_fixture(tmp_path, [_transfer_row(status="transferred")])

    assert any("AT-0001" in failure for failure in _failures(tmp_path))

    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python remains reference authority for inherited behaviour. "
        "AT-0001 transferred trace parser to C++. "
        "docs/architecture/authority_transfer_protocol.md\n",
    )

    assert _failures(tmp_path) == []


def test_valid_established_row_requires_authority_map_reference(
    tmp_path: Path,
) -> None:
    _valid_fixture(
        tmp_path,
        establishment_rows=[_establishment_row(status="established")],
    )

    assert any("AE-0001" in failure for failure in _failures(tmp_path))

    _write(
        tmp_path / "docs" / "architecture" / "authority_map.md",
        "Python remains reference authority for inherited behaviour. "
        "AE-0001 established hold gameplay in Native C++. "
        "docs/architecture/authority_transfer_protocol.md\n",
    )

    assert _failures(tmp_path) == []
