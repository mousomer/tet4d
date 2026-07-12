# Stage 47 Godot Guided Onboarding and Navigation

Status: Stage 47b corrective implementation; manual acceptance pending
Date: 2026-07-12

## Scope and prior-stage reconciliation

Stage 42 already owns static first-run explanation, mode discovery, controls,
and limitations copy. Stage 46 completed the gameplay-state HUD. Stage 47 adds
the missing contextual layer during live play and normalizes shell navigation;
it does not repeat the Stage 42 menu-copy pass.

Godot owns this guidance model, panel, player-facing formatting, and navigation
routing. Guidance consumes only existing native snapshot `last_command` and
`last_command_status` values. It does not infer legality, dispatch commands, or
mutate gameplay state. Python remains semantic authority and the accepted
native plain sessions remain the live-state source.

## Onboarding contract

- Live 2D progresses through movement, rotation, drop, and system controls.
- Live 3D distinguishes X/Z board movement, falling, plane rotation, and camera.
- Live 4D explains W slices and Q/E before the broader rotation space and camera recovery.
- Only an `accepted` result for a command listed by the current step advances it.
- Guidance is compact, non-modal, dismissible, and session-local.
- Gameplay restart does not reset or persist guidance. Stage 48 owns persistence.

## Navigation contract

| Action | Meaning |
| --- | --- |
| `Tab` | Cycle Replay, Play 2D, Play 3D, and Play 4D |
| `Esc` | Return from a live/replay child surface to Main Menu |
| Reset / Restart | Restart only the current session or replay |
| Quit | Exit from the explicit Main Menu action |

Live 4D keeps Q/E exclusively for W movement. The existing router is retained.

## Deferred work

- Stage 48: settings persistence and keybinding configuration.
- Stage 49: topology migration.
- Gameplay, scoring, legality, replay-schema, native-snapshot, renderer, Python,
  and authority-transfer changes remain out of scope.

## Stage 47b manual-acceptance correction

The first Stage 47 implementation failed manual acceptance because menu/help
content overflowed, keyboard focus was not deterministic, and onboarding was
placed below the full live controls map. Stage 47b therefore requires:

- viewport-safe vertical scrolling for Main Menu, Controls, and About;
- explicit Play 2D -> Play 3D -> Play 4D -> Replay -> How to Play -> About ->
  Settings -> Quit focus order, with initial focus on Play 2D;
- keyboard-scroll focus for help content and a visible Main Menu path;
- immediate onboarding rendering on live entry, first in inspector order;
- a prominent onboarding card with an explicit session-only `Hide Guide` action;
- roomier canonical live Fit View margins so initial entry does not feel over-zoomed;
- distinct `Main Menu` and `Quit Application` controls, with all quit surfaces
  routed through the application quit request;
- automated minimum-viewport, focus, scrolling, and initial-visibility checks.

Stage 47 must not be described as complete until this batch passes manual GUI
acceptance.
