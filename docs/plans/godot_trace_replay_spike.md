# Godot Trace Replay Spike

Role: migration replay spike  
Status: active  
Last updated: 2026-05-06

## Purpose

Stage 6 adds a small Godot 4.x + GDScript project that consumes the copied
Stage 4 migration bundle and replays topology, gameplay, and endgame traces
frame-by-frame.

This spike answers a shell-quality question: can tet4d get better menus,
display clarity, diagnostics panels, replay readability, and simple animation
polish in Godot without porting gameplay or simulation semantics?

## Boundaries

- Python remains the semantic oracle.
- `migration/exported_bundle/` remains generated and non-authoritative.
- Godot runtime loads only `res://assets/tet4d_bundle/`.
- Godot does not call Python at runtime.
- Godot does not implement gameplay, topology transport, score/lock logic, or
  endgame simulation.
- Inspector, scene, and project settings are presentation-only.
- GDScript is acceptable for this replay/UI spike, but it is not the final
  semantic-core language decision.

## Locations

- Godot project: `godot/Tet4D.Godot/`
- Sync tool: `tools/migration/sync_godot_bundle.py`
- Copied runtime bundle: `godot/Tet4D.Godot/assets/tet4d_bundle/`
- Lightweight Godot tests: `godot/Tet4D.Godot/tests/`

## Replay Scope

- Case browser grouped by `topology`, `gameplay`, and `endgame`
- Frame stepping, reset, play/pause, and speed control
- State-hash and case metadata display
- Diagnostics and event summaries
- 2D/3D rendering plus 4D W-slice visibility
- Endgame particle rendering from trace data
- Product-shell oriented panels for status, settings, diagnostics, and events

## Non-Goals

- No gameplay core port
- No topology resolver port
- No endgame simulator port
- No runtime Python bridge
- No final game menus or shipping UI
- No Steam or console packaging

## Sync Commands

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py \
  --bundle migration/exported_bundle \
  --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle

PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py \
  --bundle migration/exported_bundle \
  --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle \
  --check
```

## Verification

- Python-side sync/export/bundle tests remain authoritative in this repo.
- Godot headless checks and the lightweight GDScript test runner should be run
  locally when a Godot CLI is available.
- If Godot CLI is unavailable, the spike remains a code-and-asset bootstrap
  plus Python-side verification surface.
