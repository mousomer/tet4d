# Godot Trace Replay Spike

Role: migration replay spike  
Status: complete, pending manual visual acceptance
Last updated: 2026-05-17

## Purpose

Stage 6 adds a small Godot 4.6.2-stable + GDScript project that consumes the
copied Stage 4 migration bundle and replays topology, gameplay, and endgame
traces frame-by-frame.

This spike answers a shell-quality question: can tet4d get better menus,
display clarity, diagnostics panels, replay readability, and simple animation
polish in Godot without porting gameplay or simulation semantics?

Stage 7 records the follow-on engine decision in
`docs/plans/godot_core_port_plan.md`: Godot is the conditional primary product
shell direction after manual visual acceptance, GDScript remains shell-only,
C++ GDExtension is the recommended future deterministic core path, C# is an
alternative only under explicit criteria, and Python remains the oracle until
trace parity passes.

## Boundaries

- Python remains the semantic oracle.
- `migration/exported_bundle/` remains generated and non-authoritative.
- Godot runtime loads only `res://assets/tet4d_bundle/`.
- Godot does not call Python at runtime.
- Godot does not implement gameplay, topology transport, score/lock logic, or
  endgame simulation.
- Inspector, scene, and project settings are presentation-only.
- GDScript is acceptable for this replay/UI spike, but it is not the final
  semantic-core language decision. Stage 7 recommends C++ GDExtension for that
  future core while keeping this replay spike free of core implementation.

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
- Minimal screen-based shell navigation with Main Menu, Trace Replay Browser,
  Replay Viewer, Settings, Controls / Keyboard Hints, and Diagnostics screens;
  panels are contained inside those screens rather than being the top-level
  navigation model
- Startup opens the Main Menu; opening a copied trace from the Trace Replay
  Browser switches to the Replay Viewer without becoming playable gameplay
- Visual-only interpolation between current and next exported trace frames:
  endgame particles use `particle_id`, while gameplay cells currently snap to
  the discrete exported frame because they do not carry stable per-cell
  identity
- Short secondary particle trails and event marker pulses/fades derived only
  from trace frame data
- Timeline status shows playing/paused replay state plus current and next
  frame, with fixed replay speed presets (`0.25x`, `0.5x`, `1x`, `2x`, `4x`)
- Cells, particles, trails, events, probes, W slices, and labels share one
  trace-to-world coordinate mapper based on the existing Python/Pygame
  centered board display convention so trails and event markers stay attached
  to their trace-owned positions
- Stage 6b aligns the default Godot view with the Python display reference:
  orthographic projection, Python-like yaw/pitch, projected-bounds Fit View,
  half-cell board boundaries, and mapper-owned W label positions
- Stage 6b keeps replay motion honest: endgame particles may interpolate only
  by stable `particle_id`; gameplay active cells snap to the current exported
  frame unless future traces add stable identity; topology probe movement is
  rendered only from explicit trace positions
- Visible shell controls include `Fit View`, `Quit Replay`, and a replay-only
  keyboard hint strip (`Space`, arrows, `1`/`2`/`3`, `F`, `H`, `Q`)
- Shared replay theme plus centralized visual constants for shell spacing,
  panel hierarchy, timeline controls, and 4D W-slice presentation
- Reusable Godot Theme resources under `godot/Tet4D.Godot/themes/` for
  Diagnostic High Contrast and Tron UI styling; render materials remain
  separate, role-based, and replay-geometry specific
- Diagnostic-first viewport polish with labeled W slices, quieter side panels,
  stronger case selection, and secondary state-hash/raw-value treatment
- Bright default replay materials and higher-contrast slice/grid presentation
  so boards, pieces, particles, and event markers remain legible in the
  default camera/light setup
- Default startup display mode `Diagnostic High Contrast` plus optional
  `Tron`, with centralized role-based opaque materials for active cells,
  locked cells, probes, particles, event markers, board outlines, and W-slice
  cards so readability does not depend on trace colors, lighting, or bloom
- Replay object colors follow the existing Python/Pygame tetromino trace color
  IDs, with Godot only increasing opacity/emission for shell readability
- Brighter scene baseline so the replay surface stays readable without relying
  on dim default lighting
- Explicit replay-only shell messaging so users do not mistake the spike for
  playable Godot gameplay
- Transition checkpoint: projection readability has passed; trace fidelity
  previously failed because path visuals could detach from replay entities and
  is repaired here with shared mapped trail positions, deterministic camera fit,
  Python-informed coordinate mapping, plus frame/entity metadata diagnostics;
  right-panel clipping is repaired by a single
  container-owned Replay Viewer layout where the `SubViewport` game surface is
  constrained inside `GameArea`, the right inspector is a fixed-width sibling
  inside the same body container, and inspector overflow scrolls vertically

## Python Display Reference Used For Stage 6b

- `src/tet4d/ui/pygame/projection3d.py`: centered `raw_to_world` mapping,
  inverted visual Y, half-cell board bounds, and fit-to-projected-corners
  behavior.
- `src/tet4d/ui/pygame/front3d_render.py`: orthographic default, yaw/pitch
  reset, board panel fit, side-panel containment, and trail rendering through
  the same projection helper as particles.
- `src/tet4d/ui/pygame/render/active_piece_projection_guides.py`: cell-center
  and board-boundary display conventions for guides and boundary planes.
- `src/tet4d/ui/pygame/render/gfx_game.py` and
  `src/tet4d/ui/pygame/front4d_render.py`: role/color language for active and
  locked tetromino cells, grid lines, and projected board presentation.

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
  locally when a Godot 4.6.2-stable CLI is available.
- If Godot CLI is unavailable, the spike remains a code-and-asset bootstrap
  plus Python-side verification surface.

## Follow-On Decision

Stage 8 must not start gameplay implementation directly. The next engineering
step, if Stage 6/6b manual visual acceptance passes, is a C++ GDExtension
skeleton with build/test scaffolding and a narrow Godot API boundary. Plain 2D
gameplay porting begins only after that skeleton proves the native-core
integration path.

Stage 8 now adds only that skeleton: `Tet4DCoreApi` exposes version/status,
echo, stable text hashing, and integer addition so Godot can prove native
loading and calls. It still does not expose gameplay, topology, endgame, trace
parity, Python runtime, C#, Steam, or console implementation.

Stage 9 now adds the first semantic native slice under the core-port plan:
plain bounded 2D parity for `gameplay_plain_2d_short` only. Godot receives only
parity/smoke calls for that trace and remains non-playable; replay rendering
and shell behavior remain separate from the native core.

Stage 10 strengthens that same short-trace slice with canonical snapshot and
`state_hash` parity. The replay spike still remains a replay/product shell, not
a playable gameplay surface.

Stage 11 broadens the plain bounded 2D native parity surface with additional
Python golden traces for rotation, hard-drop lock, and a single-line clear.
Godot still receives only parity/smoke APIs by case id; no live gameplay
controls or semantic authority move into the replay shell.
