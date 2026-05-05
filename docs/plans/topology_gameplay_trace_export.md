# Topology / Gameplay Golden Trace Export

Role: migration oracle
Status: active
Last updated: 2026-05-05

## Purpose

Stage 2 records the frozen Python topology/gameplay behavior as deterministic
JSON traces for future engine replay. The traces are migration artifacts, not a
new gameplay authority, and they must be generated from the existing runtime.

Stage 3 extends this migration oracle with locked-cell endgame traces. Endgame
trace detail lives in `docs/plans/endgame_trace_export.md`.

Stage 4 packages the topology, gameplay, and endgame traces into a generated
migration bundle for engine replay spikes. Bundle detail lives in
`docs/plans/migration_config_bundle.md`.

## Locations

- Trace helpers and CLIs: `tools/migration/`
- Topology goldens: `migration/golden_traces/topology/`
- Gameplay goldens: `migration/golden_traces/gameplay/`
- Endgame goldens: `migration/golden_traces/endgame/`
- Regeneration/drift check: `tools/migration/compare_trace.py`
- Generated engine-spike bundle: `migration/exported_bundle/`
- Bundle regeneration/drift check:
  `tools/migration/export_config_bundle.py --check` and
  `tools/migration/compare_config_bundle.py`

## Contract

- Traces are versioned, sorted, newline-terminated JSON.
- Traces contain no timestamps, local absolute paths, memory reprs, or
  Python `hash()` values.
- Topology traces cover plain, wrap, invert, sphere-like, cross-axis
  transport, Play-vs-Sandbox Y-axis distinction, false-lock regression, and
  deterministic playability diagnostics.
- Gameplay traces cover plain 2D/3D/4D, topology-aware play, Y-axis drop
  policy, active/locked cell snapshots, score/line state, and launch topology
  parity.
- `compare_trace.py` regenerates known traces and fails on byte/canonical JSON
  drift across topology, gameplay, and endgame trace sets.
- `export_config_bundle.py` copies/indexes the checked-in traces for portable
  engine replay consumption without making the generated bundle authoritative.

## Migration Rule

Unity, Godot, C#, C++, or other engine work must replay the Stage 2 topology /
gameplay traces and Stage 3 endgame traces before implementing independent
topology transport, gameplay drop/lock logic, or endgame simulation. Python
remains authoritative until a replacement core passes trace parity.

Future engine work should consume the Stage 4 bundle first when locating traces,
config snapshots, schema metadata, and authority docs. The bundle is disposable
and reproducible; it must not replace `config/`, `src/`, or
`migration/golden_traces/` as authority.
