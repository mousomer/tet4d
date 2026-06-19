# tet4d Technical Debt Register

This register records project-specific technical debt for tet4d.

The debt schema and calculation rules come from
`docs/governance/workspace_bundle/technical_debt_policy.md`.

General drift-protection principles come from
`docs/governance/workspace_bundle/drift_protection_policy.md`.

tet4d-specific debt categories may include:

- `duplication`
- `config-drift`
- `semantic-drift`
- `test-gap`
- `generated-drift`
- `dependency-risk`
- `unsafe-native`
- `godot-boundary-risk`
- `parity-gap`
- `documentation-drift`
- `tooling-gap`
- `suppression`
- `authority-transfer-gap`
- `config-authority-advisory`
- `utility-reuse-advisory`
- `formatting-drift`
- `native-tooling-gap`

## Debt records

| id | category | location | source | classification | severity | remediation_minutes | interest | owner | introduced_by | repayment_trigger | status | notes |
|---|---|---|---|---|---|---:|---|---|---|---|---|---|
| TD-0001 | config-authority-advisory | Godot presentation and trace scripts | Config authority validator reports existing suspicious hardcoded constants | deliberate-prudent | medium | 240 | May hide constants that should move to standard config authority before strict mode | Godot migration | config authority governance stage | Before strict config-authority mode is enabled | accepted | Advisory only; current stage does not change runtime constants |
| TD-0002 | utility-reuse-advisory | Godot native bridge and native trace export helpers | Utility reuse validator reports duplicate trace export helper names across bridge/native surfaces | deliberate-prudent | low | 60 | May obscure ownership of trace export helper boundaries during migration | migration tooling | utility reuse governance stage | Before strict utility-reuse mode is enabled | accepted | Advisory only; no behavior change in current task |
| TD-0003 | formatting-drift | tests/unit/governance formatting baseline | Full Ruff format check reports pre-existing governance test formatting drift | inadvertent-prudent | low | 60 | Keeps full-tree format check noisy and requires touched-file format checks | governance tests | workspace bundle governance stage | Before enforcing full governance format check | accepted | Existing unrelated files remain unformatted |
| TD-0004 | native-tooling-gap | native C++ local tooling environment | Native tooling validator reports clang-format unavailable and clang-tidy skipped without compile_commands.json | deliberate-prudent | low | 120 | Native style/static-analysis execution remains environment-dependent | native tooling | native C++ tooling governance stage | Before strict native tooling mode is enabled | accepted | Policy exists; local optional tools are not installed in this environment |
