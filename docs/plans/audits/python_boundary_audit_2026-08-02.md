# Python Boundary and Complexity Audit

Role: audit

Status: active

Source of truth: repository code and the routed semantic authorities

Supersedes: none

Date: 2026-08-02

## Scope and method

This audit classifies Python conversion and validation by semantic ownership.
It covers live package code, replay and trace tooling, persistence, CLI/editor
adapters, numerical internals, migration tools, compatibility paths, and
retirement candidates. A textual search for `int`, `bool`, and `str` was used
only to locate candidates; the classification follows the caller, source data,
and owning authority. Conversion calls are not violations by themselves.

Stage 53E changes no runtime behavior. Stage 53F owns accepted remediation.
Python remains the gameplay, topology, replay, trace, and defaults oracle.

Risk meanings:

- **high**: malformed external data can become accepted semantic or identity
  state;
- **medium**: a permissive boundary can hide drift, but has a constrained
  source or downstream validation;
- **low**: conversion formats validated/internal values or implements a named
  human-input or legacy adapter;
- **protected**: exact representation validation already precedes domain use.

## Boundary inventory

| Boundary | Representative owners | Classification | Stage 53F disposition |
| --- | --- | --- | --- |
| Canonical topology contract and identity | `topology_explorer/canonical_contract.py`, `contract_validation.py`, `domain_validation.py`, `glue_model.py` | protected; exact decoded-JSON types and strict domain constructors reject Boolean-as-integer and lossy scalar coercion | preserve; use as the reference pattern |
| Native topology transport projection | `topology_explorer/topology_transport.py`, `transport_resolver.py`, shared fixtures | protected where extraction follows contract validation; many `int`/`str` calls serialize or copy already validated DTO values | add no duplicate scalar policy; retain parity checks |
| Explorer persistence v1 and legacy v0 | `runtime/topology_persistence.py`, `topology_explorer_store.py` | protected; strict current representation and an explicit evidence-backed legacy adapter share domain validation | preserve policy/adapter separation and diagnostic stability |
| Replay payload decoding | `replay/format.py` | **high**: seed/version fields are exact, but event actions use `str(...)`, ND dimensions use `int(...)`, edge-rule parts stringify arbitrary values, and config payloads inherit constructor leniency | add exact action, dimensions, edge-rule, and config-field readers before construction; retain schema/version errors |
| Replay recording helpers | `replay/__init__.py` | medium: public helpers coerce seed and tick values and clamp negative ticks even though replay identity depends on them | require domain values or move leniency into a separately named caller adapter |
| Public gameplay configuration | `engine/gameplay/game2d.py`, `game_nd.py` | **high**: `exploration_mode`, `wrap_gravity_axis`, and optional rigid-play flags use truthiness; several integer fields rely on comparisons that accept `bool` as `int`; ND dimensions are not normalized by one exact constructor boundary | establish strict public constructors, then keep UI/settings conversion outside them |
| Piece-set and gameplay record loading | `engine/gameplay/pieces_nd.py`, `pieces2d.py`, topology designer payload helpers | **high** for imported/configured records: names and numeric fields are converted before the semantic object is proven exact | introduce explicit format readers with field paths; domain objects receive validated values only |
| Movement-graph cache decoding | `topology_explorer/movement_graph.py`, `runtime/topology_cache.py` | **high**: cached coordinates, dimensions, axes, sides, IDs, and traversal coordinates are reconstructed with `int`/`str`; invalid data generally falls back, but coercible data can change the cached semantic graph | validate exact cache schema and identity inputs; retain fallback only in the cache adapter |
| Normal/explorer topology profile store | `runtime/topology_profile_store.py`, `gameplay/topology_designer.py` | **high** and separate from Stage 53D: it overlays defaults and uses legacy-friendly profile parsing for active setup and Topology Lab consumers | either version and harden this format or migrate callers to an explicit shared persistence adapter; do not merge the formats silently |
| Trace/state-hash materialization | `tools/migration/trace_schema.py`, trace exporters | **high** at the generic helper: `to_jsonable` stringifies unsupported objects and arbitrary mapping keys before hashing; most current exporters pass typed internal data | make unsupported values fail, define allowed key/value types, and test stable hashes against rejected near-types |
| Trace/config-bundle imports and comparison | `tools/migration/export_config_bundle.py`, `compare_cpp_gameplay_trace.py`, `compare_topology_transport.py` | medium to high: checked-in fixtures are trusted operationally, but several imported values use `int`/`str` before manifest validation | centralize exact manifest readers and validate before projections or identity digests |
| Settings persistence and migration | `runtime/settings_sanitize.py`, menu/keybinding/settings stores | medium: leniency is product-required, but Boolean truthiness and index conversion policies are distributed and not uniformly source-named | inventory each stored schema; keep legacy recovery in versioned/named adapters and pass strict values to runtime models |
| Editor and Topology Lab draft input | `ui/pygame/topology_lab/*`, `runtime/topology_playground_*` | low when conversion is visibly a draft/widget adapter; medium where normalized draft values directly construct domain or cache state | retain forgiving text parsing only in explicit editor adapters; add one strict handoff into domain state |
| CLI parsing | `cli/front*.py`, topology-lab entrypoint, migration tool `argparse` handlers | low: these are human-input adapters and `argparse` choices/types already make intent visible | preserve conversion at the CLI edge; test errors for identity-bearing values such as dimensions and seeds |
| Numerical and rendering internals | core transforms, scoring, rendering, animation, explosion simulation | generally low: conversions normalize arithmetic intermediates, enum-like values, or presentation output after construction | do not mechanically ban conversions; address only a demonstrated public-boundary leak |
| Output serialization | replay `to_dict`, topology/trace exporters, diagnostics | low when converting already validated domain values into JSON primitives | preserve deterministic ordering and prohibit generic fallback stringification |

## Stage 53F remediation order

1. Make replay decoding and replay-record construction exact for actions,
   dimensions, seeds, ticks, edge rules, and gameplay configuration fields.
2. Make `GameConfig` and `GameConfigND` reject Boolean-as-integer and
   truthiness-based Boolean inputs; provide explicit UI/settings adapters for
   accepted leniency.
3. Make movement-graph cache decoding exact and prove corrupt/coercible cache
   data cannot alter topology identity or neighbor results.
4. Resolve the separate `topology_profile_store.py` format: version and harden
   it or migrate its active callers without silently treating it as Stage 53D
   persistence.
5. Restrict trace/state-hash materialization to an explicit JSON value domain;
   reject arbitrary objects and non-string mapping keys rather than stringify
   them.
6. Consolidate exact manifest readers in migration/config-bundle tooling and
   add narrow regression cases for `bool`, numeric strings, and integral
   floats at the actual imported-data boundaries.
7. Review stored settings schemas individually and move evidenced recovery to
   named adapters; do not impose topology policy on unrelated settings.

## Retirement candidates

These paths should be removed rather than hardened once their callers and
compatibility commitments reach zero. Stage 53F must prove that condition
before deletion.

| Candidate | Current evidence | Exit condition |
| --- | --- | --- |
| `scripts/profile_topology_playground_startup.py` | standalone migration-era profiling script; no in-repository caller | retain only if it remains an accepted benchmark; otherwise archive results and delete |
| `src/tet4d/ui/pygame/topology_lab/__main__.py` | thin legacy direct-launch delegate retained by current RDS | remove only after the documented external compatibility window closes |
| root/`cli/front2d.py`, `front3d.py`, `front4d.py` shims | thin compatibility launchers under explicit size budgets | remove after packaging/docs/tests and supported external invocation migrate to the unified launcher |
| topology-lab shell compatibility projections in `scene_state.py` and related helpers | explicitly deferred mirrors in the current topology authority/debt register | delete individual mirrors after canonical selector callers reach zero; do not harden shadow state |
| legacy edge-rule export/preview bridge | retained for non-advanced explorer setup/export compatibility | remove after all active consumers use canonical gluing profiles |
| `engine/api.py` replay-facing compatibility facade | still used by replay and compatibility tests | migrate replay to canonical owners first; then re-audit rather than expanding the facade |

`runtime/topology_profile_store.py` is not dead: setup and Topology Lab callers
remain active. It is a migration/remediation target, not a deletion candidate.

## Ruff complexity audit

Command:

```bash
.venv/bin/ruff check . --select C901,PLR0912,PLR0915
```

The audit produced 16 findings: four `PLR0912` branch findings and twelve
`PLR0915` statement findings. Existing `C901` enforcement remains active and
reported no additional failure in this combined run.

| Classification | Findings | Decision |
| --- | --- | --- |
| active code worth focused refactoring | `score_analyzer_features.placement_features`; settings save orchestration; the main menu runner when its next behavioral change occurs | refactor only with focused behavior tests; complexity alone does not authorize churn |
| legitimate orchestration needing a narrow local exception if a rule is later enabled | bot-options loop, launcher non-key dispatcher, main menu runner/activation closure | stateful ordered dispatch is real complexity; use local exceptions only after extracting clearly owned pure decisions |
| presentation/drawing noise | main-menu, leaderboard, topology-lab, and glue-arrow drawing functions | `PLR0915` counts declarative draw calls and provides little boundary value |
| tooling or retirement candidate | `arch_metrics._build_folder_balance`, topology-playground startup profiler | keep the active metrics builder readable; decide profiler retirement before refactoring it |
| test noise | two long integration-style test methods | table/extract only when behavior clarity improves; do not enable a production rule that creates test suppression work |

Decision: do **not** enable `PLR0912` or `PLR0915` repository-wide in Stage
53E. The finding set is small but heterogeneous and dominated by orchestration,
drawing, and tests; enabling either rule would require cleanup or a suppression
inventory without protecting the high-risk semantic boundaries above.
`PLR0913` is also not enabled: parameter count was not shown to correlate with
boundary risk. Retain `C901` as the current low-noise complexity gate.

## Lightweight governance result

- Ruff's canonical formatting width is explicitly `88` and third-party native
  sources remain excluded.
- Code-size comparison is required only for substantial non-feature
  refactors. Formatted physical diff is primary; AST statement count is
  secondary when multiline layout materially distorts it.
- Both metrics are review signals, never quotas. Routine fixes, features,
  tests, and documentation do not acquire metric-reporting work.
- No size or metric policy is added to agent dispatch, the policy pack,
  templates, or generated maintenance documents.
