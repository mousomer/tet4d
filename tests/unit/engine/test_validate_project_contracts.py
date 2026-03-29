from __future__ import annotations

from pathlib import Path

import tools.governance.validate_project_contracts as contracts


def _write_backlog(root: Path, text: str) -> None:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "BACKLOG.md").write_text(text, encoding="utf-8")


def test_backlog_id_uniqueness_rejects_duplicates(tmp_path, monkeypatch) -> None:
    _write_backlog(
        tmp_path,
        "\n".join(
            [
                "1. [BKL-P2-100] one",
                "2. [BKL-P2-100] duplicate",
            ]
        ),
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    issues = contracts._validate_backlog_id_uniqueness()

    assert len(issues) == 1
    assert issues[0].kind == "duplicate"
    assert "BKL-P2-100" in issues[0].message


def test_backlog_id_uniqueness_allows_unique_ids(tmp_path, monkeypatch) -> None:
    _write_backlog(
        tmp_path,
        "\n".join(
            [
                "1. [BKL-P2-101] one",
                "2. [BKL-P2-102] two",
            ]
        ),
    )
    monkeypatch.setattr(contracts, "PROJECT_ROOT", tmp_path)

    assert contracts._validate_backlog_id_uniqueness() == []
