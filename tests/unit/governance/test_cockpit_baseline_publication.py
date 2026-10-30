"""Keep evidence provenance compatible with the real publication formatter."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
BASELINE = ROOT / "docs/design/baselines/cockpit_windowed_2026_10_26"


def test_published_baseline_has_only_declared_newline_normalization() -> None:
    manifest = json.loads((BASELINE / "manifest.json").read_text(encoding="utf-8"))
    published = (BASELINE / "observations.json").read_bytes()
    assert published.endswith(b"\n"), "published evidence must satisfy the formatter"
    representation = manifest["repository_observation"]
    assert representation["normalization"] == "append exactly one LF to supplied bytes"
    assert hashlib.sha256(published).hexdigest() == representation["sha256"]
    original_hashes = {run["sha256"] for run in manifest["runs"]}
    assert {hashlib.sha256(published[:-1]).hexdigest()} == original_hashes
    assert representation["source_sha256"] in original_hashes


@pytest.mark.parametrize("final_newline", [False, True])
def test_formatter_enforces_newline_on_tracked_evidence(
    tmp_path: Path, final_newline: bool
) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(ROOT / "scripts/check_text_formatting.sh", scripts)
    # The formatter's only environment dependency; no policy/toolchain mock is
    # used for its Git discovery or formatting logic.
    (tmp_path / "gov").write_text(
        '#!/usr/bin/env bash\nprintf "PYTHON_BIN=%q\\n" "$TET4D_TEST_PYTHON"\n',
        encoding="utf-8",
    )
    (tmp_path / "gov").chmod(0o755)
    evidence = tmp_path / "docs/design/baselines/sample/observations.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b'{"observations": []}' + (b"\n" if final_newline else b""))
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(TET4D_TEST_PYTHON=sys.executable, GIT_CONFIG_GLOBAL=os.devnull,
               GIT_CONFIG_SYSTEM=os.devnull)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=env, check=True)
    subprocess.run(["git", "add", "docs"], cwd=tmp_path, env=env, check=True)
    result = subprocess.run(
        ["bash", "scripts/check_text_formatting.sh"], cwd=tmp_path,
        env=env, capture_output=True, text=True, check=False,
    )
    assert result.returncode == (0 if final_newline else 2), result.stderr
    if not final_newline:
        assert "missing trailing newline" in result.stderr
        assert "docs/design/baselines/sample/observations.json" in result.stderr
