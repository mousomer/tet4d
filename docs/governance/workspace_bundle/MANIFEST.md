# Workspace Governance Bundle Manifest

| File | Purpose | Copy target | Project customization required? |
|---|---|---|---|
| `README.md` | Bundle overview and adoption notes | `docs/governance/workspace_bundle/` | Usually |
| `MANIFEST.md` | Bundle file list and copy contract | `docs/governance/workspace_bundle/` | Usually |
| `programming_policy.md` | General programming rules | `docs/governance/workspace_bundle/` | No |
| `codex_workflow_policy.md` | Agent workflow rules | `docs/governance/workspace_bundle/` | Usually |
| `testing_policy.md` | General testing expectations | `docs/governance/workspace_bundle/` | Usually |
| `config_constants_policy.md` | General config/constants rules | `docs/governance/workspace_bundle/` | Usually |
| `secrets_policy.md` | General secrets hygiene | `docs/governance/workspace_bundle/` | No |
| `dependency_reuse_policy.md` | Dependency and utility reuse rules | `docs/governance/workspace_bundle/` | Usually |
| `technical_debt_policy.md` | Technical debt accounting fields | `docs/governance/workspace_bundle/` | Usually |
| `drift_protection_policy.md` | General drift-protection principles | `docs/governance/workspace_bundle/` | Usually |
| `validator_design_policy.md` | Validator design rules | `docs/governance/workspace_bundle/` | No |
| `review_checklist_template.md` | Reusable review checklist | `docs/governance/workspace_bundle/` | Yes |
| `AGENTS.template.md` | Root agent-instruction template | project root as `AGENTS.md` | Yes |

After copying, add project-specific overlays for authority, verification,
configuration locations, generated outputs, language/framework constraints, and
local validators.
