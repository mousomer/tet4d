# Native and Platform

Canonical owner: native C++ safety and tooling, the Godot/native boundary, and
platform-facing implementation discipline. Product semantics remain with the
owning RDS, architecture contract, subsystem authority map, and explicit
transfer or establishment records under
`docs/architecture/authority_transfer_protocol.md`.

## Semantic boundary

Classify work before implementation:

- Inherited behaviour has an accepted reference. Reuse or port it without
  silent change, provide parity/conformance evidence, preserve fallback and
  compatibility, and complete an authority transfer before naming a new owner.
- New behaviour has no accepted predecessor. Define it in a normative contract,
  name deterministic, presentation, and data owners, provide conformance and
  compatibility evidence, and establish authority explicitly. Do not create a
  Python mirror solely to manufacture an oracle.

Godot owns the product shell and presentation: scenes, menus, input routing,
rendering, camera, animation, diagnostics, accessibility, guidance, and
Explorer interaction. It may display, animate, request, and compose
authoritative state, but must not independently compute inherited topology,
movement, collision, gravity, rotation legality, scoring, trace, or replay
truth.

Keep deterministic core logic independent from Godot headers where practical.
Keep GDExtension adapters thin, convert Godot/domain types at the boundary, and
never hide deterministic rules in adapter glue.

## C++ ownership and API safety

- Prefer values and automatic storage; then `std::unique_ptr`; use
  `std::shared_ptr` only for genuine shared lifetime and `std::weak_ptr` to
  break cycles. Raw pointers and references are non-owning by default.
- No raw owning pointers, naked `new`/`delete`, detached threads, unexplained
  global mutable state, C-style casts, or exposed internal core pointers.
- Avoid pointer arithmetic and new C-style arrays except trivial fixed-size
  local cases. `reinterpret_cast` requires a nearby written justification.
- Resource owners need deterministic cleanup and safe move/copy semantics.
  Prefer RAII for files, locks, threads, handles, and Godot/native resources.
- Stored Godot object pointers are non-owning unless explicitly documented.
  State owner, lifetime, nullability, invalidation condition, and access rules.
- Public APIs document ownership, lifetime, nullability, invariants,
  preconditions, postconditions, failure modes, and semantic authority boundary.

## Native tooling modes

`.clang-format` and `.clang-tidy` are the baselines.
`tools/governance/validate_native_cpp_tooling.py` discovers project-owned files
deterministically and excludes vendored code.

Default local mode is advisory: run available tools and report a missing tool
or compilation database as a skip. `TET4D_STRICT_NATIVE_TOOLS=1` requires
clang-format for native sources and clang-tidy plus a supported
`compile_commands.json` for implementation files. CI may use advisory mode only
while the backlog explicitly records the reproducibility gap.
Tooling success is a quality gate, never parity or semantic authority.

Native changes require applicable build, unit, parity/conformance, adapter, and
product-shell evidence under `VERIFICATION.md`. Platform and release evidence
remain separate: a successful local build or package structure check does not
claim runtime acceptance on another platform. Platform evidence carries explicit
platform identity, and a hosted export, cross-compile, or final link proves only
that boundary — never physical-device acceptance and never another platform.
