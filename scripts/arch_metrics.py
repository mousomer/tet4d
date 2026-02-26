#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _py_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return [
        p
        for p in sorted(root.rglob("*.py"))
        if ".git" not in p.parts and ".venv" not in p.parts and "__pycache__" not in p.parts
    ]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _match_lines(paths: list[Path], pattern: str) -> list[str]:
    rx = re.compile(pattern)
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def _match_engine_deep_import_lines(paths: list[Path]) -> list[str]:
    rx = re.compile(r"^\s*(?:from|import)\s+tet4d\.engine(?:\.|\b)")
    allow_rx = re.compile(
        r"^\s*(?:from|import)\s+tet4d\.engine\.api(?:\.|\b)|^\s*from\s+tet4d\.engine\s+import\s+api(?:\s|,|$)"
    )
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line) and not allow_rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def _match_core_to_non_core_engine_imports(paths: list[Path]) -> list[str]:
    rx = re.compile(r"^\s*(?:from|import)\s+tet4d\.engine(?:\.|\b)")
    allow_rx = re.compile(
        r"^\s*(?:from|import)\s+tet4d\.engine\.core(?:\.|\b)|^\s*from\s+tet4d\.engine\s+import\s+core(?:\s|,|$)"
    )
    hits: list[str] = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(_read(path).splitlines(), start=1):
            if rx.search(line) and not allow_rx.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def main() -> int:
    engine_paths = [p for p in _py_files(REPO_ROOT / "src/tet4d/engine") if "tests" not in p.parts]
    core_paths = _py_files(REPO_ROOT / "src/tet4d/engine/core")
    replay_paths = _py_files(REPO_ROOT / "src/tet4d/replay")
    ai_paths = _py_files(REPO_ROOT / "src/tet4d/ai")
    ui_paths = _py_files(REPO_ROOT / "src/tet4d/ui")
    tools_stability_paths = _py_files(REPO_ROOT / "tools/stability")
    tools_bench_paths = _py_files(REPO_ROOT / "tools/benchmarks")
    playbot_external_paths = _py_files(REPO_ROOT / "cli") + _py_files(REPO_ROOT / "tools") + _py_files(
        REPO_ROOT / "src/tet4d/engine/tests"
    )

    ui_deep_engine = _match_engine_deep_import_lines(ui_paths)
    replay_deep_engine = _match_engine_deep_import_lines(replay_paths)
    ai_deep_engine = _match_engine_deep_import_lines(ai_paths)
    core_non_core_engine = _match_core_to_non_core_engine_imports(core_paths)
    tools_stability_deep_engine = _match_engine_deep_import_lines(tools_stability_paths)
    tools_bench_deep_engine = _match_engine_deep_import_lines(tools_bench_paths)
    legacy_engine_playbot_external = _match_lines(
        playbot_external_paths,
        r"^\s*(?:from|import)\s+tet4d\.engine\.playbot(?:\.|\b)",
    )

    core_random_imports = [
        line
        for line in _match_lines(core_paths, r"^\s*(?:from|import)\s+random(?:\.|\b)")
        if not line.startswith("src/tet4d/engine/core/rng/")
    ]
    core_purity_hits = {
        "pygame_ui_tools_imports": _match_lines(
            core_paths,
            r"^\s*(?:from|import)\s+(?:pygame(?:\.|\b)|tet4d\.ui(?:\.|\b)|tet4d\.tools(?:\.|\b)|tools(?:\.|\b))",
        ),
        "time_logging_imports": _match_lines(core_paths, r"^\s*(?:from|import)\s+(?:time(?:\.|\b)|logging(?:\.|\b))"),
        "random_imports_outside_rng": core_random_imports,
        "io_or_print_calls": _match_lines(
            core_paths,
            r"\bprint\s*\(|\blogging\.|\bopen\s*\(|\.open\s*\(|\.read_text\s*\(|\.write_text\s*\(|\.read_bytes\s*\(|\.write_bytes\s*\(",
        ),
    }

    engine_side_effect_signals = {
        "pygame_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+pygame(?:\.|\b)"),
        "time_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+time(?:\.|\b)"),
        "random_imports_non_test": _match_lines(engine_paths, r"^\s*(?:from|import)\s+random(?:\.|\b)"),
        "core_step_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\.step\s*\(",
        ),
        "core_step_private_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\._[A-Za-z]\w*\s*\(",
        ),
        "core_step_state_field_assignments": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/step"),
            r"\bstate\.[A-Za-z]\w*\s*=",
        ),
        "core_rules_private_state_method_calls": _match_lines(
            _py_files(REPO_ROOT / "src/tet4d/engine/core/rules"),
            r"\._[A-Za-z]\w*\s*\(",
        ),
        "file_io_calls_non_test": _match_lines(
            engine_paths,
            r"\bopen\s*\(|\.open\s*\(|\.read_text\s*\(|\.write_text\s*\(|\.read_bytes\s*\(|\.write_bytes\s*\(",
        ),
    }

    metrics = {
        "arch_stage": 354,
        "paths": {
            "engine": "src/tet4d/engine",
            "engine_core": "src/tet4d/engine/core",
            "replay": "src/tet4d/replay",
            "ai": "src/tet4d/ai",
            "ui": "src/tet4d/ui",
        },
        "deep_imports": {
            "engine_core_to_engine_non_core_imports": {
                "count": len(core_non_core_engine),
                "samples": core_non_core_engine[:20],
            },
            "ui_to_engine_non_api": {"count": len(ui_deep_engine), "samples": ui_deep_engine[:20]},
            "replay_to_engine_non_api": {"count": len(replay_deep_engine), "samples": replay_deep_engine[:20]},
            "ai_to_engine_non_api": {"count": len(ai_deep_engine), "samples": ai_deep_engine[:20]},
            "tools_stability_to_engine_non_api": {
                "count": len(tools_stability_deep_engine),
                "samples": tools_stability_deep_engine[:20],
            },
            "tools_benchmarks_to_engine_non_api": {
                "count": len(tools_bench_deep_engine),
                "samples": tools_bench_deep_engine[:20],
            },
            "external_callers_to_engine_playbot": {
                "count": len(legacy_engine_playbot_external),
                "samples": legacy_engine_playbot_external[:20],
            },
        },
        "engine_core_purity": {
            "violation_count": sum(len(v) for v in core_purity_hits.values()),
            "checks": {k: {"count": len(v), "samples": v[:20]} for k, v in core_purity_hits.items()},
        },
        "migration_debt_signals": {
            k: {"count": len(v), "samples": v[:20]}
            for k, v in engine_side_effect_signals.items()
        },
    }
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
