# Parity Pilot Audit and Promotion Gates

## Scope

This document audits the first subsystem parity pilot and defines gates for the
next parity slice.

It is evidence-only process governance. It does not transfer semantic
authority.

## Current pilot

- pilot document: `docs/architecture/first_subsystem_parity_pilot.md`
- harness: `tools/migration/first_subsystem_parity_pilot.py`
- fixture/test: `tests/unit/migration/test_first_subsystem_parity_pilot.py`
- native/provisional surface: `scripts/test_godot_tet4d_core.sh` and
  `native/tet4d_core/tests/plain_2d_core_tests.cpp`
- strict mode: `TET4D_STRICT_PARITY=1`
- default mode: advisory only when the native bridge/toolchain is unavailable

## Authority boundary

Python remains the semantic oracle.

Godot remains product shell, UI, rendering, presentation, diagnostics, and
input routing.

C++/GDExtension remains provisional.

Passing the first pilot does not transfer authority.

Promotion to a second parity slice is not authority transfer.

Any future authority transfer still requires
`docs/architecture/authority_transfer_protocol.md` and an explicit
`transferred` record.

## Audit findings

### Routing

- parity protocol: must route both the first pilot and this audit/gates doc
- authority transfer protocol: must link this audit so parity evidence is not
  confused with transfer records
- authority map: must keep the pilot and this audit as evidence-only process
  work
- governance router: must route both parity pilot docs and state that parity
  routing is validated
- drift map: must list the audit doc plus the first pilot harness/test surfaces
- review checklist: must require review of promotion gates before a second
  parity slice
- documentation map: must route this audit as the gate document for future
  parity slices
- project structure: should keep the pilot under `tools/migration/` until a
  second parity harness exists
- AGENTS: must route parity contributors to protocol, pilot doc, and this audit
- native AGENTS: must preserve provisional native status and strict/default
  parity behavior

### Harness placement

- current path: `tools/migration/first_subsystem_parity_pilot.py`
- accepted / needs migration: accepted for the first pilot
- reason: the pilot is migration evidence for the Godot/C++ boundary, not yet a
  standalone parity-tooling domain

Future routing:

- if two or more maintained parity harnesses exist, create `tools/parity/` and
  route it explicitly
- do not move the first pilot now for aesthetics only

### Oracle comparison

- Python oracle path: `tools/migration/first_subsystem_parity_pilot.py` via
  `python_oracle_stable_hash_text(text)`
- native/provisional output path: `scripts/test_godot_tet4d_core.sh
  --pilot-stable-hash` backed by
  `native/tet4d_core/tests/plain_2d_core_tests.cpp`
- comparison rule: exact fixture membership and exact hash equality
- exact/tolerance: exact only; no tolerance mode is allowed for this pilot

### Strict/default behaviour

- default behaviour: if the native bridge/toolchain is unavailable, the pilot
  reports an advisory and stays non-blocking
- strict behaviour: `TET4D_STRICT_PARITY=1` makes native unavailability
  blocking
- mismatch behaviour: parity mismatches are blocking in both modes once native
  output is available
- unavailable native bridge behaviour: actionable advisory/failure text must
  tell the reader to restore native tooling or enable strict mode

### Fixture quality

- deterministic: yes
- small: yes
- non-random: yes
- actionable mismatch output: required; missing cases, unexpected cases, and
  exact expected/got hash mismatches must be reported

## Promotion gates for next parity slice

A second parity slice is allowed only if:

- the first pilot remains routed from parity, governance, drift, and AGENTS
  surfaces
- the Python oracle is identified
- the native/provisional output path is identified
- the fixture set is deterministic, committed, and small
- the comparison command is documented
- default mode is advisory when the native bridge is unavailable
- strict mode fails on native unavailability and parity mismatch
- failures are actionable
- no authority transfer is claimed
- drift and project-contract validators cover the new routing surface
- governance tests cover missing routing and invalid authority claims
- full verification passes

## Allowed second-slice candidates

Allowed:

- coordinate or bounds normalization
- topology identifier normalization
- trace metadata identity or digest
- dimension label normalization
- data-only config or trace fixture identity

Forbidden:

- full topology movement
- rotation semantics
- drop or collision semantics
- lock, clear, or gameplay loop semantics
- rendering, projection, or view semantics
- endgame physics

## Decision

- first pilot accepted as evidence mechanism: yes
- dedicated `tools/parity/` migration needed now: no
- next slice allowed now: yes, but only if every promotion gate above is met
- required follow-up before next slice: route the candidate slice to this audit,
  keep Python as oracle, keep native provisional, and add validator/test
  coverage for the new surface
