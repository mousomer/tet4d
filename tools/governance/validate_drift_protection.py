from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    ".github/pull_request_template.md",
    "docs/architecture/first_subsystem_parity_pilot.md",
    "docs/architecture/parity_pilot_audit_and_promotion_gates.md",
    "docs/architecture/second_parity_slice_candidate_selection.md",
    "docs/governance/workspace_bundle/drift_protection_policy.md",
    "docs/governance/drift_protection_map.md",
    "docs/governance/README.md",
    "docs/governance/review_checklist.md",
    "docs/governance/technical_debt_register.md",
    "docs/governance/native_tooling_ci_policy.md",
    "docs/architecture/authority_map.md",
    "docs/architecture/parity_protocol.md",
    "docs/architecture/authority_transfer_protocol.md",
    "docs/architecture/utility_index.md",
    "tools/governance/validate_authority_transfer.py",
    "tools/governance/validate_drift_protection.py",
    "tools/governance/validate_governance.py",
    "tools/governance/validate_project_contracts.py",
    "tools/governance/validate_workspace_bundle.py",
    "tools/governance/validate_technical_debt.py",
    "tools/governance/validate_config_authority.py",
    "tools/governance/validate_utility_reuse.py",
    "tools/governance/validate_godot_semantic_boundary.py",
    "tools/governance/validate_native_cpp_tooling.py",
)

ROUTER_LINKS = {
    "docs/governance/README.md": (
        ".github/pull_request_template.md",
        "docs/governance/workspace_bundle/drift_protection_policy.md",
        "docs/governance/workspace_bundle/review_checklist_template.md",
        "docs/governance/drift_protection_map.md",
        "docs/governance/technical_debt_register.md",
        "docs/governance/native_tooling_ci_policy.md",
        "docs/governance/review_checklist.md",
        "tools/governance/validate_drift_protection.py",
        "tools/governance/validate_technical_debt.py",
    ),
    "AGENTS.md": (
        "docs/governance/workspace_bundle/programming_policy.md",
        "docs/governance/workspace_bundle/drift_protection_policy.md",
        "docs/architecture/authority_map.md",
    ),
}

REACHABILITY_ROOTS = (
    "AGENTS.md",
    "godot/AGENTS.md",
    "native/AGENTS.md",
    "docs/DOCUMENTATION_MAP.md",
    "docs/governance/README.md",
    "docs/governance/workspace_bundle/MANIFEST.md",
    "docs/policies/INDEX.md",
    "docs/architecture/authority_map.md",
    "docs/architecture/utility_index.md",
    "docs/architecture/parity_protocol.md",
    "docs/architecture/authority_transfer_protocol.md",
    "docs/governance/drift_protection_map.md",
)

GOVERNANCE_SCAN_ROOTS = (
    "docs/governance",
    "docs/architecture",
    "docs/policies",
)

REACHABILITY_ALLOWLIST = {
    "docs/governance/workspace_bundle/README.md",
    "docs/policies/INDEX.md",
}

VALIDATORS = (
    "validate_workspace_bundle.py",
    "validate_technical_debt.py",
    "validate_authority_transfer.py",
    "validate_drift_protection.py",
    "validate_project_contracts.py",
    "validate_config_authority.py",
    "validate_utility_reuse.py",
    "validate_godot_semantic_boundary.py",
    "validate_native_cpp_tooling.py",
)

DANGEROUS_AUTHORITY_PHRASES = (
    "c++ is authoritative for gameplay",
    "c++ owns tet4d semantics",
    "gdscript owns topology",
    "godot owns movement rules",
    "godot owns collision rules",
    "native core is the source of truth",
)

AUTHORITY_EXEMPTION_PHRASES = (
    "after parity transfer",
    "once authority is transferred",
    "provisional until parity",
    "until parity transfer",
    "until explicitly promoted",
    "only after",
    "authority map records the transfer",
    "no policy claims",
    "must not claim",
    "must not imply",
)

GENERATED_SURFACES = (
    "docs/CONFIGURATION_REFERENCE.md",
    "migration/exported_bundle/manifest.json",
    "migration/exported_bundle/docs/authority_index.json",
    "migration/exported_bundle/config/tet4d_config_bundle.json",
)

REVIEW_CONCEPTS = {
    "technical debt": ("technical debt", "technical-debt"),
    "drift protection": ("drift protection",),
    "authority": ("authority",),
    "config/generated": ("config/generated", "generated outputs"),
    "utility reuse": ("utility reuse", "dependency / utility reuse"),
    "Godot boundary": ("godot semantic boundary",),
    "C++ safety or native safety": ("c++ safety", "native c++ safety"),
    "native tooling CI readiness": ("native tooling ci readiness",),
    "first parity pilot": ("first parity pilot", "first subsystem parity pilot"),
    "promotion gates": ("promotion gates", "second parity slice"),
    "parity": ("parity",),
}

PR_TEMPLATE_CONCEPTS = {
    "authority": ("authority",),
    "technical debt": ("technical debt", "technical-debt"),
    "drift protection": ("drift protection",),
    "validation": ("validation", "verify.sh"),
    "native tooling": ("native tooling", "tet4d_strict_native_tools"),
    "staging": ("staging", "staged diff", "git diff --cached --check"),
}


@dataclass(frozen=True)
class CheckResult:
    name: str
    failures: list[str]


def read_text(root: Path, rel: str, failures: list[str] | None = None) -> str:
    path = root / rel
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if failures is not None:
            failures.append(f"missing required path: {rel}")
        return ""


def _has_any(text: str, options: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(option.lower() in lower for option in options)


def contains_all_concepts(text: str, concepts: dict[str, tuple[str, ...]]) -> list[str]:
    return [name for name, options in concepts.items() if not _has_any(text, options)]


def check_required_files(root: Path = ROOT) -> CheckResult:
    failures = [
        f"missing required file: {rel}"
        for rel in REQUIRED_FILES
        if not (root / rel).exists()
    ]
    return CheckResult("required files", failures)


def check_router_reachability(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    for rel, required_links in ROUTER_LINKS.items():
        text = read_text(root, rel, failures)
        for link in required_links:
            if link not in text:
                failures.append(f"{rel} does not link to {link}")
    return CheckResult("router reachability", failures)


def _reachable_text(root: Path) -> str:
    chunks: list[str] = []
    for rel in REACHABILITY_ROOTS:
        path = root / rel
        if path.exists():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _is_governance_like_markdown(rel: str) -> bool:
    path = Path(rel)
    if path.name.upper() == "README.MD":
        return False
    if path.name == "MANIFEST.md":
        return False
    lower = rel.lower()
    if "history/" in lower or "/historical" in lower:
        return False
    if "generated" in lower:
        return False
    return rel not in REACHABILITY_ALLOWLIST


def check_governance_reachability(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    reachable = _reachable_text(root)
    for scan_root in GOVERNANCE_SCAN_ROOTS:
        base = root / scan_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if not _is_governance_like_markdown(rel):
                continue
            if rel not in reachable and path.name not in reachable:
                failures.append(
                    f"{rel} is not reachable from a governance router, index, manifest, or local AGENTS file"
                )
    return CheckResult("governance reachability", failures)


def _manifest_entries(text: str) -> set[str]:
    entries: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if match:
            entries.add(match.group(1))
    return entries


def check_workspace_bundle_consistency(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    bundle_rel = "docs/governance/workspace_bundle"
    bundle_root = root / bundle_rel
    drift_rel = f"{bundle_rel}/drift_protection_policy.md"
    manifest_rel = f"{bundle_rel}/MANIFEST.md"
    if not (root / drift_rel).exists():
        failures.append(f"{drift_rel} is missing")
    manifest_text = read_text(root, manifest_rel, failures)
    listed = _manifest_entries(manifest_text)
    if "drift_protection_policy.md" not in listed:
        failures.append(
            "workspace bundle MANIFEST.md does not list drift_protection_policy.md"
        )
    if bundle_root.exists():
        transfer_protocol = bundle_root / "authority_transfer_protocol.md"
        if transfer_protocol.exists():
            failures.append(
                "authority-transfer protocol must not live in workspace bundle"
            )
        actual_markdown = {path.name for path in bundle_root.glob("*.md")}
        for filename in sorted(actual_markdown - listed):
            failures.append(f"workspace bundle markdown file is not listed: {filename}")
        forbidden_terms = (
            "tet4d",
            "python is the current tet4d semantic oracle",
            "godot is the tet4d product shell",
        )
        for path in sorted(bundle_root.glob("*.md")):
            text = path.read_text(encoding="utf-8").lower()
            for term in forbidden_terms:
                if term in text:
                    rel = path.relative_to(root).as_posix()
                    failures.append(
                        f"{rel} contains project-specific forbidden term: {term}"
                    )
    return CheckResult("workspace bundle consistency", failures)


def check_validator_integration(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    text = read_text(root, "tools/governance/validate_governance.py", failures)
    for validator in VALIDATORS:
        token = validator.removesuffix(".py")
        if token not in text and validator not in text:
            failures.append(
                f"tools/governance/validate_governance.py does not reference {validator}"
            )
    return CheckResult("validator integration", failures)


def _append_missing_doc_concepts(
    root: Path,
    rel: str,
    concepts: dict[str, tuple[str, ...]],
    failures: list[str],
) -> None:
    text = read_text(root, rel, failures)
    for concept in contains_all_concepts(text, concepts):
        failures.append(f"{rel} is missing authority concept `{concept}`")


def _is_exempt_authority_phrase(line: str) -> bool:
    lower = line.lower()
    return any(exemption in lower for exemption in AUTHORITY_EXEMPTION_PHRASES)


def check_authority_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    _append_missing_doc_concepts(
        root,
        "docs/architecture/authority_map.md",
        {
            "Python semantic oracle": ("semantic oracle", "python"),
            "Godot shell/presentation": ("product shell", "presentation", "ui shell"),
            "C++ provisional until parity": ("provisional", "parity"),
        },
        failures,
    )
    _append_missing_doc_concepts(
        root,
        "docs/architecture/parity_protocol.md",
        {
            "Python oracle": ("python oracle", "semantic oracle"),
            "golden fixtures or traces": ("golden", "fixture", "trace"),
            "comparison mode": ("comparison mode",),
            "authority transfer or promotion": ("authority transfer", "promotion"),
        },
        failures,
    )
    _append_missing_doc_concepts(
        root,
        "docs/governance/godot_cpp_policy.md",
        {
            "GDScript no semantic truth": ("gdscript", "must not", "semantic"),
            "topology": ("topology",),
            "movement": ("movement", "move"),
            "collision": ("collision",),
            "gravity": ("gravity",),
            "rotation": ("rotation",),
            "scoring": ("scoring", "score"),
            "trace/replay semantics": ("trace", "replay"),
        },
        failures,
    )
    _append_missing_doc_concepts(
        root,
        "docs/governance/native_tooling_ci_policy.md",
        {
            "local advisory mode": ("local advisory",),
            "local strict mode": ("local strict",),
            "CI strict mode": ("ci strict",),
            "compile database": ("compile_commands.json",),
            "Python semantic oracle": ("semantic oracle",),
            "authority transfer": ("authority_transfer_protocol",),
        },
        failures,
    )

    for rel in (
        "AGENTS.md",
        "docs/governance/README.md",
        "docs/governance/godot_cpp_policy.md",
        "docs/governance/cpp_safety_policy.md",
        "docs/governance/native_tooling_ci_policy.md",
        "docs/governance/testing_policy.md",
        "docs/architecture/authority_map.md",
        "docs/architecture/parity_protocol.md",
        "docs/governance/drift_protection_map.md",
    ):
        text = read_text(root, rel, failures)
        for lineno, line in enumerate(text.splitlines(), start=1):
            lower = line.lower()
            if _is_exempt_authority_phrase(lower):
                continue
            for phrase in DANGEROUS_AUTHORITY_PHRASES:
                if phrase in lower:
                    failures.append(
                        f"{rel}:{lineno} contains dangerous authority-inversion phrase: {phrase}"
                    )
    return CheckResult("authority drift", failures)


def _has_generated_marker(text: str) -> bool:
    lower = text.lower()
    return "generated" in lower and ("do not edit" in lower or "generator" in lower)


def check_generated_file_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    map_text = read_text(root, "docs/governance/drift_protection_map.md", failures)
    config_policy = read_text(root, "docs/governance/config_policy.md", failures)
    for rel in GENERATED_SURFACES:
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        policy_names_generator = rel in map_text and (
            "tools/migration/export_config_bundle.py" in map_text
            or "tools/governance/generate_configuration_reference.py" in map_text
        )
        policy_names_source = (
            rel in config_policy or "generated from those sources" in config_policy
        )
        if not (
            _has_generated_marker(text) or policy_names_generator or policy_names_source
        ):
            failures.append(
                f"{rel} does not identify a generated marker, source authority, or generator"
            )
    return CheckResult("generated-file drift", failures)


def check_debt_advisory_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    register = read_text(root, "docs/governance/technical_debt_register.md", failures)
    governance = read_text(root, "tools/governance/validate_governance.py", failures)
    if "validate_technical_debt" not in governance:
        failures.append(
            "tools/governance/validate_governance.py does not reference validate_technical_debt.py"
        )
    if "docs/governance/workspace_bundle/technical_debt_policy.md" not in register:
        failures.append("technical debt register must link workspace debt policy")
    if "docs/governance/workspace_bundle/drift_protection_policy.md" not in register:
        failures.append("technical debt register must link workspace drift policy")
    return CheckResult("debt/advisory drift", failures)


def check_review_checklist_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    checklist = read_text(root, "docs/governance/review_checklist.md", failures)
    for concept in contains_all_concepts(checklist, REVIEW_CONCEPTS):
        failures.append(
            f"docs/governance/review_checklist.md is missing review concept `{concept}`"
        )
    pr_template = read_text(root, ".github/pull_request_template.md", failures)
    for concept in contains_all_concepts(pr_template, PR_TEMPLATE_CONCEPTS):
        failures.append(
            f".github/pull_request_template.md is missing review concept `{concept}`"
        )

    router = read_text(root, "docs/governance/README.md", failures)
    drift_map = read_text(root, "docs/governance/drift_protection_map.md", failures)
    if (
        ".github/pull_request_template.md" not in router
        and ".github/pull_request_template.md" not in drift_map
    ):
        failures.append(
            ".github/pull_request_template.md is not reachable from review governance"
        )
    return CheckResult("review checklist drift", failures)


def check_parity_pilot_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    parity_protocol = read_text(root, "docs/architecture/parity_protocol.md", failures)
    audit_rel = "docs/architecture/parity_pilot_audit_and_promotion_gates.md"
    if audit_rel not in parity_protocol:
        failures.append(
            "docs/architecture/parity_protocol.md does not link to "
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md"
        )

    governance_router = read_text(root, "docs/governance/README.md", failures)
    drift_map = read_text(root, "docs/governance/drift_protection_map.md", failures)
    if audit_rel not in governance_router and audit_rel not in drift_map:
        failures.append(
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md is not reachable from governance routing"
        )

    for rel in (
        "tools/migration/first_subsystem_parity_pilot.py",
        "tests/unit/migration/test_first_subsystem_parity_pilot.py",
    ):
        if rel not in drift_map:
            failures.append(
                f"docs/governance/drift_protection_map.md does not list {rel}"
            )

    audit_text = read_text(root, audit_rel, failures).lower()
    if (
        "does not transfer authority" not in audit_text
        and "not authority transfer" not in audit_text
    ):
        failures.append(
            "docs/architecture/parity_pilot_audit_and_promotion_gates.md must preserve no-authority-transfer wording"
        )
    return CheckResult("parity pilot drift", failures)


def check_second_parity_selection_drift(root: Path = ROOT) -> CheckResult:
    failures: list[str] = []
    selection_rel = "docs/architecture/second_parity_slice_candidate_selection.md"
    selection_text = read_text(root, selection_rel, failures)
    parity_text = read_text(root, "docs/architecture/parity_protocol.md", failures)
    governance_text = read_text(root, "docs/governance/README.md", failures)
    drift_text = read_text(root, "docs/governance/drift_protection_map.md", failures)

    if selection_text:
        lower_selection = selection_text.lower()
        if "candidate selection does not transfer authority" not in lower_selection:
            failures.append(
                f"{selection_rel} must state candidate selection does not transfer authority"
            )
        if "transferred" in lower_selection and "must not" not in lower_selection:
            failures.append(
                f"{selection_rel} must not claim a transferred authority state"
            )
    if selection_rel not in parity_text:
        failures.append(
            "parity_protocol.md must route to second parity slice selection"
        )
    if selection_rel not in governance_text and selection_rel not in drift_text:
        failures.append(
            "second parity slice selection must be reachable from governance README or drift map"
        )
    if selection_rel not in drift_text:
        failures.append(
            "drift_protection_map.md must list second parity slice selection as a parity drift surface"
        )

    return CheckResult("second parity selection drift", failures)


def validate(root: Path = ROOT) -> list[CheckResult]:
    return [
        check_required_files(root),
        check_router_reachability(root),
        check_governance_reachability(root),
        check_workspace_bundle_consistency(root),
        check_validator_integration(root),
        check_authority_drift(root),
        check_generated_file_drift(root),
        check_debt_advisory_drift(root),
        check_review_checklist_drift(root),
        check_parity_pilot_drift(root),
        check_second_parity_selection_drift(root),
    ]


def main() -> int:
    results = validate(ROOT)
    failures = [failure for result in results for failure in result.failures]
    if failures:
        print("Drift protection validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Drift protection validation passed.")
    print("Checks:")
    for result in results:
        print(f"- {result.name}: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
