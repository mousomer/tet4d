# Godot Live 3D Manual Acceptance

Role: checklist
Status: passed after Stage 22g corrections
Source of truth: docs/plans/gameboard_visual_language_design.md
Supersedes: none
Stage: 22f manual acceptance gate
Last updated: 2026-06-09

## Purpose

This checklist records the manual Stage 22f gate for the Godot Live 3D board.
It must be executed after Stage 22e implementation work and before Stage 23
Live Plain 4D begins.

Stage 22f manual Live 3D visual acceptance passed after Stage 22g corrections.
Stage 23 Live Plain 4D Godot Prototype is now unblocked.

## Initial Failed Inspection

An initial Stage 22f inspection on 2026-06-09 did not pass. The rejected state
had these visual-interface failures:

- Live 3D default/Fit View read from below the board instead of slightly above.
- Camera preset and view-state diagnostics were not visible.
- Bundle status could be clipped before the important status was readable.
- Active Live 3D cells were not visually distinct enough from locked cells.
- The active piece still needed a visible origin/orientation cue.

Stage 22g corrected these observations as a visual-only pass. The manual
Stage 22f rerun passed after those corrections.

## Checklist

- [x] Godot opens the replay scene without load errors.
- [x] Bundle status is visible.
- [x] Bundle status primary text is compact and readable.
- [x] Top bar is visible and not clipped.
- [x] Left case browser is visible.
- [x] Right diagnostics/events/settings panel is fully visible.
- [x] Bottom playback controls are visible and clickable.
- [x] Board is centered inside the board panel.
- [x] Board does not overlap side panels.
- [x] 3D case is readable on first load.
- [x] 4D W/layer representation is understandable.
- [x] Cells and traces/markers use the same coordinate projection.
- [x] No fake motion is introduced.
- [x] Playback frame stepping works.
- [x] Play/pause works.
- [x] Reset works.
- [x] Resize preserves panel visibility.
- [x] Minimum supported viewport preserves required text.
- [x] Quit/back path works or is explicitly documented as still pending.

## Live 3D Visual-Language Checks

- [x] Cells read as solid external cubes.
- [x] Active-piece shape is decipherable quickly.
- [x] Piece direction is not ambiguous.
- [x] `X`, `Y`, and `Z` axes are distinguishable.
- [x] Drop axis is clear.
- [x] `XZ` and `YZ` rotations are understandable.
- [x] Rotation-plane feedback is visible.
- [x] Score, status, and game-over are visible.
- [x] `Fit View` returns to the canonical exterior view.
- [x] Canonical Live 3D view is slightly above the board, not below it.
- [x] Camera preset/projection/yaw/pitch/roll/fit state are visible.
- [x] Active cells are stronger than locked cells.
- [x] Active-piece origin/orientation marker is visible.
- [x] Live 2D is unaffected.
- [x] Replay is unaffected.

## Current Status

Passed after Stage 22g corrections. Stage 22f manual Live 3D visual acceptance
passed after Stage 22g corrections. Stage 23 Live Plain 4D Godot Prototype is
now unblocked.
