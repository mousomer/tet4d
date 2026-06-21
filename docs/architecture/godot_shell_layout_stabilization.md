# Godot Shell Layout Stabilization

Stage 28 audits the current Godot product shell and fixes the viewer layout
contract. This is not a parity stage, a native authority stage, or a gameplay
semantic change.

## Boundary

Python gameplay semantics and golden traces remain the oracle for gameplay,
topology, movement, collision, rotation, scoring, trace correctness, and
replay behavior. Godot owns product-shell presentation: scenes, menus, panels,
input routing, rendering, camera affordances, diagnostics, and layout.

C++ remains limited to already documented native migration surfaces. The
accepted live plain 2D, 3D, and 4D shells route commands to native sessions and
render returned snapshots; Godot does not define those gameplay results.

This stage introduces no authority transfer.

## Inspected Godot Surfaces

| Surface | Classification | Notes |
| --- | --- | --- |
| `godot/Tet4D.Godot/project.godot` | compliant | Godot project shell configuration only. |
| `godot/Tet4D.Godot/scenes/trace_replay.tscn` | compliant | Root `Control` scene with app node and HUD; no gameplay authority. |
| `godot/Tet4D.Godot/scripts/app/trace_replay_app.gd` | boundary-risk issue | Owns shell mode switching, input routing, camera control, replay playback, and native command dispatch. It must stay a router/renderer and must not compute gameplay legality. |
| `godot/Tet4D.Godot/scripts/native/tet4d_core_bridge.gd` | boundary-risk issue | Exposes native bridge calls. Existing scope is allowed only because native owns returned live snapshots and parity/status APIs; the bridge must not become a GDScript semantic fallback. |
| `godot/Tet4D.Godot/scripts/ui/*.gd` | layout issue only | UI panels and HUD are product-shell code. The replay viewer right inspector needed a stricter container/minimum-size contract. |
| `godot/Tet4D.Godot/scripts/rendering/*.gd` | compliant | Rendering and camera presentation only; visual plausibility is not semantic evidence. |
| `godot/Tet4D.Godot/scripts/presentation/*.gd` | compliant | Presentation/projection adapters for display. |
| `godot/Tet4D.Godot/scripts/traces/*.gd` | compliant | Extracts copied trace snapshots for display and diagnostics without redefining trace event semantics. |
| `godot/Tet4D.Godot/scripts/bundle/*.gd` | compliant | Loads copied `res://assets/tet4d_bundle/` data; copied assets are non-authoritative. |
| `godot/Tet4D.Godot/themes/*.tres` | compliant | Theme/readability resources only. |
| `godot/Tet4D.Godot/tests/*.gd` | compliant | Godot shell, rendering, bridge, and layout tests. They are product-shell/regression checks unless explicitly tied to parity evidence. |
| `godot/Tet4D.Godot/README.md` | compliant | States that Godot is shell/presentation and not semantic authority. |
| Godot-facing docs under `docs/plans/` and `docs/architecture/` | compliant | Current authority docs keep Python as oracle and require explicit authority transfer. |

No semantic violation was found in the inspected Godot shell surfaces.

## Fixed Layout Failure

The known failure was:

- the main game panel consumed the window;
- the right inspector panels were only partially visible;
- resizing did not recover the right panels reliably.

This is a Control/container contract problem, not rendering, projection, trace,
or gameplay behavior.

The layout owner is `ReplayHud` in
`godot/Tet4D.Godot/scripts/ui/replay_hud.gd`. The shell sizing constants live
in `ReplayVisuals` in `godot/Tet4D.Godot/scripts/ui/replay_visuals.gd`.

Stage 28 makes the shell minimum explicit:

- `LEFT_PANEL_WIDTH`
- `GAME_AREA_MIN_WIDTH`
- `RIGHT_PANEL_MIN_WIDTH`
- `BODY_MIN_WIDTH`
- `BODY_MIN_HEIGHT`
- `SHELL_MIN_WIDTH`
- `SHELL_MIN_HEIGHT`

`ReplayHud` installs that minimum on itself, its parent scene root when
available, and the Godot window. The viewer `VBoxContainer`, body
`HBoxContainer`, and right inspector `ScrollContainer` now participate in the
same contract. The right inspector keeps its reserved width and remains
vertically scrollable; horizontal scrolling is disabled so panel content wraps
inside the reserved inspector.

## Verification Contract

`godot/Tet4D.Godot/tests/test_replay_viewer_layout.gd` now asserts, across
supported viewport sizes, that:

- the HUD reports the supported shell minimum size;
- the root satisfies that minimum size;
- the left browser keeps its reserved width;
- the game area keeps its minimum width;
- the right inspector keeps its reserved width;
- body, game area, viewport, left browser, inspector, and bottom bar remain
  contained and non-overlapping;
- the inspector preserves detailed bundle and camera diagnostics.

## Risks and Deferred Work

- `trace_replay_app.gd` and `tet4d_core_bridge.gd` remain boundary-risk
  surfaces because they expose live native command paths. They are acceptable
  only while Godot sends commands and renders returned native snapshots.
- No topology editor, topology transport, endgame simulation, GDScript
  legality checks, Python runtime calls from Godot, or authority transfer was
  added.
- Manual GUI verification should still check actual OS window behavior:
  launch the Godot project, open Replay Viewer, resize near the supported
  minimum, and confirm that left browser, game viewport, right inspector, and
  bottom controls remain visible.

## Acceptance Criteria

- Godot remains a product shell / replay-view and live-shell presentation
  surface.
- Python remains the semantic oracle.
- C++ authority is unchanged.
- Right inspector panels are reserved by container minimums instead of relying
  on incidental child panel sizes.
- Layout regression coverage catches inspector collapse or game-panel
  over-expansion.
