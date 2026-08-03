# tet4d Authority Transfer and Establishment Protocol

This document defines two distinct operations:

1. **authority transfer** for inherited behaviour that already has an owner;
2. **authority establishment** for genuinely new behaviour with no predecessor.

This document does not move or establish authority by itself.

## Relationship to other documents

- `docs/architecture/authority_map.md` records current subsystem authority.
- `docs/architecture/parity_protocol.md` defines reusable parity evidence.
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md` defines the
  reusable promotion gate for inherited parity work. The pilot and its audit
  are evidence-only pilot material; they are not transfer records.
- `docs/architecture/parity_evidence_package_review.md` reviews parity evidence
  packaging. Evidence-package reviews are not transfer records.
- `docs/architecture/trace_schema_version_normalization_parity.md` records a
  specific inherited parity result. It is not a transfer record.
- other promotion-gate and evidence-review documents provide supporting
  evidence only.
- `docs/plans/professional_godot_game_programme.md` defines the product sequence
  that creates new authority needs.
- `tools/governance/validate_authority_transfer.py` validates recorded claims
  where supported by the current schema.

Evidence packages, parity reviews, implementation success, and product use do
not change authority without the required record and authority-map update.

## 1. Authority transfer

Authority transfer applies when another implementation replaces behaviour that
already has an accepted owner.

The common current case is movement from an inherited Python-reference
subsystem to native C++.

### Transfer rule

A subsystem may receive transferred authority only when:

1. the current authority is named;
2. the exact observable behaviour is scoped;
3. relevant parity or conformance evidence exists;
4. comparison commands are documented;
5. known exclusions are documented;
6. the fallback/reversion path is documented;
7. the candidate does not depend on duplicate semantic glue elsewhere;
8. `docs/architecture/authority_map.md` is updated;
9. the transfer record status is `transferred`;
10. required governance validation passes.

Parity is necessary for inherited behaviour but is not sufficient by itself.

### Transfer statuses

Allowed transfer statuses:

- `candidate`
- `blocked`
- `ready`
- `transferred`
- `retired`

Only `transferred` changes authority.

### Required transfer record fields

| Field | Required | Meaning |
| --- | ---: | --- |
| `id` | yes | Stable transfer ID |
| `operation` | yes | `transfer` |
| `subsystem` | yes | Exact semantic subsystem |
| `current_authority` | yes | Accepted owner before transfer |
| `candidate_authority` | yes | Proposed new owner |
| `scope` | yes | Exact behaviour covered |
| `reference_implementation` | yes | Existing implementation or contract used as reference |
| `golden_fixtures` | yes | Traces, fixtures, or equivalent conformance evidence |
| `comparison_command` | yes | Command that compares candidate with reference |
| `known_exclusions` | yes | Behaviour not covered |
| `fallback_path` | yes | Reversion or compatibility path |
| `authority_map_update` | yes | Required map change |
| `validation` | yes | Required validation command(s) |
| `status` | yes | Transfer status |
| `notes` | no | Additional context |

The field is named `reference_implementation`, not `python_oracle`, because an
inherited subsystem may eventually transfer from an owner other than Python.

## 2. Authority establishment

Authority establishment applies when a new capability has no accepted
predecessor.

Examples include:

- new Godot 4D presentation-basis state;
- Explorer Y/slice basis exchange;
- new Hold gameplay if no existing authoritative implementation is found;
- challenge predicates and campaign rules;
- future native physics beyond the inherited explosion model.

A new capability must not be implemented in Python solely to create an oracle.

### Establishment rule

A new subsystem may receive established authority only when:

1. the capability is demonstrably new rather than an undocumented rewrite of
   inherited behaviour;
2. a normative RDS, specification, schema, or versioned contract exists;
3. the implementation owner is named;
4. any declarative-data owner is named separately;
5. deterministic and presentation boundaries are explicit;
6. conformance tests exist where the behaviour is deterministic;
7. persistence, replay, compatibility, and versioning rules are documented
   where applicable;
8. fallback or safe-failure behaviour is documented where relevant;
9. no competing truth implementation remains;
10. `docs/architecture/authority_map.md` is updated;
11. the establishment record status is `established`;
12. required governance validation passes.

Authority establishment does not require Python parity when no Python behaviour
exists.

### Establishment statuses

Allowed establishment statuses:

- `proposed`
- `blocked`
- `ready`
- `established`
- `retired`

Only `established` creates authority.

### Required establishment record fields

| Field | Required | Meaning |
| --- | ---: | --- |
| `id` | yes | Stable establishment ID |
| `operation` | yes | `establishment` |
| `subsystem` | yes | Exact new subsystem |
| `normative_contract` | yes | Owning RDS, specification, or schema |
| `implementation_authority` | yes | Code/runtime owner |
| `data_authority` | conditional | Versioned data owner where separate |
| `scope` | yes | Exact behaviour covered |
| `semantic_boundaries` | yes | Deterministic versus presentation ownership |
| `conformance_evidence` | yes | Tests, fixtures, validators, or review evidence |
| `compatibility_rules` | yes | Persistence/replay/versioning impact or `none` |
| `known_exclusions` | yes | Behaviour not covered |
| `safe_failure_or_fallback` | yes | Failure/recovery policy or `not applicable` |
| `authority_map_update` | yes | Required map change |
| `validation` | yes | Required validation command(s) |
| `status` | yes | Establishment status |
| `notes` | no | Additional context |

## 3. Mixed subsystems

A product feature may combine several authorities.

For example, a challenge feature may use:

- versioned declarative data for challenge content;
- native C++ for deterministic success predicates;
- Godot for instructions, hints, progress, and campaign navigation;
- inherited gameplay semantics that remain Python-reference until transferred.

Do not force such a feature into one monolithic owner.

Record the boundaries explicitly.

## 4. Presentation authority

New presentation behaviour may be Godot-authoritative from inception when it
does not redefine inherited deterministic semantics.

Examples include:

- camera orientation;
- 4D view/presentation basis;
- slice layout and labels;
- transition animation;
- challenge UI and hints;
- Explorer controls and diagnostics.

Where presentation uses shared exact mathematics, a native deterministic
utility may own the transform while Godot owns user-facing state and animation.

## 5. Transfer and establishment records

No authority changes are active unless a record below has the terminal status
for its operation and the authority map agrees.

### Active transfer records

| id | operation | subsystem | current_authority | candidate_authority | scope | reference_implementation | golden_fixtures | comparison_command | known_exclusions | fallback_path | authority_map_update | validation | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### Active establishment records

| id | operation | subsystem | normative_contract | implementation_authority | data_authority | scope | semantic_boundaries | conformance_evidence | compatibility_rules | known_exclusions | safe_failure_or_fallback | authority_map_update | validation | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 6. Deferred candidates

Prose candidates do not change authority.

Potential inherited transfer candidates include:

- bounded board/piece state transition;
- bounded movement and rotation legality;
- gravity and drop/lock progression;
- scoring and clear transitions;
- topology resolution;
- trace/replay normalization helpers;
- existing explosion stepping.

Potential new establishment candidates include:

- Hold gameplay state;
- Godot 4D view-basis state;
- Explorer complete camera/basis controls;
- challenge content schema;
- deterministic challenge predicates;
- future physics beyond the inherited explosion model.

Do not transfer or establish the full gameplay loop, full topology system,
Explorer, or challenge campaign as one undifferentiated subsystem.

## 7. Forbidden claims

Do not:

- claim authority from parity evidence alone;
- claim universal Python authority over a new capability;
- create a Python mirror solely to satisfy an obsolete oracle rule;
- label runtime implementation ownership as semantic authority without the
  appropriate record;
- establish new native authority without a normative contract and tests;
- let Godot presentation silently redefine inherited gameplay or topology
  semantics;
- leave the authority map inconsistent with a terminal record.
