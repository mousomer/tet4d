# C++ Safety Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Scope

This policy applies to native C++ and GDExtension code used by Tet4D.

It does not make C++ universally authoritative.

For inherited, untransferred subsystems, Python remains the semantic oracle and
reference authority. Native behaviour remains provisional until parity
evidence, a completed transfer record in
`docs/architecture/authority_transfer_protocol.md`, and an authority-map update
say otherwise.

Genuinely new deterministic behaviour may establish native authority directly
when it has a normative contract, conformance evidence, an establishment
record, and an authority-map update.

## Memory ownership

Rules:

- No raw owning pointers.
- No naked `new` or `delete` in project logic.
- Prefer values and RAII.
- Use `std::unique_ptr` for exclusive ownership.
- Use `std::shared_ptr` only when shared ownership is necessary and documented.
- Use references or non-owning pointers only when lifetime is externally owned
  and documented.
- Avoid pointer arithmetic.
- Avoid C-style arrays in new code except trivial fixed-size local cases.
- Avoid C-style casts.
- No `reinterpret_cast` without a written justification near the use site.
- No global mutable state unless explicitly justified.
- No detached threads.

## Godot/GDExtension boundary

Rules:

- Keep the GDExtension adapter thin.
- Keep deterministic rule logic independent of Godot headers where practical.
- Convert Godot types to domain/core types at the boundary.
- Do not expose raw internal core pointers to GDScript.
- Do not implement deterministic game rules in adapter glue.
- Stored Godot object pointers are non-owning unless explicitly documented.
- Any stored Godot pointer must document owner, lifetime, nullability, and
  invalidation condition.

## Comments and API documentation

Public native APIs must document:

- ownership;
- lifetime;
- nullability;
- invariants;
- preconditions;
- postconditions;
- failure modes;
- authority boundary where the API exposes deterministic semantics.

Comments should explain intent and invariants, not restate obvious code.

## Style and static analysis

The native style baseline is `.clang-format`. The static-analysis baseline is
`.clang-tidy`.

Native C++ tooling checks run through the governance verification path via
`tools/governance/validate_native_cpp_tooling.py`. They execute clang-format
when available and clang-tidy when a compilation database is available. Missing
optional native tools are reported as skips unless strict mode is enabled with
`TET4D_STRICT_NATIVE_TOOLS=1`.

CI readiness and strict-mode expectations are defined in
`docs/governance/native_tooling_ci_policy.md`. Passing native tooling checks is
a quality gate only; it does not transfer or establish semantic authority.

## Inherited authority transfer

A native implementation of inherited behaviour is provisional until:

1. the current reference behaviour is identified;
2. parity tests or golden traces exist;
3. the native implementation passes the comparison;
4. known exclusions and fallback are documented;
5. `docs/architecture/authority_transfer_protocol.md` contains a completed
   transfer record;
6. `docs/architecture/authority_map.md` is updated.

## New authority establishment

A genuinely new deterministic subsystem may establish native authority when:

1. an owning RDS, specification, or schema defines the behaviour;
2. deterministic and presentation boundaries are explicit;
3. native conformance tests exist;
4. persistence, replay, compatibility, and safe-failure rules are documented
   where applicable;
5. no competing truth implementation remains;
6. `docs/architecture/authority_transfer_protocol.md` contains an established
   record;
7. `docs/architecture/authority_map.md` is updated.

Do not create a Python implementation solely to manufacture an oracle for new
native behaviour.
