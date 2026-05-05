# Endgame Golden Trace Export

Role: migration oracle  
Status: active  
Last updated: 2026-05-05

## Purpose

Stage 3 records the locked-cell endgame explosion model as deterministic JSON
traces for future engine replay. Python remains the semantic oracle. Pygame
rendering, shell artifacts, audio, and visual polish are presentation layers,
not the endgame simulation authority.

## Locations

- Headless model/simulation: `src/tet4d/ui/pygame/locked_cell_explosion/model.py`
  and `src/tet4d/ui/pygame/locked_cell_explosion/simulation.py`
- Trace cases and CLIs: `tools/migration/`
- Endgame goldens: `migration/golden_traces/endgame/`
- Regeneration/drift check: `tools/migration/compare_trace.py`
- Generated Stage 4 migration bundle: `migration/exported_bundle/`

## Contract

- Endgame state construction and stepping run without a screen, event loop,
  renderer, camera, audio device, or wall-clock dependency.
- Particle state is dimension-aware: 2D, 3D, and 4D positions and velocities
  have matching lengths, and W is a real simulated coordinate in 4D.
- Locked-cell live-subset selection is deterministic for the same locked cells,
  seed, and settings; the full locked-cell context remains separate from the
  selected moving particle subset.
- Boundary planes use the canonical cell-extent box:
  `-0.5 .. size - 0.5` on every axis.
- Topology presets affect particle movement, not only spawn or rendering.
  Endgame motion uses the shared explorer transport resolver through the thin
  explosion topology adapter, including velocity transforms across seams.
- Kinetic energy is model-owned and computed as
  `K = 1/2 Σ m_i ||v_i||^2`.
- Endgame traces are versioned, sorted, newline-terminated JSON with fixed
  float precision and stable `state_hash` fields. They contain no timestamps,
  local absolute paths, object reprs, or Python `hash()` values.
- Stage 4 copies and indexes endgame traces in the generated migration bundle
  for Unity/Godot replay spikes. The copied bundle traces remain generated
  artifacts; `migration/golden_traces/endgame/` remains the trace authority.

## Migration Rule

Unity, Godot, C#, C++, or other engine work must replay topology, gameplay,
and endgame traces before implementing independent topology transport,
drop/lock logic, or endgame simulation. A renderer may draw endgame traces
frame-by-frame before a port owns its own physics.

Visual polish remains deferred and is not part of the Stage 3 acceptance bar.

Stage 4 bundle packaging is documented in
`docs/plans/migration_config_bundle.md`. Engine scene/inspector defaults must
not become endgame simulation authority.
