from __future__ import annotations

from pathlib import Path

PATH = Path("tests/unit/governance/test_governance_validate_project_contracts.py")
OLD = '    assert "## Task profiles" in must_contain\n'
NEW = (
    '    assert "## Machine-readable task routing and composable verification" '
    'in must_contain\n'
)

text = PATH.read_text(encoding="utf-8")
if OLD not in text:
    raise SystemExit("expected legacy workflow-heading assertion not found")
PATH.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
