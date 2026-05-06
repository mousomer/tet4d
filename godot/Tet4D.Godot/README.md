# Tet4D Godot Trace Replay Spike

This Godot 4.x project is a replay-only spike for tet4d migration work.

It consumes a copied Stage 4 migration bundle from:

- `res://assets/tet4d_bundle/`

It does not:

- call Python at runtime;
- read `src/`, `config/`, `tools/`, or `docs/` at runtime;
- implement gameplay rules;
- implement topology transport;
- simulate endgame particles;
- treat inspector, scene, or project settings as semantic authority.

The migration reason for this spike is product-shell quality: menus, settings
UX, diagnostics panels, display clarity, and replay readability. It is not a
claim that Godot should own tet4d gameplay semantics.

## Bundle Sync

Copy the generated bundle into Godot assets with:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py \
  --bundle migration/exported_bundle \
  --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle
```

Check for drift with:

```bash
PYTHONPATH=src .venv/bin/python tools/migration/sync_godot_bundle.py \
  --bundle migration/exported_bundle \
  --godot-assets godot/Tet4D.Godot/assets/tet4d_bundle \
  --check
```

## Runtime Scope

The runtime loads:

- `manifest.json`
- `config/tet4d_config_bundle.json`
- copied topology traces
- copied gameplay traces
- copied endgame traces

The runtime renders frames and diagnostics only. Python remains the semantic
oracle and the exported bundle remains non-authoritative.

## Opening In Godot

1. Open `godot/Tet4D.Godot/` in Godot 4.x.
2. Let Godot generate `.godot/` and import caches locally.
3. Open `res://scenes/trace_replay.tscn`.
4. Run the main scene.

## Spike Controls

- `Left` / `Right`: previous / next frame
- `Space`: play / pause
- `R`: reset
- `Up` / `Down`: previous / next case
- `1` / `2` / `3`: topology / gameplay / endgame
- mouse drag: orbit
- `Shift` + mouse drag: pan
- mouse wheel: zoom

These are replay controls only. They are not final keybinding authority.

## Tests

If a Godot CLI is installed locally, run a syntax check with:

```bash
godot4 --headless --path godot/Tet4D.Godot --check-only
```

Run the lightweight replay tests with:

```bash
godot4 --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The GDScript tests cover bundle loading and sample trace parsing. They were
written but may not be executable in this environment if a Godot binary is
unavailable.

## Known Limitations

- The visuals are intentionally rough and diagnostic-first.
- The runtime uses copied bundle JSON and does not try to match pygame output.
- 4D is displayed as visible W-separated board slices rather than a final 4D
  presentation.
- GDScript is used only for the replay/UI spike. A future core-port language
  remains undecided between C++ GDExtension and C# if Godot is chosen.
