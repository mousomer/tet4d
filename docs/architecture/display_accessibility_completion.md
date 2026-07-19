# Stage 51 Display and Accessibility Completion

Status: implementation authority for the bounded Stage 51 Godot presentation
batch.

## Existing baseline and remaining gaps

Stage 48 already persists replay speed/loop, W-label visibility, projection
strength, theme, keyboard hints, and guided-onboarding visibility through the
registry-backed `user://shell_settings.json`; layout bounds remain session-only.
The generated Settings screen, scroll-safe shell screens, explicit focus order,
Plain/default themes, onboarding dismissal, active/locked cell outlines, active
4D layer frame weight, and viewport minimums are existing accessibility
foundations.

The remaining product behavior is hard-coded: window mode and size, one UI
scale, one live HUD density, one board-detail level, standard palette contrast,
camera orbit sensitivity/direction, camera interpolation, and the
automatic-only contextual-hint policy. Stage 51 closes only those presentation
gaps.

## Canonical bounded settings

The existing registry/store remains the single owner. Stage 51 adds:

| Setting | Values | Consumer |
| --- | --- | --- |
| `display.window_mode` | `windowed`, `fullscreen` | shell window application |
| `display.windowed_size` | validated `WIDTHxHEIGHT` | shell window application |
| `display.ui_scale` | `small`, `standard`, `large`, `extra_large` | root shell scaling/layout |
| `display.hud_density` | `compact`, `standard`, `detailed` | live HUD/inspector |
| `display.board_detail` | `minimal`, `standard`, `full` | grid/board renderer |
| `accessibility.contrast_mode` | `standard`, `high` | shell style and board renderer |
| `accessibility.animation_mode` | `reduced`, `standard` | shell/camera presentation |
| `camera.sensitivity` | `low`, `standard`, `high` | 3D/4D camera rig |
| `camera.invert_y` | boolean | camera pitch input only |
| `controls_help.contextual_help` | `automatic`, `always`, `hidden` | contextual help panels |

Windowed size is remembered automatically and is not shown as an arbitrary
resolution selector. Stable presets are deliberately used for every other
multi-value preference.

The shell-settings file advances from schema 1 to schema 2. Schema-1 files are
migrated in memory by retaining every valid Stage 48 persistent value and
defaulting new fields. Schema-2 loading validates each field independently, so
one invalid or unknown value cannot discard valid siblings. Malformed JSON,
invalid roots, and future schema versions recover to safe defaults without
rewriting the source automatically. Reset writes the complete schema-2 default
set. `user://game_setup.json` and onboarding visibility remain independent.

## Application contract

The settings store feeds the generated panels; panel signals feed the existing
`ReplayHud` presentation owner, which applies shell/window/help/HUD settings
and forwards renderer/camera settings through `TraceReplayApp`. Consumers never
read the settings file directly.

- UI scaling applies to menus, setup, Settings, HUD, help, and focus visuals,
  while the supported physical viewport minimum remains enforced.
- HUD density changes only which already-available player-facing values are
  visible.
- Board detail maps boundary/grid/edge/helper visibility consistently where a
  renderer supports it. It never changes coordinates, occupancy, collision, or
  camera-fit bounds.
- High contrast strengthens focus, active/locked cell outlines, selected-layer
  frame weight/label treatment, and warning borders/text. Colour is
  reinforcement rather than the sole cue.
- Reduced motion snaps camera interpolation and suppresses non-essential visual
  pulsing while retaining destination, selection, lock, and error feedback. It
  cannot alter gravity, replay playback rate, input acceptance, lock/drop
  timing, score, or native state.
- Camera sensitivity scales orbit/roll response only; inversion changes only
  the vertical pitch direction. 2D safely ignores camera-only preferences.
- Contextual help is automatic, always visible, or hidden. Essential status,
  validation, error text, Controls access, and the separate onboarding
  preference remain available.

## Acceptance criteria

Completion requires registry/store migration and malformed-input coverage;
runtime/persistence coverage for every preset; keyboard-reachable generated
controls with visible focus; safe minimum/desktop/wide layouts at maximum UI
scale in default and Plain themes; distinct active, locked, selected-layer,
focus, and warning treatments; unchanged native snapshots/timing under display
and reduced-motion choices; and accepted 2D, 3D, and Wide-W 4D interaction
including all eight W layers, Q/E, fourth-axis rotation, Shift+wheel, Fit View,
hard drop, restart, New Random, and Change Setup. Full repository verification
and manual GUI acceptance are required.

## Explicit deferrals and boundary

Deferred: key rebinding, keyboard profiles, controller support, dynamic
binding-derived labels, arbitrary resolutions, exclusive fullscreen, audio,
developer rendering toggles, topology/UI, replay redesign, bots, kicks,
challenge/progression, packaging, and platform integration.

Every Stage 51 behavior is Godot-owned presentation. Python gameplay/reference
rules, native gameplay authority and state, RNG, piece sets, board setup,
topology, replay schemas/identity, scoring, movement, rotation, collision,
locking, and deterministic restart remain unchanged.
