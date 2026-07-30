# tet4d Dispatch

tet4d is a Python-centered game and engine with Godot as the product-shell
direction. Python remains the semantic oracle for gameplay, topology, trace,
replay, and defaults unless a documented authority transfer says otherwise.
Native C++/GDExtension receives subsystem authority only through documented
parity evidence and the authority-transfer process.

## Canonical authorities

- Governance and generated-maintenance policy:
  `config/project/policy_pack.json`
- Contributor workflow and verification: `docs/WORKFLOW_CODEX.md`
- Product behaviour: relevant documents under `docs/rds/`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Migration ownership: `docs/architecture/authority_map.md`
- Documentation and historical routing: `docs/DOCUMENTATION_MAP.md`
- Governance policy routing: `docs/governance/README.md`
- Repository-changing task boundary: `docs/governance/task_contract.md`
- Completion evidence format: `docs/governance/completion_report.md`
- Restart and staged-work handoff only: `CURRENT_STATE.md`
- Open work and deferred scope: `docs/BACKLOG.md`

## Task routing

- Narrow review: inspect the changed diff, touched tests, and the authority
  routed by `docs/DOCUMENTATION_MAP.md`.
- Python engine or gameplay: read the architecture contract, relevant RDS,
  touched modules, and tests.
- Godot UI/product shell: also follow `godot/AGENTS.md` and the relevant
  product or presentation authority.
- Native C++/GDExtension: also follow `native/AGENTS.md`, the authority map,
  and the applicable parity or authority-transfer protocol.
- Topology explorer: read
  `docs/plans/topology_playground_current_authority.md`, then the relevant
  runtime and tests.
- Governance, validation, generated maintenance docs, policy-backed tooling,
  manifest contracts, or policy interpretation: read the policy pack,
  governance router, and affected validators or generators.
- Packaging: read `docs/rds/RDS_PACKAGING.md`,
  `docs/RELEASE_CHECKLIST.md`, and affected scripts/tests.
- Staged migration, restart, architecture restructuring, or multi-batch
  handoff: read `CURRENT_STATE.md`, `docs/BACKLOG.md`, and the routed
  architecture authorities.

Use `docs/WORKFLOW_CODEX.md` for detailed workflow and focused checks. Do not
load `CURRENT_STATE.md` or the full policy pack for an ordinary isolated task
unless one of the routes above requires it.

## Universal invariants

- Inspect current code, tests, and owning authority documents before editing;
  search for existing implementations and policies before adding new ones.
- Relevant RDS documents own product behaviour. The architecture contract and
  authority map own boundaries; do not invent a competing authority.
- Python remains the semantic oracle until a completed transfer record changes
  a named subsystem. Godot shell work and parity evidence alone do not transfer
  authority.
- Behavioural changes require tests. Preserve security, config, testing,
  parity, and semantic-boundary guarantees routed by the workflow and policy
  documents.
- Keep one semantic objective per PR. Separate unrelated formatting and
  toolchain migrations from product behavior where practical; use a scope
  matrix when cross-layer integration is deliberate.
- Preserve deterministic identity, parity evidence, repository sanitation, and
  explicit deferrals. Never weaken tests or silently continue into the next
  task.
- Nested `AGENTS.md` files may add narrower constraints and cannot weaken this
  dispatch.
- Partial satisfaction of acceptance criteria must not be reported as
  completion.

## Verification and completion

Run focused checks while iterating, then the applicable final gate:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Report files changed, authorities reused or extended, any routing/authority
decision, checks and results, and remaining risks or unverified areas.
