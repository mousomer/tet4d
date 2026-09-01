# tet4d Dispatch

tet4d is a Python-origin game and engine with Godot as the product shell and
subsystem-specific semantic authority.

## Governance bootstrap

The machine-readable owner and route registry is
`config/project/policy_pack.json` under `authority_model` and `codex_routing`.
Human governance has exactly these canonical owners:

- `docs/governance/ENGINEERING.md`
- `docs/governance/VERIFICATION.md`
- `docs/governance/SECURITY_AND_SANITATION.md`
- `docs/governance/CONFIG_AND_GENERATED_DATA.md`
- `docs/governance/NATIVE_AND_PLATFORM.md`
- `docs/governance/CHANGE_GOVERNANCE.md`

Product behaviour lives in relevant `docs/rds/*`; architecture and subsystem
ownership live in `docs/ARCHITECTURE_CONTRACT.md` and
`docs/architecture/authority_map.md`. Authority transfer or establishment uses
`docs/architecture/authority_transfer_protocol.md`. Active work and deferrals
live in `docs/BACKLOG.md`; `CURRENT_STATE.md` is restart/handoff context only.

## Compositional routes

Select zero, one, or several matching routes:

`product_planning`, `python_reference_engine`, `godot_product_shell`,
`native_deterministic_core`, `topology_and_explorer`,
`governance_and_tooling`, `packaging_and_release`.

Routes add context and default evidence; none is primary or exclusive. Union
the selected routes, then derive final verification from the actual diff,
claims, contracts, and authority boundaries. Repository changes require
affected layers, a claim, and non-empty verification. Select an additional
route only when the actual claims, contracts, or authority boundaries make it
applicable. `review_only`, `staged_handoff`, `cross_layer`, and
`verification_failure` are workflow modifiers, not routes.

Follow `godot/AGENTS.md` or `native/AGENTS.md` when those trees are in scope.
Nested dispatch may tighten but never weaken this contract.

## Universal invariants

- Inspect current code, tests, and routed authorities before editing; search
  for existing implementations and utilities first.
- Start restructuring or behaviour work with a concise plan and acceptance
  criteria; update the owning design documentation before finalizing code.
- Python remains reference authority only for inherited, untransferred
  behaviour. Implementation, parity, or visual plausibility alone does not
  transfer authority.
- New authority requires a normative contract, named owners, conformance
  evidence, compatibility rules, an establishment record, and map update.
- Keep one semantic objective per PR. Cross-layer work needs a scope matrix and
  provider-consumer integration evidence.
- Behaviour changes require tests. Never weaken tests, deterministic identity,
  replay/trace compatibility, sanitation, or explicit deferrals.
- Update affected docs and `docs/BACKLOG.md`; update `CURRENT_STATE.md` only for
  staged/restart/handoff context.
- GitHub writes target canonical `origin` under its owner. Never publish
  secrets, private identity data, or machine-local paths.
- Partial acceptance is not completion; do not continue into another task or
  stage without separate scope.

Run focused checks from `VERIFICATION.md`; governance, authority, broad shared
infrastructure, uncertainty, reviewer, or release claims require:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

Report routes, modifiers, layers, claims, authorities, evidence, omissions and
rationale, scope matrix, authority effects, risks, and unverified areas.
