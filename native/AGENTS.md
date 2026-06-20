# Native C++ / GDExtension AGENTS.md

This directory contains native code for the Godot migration.

See `docs/governance/cpp_safety_policy.md` for native C++ memory-safety rules.
See `docs/architecture/parity_protocol.md` and
`docs/architecture/first_subsystem_parity_pilot.md` for parity-pilot rules.
See `docs/governance/native_tooling_ci_policy.md` for native tooling CI rules.
See `docs/architecture/authority_map.md` for semantic authority.

Rules:

- Keep deterministic rule logic independent from Godot where possible.
- Keep the GDExtension/Godot adapter thin.
- Convert Godot types to domain/core types and back.
- Do not implement game rules in adapter glue.
- Do not duplicate existing Python semantics.
- No raw owning pointers.
- No naked `new` or `delete`.
- Use RAII and explicit ownership.
- No unsafe casts without written justification.
- Public APIs must document ownership, lifetime, nullability, invariants,
  preconditions, and failure modes.
- Ported behavior requires parity tests against Python traces or equivalent
  fixtures.
