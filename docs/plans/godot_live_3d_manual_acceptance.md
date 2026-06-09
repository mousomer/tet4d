# Godot Live 3D Manual Acceptance

Role: checklist
Status: pending after failed initial inspection
Source of truth: docs/plans/gameboard_visual_language_design.md
Supersedes: none
Stage: 22f manual acceptance gate
Last updated: 2026-06-09

## Purpose

This checklist records the manual Stage 22f gate for the Godot Live 3D board.
It must be executed after Stage 22e implementation work and before Stage 23
Live Plain 4D begins.

Stage 23 remains blocked until this checklist is manually executed and marked
passed.

## Initial Failed Inspection

An initial Stage 22f inspection on 2026-06-09 did not pass. The rejected state
had these visual-interface failures:

- Live 3D default/Fit View read from below the board instead of slightly above.
- Camera preset and view-state diagnostics were not visible.
- Bundle status could be clipped before the important status was readable.
- Active Live 3D cells were not visually distinct enough from locked cells.
- The active piece still needed a visible origin/orientation cue.

Stage 22g corrects these observations as a visual-only pass. It does not mark
Stage 22f passed; this checklist must be rerun manually after Stage 22g.

## Checklist

- [ ] Godot opens the replay scene without load errors.
- [ ] Bundle status is visible.
- [ ] Bundle status primary text is compact and readable.
- [ ] Top bar is visible and not clipped.
- [ ] Left case browser is visible.
- [ ] Right diagnostics/events/settings panel is fully visible.
- [ ] Bottom playback controls are visible and clickable.
- [ ] Board is centered inside the board panel.
- [ ] Board does not overlap side panels.
- [ ] 3D case is readable on first load.
- [ ] 4D W/layer representation is understandable.
- [ ] Cells and traces/markers use the same coordinate projection.
- [ ] No fake motion is introduced.
- [ ] Playback frame stepping works.
- [ ] Play/pause works.
- [ ] Reset works.
- [ ] Resize preserves panel visibility.
- [ ] Minimum supported viewport preserves required text.
- [ ] Quit/back path works or is explicitly documented as still pending.

## Live 3D Visual-Language Checks

- [ ] Cells read as solid external cubes.
- [ ] Active-piece shape is decipherable quickly.
- [ ] Piece direction is not ambiguous.
- [ ] `X`, `Y`, and `Z` axes are distinguishable.
- [ ] Drop axis is clear.
- [ ] `XZ` and `YZ` rotations are understandable.
- [ ] Rotation-plane feedback is visible.
- [ ] Score, status, and game-over are visible.
- [ ] `Fit View` returns to the canonical exterior view.
- [ ] Canonical Live 3D view is slightly above the board, not below it.
- [ ] Camera preset/projection/yaw/pitch/roll/fit state are visible.
- [ ] Active cells are stronger than locked cells.
- [ ] Active-piece origin/orientation marker is visible.
- [ ] Live 2D is unaffected.
- [ ] Replay is unaffected.

## Current Status

Pending after failed initial inspection. Stage 22g is the visual-only
correction pass for the failed observations above. A human manual rerun must
mark this checklist passed before Stage 23 can begin.
