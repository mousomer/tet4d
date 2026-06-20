# tet4d Authority Transfer Protocol

This document defines how semantic authority may move from the current Python
oracle to another implementation.

Current state:

- Python remains the semantic oracle.
- Godot remains product shell, presentation, input routing, UI, diagnostics,
  and visualization.
- C++/GDExtension remains provisional until parity evidence and an explicit
  completed transfer record exist.
- The first subsystem parity pilot is evidence only and must not be recorded
  as a transferred subsystem.

This document does not transfer authority by itself.

## Relationship to other documents

- `docs/architecture/authority_map.md` defines current subsystem authority.
- `docs/architecture/parity_protocol.md` defines evidence required for parity.
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md` defines the
  reusable gate for any second parity slice.
- `docs/architecture/second_parity_slice_candidate_selection.md` records
  Stage 17 candidate selection only; selection documents are not transfer
  records.
- This document defines the additional transfer record required before
  authority changes.
- `tools/governance/validate_authority_transfer.py` validates transfer claims.

Parity-pilot evidence and promotion-gate audits are not transfer records.
Future second-slice parity evidence is also insufficient for transfer without
an explicit transfer record and authority-map update.

## Rule

Parity evidence is necessary but not sufficient.

A subsystem may become non-Python-authoritative only when:

1. the relevant parity evidence exists,
2. the comparison command is documented,
3. known exclusions are documented,
4. fallback/reversion path is documented,
5. current and new authority are named,
6. the authority map is updated,
7. the transfer record status is `transferred`,
8. governance validation passes.

## Transfer statuses

Allowed statuses:

- `candidate`
- `blocked`
- `ready`
- `transferred`
- `retired`

Definitions:

- `candidate`: proposed transfer area; no authority change.
- `blocked`: transfer cannot proceed because evidence or design is missing.
- `ready`: evidence appears sufficient, but authority has not moved.
- `transferred`: authority has moved according to the record.
- `retired`: old or superseded transfer record.

Only `transferred` changes authority.

## Required transfer record fields

| Field | Required | Meaning |
|---|---:|---|
| `id` | yes | Stable transfer ID |
| `subsystem` | yes | Semantic subsystem being transferred |
| `current_authority` | yes | Current authority before transfer |
| `candidate_authority` | yes | Proposed new authority |
| `scope` | yes | Exact behavior covered |
| `python_oracle` | yes | Python files/modules used as oracle |
| `golden_fixtures` | yes | Fixtures/traces used as evidence |
| `comparison_command` | yes | Command that compares candidate against oracle |
| `known_exclusions` | yes | Behavior not covered by transfer |
| `fallback_path` | yes | How to revert or route back to Python |
| `authority_map_update` | yes | Required authority-map update |
| `validation` | yes | Required validation command(s) |
| `status` | yes | candidate, blocked, ready, transferred, retired |
| `notes` | no | Extra context |

## Transfer records

No semantic authority transfers are active unless a row below has status
`transferred`.

| id | subsystem | current_authority | candidate_authority | scope | python_oracle | golden_fixtures | comparison_command | known_exclusions | fallback_path | authority_map_update | validation | status | notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Deferred transfer candidates

This section may list future candidates in prose only. Prose candidates do not
change authority.

Potential future candidates:

- coordinate/bounds helper
- trace metadata identity/digest
- trace parser
- topology lookup helper
- deterministic scoring helper
- first subsystem parity pilot for `stable_hash_text(text)` evidence only

Any future parity slice still needs the promotion gates in
`docs/architecture/parity_pilot_audit_and_promotion_gates.md` plus an explicit
transfer record before authority moves.

Do not list full gameplay loop, full topology engine, or rotation system as a
first transfer unless evidence already exists.
