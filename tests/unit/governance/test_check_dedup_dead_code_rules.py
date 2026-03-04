from __future__ import annotations

from pathlib import Path

import tools.governance.check_dedup_dead_code_rules as dedup


def test_todo_requires_backlog_id(tmp_path: Path, monkeypatch) -> None:
    code_dir = tmp_path / "src" / "pkg"
    code_dir.mkdir(parents=True, exist_ok=True)
    (code_dir / "sample.py").write_text(
        "def f():\n    # TODO cleanup this block\n    return 1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(dedup, "ROOT", tmp_path)
    issues = dedup._check_todo_backlog_rule(
        {
            "todo_backlog_rule": {
                "scope_globs": ["src/**/*.py"],
                "ignore_globs": [],
                "token_regex": r"\bTODO\b",
                "required_backlog_regex": r"\[BKL-[^\]]+\]",
            }
        }
    )
    assert issues
    assert "missing backlog id" in issues[0].message


def test_duplicate_function_body_detected(tmp_path: Path, monkeypatch) -> None:
    gov_dir = tmp_path / "tools" / "governance"
    gov_dir.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        [
            "def copy_logic(x):",
            "    a = x + 1",
            "    b = a + 1",
            "    c = b + 1",
            "    d = c + 1",
            "    e = d + 1",
            "    f = e + 1",
            "    g = f + 1",
            "    h = g + 1",
            "    i = h + 1",
            "    j = i + 1",
            "    k = j + 1",
            "    return k",
        ]
    )
    (gov_dir / "a.py").write_text(body + "\n", encoding="utf-8")
    (gov_dir / "b.py").write_text(body + "\n", encoding="utf-8")
    monkeypatch.setattr(dedup, "ROOT", tmp_path)
    issues, warnings = dedup._check_duplicate_functions(
        {
            "duplicate_functions": {
                "enabled": True,
                "strict_scope_globs": ["tools/governance/*.py"],
                "advisory_scope_globs": [],
                "min_body_lines": 10,
                "max_allowed_duplicates_per_signature": 1,
                "exclude_function_names": [],
            }
        }
    )
    assert issues
    assert warnings == []
    assert "duplicate function bodies detected" in issues[0].message
