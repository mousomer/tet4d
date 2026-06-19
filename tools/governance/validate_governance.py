from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

POLICY_PACK_PATH = ROOT / "config/project/policy_pack.json"


@dataclass(frozen=True)
class GovernanceCheck:
    name: str
    runner: Callable[[], int]


def _append_missing_keys(
    payload: object, label: str, required_keys: tuple[str, ...], issues: list[str]
) -> None:
    if not isinstance(payload, dict):
        issues.append(f"{label} must be an object")
        return
    for key in required_keys:
        if key not in payload:
            issues.append(f"{label} missing required key: {key}")


def _validate_unified_manifest_shape() -> list[str]:
    from tools.governance._common import load_json_object

    issues: list[str] = []
    policy_pack = load_json_object(POLICY_PACK_PATH, "config/project/policy_pack.json")

    required_pack_keys = (
        "authority_model",
        "governance",
        "code_rules",
        "maintenance_contract",
        "maintenance_docs",
        "deprecated_authorities",
    )
    for key in required_pack_keys:
        if key not in policy_pack:
            issues.append(f"policy_pack.json missing required key: {key}")

    _append_missing_keys(
        policy_pack.get("authority_model", {}),
        "policy_pack.json authority_model",
        (
            "machine_authority",
            "dispatch_file",
            "workflow_doc",
            "handoff_doc",
            "product_requirements_root",
        ),
        issues,
    )
    _append_missing_keys(
        policy_pack.get("governance", {}),
        "policy_pack.json governance",
        (
            "verification_command",
            "ci_entrypoint",
            "policy_index_contract",
            "menu_simplification_manifest_rule",
            "menu_structure_single_source",
            "contributor_directives",
            "risk_gates",
            "architecture",
            "tech_debt_budget",
            "drift_protection",
            "contracts",
        ),
        issues,
    )
    _append_missing_keys(
        policy_pack.get("code_rules", {}),
        "policy_pack.json code_rules",
        (
            "sanitation",
            "magic_numbers",
            "config_backed_runtime_constants",
            "wheel_reuse",
            "dead_code",
            "loc_guidance",
        ),
        issues,
    )
    _append_missing_keys(
        policy_pack.get("maintenance_docs", {}),
        "policy_pack.json maintenance_docs",
        (
            "entry_points",
            "runtime_owners",
            "sources_of_truth",
            "verification",
        ),
        issues,
    )
    _append_missing_keys(
        policy_pack.get("deprecated_authorities", {}),
        "policy_pack.json deprecated_authorities",
        ("blocked_paths", "reference_checks"),
        issues,
    )

    return issues


def _checks() -> tuple[GovernanceCheck, ...]:
    from tools.governance import check_dedup_dead_code_rules
    from tools.governance import check_drift_protection
    from tools.governance import check_loc_guidance
    from tools.governance import lint_menu_graph
    from tools.governance import check_policy_runtime_rules
    from tools.governance import check_risk_gates
    from tools.governance import check_wheel_reuse_rules
    from tools.governance import validate_authority_transfer
    from tools.governance import validate_config_authority
    from tools.governance import validate_drift_protection
    from tools.governance import validate_godot_semantic_boundary
    from tools.governance import validate_native_cpp_tooling
    from tools.governance import validate_project_contracts
    from tools.governance import validate_technical_debt
    from tools.governance import validate_utility_reuse
    from tools.governance import validate_workspace_bundle

    return (
        GovernanceCheck("contracts", validate_project_contracts.main),
        GovernanceCheck("workspace_bundle", validate_workspace_bundle.main),
        GovernanceCheck("technical_debt", validate_technical_debt.main),
        GovernanceCheck("authority_transfer", validate_authority_transfer.main),
        GovernanceCheck("project_drift_protection", validate_drift_protection.main),
        GovernanceCheck("config_authority", validate_config_authority.main),
        GovernanceCheck(
            "godot_semantic_boundary", validate_godot_semantic_boundary.main
        ),
        GovernanceCheck("native_cpp_tooling", validate_native_cpp_tooling.main),
        GovernanceCheck("menu_graph", lint_menu_graph.main),
        GovernanceCheck("risk_gates", check_risk_gates.main),
        GovernanceCheck("policy_runtime_rules", check_policy_runtime_rules.main),
        GovernanceCheck("wheel_reuse_rules", check_wheel_reuse_rules.main),
        GovernanceCheck("utility_reuse", validate_utility_reuse.main),
        GovernanceCheck("loc_guidance", check_loc_guidance.main),
        GovernanceCheck("dedup_dead_code_rules", check_dedup_dead_code_rules.main),
        GovernanceCheck("drift_protection", check_drift_protection.main),
    )


def main() -> int:
    issues = _validate_unified_manifest_shape()
    if issues:
        print("Unified governance validation failed:")
        for issue in issues:
            print(f"- [schema] {issue}")
        return 1

    failed: list[str] = []
    for check in _checks():
        status = check.runner()
        if status != 0:
            failed.append(check.name)

    if failed:
        print("Unified governance validation failed:")
        for name in failed:
            print(f"- [check] {name}")
        return 1

    print("Unified governance validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
