# Bounded Godot practice Explorer

This plan records **bounded 2D/3D/4D practice and pending novice
acceptance**. The 2D access repair composes existing bounded native queries;
it does not activate T2 topology transport or complete its transfer. It is not the forward topology roadmap. The normative 2D/3D/4D
preset/builder and movement contract is `docs/rds/RDS_EXPLORER_TOPOLOGIES.md`;
see its stages T1-T7. Retain these bounded regression requirements without
imposing a bounded-only restriction on the new Explorer.

Role: spec
Status: active
Source of truth: this file for bounded implementation scope and novice acceptance tasks
Supersedes: none
Authority: `professional_godot_game_programme.md` section 8 and
`spatial_intuition_research_plan.md` E1. Product contract:
`docs/architecture/bounded_practice_explorer.md`.

## Scope and acceptance

Implement one bounded Sandbox in the existing Godot 3D/4D viewer. Reuse the
native geometry, bounded-pose and topology-step queries and existing Godot
camera, exact basis, slice projection and control-frame owners. Add a direct
Explorer menu entry, dimension selection, deliberate movement on every axis,
all object rotation planes, a View-first rail without debug readouts,
independent slice inspection, object retry, view reset and ordinary Play entry.

Automated acceptance covers no elapsed-time movement or locking, atomic wall
rejection, native query conformance, inverse/four-turn rotations, retry,
independent camera/basis/slice/object state, camera-relative 3D/4D movement,
normal Play restart and lifecycle cleanup. The full repository gate and Godot
suite must pass. Do not claim novice or physical-device acceptance from tests.

## Layer scope

| Provider | Consumer | Evidence |
| --- | --- | --- |
| Native T2A indexed piece runtime | Godot 2D topology selector and practice adapter | Admitted profile/identity/failure/Retry adapter tests, core preservation suite and Explorer seam integration |
| Existing native geometry, pose and step queries | Godot practice adapter | Query conformance and boundary tests |
| Existing native configured piece selection | Detached Sandbox pose | Fixed-seed initialization and deterministic retry |
| Existing Godot control-frame, basis and camera owners | Practice input and view | 3D/4D input and isolation regressions |
| Practice adapter | Existing renderer and practice controls | Bootstrap integration, coordinates and markers |

No native gameplay/replay format changes, topology editor, non-bounded
selector, study collection, backend, campaign, release-matrix changes or
reopening of accepted board allocation. Play starts a fresh ordinary session
from the frozen bounded setup; it does not pretend a Sandbox pose is a replay.

## Local review and verification

Launch the game bootstrap using the supported Godot executable:

```sh
"$GODOT_BIN" --path godot/Tet4D.Godot res://scenes/game_bootstrap.tscn
```

Open Main Menu → Explorer or press `E` on the Main Menu. Choose 2D/3D/4D in
the practice rail. In 2D, use left/right and the usual rotation bindings;
W/S or Up/Down move Y, A/D or Left/Right move X; R/T rotate XY and
Backspace retries, sharing the 3D action inventory. PageUp/PageDown do not move
the 2D piece. The View page offers bounded, X/Y cylinders and torus profiles;
verify seam crossing, wrapped-axis inverse, unwrapped walls, exact Retry and
atomic rejection of an incompatible switch. Möbius/Klein and non-bounded
rotations remain visibly unavailable. Movement must preserve panel node IDs,
selected tab, scroll, rectangles and fit scale through intermediate frames. Verify the
flat board, all seven classic pieces, Retry, menu return and fresh Play.
2D has no orbit, basis, slice, Z-axis or W-axis controls. Entry and slice selection draw no automatic dots; New
target (Piece page) explicitly marks a reachable target away from the object.
In 4D, Slice −/+ moves the active-slice frame off the object's layer; basis
turns and Reset View return it to the object.
View opens first with one unified VIEW helper/control panel. Its keycaps are
clickable and show bindings for all six exact planes, look, zoom, framing and
slice inspection; Piece contains selection, replacement, Retry and canonical object
controls. The lower helper deck stays, showing Explorer translation, rotation,
Z/X and Retry rows; cell/neighbor/angle readouts are hidden.
Z moves up and X moves down on compact keyboards; PageUp/PageDown remain
aliases. Repeated movement must preserve panel controls, the selected tab and
scroll position, updating only changed readouts.
The same invariants apply to camera/basis changes, Reset/Fit View and piece
replacement. Use the piece selector for direct native-catalog choice or
Replace piece (Space; P alias) for the next catalogue entry; Retry restores that choice.
Test Space after clicking a control, and switch 3D/4D from the Piece or View tab;
the Explorer tab/control instances must survive dimension changes.
Verify every VIEW keycap against its shortcut, including Shift+1/2 (XY),
Shift+3/4 (YZ), Shift+5/6 (YW), plain 1–6 (XZ/XW/ZW), O/L, I/K, zoom,
reset and [/] slice inspection. Rebind and clear a Y-plane action: the same
keycap must reflect the current binding without resurrecting its default.
Space, moves, rotations, rejected moves, Retry, camera/basis/slice changes and
Reset/Fit View must preserve panel/board rectangles, fit scales and outer
scrollbar visibility through intermediate frames, not only after settling.
Rejected-action feedback occupies a font-relative scrolling slot; long messages remain
complete and reachable without growing the surrounding HUD. Check at
1280×800, 1280×720 and narrow windows; resizing, UI font/scale and density
changes must still trigger appropriate layout.
For reproducible review, use Standard board, Fixed Seed
1337 and speed 1 in each dimension's setup before opening Explorer. Piece contains canonical-axis controls; View separates camera, exact basis
and slice selection. Exercise XY, YZ and YW view turns, including inverses;
the object must remain fixed and Play must restore a Y-fixed ordinary basis.
Review at 1280×720/800 and fullscreen. Retry Object restores the object;
Reset View restores presentation; Play starts a fresh bounded game.

```sh
"$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_practice_explorer.gd
./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
```

## Novice acceptance (EXPLORER_LEARNING_READY remains pending)

- Discover Explorer from the main menu and switch between 3D and 4D.
- Reach the marked coordinate using deliberate movement, including both Y
  directions, without waiting for gravity or accidentally locking a piece.
- Predict a rotation, execute it and recover the original object using Retry.
- Orbit the camera, change the exact 4D basis and inspect a different slice;
  identify which state changed each time. Reset View without moving the object.
- Use XY, YZ and YW view turns, undo them, and verify the object stays fixed.
  Confirm no coordinate, neighbor or view-angle debug readouts occupy the rail.
- Recover from disorientation, start ordinary bounded Play, then return to
  Explorer without inheriting practice controls or timing into normal Play.
- Review readable controls and unclipped board at supported window sizes.

Record actual observed results and failures before promoting the gate. A
published test build and owner review remain separate from implementation.
