from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import tools.governance.generate_maintenance_docs as maint_doc


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scratch_root() -> Path:
    root = Path('.tmp_test_generate_maintenance_docs') / uuid4().hex
    root.mkdir(parents=True, exist_ok=False)
    return root


def _metrics_payload() -> dict[str, object]:
    return {
        "arch_stage": 900,
        "deep_imports": {
            "engine_to_ui_non_api": {"count": 0},
            "engine_to_ai_non_api": {"count": 0},
            "ui_to_engine_non_api": {"count": 118},
            "ai_to_engine_non_api": {"count": 26},
        },
        "engine_core_purity": {"violation_count": 0},
        "migration_debt_signals": {"pygame_imports_non_test": {"count": 0}},
        "tech_debt": {
            "score": 2.03,
            "status": "low",
            "weighted_component_contributions": {
                "code_balance": 0.72,
                "delivery_size_pressure": 1.31,
            },
        },
    }


def _maintenance_contract() -> dict[str, object]:
    return {
        "entry_points": [
            {"path": "cli/front.py", "description": "unified launcher"},
            {"path": "cli/front2d.py", "description": "thin 2D shim"},
        ],
        "runtime_owners": {
            "Engine": [
                {"path": "src/tet4d/engine/api.py", "description": "engine facade"}
            ],
            "UI": [
                {"path": "src/tet4d/ui/pygame/front2d_game.py", "description": "2D orchestration entry"}
            ],
            "AI": [
                {"path": "src/tet4d/ai/playbot/controller.py", "description": "playbot runtime controller"}
            ],
        },
        "sources_of_truth": [
            {
                "path": "config/project/policy_pack.json",
                "description": "single machine-readable governance authority",
            },
            {"path": "docs/WORKFLOW_CODEX.md", "description": "workflow explainer"},
        ],
        "verification": {
            "local_gate": "CODEX_MODE=1 ./scripts/verify.sh",
            "ci_entrypoint": "./scripts/ci_check.sh",
            "enforcers": [
                "scripts/check_editable_install.sh",
                "scripts/check_architecture_boundaries.sh",
            ],
        },
        "symbol_index": {
            "source_roots": ["src/tet4d", "cli"],
            "max_symbols_per_file": 4,
        },
        "likely_test_files": {
            "source_roots": ["src/tet4d", "cli"],
            "test_roots": ["tests"],
            "max_matches_per_file": 3,
        },
    }


def _current_state_template() -> str:
    return """# CURRENT_STATE

Manual intro.

Manual midpoint.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
stale
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_drift_watch -->
stale
<!-- END GENERATED:current_state_drift_watch -->

Manual tail.
"""


def _project_structure_template() -> str:
    return """# PROJECT_STRUCTURE

Manual intro.

<!-- BEGIN GENERATED:project_structure_entry_points -->
stale
<!-- END GENERATED:project_structure_entry_points -->

<!-- BEGIN GENERATED:project_structure_runtime_owners -->
stale
<!-- END GENERATED:project_structure_runtime_owners -->

<!-- BEGIN GENERATED:project_structure_sources_of_truth -->
stale
<!-- END GENERATED:project_structure_sources_of_truth -->

Manual midpoint.

<!-- BEGIN GENERATED:project_structure_verification_contract -->
stale
<!-- END GENERATED:project_structure_verification_contract -->

<!-- BEGIN GENERATED:project_structure_symbol_index -->
stale
<!-- END GENERATED:project_structure_symbol_index -->

<!-- BEGIN GENERATED:project_structure_likely_test_files -->
stale
<!-- END GENERATED:project_structure_likely_test_files -->
"""


def _seed_project_structure_index_inputs(root: Path) -> None:
    _write_text(
        root / "src" / "tet4d" / "engine" / "routing.py",
        """def route_event(board, piece, *, strict=False):
    return board, piece, strict


class Router:
    def __init__(self, board, *, strict=False):
        self.board = board
        self.strict = strict
""",
    )
    _write_text(
        root / "cli" / "front.py",
        """def main(argv=None):
    return argv
""",
    )
    _write_text(
        root / "tests" / "unit" / "engine" / "test_routing.py",
        "def test_routing_exact():\n    assert True\n",
    )
    _write_text(
        root / "tests" / "unit" / "engine" / "test_front_smoke.py",
        "def test_front_prefix():\n    assert True\n",
    )


def test_render_maintenance_docs_replaces_generated_sections(monkeypatch) -> None:
    scratch_root = _scratch_root()
    current_state = scratch_root / "CURRENT_STATE.md"
    project_structure = scratch_root / "docs" / "PROJECT_STRUCTURE.md"
    _write_text(current_state, _current_state_template())
    _write_text(project_structure, _project_structure_template())
    _seed_project_structure_index_inputs(scratch_root)

    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(maint_doc, "CURRENT_STATE_PATH", current_state)
    monkeypatch.setattr(maint_doc, "PROJECT_STRUCTURE_PATH", project_structure)
    monkeypatch.setattr(maint_doc, "_arch_metrics_payload", _metrics_payload)
    monkeypatch.setattr(maint_doc, "_load_maintenance_doc_contract", _maintenance_contract)
    monkeypatch.setattr(
        maint_doc.drift_guard,
        "_load_manifest",
        lambda: {
            "hotspot_scan": {"roots": ["src", "cli"], "top_n": 2},
            "thin_wrapper_budgets": [
                {"path": "cli/front.py", "max_real_loc": 720, "role": "compatibility launcher wrapper"}
            ],
            "tutorial_copy_contract": {
                "lessons_path": "config/tutorial/lessons.json",
                "overlay_path": "src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py",
                "forbidden_prefixes": ["Goal:", "Action:"],
                "required_overlay_tokens": ["Do this:", "Tip:", "USE:"],
            },
        },
    )
    monkeypatch.setattr(maint_doc.drift_guard, "_validate_hotspot_scan", lambda payload, issues: ("src", "cli"))
    monkeypatch.setattr(maint_doc.drift_guard, "collect_top_hotspots", lambda *, roots, top_n: [(42, "src/tet4d/engine/tutorial/setup_apply.py"), (17, "cli/front.py")])
    monkeypatch.setattr(maint_doc.drift_guard, "count_real_loc", lambda path: 681 if path.as_posix().endswith("cli/front.py") else 0)

    rendered_current = maint_doc.render_current_state_doc()
    rendered_structure = maint_doc.render_project_structure_doc()

    assert "`tech_debt.score = 2.03` (`low`)" in rendered_current
    assert "## Live Drift Watch" in rendered_current
    assert "`src/tet4d/engine/tutorial/setup_apply.py`: `42` real LOC" in rendered_current
    assert "`cli/front.py: 681/720 real LOC (compatibility launcher wrapper)`" in rendered_current
    assert "Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`." in rendered_current
    assert "Manual intro." in rendered_current
    assert "## Canonical Entry Points" in rendered_structure
    assert "`cli/front2d.py`: thin 2D shim" in rendered_structure
    assert "## Verification Contract" in rendered_structure
    assert "`config/project/policy_pack.json`: single machine-readable governance authority" in rendered_structure
    assert "## Public Symbol Skim" in rendered_structure
    assert "routing aid" in rendered_structure
    assert "`src/tet4d/engine/routing.py`: `route_event(board, piece, *, strict=...)`, `Router(board, *, strict=...)`" in rendered_structure
    assert "## Likely Test Files" in rendered_structure
    assert "heuristic links" in rendered_structure
    assert "They are routing hints only, using tiered exact, prefix, then controlled fallback matching." in rendered_structure
    assert "`src/tet4d/engine/routing.py`: `tests/unit/engine/test_routing.py` (exact)" in rendered_structure
    assert "`cli/front.py`: `tests/unit/engine/test_front_smoke.py` (prefix)" in rendered_structure
    assert "coverage" not in rendered_structure
    assert "Manual midpoint." in rendered_structure


def test_check_generated_docs_detects_stale_output(monkeypatch) -> None:
    scratch_root = _scratch_root()
    current_state = scratch_root / "CURRENT_STATE.md"
    project_structure = scratch_root / "docs" / "PROJECT_STRUCTURE.md"
    _write_text(current_state, _current_state_template())
    _write_text(project_structure, _project_structure_template())
    _seed_project_structure_index_inputs(scratch_root)

    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(maint_doc, "CURRENT_STATE_PATH", current_state)
    monkeypatch.setattr(maint_doc, "PROJECT_STRUCTURE_PATH", project_structure)
    monkeypatch.setattr(maint_doc, "_arch_metrics_payload", _metrics_payload)
    monkeypatch.setattr(maint_doc, "_load_maintenance_doc_contract", _maintenance_contract)
    monkeypatch.setattr(
        maint_doc.drift_guard,
        "_load_manifest",
        lambda: {
            "hotspot_scan": {"roots": ["src", "cli"], "top_n": 2},
            "thin_wrapper_budgets": [
                {"path": "cli/front.py", "max_real_loc": 720, "role": "compatibility launcher wrapper"}
            ],
            "tutorial_copy_contract": {
                "lessons_path": "config/tutorial/lessons.json",
                "overlay_path": "src/tet4d/ui/pygame/runtime_ui/tutorial_overlay.py",
                "forbidden_prefixes": ["Goal:", "Action:"],
                "required_overlay_tokens": ["Do this:", "Tip:", "USE:"],
            },
        },
    )
    monkeypatch.setattr(maint_doc.drift_guard, "_validate_hotspot_scan", lambda payload, issues: ("src", "cli"))
    monkeypatch.setattr(maint_doc.drift_guard, "collect_top_hotspots", lambda *, roots, top_n: [(42, "src/tet4d/engine/tutorial/setup_apply.py"), (17, "cli/front.py")])
    monkeypatch.setattr(maint_doc.drift_guard, "count_real_loc", lambda path: 681 if path.as_posix().endswith("cli/front.py") else 0)

    assert maint_doc.check_generated_docs() == 1

    _write_text(current_state, maint_doc.render_current_state_doc())
    _write_text(project_structure, maint_doc.render_project_structure_doc())

    rendered_structure = project_structure.read_text(encoding="utf-8")
    assert "<!-- BEGIN GENERATED:project_structure_symbol_index -->" in rendered_structure
    assert "<!-- BEGIN GENERATED:project_structure_likely_test_files -->" in rendered_structure
    assert "## Public Symbol Skim" in rendered_structure
    assert "## Likely Test Files" in rendered_structure
    assert maint_doc.check_generated_docs() == 0
