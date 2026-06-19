# Workspace Governance Bundle

This directory contains reusable programming-governance guidance intended to be
copied into other projects.

It defines general engineering rules. It does not define project-specific
authority, domain semantics, build commands, config paths, or migration plans.

A project that copies this bundle should add its own project-specific overlays
for:

- authority map
- verification commands
- config locations
- domain semantics
- language/framework-specific constraints
- generated-file surfaces
- project-specific validators

See `MANIFEST.md` for files and customization requirements.

Use `tools/governance/export_workspace_governance_bundle.py` from the source
project to copy only this bundle into another repository.

Use `technical_debt_policy.md` for reusable debt accounting rules and
`drift_protection_policy.md` for reusable drift-protection principles.
