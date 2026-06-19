# General Programming Policy

## Scope

This policy applies to source code, scripts, tests, validators, build helpers,
migration tools, and generated-file producers in any project that adopts this
bundle.

It does not define project-specific domain authority.

## Rules

### Preserve existing behaviour

Do not rewrite working code unless the task explicitly asks for a refactor,
replacement, or semantic change.

Prefer extending, wrapping, or reusing existing functions over replacing them.

### Search first

Before adding helpers, utilities, parsers, config readers, path walkers,
subprocess wrappers, trace readers, serializers, validators, or adapters, search
for existing implementations.

### Single authority

Do not create parallel truth. Every subsystem should have a clear authority.
Adapters route; authorities decide.

### No secrets or local paths

Do not commit secrets, credentials, private tokens, private URLs, local absolute
user paths, or machine-specific configuration.

### No nontrivial magic numbers

Constants that control behaviour, thresholds, timing, layout, scoring,
diagnostics, or semantics should live in the project's standard config or
constants authority.

### Generated files

Generated files are outputs, not hand-authored authority. Update the generator,
source config, schema, or contract first.

### Determinism

Tests, traces, exports, validators, generated docs, and generated bundles should
be deterministic unless explicitly marked otherwise.

### Meaningful tests

Tests should assert behaviour, invariants, regressions, error handling, or
parity. Do not add low-value tests merely to increase counts or coverage.

### Comments

Comments should explain intent, invariants, ownership, failure modes, and
non-obvious constraints. Do not narrate obvious syntax.

### Public interfaces

Do not break public or cross-layer APIs without a migration plan, tests, and
call-site updates.

### Failure modes

Tooling, scripts, validators, and public APIs should fail explicitly with
actionable messages.

### Maintainability

Keep functions cohesive, avoid giant files, avoid deep nesting, and prefer clear
ownership over clever abstraction.

### Suppressions

Suppressions are localized debt. They require a narrow reason and should not
hide broad policy violations.
