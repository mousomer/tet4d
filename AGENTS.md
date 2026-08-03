# tet4d Dispatch

tet4d is a Python-origin game and engine with Godot as the product-shell
direction. Semantic authority is subsystem-specific.

Python remains reference authority for inherited gameplay, topology, trace,
replay, configuration, and related behaviour only until the named subsystem is
transferred or retired. New capabilities without a Python predecessor may
establish authority directly in native C++, Godot, or versioned declarative
data through the documented authority-establishment process.

## Canonical authorities

- Professional product programme and phase gates:
  `docs/plans/professional_godot_game_programme.md`
- Governance and generated-maintenance policy:
  `config/project/policy_pack.json`
- Contributor workflow and verification: `docs/WORKFLOW_CODEX.md`
- Product behaviour: relevant documents under `docs/rds/`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Subsystem ownership: `docs/architecture/authority_map.md`
- Authority transfer and establishment:
  `docs/architecture/authority_transfer_protocol.md`
- Documentation and historical routing: `docs/DOCUMENTATION_MAP.md`
- Governance policy routing: `docs/governance/README.md`
- Repository-changing task boundary: `docs/governance/task_contract.md`
- Completion evidence format: `docs/governance/completion_report.md`
- Restart and staged-work handoff only: `CURRENT_STATE.md`
- Open work and deferred scope: `docs/BACKLOG.md`

## Task routing

- Narrow review: inspect the changed diff, touched tests, and the authority
  routed by `docs/DOCUMENTATION_MAP.md`.
- Product planning or phase sequencing: read
  `docs/plans/professional_godot_game_programme.md` and the relevant RDS.
- Python engine or inherited gameplay: read the architecture contract,
  relevant RDS, authority map, touched modules, and tests.
- Godot UI/product shell: also follow `godot/AGENTS.md` and the relevant
  product or presentation authority.
- Native C++/GDExtension: also follow `native/AGENTS.md`, the authority map,
  and the applicable parity, transfer, or establishment protocol.
- Topology explorer: read
  `docs/plans/topology_playground_current_authority.md`, then the relevant
  runtime, authority boundary, and tests.
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
- For inherited behaviour, preserve the current reference authority until a
  completed transfer record changes the named subsystem. Godot shell work and
  parity evidence alone do not transfer authority.
- For genuinely new behaviour, establish authority through an owning contract,
  named implementation/data owners, conformance evidence, and authority-map
  update. Do not create a Python mirror solely to manufacture an oracle.
- Godot may own product and presentation semantics directly, but must not
  silently redefine inherited gameplay, topology, scoring, replay, or trace
  behaviour.
- Behavioural changes require tests. Preserve security, config, testing,
  parity, and semantic-boundary guarantees routed by the workflow and policy
  documents.
- Keep one semantic objective per PR. Separate unrelated formatting and
  toolchain migrations from product behavior where practical; use a scope
  matrix when cross-layer integration is deliberate.
- Preserve deterministic identity, parity/conformance evidence, repository
  sanitation, and explicit deferrals. Never weaken tests or silently continue
  into the next task.
- All GitHub writes for this repository, including pushes, pull requests,
  releases, and metadata edits, must target the canonical `origin` repository
  and authenticate as that repository's owner. Never use an unrelated personal
  or organization account. Verify the active GitHub and transport identity
  locally before writing; stop if it cannot be confirmed. Do not publish the
  checked account name, local identity-file path, token details, private email,
  or machine-specific paths in tracked files or GitHub metadata.
- Nested `AGENTS.md` files may add narrower constraints and cannot weaken this
  dispatch.
- Partial satisfaction of acceptance criteria must not be reported as
  completion.

## Verification and completion

Run focused checks while iterating, then the applicable final gate:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Report files changed, authorities reused/transferred/established, any routing
or authority decision, checks and results, and remaining risks or unverified
areas.
