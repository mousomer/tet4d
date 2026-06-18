# Utility Index

This file records reusable utilities that should be reused rather than
duplicated.

Before adding a helper, search the repo for an existing implementation.

| Utility | Location | Purpose | Reuse rule |
|---|---|---|---|
| Governance validator | `tools/governance/validate_project_contracts.py` | Validates project contracts and manifest-backed governance. | Reuse for project contract checks instead of adding ad hoc governance validation. |
| Maintenance doc generator | `tools/governance/generate_maintenance_docs.py` | Regenerates policy-backed maintenance docs. | Update policy-pack inputs instead of hand-editing generated maintenance outputs. |
| Godot bundle sync | `tools/migration/sync_godot_bundle.py` | Copies the generated migration bundle into Godot assets. | Reuse for Godot asset refresh instead of manually copying bundle files. |
| C++ trace comparator | `tools/migration/compare_cpp_gameplay_trace.py` | Compares native C++ gameplay traces with Python golden traces. | Reuse for parity evidence before promoting native authority. |
