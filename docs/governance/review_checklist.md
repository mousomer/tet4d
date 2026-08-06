# Tet4D Review Checklist

This is the durable project review overlay. Apply only the conditional sections
that match the task contract; completed migration stages are evidence, not
universal review steps. It extends
`docs/governance/workspace_bundle/review_checklist_template.md`; routing remains
in `docs/governance/README.md`. Work starts from the task contract and ends
with `docs/governance/completion_report.md`.

Stable references: `docs/architecture/authority_map.md`,
`docs/architecture/parity_protocol.md`,
`docs/architecture/authority_transfer_protocol.md`,
`docs/governance/technical_debt_register.md`, and
`docs/governance/drift_protection_map.md`.

## Scope and task contract

- [ ] The PR has one semantic objective and explicit deferrals.
- [ ] Allowed and forbidden systems match `docs/governance/task_contract.md`.
- [ ] Deliberate cross-layer work includes a scope matrix.
- [ ] Unrelated formatting and toolchain changes are separated where practical.
- [ ] Work did not silently continue into the next task or stage.

## Authority and semantics

- [ ] Owning RDS/architecture authorities were consulted and updated when
      behaviour or boundaries changed.
- [ ] The named subsystem authority matches the authority map in
      `docs/architecture/authority_map.md`.
- [ ] For inherited, untransferred behaviour, the Python oracle/reference
      remains authoritative unless a completed transfer record changes the
      named subsystem.
- [ ] Parity evidence and known exclusions were reviewed for every inherited
      transfer claim.
- [ ] New behaviour without a predecessor has a normative contract, named
      implementation/data owners, conformance evidence, and an establishment
      record where semantic authority is claimed.
- [ ] No Python mirror was introduced solely to manufacture an oracle.
- [ ] Godot owns product/presentation behaviour only within its documented
      boundary and does not independently duplicate inherited semantic truth.
- [ ] Native implementation ownership was not confused with inherited semantic
      transfer or new authority establishment.
- [ ] Tests were not weakened, deleted, or redefined to fit implementation.

## Safety and repository hygiene

- [ ] No secrets, unsafe local paths, generated machine state, or destructive
      migration shortcuts were introduced.
- [ ] Dependency / utility reuse was reviewed before new helpers were added;
      `validate_utility_reuse` and no-reinvention findings were resolved or
      classified.
- [ ] No-reinvention policy is preserved; reuse and utility ownership remain
      explicit.
- [ ] Config/generated outputs identify their source authority and generator.
- [ ] Config-authority validator findings and suspicious hardcoded constants
      are resolved, narrowly suppressed, or recorded.
- [ ] Generated outputs were not hand-edited.
- [ ] The staged diff is intentional and passes sanitation and whitespace
      checks.

## Conditional change-class review

### Godot shell, UI, visual design, or new presentation semantics

- [ ] `godot/AGENTS.md`, accessibility, layout, and visual/product authorities
      remain satisfied.
- [ ] The Godot semantic boundary and semantic-boundary validator remain clean.
- [ ] GDScript does not duplicate inherited gameplay, topology, scoring,
      replay, or trace semantics.
- [ ] New Godot-authoritative camera, basis, animation, guidance, or challenge
      presentation behaviour is covered by an owning contract and tests/manual
      evidence.
- [ ] Focus, scaling, scrolling, input isolation, and colour-independent cues
      were verified where applicable.
- [ ] Visual plausibility was not treated as deterministic semantic
      correctness.

### Native C++ or GDExtension

- [ ] Native C++ safety rules are preserved: no raw owning pointers or naked
      `new`/`delete`; lifetime/nullability are explicit.
- [ ] Native tooling CI readiness was checked in advisory and strict modes, or
      the blocker is recorded.
- [ ] CI strict mode and `TET4D_STRICT_NATIVE_TOOLS=1` readiness are reported
      without treating tooling as parity or authority.
- [ ] GDExtension adapters remain thin.
- [ ] Inherited ports provide reference parity and do not claim authority
      without a completed transfer.
- [ ] New deterministic subsystems provide a normative contract and
      establishment evidence rather than an artificial Python predecessor.

### Gameplay, topology, replay, trace, or migration

#### Inherited parity / authority transfer

- [ ] The inherited reference implementation and deterministic fixtures/traces
      were identified.
- [ ] Applicable comparison modes, strict/default behaviour, and disagreement
      rules from `docs/architecture/parity_protocol.md` were followed.
- [ ] Topology/gameplay/replay semantics and stable identity were covered by
      focused tests.
- [ ] Further parity expansion consulted only the relevant historical evidence
      routed by the parity protocol and documentation map.
- [ ] Any transfer claim has a completed transfer record, fallback path, known
      exclusions, and authority-map update.
- [ ] Godot visual correctness was not treated as semantic parity.

#### New authority establishment

- [ ] The feature is genuinely new rather than an undocumented rewrite of
      inherited behaviour.
- [ ] A normative RDS, specification, or schema defines the behaviour.
- [ ] Implementation and data owners are named separately where applicable.
- [ ] Deterministic and presentation boundaries are explicit.
- [ ] Conformance, persistence, replay/versioning, safe-failure, and
      compatibility requirements are covered where applicable.
- [ ] Any authority claim has an `established` record and authority-map update.

### Governance or documentation

- [ ] No duplicate policy source or contradictory precedence was introduced.
- [ ] Drift protection, router reachability, validators, generators, and
      policy-pack contracts remain aligned.
- [ ] `tools/governance/validate_governance.py` and the affected focused
      validators passed.
- [ ] Historical material remains discoverable without becoming active
      instruction.
- [ ] Generated bundle changes, staging discipline, technical-debt delta, and
      advisory validator findings are reported when applicable.

## Verification and completion

- [ ] Focused tests and validators for the changed class passed.
- [ ] `git diff --check` passed.
- [ ] `./scripts/check_git_sanitation_repo.sh` passed.
- [ ] `CODEX_MODE=1 ./scripts/verify.sh` passed, or the exact blocker is
      reported.
- [ ] Manual acceptance required by the task contract is recorded separately
      from automated success.
- [ ] The final report follows `docs/governance/completion_report.md` and
      includes warnings, limitations, diffstat, commit, PR, and worktree state.
