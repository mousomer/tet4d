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


def _current_state_template() -> str:
    return """# CURRENT_STATE

Manual intro.

<!-- BEGIN GENERATED:current_state_architecture_snapshot -->
stale
<!-- END GENERATED:current_state_architecture_snapshot -->

Manual midpoint.

<!-- BEGIN GENERATED:current_state_metric_snapshot -->
stale
<!-- END GENERATED:current_state_metric_snapshot -->

<!-- BEGIN GENERATED:current_state_canonical_ownership -->
stale
<!-- END GENERATED:current_state_canonical_ownership -->

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
"""


def test_render_maintenance_docs_replaces_generated_sections(monkeypatch) -> None:
    scratch_root = _scratch_root()
    current_state = scratch_root / "CURRENT_STATE.md"
    project_structure = scratch_root / "docs" / "PROJECT_STRUCTURE.md"
    _write_text(current_state, _current_state_template())
    _write_text(project_structure, _project_structure_template())

    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(maint_doc, "CURRENT_STATE_PATH", current_state)
    monkeypatch.setattr(maint_doc, "PROJECT_STRUCTURE_PATH", project_structure)
    monkeypatch.setattr(maint_doc, "_arch_metrics_payload", _metrics_payload)
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

    assert "## Current Architecture Snapshot" in rendered_current
    assert "`tech_debt.score = 2.03` (`low`)" in rendered_current
    assert "## Live Drift Watch" in rendered_current
    assert "`src/tet4d/engine/tutorial/setup_apply.py`: `42` real LOC" in rendered_current
    assert "`cli/front.py: 681/720 real LOC (compatibility launcher wrapper)`" in rendered_current
    assert "Manual intro." in rendered_current
    assert "## Canonical Entry Points" in rendered_structure
    assert "`cli/front2d.py`: thin 2D shim" in rendered_structure
    assert "## Verification Contract" in rendered_structure
    assert "Manual midpoint." in rendered_structure


def test_check_generated_docs_detects_stale_output(monkeypatch) -> None:
    scratch_root = _scratch_root()
    current_state = scratch_root / "CURRENT_STATE.md"
    project_structure = scratch_root / "docs" / "PROJECT_STRUCTURE.md"
    _write_text(current_state, _current_state_template())
    _write_text(project_structure, _project_structure_template())

    monkeypatch.setattr(maint_doc, "PROJECT_ROOT", scratch_root)
    monkeypatch.setattr(maint_doc, "CURRENT_STATE_PATH", current_state)
    monkeypatch.setattr(maint_doc, "PROJECT_STRUCTURE_PATH", project_structure)
    monkeypatch.setattr(maint_doc, "_arch_metrics_payload", _metrics_payload)
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

    assert maint_doc.check_generated_docs() == 0
