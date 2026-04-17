from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

if __package__:
    from . import check_drift_protection as drift_guard
    from ._common import load_maintenance_docs
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    import check_drift_protection as drift_guard
    from _common import load_maintenance_docs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENT_STATE_PATH = PROJECT_ROOT / "CURRENT_STATE.md"
PROJECT_STRUCTURE_PATH = PROJECT_ROOT / "docs" / "PROJECT_STRUCTURE.md"


def _load_maintenance_doc_contract() -> dict[str, object]:
    payload = load_maintenance_docs(PROJECT_ROOT)
    if isinstance(payload, dict):
        return payload
    raise SystemExit("missing required file: config/project/policy_pack.json")


def _rows_from_entries(entries: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(entries, list):
        return ()
    rows: list[tuple[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        description = entry.get("description")
        if isinstance(path, str) and isinstance(description, str):
            rows.append((path, description))
    return tuple(rows)


def _owner_rows(
    contract: dict[str, object], section: str, heading: str
) -> tuple[tuple[str, str], ...]:
    owners = contract.get(section)
    if not isinstance(owners, dict):
        return ()
    return _rows_from_entries(owners.get(heading))


def _verification_contract(
    contract: dict[str, object],
) -> tuple[str, str, tuple[str, ...]]:
    verification = contract.get("verification")
    if not isinstance(verification, dict):
        return (
            "CODEX_MODE=1 ./scripts/verify.sh",
            "./scripts/ci_check.sh",
            (),
        )
    local_gate = verification.get("local_gate")
    if not isinstance(local_gate, str) or not local_gate.strip():
        local_gate = "CODEX_MODE=1 ./scripts/verify.sh"
    ci_entrypoint = verification.get("ci_entrypoint")
    if not isinstance(ci_entrypoint, str) or not ci_entrypoint.strip():
        ci_entrypoint = "./scripts/ci_check.sh"
    enforcers = verification.get("enforcers")
    if not isinstance(enforcers, list):
        return local_gate, ci_entrypoint, ()
    return (
        local_gate,
        ci_entrypoint,
        tuple(path for path in enforcers if isinstance(path, str)),
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
        "Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.",
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
    maintenance_contract = _load_maintenance_doc_contract()
    local_gate, _, enforcers = _verification_contract(maintenance_contract)
    sections: dict[str, str] = {}
    sections["project_structure_entry_points"] = "\n".join(
        [
            "## Canonical Entry Points",
            "",
            _render_numbered_rows(
                _rows_from_entries(maintenance_contract.get("entry_points"))
            ),
        ]
    )

    owner_lines = ["## Canonical Runtime Owners", ""]
    for heading in ("Engine", "UI", "AI"):
        owner_lines.append(f"### {heading}")
        owner_lines.append("")
        owner_lines.append(
            _render_numbered_rows(
                _owner_rows(maintenance_contract, "runtime_owners", heading)
            )
        )
        owner_lines.append("")
    sections["project_structure_runtime_owners"] = "\n".join(owner_lines).rstrip()

    sections["project_structure_sources_of_truth"] = "\n".join(
        [
            "## Config And Docs Sources Of Truth",
            "",
            _render_numbered_rows(
                _rows_from_entries(maintenance_contract.get("sources_of_truth"))
            ),
        ]
    )

    sections["project_structure_verification_contract"] = "\n".join(
        [
            "## Verification Contract",
            "",
            "Run:",
            "",
            "```bash",
            local_gate,
            "```",
            "",
            "Authoritative enforcement is backed by:",
            "",
            *[f"{index}. `{path}`" for index, path in enumerate(enforcers, start=1)],
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
