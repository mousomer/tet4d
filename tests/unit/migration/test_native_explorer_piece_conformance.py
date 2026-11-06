"""The full pytest gate must compile and execute production native preservation tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_native_explorer_piece_conformance() -> None:
    completed = subprocess.run(
        [
            "bash",
            str(ROOT / "scripts/test_godot_tet4d_core.sh"),
            "--explorer-piece-conformance",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    prefix = "explorer_piece_conformance: "
    report = json.loads(
        next(
            line.removeprefix(prefix)
            for line in completed.stdout.splitlines()
            if line.startswith(prefix)
        )
    )
    fixture = ROOT / "tests/fixtures/explorer_topology/transport_v1.json"
    assert report["fixture_sha256"] == hashlib.sha256(fixture.read_bytes()).hexdigest()
    assert report["sequences"] > 0
    assert report["successful_translations"] > 0
    assert report["inverse_recoveries"] > 0
    assert report["atomic_rejections"] > 0
