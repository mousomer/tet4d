from __future__ import annotations

from pathlib import Path

import tools.governance.validate_workspace_bundle as validator


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _manifest(files: set[str] | None = None) -> str:
    rows = [
        "# Workspace Governance Bundle Manifest",
        "",
        "| File | Purpose | Copy target | Project customization required? |",
        "|---|---|---|---|",
    ]
    for filename in sorted(files or validator.REQUIRED_BUNDLE_FILES):
        rows.append(
            f"| `{filename}` | Purpose | `docs/governance/workspace_bundle/` | No |"
        )
    return "\n".join(rows) + "\n"


def _write_valid_workspace_bundle(root: Path) -> None:
    bundle = root / validator.BUNDLE_REL
    for filename in validator.REQUIRED_BUNDLE_FILES:
        if filename == "MANIFEST.md":
            _write(bundle / filename, _manifest())
        elif filename == "README.md":
            _write(
                bundle / filename,
                "Workspace Governance Bundle\n"
                "tools/governance/export_workspace_governance_bundle.py\n",
            )
        else:
            _write(bundle / filename, f"# {filename}\nReusable neutral guidance.\n")
    _write(
        root / "AGENTS.md",
        "See docs/governance/workspace_bundle/programming_policy.md.\n",
    )
    _write(
        root / "docs" / "governance" / "README.md",
        "See docs/governance/workspace_bundle/.\n",
    )
    for rel in validator.PROJECT_OVERLAY_RELS:
        _write(root / rel, "Extends docs/governance/workspace_bundle/.\n")
    _write(root / validator.EXPORT_HELPER_REL, "def main():\n    return 0\n")


def test_valid_workspace_bundle_passes(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)

    assert validator.validate(tmp_path) == []


def test_missing_bundle_readme_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    (tmp_path / validator.BUNDLE_REL / "README.md").unlink()

    issues = validator.validate(tmp_path)

    assert any("README.md" in issue.message for issue in issues)


def test_missing_manifest_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    (tmp_path / validator.BUNDLE_REL / "MANIFEST.md").unlink()

    issues = validator.validate(tmp_path)

    assert any("MANIFEST.md" in issue.message for issue in issues)


def test_missing_required_bundle_file_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    (tmp_path / validator.BUNDLE_REL / "testing_policy.md").unlink()

    issues = validator.validate(tmp_path)

    assert any("testing_policy.md" in issue.message for issue in issues)


def test_missing_drift_protection_policy_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    (tmp_path / validator.BUNDLE_REL / "drift_protection_policy.md").unlink()

    issues = validator.validate(tmp_path)

    assert any("drift_protection_policy.md" in issue.message for issue in issues)


def test_manifest_missing_file_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    listed = set(validator.REQUIRED_BUNDLE_FILES)
    listed.remove("secrets_policy.md")
    _write(tmp_path / validator.BUNDLE_REL / "MANIFEST.md", _manifest(listed))

    issues = validator.validate(tmp_path)

    assert any(
        "does not list bundle file: secrets_policy.md" in issue.message
        for issue in issues
    )


def test_manifest_missing_drift_protection_policy_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    listed = set(validator.REQUIRED_BUNDLE_FILES)
    listed.remove("drift_protection_policy.md")
    _write(tmp_path / validator.BUNDLE_REL / "MANIFEST.md", _manifest(listed))

    issues = validator.validate(tmp_path)

    assert any("drift_protection_policy.md" in issue.message for issue in issues)


def test_manifest_listing_nonexistent_file_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    listed = set(validator.REQUIRED_BUNDLE_FILES)
    listed.add("extra_policy.md")
    _write(tmp_path / validator.BUNDLE_REL / "MANIFEST.md", _manifest(listed))

    issues = validator.validate(tmp_path)

    assert any("extra_policy.md" in issue.message for issue in issues)


def test_forbidden_project_specific_term_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    _write(
        tmp_path / validator.BUNDLE_REL / "programming_policy.md",
        "This bundle is for tet4d.\n",
    )

    issues = validator.validate(tmp_path)

    assert any("forbidden term: tet4d" in issue.message for issue in issues)


def test_forbidden_project_specific_term_in_drift_policy_fails(
    tmp_path: Path,
) -> None:
    _write_valid_workspace_bundle(tmp_path)
    _write(
        tmp_path / validator.BUNDLE_REL / "drift_protection_policy.md",
        "Python is the current tet4d semantic oracle.\n",
    )

    issues = validator.validate(tmp_path)

    assert any("forbidden term" in issue.message for issue in issues)


def test_root_agents_missing_programming_policy_link_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    _write(tmp_path / "AGENTS.md", "No bundle link.\n")

    issues = validator.validate(tmp_path)

    assert any("AGENTS.md must link" in issue.message for issue in issues)


def test_governance_router_missing_workspace_bundle_link_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    _write(tmp_path / "docs" / "governance" / "README.md", "No bundle link.\n")

    issues = validator.validate(tmp_path)

    assert any(
        "README.md must link to workspace bundle" in issue.message for issue in issues
    )


def test_export_helper_missing_fails(tmp_path: Path) -> None:
    _write_valid_workspace_bundle(tmp_path)
    (tmp_path / validator.EXPORT_HELPER_REL).unlink()

    issues = validator.validate(tmp_path)

    assert any("missing export helper" in issue.message for issue in issues)
