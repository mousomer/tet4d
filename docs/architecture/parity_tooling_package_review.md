# Parity Tooling Package Review

## Purpose

Stage 24 reviews whether parity tooling is still migration-local or now
deserves its own package/tooling namespace.

At Stage 24 review time, the maintained parity/evidence harnesses all lived
under `tools/migration/`, but they described recurring comparison contracts
rather than one-off bundle or trace-export chores. This review records the
decision that Stage 25 later applies.

This review does not move files.
This review does not add parity logic.
This review does not change gameplay, topology, trace semantics, Godot, or
native code.

## Current Parity Inventory

| Stage | Surface | Current file path | Fixture path | Test path | Purpose | Current character |
| --- | --- | --- | --- | --- | --- | --- |
| 15 | First subsystem parity pilot | `tools/parity/first_subsystem_parity_pilot.py` | In-code fixture set: `""`, `tet4d`, `oracle-check`, `hash-bridge` | `tests/unit/migration/test_first_subsystem_parity_pilot.py` | Proves the parity process shape for exact `stable_hash_text(text)` comparison between Python oracle and native/provisional output. | Reusable parity infrastructure |
| 18 | Trace metadata identity/digest parity | `tools/parity/trace_metadata_identity_digest_parity.py` | `tests/fixtures/parity/trace_metadata_identity_digest.json` | `tests/unit/migration/test_trace_metadata_identity_digest_parity.py` | Compares compact canonical trace metadata identity and digest behavior. | Reusable parity infrastructure |
| 20 | Topology identifier normalization parity | `tools/parity/topology_identifier_normalization_parity.py` | `tests/fixtures/parity/topology_identifier_normalization.json` | `tests/unit/migration/test_topology_identifier_normalization_parity.py` | Compares canonical topology identifier normalization without topology mechanics. | Reusable parity infrastructure |
| 22 | Trace schema/version normalization parity | `tools/parity/trace_schema_version_normalization_parity.py` | `tests/fixtures/parity/trace_schema_version_normalization.json` | `tests/unit/migration/test_trace_schema_version_normalization_parity.py` | Compares trace schema/version metadata identity without interpreting trace events. | Reusable parity infrastructure |

Related supporting surfaces:

- `tools/migration/trace_schema.py`: shared Python trace schema helper used by
  parity and migration trace tooling.
- `tools/migration/compare_cpp_gameplay_trace.py`: gameplay trace comparison
  harness tied to migration golden traces.
- `migration/golden_traces/`: committed Python-oracle migration traces.
- `tests/fixtures/parity/`: committed fixtures for maintained data-only parity
  slices.
- `docs/architecture/parity_protocol.md`: parity process authority.
- `docs/architecture/parity_evidence_package_review.md`: Stage 21 package
  review that kept parity harnesses under `tools/migration/` until at least
  four maintained harnesses existed.

Historical note: no `tools/parity/` directory existed at the time of this
Stage 24 review. Stage 25 later creates that route and moves the approved
harnesses there without semantic changes.

## Classification Criteria

| Location | Meaning | Use when |
| --- | --- | --- |
| `tools/migration/` | migration-specific support tooling | tool is temporary, one-off, or only meaningful during Python->Godot/C++ transition |
| `tools/parity/` | reusable parity infrastructure | tool expresses a stable comparison contract between oracle/provisional/native implementations |
| neither | wrong abstraction | tool should be deleted, merged, or kept elsewhere |

A parity harness should move to `tools/parity/` only if it is reusable,
maintained, test-backed, and not merely a temporary migration script.

A migration helper should remain in `tools/migration/` if it only exists to
build/export/inspect migration bundles or stage-specific transition artifacts.

Additional decision checks:

- A stable comparison contract can be described without relying on the current
  Godot/native migration stage.
- The harness has either committed fixtures or a clearly enumerated deterministic
  fixture set.
- The harness has unit tests that exercise default/advisory and strict or exact
  comparison behavior where applicable.
- Moving the file would make imports and future task routing clearer.
- Moving the file would not require semantic changes, fixture changes, or new
  parity coverage.

## Evidence Review

### Stage 15 - First Subsystem Parity Pilot

Classification: reusable parity infrastructure.

The harness compares a stable text-hash contract with a deterministic in-code
fixture set and unit tests. It remains process-only evidence and does not prove
gameplay parity, but its shape is reusable: Python oracle output,
native/provisional output loading, missing/extra case diagnostics, mismatch
reporting, and advisory versus strict behavior.

Its current `tools/migration/` path now mildly misleads future contributors
because the pilot is no longer just a migration export helper. Moving it would
reduce confusion if Stage 25 preserves its CLI behavior and import compatibility
through updated tests/docs.

### Stage 18 - Trace Metadata Identity/Digest Parity

Classification: reusable parity infrastructure.

The harness compares stable metadata identity and digest contracts using a
committed fixture and tests. It has exact comparison semantics, explicit
exclusions, and a provisional native route when available. It is data-only and
trace/replay relevant without touching gameplay events.

The current path under `tools/migration/` makes this look temporary even though
trace metadata identity/digest comparison is an ongoing semantic-safety
mechanism. This is a strong candidate for `tools/parity/`.

### Stage 20 - Topology Identifier Normalization Parity

Classification: reusable parity infrastructure.

The harness compares a stable identifier-normalization contract with a committed
fixture and tests. It intentionally has no safe native/provisional route yet,
but default/advisory and strict behavior are documented and tested. Its scope is
identifier-only and excludes topology traversal, neighbor lookup, movement,
gameplay, rendering, and authority transfer.

Because this harness is fixture-backed and exact-comparison oriented, it is not
merely a migration bundle helper. Its `tools/migration/` path can obscure the
fact that identifier normalization parity remains useful after the immediate
migration stage.

### Stage 22 - Trace Schema/Version Normalization Parity

Classification: reusable parity infrastructure.

The harness compares schema/version metadata identity through a deterministic
fixture and tests. It is exact-comparison friendly and explicitly excludes
trace events, board snapshots, piece positions, topology movement, gameplay,
rendering, and authority transfer.

This fourth maintained harness satisfies the Stage 21 trigger for revisiting
the package route. Keeping it under `tools/migration/` now makes the parity
family harder to identify and raises the chance that future Codex tasks treat
stable parity checks as temporary migration scaffolding.

## `tools/parity/` Decision

Decision: approve `tools/parity/` split in Stage 25.

Rationale:

- Four maintained parity harnesses now form a reusable parity family.
- Stage 21 kept harnesses under `tools/migration/` until there were at least
  four maintained parity harnesses, or until parity harnesses were used outside
  the Godot/native migration path. The four-harness trigger is now met.
- Keeping these harnesses under `tools/migration/` makes parity look temporary.
- A dedicated `tools/parity/` namespace clarifies that parity is an ongoing
  semantic-safety mechanism, not merely migration scaffolding.
- Stage 24 should decide only; the actual move should be isolated in Stage 25
  to avoid mixing architecture decision and import-routing refactor.

Benefits:

- Clearer task routing for future parity work.
- Lower chance that migration cleanup deletes or ignores maintained parity
  checks.
- Cleaner distinction between export/sync/bundle tools and stable comparison
  contracts.
- Better alignment with the Stage 23 Python oracle boundary audit, which marks
  temporary migration harness layout as non-authoritative while preserving
  parity evidence semantics.

Risks:

- Import path churn in tests, docs, and validators.
- CLI references may drift if Stage 25 moves files without compatibility
  review.
- Some helpers, especially `tools/migration/trace_schema.py`, are shared by
  migration and parity surfaces and need careful ownership decisions.
- Moving harnesses can look like a semantic change unless Stage 25 is kept to
  routing/refactor only.

Must remain in `tools/migration/`:

- migration trace exporters such as `export_topology_trace.py`,
  `export_gameplay_trace.py`, and `export_endgame_trace.py`
- bundle tooling such as `export_config_bundle.py`, `compare_config_bundle.py`,
  `sync_godot_bundle.py`, and `sync_unity_bundle.py`
- migration golden-trace case routing such as `trace_cases.py`
- migration-specific trace comparison such as `compare_trace.py` and
  `compare_cpp_gameplay_trace.py`, unless a later review separates general
  parity comparison from migration trace replay

Approved to move to `tools/parity/` in Stage 25:

- `tools/parity/first_subsystem_parity_pilot.py`
- `tools/parity/trace_metadata_identity_digest_parity.py`
- `tools/parity/topology_identifier_normalization_parity.py`
- `tools/parity/trace_schema_version_normalization_parity.py`

Requires explicit Stage 25 review before moving:

- `tools/migration/trace_schema.py`, because it supports both migration trace
  tooling and parity metadata helpers.

Why Stage 24 does not perform the move:

- This stage is an architecture decision only.
- Moving files would require import-path, CLI, docs, validator, and test
  routing changes.
- The refactor should be isolated so verification failures can be attributed to
  routing changes rather than to the decision document.

## Implemented Stage 25 Scope

Stage 25 is a pure routing/refactor stage limited to:

```text
move tools/migration/*parity*.py -> tools/parity/
update tests/docs/validators/routing/import paths
preserve CLI behaviour where applicable
preserve fixture contents
preserve harness semantics
preserve advisory/strict behaviour
no new parity logic
no new fixtures
no gameplay changes
no authority transfer
```

Stage 25 must not include:

- new parity slice
- trace envelope validation implementation
- gameplay/topology/movement work
- native/provisional implementation
- Godot scene/resource changes
- fixture semantic changes
- authority transfer

Stage 25 acceptance criteria should include:

- old and new command routes are either intentionally supported or explicitly
  documented as changed
- all moved harnesses keep exact behavior and diagnostics
- tests import from the new package route
- fixtures remain byte-for-byte semantically unchanged
- `CODEX_MODE=1 ./scripts/verify.sh` passes

## Impact on Later Stages

After Stage 24 and optional Stage 25, the intended sequence remains:

```text
25. If approved, move parity harnesses from tools/migration/ to tools/parity/
26. Select first structural-but-safe parity slice
27. Implement first structural-but-safe parity slice
28. Authority-transfer readiness review
```

The recommended next structural-but-safe candidate remains:

```text
trace envelope validation
```

Allowed future scope for trace envelope validation:

- top-level trace object shape
- required metadata keys
- schema/version field presence
- identity/digest field presence
- fixture envelope structure
- exact validation result comparison

Forbidden future scope:

- trace events
- board snapshots
- piece positions
- topology traversal
- movement
- gameplay semantics
- rendering/view/camera
- authority transfer

## Boundary Statement

This review does not transfer authority from Python to Godot or C++.
This review does not approve deletion of Python semantic code.
This review does not authorize gameplay, topology, trace-event, movement,
rendering, Godot, or native-code changes.
This review document itself did not move `tools/migration` files or create
`tools/parity/`.
Stage 25 is the isolated follow-through that applies the approved routing
refactor only.
