from __future__ import annotations

from pathlib import Path
import json

import tools.governance.validate_project_contracts as contracts


def _write_backlog(root: Path, text: str) -> None:
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    (docs_dir / "BACKLOG.md").write_text(text, encoding="utf-8")


def _write_context_router(root: Path, payload: dict[str, object]) -> Path:
    manifest_dir = root / "config/project/policy/manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / "context_router_manifest.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _valid_context_router_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "contexts": [
            {
                "id": "code",
                "title": "Code",
                "description": "Code context",
                "include_globs": ["src/**"],
                "exclude_globs": ["**/__pycache__/**"],
                "priority": 10,
            },
            {
                "id": "planning",
                "title": "Planning",
                "description": "Planning context",
                "include_globs": ["docs/**/plans/**"],
                "exclude_globs": [],
                "priority": 20,
            },
        ],
        "routing_rules": [
            {
                "when_task_tags_any": ["refactor"],
                "include_contexts_ordered": ["code", "planning"],
            }
        ],
    }


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


def test_context_router_manifest_allows_valid_payload(tmp_path, monkeypatch) -> None:
    path = _write_context_router(tmp_path, _valid_context_router_payload())
    monkeypatch.setattr(contracts, "CONTEXT_ROUTER_PATH", path)

    assert contracts._validate_context_router_manifest() == []


def test_context_router_manifest_rejects_unknown_context_id(
    tmp_path, monkeypatch
) -> None:
    payload = _valid_context_router_payload()
    contexts = payload["contexts"]
    assert isinstance(contexts, list)
    contexts[0]["id"] = "unknown"  # type: ignore[index]
    path = _write_context_router(tmp_path, payload)
    monkeypatch.setattr(contracts, "CONTEXT_ROUTER_PATH", path)

    issues = contracts._validate_context_router_manifest()

    assert issues
    assert any("must be one of" in issue.message for issue in issues)
