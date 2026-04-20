from __future__ import annotations

from pathlib import Path

import tools.governance.generate_maintenance_docs as maint_doc


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _match_rows(
    matches: tuple[maint_doc._LikelyTestMatch, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple((match.path, match.tier) for match in matches)


def test_public_symbol_skim_extracts_public_top_level_symbols(
    tmp_path: Path, monkeypatch
) -> None:
    module_path = tmp_path / "src" / "tet4d" / "sample.py"
    _write_text(
        module_path,
        """def public_route(alpha, beta=1, *, strict=False):
    def nested_helper():
        return None
    return alpha, beta, strict


def _private_route():
    return None


async def async_route(name, *, enabled=True):
    return name, enabled


class Router:
    def __init__(self, board, *, strict=False):
        self.board = board


class _PrivateRouter:
    pass
""",
    )
    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", tmp_path)

    symbols, truncated = maint_doc._public_symbol_skim(
        "src/tet4d/sample.py",
        max_symbols=12,
    )

    assert truncated is False
    assert symbols == (
        "public_route(alpha, beta=..., *, strict=...)",
        "async async_route(name, *, enabled=...)",
        "Router(board, *, strict=...)",
    )


def test_public_symbol_skim_truncates_long_signatures(
    tmp_path: Path, monkeypatch
) -> None:
    module_path = tmp_path / "src" / "tet4d" / "long_form.py"
    _write_text(
        module_path,
        """def verbose_route(alpha, beta, gamma, delta, epsilon, zeta, eta, theta, *, strict=False, retries=3, timeout=10):
    return alpha
""",
    )
    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", tmp_path)

    symbols, truncated = maint_doc._public_symbol_skim(
        "src/tet4d/long_form.py",
        max_symbols=12,
    )

    assert truncated is False
    assert len(symbols) == 1
    assert symbols[0].startswith("verbose_route(")
    assert "..." in symbols[0]
    assert len(symbols[0]) < 80


def test_symbol_and_test_config_validation_degrades_safely() -> None:
    symbol_cfg = maint_doc._symbol_index_config(
        {
            "symbol_index": {
                "source_roots": "src/tet4d",
                "max_symbols_per_file": "12",
            }
        }
    )
    test_cfg = maint_doc._likely_test_files_config(
        {
            "likely_test_files": {
                "source_roots": "cli",
                "test_roots": "tests",
                "max_matches_per_file": 0,
            }
        }
    )
    clamped_cfg = maint_doc._likely_test_files_config(
        {
            "likely_test_files": {
                "source_roots": ["src/tet4d"],
                "test_roots": ["tests"],
                "max_matches_per_file": 999,
            }
        }
    )

    assert symbol_cfg.source_roots == maint_doc.DEFAULT_SYMBOL_SOURCE_ROOTS
    assert symbol_cfg.max_symbols_per_file == maint_doc.DEFAULT_SYMBOLS_PER_FILE
    assert test_cfg.source_roots == maint_doc.DEFAULT_TEST_SOURCE_ROOTS
    assert test_cfg.test_roots == maint_doc.DEFAULT_TEST_ROOTS
    assert test_cfg.max_matches_per_file == maint_doc.DEFAULT_TEST_MATCHES_PER_FILE
    assert clamped_cfg.max_matches_per_file == maint_doc.MAX_TEST_MATCHES_PER_FILE


def test_likely_test_files_prefers_exact_then_prefix_then_fallback() -> None:
    tests = (
        "tests/unit/engine/test_front.py",
        "tests/unit/topology_lab/test_topology_lab_interaction_audit.py",
        "tests/unit/engine/test_front_launcher_routes.py",
        "tests/unit/render/test_projected_piece_occlusion.py",
    )

    assert _match_rows(
        maint_doc._likely_test_files_for_source(
            "cli/front.py",
            tests,
            max_matches=4,
        )
    ) == (("tests/unit/engine/test_front.py", "exact"),)
    assert _match_rows(
        maint_doc._likely_test_files_for_source(
            "cli/front_launcher.py",
            tests,
            max_matches=4,
        )
    ) == (("tests/unit/engine/test_front_launcher_routes.py", "prefix"),)
    assert _match_rows(
        maint_doc._likely_test_files_for_source(
            "src/tet4d/ui/pygame/topology_lab/interaction_audit.py",
            tests,
            max_matches=4,
        )
    ) == (
        ("tests/unit/topology_lab/test_topology_lab_interaction_audit.py", "fallback"),
    )


def test_generic_exact_match_requires_support_signal(
    tmp_path: Path, monkeypatch
) -> None:
    source_path = tmp_path / "src" / "tet4d" / "engine" / "gameplay" / "topology.py"
    test_path = tmp_path / "tests" / "unit" / "engine" / "test_topology.py"
    _write_text(source_path, "def normalize_topology_mode(value):\n    return value\n")
    _write_text(
        test_path,
        "from tet4d.engine.gameplay.topology import normalize_topology_mode\n",
    )
    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", tmp_path)

    assert _match_rows(
        maint_doc._likely_test_files_for_source(
            "src/tet4d/engine/gameplay/topology.py",
            ("tests/unit/engine/test_topology.py",),
            max_matches=4,
        )
    ) == (("tests/unit/engine/test_topology.py", "exact"),)


def test_likely_test_files_suppresses_thin_cli_render_false_positive() -> None:
    assert (
        maint_doc._likely_test_files_for_source(
            "cli/front4d.py",
            ("tests/unit/engine/test_front4d_render.py",),
            max_matches=4,
        )
        == ()
    )


def test_likely_test_files_suppresses_generic_exact_without_support_signal() -> None:
    assert (
        maint_doc._likely_test_files_for_source(
            "src/tet4d/ui/pygame/locked_cell_explosion/topology.py",
            ("tests/unit/engine/test_topology.py",),
            max_matches=4,
        )
        == ()
    )


def test_likely_test_files_suppresses_weak_scoring_bonus_fallback() -> None:
    assert (
        maint_doc._likely_test_files_for_source(
            "src/tet4d/engine/core/rules/scoring.py",
            ("tests/unit/engine/test_scoring_bonus.py",),
            max_matches=4,
        )
        == ()
    )


def test_likely_test_files_controls_generic_stem_noise() -> None:
    tests = (
        "tests/unit/render/test_projection_render.py",
        "tests/unit/engine/test_menu_layout.py",
        "tests/unit/engine/test_state_machine.py",
        "tests/unit/render/test_render_pipeline.py",
    )

    assert maint_doc._likely_test_files_for_source(
        "src/tet4d/ui/pygame/render/render.py",
        tests,
        max_matches=4,
    ) == ()
    assert maint_doc._likely_test_files_for_source(
        "src/tet4d/engine/runtime/menu.py",
        tests,
        max_matches=4,
    ) == ()
    assert maint_doc._likely_test_files_for_source(
        "src/tet4d/engine/runtime/state.py",
        tests,
        max_matches=4,
    ) == ()
