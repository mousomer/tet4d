# tet4d Dispatch

This file is the thin entrypoint for repo workflow. It dispatches to the
single machine-readable policy authority and to the human docs that explain how
to apply it.

## Canonical authorities

- Machine-readable governance authority: `config/project/policy_pack.json`
- Human workflow explainer: `docs/WORKFLOW_CODEX.md`
- Restart handoff only: `CURRENT_STATE.md`
- Product requirements: `docs/rds/`
- Architecture boundary contract: `docs/ARCHITECTURE_CONTRACT.md`
- Topology-playground current authority:
  `docs/plans/topology_playground_current_authority.md`

## Context-loading order

1. Read this `AGENTS.md`.
2. Read `CURRENT_STATE.md` first for long-running refactors, restart handoff,
   architecture cleanup, or staged migration work.
3. For topology-playground work, read
   `docs/plans/topology_playground_current_authority.md` before archived
   topology-playground plans or audits.
4. Read `docs/WORKFLOW_CODEX.md` for repo workflow, verification, and update
   sequencing.
5. Read the relevant `docs/rds/*` files before changing product behavior.
6. Read `docs/ARCHITECTURE_CONTRACT.md` before boundary-sensitive refactors or
   folder moves.
7. Read `config/project/policy_pack.json` when the task touches governance,
   validation, generated maintenance docs, or policy-backed tooling.

## Operating reminders

- `CURRENT_STATE.md` is handoff-only. Do not treat it as a second governance
  authority.
- `docs/rds/` owns product behavior. Repo workflow belongs in
  `docs/WORKFLOW_CODEX.md`.
- Generated maintenance docs and maintenance validation are driven from
  `config/project/policy_pack.json`.

## Validation

Run:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```
