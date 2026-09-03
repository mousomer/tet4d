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

The product-family/platform support matrix is a controlled product-plan
contract owned structurally by `product_platform_contract` in
`config/project/policy_pack.json`. Packaging, CI, build, export, platform, or
implementation work may not add, remove, rename, or reinterpret a target
implicitly. A matrix change requires an explicit product-plan instruction,
the `product_planning` route, intentional machine-contract and owning-RDS
updates, consumer/backlog reconciliation, tests, and a PR statement naming the
added or removed cells. Missing or broken implementations do not remove a
target; experiments, workflow jobs, artifacts, and export presets do not add
one. All consumers must be verified in the same deliberate matrix change.
`transitional_mismatch` is not a general exception: its closed, grandfathered
consumer set is the machine-contract's `legacy_designer_android` and
`legacy_designer_ipados` entries only. Adding, removing, or changing one is a
product-contract change and requires the same route, RDS, backlog, test, and
PR evidence as any other matrix change.
Each product record also owns its canonical release-artifact naming token.
`ARTIFACT_SPECS` must bind each registered consumer's filename template to that
declared product identity; it may not use a different product's filename
identity. The named transitional consumers remain consumer-specific status
exceptions, not a general filename-identity bypass.

These six canonical files are the complete human governance owner set. If a
durable rule cannot fit without semantic distortion, stop and reassess the
domain model rather than adding an overlapping owner.

## Document roles and active surface

Machine governance assigns routed documents one structural role: governance,
current state, active task, planning, history, architecture, product contract,
template, or generated reference. History, plans, templates, generated
references, architecture, and product contracts never enter the default active
governance surface merely because they exist. Active routes must resolve to
tracked current files and must not enter `docs/history/`.

The registered active surface is the union of human governance and dispatch,
`config/project/policy_pack.json`, `CURRENT_STATE.md`, `docs/BACKLOG.md`, and
any explicitly registered active task record. Its binding ceiling is 2,500
physical lines. Local guards are 150 lines for root `AGENTS.md` and
`CURRENT_STATE.md`, 70 for each subtree dispatch, 300 for each canonical owner,
250 for `docs/BACKLOG.md` and any active task record, and 1,000 for the policy
pack. The canonically serialized policy pack also has an 80,000-byte hard
ceiling so line collapsing cannot hide machine-policy growth. Local compliance
never substitutes for aggregate compliance.

Current routed files must not accumulate previous, prior, earlier, or last
task, stage, work, session, completion, or task-report sections, including
plural, repeated-qualifier, date, and identifier variants. Durable current
governance must not pin volatile current suite inventories; immutable
PR/stage/run references and historical evidence remain valid.

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

Use `.github/pull_request_template.md`. A completed change reports selected
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
