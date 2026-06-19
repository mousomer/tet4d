from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
BUNDLE_REL = "docs/governance/workspace_bundle"
BUNDLE_ROOT = ROOT / BUNDLE_REL
EXPORT_HELPER_REL = "tools/governance/export_workspace_governance_bundle.py"
REQUIRED_BUNDLE_FILES = {
    "README.md",
    "MANIFEST.md",
    "programming_policy.md",
    "codex_workflow_policy.md",
    "testing_policy.md",
    "config_constants_policy.md",
    "secrets_policy.md",
    "dependency_reuse_policy.md",
    "technical_debt_policy.md",
    "drift_protection_policy.md",
    "validator_design_policy.md",
    "review_checklist_template.md",
    "AGENTS.template.md",
}
FORBIDDEN_TERMS = (
    "tet4d",
    "4d tetris",
    "w-slice",
    "godot is the tet4d product shell",
    "python is the current tet4d semantic oracle",
    "migration/exported_bundle",
    "config/project/policy_pack.json",
)
PROJECT_OVERLAY_RELS = (
    "docs/governance/codex_policy.md",
    "docs/governance/config_policy.md",
    "docs/governance/testing_policy.md",
    "docs/governance/secrets_policy.md",
    "docs/governance/godot_cpp_policy.md",
    "docs/governance/cpp_safety_policy.md",
    "docs/governance/review_checklist.md",
)


@dataclass(frozen=True)
class BundleIssue:
    kind: str
    message: str


def _read_text(root: Path, rel: str, issues: list[BundleIssue]) -> str | None:
    path = root / rel
    if not path.exists():
        issues.append(BundleIssue("missing", f"missing required path: {rel}"))
        return None
    return path.read_text(encoding="utf-8")


def _listed_manifest_files(manifest_text: str) -> set[str]:
    listed: set[str] = set()
    for line in manifest_text.splitlines():
        match = re.match(r"^\|\s*`([^`]+)`\s*\|", line)
        if match:
            listed.add(match.group(1))
    return listed


def _validate_required_files(root: Path, issues: list[BundleIssue]) -> None:
    if not (root / BUNDLE_REL / "README.md").exists():
        issues.append(
            BundleIssue("missing", f"missing required path: {BUNDLE_REL}/README.md")
        )
    if not (root / BUNDLE_REL / "MANIFEST.md").exists():
        issues.append(
            BundleIssue("missing", f"missing required path: {BUNDLE_REL}/MANIFEST.md")
        )
    for filename in sorted(REQUIRED_BUNDLE_FILES):
        rel = f"{BUNDLE_REL}/{filename}"
        if not (root / rel).exists():
            issues.append(BundleIssue("missing", f"missing bundle file: {rel}"))


def _validate_manifest(root: Path, issues: list[BundleIssue]) -> None:
    manifest = _read_text(root, f"{BUNDLE_REL}/MANIFEST.md", issues)
    if manifest is None:
        return
    listed = _listed_manifest_files(manifest)
    missing = REQUIRED_BUNDLE_FILES - listed
    extra = listed - REQUIRED_BUNDLE_FILES
    for filename in sorted(missing):
        issues.append(
            BundleIssue("content", f"MANIFEST.md does not list bundle file: {filename}")
        )
    for filename in sorted(extra):
        issues.append(
            BundleIssue(
                "content", f"MANIFEST.md lists nonexistent bundle file: {filename}"
            )
        )

    bundle_root = root / BUNDLE_REL
    if not bundle_root.exists():
        return
    actual_markdown = {path.name for path in bundle_root.glob("*.md")}
    unlisted = actual_markdown - listed
    for filename in sorted(unlisted):
        issues.append(
            BundleIssue("content", f"bundle markdown file is not listed: {filename}")
        )


def _validate_project_neutrality(root: Path, issues: list[BundleIssue]) -> None:
    bundle_root = root / BUNDLE_REL
    if not bundle_root.exists():
        return
    for path in sorted(bundle_root.glob("*.md")):
        text = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            if term in text:
                rel = path.relative_to(root).as_posix()
                issues.append(
                    BundleIssue(
                        "content",
                        f"{rel} contains project-specific forbidden term: {term}",
                    )
                )


def _validate_router_links(root: Path, issues: list[BundleIssue]) -> None:
    agents = _read_text(root, "AGENTS.md", issues)
    if agents is not None and "workspace_bundle/programming_policy.md" not in agents:
        issues.append(
            BundleIssue(
                "content",
                "AGENTS.md must link to workspace_bundle/programming_policy.md",
            )
        )

    router = _read_text(root, "docs/governance/README.md", issues)
    if router is not None and "docs/governance/workspace_bundle/" not in router:
        issues.append(
            BundleIssue(
                "content",
                "docs/governance/README.md must link to workspace bundle",
            )
        )

    for rel in PROJECT_OVERLAY_RELS:
        text = _read_text(root, rel, issues)
        if text is None:
            continue
        if "docs/governance/workspace_bundle/" not in text and (
            "workspace_bundle/programming_policy.md" not in text
        ):
            issues.append(
                BundleIssue("content", f"{rel} must link to workspace bundle")
            )


def _validate_export_helper(root: Path, issues: list[BundleIssue]) -> None:
    if not (root / EXPORT_HELPER_REL).exists():
        issues.append(
            BundleIssue("missing", f"missing export helper: {EXPORT_HELPER_REL}")
        )
    readme = _read_text(root, f"{BUNDLE_REL}/README.md", issues)
    manifest = _read_text(root, f"{BUNDLE_REL}/MANIFEST.md", issues)
    combined = f"{readme or ''}\n{manifest or ''}"
    if "export_workspace_governance_bundle.py" not in combined:
        issues.append(
            BundleIssue(
                "content",
                "bundle README or MANIFEST must mention export helper",
            )
        )
    if "drift_protection_policy.md" not in combined:
        issues.append(
            BundleIssue(
                "content",
                "bundle README or MANIFEST must mention drift_protection_policy.md",
            )
        )


def validate(root: Path = ROOT) -> list[BundleIssue]:
    issues: list[BundleIssue] = []
    _validate_required_files(root, issues)
    _validate_manifest(root, issues)
    _validate_project_neutrality(root, issues)
    _validate_router_links(root, issues)
    _validate_export_helper(root, issues)
    return issues


def main() -> int:
    issues = validate(ROOT)
    if issues:
        print("Workspace bundle validation failed:")
        for issue in issues:
            print(f"- [{issue.kind}] {issue.message}")
        return 1
    print("Workspace bundle validation passed.")
    print(f"Required bundle files: {len(REQUIRED_BUNDLE_FILES)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
