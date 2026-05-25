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

- Stage 6b display alignment: the replay renderer now follows the
  Python/Pygame centered board display convention, uses orthographic fit
  against projected bounds, and keeps W labels/boards/cells/particles/trails
  on one mapper-owned coordinate basis.
- Trace fidelity: repaired for previously detached presentation trails and
  guarded by frame/entity metadata diagnostics plus identity-safe interpolation
  policy.
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
Fit View uses the same Python-informed orthographic yaw/pitch and projected
board bounds every time a trace loads, resets, or changes display geometry, so
startup does not depend on a drifting manual camera pose.

Stage 8 adds a native C++ GDExtension skeleton only. It proves Godot can load
and call `Tet4DCoreApi`, but it does not implement gameplay, topology,
endgame, trace parity, Python runtime calls, C#, Steam packaging, or console
packaging. On a fresh checkout, initialize submodules and build the native
library before running the Godot tests:

```bash
git submodule update --init --recursive
./scripts/build_godot_tet4d_core.sh
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The native extension test will fail until `native/third_party/godot-cpp` is
initialized and the compiled library exists under
`res://addons/tet4d_core/bin/`.

Stage 11 keeps the native plain-2D surface parity-only while broadening it
beyond `gameplay_plain_2d_short`. The allowed calls are
`run_builtin_plain_2d_smoke_case()`, `list_plain_2d_parity_cases()`,
`get_plain_2d_parity_status()`, `export_plain_2d_trace_json(case_id)`, and
`get_plain_2d_required_field_parity(case_id)`. These calls are for migration
parity and smoke tests only. They do not expose playable Godot movement,
rotation, drop, lock, topology, endgame, or Python runtime behavior.

Gameplay replay frames are post-command snapshots. A hard-drop trace shows the
resulting locked cells, score, and respawned active piece for that exported
frame; it does not animate the piece falling. The replay renderer uses a
role-based active-cell material for gameplay snapshots so synthetic trace
`color_id` values do not turn the active piece into a same-color blob.

Stage 12 adds `Live 2D`, the first playable Godot shell milestone. It is plain
bounded 2D only. Godot captures input and renders the native snapshot JSON;
the C++ GDExtension owns movement, rotation, gravity tick, hard drop, lock,
line clear, scoring, spawn, and state hash. Replay mode remains separate.
Stage 12b keeps live sequencing in C++ with a deterministic fixed classic
piece order (`I, O, T, S, Z, J, L`). This is not the later shuffled Python bag
parity path, and it does not alter Stage 11 golden trace fixtures. Native
snapshots also expose `game_over`, `game_over_reason`, `paused`, and
`state_hash`; Godot renders those fields, stops automatic gravity ticks after
native game-over, and routes reset/new game back to C++.

Stage 13 keeps that same plain 2D scope and polishes the shell loop. Godot
owns elapsed-time accumulation with a visible `0.50s` gravity interval,
left/right and soft-drop held-key repeat, pause-mode command gating, and
live/replay mode switching. C++ still owns every gameplay result and now
exposes `next_piece` and `last_command_status` for HUD display.

Stage 15 adds native plain-ND trace parity scaffolding only. Godot can call
parity/list/export/status methods for `gameplay_plain_3d_short` and
`gameplay_plain_4d_short`, but there is still no live Godot 3D/4D session,
no topology gameplay API, no endgame API, and no Godot-side gameplay
legality.

Stage 18 adds native plain-ND rotation parity through the same parity-only API
for `gameplay_plain_3d_rotation_short` and
`gameplay_plain_4d_rotation_short`. Godot can list/export/status-check those
cases, but it still does not expose live ND movement or rotation commands.
Plane clear/scoring and spawn-blocked game-over parity remain deferred.

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
the Replay Viewer hint strip. Replay mode does not show live movement/drop
hints.

Live 2D controls:

- `A` / `D` or `Left` / `Right`: move active piece
- `W` / `Up` / `X`: rotate clockwise
- `Z`: rotate counter-clockwise
- `S` / `Down`: soft drop
- `Space`: hard drop
- `P`: pause / resume gravity tick
- `R`: reset live 2D
- `F`: fit live board view
- `Tab`: return to Replay
- `Q` / `Esc`: quit shell

Live mode keeps this hint strip visible above the viewport and does not show
replay frame/case controls except `Tab` back to Replay.
Switching to Replay pauses live ticking but preserves the native live session;
use `R` / Reset Live for a fresh deterministic new game. While paused, Godot
blocks gameplay command dispatch except pause/resume, reset, fit, mode switch,
help, and quit.

The Replay Viewer uses one container-owned layout: the game renders through a
`SubViewport` inside `GameArea`, while the right inspector is a fixed-width
body sibling with vertical scrolling. Enable the `Geom` checkbox in the bottom
bar to print root/body/game-area/inspector/bottom-bar rectangles and viewport
size while checking resize behavior.

## Tests

If a Godot 4.6.2-stable CLI is installed locally, run a syntax check with:

```bash
godot --headless --path godot/Tet4D.Godot --check-only
```

Run the lightweight replay tests with:

```bash
godot --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
```

The GDScript tests cover bundle loading, sample trace parsing, centralized
coordinate mapping, deterministic camera fit, replay-viewer layout containment,
gameplay-cell snap policy when stable identity is absent, live 2D native
status, and the native extension smoke/parity API including Stage 18 plain-ND
movement/drop and rotation trace exports. On a fresh checkout, run the
submodule and native build
commands above first; the extension smoke test intentionally fails if Godot
cannot load the native library.

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
- GDScript is used only for shell/UI work. Native ND APIs are parity export
  surfaces only; they are not live 3D/4D gameplay.
