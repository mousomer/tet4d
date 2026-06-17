# Live ND Manual Acceptance

Role: spec
Status: passed
Source of truth: docs/plans/live_plain_nd_godot_prototype_plan.md
Supersedes: none
Last updated: 2026-06-17

Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance after
Stage 23b/23c/23d corrections. Stage 24 is Live ND polish and hardening only:
Godot owns input, presentation, rendering, HUD, camera, layout, and mode
switching; C++ remains gameplay authority; Python remains the oracle/reference,
not a Godot runtime dependency. Topology and endgame remain deferred.

Stage 24 manual acceptance passed. Stage 25 topology planning is unblocked.

## Scope

- Live 2D, Live 3D, Live 4D, and Replay must remain usable.
- Switching away to Replay and back must resume the selected live mode without
  resetting the native C++ session.
- Reset must reset only the current live session.
- Space must hard-drop in every live mode before UI accept/back handling.
- Q must not quit/back in live modes.
- Esc remains the keyboard back/quit path.
- Live 4D keeps Q/E as W-/W+, H/J as YW rotation, and I/K, O/L, -/= as camera
  controls.
- Fit View remains the canonical recovery action.
- No topology, endgame, Godot-side gameplay legality, C#, or Python runtime
  calls from Godot are allowed.

## Replay

- [ ] Replay opens from the main scene.
- [ ] Case browser, frame stepping, play/pause, speed, and trace family
      controls work.
- [ ] Fit View recovers the replay board.
- [ ] Quit/back path works.
- [ ] Replay does not expose or simulate live gameplay semantics.

## Live 2D

- [ ] Live 2D opens and shows `LIVE 2D · C++ CORE`.
- [ ] Movement, rotation, soft drop, hard drop, pause, and reset work.
- [ ] Space hard-drops and does not activate focused UI controls.
- [ ] Q does not quit or dispatch a Live 2D gameplay command.
- [ ] Esc backs/quits.
- [ ] HUD shows score/lines, state hash, piece/next piece, last command/status,
      and running/paused/game-over state.
- [ ] Switching to Replay and back resumes the same native session without
      resetting it.
- [ ] Reset affects only Live 2D.

## Live 3D

- [ ] Live 3D opens in the accepted canonical exterior view.
- [ ] Active and locked cells remain readable and distinct.
- [ ] X/Y/Z/drop orientation remains understandable.
- [ ] R/T, F/G, and V/B rotations work and show signed feedback.
- [ ] Space hard-drops and does not activate focused UI controls.
- [ ] Q does not quit or dispatch a Live 3D gameplay command.
- [ ] Esc backs/quits.
- [ ] Fit View restores the accepted Live 3D view.
- [ ] Switching to Replay and back resumes the same native session without
      resetting it.
- [ ] Reset affects only Live 3D.

## Live 4D

- [ ] Live 4D opens in the accepted fitted W-slice view.
- [ ] W-slice headers are obvious and readable without searching.
- [ ] Q/E move W-/W+ and Q does not quit.
- [ ] Space hard-drops and does not activate focused UI controls.
- [ ] Esc backs/quits.
- [ ] H/J perform YW rotation and do not open Help.
- [ ] I/K pitch the camera.
- [ ] O/L yaw the camera.
- [ ] - zooms out and =/+ zoom in.
- [ ] Camera diagnostics change after camera controls.
- [ ] Fit View restores the full fitted W-slice layout.
- [ ] Zoom and Space still work after clicking panels/buttons.
- [ ] Zoom still works after switching away to Replay and back.
- [ ] Active and locked cells remain readable and distinct without glare.
- [ ] HUD shows score/lines, state hash, piece/next piece, last command/status,
      signed rotation feedback, active W context, and running/paused/game-over
      state.
- [ ] Switching to Replay and back resumes the same native session without
      resetting it.
- [ ] Reset affects only Live 4D and returns to fitted view.

## Reject Stage 24 If

- [ ] Any live mode loses gameplay input after clicking UI.
- [ ] Space triggers UI action in a live mode.
- [ ] Q quits or backs out in a live mode.
- [ ] Live 4D camera controls fail or mutate gameplay state.
- [ ] Fit View fails to recover Live 3D or Live 4D.
- [ ] HUD hints contradict actual controls.
- [ ] Live 2D, Live 3D, Live 4D, or Replay regresses.
- [ ] Topology or endgame behavior appears.
- [ ] Godot-side gameplay legality appears.
- [ ] C++ parity or governance gates fail.
