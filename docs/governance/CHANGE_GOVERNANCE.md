# Change Governance

Canonical owner: task routing, change discipline, documentation lifecycle,
completion, and publication workflow.

## Authority order

Use newer explicit task instructions first. Then apply the machine-readable
governance in `config/project/policy_pack.json`, the owning product or domain
contract, relevant RDS under `docs/rds/`, architecture and subsystem authority,
these canonical governance owners, and finally applicable handoff/backlog state. When sources
conflict, follow the higher owner and update or retire the stale lower text in
the same change.

Authority transfer and authority establishment require the normative contract,
named owners, parity evidence or conformance evidence, compatibility rules,
known exclusions, fallback path, establishment record, and authority map
update defined by `docs/architecture/authority_transfer_protocol.md`.

`CURRENT_STATE.md` is restart or staged-handoff context only.
`docs/BACKLOG.md` owns open work and explicit deferrals. Completed execution
evidence is historical and becomes context only when a current owner routes to
it. Active routed documents must not accumulate completed executions as
append-only history.

## Compositional routing

Select every route matching the actual work; zero, one, or several may match:

- `product_planning`
- `python_reference_engine`
- `godot_product_shell`
- `native_deterministic_core`
- `topology_and_explorer`
- `governance_and_tooling`
- `packaging_and_release`

Route labels select additional context and default evidence. They do not assign
exclusive ownership, and no route is primary. Union the selected routes'
authorities, dispatch files, and default verification, then add obligations
from the actual diff, claims, contracts, and authority boundaries as defined by
`VERIFICATION.md`. A documentation-only task can match no subsystem route, but
any repository change must still have affected layers, a claim, and non-empty
verification.

Workflow modifiers are `review_only`, `staged_handoff`, `cross_layer`, and
`verification_failure`; they describe execution context, not subsystem
ownership.

These six canonical files are the complete human governance owner set. If a
durable rule cannot fit without semantic distortion, stop and reassess the
domain model rather than adding an overlapping owner.

## Before and during a change

1. Inspect current code, tests, and routed authorities; do not work from guessed
   state.
2. State a concise plan and acceptance criteria. Compare restructuring or
   behaviour changes with the owning RDS, architecture record, ADR, or
   equivalent design source.
3. Keep one semantic objective per PR. Record allowed and forbidden scope and
   explicit deferrals. Cross-layer work includes a provider/consumer scope
   matrix.
   Track the LOC delta and prefer net reduction for non-feature refactors.
4. Update the relevant design authority before finalizing implementation.
   Behaviour changes update tests and the owning RDS; boundary changes update
   architecture; scope/debt changes update the backlog.
5. Use additive staged migrations where feasible: add the path, route one flow,
   verify, then retire the superseded path. Do not silently continue into the
   next task or stage.
6. Preserve unrelated worktree changes, generated provenance, sanitation,
   deterministic identity, replay/trace compatibility, and explicit
   deferrals.

Update `CURRENT_STATE.md` only for restart, staged, phase-dependent,
restructuring, or multi-batch handoff information. Do not accumulate task logs,
CI diaries, or generic workflow there.

## Review, completion, and publication

Use `.github/PULL_REQUEST_TEMPLATE.md`. A completed change reports selected
routes and modifiers, affected layers, claims, authorities, required evidence,
omissions with rationale, full-gate decision, scope matrix where applicable,
files changed and deliberately untouched, authority effects, exact checks,
manual acceptance, warnings, risks, unverified areas, commit/PR state, and
worktree state.

Distinguish implemented, automatically verified, manually inspected, human
accepted, published, and merged. Partial acceptance, a branch, or a draft PR is
not completion. Do not finish while required validators fail, references are
broken, authority is ambiguous, or acceptance criteria remain unsatisfied.

Before any GitHub write, verify canonical `origin` and matching repository-owner
identity. If identity is ambiguous, stop. Never publish credentials, private
identity details, or machine-local paths.
