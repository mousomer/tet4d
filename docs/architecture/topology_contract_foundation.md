# Shared Topology Contract Foundation

Status: active cross-language contract foundation

## Purpose and authority

`contracts/topology_contract_v1.json` is the language-neutral authority for
topology scalar acceptance shared by Python and provisional native C++.
`tools/codegen/generate_topology_contract.py` validates that source and
deterministically generates:

- `src/tet4d/generated/topology_contract_v1.py`;
- `native/tet4d_core/include/tet4d_core/generated/topology_contract_v1.hpp`;
- the scalar limits in `config/schema/topology_contract.schema.json`.

Shared topology validity, canonicalization, identity, and transport acceptance
values must originate from the versioned language-neutral topology contract.
Python remains the topology semantic oracle. Generated C++ constants establish
shared metadata and acceptance limits; they do not transfer topology authority
or implement native transport.

## Contract values and fingerprint

Version 1 defines ranks 2 through 4, axis lengths 1 through 1,000,000, maximum
indexable volume 9,223,372,036,854,775,807, axes `x/y/z/w`, signed transforms
`-1/+1`, boundary sides `-/+`, and unit movement deltas `-1/+1`.

The contract fingerprint is lowercase SHA-256 over compact UTF-8 JSON with
object keys sorted recursively. Source whitespace and original key order do not
affect it. Generated files are checked in for normal Python and native builds;
`python tools/codegen/generate_topology_contract.py --check` detects missing,
manually edited, or stale bindings without modifying the worktree.

## Scalar acceptance

Canonical and transport-facing integer fields require exact JSON integer
semantics. Python booleans are rejected even though Python equality and
inheritance can otherwise make `True` resemble `1`. Floats, numeric strings,
and other coercible values are also rejected before normalization. String
fields are type-checked before trimming or case normalization.

Semantic limits describe interoperable topology documents. UI, build, tooling,
performance, and resource-budget configuration may remain component-specific
provided it cannot redefine shared topology semantics.

## Included and deferred fields

The shared source covers contract version, rank, board-axis lengths, indexable
volume, axis names and indices, transform signs, boundary sides, and unit
movement deltas. Transform permutation entries use the same exact-integer rule
and their dimension-dependent bounds remain enforced by the canonical parser.
Coordinates are not serialized by topology contract v1; strict resolver query
input is deliberately excluded from this foundation and remains a later
transport-boundary responsibility.

Legacy persistence adapters, editor-input recovery, arbitrary constructor
hardening, resolver-wide hardening, full native topology transport,
topology-aware gameplay, and Godot topology UI remain deferred. Native
topology transport depends on this foundation and must consume the generated
constants rather than restating them.
