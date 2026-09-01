# Workspace Governance Bundle

Status: NON-AUTHORITATIVE TEMPLATE; project-bootstrap only; not tet4d governance.

This directory contains reusable programming-governance guidance intended to be
copied and customized in other projects. Current tet4d governance is routed by
the root `AGENTS.md`; no file in this directory owns or routes tet4d work.

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
