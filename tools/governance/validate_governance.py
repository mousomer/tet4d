from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

GOVERNANCE_PATH = ROOT / "config/project/policy/governance.json"
CODE_RULES_PATH = ROOT / "config/project/policy/code_rules.json"


@dataclass(frozen=True)
class GovernanceCheck:
    name: str
    runner: Callable[[], int]


def _validate_unified_manifest_shape() -> list[str]:
    from tools.governance._common import load_json_object

    issues: list[str] = []
    governance = load_json_object(
        GOVERNANCE_PATH, "config/project/policy/governance.json"
    )
    code_rules = load_json_object(
        CODE_RULES_PATH, "config/project/policy/code_rules.json"
    )

    required_governance_keys = (
        "verification_command",
        "ci_entrypoint",
        "contributor_directives",
        "risk_gates",
        "architecture",
        "tech_debt_budget",
        "drift_protection",
        "contracts",
    )
    for key in required_governance_keys:
        if key not in governance:
            issues.append(f"governance.json missing required key: {key}")

    required_code_rule_keys = (
        "sanitation",
        "magic_numbers",
        "wheel_reuse",
        "dead_code",
        "loc_guidance",
    )
    for key in required_code_rule_keys:
        if key not in code_rules:
            issues.append(f"code_rules.json missing required key: {key}")

    return issues


def _checks() -> tuple[GovernanceCheck, ...]:
    from tools.governance import check_dedup_dead_code_rules
    from tools.governance import check_drift_protection
    from tools.governance import check_loc_guidance
    from tools.governance import check_policy_runtime_rules
    from tools.governance import check_risk_gates
    from tools.governance import check_wheel_reuse_rules
    from tools.governance import validate_project_contracts

    return (
        GovernanceCheck("contracts", validate_project_contracts.main),
        GovernanceCheck("risk_gates", check_risk_gates.main),
        GovernanceCheck("policy_runtime_rules", check_policy_runtime_rules.main),
        GovernanceCheck("wheel_reuse_rules", check_wheel_reuse_rules.main),
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
