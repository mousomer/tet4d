# Tet4D Godot Trace Replay Spike

This Godot 4.6.2-stable project is a replay-only spike for tet4d migration
work. It is not playable gameplay.

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

Current transition status:

- Projection readability: passed for the diagnostic replay shell.
- Trace fidelity: previously failed due to detached presentation trails; this
  pass repairs trail attachment and adds frame/entity metadata diagnostics.
- Menu-screen architecture: introduced with Main Menu, Trace Replay Browser,
  Replay Viewer, Settings, Controls / Keyboard Hints, and Diagnostics screens.
- Right-panel layout: repaired with responsive containers so the inspector
  remains visible at the default window size and during resize.

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
oracle and the exported bundle remains non-authoritative. The shell should
make that explicit with replay-only status text and replay-labelled controls.
The startup display mode is `Diagnostic High Contrast`, not `Tron`: bright
opaque role-based materials are the default so board outlines, W slices,
probes, cells, and endgame particles stay readable before any aesthetic
styling is considered. Replay geometry follows the existing Python/Pygame
display conventions for centered board coordinates, inverted visual Y, board
half-cell boundaries, and tetromino-style trace color IDs; Godot adds only the
labeled W-card layout needed to inspect copied 4D trace frames.
UI styling is carried by reusable Godot Theme resources in `res://themes/`:
`replay_diagnostic_theme.tres` for the startup shell and
`replay_tron_theme.tres` for the optional neon variant. Replay geometry uses
separate role-based materials in GDScript so UI theme changes do not alter
trace semantics or object visibility rules.
Startup opens a real Main Menu. The Trace Replay Browser loads copied bundle
cases, and opening a case switches to the Replay Viewer. The viewer renders
visual-only interpolation only where exported trace frames carry stable
identity. Endgame particles interpolate by `particle_id`; gameplay cells
update discretely because they do not currently carry stable per-cell
identity. Particle trails, event pulses, and timeline movement are
presentation from trace frames only; Godot still does not simulate gameplay,
topology transport, or endgame physics. Cells, particles, trails, events,
probes, W slices, and labels share one trace-to-world coordinate mapper based
on that Python display reference so visual attachments stay aligned.

## Opening In Godot

1. Open `godot/Tet4D.Godot/` in Godot 4.6.2-stable or the latest stable
   Godot 4.x editor.
2. Let Godot generate `.godot/` and import caches locally.
3. Open `res://scenes/trace_replay.tscn`.
4. Run the main scene.

## Spike Controls

- `Left` / `Right`: previous / next frame
- `Space`: play replay / pause replay
- `R`: reset replay
- `F`: fit current trace view
- `H`: toggle replay help
- `Q` / `Esc`: quit replay shell
- `Up` / `Down`: previous / next case
- `1` / `2` / `3`: topology / gameplay / endgame
- mouse drag: orbit
- `Shift` + mouse drag: pan
- mouse wheel: zoom
- speed menu: `0.25x` / `0.5x` / `1x` / `2x` / `4x` replay speed

These are replay controls only. They are not gameplay controls and they are
not final keybinding authority.

The same controls are visible in the `Controls / Keyboard Hints` screen and in
the Replay Viewer bottom status strip.

The Replay Viewer uses one container-owned layout: the game renders through a
`SubViewport` inside `GameArea`, while the right inspector is a fixed-width
body sibling with vertical scrolling. Enable the `Geom` checkbox in the bottom
bar to print root/body/game-area/inspector/bottom-bar rectangles and viewport
size while checking resize behavior.

## Tests

If a Godot 4.6.2-stable CLI is installed locally, run a syntax check with:

```bash
godot4 --headless --path godot/Tet4D.Godot --check-only
```

Run the lightweight replay tests with:

```bash
godot4 --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The GDScript tests cover bundle loading and sample trace parsing. They were
written but may not be executable in this environment if a Godot 4.6.2-stable
binary is unavailable.

## Known Limitations

- The visuals are intentionally diagnostic-first.
- `Tron` is an optional presentation variant only; `Diagnostic High Contrast`
  is the default readability mode and remains the acceptance bar for replay
  visibility.
- The runtime uses copied bundle JSON and follows Python/Pygame display
  conventions where they are already defined; it does not call Python or port
  gameplay semantics.
- 4D is displayed as visible W-separated board slices rather than a final 4D
  presentation.
- GDScript is used only for the replay/UI spike. A future core-port language
  remains undecided between C++ GDExtension and C# if Godot is chosen.
