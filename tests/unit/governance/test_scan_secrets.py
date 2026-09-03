from __future__ import annotations

import json
from pathlib import Path

import pytest

import tools.governance.scan_secrets as scanner

# Every fake token below is assembled at runtime from fragments so that this
# source file never contains a string the repository scanner would match.
_LONG_PREFIX = "gh" + "p" + "_"
_LONG_BODY = "Q7w" * 12  # 36 chars, well above the 20-char pattern minimum
_SHORT_BODY = "ZZ" + "4" * 4


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _long_token() -> str:
    return _LONG_PREFIX + _LONG_BODY


def _short_token() -> str:
    return _SHORT_BODY


def _config(allowlist: list[dict[str, object]] | None = None) -> str:
    return json.dumps(
        {
            "version": 1,
            "scan_roots": ["."],
            "exclude_dirs": [],
            "exclude_globs": [],
            "max_file_bytes": 1_048_576,
            "patterns": [
                {"id": "long_demo", "regex": "gh[pousr]_[A-Za-z0-9]{20,}"},
                {"id": "short_demo", "regex": "ZZ[0-9]{4}"},
            ],
            "allowlist": allowlist or [],
        }
    )


@pytest.fixture
def scan_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    config = tmp_path / "secret_scan.json"
    _write(config, _config())
    monkeypatch.setattr(scanner, "PROJECT_ROOT", root)
    monkeypatch.setattr(scanner, "CONFIG_PATH", config)
    return root


def _run(capsys: pytest.CaptureFixture[str]) -> tuple[int, str]:
    result = scanner.main()
    captured = capsys.readouterr()
    return result, captured.out + captured.err


def test_finding_carries_no_matched_content() -> None:
    assert "preview" not in scanner.Finding.__dataclass_fields__
    assert not hasattr(scanner, "_token_preview")


def test_long_match_is_reported_without_any_fragment(
    scan_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    token = _long_token()
    _write(scan_root / "src" / "leak.txt", f"first\nkey = {token}\n")

    result, output = _run(capsys)

    assert result == 1
    assert "- [long_demo] src/leak.txt:2" in output
    assert token not in output
    assert token[:4] not in output
    assert token[-4:] not in output
    assert _LONG_BODY[:6] not in output


def test_short_match_is_reported_without_value(
    scan_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    token = _short_token()
    _write(scan_root / "note.md", f"{token}\n")

    result, output = _run(capsys)

    assert result == 1
    assert "- [short_demo] note.md:1" in output
    assert token not in output


def test_multiple_findings_are_bounded(
    scan_root: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(scanner, "MAX_REPORTED_FINDINGS", 3)
    token = _long_token()
    for index in range(5):
        _write(scan_root / f"file{index}.txt", f"{token}\n")

    result, output = _run(capsys)

    assert result == 1
    finding_lines = [line for line in output.splitlines() if "[long_demo]" in line]
    assert len(finding_lines) == 3
    assert "2 additional finding(s) omitted" in output
    assert token not in output


def test_format_findings_without_overflow_has_no_omitted_row() -> None:
    findings = [scanner.Finding("id", "a.txt", 1), scanner.Finding("id", "b.txt", 2)]

    lines = scanner.format_findings(findings, limit=2)

    assert lines == ["- [id] a.txt:1", "- [id] b.txt:2"]


def test_allowlisted_match_is_not_reported(
    scan_root: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    token = _long_token()
    _write(scan_root / "fixtures" / "sample.txt", f"{token}\n")
    _write(
        tmp_path / "secret_scan.json",
        _config(
            allowlist=[
                {
                    "path_glob": "fixtures/*",
                    "pattern_ids": ["long_demo"],
                    "contains": _LONG_BODY[:9],
                }
            ]
        ),
    )

    result, output = _run(capsys)

    assert result == 0
    assert "Secret scan passed" in output
    assert token not in output


def test_clean_tree_passes(scan_root: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(scan_root / "README.md", "nothing sensitive here\n")

    result, output = _run(capsys)

    assert result == 0
    assert (
        output.strip() == "Secret scan passed: no potential secret patterns detected."
    )
