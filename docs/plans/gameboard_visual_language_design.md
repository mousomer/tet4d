# Gameboard Visual Language Design

Role: authority
Status: active
Source of truth: this file for gameboard visual-language decisions
Supersedes: ad hoc Live 3D readability notes in Stage 22b/22c
Stage: 22d design authority
Last updated: 2026-06-16

## 1. Decision Summary

Stage 22d is design-only. It defines the gameboard visual grammar and does not
implement rendering changes.

Stage 22g is a visual-only correction pass against this authority after an
initial Stage 22f manual inspection found the Live 3D default view, camera
diagnostics, bundle readability, and active-vs-locked contrast insufficient.
It does not change gameplay semantics, rotation math, trace parity, or the
accepted Live 2D/replay behavior.

The decisions are:

1. tet4d board rendering is diagrammatic, not realistic.
2. Live 3D uses a canonical exterior view.
3. Cells read as solid external cubes.
4. Active-piece orientation is actively disambiguated.
5. Axis markers are interface elements, not decoration.
6. Rotation-plane feedback is mandatory.
7. The HUD keeps critical state visible in the main play area.
8. The existing `TraceCoordinateMapper` / `TraceSceneRenderer` /
   `CellRenderer` path is reused.
9. Live 4D inherits this grammar rather than inventing a separate language.
10. Stage 23 started only after Live 3D visual acceptance passed in Stage 22f
    after Stage 22g corrections.

## 2. Problem Statement

Stage 22b/22c addressed the earlier convexity problem: Live 3D cells should no
longer read primarily as internal walls, concave geometry, translucent panels,
or hollow cages.

The remaining problem is different. Solid cells are visible, but the active
piece can still appear to point in the wrong direction because its orientation,
depth direction, and rotation plane are perceptually ambiguous. The player
lacks enough stable axis, depth, and rotation cues to resolve the state
immediately. A mathematically correct C++ snapshot is necessary but not
sufficient when the display permits multiple plausible readings.

## 3. Why Python Did Not Expose The Same Problem

The Python/Pygame renderer is a useful visual reference because it is more
diagrammatic than generic physical 3D rendering. It uses a controlled centered
projection convention, an orthographic default view, fitted projected bounds,
depth-sorted faces, explicit per-face brightness factors, strong active-cell
outlines, secondary locked-cell treatment, projected lattice lines, and
optional active-piece boundary guides.

Python does not depend primarily on a physical camera, lights, normals, and
material interpretation to explain board state. Godot must recover that
symbolic clarity intentionally. Rendering realistic cubes is not the target.

## 4. Visual Goals

Live 3D is acceptable only when:

1. The active piece is readable within approximately `0.5` seconds.
2. The direction in which the active piece extends is not ambiguous.
3. `X`, `Y`, and `Z` are visually distinguishable.
4. The `Y` drop axis is unmistakable.
5. The current or most recent rotation plane is visible.
6. Locked cells remain readable but visually secondary.
7. Score, clear count, running/paused/game-over state, and command status are
   visible without opening diagnostics.
8. The board grid supports orientation without dominating the cells.

## 5. Camera/View Convention

The canonical Live 3D view is:

```text
LIVE_3D_EXTERNAL_DIAGRAM_VIEW
```

Required properties:

1. Use orthographic projection by default.
2. Use an exterior three-quarter angle.
3. View the board from slightly above, not below.
4. Keep roll at `0`.
5. Target the board center.
6. `Fit View` preserves the canonical yaw/pitch and changes only framing,
   bounds, and zoom.
7. Do not use an inside, below-board, or behind-board default view.
8. Manual orbit/pan/zoom may exist, but reset and `Fit View` return to
   `LIVE_3D_EXTERNAL_DIAGRAM_VIEW`.
9. The HUD or inspector exposes the active camera preset, projection,
   above/below status, yaw, pitch, roll, and fit/manual state.

Reject a candidate view when:

1. `X` and `Z` collapse into visually similar screen directions.
2. `Y` drop movement is confused with `Z` movement.
3. The active-piece silhouette collapses.
4. The player must orbit to understand the current piece.

## 6. Projection Basis / Axis Separation

A visually attractive camera is insufficient if it does not make game actions
legible.

The canonical screen-space basis must satisfy:

1. `X` has a strong left/right component.
2. `Y` drop has a clearly distinct downward component.
3. `Z` has a clearly distinct diagonal depth component.
4. No pair of gameplay axes should require trial input to tell them apart.

## 7. Cell Visual Grammar

The implementation vocabulary is:

```text
live_3d_active
live_3d_locked
live_3d_outline
live_3d_active_outline
live_3d_locked_outline
live_3d_origin_marker
live_3d_rotation_feedback
board_grid
board_bounds
```

Active cells:

1. Are opaque.
2. Are saturated or bright.
3. Have a crisp external outline.
4. Are visually stronger than locked cells.
5. Read as one active piece while preserving enough separation to parse its
   occupied cells.

Locked cells:

1. Are opaque or near-opaque.
2. Are darker and secondary to active cells.
3. Remain readable as cells.
4. Must not merge into a confusing wall.

Board grid and bounds:

1. Are thin and stable.
2. Support orientation.
3. Remain weaker than the active piece.

## 8. Exterior-Face Rule

Cells must read as solid external blocks:

1. Not glass.
2. Not hollow cages.
3. Not internal wall panels.
4. Not flat billboards.

Recommended encoding:

1. Use subtle per-face brightness differences.
2. Distinguish top, near, and side faces.
3. Use an external edge outline.
4. Choose roughness/specular settings that strengthen silhouette.
5. Use ambient fill so visible faces do not collapse to black.
6. Do not use high transparency as the default.

## 9. Outline/Silhouette Rules

1. The active piece receives the strongest outline.
2. Locked cells receive lighter, quieter outlines.
3. Outlines define external silhouettes.
4. Outlines must not make cells read as hollow.
5. Adjacent active cells remain separable enough to parse piece shape.

## 10. Active-Piece Orientation Cues

Stage 22e must implement at least one explicit active-piece orientation cue.
Valid options include:

1. Origin/root cube marker.
2. Small colored corner tick.
3. Brighter origin face.
4. Selected-cell marker.
5. Last-command pulse.
6. Active-piece outline pulse.

The minimum result is stronger than a generic outline pulse alone: the player
must know where the piece origin or pivot reference is and which way the piece
extends.

Stage 22g selects a solid origin/root cube marker plus stronger active-cell
outline priority as the minimum implemented cue for the current Live 3D
prototype.

## 11. Axis Markers And Board Landmarks

Live 3D requires:

1. `X` label.
2. `Y / DROP` label.
3. `Z` label.
4. Near/far corner cue.
5. Drop-direction marker.

These markers must be subtle but visible, stable across mode switches, and
useful for distinguishing front/back and depth. They are board-interface
landmarks, not decorative scene dressing.

## 12. Rotation-Plane Feedback

Live 3D uses direct plane-pair controls:

```text
R / T     XY- / XY+
F / G     XZ- / XZ+
V / B     YZ- / YZ+
```

The HUD must show:

```text
Last rotation: XY+ | XY- | XZ+ | XZ- | YZ+ | YZ-
```

Optional board feedback:

1. Brief rotation-plane flash.
2. Axis-pair highlight.
3. Active-piece outline pulse.

Prefer:

```text
snap to returned C++ state + clear plane feedback
```

over:

```text
misleading Godot-side tweened rotation
```

Godot may animate presentation later only if the animation is derived from and
cannot contradict the returned native snapshot.

## 13. HUD Layout Rules

Critical state belongs in the main live play surface:

1. `LIVE 3D · C++ CORE`.
2. Score.
3. Clears/lines.
4. State-hash prefix.
5. Current piece.
6. Next piece when available.
7. Last command and status.
8. Last rotation plane.
9. Running, paused, or game-over state.
10. Control hints.
11. Compact readable bundle health.
12. Live 3D camera preset/view state.

Score and game-over must never be buried only in diagnostics or side panels.
Long bundle digests belong in detail/diagnostic text; the top status must keep
the primary bundle health readable.

## 14. Live 3D Control Hint Rules

The default visible hints are:

```text
Move: A/D or <-/-> X, W/S or Up/Down Z
Drop: Shift Soft, Space Hard
Rotate: R/T XY, F/G XZ, V/B YZ
P Pause · Backspace Reset · Tab Mode · Q/Esc Quit
```

Split this into two lines when needed. The visible text must not become
unreadable through forced single-line compression.

## 15. Future Live 4D Visual Constraints

Live 4D is allowed only after Live 3D passes Stage 22f manual acceptance. That
gate passed after Stage 22g corrections, and Stage 23 implements the first
narrow Live Plain 4D prototype. Stage 23 manual GUI acceptance found W labels
too small, Space leaking to focused UI activation instead of hard drop, and
overly bright active Live 4D cells. Stage 23b corrects those visual/input
defects. Stage 23c further corrects view/readability by using explicit W-slice
headers, opening/resetting Live 4D in a fitted W-slice view, and adding safe
camera adjustment controls. Stage 23d corrects the zoom part of those controls
so Live 4D orthographic zoom changes camera size and remains available after UI
focus changes. Stage 23 Live Plain 4D Godot Prototype passed manual GUI
acceptance after Stage 23b/23c/23d corrections. Live 4D is accepted as a
narrow plain bounded prototype. Stage 24 Live ND polish and hardening is now
unblocked. Topology and endgame remain deferred.

Constraints for Stage 23 and later Live 4D polish:

1. Reuse the same cell grammar.
2. Show `W` as side-by-side slices unless a later design proves a clearer
   alternative.
3. Keep `W` labels stable.
4. Make `W-` / `W+` movement visible.
5. Extend the rotation-plane HUD to `XY`, `XZ`, `XW`, `YZ`, `YW`, and `ZW`.
6. Keep selected/current `W` context visible.
7. Do not invent a separate visual language for Live 4D.
8. Keep W labels large enough to read at default/Fit View with high-contrast
   backing.
9. Consume Space as live hard-drop before shell UI controls can treat it as
   accept/back.
10. Keep active Live 4D cells moderately brighter than locked cells with a
    stronger outline and origin marker, but avoid high-emission glare.
11. Use a canonical fitted Live 4D default that frames all W slices and slice
    headers.
12. Keep Fit View as the canonical recovery action for the full W-slice layout.
13. Allow limited Live 4D camera adjustment controls that do not overlap
    movement, rotation, drop, pause, reset, mode switch, or quit controls.
14. Live 4D orthographic zoom must adjust effective orthographic size; camera
    distance alone is not visible zoom for this view.

## 16. Implementation Stages After Stage 22d

```text
Stage 22e - Implement Live 3D Gameboard Visual Language
Stage 22f - Manual Live 3D Visual Acceptance
Stage 22g - Correct failed Live 3D visual acceptance observations when needed
Stage 22f - Rerun Manual Live 3D Visual Acceptance
Stage 23  - Live Plain 4D Godot Prototype
Stage 23b - Live 4D Acceptance Corrections
Stage 23c - Live 4D View And W-Slice Readability Corrections
Stage 23d - Live 4D Zoom-Control Correction
Stage 24  - Live ND Polish And Hardening
```

Stage 23 did not start before Stage 22f passed. Future Live 4D polish must
continue to inherit this visual grammar rather than inventing a separate board
language. Stage 23 Live Plain 4D Godot Prototype passed manual GUI acceptance
after Stage 23b/23c/23d corrections. Live 4D is accepted as a narrow plain
bounded prototype. Stage 24 Live ND polish and hardening is now unblocked.
Topology and endgame remain deferred.

Design rule after Stage 23c:

1. Live 3D may rely on a fixed canonical exterior view.
2. Live 4D requires a canonical fitted default plus safe camera adjustment
   controls.

## 17. Manual Acceptance Checklist

Live 3D acceptance:

- [ ] Cells read as solid external cubes.
- [ ] Active cells are visually stronger than locked cells.
- [ ] Active-piece shape is decipherable quickly.
- [ ] Active-piece origin/orientation cue is visible.
- [ ] Piece direction is not ambiguous.
- [ ] `X`, `Y`, and `Z` axes are distinguishable.
- [ ] Drop axis is clear.
- [ ] `XZ` and `YZ` rotations are understandable.
- [ ] Rotation-plane feedback is visible.
- [ ] Score, status, and game-over are visible.
- [ ] Bundle health and camera preset/view state are readable.
- [ ] `Fit View` returns to the canonical exterior view.
- [ ] Live 2D is unaffected.
- [ ] Replay is unaffected.

Future Live 4D acceptance:

- [ ] `W` slices are identifiable.
- [ ] `W` labels are immediately noticeable and remain readable after Fit View
      and resize.
- [ ] Live 4D opens already fitted to the full W-slice layout.
- [ ] `Fit View` restores the full W-slice layout after camera adjustment.
- [ ] Camera controls allow inspection and do not interfere with gameplay
      controls.
- [ ] Current/focused slice is visible.
- [ ] `W` movement is readable.
- [ ] Space hard-drops and does not activate menu/back/reset/UI controls.
- [ ] Six rotation planes are represented clearly.
- [ ] Active piece is decipherable across slices.
- [ ] Active cells are distinct from locked cells without becoming a glowing
      blob.
- [ ] Q/E are W-/W+ and Esc remains quit/back.

## 18. Risks And Mitigations

Risk: over-realistic 3D makes puzzle state ambiguous.
Mitigation: diagrammatic rendering, face tint, outlines, and axis labels.

Risk: a camera angle looks good but hides game axes.
Mitigation: enforce the projection-basis acceptance rule.

Risk: the active piece becomes a uniform cube blob.
Mitigation: add an explicit active-piece orientation cue.

Risk: rotation animation lies.
Mitigation: snap to C++ state and show clear plane feedback.

Risk: 4D inherits unresolved 3D ambiguity.
Mitigation: Stage 23 was blocked until Stage 22f acceptance passed after Stage
22g corrections; future Live 4D changes must keep the same grammar.
