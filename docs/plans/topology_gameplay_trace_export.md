# Topology / Gameplay Golden Trace Export

Role: migration oracle
Status: active
Last updated: 2026-05-05

## Purpose

Stage 2 records the frozen Python topology/gameplay behavior as deterministic
JSON traces for future engine replay. The traces are migration artifacts, not a
new gameplay authority, and they must be generated from the existing runtime.

## Locations

- Trace helpers and CLIs: `tools/migration/`
- Topology goldens: `migration/golden_traces/topology/`
- Gameplay goldens: `migration/golden_traces/gameplay/`
- Regeneration/drift check: `tools/migration/compare_trace.py`

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
  drift.

## Migration Rule

Unity, Godot, C#, C++, or other engine work must replay the Stage 2 traces
before implementing independent topology transport or gameplay drop/lock logic.
Python remains authoritative until a replacement core passes trace parity.

Endgame traces are out of Stage 2 scope and remain deferred to Stage 3 or a
later endgame rescue/export task.
