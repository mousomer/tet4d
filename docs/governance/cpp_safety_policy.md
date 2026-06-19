# C++ Safety Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Scope

This policy applies to native C++ and GDExtension code used by the Godot
migration.

It does not make C++ the semantic authority. Python remains the semantic oracle
until parity evidence and the authority map say otherwise.

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
- Do not implement semantic game rules in adapter glue.
- Stored Godot object pointers are non-owning unless explicitly documented.
- Any stored Godot pointer must document owner, lifetime, nullability, and
  invalidation condition.

## Comments and API documentation

Public native APIs must document:

- ownership
- lifetime
- nullability
- invariants
- preconditions
- postconditions
- failure modes

Comments should explain intent and invariants, not restate obvious code.

## Style and static analysis

The native style baseline is `.clang-format`. The static-analysis baseline is
`.clang-tidy`.

Native C++ tooling checks run through the governance verification path via
`tools/governance/validate_native_cpp_tooling.py`. They execute clang-format
when available and clang-tidy when a compilation database is available. Missing
optional native tools are reported as skips unless strict mode is enabled with
`TET4D_STRICT_NATIVE_TOOLS=1`.

## Authority

A native subsystem is provisional until:

1. Python behavior is identified.
2. Parity tests or golden traces exist.
3. Native implementation passes parity checks.
4. `docs/architecture/authority_map.md` is updated.
