from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

if __package__:
    from . import check_drift_protection as drift_guard
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    import check_drift_protection as drift_guard

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENT_STATE_PATH = PROJECT_ROOT / "CURRENT_STATE.md"
PROJECT_STRUCTURE_PATH = PROJECT_ROOT / "docs" / "PROJECT_STRUCTURE.md"

ENTRY_POINTS: tuple[tuple[str, str], ...] = (
    ("cli/front.py", "unified launcher"),
    ("cli/front2d.py", "thin 2D shim"),
    ("cli/front3d.py", "thin 3D shim"),
    ("cli/front4d.py", "thin 4D shim"),
)

CANONICAL_OWNERS: dict[str, tuple[tuple[str, str], ...]] = {
    "Engine": (
        (
            "src/tet4d/engine/api.py",
            "small compatibility facade used mainly by replay and explicit compatibility tests",
        ),
        ("src/tet4d/engine/gameplay/api.py", "gameplay convenience exports"),
        ("src/tet4d/engine/runtime/api.py", "runtime/help/menu convenience exports"),
        ("src/tet4d/engine/tutorial/api.py", "tutorial convenience exports"),
        (
            "src/tet4d/engine/core/piece_transform.py",
            "canonical piece-local transform math",
        ),
        (
            "src/tet4d/engine/core/rotation_kicks.py",
            "canonical kick candidate generation and shared resolution",
        ),
        (
            "src/tet4d/engine/core/rules/lifecycle.py",
            "shared lock/spawn/drop lifecycle orchestration",
        ),
        (
            "src/tet4d/engine/topology_explorer/",
            "explorer-only general gluing kernel, validation, mapping, and movement graph helpers",
        ),
        ("src/tet4d/engine/gameplay/game2d.py", "2D gameplay state/rules"),
        ("src/tet4d/engine/gameplay/game_nd.py", "3D/4D gameplay state/rules"),
        (
            "src/tet4d/engine/gameplay/lock_flow.py",
            "shared lock-and-analysis orchestration",
        ),
        ("src/tet4d/engine/runtime/menu_config.py", "menu/runtime config loading"),
        (
            "src/tet4d/engine/runtime/keybinding_store.py",
            "runtime-owned keybinding profile/path/json storage",
        ),
        (
            "src/tet4d/engine/runtime/menu_settings_state.py",
            "stable persisted-settings facade over `runtime/menu_settings/`",
        ),
        (
            "src/tet4d/engine/runtime/menu_structure_schema.py",
            "stable menu-structure parsing facade over `runtime/menu_structure/`",
        ),
        (
            "src/tet4d/engine/runtime/score_analyzer.py",
            "stable score-analysis facade over `runtime/score_analysis/`",
        ),
        ("src/tet4d/engine/tutorial/content.py", "tutorial content loader"),
        ("src/tet4d/engine/tutorial/runtime.py", "tutorial runtime session logic"),
    ),
    "UI": (
        ("src/tet4d/ui/pygame/front2d_game.py", "2D orchestration entry"),
        ("src/tet4d/ui/pygame/front2d_setup.py", "2D setup/menu owner"),
        ("src/tet4d/ui/pygame/front2d_loop.py", "2D runtime orchestration entrypoint"),
        ("src/tet4d/ui/pygame/front2d_session.py", "2D session/state owner"),
        ("src/tet4d/ui/pygame/front2d_frame.py", "2D per-frame/update owner"),
        ("src/tet4d/ui/pygame/front2d_results.py", "2D results/leaderboard owner"),
        (
            "src/tet4d/ui/pygame/frontend_nd_setup.py",
            "shared ND setup/menu/config owner",
        ),
        (
            "src/tet4d/ui/pygame/frontend_nd_state.py",
            "shared ND state-construction owner",
        ),
        (
            "src/tet4d/ui/pygame/frontend_nd_input.py",
            "shared ND gameplay/input routing owner",
        ),
        ("src/tet4d/ui/pygame/front3d_game.py", "3D frontend"),
        ("src/tet4d/ui/pygame/front4d_game.py", "4D frontend"),
        ("src/tet4d/ui/pygame/front3d_render.py", "3D render adapter"),
        ("src/tet4d/ui/pygame/front4d_render.py", "4D render adapter"),
        (
            "src/tet4d/ui/pygame/runtime_ui",
            "bootstrap, pause/help, tutorial overlay, shared loop helpers",
        ),
        (
            "src/tet4d/ui/pygame/launch",
            "launcher, settings, bot, leaderboard flows, including `settings_hub_model.py`, `settings_hub_actions.py`, and `launcher_settings.py`",
        ),
        (
            "src/tet4d/ui/pygame/menu",
            "shared menu/keybinding adapters, including `setup_menu_runner.py`",
        ),
        ("src/tet4d/ui/pygame/render", "render/layout/helper adapters"),
    ),
    "AI": (
        ("src/tet4d/ai/playbot/controller.py", "playbot runtime controller"),
        ("src/tet4d/ai/playbot/planner_2d.py", "2D planning"),
        ("src/tet4d/ai/playbot/planner_nd.py", "ND planning entry"),
        ("src/tet4d/ai/playbot/planner_nd_core.py", "shared ND candidate logic"),
        ("src/tet4d/ai/playbot/planner_nd_search.py", "ND search/budget logic"),
        ("src/tet4d/ai/playbot/dry_run.py", "stability/dry-run harness"),
    ),
}

CANONICAL_OWNERS_FOR_CURRENT_STATE: dict[str, tuple[str, ...]] = {
    "Engine": (
        "src/tet4d/engine/core/piece_transform.py",
        "src/tet4d/engine/core/rotation_kicks.py",
        "src/tet4d/engine/core/rules/lifecycle.py",
        "src/tet4d/engine/topology_explorer/*",
        "src/tet4d/engine/gameplay/*",
        "src/tet4d/engine/gameplay/api.py",
        "src/tet4d/engine/runtime/*",
        "src/tet4d/engine/runtime/api.py",
        "src/tet4d/engine/tutorial/*",
        "src/tet4d/engine/tutorial/api.py",
        "src/tet4d/engine/api.py (small compatibility facade for replay/tests/tutorial payload exports)",
    ),
    "UI": (
        "src/tet4d/ui/pygame/front2d_game.py",
        "src/tet4d/ui/pygame/front2d_setup.py",
        "src/tet4d/ui/pygame/front2d_loop.py",
        "src/tet4d/ui/pygame/front2d_session.py",
        "src/tet4d/ui/pygame/front2d_frame.py",
        "src/tet4d/ui/pygame/front2d_results.py",
        "src/tet4d/ui/pygame/frontend_nd_setup.py",
        "src/tet4d/ui/pygame/frontend_nd_state.py",
        "src/tet4d/ui/pygame/frontend_nd_input.py",
        "src/tet4d/ui/pygame/front3d_game.py",
        "src/tet4d/ui/pygame/front4d_game.py",
        "src/tet4d/ui/pygame/front3d_render.py",
        "src/tet4d/ui/pygame/front4d_render.py",
        "src/tet4d/ui/pygame/runtime_ui/*",
        "src/tet4d/ui/pygame/menu/*",
        "src/tet4d/ui/pygame/launch/* (with settings_hub_model.py owning settings model/layout, settings_hub_actions.py owning settings mutations/text-entry, and launcher_settings.py owning orchestration/view)",
        "src/tet4d/ui/pygame/render/*",
    ),
    "AI": ("src/tet4d/ai/playbot/*",),
}

SOURCE_OF_TRUTH_FILES: tuple[tuple[str, str], ...] = (
    ("config/menu/structure.json", "launcher/pause/settings/help/menu graph and copy"),
    ("config/menu/defaults.json", "default persisted settings payload"),
    ("config/tutorial/lessons.json", "tutorial packs and board profiles"),
    ("config/gameplay/tuning.json", "scoring/kick/tuning defaults"),
    ("docs/CONFIGURATION_REFERENCE.md", "generated full config inventory"),
    ("docs/USER_SETTINGS_REFERENCE.md", "generated user-facing settings summary"),
    ("docs/ARCHITECTURE_CONTRACT.md", "dependency contract"),
    ("CURRENT_STATE.md", "restart handoff"),
    ("docs/BACKLOG.md", "active backlog and current change footprint"),
)

VERIFICATION_ENFORCERS: tuple[str, ...] = (
    "scripts/check_editable_install.sh",
    "scripts/check_architecture_boundaries.sh",
    "scripts/check_engine_core_purity.sh",
    "scripts/arch_metrics.py",
    "tools/governance/architecture_metric_budget.py",
)


def _arch_metrics_payload() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "scripts/arch_metrics.py"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def _replace_generated_section(text: str, marker_id: str, body: str) -> str:
    begin = f"<!-- BEGIN GENERATED:{marker_id} -->"
    end = f"<!-- END GENERATED:{marker_id} -->"
    start_idx = text.find(begin)
    end_idx = text.find(end)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError(f"missing generated marker block: {marker_id}")
    before = text[: start_idx + len(begin)]
    after = text[end_idx:]
    rendered = "\n" + body.rstrip() + "\n"
    return before + rendered + after


def _render_numbered_rows(rows: Iterable[tuple[str, str]]) -> str:
    return "\n".join(
        f"{index}. `{path}`: {description}"
        for index, (path, description) in enumerate(rows, start=1)
    )


def _render_bullet_rows(rows: Iterable[str]) -> str:
    return "\n".join(f"- `{row}`" for row in rows)


def _top_pressure_lines(metrics: dict[str, object]) -> list[str]:
    weighted = metrics["tech_debt"]["weighted_component_contributions"]
    if not isinstance(weighted, dict):
        return []
    ranked = sorted(
        (
            (name, float(value))
            for name, value in weighted.items()
            if float(value) > 0.0
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        f"{index}. `{name} = {value:.2f}`"
        for index, (name, value) in enumerate(ranked[:2], start=1)
    ]


def render_current_state_sections(
    metrics: dict[str, object] | None = None,
) -> dict[str, str]:
    payload = metrics if metrics is not None else _arch_metrics_payload()
    drift_manifest = drift_guard._load_manifest()
    deep = payload["deep_imports"]
    purity = payload["engine_core_purity"]
    debt = payload["tech_debt"]
    sections: dict[str, str] = {}

    sections["current_state_architecture_snapshot"] = "\n".join(
        [
            "## Current Architecture Snapshot",
            "",
            f"- `arch_stage`: `{payload['arch_stage']}`",
            "- Canonical local gate: `CODEX_MODE=1 ./scripts/verify.sh`",
            "- CI wrapper: `./scripts/ci_check.sh`",
            "- Full local gate runs are serialized by `scripts/verify.sh`, use an isolated per-run state root via `TET4D_STATE_ROOT` when no explicit override is provided, and include the CI sanitation/policy checks (`scripts/check_policy_compliance.sh`, `scripts/check_policy_compliance_repo.sh`, `scripts/check_git_sanitation_repo.sh`) so local verification matches GitHub policy enforcement.",
            "- Dependency direction:",
            "  - `ui`, `ai`, `replay`, and `tools` may import engine modules directly",
            "  - `engine` must not import `ui`, `ai`, `replay`, or `tools`",
            "  - `engine/core` remains strict-pure",
        ]
    )

    metric_lines = [
        "## Current Metric Snapshot",
        "",
        "From `python scripts/arch_metrics.py`:",
        "",
        f"- `deep_imports.engine_to_ui_non_api.count = {deep['engine_to_ui_non_api']['count']}`",
        f"- `deep_imports.engine_to_ai_non_api.count = {deep['engine_to_ai_non_api']['count']}`",
        f"- `deep_imports.ui_to_engine_non_api.count = {deep['ui_to_engine_non_api']['count']}` (allowed under current rule)",
        f"- `deep_imports.ai_to_engine_non_api.count = {deep['ai_to_engine_non_api']['count']}` (allowed under current rule)",
        f"- `engine_core_purity.violation_count = {purity['violation_count']}`",
        f"- `migration_debt_signals.pygame_imports_non_test.count = {payload['migration_debt_signals']['pygame_imports_non_test']['count']}`",
        f"- `tech_debt.score = {float(debt['score']):.2f}` (`{debt['status']}`)",
        "",
        "Dominant remaining pressure:",
        "",
    ]
    metric_lines.extend(_top_pressure_lines(payload))
    sections["current_state_metric_snapshot"] = "\n".join(metric_lines)

    ownership_lines = ["## Canonical Ownership After This Batch", ""]
    for heading in ("Engine", "UI", "AI"):
        ownership_lines.append(f"### {heading}")
        ownership_lines.append("")
        ownership_lines.append(
            _render_bullet_rows(CANONICAL_OWNERS_FOR_CURRENT_STATE[heading])
        )
        ownership_lines.append("")
    sections["current_state_canonical_ownership"] = "\n".join(ownership_lines).rstrip()
    sections["current_state_drift_watch"] = _render_current_state_drift_watch(
        drift_manifest=drift_manifest
    )
    return sections


def _render_current_state_drift_watch(*, drift_manifest: dict[str, object]) -> str:
    hotspot_scan = drift_manifest.get("hotspot_scan", {})
    if isinstance(hotspot_scan, dict):
        top_n = int(hotspot_scan.get("top_n", 8))
        roots = drift_guard._validate_hotspot_scan(hotspot_scan, [])
    else:
        top_n = 8
        roots = ("src", "cli", "tests", "tools", "scripts")
    hotspots = drift_guard.collect_top_hotspots(roots=roots, top_n=top_n)

    budget_rows: list[str] = []
    budget_entries = drift_manifest.get("thin_wrapper_budgets", [])
    if isinstance(budget_entries, list):
        for entry in budget_entries:
            if not isinstance(entry, dict):
                continue
            raw_path = entry.get("path")
            max_real_loc = entry.get("max_real_loc")
            role = entry.get("role")
            if not isinstance(raw_path, str) or not isinstance(max_real_loc, int):
                continue
            if not isinstance(role, str):
                role = "wrapper budget"
            current = drift_guard.count_real_loc(PROJECT_ROOT / raw_path)
            budget_rows.append(
                f"{raw_path}: {current}/{max_real_loc} real LOC ({role})"
            )

    lines = [
        "## Live Drift Watch",
        "",
        "Generated from `tools/governance/check_drift_protection.py` and `config/project/policy/manifests/drift_protection.json`.",
        "",
        f"Top {top_n} live Python hotspots by real LOC:",
        "",
    ]
    lines.extend(
        f"{index}. `{path}`: `{loc}` real LOC"
        for index, (loc, path) in enumerate(hotspots, start=1)
    )
    lines.extend(
        [
            "",
            "Thin-wrapper budgets:",
            "",
        ]
    )
    lines.extend(f"{index}. `{row}`" for index, row in enumerate(budget_rows, start=1))
    lines.extend(
        [
            "",
            "Tutorial wording drift guard:",
            "",
            "1. Lesson copy must not start with `Goal:` or `Action:`.",
            "2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.",
        ]
    )
    return "\n".join(lines)


def render_project_structure_sections() -> dict[str, str]:
    sections: dict[str, str] = {}
    sections["project_structure_entry_points"] = "\n".join(
        ["## Canonical Entry Points", "", _render_numbered_rows(ENTRY_POINTS)]
    )

    owner_lines = ["## Canonical Runtime Owners", ""]
    for heading in ("Engine", "UI", "AI"):
        owner_lines.append(f"### {heading}")
        owner_lines.append("")
        owner_lines.append(_render_numbered_rows(CANONICAL_OWNERS[heading]))
        owner_lines.append("")
    sections["project_structure_runtime_owners"] = "\n".join(owner_lines).rstrip()

    sections["project_structure_sources_of_truth"] = "\n".join(
        [
            "## Config And Docs Sources Of Truth",
            "",
            _render_numbered_rows(SOURCE_OF_TRUTH_FILES),
        ]
    )

    sections["project_structure_verification_contract"] = "\n".join(
        [
            "## Verification Contract",
            "",
            "Run:",
            "",
            "```bash",
            "CODEX_MODE=1 ./scripts/verify.sh",
            "```",
            "",
            "Authoritative enforcement is backed by:",
            "",
            *[
                f"{index}. `{path}`"
                for index, path in enumerate(VERIFICATION_ENFORCERS, start=1)
            ],
        ]
    )
    return sections


def render_current_state_doc() -> str:
    text = CURRENT_STATE_PATH.read_text(encoding="utf-8")
    for marker_id, body in render_current_state_sections().items():
        text = _replace_generated_section(text, marker_id, body)
    return text.rstrip() + "\n"


def render_project_structure_doc() -> str:
    text = PROJECT_STRUCTURE_PATH.read_text(encoding="utf-8")
    for marker_id, body in render_project_structure_sections().items():
        text = _replace_generated_section(text, marker_id, body)
    return text.rstrip() + "\n"


def _check_doc(path: Path, expected: str) -> int:
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        print(
            f"Generated maintenance documentation is out of date: {rel}. Run tools/governance/generate_maintenance_docs.py.",
            file=sys.stderr,
        )
        return 1
    return 0


def check_generated_docs() -> int:
    failures = 0
    failures |= _check_doc(CURRENT_STATE_PATH, render_current_state_doc())
    failures |= _check_doc(PROJECT_STRUCTURE_PATH, render_project_structure_doc())
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated maintenance docs are stale",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check_generated_docs()
    CURRENT_STATE_PATH.write_text(render_current_state_doc(), encoding="utf-8")
    PROJECT_STRUCTURE_PATH.write_text(render_project_structure_doc(), encoding="utf-8")
    print(f"Wrote {CURRENT_STATE_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote {PROJECT_STRUCTURE_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
