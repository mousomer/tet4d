# tet4d Dispatch

This file is the thin entrypoint for repo workflow. It dispatches to the
single machine-readable policy authority and to the human docs that explain how
to apply it.

tet4d is currently a Python-centered project. The existing Python
implementation is the semantic oracle for gameplay, topology, trace, rotation,
collision, movement, scoring, configuration defaults, and replay behavior
unless an authority document explicitly says otherwise. Godot/C++ governance is
a migration overlay, not a replacement root constitution.

## Canonical authorities

- Machine-readable governance authority: `config/project/policy_pack.json`
- Human workflow explainer: `docs/WORKFLOW_CODEX.md`
- Restart handoff only: `CURRENT_STATE.md`
- Product requirements: `docs/rds/`
- Architecture boundary contract: `docs/ARCHITECTURE_CONTRACT.md`
- Migration authority map: `docs/architecture/authority_map.md`
- Governance router: `docs/governance/README.md`
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
8. For migration decisions, read `docs/architecture/authority_map.md` and
   `docs/governance/README.md`.
9. For Godot UI/product-shell work, also read `godot/AGENTS.md` if present.
10. For C++/GDExtension/native work, also read `native/AGENTS.md` if present.

## Instruction routing

- General programming rules follow
  `docs/governance/workspace_bundle/programming_policy.md`.
- tet4d-specific semantic authority follows
  `docs/architecture/authority_map.md`.
- Python implementation work follows existing repo/Python governance, relevant
  `docs/rds/*`, and the current Python tests and traces.
- Godot UI/product-shell work follows root governance plus `godot/AGENTS.md`
  and `docs/governance/godot_cpp_policy.md`.
- C++/GDExtension/native work follows root governance plus `native/AGENTS.md`
  and `docs/governance/godot_cpp_policy.md`.
- Testing, constants/config, secrets, and review requirements route through
  the relevant documents under `docs/governance/` and `docs/policies/`.

## Operating reminders

- `CURRENT_STATE.md` is handoff-only. Do not treat it as a second governance
  authority.
- `docs/rds/` owns product behavior. Repo workflow belongs in
  `docs/WORKFLOW_CODEX.md`.
- Generated maintenance docs and maintenance validation are driven from
  `config/project/policy_pack.json`.
- Do not rewrite existing functions unless explicitly asked.
- Search for existing implementations before adding new code or governance.
- Reuse existing utilities and policies; do not duplicate rule logic or
  governance documents.
- No secrets in source, config, tests, traces, logs, screenshots, prompts, or
  documentation examples.
- No nontrivial magic numbers in source; route constants through standard
  config policy.
- Behavioral changes require tests.
- Python remains the semantic oracle until a documented authority transfer
  occurs.
- Godot/C++ code must prove parity with Python through tests, traces, or
  documented verification before it becomes authoritative.

## Done criteria

Every change must report:

- files changed
- existing governance files reused or extended
- new routing/authority decisions introduced
- tests or checks run
- risks or unverified areas

## Validation

Run:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```
