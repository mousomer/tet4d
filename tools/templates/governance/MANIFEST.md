# Workspace Governance Bundle Manifest

Status: NON-AUTHORITATIVE TEMPLATE; project-bootstrap only; not tet4d governance.

| File | Purpose | Copy target | Project customization required? |
|---|---|---|---|
| `README.md` | Bundle overview and adoption notes | adopting project governance directory | Usually |
| `MANIFEST.md` | Bundle file list and copy contract | adopting project governance directory | Usually |
| `programming_policy.md` | General programming rules | adopting project governance directory | No |
| `codex_workflow_policy.md` | Agent workflow rules | adopting project governance directory | Usually |
| `testing_policy.md` | General testing expectations | adopting project governance directory | Usually |
| `config_constants_policy.md` | General config/constants rules | adopting project governance directory | Usually |
| `secrets_policy.md` | General secrets hygiene | adopting project governance directory | No |
| `dependency_reuse_policy.md` | Dependency and utility reuse rules | adopting project governance directory | Usually |
| `technical_debt_policy.md` | Technical debt accounting fields | adopting project governance directory | Usually |
| `drift_protection_policy.md` | General drift-protection principles | adopting project governance directory | Usually |
| `validator_design_policy.md` | Validator design rules | adopting project governance directory | No |
| `review_checklist_template.md` | Reusable review checklist | adopting project governance directory | Yes |
| `AGENTS.template.md` | Root agent-instruction template | project root as `AGENTS.md` | Yes |

After copying, add project-specific overlays for authority, verification,
configuration locations, generated outputs, language/framework constraints, and
local validators.
