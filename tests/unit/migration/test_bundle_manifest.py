from __future__ import annotations

import json
import re
from pathlib import Path

from tools.migration.export_config_bundle import export_bundle, file_sha256


_LOCAL_USER_PATH = "/" + "Users" + "/"
_LOCAL_USER_PATH_WINDOWS = "\\" + "Users" + "\\"
_FORBIDDEN_TEXT = re.compile(
    "|".join(
        re.escape(pattern)
        for pattern in (
            _LOCAL_USER_PATH,
            _LOCAL_USER_PATH_WINDOWS,
            "generated_at",
            "created_at",
            "timestamp",
            "datetime",
            "object at 0x",
        )
    ),
    re.IGNORECASE,
)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def test_bundle_manifest_declares_non_authoritative_migration_bundle(
    tmp_path: Path,
) -> None:
    export_bundle(tmp_path)
    manifest = _read_json(tmp_path / "manifest.json")

    assert manifest["bundle_type"] == "tet4d_migration_bundle"
    assert manifest["bundle_version"] == 1
    assert manifest["authority"]["python_semantic_oracle"] is True
    assert manifest["authority"]["exported_bundle_is_authority"] is False
    assert manifest["verification"]["compare_trace_required"] is True
    assert manifest["verification"]["config_bundle_check_required"] is True


def test_bundle_indexes_and_copies_topology_gameplay_and_endgame_traces(
    tmp_path: Path,
) -> None:
    export_bundle(tmp_path)
    manifest = _read_json(tmp_path / "manifest.json")

    for trace_type in ("topology", "gameplay", "endgame"):
        entries = manifest["traces"][trace_type]
        source_files = sorted(
            Path("migration/golden_traces", trace_type).glob("*.json")
        )
        assert [entry["source_path"] for entry in entries] == [
            path.as_posix() for path in source_files
        ]
        for entry in entries:
            source = Path(entry["source_path"])
            copied = tmp_path / entry["path"]
            assert copied.is_file()
            assert entry["sha256"] == file_sha256(source)
            assert file_sha256(copied) == file_sha256(source)
            assert entry["case_id"]
            assert entry["frame_count"] >= 0


def test_bundle_config_digest_entries_match_source_files(tmp_path: Path) -> None:
    export_bundle(tmp_path)
    config_bundle = _read_json(tmp_path / "config" / "tet4d_config_bundle.json")

    assert config_bundle["authority"]["exported_bundle_is_authority"] is False
    for path, entry in config_bundle["source_files"].items():
        assert entry["sha256"] == file_sha256(Path(path))
    assert (
        config_bundle["source_files"]["config/project/policy_pack.json"][
            "payload_included"
        ]
        is False
    )


def test_bundle_authority_docs_and_schema_indexes_are_present(tmp_path: Path) -> None:
    export_bundle(tmp_path)
    docs = _read_json(tmp_path / "docs" / "authority_index.json")
    schemas = _read_json(tmp_path / "schemas" / "schema_index.json")

    doc_paths = {entry["source_path"] for entry in docs["files"]}
    assert "CURRENT_STATE.md" in doc_paths
    assert "docs/rds/RDS_TETRIS_GENERAL.md" in doc_paths
    assert "docs/plans/endgame_trace_export.md" in doc_paths
    assert "docs/plans/gameboard_visual_language_design.md" in doc_paths
    for entry in docs["files"]:
        assert entry["sha256"] == file_sha256(Path(entry["source_path"]))

    assert schemas["trace_schema"]["source_path"] == "tools/migration/trace_schema.py"
    assert schemas["files"]
    for entry in schemas["files"]:
        assert entry["sha256"] == file_sha256(Path(entry["source_path"]))


def test_bundle_readme_and_contents_are_hygienic(tmp_path: Path) -> None:
    export_bundle(tmp_path)
    readme = (tmp_path / "README.md").read_text(encoding="utf-8").lower()

    assert "generated" in readme
    assert "not a source of truth" in readme
    assert "python remains the semantic oracle" in readme

    for path in tmp_path.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert not _FORBIDDEN_TEXT.search(text), path
