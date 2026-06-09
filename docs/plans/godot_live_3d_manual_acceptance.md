# Godot Live 3D Manual Acceptance

Role: checklist
Status: pending
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

## Checklist

- [ ] Godot opens the replay scene without load errors.
- [ ] Bundle status is visible.
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
- [ ] Live 2D is unaffected.
- [ ] Replay is unaffected.

## Current Status

Pending. This task updates the shell/layout and presentation boundary, but it
does not perform the required manual Live 3D acceptance pass.
