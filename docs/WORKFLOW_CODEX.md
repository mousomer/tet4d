# Workflow For Codex And Contributors

This document is the detailed human-readable workflow for applying
`config/project/policy_pack.json`. The root `AGENTS.md` is only a dispatch.

## Workflow authority

- Machine-readable governance authority: `config/project/policy_pack.json`
- Contributor dispatch: `AGENTS.md`
- Documentation ownership and history routing: `docs/DOCUMENTATION_MAP.md`
- Governance router: `docs/governance/README.md`
- Restart and staged-work handoff only: `CURRENT_STATE.md`
- Active backlog and deferred scope: `docs/BACKLOG.md`
- Product behaviour: relevant `docs/rds/*`
- Architecture boundaries: `docs/ARCHITECTURE_CONTRACT.md`
- Migration ownership: `docs/architecture/authority_map.md`

## Source-of-truth precedence

1. Newer task instructions.
2. `config/project/policy_pack.json` for governance, validation, manifest
   contracts, and generated-maintenance inputs.
3. The owning domain authority or active specification routed by
   `docs/DOCUMENTATION_MAP.md`.
4. Relevant `docs/rds/*` for durable product behaviour.
5. `docs/ARCHITECTURE_CONTRACT.md` and
   `docs/architecture/authority_map.md` for code and migration boundaries.
6. This workflow for contributor process.
7. `CURRENT_STATE.md` and `docs/BACKLOG.md` for applicable handoff and open
   work, never as replacements for the authorities above.

When authorities disagree, follow the higher-precedence source and update or
route the stale lower-precedence text in the same change.

## Common preconditions

Before editing:

1. Read `AGENTS.md`, the touched files/tests, and only the authorities routed
   for the task.
2. Inspect current code and search for existing implementations, helpers,
   utilities, policies, and validators. Do not operate on guessed repo state.
3. For restructuring or behaviour changes, state a short plan and explicit
   acceptance criteria, then compare the proposal with the owning RDS,
   architecture document, ADR, or equivalent design source.
4. Authority files must be tracked in Git; untracked local copies do not
   satisfy the contract.
5. Identify focused verification before editing and broaden it only when the
   change proves cross-cutting.

`CURRENT_STATE.md` is required only for staged migrations, restart/handoff,
architecture restructuring, active multi-batch work, tasks whose correctness
depends on the current project phase, or when another authority routes there.
Ordinary isolated fixes, tests, documentation corrections, narrow reviews, and
narrow implementation changes do not load it by default.

Read the full policy pack only for governance, validation, generated
maintenance documents, policy-backed tooling, manifest contracts, or validator
failures that require policy interpretation. Structured enforcement data is not
routine implementation context. Do not split the pack without concrete
maintenance evidence and corresponding schema, validator, generator,
documentation, and test updates.

## GitHub publication identity

Tet4D is published solely through the owner of the canonical `origin`
repository. Before any push, pull-request mutation, release, or other GitHub
write, verify locally that the target is `origin` and that the active transport
or CLI identity matches its owner. Never use an unrelated personal or
organization account. If the identity is ambiguous or does not match, stop
before writing.

The verification result is a local safety check, not public evidence. Do not
copy unrelated account identifiers, local credential or identity paths, token
details, private email addresses, or machine-specific paths into tracked files,
PR descriptions, issues, comments, or other public GitHub metadata.

## Machine-readable task routing and composable verification

`config/project/policy_pack.json.codex_routing` defines seven stable primary
task types, four workflow modifiers, and twelve verification requirements.
Codex selects exactly one primary task type; modifiers describe execution
context and never replace subsystem ownership.

| Task type | Primary scope | Typical requirements |
| --- | --- | --- |
| `product_planning` | programme, phase gates, backlog, product scope | `documentation` |
| `python_reference_engine` | inherited Python gameplay, replay, trace, configuration | `python`, `deterministic` |
| `godot_product_shell` | Godot UI, controls, rendering, accessibility | `godot` |
| `native_deterministic_core` | C++, GDExtension, deterministic native contracts | `native`, `deterministic` |
| `topology_and_explorer` | topology rules, transport, Explorer interaction | owner-dependent plus `deterministic` where semantic |
| `governance_and_tooling` | policy, validators, generators, CI-routing contracts | `governance_structure` |
| `packaging_and_release` | installers, exports, platform release work | `packaging`, `platform` for executable changes |

Workflow modifiers are `review_only`, `staged_handoff`, `cross_layer`, and
`verification_failure`. `cross_layer` requires an affected-layer list, scope
matrix, provider and consumer checks, and `integration` evidence.

Verification requirements are composable evidence sets, not a hierarchy:
`documentation`, `governance_structure`, `python`, `godot`, `native`,
`deterministic`, `parity_or_conformance`, `integration`, `human_visual`,
`packaging`, `platform`, and `release_acceptance`.

Apply this selection algorithm:

1. Select one primary task type and applicable workflow modifiers.
2. Identify affected layers and the claims made by the change.
3. Load the task type's typical requirements as heuristics.
4. Remove only requirements demonstrably inapplicable to the actual diff, and
   record the reason for every omission.
5. Add requirements implied by changed behaviour, authority boundaries,
   compatibility obligations, modifiers, and policy.
6. Compose the final requirement set by union; no category supersedes another.
7. Use `requires_full_repository_gate=true` when an authority, broad shared
   infrastructure, material uncertainty, reviewer, or release claim requires it.

`review_only` is a modifier, not a verification requirement. It is valid only
when tracked repository state is unchanged and resolves to an empty requirement
set. Once implementation starts, remove `review_only`, reclassify the task, and
produce a non-empty requirement set. Repository-changing work can never resolve
to no verification.

A prose-only packaging edit may therefore select `documentation` without
`packaging` or `platform`, provided the completion report explains why those
typical requirements were inapplicable. A native query consumed by Godot uses
one primary owner plus `cross_layer`, and composes `native`, `deterministic`,
`parity_or_conformance`, `integration`, and `godot` as applicable.

The completion report must state: task type, modifiers, repository-change
status, affected layers, claims, verification requirements, authorities,
checks run, typical checks omitted with rationale, full-gate decision, scope
matrix, authority effects, remaining risks, and unverified areas.


### Machine resolver

Use the policy-backed resolver to turn a task declaration into a stable
verification decision and completion-report skeleton:

```bash
python tools/governance/resolve_codex_verification.py request.json --format json
python tools/governance/resolve_codex_verification.py request.json --format markdown
```

The request records one primary task type, modifiers, repository-change status,
affected layers, claims with any explicit evidence obligations, additional
requirements, justified omissions of typical requirements, and the full-gate
override. The resolver loads `policy_pack.json`; callers must not copy the task
or requirement inventories into a second configuration.

The resolver enforces these invariants:

- `review_only` requires `repository_changed=false`, no executable evidence
  requirements, and no full gate;
- repository-changing work requires affected layers, at least one claim, and a
  non-empty verification set;
- `cross_layer` requires at least two affected layers, adds `integration`, and
  emits a scope matrix;
- omitted typical requirements need a non-empty rationale and may not be
  reintroduced by the actual layers or claims;
- deterministic, integration, platform, and release obligations remain
  independent members of the union.

Resolver output selects evidence obligations; it does not claim that checks
have passed. Completion reports must populate checks, authority effects,
remaining risks, and unverified areas with actual final evidence.

## Stable change classes

Use capability classes for current routing. Stage numbers may identify
historical evidence, but they do not define universal workflow.

| Change class | Primary authority | Expected verification | Common forbidden scope | Likely manual acceptance |
| --- | --- | --- | --- | --- |
| Documentation or philosophy | documentation map and owning document/RDS | docs, links, governance validators | runtime or semantic changes | usually none |
| Shell, menu, or UI | menu/product RDS, editing guide, or Godot shell authority | focused UI/input/layout tests | gameplay or topology truth in UI code | real-window navigation when behavior is visible |
| Visual design | visual-system authority, theme/config owner, accessibility contract | theme/UI/headless, focus/scale, deterministic identity checks | gameplay, topology, replay, or native semantics | required for subjective design acceptance |
| Gameplay semantics | relevant RDS, Python oracle, architecture contract | focused engine tests, deterministic traces, parity | implicit authority transfer or presentation-only truth | representative play when routed |
| Topology semantics | topology authority, Python profile/resolver, fixtures | topology invariants, trace/endgame/explosion coverage, parity | UI-owned topology truth or silent normalization | representative explorer/play cases when behavior changes |
| Native core | native rules, authority map, safety/tooling policy | native build/tests, selected parity, adapter smoke | unrecorded semantic ownership | product shell only when exposed |
| Migration or parity | parity protocol, selected subsystem authority, fixtures | default/strict comparison, synthetic merge when required | adjacent slices or implicit transfer | only for exposed product surfaces |
| Replay and trace | replay/trace RDS, schema, Python oracle | strict load/round-trip, golden drift, parity | silent schema or event-semantic change | replay usability when presentation changes |
| Packaging or release | packaging RDS and release checklist | packaging tests, sanitation, platform checks | product semantics and unrelated cleanup | installer/launch checks |
| Governance | policy pack, governance router, affected validators/generators | governance/docs tests, generation checks, sanitation, full gate | runtime, UI, gameplay, toolchain, or formatting changes | none unless the governance changes a human workflow |

## Task and PR contract

Repository-changing work starts from
`docs/governance/task_contract.md`. The contract records the objective,
authority, allowed and forbidden paths, required changes, acceptance criteria,
automated/manual verification, documentation updates, and explicit deferrals.

- Keep one semantic objective per PR.
- Separate unrelated formatting from behavioral work.
- Separate toolchain migrations from product behavior where practical.
- Deliberately cross-layer integration requires a scope matrix explaining why
  each layer must change and how it is verified.
- Do not weaken, delete, or silently redefine tests to fit implementation.
- Do not continue into the next task, stage, or deferral without a new
  contract and branch.
- A branch or draft PR is not completion.

Use `docs/governance/completion_report.md` for final handoff. Distinguish
implemented, automatically verified, manually inspected, human accepted, and
merged states.

## Boundary model

- Machine-readable policy data belongs in `config/project/policy_pack.json`.
- `tools/governance/validate_project_contracts.py` owns validation procedure only.
  It may interpret pack data and detect drift; it must not become a second
  policy inventory.
- `tools/governance/generate_maintenance_docs.py` owns rendering procedure only.
  Generated inputs belong in the policy pack.
- `docs/WORKFLOW_CODEX.md` owns human workflow, not product behaviour.
- `CURRENT_STATE.md` owns restart and staged-work handoff, not universal
  workflow, product policy, or historical ledgers.
- `docs/BACKLOG.md` owns open work and current change footprint.
- `docs/PROJECT_STRUCTURE.md` owns generated structure and source-of-truth
  snapshots.

## Implementation workflow

1. Prefer existing helpers and APIs over local reinvention.
2. Identify the owning config before adding a repo-owned runtime constant.
3. Keep staged migrations additive: add the new path, route one flow, verify,
   then remove superseded paths.
4. Update relevant design documentation before finalizing implementation.
   Behaviour changes update tests and the owning RDS; boundary changes update
   architecture docs; scope changes update `docs/BACKLOG.md`.
5. Update `CURRENT_STATE.md` only when restart, phase, staged, or multi-batch
   handoff information changed. Do not add generic workflow rules there.
6. Never treat partial progress as completion. Every stated acceptance
   criterion must be explicitly satisfied or reported as unsatisfied.
7. For substantial non-feature refactors, compare formatted production diff
   size with the base revision. When multiline formatting materially distorts
   that comparison, use Python AST statement count as secondary evidence.
   These are review signals, not quotas: do not compress expressions, calls,
   or literals merely to improve either metric.

For long-lived branches or pre-merge acceptance, branch-local verification may
be insufficient. When required by the task, test a non-destructive synthetic
merge against the current target and record both tested SHAs.

## Edit and file safety

1. Read the exact current file before editing.
2. Use localized patches with fresh context; use a deterministic rewrite for a
   broad document or generated file rather than repeated drifting patches.
3. After a rejected patch attempt on a file, switch method instead of retrying
   broad patches.
4. Preserve UTF-8 without BOM and avoid literal escape-text artifacts.
5. After a non-patch source rewrite, check encoding/artifacts and run focused
   lint before broader tests.
6. Preserve user changes in a dirty worktree and avoid destructive Git or file
   operations unless explicitly authorized.
7. Never add secrets or credentials to code, config, tests, logs, prompts,
   screenshots, or documentation.

## Verification

Use the repository-managed environment: prefer `${PYTHON_BIN}`, otherwise
`${WORKSPACE_VENV}/bin/python` when set, otherwise the documented verification
scripts; prefer the current repo virtualenv interpreter when one is available.
Do not hardcode a machine-local interpreter path.

Focused iteration:

```bash
./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]
```

Governance/documentation changes:

```bash
python tools/governance/validate_project_contracts.py
python tools/governance/generate_maintenance_docs.py --check
python tools/governance/generate_configuration_reference.py --check
```

Use the selected managed interpreter in place of `python` in those examples.

Focused keybinding contract:

```bash
./scripts/check_keybinding_contract.sh
```

Primary local gate:

```bash
CODEX_MODE=1 ./scripts/verify.sh
```

CI preflight:

```bash
./scripts/ci_preflight.sh
```

Run focused checks first. Never run `./scripts/verify.sh` and
`./scripts/ci_check.sh` in parallel. Run the full local gate when the resolved
requirements or `requires_full_repository_gate` demand it; otherwise report the
selected focused checks and why unrelated lanes were inapplicable. Use quiet
output by default and increase verbosity only for diagnosis.

Godot shell-settings changes must also run:

```bash
python tools/governance/check_godot_settings_externalization.py
```

Toolchain-specific pins and canonical commands are owned by the relevant policy
pack sections and migration audits; consult them only when that toolchain is in
scope.

## Completion and handoff

Every completed change reports:

- files changed and deliberately not changed;
- existing authorities reused or extended;
- new routing or authority decisions, including an explicit “none”;
- acceptance criteria satisfied and any unsatisfied criteria;
- checks run with exact results;
- remaining risks, old paths, blockers, or unverified areas.

Staged migration handoffs additionally report files added, remaining old paths,
phase-dependent next steps, and enough branch/worktree context to resume safely.
Do not claim completion while required validators fail, references are broken,
authority is ambiguous, or acceptance criteria remain unmet.
