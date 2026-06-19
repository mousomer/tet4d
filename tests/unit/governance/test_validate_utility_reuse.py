from __future__ import annotations

from pathlib import Path

import tools.governance.validate_utility_reuse as utility_reuse


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_minimal_policy_docs(root: Path) -> None:
    _write(
        root / "docs" / "architecture" / "utility_index.md",
        "## Required fields\nOwner\nReuse rule\nMigration relevance\n",
    )
    _write(
        root / "docs" / "governance" / "README.md",
        "utility_index POLICY_NO_REINVENTING_WHEEL validate_utility_reuse "
        "check_wheel_reuse_rules check_dedup_dead_code_rules\n",
    )
    _write(
        root / "docs" / "governance" / "review_checklist.md",
        "## Dependency / utility reuse\nreuse no-reinvention utility\n",
    )
    _write(
        root / "docs" / "governance" / "codex_policy.md",
        "Search existing helpers before adding new utility code.\n",
    )
    _write(
        root / "docs" / "policies" / "POLICY_NO_REINVENTING_WHEEL.md",
        "Search existing project utilities and utility index.\n",
    )
    _write(
        root / "tools" / "governance" / "validate_governance.py",
        "from tools.governance import validate_utility_reuse\n",
    )


def test_utility_index_missing_fails(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_policy_docs(tmp_path)
    (tmp_path / "docs" / "architecture" / "utility_index.md").unlink()
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)

    findings = utility_reuse.validate_policy_links()

    assert any(
        "docs/architecture/utility_index.md missing" in finding.message
        for finding in findings
    )


def test_router_missing_utility_index_link_fails(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_policy_docs(tmp_path)
    _write(tmp_path / "docs" / "governance" / "README.md", "validate_utility_reuse\n")
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)

    findings = utility_reuse.validate_policy_links()

    assert any("utility_index" in finding.message for finding in findings)


def test_invalid_suppression_reason_is_blocking(tmp_path: Path) -> None:
    target = tmp_path / "tools" / "sample.py"
    marker = "tet4d-utility-" + "reuse: allow temporary"
    _write(
        target,
        f"# {marker}\ndef load_config() -> dict[str, str]:\n    return {{}}\n",
    )

    _symbols, findings = utility_reuse.scan_symbols(target)

    assert any(
        finding.severity == "blocking"
        and "invalid utility-reuse suppression reason `temporary`" in finding.message
        for finding in findings
    )


def test_valid_suppression_applies_to_next_line(tmp_path: Path) -> None:
    target = tmp_path / "tools" / "sample.py"
    marker = "tet4d-utility-" + "reuse: allow local-one-off"
    _write(
        target,
        f"# {marker}\ndef load_config() -> dict[str, str]:\n    return {{}}\n",
    )

    symbols, findings = utility_reuse.scan_symbols(target)

    assert findings == []
    assert symbols == []


def test_duplicate_helper_is_advisory_by_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)
    first = tmp_path / "src" / "tet4d" / "engine" / "config_reader.py"
    second = tmp_path / "tools" / "migration" / "config_reader.py"
    _write(first, "def load_config() -> dict[str, str]:\n    return {}\n")
    _write(second, "def load_config() -> dict[str, str]:\n    return {}\n")

    symbols = [
        utility_reuse.Symbol("load_config", first, 1),
        utility_reuse.Symbol("load_config", second, 1),
    ]

    findings = utility_reuse._duplicate_findings(symbols, strict=False)

    assert len(findings) == 1
    assert findings[0].severity == "advisory"
    assert "possible duplicate helper name `load_config`" in findings[0].message


def test_default_mode_does_not_fail_only_for_advisory_duplicates(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_policy_docs(tmp_path)
    _write(
        tmp_path / "src" / "tet4d" / "engine" / "config_reader.py",
        "def load_config() -> dict[str, str]:\n    return {}\n",
    )
    _write(
        tmp_path / "tools" / "migration" / "config_reader.py",
        "def load_config() -> dict[str, str]:\n    return {}\n",
    )
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)
    monkeypatch.delenv("TET4D_STRICT_UTILITY_REUSE", raising=False)

    assert utility_reuse.main() == 0


def test_duplicate_helper_is_blocking_in_strict_mode(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)
    first = tmp_path / "src" / "tet4d" / "engine" / "trace_reader.py"
    second = tmp_path / "tools" / "migration" / "trace_reader.py"
    _write(first, "def parse_trace() -> dict[str, str]:\n    return {}\n")
    _write(second, "def parse_trace() -> dict[str, str]:\n    return {}\n")

    symbols = [
        utility_reuse.Symbol("parse_trace", first, 1),
        utility_reuse.Symbol("parse_trace", second, 1),
    ]

    findings = utility_reuse._duplicate_findings(symbols, strict=True)

    assert len(findings) == 1
    assert findings[0].severity == "blocking"


def test_strict_mode_fails_on_unsuppressed_duplicate_helpers(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_policy_docs(tmp_path)
    _write(
        tmp_path / "src" / "tet4d" / "engine" / "trace_reader.py",
        "def parse_trace() -> dict[str, str]:\n    return {}\n",
    )
    _write(
        tmp_path / "tools" / "migration" / "trace_reader.py",
        "def parse_trace() -> dict[str, str]:\n    return {}\n",
    )
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)
    monkeypatch.setenv("TET4D_STRICT_UTILITY_REUSE", "1")

    assert utility_reuse.main() == 1


def test_godot_lifecycle_methods_are_ignored(tmp_path: Path) -> None:
    target = tmp_path / "godot" / "scripts" / "sample.gd"
    _write(target, "func _ready():\n\tpass\nfunc _process(delta):\n\tpass\n")

    symbols, findings = utility_reuse.scan_symbols(target)

    assert findings == []
    assert symbols == []


def test_test_functions_are_ignored(tmp_path: Path) -> None:
    target = tmp_path / "tests" / "unit" / "test_sample.py"
    _write(target, "def test_load_config() -> None:\n    pass\n")

    symbols, findings = utility_reuse.scan_symbols(target)

    assert findings == []
    assert symbols == []


def test_discovery_excludes_vendored_and_godot_cache_files(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)
    kept = tmp_path / "tools" / "governance" / "sample.py"
    vendored = tmp_path / "native" / "third_party" / "lib" / "sample.py"
    godot_cache = tmp_path / "godot" / "Tet4D.Godot" / ".godot" / "cache.gd"
    _write(kept, "def load_config() -> dict[str, str]:\n    return {}\n")
    _write(vendored, "def load_config() -> dict[str, str]:\n    return {}\n")
    _write(godot_cache, "func load_config():\n\treturn {}\n")

    files = utility_reuse.discover_source_files(tmp_path)

    assert files == [kept]


def test_existing_dedup_and_wheel_scripts_are_recognized(
    tmp_path: Path, monkeypatch
) -> None:
    _write_minimal_policy_docs(tmp_path)
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)

    findings = utility_reuse.validate_policy_links()

    assert findings == []


def test_advisory_output_includes_path_and_line_number(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    _write_minimal_policy_docs(tmp_path)
    _write(
        tmp_path / "src" / "tet4d" / "engine" / "config_reader.py",
        "\ndef load_config() -> dict[str, str]:\n    return {}\n",
    )
    _write(
        tmp_path / "tools" / "migration" / "config_reader.py",
        "def load_config() -> dict[str, str]:\n    return {}\n",
    )
    monkeypatch.setattr(utility_reuse, "ROOT", tmp_path)

    assert utility_reuse.main() == 0
    output = capsys.readouterr().out
    assert "src/tet4d/engine/config_reader.py:2" in output
