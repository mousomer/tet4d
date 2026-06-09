# Live Plain ND Godot Prototype Plan

Role: Stage 21 implementation plan  
Status: Stage 22 live plain 3D implemented; Stage 22d complete; Stage 22e partial; Stage 22f failed initial inspection/pending rerun; Stage 22g corrective pass; Stage 23 blocked
Last updated: 2026-06-09

## 1. Decision summary

Stage 21 is planning-only. It does not add live 3D/4D code, native live ND
session APIs, Godot modes, topology, endgame, C#, or Python runtime calls from
Godot.

The implementation sequence is:

1. Stage 22: Live Plain 3D Godot Prototype.
2. Stage 22d: Gameboard Visual Language Design.
3. Stage 22e: Implement Live 3D Gameboard Visual Language.
4. Stage 22f: Manual Live 3D Visual Acceptance.
5. Stage 22g: Correct failed Live 3D visual acceptance observations when
   needed.
6. Stage 22f: Rerun Manual Live 3D Visual Acceptance.
7. Stage 23: Live Plain 4D Godot Prototype only after Stage 22f passes.
8. Stage 24: Live ND polish and hardening.
9. Stage 25: topology parity planning.

Stage 22 should start with live plain 3D only. This keeps control, rendering,
HUD, and testing risk below the accepted live 2D shell while reusing the native
plain-ND sidecar semantics proven by the Stage 15, 18, 19, and 20 parity
traces.

The future native implementation should use an internal dimension-parameterized
plain ND session model, but expose a narrow Stage 22 Godot-facing live 3D
facade. That keeps the Stage 22 API small without baking 3D-only shortcuts into
the core.

## 2. Current baseline

The accepted baseline is:

- Godot is the GDScript product shell.
- C++ GDExtension owns live plain bounded 2D gameplay through
  `Plain2DSession`.
- Godot captures input, owns presentation timing and rendering, sends command
  strings, and displays native snapshots/status.
- C++ owns 2D movement, rotation, gravity tick results, hard drop, lock, line
  clear, scoring, piece sequence, spawn, game-over, and `state_hash`.
- Python remains the semantic oracle until native behavior has explicit parity
  coverage.
- Replay mode remains separate from live mode and consumes copied generated
  bundle traces.

Native plain-ND trace parity now covers:

- `gameplay_plain_3d_short`
- `gameplay_plain_4d_short`
- `gameplay_plain_3d_rotation_short`
- `gameplay_plain_4d_rotation_short`
- `gameplay_plain_3d_plane_clear_short`
- `gameplay_plain_4d_plane_clear_short`
- `gameplay_plain_3d_spawn_blocked_game_over`
- `gameplay_plain_4d_spawn_blocked_game_over`

Live Godot support still covers only plain bounded 2D.

Stage 22 settlement:

- live plain 3D now exists as its own Godot mode;
- native C++ owns the live 3D session, command results, score/clear,
  spawn/game-over, and `state_hash`;
- Godot reuses the existing trace coordinate mapper and renderer;
- accepted live plain 2D and replay mode remain preserved;
- live 4D remains Stage 23.

Stage 22b settlement target:

- live 3D cells must render as solid cuboids through the existing
  `TraceCoordinateMapper` / `TraceSceneRenderer` / `CellRenderer` path;
- Live 3D may use dimension-specific visual roles, materials, outlines, and
  camera fit presets, but Live 2D and Replay styling must remain separate;
- XZ/YZ rotation readability is a HUD/camera/rendering concern when C++ parity
  passes, with explicit signed plane labels such as `XZ+` / `YZ-` sourced from
  returned native command status;
- Stage 22b must not add live 4D, topology, endgame, C#, Python runtime calls
  from Godot, Godot-side legality, or independent rotation transforms.

Stage 22c settlement target:

- live 3D cells must read as solid exterior blocks, not interior walls,
  translucent panels, or hollow cages;
- Live 3D cell faces should use opaque exterior face panels with restrained
  silhouette outlines and subtle face-orientation brightness cues;
- rotation feedback may briefly pulse the active piece outline after a returned
  native rotation snapshot, but Godot must not interpolate or transform cells
  independently of C++ state;
- the accepted Live 2D shallow board style and Replay rendering must remain
  separate.

Stage 22d settlement:

- `docs/plans/gameboard_visual_language_design.md` is the gameboard visual-
  language authority;
- Stage 22d is design-only and adds no rendering implementation;
- Live 3D must use a diagrammatic visual grammar with a canonical exterior
  view, stable axis landmarks, an explicit active-piece orientation cue,
  rotation-plane feedback, and primary-surface HUD state;
- Stage 22e implements that authority and Stage 22f performs manual Live 3D
  visual acceptance;
- Stage 23 must not start until Stage 22f passes.

Stage 22g correction target:

- correct the failed initial Stage 22f visual observations without changing
  gameplay semantics or trace parity;
- make Live 3D default/Fit View slightly above the board and expose camera
  preset/projection/yaw/pitch/roll/fit diagnostics;
- keep bundle status compact in the top bar while preserving digest/detail
  text in the inspector;
- make active Live 3D cells visually stronger than locked cells and add a
  visible active-piece origin/orientation marker;
- leave Stage 22f pending until a human reruns the manual checklist.

## 3. Why live ND now

Native plain-ND parity has passed the first risk cluster: movement/drop,
rotation metadata, plane clear/scoring, spawn-blocked game-over, canonical
snapshot fields, and frame/final `state_hash` for small 3D/4D fixtures.

The next risk is no longer whether the C++ sidecar can match the Python
fixture semantics. The next risk is product integration:

- how live 3D controls should map to ND commands;
- how direct rotation-plane controls should feel without moving legality into
  GDScript;
- how live ND snapshots should reuse the existing replay renderer;
- how HUD/status fields should stay readable during play;
- how to introduce 4D W-slices without destabilizing accepted live 2D.

Planning those boundaries before implementation keeps Stage 22 narrow and
reviewable.

## 4. What remains deferred

Stage 21 and the next live prototype stages defer:

- topology transport;
- wrap, invert, sphere-like, and custom topology gameplay;
- endgame simulation;
- C#;
- Python runtime calls from Godot;
- Godot-side gameplay legality;
- refactoring the accepted live plain 2D session;
- generic multi-session live ND management unless Stage 23/24 explicitly needs
  it;
- ghost/drop target cells unless C++ computes and exposes them;
- broad RNG/bag parity beyond the deterministic live sequence chosen for the
  native session;
- broader post-game-over command behavior unless future tests observe it.

## 5. Mode design: Live 3D / Live 4D / Live ND

Use staged separate product modes, backed by an evolvable ND core.

Stage 22 should add `Live Plain 3D` as its own Godot mode. It should not expose
`Live 4D` yet and should not replace the accepted `Live Plain 2D` path.

Stage 23 should add `Live Plain 4D` only after Stage 22f accepts the Live 3D
visual language. 4D needs W-slice navigation/presentation and six rotation
planes, so it must not inherit unresolved 3D ambiguity.

Stage 24 may consolidate polish across live 3D/4D and decide whether the
visible product should keep separate `Live 3D` / `Live 4D` entries or present a
single `Live ND` entry with a dimension selector. That decision should be made
after both modes have real playtest feedback.

## 6. Native C++ API plan

The C++ core should add an internal live plain ND session type in Stage 22:

```text
PlainNDSession
  dimension
  board_shape
  gravity_axis
  deterministic_piece_sequence
  GameStateND
  reset()
  apply_command(GameCommandND)
  tick()
  snapshot_json()
  status()
  state_hash()
```

The internal type should reuse the sidecar ND model and Python-compatible
snapshot conventions already proven by trace parity. It should not refactor
`Plain2DSession`.

The Stage 22 Godot-facing API should remain narrow and 3D-specific:

```text
live_3d_reset() -> Dictionary/String status
live_3d_apply_command(command: Dictionary/String) -> Dictionary/String status
live_3d_tick() -> Dictionary/String status
live_3d_snapshot_json() -> String
live_3d_status() -> Dictionary/String
live_3d_state_hash() -> String
```

The API names may follow the existing `live_2d_*` naming pattern in
`Tet4DCoreApi` for consistency. Command payloads should map to ND command
objects:

```text
move_axis(axis, delta)
rotate(axis_a, axis_b, delta)
soft_drop
hard_drop
tick
reset
pause
```

Stage 22 should not expose a generic Godot API such as
`create_plain_nd_session(dimension, seed)` unless implementation pressure proves
that the narrow facade would create duplication. The preferred compromise is:
dimension-generic C++ internals, narrow live 3D Godot facade first.

Stage 23 can add `live_4d_*` methods over the same internal session owner.
Stage 24 can then evaluate a generic session API:

```text
create_plain_nd_session(dimension: int, fixture_or_seed: String) -> session_id
reset_plain_nd_session(session_id)
destroy_plain_nd_session(session_id)
apply_plain_nd_command(session_id, command)
tick_plain_nd_session(session_id)
get_plain_nd_snapshot_json(session_id)
get_plain_nd_status(session_id)
get_plain_nd_state_hash(session_id)
```

## 7. Godot bridge plan

The Godot bridge should remain a thin wrapper over native C++:

- add live 3D bridge methods only when Stage 22 implements the native API;
- convert Godot input events into command dictionaries or command strings;
- never calculate collision, valid moves, rotation acceptance, drop distance,
  clears, score, spawn, game-over, or hashes in GDScript;
- expose the current native snapshot JSON unchanged except for parsing into a
  renderer-friendly dictionary;
- keep replay, live 2D, and live 3D mode state separate.

The Stage 22 UI should add a `Live Plain 3D` mode entry without changing replay
case loading or live 2D session lifetime. Switching away from live 3D may pause
presentation ticks, but should not destroy the native session unless the user
chooses reset/new game.

## 8. Input/control model

Stage 22 should use direct command bindings for live 3D:

```text
A / Left      move_axis(0, -1)
D / Right     move_axis(0, +1)
W / Up        move_axis(2, -1)
S / Down      move_axis(2, +1)
Shift         soft_drop
Space         hard_drop
P             pause/resume presentation dispatch
Backspace     reset/new game
Tab           switch between live/replay surfaces
Esc / Q       quit/back
```

This deliberately reserves the gravity axis for soft/hard drop rather than
ordinary `move_axis(1, delta)` input. C++ still owns the legality and lifecycle
effects of every command.

Existing live 2D key hints can continue using their accepted bindings. Live 3D
should not inherit a conflicting `R Reset` binding because `R` is needed for
direct rotation.

## 9. Rotation-control model

Stage 22 should avoid a hidden rotation-plane selector for the first 3D
prototype. Direct key pairs are clearer and align with existing keybinding
defaults:

```text
R / T     rotate(axis_a=0, axis_b=1, delta=-1 / +1)  XY
F / G     rotate(axis_a=0, axis_b=2, delta=-1 / +1)  XZ
V / B     rotate(axis_a=1, axis_b=2, delta=-1 / +1)  YZ
```

The HUD should show the most recent rotation plane and status returned by C++.
Godot may label the controls, but must not reinterpret failed rotation results.

Stage 22b should show a signed last-rotation label in the Live 3D HUD
(`XY+`, `XY-`, `XZ+`, `XZ-`, `YZ+`, `YZ-`) derived from the returned native
command string/status. Godot may preserve that label for readability after
later non-rotation commands, but it must not apply a visual rotation transform
or change state before the C++ snapshot is returned.

Stage 23 should extend the same direct-pair model for 4D:

```text
R / T     XY
F / G     XZ
V / B     YZ
Y / U     XW
H / J     YW
N / M     ZW
Q / E     move_axis(3, -1 / +1)
```

A future optional selector can be added later for accessibility, but it should
send the same command vocabulary and should not replace direct bindings in the
first prototype.

## 10. Display/rendering model

Live ND must reuse the existing replay renderer and coordinate mapper.

Correct pipeline:

```text
C++ live ND snapshot
  -> Godot snapshot adapter / parsed JSON
  -> TraceCoordinateMapper
  -> TraceSceneRenderer
  -> GridRenderer / CellRenderer
```

The live ND snapshot should use the same renderer-facing fields already used by
replay and live 2D:

- `trace_type` such as `live_3d` or `live_4d`;
- `dimension`;
- `board_shape`;
- `active_cells`;
- `locked_cells`;
- score/clear fields;
- `game_over`;
- current/next piece fields when exposed by C++;
- `last_command` and `last_command_status`;
- `state_hash`;
- metadata/diagnostics for display only.

Stage 22 should not create a new live 3D renderer or a new coordinate system.
If styling needs to distinguish live cells from replay cells, extend the
existing renderer role selection to treat `trace_type` values beginning with
`live_` as live snapshots.

Stage 22b should keep that pipeline and split Live 3D presentation from the
accepted Live 2D shallow board language: Live 3D cells are full cuboids with
lit face contrast and edge outlines, while Live 2D remains on the existing
flat board/grid styling.

Stage 22c should prefer exterior-face readability over cage-like outlines:
Live 3D active and locked cells should use opaque shaded face panels, a dark
but restrained external silhouette, and no transparent-wall default.

Stage 22e must implement the visual grammar in
`docs/plans/gameboard_visual_language_design.md` without adding a second
renderer or coordinate mapper. The Stage 22e implementation boundary now
requires an explicit Godot shell layout with reserved left/board/right regions,
a scroll-safe right inspector, and a focused presentation/projection owner
between snapshots and renderer nodes. The remaining visual additions are
presentation-only: canonical exterior diagram view behavior, axis/landmark
cues, at least one explicit active-piece origin/orientation cue,
rotation-plane feedback, and primary-surface HUD visibility.

## 11. 4D W-slice presentation

After Stage 22f passes, Stage 23 should reuse the existing W-slice rendering
path:

- one visible board grid per W layer;
- mapper-owned W offsets;
- `W=n` labels from the existing grid renderer;
- active and locked cells rendered in their actual W layer;
- camera fit computed from mapped bounds across all W slices.

4D live HUD should include:

- focused W slice when the UI later adds focus;
- W movement command status;
- current direct rotation plane;
- score/clears and state hash.

The first live 4D prototype should not add gameplay semantics tied to a
selected slice. W focus is presentation/navigation only unless C++ later exposes
an explicit command that changes gameplay state.

## 12. HUD/status design

Live 3D and live 4D HUDs should make the native authority visible:

```text
LIVE 3D · C++ CORE
LIVE 4D · C++ CORE
```

Required fields:

- score;
- generic clear count field used by C++/Python snapshots, currently `lines`
  for the plain-ND traces;
- `state_hash`;
- current piece;
- next piece if exposed by C++;
- selected or last rotation plane;
- last command;
- last command status;
- running/paused/game-over state;
- compact mode-specific controls hint strip.

Score and clear count must stay in the primary HUD area, not buried only in a
diagnostic side panel. Diagnostics may show full JSON or metadata, but the
playable status strip must remain readable during normal play.

## 13. Test plan

Future Stage 22 native tests:

- create/reset a live 3D session;
- verify deterministic initial snapshot and hash;
- apply `move_axis(0, +/-1)` and `move_axis(2, +/-1)`;
- apply each 3D rotation plane command;
- apply `soft_drop`, `hard_drop`, and `tick`;
- verify C++ owns command status and rejects illegal moves;
- verify reset restores deterministic initial state;
- verify game-over fixture behavior if a live fixture hook exists;
- keep all plain 2D and plain-ND parity traces passing.

Future Stage 22 Godot tests:

- bridge exposes live 3D methods only after native API exists;
- live 3D mode can be entered without destroying live 2D;
- commands route through the bridge;
- snapshot JSON parses and renders through the existing renderer path;
- HUD/hints are mode-specific;
- no GDScript legality checks are added.

Manual Stage 22 checks:

- live 3D starts from the main menu;
- X/Z movement works;
- XY/XZ/YZ rotations work;
- soft drop and hard drop work;
- HUD score/hash/status are readable;
- camera fit and replay mode still work;
- live 2D remains accepted.

## 14. Implementation sequence

Stage 22 - Live Plain 3D Godot Prototype:

- add internal C++ `PlainNDSession` owner for dimension `3`;
- expose only live 3D Godot-facing methods;
- add Godot `Live Plain 3D` mode and bridge calls;
- send ND command dictionaries/strings from input;
- render native live 3D snapshots through the existing trace renderer;
- add live 3D HUD/hints;
- preserve live 2D and replay tests.

Stage 22d - Gameboard Visual Language Design:

- add `docs/plans/gameboard_visual_language_design.md`;
- define the Live 3D diagrammatic grammar and future Live 4D constraints;
- add no rendering or gameplay implementation.

Stage 22e - Implement Live 3D Gameboard Visual Language:

- preserve the existing mapper/renderer path;
- reserve left case browser, board, right inspector, top status, and bottom
  playback regions structurally in the Godot shell;
- route snapshot-to-world projection through a focused presentation/projection
  owner rather than ad hoc renderer formulas;
- implement the canonical exterior diagram view;
- add axis landmarks, a drop-direction cue, and an active-piece
  origin/orientation cue;
- keep rotation-plane feedback and critical HUD state visible;
- preserve Live 2D and Replay.

Stage 22f - Manual Live 3D Visual Acceptance:

- run the checklist in `docs/plans/godot_live_3d_manual_acceptance.md`;
- block Live 4D until the checklist passes.

Stage 22g - Live 3D Visual Acceptance Corrections:

- correct failed Stage 22f visual observations only;
- preserve C++ gameplay semantics, rotation math, golden traces, Live 2D, and
  Replay;
- require a Stage 22f manual rerun before Stage 23.

Stage 23 - Live Plain 4D Godot Prototype, only after Stage 22f:

- reuse `PlainNDSession` for dimension `4`;
- expose live 4D bridge methods;
- render W-sliced live snapshots through the existing mapper/renderer;
- add W-axis movement and six direct rotation plane pairs;
- add live 4D HUD/hints.

Stage 24 - Live ND polish/hardening:

- tune input repeat, camera fit, and status readability;
- decide whether product navigation should stay split or become one `Live ND`
  selector;
- add next-piece, ghost/drop target, or preview fields only if C++ owns them;
- harden reset/session lifetime behavior.

Stage 25 - Topology parity planning:

- plan topology trace parity before adding wrap/invert/sphere-like live
  gameplay.

## 15. Risks and mitigations

- Risk: accepted live 2D regresses. Mitigation: do not refactor
  `Plain2DSession`; add live ND beside it and keep live 2D tests mandatory.
- Risk: Godot becomes gameplay authority. Mitigation: Godot sends commands and
  renders snapshots only; C++ owns legality and status.
- Risk: 3D controls are hard to learn. Mitigation: use direct axis and direct
  plane-pair bindings with a visible hint strip.
- Risk: 4D inherits unresolved 3D ambiguity. Mitigation: Stage 22e implements
  the visual grammar and Stage 22f must pass before Stage 23 starts.
- Risk: renderer coordinate drift. Mitigation: reuse `TraceCoordinateMapper`
  and existing replay renderers.
- Risk: native API over-generalizes too early. Mitigation: implement a
  dimension-generic internal session, but expose a narrow live 3D facade first.
- Risk: trace parity broadens accidentally. Mitigation: keep Python golden
  traces unchanged and keep `--all-plain-nd` green during every live stage.

## 16. Acceptance criteria for the next implementation stage

Stage 22 is accepted only if:

- live plain 3D starts from the Godot shell;
- C++ owns the live 3D session state and all gameplay legality;
- Godot sends only command payloads and renders returned snapshots;
- live 3D movement, rotation, soft drop, hard drop, gravity tick, lock, score,
  clear, spawn, game-over, and `state_hash` are native-owned;
- live 3D snapshots render through the existing mapper/renderer path;
- HUD shows `LIVE 3D · C++ CORE`, score, clear count, state hash, piece/status,
  and controls;
- live 2D remains accepted and passing;
- replay mode remains intact;
- all plain 2D and implemented plain-ND parity gates pass;
- no live 4D gameplay is added in Stage 22;
- no topology, endgame, C#, Python runtime calls, or Godot-side legality are
  added.

Stage 22d is complete when the design authority exists and the roadmap blocks
Stage 23 behind Stage 22e implementation plus Stage 22f manual visual
acceptance. The Stage 22f run record is owned by
`docs/plans/godot_live_3d_manual_acceptance.md` and remains pending until a
human manual pass marks it passed.
