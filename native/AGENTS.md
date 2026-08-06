# Native C++ / GDExtension Dispatch

This directory contains native deterministic implementations and Godot
GDExtension adapters.

Authority is subsystem-specific.

Inherited behaviour remains provisional in native code until a completed
authority-transfer record names the transferred subsystem. Genuinely new
deterministic behaviour may establish native authority directly when it has no
predecessor and satisfies the authority-establishment protocol.

Read:

- `docs/architecture/authority_map.md` for current ownership;
- `docs/architecture/parity_protocol.md` for inherited parity evidence;
- `docs/architecture/authority_transfer_protocol.md` for inherited transfer
  and new authority establishment;
- `docs/governance/cpp_safety_policy.md` for memory and API safety;
- `docs/governance/native_tooling_ci_policy.md` for build/tooling evidence;
- the current product, parity, migration, or establishment authority routed by
  `docs/DOCUMENTATION_MAP.md`.

Rules:

- Keep deterministic core logic independent from Godot and keep the adapter
  thin; convert Godot types at the boundary.
- Do not duplicate inherited Python/reference semantics or implement rules in
  adapter glue.
- Ported inherited behaviour requires reference parity fixtures and regression
  tests.
- New deterministic behaviour requires a normative contract, named owner,
  conformance tests, compatibility rules, and an establishment record. Do not
  create a Python predecessor solely to manufacture parity.
- Native implementation ownership, successful builds, parity evidence, and
  visual correctness do not by themselves establish or transfer semantic
  authority.
- Preserve documented default/advisory and strict parity behaviour when native
  output is unavailable.
- Follow RAII and explicit ownership; no raw owning pointers, naked
  `new`/`delete`, or unjustified unsafe casts.
- Public APIs document ownership, lifetime, nullability, invariants,
  preconditions, and failure modes.
- Do not expand beyond the routed subsystem or its explicit exclusions.
