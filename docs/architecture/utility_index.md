# Utility Index

This file records reusable utilities that should be reused rather than
duplicated.

Before adding a helper, search the repo for an existing implementation.

## Required fields

| Utility | Location | Purpose | Owner | Reuse rule | Migration relevance |
|---|---|---|---|---|---|
| Governance validator | `tools/governance/validate_project_contracts.py` | Validates project contracts and manifest-backed governance. | Governance tooling | Reuse for project contract checks instead of adding ad hoc governance validation. | Keeps migration governance mechanically checked. |
| Unified governance runner | `tools/governance/validate_governance.py` | Runs the governance validation suite. | Governance tooling | Wire new governance validators through this runner instead of bypassing the existing gate. | Keeps migration-specific governance in the canonical verification path. |
| Wheel reuse checker | `tools/governance/check_wheel_reuse_rules.py` | Enforces policy-pack rules for common reinvention patterns. | Governance tooling | Extend policy-pack wheel rules before adding a separate hard-coded reinvention checker. | Prevents Godot/C++ migration helpers from duplicating existing parsing/config/path utilities. |
| Dedup/dead-code checker | `tools/governance/check_dedup_dead_code_rules.py` | Enforces forbidden legacy paths, TODO backlog routing, and configured duplicate-function checks. | Governance tooling | Reuse for duplicate body/dead-code policy instead of adding parallel duplicate-function logic. | Keeps cleanup and migration debt checks aligned with the policy pack. |
| Maintenance doc generator | `tools/governance/generate_maintenance_docs.py` | Regenerates policy-backed maintenance docs. | Governance tooling | Update policy-pack inputs instead of hand-editing generated maintenance outputs. | Keeps authority and project-structure summaries synchronized. |
| Godot bundle sync | `tools/migration/sync_godot_bundle.py` | Copies the generated migration bundle into Godot assets. | Migration tooling | Reuse for Godot asset refresh instead of manually copying bundle files. | Preserves bundle authority boundaries during Godot migration. |
| C++ trace comparator | `tools/migration/compare_cpp_gameplay_trace.py` | Compares native C++ gameplay traces with Python golden traces. | Migration tooling | Reuse for parity evidence before promoting native authority. | Blocks silent C++ semantic drift from the Python oracle. |

## Candidate areas to index

- configuration loading and validation
- topology transition helpers
- trace/replay readers and writers
- projection/view helpers
- migration bundle export helpers
- governance subprocess/path helpers
