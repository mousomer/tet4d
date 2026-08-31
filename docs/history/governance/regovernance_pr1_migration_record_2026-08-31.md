# Re-Governance PR 1 Migration Record

Status: HISTORICAL / NON-AUTHORITATIVE

This record documents the mechanical path migration performed by PR 1. It is
not an active route, task contract, or replacement governance model.

## Design comparison

The pre-change machine and human design sources were
`config/project/policy_pack.json`, `docs/governance/README.md`,
`docs/WORKFLOW_CODEX.md`, and `docs/DOCUMENTATION_MAP.md`. They coupled active
routing and content validation to two accumulated execution ledgers even
though subsystem authority, product behaviour, verification categories, and
architecture ownership were defined elsewhere. PR 1 removes only that
lifecycle coupling.

## Migration coverage

| Source path | Disposition | Historical destination | `content_rules` | `required_paths` | Routing/reference checks | Other live references |
| --- | --- | --- | --- | --- | --- | --- |
| `docs/governance/task_contract.md` | Retired as active governance; durable execution rationale retained | `docs/history/tasks/task_contract_ledger_through_2026-08-31.md` | Obsolete heading rule removed | No pre-change entry; absence verified | Old path blocked; active routers protected from reintroduction | Workflow, governance router, review checklist, drift map, documentation map, and restart handoff reconciled |
| `docs/governance/completion_report.md` | Retired as active governance; durable manual findings and limitations retained | `docs/history/completion_reports/completion_report_ledger_through_2026-08-31.md` | Obsolete heading rule removed | No pre-change entry; absence verified | Old path blocked; active routers protected from reintroduction | Workflow, governance router, review checklist, drift map, documentation map, and restart handoff reconciled |
| `docs/DOCUMENTATION_MAP.md` | Remains active with stale ledger routes removed | N/A | Existing ownership retained | Existing status retained | Broader consolidation intentionally deferred | Final disposition is pending PR 2 |

## Semantic effect

None. The migration does not change architecture authority, product semantics,
runtime behaviour, task-routing taxonomy, workflow modifiers, verification
requirements, or authority transfer/establishment rules.

## Surface measurement

The repeatable counting boundary includes root and nested dispatch files, the
governance router/workflow/policies, machine policy pack, review and PR
contracts, documentation map, authority-transfer protocol, and restart
handoff. It excludes historical files, task-selected product/architecture
authorities, generated inventories, and `tools/governance/*.py` implementation.

- Active routed governance before: 9,824 lines.
- Active routed governance after: 5,801 lines.
- `CURRENT_STATE.md` before/after: 733 / 107 lines.
- Active task/completion ledger lines removed: 3,438.
- Archived ledger lines after non-authoritative headers: 3,463.
