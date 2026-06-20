# Native Tooling CI Policy

This policy is the tet4d-specific native tooling overlay. General validator
design rules remain in `docs/governance/workspace_bundle/`; native memory and
API safety rules remain in `docs/governance/cpp_safety_policy.md`.

## Authority boundary

Native tooling quality does not transfer semantic authority.

Python remains the semantic oracle for gameplay, topology, trace, rotation,
collision, movement, scoring, configuration defaults, and replay behavior until
`docs/architecture/authority_transfer_protocol.md` contains a completed
transfer record and `docs/architecture/authority_map.md` records the promoted
authority.

Godot remains the product shell, UI, rendering, input, animation, diagnostics,
and adapter host unless a documented authority transfer says otherwise.

C++/GDExtension remains a provisional port surface. Passing clang-format,
clang-tidy, or native CI readiness checks is a quality gate only; it is not
semantic parity and does not promote C++ authority.

## Tooling modes

### Local advisory mode

Local advisory mode is the default for
`tools/governance/validate_native_cpp_tooling.py`.

Requirements:

- discover project-owned native C++ files deterministically
- require the project style/static-analysis configuration files when native
  project C++ files exist
- run clang-format when it is available
- run clang-tidy only when it is available and a `compile_commands.json`
  database exists in a supported location
- report missing local tools or missing compile database as skipped/advisory
  messages, not failures

This mode keeps ordinary local validation usable on machines without native
toolchain setup.

### Local strict mode

Local strict mode is enabled with `TET4D_STRICT_NATIVE_TOOLS=1`.

Requirements:

- native C++ file discovery failures fail validation
- clang-format is required when project-owned native C++ files exist
- clang-tidy is required when project-owned native implementation files exist
- `compile_commands.json` is required before clang-tidy can run
- clang-format violations and clang-tidy diagnostics fail validation

Local strict mode is a readiness probe. It may fail until the native toolchain
and compilation database are reproducible.

### CI strict mode

CI strict mode uses the same strict behavior as
`TET4D_STRICT_NATIVE_TOOLS=1`.

CI must not enable strict native tooling until the readiness checklist below is
complete. Until then, CI may run the validator in local advisory mode so missing
clang tools or compile database do not make unrelated governance checks brittle.

## CI readiness checklist

Before strict native tooling is enabled in CI:

- clang-format is installed at a pinned or runner-documented version
- clang-tidy is installed at a pinned or runner-documented version
- native build setup reliably emits `compile_commands.json`
- the compile database points only at project-owned native files and excludes
  vendored `native/third_party/` code
- `tools/governance/validate_native_cpp_tooling.py` passes with
  `TET4D_STRICT_NATIVE_TOOLS=1`
- native C++ parity evidence remains separate from tooling quality checks
- accepted native tooling gaps in
  `docs/governance/technical_debt_register.md` are closed or updated

## Current status

Strict native tooling is deferred for CI.

The repository has native C++ sources plus `.clang-format` and `.clang-tidy`,
but a supported `compile_commands.json` is not guaranteed in normal local or CI
validation. The accepted gap is recorded as `TD-0004` in
`docs/governance/technical_debt_register.md`.
