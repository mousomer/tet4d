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

## Orchestration repair boundary

The accepted results and supplied pre-repair observations are locked in
`docs/design/ui_cockpit_result_lock_2026_10_27.md`. The bounded plan is
`docs/plans/ui_cockpit_orchestration_repair.md`; the helper-state extraction is
implemented, and ordinary layout scheduling/policy are extracted. Designer
panel lifecycle is delegated to DesignerPanelSession; shell conversion remains
pending.
Owner decision (2026-10-27): explicit Fit finishes the requested orbit before
measuring size, anchor and board demand; normal orbit easing is unchanged.
Leaving/restarting a helper-fit search clears pending/search state. These two
source repairs now pass focused camera/cockpit suites under the owner's
relevant-test authorization. Full integration/manual acceptance remains pending;
see `docs/history/ui_cockpit_focused_verification_2026_10_30.md`. No layout or
scale retuning is authorized.

## Helper fit ownership

`HelperFitState` owns one group's relaxed/compact/probing transitions, recorded
height, sample agreement, scale interval and cancellation. Its public `observe`
operation consumes scalar measurements, a transient room policy, frame number
and intrinsic content identity; it returns compact/scale/remeasure decisions.
It stores no scene nodes and schedules no work. `LiveCockpit` measures and
applies those decisions through the existing fit containers and next-frame
scheduler. Packing policy, floor 0.6, step 0.02 and settle limit 30 are retained.

`ResponsivePanelPolicy.fit_content_key` observes intrinsic content: existing
control identity/visibility, text, font metrics, custom minimums, relevant theme
and spacing inputs. Compacted gaps use their recorded relaxed values. Measured
wrapping, allocated sizes and fit scale are excluded because they change during
probes. A changed key discards the old sample and restarts at relaxed full scale;
thus editing an existing label or font cannot retain a completed stale fit.
Constraint changes and fresh-subtree cancellation keep their previous behavior.
This remains local content invalidation; queued layout work is owned by the
coordinator described below.

## Layout coordination and policy

`CockpitLayoutCoordinator`, owned as a child of LiveCockpit, is the only
scheduler of ordinary cockpit policy/fit work. Metrics bursts and fit requests
coalesce on one next-frame callback. Fit requests take priority because they
already remeasure the current controls. Synchronous context setters call
`apply_now`, which advances the scheduling generation, cancels obsolete queued
work and applies immediately. Requests produced during application remain
queued for a later measurement pass. Designer ownership changes invalidate
old queued work without applying ordinary placement; tree exit disconnects it.
Completion requires coordinator idle plus every helper state settled.

Callbacks carry a scheduling generation and read fresh measurements. No queued
callback stores a measured layout or a policy decision from an old context.
`CockpitLayoutPolicy` computes placement, row packing, floor/gap decisions,
row heights, deck room and rail spare-width choices from explicit measured
values. It performs no scene-tree reads or mutation. LiveCockpit adapts measured
controls into those inputs and applies the results. The previous second
metrics flag, process-frame fit connection and deferred policy recheck path are
removed. Godot's own container-sort notifications remain; detached Designer
panel constraints belong to DesignerPanelSession under the Designer contract.

## Responsive panel contract

`scripts/ui/responsive_panel_policy.gd` owns shared presentation fitting:
constrain panels to the current usable application viewport, reflow controls
from their measured minimum widths, compact spacing, then scroll only the
content that still exceeds the available space. Fonts retain the existing
menu/helper readability floors. UI scale is a user preference, not a fitting
mechanism. Settings, setup, Designer and Design Laboratory consume this policy;
their Apply/Start, Cancel/Close and Back actions stay reachable outside long
content. Popups are clamped when opened and when their owning window resizes.

Width, height, fullscreen, UI scale and content changes must all invalidate
layout. Godot's current viewport/client size is the usable boundary; nominal
display resolution does not account for macOS backing scale or fullscreen
geometry. Wrapped content must not impose an unbounded horizontal minimum on
the enclosing panel. Scroll surfaces follow keyboard focus, and automatic
scrollbars disappear when measured content fits.

Helper overlays fit independently of gameplay allocation. Stage 58 side-rail,
legend-deck, board-region and camera contracts remain owned by the cockpit and
presentation authorities; fitting an editor must not shrink the board.

Regression evidence covers 1512×982, 1440×900, 1280×720, 1024×640 and 800×500
logical pixels, height-only changes, maximum UI scale, and actual macOS
windowed/fullscreen/windowed transitions. Geometry and scroll reachability
assertions accompany rendered screenshots; neither substitutes for the other.

### Failure diagnosis and ownership

| Surface | Shared failure | Correction |
| --- | --- | --- |
| Main menu | One tall command list plus nested margins exceeded ordinary client heights. | The single list stays (Play, Play 2D/3D/4D, Change Setup, then LEARN and SYSTEM) with its spacing and font sizes, and scales as a whole to fit the window, to `MENU_FIT_SCALE_FLOOR` (0.5) before it scrolls. |
| Settings | Disabled horizontal scrolling propagated fixed label/control minimums: a requested 280 px panel grew to 390 px. | Decouple scroll minimums and reflow measured rows; keep controls at their natural readable height. |
| Setup | Fixed 720 px content minimum and actions inside the content scroll. | Bound preferred width, reflow fields, and reserve a fixed action footer. |
| Designer | Nested scrolls and action HBoxes imposed a 539 px width on a requested 400 px editor. | One bounded content scroll, flowing action rows, wrapped labels and fixed close actions. |
| Detached helper panels | A wide 4D deck layout retained horizontal minimums inside a narrow movable frame. | Reflow detached guidance vertically, clamp helper frames to the client area, and restore the ordinary legend on exit. |
| Guided onboarding | An unwrapped progress line and the header's sibling minimums widened the guide beyond the client. | Bound the guide independently, wrap text, retain its natural height when it fits, and pin Hide Guide above fallback body scrolling. |
| Live navigation/actions | At enlarged UI scale below the desktop minimum, a horizontal header pushed session actions off-screen. | Fit the header to the client width and stack its measured columns only when they cannot fit side by side. |
| Design Laboratory | A 440×560 minimum and fixed overlay anchors escaped short client areas. | Viewport-bound placement, flowing actions and content scrolling. |
| Diagnostics | Two stacked panel minimum heights could exceed the scaled client area. | Bound their common content scroll while retaining navigation. |
| Dialogs and selectors | Position was calculated at open time and could become stale after resize. | Clamp current size and position on open, resize and theme/content changes. |

These are Godot container/minimum-size failures. macOS backing scale and
fullscreen are separate measurement inputs; no nominal screen-height deduction
or board-size workaround is part of the repair.

### Live cockpit helper panels

Every shell container that carries the desktop minimum (680×520) is clamped to
the window, the viewer's outer column included; one left unclamped kept the
cockpit 520 units tall in shorter windows and ran the board and its helpers
off the bottom edge. A deck below the board is likewise capped to what the
window leaves under the board's minimum, but never below one row at the scale
floor, so a short window with the guide open cannot hide it outright.

Live 4D's wide, short slice row rarely uses the shared 240-unit board floor,
so it has its own (`LIVE_4D_BODY_MIN_HEIGHT`, 160), and a deck below the board
packs NEXT/HOLD first, as the rail and the split column already do. In a small
window the deck therefore keeps NEXT/HOLD and MOVE on screen.

The live cockpit and the Main Menu are owner-accepted (2026-10-25) and locked
by `tests/test_locked_shell_layouts.gd`: the menu stays one list with Play
2D/3D/4D and scales as a whole; the 2D/3D rail shows every helper without a
scrollbar at 1440×900 and 1280×720, with whole NEXT/HOLD names and the 3D MOVE
compass beside its drop keys; Live 4D keeps its split without helper
scrollbars there, and in a small window its deck leads with NEXT/HOLD on
screen. Changing any of these is a product decision, not a layout fix.

Display safe-area insets (a fullscreen MacBook notch) arrive in window pixels
and are converted to canvas units before they become shell margins
(`SafeAreaInsets.to_canvas`). Applied as pixels, a 78-pixel notch became a
78-unit band above the cockpit on a canvas where it spans about 24 units.

The normal-play helpers (NEXT/HOLD, the piece legend and VIEW, in the 2D/3D
side rail, the Live 4D split column, or the deck below the board) follow the
same order, owned by `scripts/ui/live_cockpit.gd`: give the measured content
its room, compact, shrink the content to fit, and scroll only what still
overflows at the readability floor.

- Compaction halves the helpers' vertical gaps and margins. A group compacts
  only when its relaxed height, agreed across a frame boundary, exceeds its
  room, and relaxes as soon as that recorded height fits again. A constant the
  owning strip changes while compacted is the strip's and is never overwritten
  on restore.
- Text and content then shrink together: `scripts/ui/fit_scale_container.gd`
  shows the deck or column content uniformly scaled, laid out at its width
  divided by the scale, so labels, keycaps, glyphs and previews stay in
  proportion. Wider layout wraps less, so the shown height is not proportional
  to the scale: the cockpit searches for the largest scale that fits, one
  settled measurement at a time, from a proportional first guess. The floor is
  `FIT_SCALE_FLOOR` (0.6, keeping 22-unit control hints near 13 units); only
  content that overflows at the floor scrolls. A new room or width restarts the
  search from full scale, so the result depends on the current size and
  content, never on resize history. `LiveCockpit.fit_settled()` reports when
  every step has decided; layout checks wait for it.
- The Live 4D split column spans the whole stage height beside board and
  legend deck whenever the narrowed deck still holds the legend's single line
  with room for its scrollbar; otherwise the deck keeps the full width and the
  column the board's height. The 1280×720 opening-window legend contract is
  unchanged.
- The camera fits the board to any rect, so the board has no aspect-derived
  demand to measure. A deck below the board may use the stage height above a
  reserved half for the board (`BOARD_RESERVE_STAGE_SHARE`) before it
  scrolls; the previous 20 % share remains its floor.
- The 2D/3D side rail keeps its share-based width as a floor and grows to what
  its content asks for: NEXT/HOLD cards wide enough for the longest built-in
  piece name (`PiecePreviewLayout.PIECE_NAME_REFERENCE`) and, in 3D, the MOVE
  compass beside its drop keys. It grows only into width the right-anchored
  board leaves unused. The camera reports the fitted board's width per unit of
  height (`CameraRig.fitted_board_aspect`) from span and margin alone, so the
  board's demand follows the stage height, and the rail never takes the
  board's width or the board surface's minimum. The board's on-screen size is
  unchanged.
- The cockpit's metric signals (deck and split-column resizes, module and
  header minimum sizes) never run placement inline. They can fire while Godot
  propagates visibility or sorts a container, when it refuses `add_child` on
  the node being notified; `reparent()` has already removed the node by then,
  so a refused move leaves the Live 4D deck with no parent at all. A burst
  queues one check for the next frame (`_queue_deck_metrics_check`), and
  `fit_settled()` stays false while it waits; signals raised by the policy's
  own pass are dropped. A `call_deferred` check would run in the idle flush
  that sorts the containers its pass resized, feed each pass back as new work
  and overflow the message queue.

`tests/support/panel_responsive_probe.gd#inspect_cockpit` fails a deck, rail
or split column that scrolls before compacting or above the scale floor, a
full-height column shorter than its stage, a below-board deck that scrolls
short of its allowance, a rail narrower than its content while the board
leaves width unused, a trimmed NEXT/HOLD name in that state, and any nested
helper scrollbar. It runs at every size, UI scale and live mode, with the
guide open and closed, after the fit settles. In the rendered macOS run only
the Live 4D deck at 1280×720 with enlarged UI still scrolls, at the floor.
Regenerated Designer controls reapply the shared shell style so opening or
changing the active mode cannot leave default dark checkbox text on a dark
panel. Selected option text wraps rather than truncating to the panel width.

### Viewer regression coverage

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
