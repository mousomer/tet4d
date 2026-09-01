# Engineering

Canonical owner: general coding, structure, dependency use, comments, and
public-interface discipline.

## Core rules

- Inspect the current implementation, tests, and owning design authority before
  editing. Search for existing helpers, libraries, policies, and validators.
- Preserve working behaviour unless the task explicitly changes it. Prefer a
  small extension, adapter, or reuse over a parallel implementation.
- Keep one truth owner per subsystem. Adapters translate; authorities decide.
- Keep functions cohesive, nesting shallow, ownership clear, and failures
  explicit and actionable. Do not optimize for compressed line counts.
- Do not break a public or cross-layer interface without a migration plan,
  updated call sites, compatibility decisions, and tests.
- Comments explain intent, invariants, ownership, authority boundaries, failure
  modes, and non-obvious choices; they do not narrate syntax.
- Generated files are outputs. Change their source, schema, contract, or
  generator and then regenerate them.
- Suppressions are narrow, reasoned debt. Never use them to hide a broad
  violation or weaken a test.
- Record open technical debt in `docs/BACKLOG.md` with its affected owner,
  practical impact, resolution trigger, and intended disposition. Do not create
  a parallel debt register or preserve closed chronology in active governance.

Prefer coherent localized patches over fragmented edits. Use a patch with
fresh context for localized changes and one deterministic scripted rewrite for
broad mechanical changes. After one rejected patch attempt on a file, switch
methods instead of retrying stale context. Every write must preserve UTF-8
without a byte-order mark and avoid literal escape-text artifacts.

## Reuse and dependencies

Use this decision order for generic functionality:

1. language built-ins and standard library;
2. an existing repository utility or dependency;
3. a maintained third-party package with acceptable correctness, platform,
   licensing, size, and security properties;
4. a minimal custom implementation with a documented mismatch or constraint.

Before adding a reusable helper, search the codebase and
`docs/architecture/utility_index.md`. Update that index when ownership of a
shared utility changes. Do not add a large dependency for trivial logic or
create local mini-frameworks, parsers, serializers, or config loaders where an
approved implementation already exists.

## Behaviour and architecture

Python remains reference authority only for inherited, untransferred
behaviour. Godot presentation work and native parity evidence do not transfer
semantic ownership. A genuinely new capability may establish authority
directly only through a normative contract, named owners, conformance evidence,
compatibility rules, an establishment record, and an authority-map update.

Verification for behaviour changes and bug fixes is owned by
`VERIFICATION.md`. Use `CONFIG_AND_GENERATED_DATA.md` for constants and
generated outputs, and `NATIVE_AND_PLATFORM.md` for Godot/native boundaries.
