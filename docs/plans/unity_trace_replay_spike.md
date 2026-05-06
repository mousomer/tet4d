# Unity Trace Replay Spike

Role: migration replay spike  
Status: active  
Last updated: 2026-05-05

## Purpose

Stage 5 adds a small Unity project that consumes the copied Stage 4 migration
bundle and replays topology, gameplay, and endgame traces frame-by-frame.

This spike answers a narrow question: can tet4d trace data be made visually
readable in Unity without porting gameplay or simulation semantics?

## Boundaries

- Python remains the semantic oracle.
- `migration/exported_bundle/` remains generated and non-authoritative.
- Unity runtime loads only `Assets/StreamingAssets/tet4d_bundle/`.
- Unity does not call Python at runtime.
- Unity does not implement gameplay, topology transport, score/lock logic, or
  endgame simulation.
- Inspector, prefab, scene, or ScriptableObject values are presentation-only.

## Locations

- Unity project: `unity/Tet4D.Unity/`
- Sync tool: `tools/migration/sync_unity_bundle.py`
- Copied runtime bundle:
  `unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle/`

## Replay Scope

- Case browser grouped by `topology`, `gameplay`, and `endgame`
- Frame stepping and play/pause
- State-hash and case metadata display
- Basic diagnostics/config metadata display
- 2D/3D rendering plus 4D W-slice visibility
- Endgame particle rendering from trace data

## Non-Goals

- No gameplay core port
- No topology resolver port
- No endgame simulator port
- No Steam or console packaging
- No final UI polish
- No Godot work in this stage

## Sync Commands

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py \
  --bundle migration/exported_bundle \
  --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle

PYTHONPATH=src .venv/bin/python tools/migration/sync_unity_bundle.py \
  --bundle migration/exported_bundle \
  --unity-assets unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle \
  --check
```

## Verification

- Python-side sync/export/bundle tests are authoritative in this repo.
- Unity EditMode tests should be run locally when a Unity CLI is available.
- If Unity CLI is unavailable, the spike remains a code-and-asset bootstrap
  plus Python-side verification surface.
