from __future__ import annotations

from pathlib import Path

import tools.governance.validate_config_authority as validator


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_required_policy_docs(
    root: Path, *, config_policy: str | None = None
) -> None:
    _write_text(
        root / "docs" / "governance" / "config_policy.md",
        config_policy
        or "\n".join(
            [
                "# Config Policy",
                "Config authority routes through docs/policies/POLICY_NO_MAGIC_NUMBERS.md.",
                "Python configuration remains authoritative.",
                "Use config/project/constants.json.",
                "Use config/gameplay/tuning.json.",
                "Use config/menu/defaults.json.",
            ]
        ),
    )
    _write_text(
        root / "docs" / "policies" / "POLICY_NO_MAGIC_NUMBERS.md",
        "See docs/governance/config_policy.md and validate_config_authority.\n",
    )
    _write_text(
        root / "docs" / "policies" / "POLICY_CONFIGURATION_DOCUMENTATION.md",
        "\n".join(
            [
                "config/project/policy_pack.json",
                "config/project/constants.json",
                "config/gameplay/tuning.json",
                "config/menu/defaults.json",
                "docs/CONFIGURATION_REFERENCE.md",
            ]
        ),
    )
    _write_text(root / "docs" / "policies" / "INDEX.md", "config policies\n")


def test_no_source_files_found_succeeds(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)

    findings, scanned = validator.validate(tmp_path)

    assert findings == []
    assert scanned == 0


def test_trivial_literals_do_not_warn(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(tmp_path / "tet4d" / "sample.py", "value = -1 + 0 + 1 + 2\n")

    findings, scanned = validator.validate(tmp_path)

    assert scanned == 1
    assert findings == []


def test_suspicious_literal_produces_advisory(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(
        tmp_path / "tet4d" / "sample.py",
        "alpha = 0.5\ncell_size = 24\nduration_ms = 250\n",
    )

    findings, _ = validator.validate(tmp_path)

    assert any(finding.severity == "advisory" for finding in findings)
    assert any("0.5" in finding.message for finding in findings)


def test_default_mode_allows_advisory_constants(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(tmp_path / "tet4d" / "sample.py", "alpha = 0.5\n")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.delenv("TET4D_STRICT_CONFIG_AUTHORITY", raising=False)

    assert validator.main() == 0
    assert "advisory warnings" in capsys.readouterr().out


def test_strict_mode_fails_on_unsuppressed_suspicious_constants(
    tmp_path: Path, monkeypatch
) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(tmp_path / "tet4d" / "sample.py", "duration = 0.25\n")
    monkeypatch.setattr(validator, "ROOT", tmp_path)
    monkeypatch.setenv("TET4D_STRICT_CONFIG_AUTHORITY", "1")

    assert validator.main() == 1


def test_valid_suppression_reason_suppresses_warning(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(
        tmp_path / "tet4d" / "sample.py",
        "# tet4d-config-authority: allow legacy-existing\nalpha = 0.5\n",
    )

    findings, _ = validator.validate(tmp_path)

    assert findings == []


def test_invalid_suppression_reason_fails(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(
        tmp_path / "tet4d" / "sample.py",
        "# tet4d-config-authority: allow broad-exception\nalpha = 0.5\n",
    )

    findings, _ = validator.validate(tmp_path)

    assert any(finding.severity == "error" for finding in findings)
    assert any("broad-exception" in finding.message for finding in findings)


def test_excluded_vendor_and_build_paths_are_ignored(tmp_path: Path) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(tmp_path / "native" / "vendor" / "sample.cpp", "float alpha = 0.5;\n")
    _write_text(tmp_path / "native" / "build" / "sample.cpp", "float alpha = 0.5;\n")

    findings, scanned = validator.validate(tmp_path)

    assert findings == []
    assert scanned == 0


def test_policy_link_validation_fails_when_config_policy_text_missing(
    tmp_path: Path,
) -> None:
    _write_required_policy_docs(tmp_path, config_policy="# Config Policy\n")

    findings = validator.validate_policy_links(tmp_path)

    assert any("config policy missing" in finding.message for finding in findings)


def test_advisory_output_includes_path_and_line_number(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_required_policy_docs(tmp_path)
    _write_text(tmp_path / "tet4d" / "sample.py", "\nalpha = 0.5\n")
    monkeypatch.setattr(validator, "ROOT", tmp_path)

    assert validator.main() == 0
    output = capsys.readouterr().out
    assert "tet4d/sample.py:2" in output
