# Python Topology Domain Model

Status: Stage 53C implementation authority

Semantic authority: Python

Shared scalar authority: `contracts/topology_contract_v1.json`

## Boundary policy

Python topology domain constructors validate semantic types before
normalization. They do not use `int(...)`, `bool(...)`, or `str(...)` as
validation mechanisms.

Lenient parsing belongs in explicitly named source adapters. Domain objects
contain only validated topology values.

JSON canonical and native-transport inputs retain exact JSON scalar rules.
Internal domain integer fields may accept `numbers.Integral` implementations,
excluding booleans, and normalize them to built-in `int` only after validation.
Boolean fields require exact `bool`; string fields require `str` before
trimming or other normalization; supported sequences are checked element by
element before immutable tuple storage.

## Owned invariants

- dimensions use the generated minimum and maximum rank;
- boundary axes are non-negative and rank-relative where rank is known;
- sides are strings normalized to `-` or `+`;
- boundary transforms are non-empty signed permutations with matching lengths;
- gluing identifiers are non-empty strings and enabled flags are exact
  booleans;
- profiles contain only gluing descriptors for their own dimension;
- movement axes are non-negative and movement deltas use the generated unit
  values.

Canonical identity, Stage 53B transport DTO validation, resolver semantics,
gameplay/replay hashes, and Python semantic authority do not change in Stage
53C.

## Source adapters and deferrals

The explorer-profile store is a persistence adapter. Stage 53D defines its
strict current loader, named legacy-v0 adapter, structured diagnostics, and
recovery granularity in `topology_persistence_recovery.md`. Human-input parsing
likewise belongs in an explicitly named editor adapter rather than a domain
constructor.

Repository-wide Python coercion hardening is a short-term governance objective,
but it must be driven by boundary classification rather than a mechanical ban
on conversion functions.

Stage 53E will classify strict identity inputs, replay/state-hash inputs,
domain constructors, transports, persistence, human input, numerical internals,
runtime modules, migration tools, and dead paths. Stage 53F will apply targeted
corrections and drift governance from that inventory.
