# Native C++ / GDExtension Dispatch

This directory contains provisional native implementation for the Godot
product-shell migration. Python remains the semantic oracle unless a completed
authority-transfer record names a transferred subsystem.

Read:

- `docs/architecture/authority_map.md` for current ownership;
- `docs/architecture/parity_protocol.md` for parity implementation/evidence;
- `docs/architecture/authority_transfer_protocol.md` for authority changes;
- `docs/governance/cpp_safety_policy.md` for memory and API safety;
- `docs/governance/native_tooling_ci_policy.md` for build/tooling evidence;
- the current parity or migration authority routed by
  `docs/DOCUMENTATION_MAP.md`.

Rules:

- Keep deterministic core logic independent from Godot and keep the adapter
  thin; convert Godot types at the boundary.
- Do not duplicate Python semantics or implement rules in adapter glue.
- Ported behaviour requires Python-oracle parity fixtures and regression tests.
- Native work remains provisional until explicit authority transfer. Parity
  evidence, a successful build, and visual correctness do not transfer
  authority.
- Preserve documented default/advisory and strict parity behaviour when native
  output is unavailable.
- Follow RAII and explicit ownership; no raw owning pointers, naked
  `new`/`delete`, or unjustified unsafe casts.
- Public APIs document ownership, lifetime, nullability, invariants,
  preconditions, and failure modes.
- Do not expand beyond the routed subsystem or its explicit exclusions.
