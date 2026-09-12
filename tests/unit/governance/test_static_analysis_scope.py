"""One static-analysis scope, consumed by every gate.

The canonical gate checked formatting over `scripts tools` while the focused
gate defaulted to the whole repository. Thirteen files were therefore in
violation and invisible to the gate that decides whether a change may merge.
The defect was not the thirteen files; it was two gates carrying separate
target lists. These cases pin the single authority and refuse a return to that
shape.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
POLICY = ROOT / "config/project/policy_pack.json"
GATES = (ROOT / "scripts/verify.sh", ROOT / "scripts/verify_focus.sh")


def declared_scope() -> dict[str, list[str]]:
    return json.loads(POLICY.read_text(encoding="utf-8"))["code_rules"][
        "static_analysis"
    ]


def ruff_invocations(script: Path) -> list[str]:
    lines = []
    for raw in script.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#"):
            continue
        if "ruff check" in line or "ruff format" in line:
            lines.append(line)
    return lines


def test_the_scope_is_declared_once() -> None:
    scope = declared_scope()
    assert scope["ruff_check_scope"], scope
    assert scope["ruff_format_scope"], scope


def test_lint_and_format_cover_the_same_scope() -> None:
    """A narrower format scope is exactly how the drift hid.

    Lint already ran repository-wide, so formatting checked less than linting
    and nothing reported the difference.
    """
    scope = declared_scope()
    assert scope["ruff_check_scope"] == scope["ruff_format_scope"], scope


def test_every_gate_reads_the_declared_scope() -> None:
    for gate in GATES:
        assert "static_analysis" in gate.read_text(encoding="utf-8"), gate.name


def test_no_gate_spells_a_ruff_target_literally() -> None:
    """Drift is only possible while a gate carries its own target list."""
    for gate in GATES:
        invocations = ruff_invocations(gate)
        assert invocations, f"{gate.name} runs no ruff at all"
        for line in invocations:
            arguments = line.split("ruff", 1)[1]
            assert "[@]}" in arguments, f"{gate.name}: {line}"
