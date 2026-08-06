# tet4d Dispatch

tet4d is a Python-origin game and engine with Godot as the product shell and
subsystem-specific semantic authority.

## Routing bootstrap

- Machine-readable task types, workflow modifiers, verification requirements,
  and authority pointers: `config/project/policy_pack.json` under
  `authority_model` and `codex_routing`.
- Detailed routing and verification algorithm: `docs/WORKFLOW_CODEX.md`.
- Product programme: `docs/plans/professional_godot_game_programme.md`.
- Product behaviour: relevant `docs/rds/*`.
- Architecture and subsystem ownership: `docs/ARCHITECTURE_CONTRACT.md` and
  `docs/architecture/authority_map.md`.
- Authority transfer or establishment:
  `docs/architecture/authority_transfer_protocol.md`.
- Active work and explicit deferrals: `docs/BACKLOG.md`.
- Restart or staged handoff only: `CURRENT_STATE.md`.

Select exactly one primary task type. Treat `review_only`, `staged_handoff`,
`cross_layer`, and `verification_failure` as workflow modifiers, never as task
types. Derive verification from the actual diff, claims, and authority
boundaries; compose required evidence by union. A repository-changing task may
not resolve to no verification. Ambiguity broadens verification.

Follow `godot/AGENTS.md` or `native/AGENTS.md` when those trees are in scope.
Nested dispatch files may narrow this contract and may not weaken it.

## Universal invariants

- Inspect current code, tests, and routed authorities before editing; reuse
  existing implementations and policy before adding new ones.
- Python remains the semantic oracle only for inherited, untransferred
  behaviour. Godot or C++/GDExtension work, visual plausibility, and parity
  evidence alone do not transfer authority.
- New behaviour may establish authority directly only through a normative
  contract, named owners, conformance evidence, and authority-map update.
- Keep one semantic objective per PR. Deliberate cross-layer work requires a
  scope matrix and provider-consumer integration evidence.
- Behavioural changes require tests. Never weaken tests, deterministic identity,
  replay/trace compatibility, sanitation, or explicit-deferral discipline.
- All GitHub writes must target canonical `origin` under the repository owner;
  do not publish credentials, private identity data, or machine-local paths.
- Partial acceptance is not completion, and work must not silently continue
  into another task or stage.

## Verification and completion

Use focused checks selected by `docs/WORKFLOW_CODEX.md`; apply the full gate
when an authority, broad shared-infrastructure change, uncertainty, reviewer, or
release claim requires it:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Report task type, modifiers, affected layers, claims, authorities, required and
omitted checks with rationale, authority effects, risks, and unverified areas.
