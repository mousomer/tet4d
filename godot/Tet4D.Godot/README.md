# Tet4D Godot Trace Replay Spike

This Godot 4.6.3-stable project is a replay-only spike for tet4d migration
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

- Godot version target: locked to Godot 4.6.3-stable for this migration stage.
- Stage 6b display alignment: the replay renderer now follows the
  Python/Pygame centered board display convention, uses orthographic fit
  against projected bounds, and keeps W labels/boards/cells/particles/trails
  on one mapper-owned coordinate basis.
- Trace fidelity: repaired for previously detached presentation trails and
  guarded by frame/entity metadata diagnostics plus identity-safe interpolation
  policy.
- Menu-screen architecture: introduced with Main Menu, Trace Replay Browser,
  Replay Viewer, Settings, Controls / Keyboard Hints, and Diagnostics screens.
- Shell layout: repaired as an explicit top/status, left case browser, center
  board, right scroll-safe inspector, and bottom playback model so the board
  viewport cannot consume either side panel.

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
Stage 19 adds native plain-ND clear/scoring parity through that same
parity-only API for `gameplay_plain_3d_plane_clear_short` and
`gameplay_plain_4d_plane_clear_short`. Godot can list/export/status-check
those cases, but it still does not expose live ND movement, rotation, clear,
or scoring commands. Stage 20 adds native plain-ND spawn-blocked game-over
parity through the same parity-only API for
`gameplay_plain_3d_spawn_blocked_game_over` and
`gameplay_plain_4d_spawn_blocked_game_over`. Godot can list/export/status-check
those cases, but it still does not expose live ND gameplay, topology, or
endgame APIs.

Stage 22 adds `Live 3D`, the first live plain ND Godot prototype. It is plain
bounded 3D only. Godot captures input, manages repeat/tick cadence, switches
between Replay / Live 2D / Live 3D, parses the native snapshot JSON, renders
through the existing trace coordinate mapper and renderer, and displays the
`LIVE 3D · C++ CORE` HUD/hints. The C++ GDExtension owns the live 3D session,
movement, rotation, soft/hard drop, gravity tick results, lock,
clear/scoring, spawn/game-over, command status, and `state_hash`. Live 4D,
topology, endgame, C#, Python runtime calls, and Godot-side gameplay legality
remain deferred.

Stage 22b keeps that boundary and corrects Live 3D readability: live 3D cells
render as solid cuboids with lit face contrast and edge outlines through the
existing renderer, Fit View uses a depth-readable 3D angle, and the HUD shows
signed last-rotation labels such as `XZ+` / `YZ-` from returned native
command/status data.

Stage 22c keeps the same visual-only boundary and tunes those cells to read as
external solid blocks: Live 3D uses opaque shaded exterior face panels,
restrained silhouettes, and subtle face brightness cues instead of a
cage-like or transparent-wall presentation.

Stage 22d defines the gameboard visual-language authority in
`docs/plans/gameboard_visual_language_design.md`. Stage 22e implements that
authority incrementally through the existing mapper/renderer path; the current
Godot shell reserves left/board/right panel regions structurally and routes
snapshot projection through focused presentation scripts. Stage 22f manual
Live 3D acceptance passed after Stage 22g corrections: Live 3D default/Fit
View uses the above-board `LIVE_3D_EXTERNAL_DIAGRAM_VIEW`, camera preset/view
diagnostics are visible, bundle status stays compact with inspector detail,
and active cells are stronger than locked cells with an origin marker. Stage
23 adds a narrow Live 4D mode backed by C++ `PlainNDSession`, side-by-side W
slices through the existing mapper/renderer, Q/E W movement, and six direct
rotation plane pairs.
Stage 23 manual GUI acceptance found W labels too small, Space leaking to
focused UI activation, and active Live 4D cells too bright. Stage 23b corrects
those visual/input defects by enlarging/backing W labels, consuming Space as
live hard-drop before UI accept handling, and reducing Live 4D active-cell
brightness while preserving outlines/origin markers. Stage 23 manual
acceptance passed after Stage 23b/23c/23d corrections; Stage 24 shell
hardening passed manual acceptance and Stage 25 topology planning is
unblocked.
Stage 23c further corrects Live 4D view/readability: W markers are now
`W SLICE n/N` headers with larger chips, Live 4D opens/resets in a fitted
W-slice view, `Fit View` restores that canonical full layout, and safe camera
keys allow inspection without overlapping gameplay controls.
Stage 23d fixes the Live 4D zoom path: `-` zooms out, `=`/`+` zoom in by
changing orthographic camera size, camera diagnostics expose size/zoom state,
mouse wheel up/down use the same visible zoom direction, and camera keys remain
captured even after clicking viewer panels/buttons.
Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain bounded
prototype. Stage 24 Live ND polish and hardening is implemented as Godot shell
lifecycle/input hardening: switching from Replay back to Live 2D, Live 3D, or
Live 4D resumes the selected native session without resetting it, pauses
non-selected live modes, clears focus/repeat state, and keeps Space hard-drop
plus Live 4D camera/zoom keys captured before HUD focus. Topology and endgame
remain deferred. Manual Stage 24 acceptance via
`docs/plans/live_nd_manual_acceptance.md` is required before Stage 25 topology
planning.

## Opening In Godot

1. Open `godot/Tet4D.Godot/` in Godot 4.6.3-stable.
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
- mouse wheel up/down: zoom in/out
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
- `Tab`: switch to Live 3D
- `Esc`: quit shell

Live 2D mode keeps this hint strip visible above the viewport and does not show
replay frame/case controls.
Switching to Replay pauses live ticking but preserves the native live session;
use `R` / Reset Live for a fresh deterministic new game. While paused, Godot
blocks gameplay command dispatch except pause/resume, reset, fit, mode switch,
help, and quit.

Live 3D controls:

- `A` / `D` or `Left` / `Right`: move active piece on X
- `W` / `S` or `Up` / `Down`: move active piece on Z
- `Shift`: soft drop
- `Space`: hard drop
- `R` / `T`: XY rotate
- `F` / `G`: XZ rotate
- `V` / `B`: YZ rotate
- `P`: pause / resume gravity tick
- `Backspace`: reset live 3D
- `Tab`: switch to Live 4D
- `Esc`: quit shell

Live 3D uses the same renderer/mapper path as replay and live 2D. `F` remains
an XZ rotation key in Live 3D; use the visible `Fit View` button for camera
fit in that mode. The HUD reports `Last rotation: XY+/-`, `XZ+/-`, or
`YZ+/-` after native rotation commands, and the active outline briefly pulses
after a returned native rotation snapshot.

Live 4D controls:

- `A` / `D` or `Left` / `Right`: move active piece on X
- `W` / `S` or `Up` / `Down`: move active piece on Z
- `Q` / `E`: move active piece W- / W+
- `Shift`: soft drop
- `Space`: hard drop
- `R` / `T`: XY rotate
- `F` / `G`: XZ rotate
- `V` / `B`: YZ rotate
- `Y` / `U`: XW rotate
- `H` / `J`: YW rotate
- `N` / `M`: ZW rotate
- `I` / `K`: camera pitch adjustment
- `O` / `L`: camera yaw adjustment
- `-`: camera zoom out
- `=` / `+`: camera zoom in
- `P`: pause / resume gravity tick
- `Backspace`: reset live 4D
- `Tab`: return to Replay
- `Esc`: quit shell

In Live 4D, `Q` is W- movement and `E` is W+ movement; `Q` does not quit.
`H` is YW- rotation and does not open Help. `Esc` is the keyboard quit/back
path. Space is captured by live gameplay as hard drop before focused shell
buttons can receive UI accept. Visible `Fit View`, reset, and quit/back
buttons remain mouse-clickable. The HUD reports `LIVE 4D · C++ CORE`, score,
lines, hash, pieces, last command, signed last rotation, and active W context.
The W-slice headers use larger outlined `W SLICE n/N` text with high-contrast
backing chips for default/Fit View readability. Live 4D opens and resets in a
canonical fitted W-slice view. `Fit View` is the recovery action after manual
camera adjustment. `I/K`, `O/L`, and `-`/`=` adjust only the camera and do not
dispatch gameplay commands. Returning from Replay resumes the selected live
mode without resetting native state, and Space/zoom controls continue to work
after clicking HUD panels or buttons.

The Replay Viewer uses one explicit shell layout: the game renders through a
`SubViewport` inside `GameArea`, with a bounded left case browser and a
fixed-width right inspector as body siblings. Inspector overflow scrolls
vertically. Enable the `Geom` checkbox in the bottom bar to print
root/body/left/game-area/inspector/bottom-bar rectangles and viewport size
while checking resize behavior.

## Tests

If a Godot 4.6.3-stable CLI is installed locally, run a syntax check with:

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
status, and the native extension smoke/parity API including Stage 19 plain-ND
movement/drop, rotation, and clear/scoring trace exports plus Stage 20
spawn-blocked game-over trace exports, Stage 22 live 3D bridge/shell coverage,
and Stage 23/23b/23c live 4D bridge/shell coverage including Q/E W movement,
Esc-only live quit, Space hard-drop capture, W-slice header readability,
fitted Live 4D entry, Fit View recovery, safe camera-key non-mutation, and
restrained Live 4D active-cell brightness. Stage 23d adds coverage for
orthographic zoom size changes, `-`/`=`/`+` key variants, focused-UI capture,
mouse-wheel direction, diagnostic size/zoom text, Fit View recovery, and
switching away/back to Live 4D. Stage 24 adds lifecycle/focus coverage for
resuming Live 2D/3D/4D from Replay without native reset, pausing non-selected
live modes, and preserving pre-UI Space hard-drop plus Live 4D zoom capture
after HUD focus changes. On a fresh checkout, run the
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
- GDScript is used only for shell/UI work. Native ND parity APIs remain trace
  export surfaces; live 3D and live 4D gameplay state remain owned by C++.
  Stage 23 Live 4D is a narrow prototype, not topology or endgame gameplay.
- Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
  Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain bounded
  prototype. Stage 24 Live ND polish and hardening is implemented as shell
  lifecycle/input hardening. Topology and endgame remain deferred.
- Stage 23c adds fitted Live 4D camera controls for inspection; it does not add
  topology/endgame behavior or change C++ gameplay semantics.
- Stage 23d makes those zoom controls affect orthographic camera size; it does
  not add topology/endgame behavior or change C++ gameplay semantics.
- Stage 24 resumes selected live sessions on re-entry and hardens focus/input
  capture; it does not add topology/endgame behavior or change C++ gameplay
  semantics. Manual Stage 24 acceptance is required before Stage 25 topology
  planning.
