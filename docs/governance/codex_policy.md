# Codex Policy

This policy extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

## Purpose

Codex must preserve the Python-centered authority structure while supporting
the Godot/C++ migration.

## Before editing

Codex must inspect existing files and search for existing implementations,
helpers, utilities, libraries, or policies before adding new ones.

Use searches equivalent to:

```bash
rg "<function_or_concept>" .
rg "TODO|FIXME|HACK|legacy|deprecated|governance|policy|authority|oracle|migration" .
```

For governance work, Codex must identify whether an existing document already
covers the topic and extend it instead of creating a duplicate.

Before adding a new helper, adapter, parser, config loader, trace reader,
topology helper, projection helper, subprocess wrapper, or test fixture tool,
Codex must search by concept, likely function/class name, related config key,
and subsystem name. Shared reusable helpers must be checked against
`docs/architecture/utility_index.md`.

## Review reporting

Codex tasks must use `docs/governance/review_checklist.md` for final review
coverage. When a task changes governance, migration, generated outputs, or
cross-layer behavior, the final report must include changed files, created
files, preserved areas, checks run, technical-debt delta, drift/authority
implications, and remaining risks.

Parity tasks must also report routing, authority boundary, Python oracle,
fixture evidence, comparison command, strict/default behavior, and validation
results.

Second parity slice tasks must also report the selected candidate, explicit
exclusions, Stage 18 boundary, authority boundary, routing, and validation.

Stage 18 implementation tasks must also report the committed implementation
doc, exact fixture set, comparison mode, native command, and any provisional
native fallback behavior.

## Task routing

### Python task

Examples:

- gameplay rule fix
- topology semantics
- trace generation
- existing pygame/Python behavior
- Python test update
- current implementation refactor

Read:

- root `AGENTS.md`
- existing Python governance and relevant `docs/rds/*`
- governance router
- architecture authority map
- testing policy

### Godot task

Examples:

- menu
- scene
- UI layout
- camera
- animation
- product-shell readability
- inspector/probe panel
- visual diagnostics

Read:

- root `AGENTS.md`
- `godot/AGENTS.md`
- governance router
- Godot/C++ migration policy
- authority map

### C++ / GDExtension / native task

Examples:

- native core API
- Godot adapter
- C++ test
- memory safety
- native build
- CMake/SCons/native library configuration

Read:

- root `AGENTS.md`
- local native/GDExtension `AGENTS.md`
- governance router
- Godot/C++ migration policy
- authority map
- testing policy
- config policy

### Mixed migration task

Examples:

- port Python rule to C++
- expose C++ rule to Godot
- replace replay-only behavior with real core behavior
- compare Python trace with Godot/C++ output

Read all relevant policies:

- root `AGENTS.md`
- existing Python governance
- local Godot/C++ `AGENTS.md`
- governance router
- authority map
- migration plan
- testing policy
- config policy

## No-rewrite rule

Codex must not rewrite existing functions or governance documents wholesale
unless the task explicitly asks for a rewrite.

Allowed:

- append a routing section
- add a clarification
- add cross-links
- add a small new document when no equivalent exists
- split a bloated document only if all links are preserved

Not allowed:

- delete existing governance
- move all governance under Godot
- silently replace Python authority with Godot/C++ authority
- duplicate existing policy under a new name

## Final response requirements

Codex must report:

- files changed
- files intentionally not changed
- existing governance reused
- new governance created
- conflicts found and how they were resolved
- checks run
- unresolved risks
