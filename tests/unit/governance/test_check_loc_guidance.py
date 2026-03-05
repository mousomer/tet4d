from __future__ import annotations

import tools.governance.check_loc_guidance as loc


def test_collect_buckets_tracks_net_loc() -> None:
    rows = [
        (10, 2, "src/tet4d/example.py"),
        (3, 1, "tools/governance/example.py"),
        (5, 5, "tests/unit/test_example.py"),
        (8, 0, "README.md"),
    ]
    buckets = loc._collect_buckets(
        rows,
        include_exts={".py"},
        bucket_patterns={
            "src": "src/",
            "tests": "tests/",
            "tools_scripts": "tools/|scripts/",
        },
    )
    assert buckets["src"].net == 8
    assert buckets["tests"].net == 0
    assert buckets["tools_scripts"].net == 2


def test_main_emits_non_blocking_warning(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        loc,
        "_load_config",
        lambda: {
            "include_extensions": [".py"],
            "buckets": {"src": "src/"},
            "thresholds": {"mixed": {"src": 1}},
            "default_batch_type": "mixed",
            "batch_type_env_var": "LOC_GUIDANCE_BATCH_TYPE",
        },
    )
    monkeypatch.setattr(loc, "_git_numstat", lambda: [(5, 0, "src/tet4d/foo.py")])
    assert loc.main() == 0
    out = capsys.readouterr().out
    assert "warnings (non-blocking)" in out
