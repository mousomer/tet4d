from __future__ import annotations

from pathlib import Path

import pytest

import tools.governance.validate_godot_semantic_boundary as boundary


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_validate_can_inspect_an_empty_targeted_fixture(tmp_path: Path) -> None:
    findings, scanned = boundary.validate(tmp_path / "godot")

    assert findings == []
    assert scanned == 0


def test_main_rejects_nonexistent_root_with_explicit_coverage_diagnostic(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "missing-godot"
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 1

    output = capsys.readouterr().out
    assert "Scanned 0 Godot script files." in output
    assert "coverage-integrity failure" in output
    assert "no eligible Godot script files" in output


def test_main_rejects_existing_root_that_yields_zero_files(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "godot"
    root.mkdir()
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 1

    assert "Scanned 0 Godot script files." in capsys.readouterr().out


def test_main_rejects_partial_tree_missing_required_test_domain(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "godot"
    _write_text(root / "scripts" / "shell.gd", "func render_shell():\n\tpass\n")
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 1

    output = capsys.readouterr().out
    assert "Scanned 1 Godot script files." in output
    assert "required scan domain(s) not represented: test" in output


def test_main_accepts_clean_tree_with_required_scan_domains(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "godot"
    _write_text(root / "scripts" / "shell.gd", "func render_shell():\n\tpass\n")
    _write_text(root / "tests" / "test_shell.gd", "func test_shell():\n\tpass\n")
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 0

    output = capsys.readouterr().out
    assert "Scanned 2 Godot script files." in output
    assert "validation passed" in output


def test_display_only_topology_label_does_not_fail(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "ui" / "panel.gd"
    _write_text(script, 'var topology_label = "Topology"\n')

    findings, scanned = boundary.validate(tmp_path / "godot")

    assert scanned == 1
    assert findings == []


def test_semantic_path_predicates_require_project_relative_paths(
    tmp_path: Path,
) -> None:
    absolute = tmp_path / "ui" / "scripts" / "rules.gd"

    with pytest.raises(ValueError, match="Godot-project-relative"):
        boundary._is_presentation_path(absolute)
    with pytest.raises(ValueError, match="Godot-project-relative"):
        boundary._is_godot_test_fixture(absolute)


def test_semantic_path_predicates_share_the_project_relative_frame() -> None:
    assert boundary._is_presentation_path(Path("scripts/ui/panel.gd"))
    assert not boundary._is_presentation_path(Path("scripts/rules.gd"))
    assert boundary._is_godot_test_fixture(Path("tests/test_shell.gd"))
    assert boundary._is_godot_test_fixture(Path("tests/integration/test_shell.gd"))
    assert not boundary._is_godot_test_fixture(Path("scripts/tests/test_shell.gd"))


def test_path_classification_is_checkout_parent_independent(tmp_path: Path) -> None:
    findings_by_parent: dict[str, list[tuple[int, str]]] = {}
    source = "var collision_map = {}\n"

    for parent in ("neutral", "ui", "tests", "bundle"):
        root = tmp_path / parent / "Tet4D.Godot"
        _write_text(root / "scripts" / "rules.gd", source)
        findings, scanned = boundary.validate(root)
        findings_by_parent[parent] = [
            (finding.line, finding.message) for finding in findings
        ]
        assert scanned == 1

    assert findings_by_parent == {
        parent: [(1, "suspicious semantic data structure")]
        for parent in ("neutral", "ui", "tests", "bundle")
    }


def test_adapter_routing_legal_move_call_with_suppression_does_not_fail(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "scripts" / "live_shell.gd"
    _write_text(
        script,
        "# tet4d-semantic-boundary: allow adapter-routing\nvar legal_moves = core.get_legal_moves(state)",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert findings == []


def test_compute_legal_moves_function_fails(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "rules.gd"
    _write_text(script, "func compute_legal_moves(state):\n\treturn []\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert findings[0].line == 1
    assert "compute_legal_moves" in findings[0].message


@pytest.mark.parametrize(
    "function_name",
    ("_check_collision_at", "check_collision_at", "_assert_legal_moves"),
)
def test_semantic_risk_outranks_helper_prefix_in_recognized_fixture(
    tmp_path: Path, function_name: str
) -> None:
    script = tmp_path / "godot" / "tests" / "test_shell.gd"
    _write_text(
        script,
        f"func {function_name}():\n\treturn true\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert function_name in findings[0].message


def test_ordinary_setup_helper_in_recognized_fixture_does_not_fail(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "tests" / "test_shell.gd"
    _write_text(
        script,
        "func _setup_shell_fixture():\n\treturn core.get_shell_state()\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert findings == []


@pytest.mark.parametrize(
    "fixture_path",
    (Path("tests/test_shell.gd"), Path("tests/integration/test_shell.gd")),
)
def test_equivalent_fixture_locations_accept_ordinary_assertion_helpers(
    tmp_path: Path, fixture_path: Path
) -> None:
    script = tmp_path / "godot" / fixture_path
    _write_text(
        script,
        "func _assert_rendered_label():\n\treturn rendered_label\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert findings == []


def test_semantic_computation_function_in_recognized_fixture_still_fails(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "tests" / "test_rules.gd"
    _write_text(script, "func compute_legal_moves(state):\n\treturn []\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "compute_legal_moves" in findings[0].message


def test_semantic_named_helper_in_nested_tests_directory_still_fails(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "scripts" / "tests" / "test_shell.gd"
    _write_text(
        script,
        "func _check_game_setup_validation_role():\n\treturn true\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "_check_game_setup_validation_role" in findings[0].message


@pytest.mark.parametrize(
    ("fixture_path", "expected_message"),
    (
        (Path("tests/test_x.gd"), "suspicious semantic assignment"),
        (Path("scripts/tests/test_x.gd"), "suspicious semantic data structure"),
    ),
)
def test_tests_path_component_does_not_create_presentation_assignment_exemption(
    tmp_path: Path, fixture_path: Path, expected_message: str
) -> None:
    script = tmp_path / "godot" / fixture_path
    _write_text(script, "var collision_map = {}\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert findings[0].message == expected_message


def test_same_semantic_named_helper_in_production_still_fails(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "shell.gd"
    _write_text(
        script,
        "func _check_game_setup_validation_role():\n\treturn true\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "_check_game_setup_validation_role" in findings[0].message


def test_explicit_test_fixture_suppression_remains_supported(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "tests" / "test_shell.gd"
    _write_text(
        script,
        "# tet4d-semantic-boundary: allow test-fixture\nvar collision_map = {}\n",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert findings == []


def test_recognized_test_fixture_does_not_bypass_semantic_assignments(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "tests" / "test_shell.gd"
    _write_text(script, "var collision_map = {}\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "semantic assignment" in findings[0].message


def test_local_collision_map_assignment_fails(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "rules.gd"
    _write_text(script, "var collision_map = {}\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "semantic data structure" in findings[0].message


def test_invalid_suppression_reason_fails(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "panel.gd"
    _write_text(script, "# tet4d-semantic-boundary: allow broad-waiver\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert len(findings) == 1
    assert "invalid semantic-boundary suppression reason" in findings[0].message


def test_vendor_addon_and_build_paths_are_excluded(tmp_path: Path) -> None:
    root = tmp_path / "godot"
    _write_text(root / "addons" / "x" / "rules.gd", "func compute_legal_moves():\n")
    _write_text(root / "build" / "rules.gd", "func compute_legal_moves():\n")
    _write_text(root / "vendor" / "rules.gd", "func compute_legal_moves():\n")

    findings, scanned = boundary.validate(root)

    assert findings == []
    assert scanned == 0


def test_coordinate_comparison_with_semantic_context_fails(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "rules.gd"
    _write_text(
        script,
        "var boundary_state = true\nfunc render_preview():\n\tif x < 0:\n\t\treturn false",
    )

    findings, _ = boundary.validate(tmp_path / "godot")

    assert any("coordinate comparison" in finding.message for finding in findings)


def test_coordinate_comparison_in_ui_layout_does_not_fail(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "scripts" / "layout.gd"
    _write_text(script, "func layout_panel(x):\n\tif x < 0:\n\t\treturn 0\n")

    findings, _ = boundary.validate(tmp_path / "godot")

    assert findings == []


def test_main_output_includes_path_and_line_number(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    root = tmp_path / "godot"
    script = root / "scripts" / "rules.gd"
    _write_text(script, "func compute_legal_moves(state):\n\treturn []\n")
    _write_text(root / "tests" / "test_shell.gd", "func test_shell():\n\tpass\n")
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 1

    output = capsys.readouterr().out
    assert "godot/scripts/rules.gd:1" in output
