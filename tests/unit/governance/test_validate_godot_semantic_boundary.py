from __future__ import annotations

from pathlib import Path

import tools.governance.validate_godot_semantic_boundary as boundary


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_no_scripts_found_returns_success(tmp_path: Path) -> None:
    findings, scanned = boundary.validate(tmp_path / "godot")

    assert findings == []
    assert scanned == 0


def test_display_only_topology_label_does_not_fail(tmp_path: Path) -> None:
    script = tmp_path / "godot" / "ui" / "panel.gd"
    _write_text(script, 'var topology_label = "Topology"\n')

    findings, scanned = boundary.validate(tmp_path / "godot")

    assert scanned == 1
    assert findings == []


def test_adapter_routing_legal_move_call_with_suppression_does_not_fail(
    tmp_path: Path,
) -> None:
    script = tmp_path / "godot" / "scripts" / "live_shell.gd"
    _write_text(
        script,
        "\n".join(
            [
                "# tet4d-semantic-boundary: allow adapter-routing",
                "var legal_moves = core.get_legal_moves(state)",
            ]
        ),
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
        "\n".join(
            [
                "var boundary_state = true",
                "func render_preview():",
                "\tif x < 0:",
                "\t\treturn false",
            ]
        ),
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
    monkeypatch.setattr(boundary, "ROOT", tmp_path)
    monkeypatch.setattr(boundary, "GODOT_ROOT", root)

    assert boundary.main() == 1

    output = capsys.readouterr().out
    assert "godot/scripts/rules.gd:1" in output
