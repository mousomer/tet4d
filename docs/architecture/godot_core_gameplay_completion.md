# Stage 46 Godot Core Gameplay Completion

Status: implementation in progress
Date: 2026-07-12

## Authority and scope

Python remains the semantic reference for gameplay, topology, replay, and
parity behavior. Godot owns live input routing, camera, rendering, HUD, and
presentation. The existing native plain-session bridge supplies live state;
this stage does not expand native authority or add gameplay decisions to
GDScript.

Stage 46 covers only Live Plain 2D, Live Plain 3D, and Live Plain 4D. Godot
topology, settings persistence, broad onboarding, and packaging remain outside
this stage.

## Gameplay audit

| Mode | Existing complete path | Stage 46 gap addressed |
| --- | --- | --- |
| Live Plain 2D | Spawn, X movement, XY rotation, soft/hard drop, lock/spawn, gravity, pause, reset, game over, and fit view | Make score, clears, current/next piece, command rejection, and successful lock visible in primary live HUD chrome |
| Live Plain 3D | Spawn, X/Z movement, XY/XZ/YZ rotation, soft/hard drop, lock/spawn, gravity, pause, reset, game over, exterior camera, orbit/zoom, and fit view | Give the same primary gameplay-state feedback without changing the accepted exterior-board renderer or camera semantics |
| Live Plain 4D | Spawn, X/Z/W movement, six rotation planes, soft/hard drop, lock/spawn, gravity, pause, reset, game over, W-slice rendering, orbit/roll/zoom, and fit view | Surface primary gameplay state and decisive lock feedback while preserving W-slice readability and camera-only controls |

The accepted Stage 41 deterministic sequences already protect
spawn -> move -> rotate -> soft drop -> hard drop -> lock for all three modes.
Stage 46 extends the shell test so those real live sequences also protect the
player-facing score, queue, and lock feedback.

## Implementation boundary

The live HUD reads only native snapshot fields: `score`, `lines`,
`current_piece`, `next_piece`, `last_command`, `last_command_status`,
`paused`, `game_over`, and `game_over_reason`. It formats those values for the
player but does not infer legality, calculate score, detect clears, decide a
lock, or mutate session state.

Primary live chrome now prioritizes:

- score and total clears;
- current and next piece;
- accepted hard-drop lock confirmation;
- blocked command, pause, and game-over state.

Existing active/locked cell materials, dimensional camera presets, fit-view
behavior, input repeat timings, native snapshots, and parity fixtures remain
unchanged.

## Explicit deferrals

- Stage 47: broad UX, onboarding, tutorials, and menu redesign.
- Stage 48: settings persistence, keybinding configuration, and save behavior.
- Stage 49: topology-aware Godot gameplay and topology migration.
- Any Python gameplay-rule change, replay/parity schema change, native
  authority transfer, renderer rewrite, or migration-bundle regeneration.

