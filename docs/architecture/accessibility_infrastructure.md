# Accessibility Infrastructure

Status: Stage 52 architecture contract and focused audit.

## 1. Purpose

Stage 52 completes the Godot product shell's accessibility layer on top of the
accepted Stage 51 display infrastructure. It makes keyboard operation, focus,
non-colour state, contrast, motion, and optional help coherent presentation
concerns without changing gameplay, topology, replay, setup, RNG, or native
state.

## 2. Stage 51 baseline

Stage 51 remains the display-only authority in
`display_infrastructure.md`. Its registry, `SettingsStore`, generated
`SettingsPanel`, historically named `ReplayHud` presentation owner, and
renderer/camera consumers are reused. Stage 52 does not add another settings
file, store, writer, or propagation service.

The focused audit found:

- central focus styles, initial focus, explicit linear Settings/setup focus
  order, live-input isolation, and active/locked cell outlines already exist;
- the main shell, mode/setup screens, Settings, live pause/end-state actions,
  and replay routes already have keyboard entry points, but focus policy is
  distributed and requires invariant-level regression coverage;
- the existing `controls_help.show_keyboard_hints` preference is semantically
  equivalent to the requested optional-help preference and must be migrated,
  not duplicated;
- focused and hovered controls currently share border treatment, and focus
  borders are only one pixel; focus needs a static geometric distinction;
- selected W layers already have a heavier frame and a `wN ◀` marker, giving
  two non-colour cues; this contract makes that behavior mandatory;
- current and locked cells already use distinct geometry/outline treatments,
  while ghost/projection roles require explicit regression protection;
- validation, pause, game-over, and modal states already contain text; tests
  must prevent regression to colour-only signaling;
- camera interpolation, live 3D rotation pulse, replay/event-marker pulse, and
  replay-frame interpolation are the relevant motion surfaces; replay
  interpolation is informative playback and its event timing is not a
  gameplay-motion control;
- no general sliding-menu/tween framework exists, so Stage 52 must not invent
  one;
- the removed combined Stage 51 prototype proved that semantic high-contrast
  composition, camera snapping, pulse suppression, and renderer edge weights
  fit the existing owner. Stage 52 may reuse those narrow mechanisms under the
  schema-3 and invariant/preference rules in this contract.

## 3. Accessibility authority

Godot owns accessibility preferences, focus and keyboard presentation, shell
navigation, hints, contrast roles, static semantic cues, renderer emphasis, and
presentation-only motion. Python remains the semantic oracle. Native C++ keeps
accepted bounded gameplay authority. Accessibility code may consume snapshots
but cannot determine legality or mutate gameplay.

## 4. Accessibility invariants

Visible static focus, keyboard reachability, deliberate navigation order,
modal containment, sensible focus restoration, input isolation, readable
essential labels, reachable primary actions, and non-colour essential state are
always enabled. They are not settings and cannot be reset or hidden.

Essential state includes focus, selected options, active W layer, active versus
locked or ghost cells, disabled controls where ambiguous, validation failures,
pause/game-over/modal state, and required setup or navigation actions.

## 5. Accessibility preferences

The bounded preferences are:

| ID | Values | Default |
| --- | --- | --- |
| `accessibility.high_contrast` | boolean | `false` |
| `accessibility.reduced_motion` | boolean | `false` |
| `accessibility.show_help_hints` | boolean | `true` |

There is no focus-visibility or non-colour-cue preference.

## 6. Canonical settings model

`config/shell_settings_registry.json` owns IDs, labels, descriptions, types,
defaults, and persistence declarations. `SettingsStore` owns validated runtime
values and snapshots. Persisted data contains no scene references, free-form
policy dictionaries, gameplay state, or native-session dependency.

## 7. Persistence and schema migration

`user://shell_settings.json` advances from schema 2 to schema 3 through the
existing guarded writer. Schema-2 values migrate field by field:

- every valid display, theme, camera, replay, and onboarding value survives;
- `controls_help.show_keyboard_hints` migrates to
  `accessibility.show_help_hints`;
- high contrast and reduced motion receive their defaults;
- the obsolete hint field remains a compatibility read only and is not emitted
  by schema 3.

Schema 1 remains readable through the existing history: Stage 48 values first
normalize through the same field-level store logic, then receive schema-3
defaults. Loading never rewrites a source file. Missing/malformed/unsupported
documents use safe in-memory defaults. Future-schema files remain untouched
until an explicit change or reset.

## 8. Runtime policy and propagation

The single flow is:

```text
shell_settings_registry.json
        -> SettingsStore
        -> SettingsPanel
        -> ReplayHud presentation owner
        -> Window / Theme / HUD / Renderer / Camera / Help / Overlays
```

`ReplayHud` remains named for historical reasons: it already coordinates shell
and live screens without depending on replay semantics. Renaming it would add
risk without removing an accessibility dependency.

Consumers receive derived contrast, motion, and hint policy. They do not read
the store or interpret persisted JSON directly.

## 9. Focus visibility policy

Every interactive control uses a static focus outline thicker than its normal
and hover borders, with sufficient margin to avoid clipping at all four UI
scales. Focus remains visible in all base themes and High Contrast. Hover may
share fill emphasis but cannot erase the geometric focus ring.

## 10. Keyboard-navigation policy

Main menu, mode selection, board setup, game setup, Settings, pause, end state,
confirmations, replay routes, and interactive help use existing Godot actions
and Enter/Space activation. Explicit neighbours are assigned where automatic
container order is unreliable. Hidden or disabled controls are excluded.

## 11. Focus containment and restoration

Every screen chooses a deliberate initial control. Modal and confirmation
owners disable background focus/input, cycle only through visible modal
actions, and remember the originating control. Closing a child or modal
restores that origin when valid, otherwise the nearest safe action. Gameplay
commands remain blocked while shell UI owns input.

## 12. Non-colour semantic cue policy

Focus uses border geometry; selected options use their native check/selection
marker plus text; active W layers use a heavier frame plus explicit arrow/active
text; active cells use stronger outlines than locked cells; ghost/projection
uses outline/transparency; errors use text; pause/game-over/modals use explicit
labels and structure. Colour reinforces these cues but never owns them alone.

## 13. High-contrast policy

High Contrast is a semantic override composed with Diagnostic, Plain, or Vector
Arcade. It strengthens foreground/background separation, focus and selection
outlines, disabled/active differentiation, board hierarchy, cell outlines,
active-layer frames, labels, warnings, errors, HUD, and helper panels. It does
not change base-theme identity, layout scale, HUD density, board geometry,
camera state, gameplay, setup, replay, or hashes.

## 14. Reduced-motion policy

Motion is classified as:

- essential: native piece-state changes; unchanged;
- informative: replay-frame interpolation; timing/order unchanged;
- decorative: camera smoothing, outline/event pulse, and shell emphasis.

Reduced Motion snaps or sharply shortens presentation camera interpolation and
replaces decorative pulse/flash with static emphasis. It never scales gravity,
input repeat, lock/drop timing, replay event timing, or native simulation.
Sensitivity still controls response magnitude; inversion still changes pitch
only.

## 15. Help and hint policy

`accessibility.show_help_hints` controls optional keyboard legends, repeated
control prompts, and contextual helper panels live. It cannot hide button
labels, mode/setup identity, active-layer labels, validation/error text,
mandatory warnings, primary navigation, or focus. Onboarding completion is
preserved and is not replayed or reset.

## 16. Menu and overlay integration

Menus, setup screens, Settings, pause, end state, replay routes, help, and
confirmations consume the shared focus, contrast, motion, and hint policy.
Input ownership and Back/Escape contracts remain unchanged.

## 17. HUD integration

Compact, Standard, and Detailed HUD retain essential status and explicit active
layer identity. High Contrast applies to semantic roles; Reduced Motion removes
decorative emphasis; optional hint panels respect the hint preference. No
accessibility diagnostics become player HUD fields.

## 18. Renderer integration

The 2D/3D/4D renderer accepts derived contrast and motion values. It strengthens
existing active/locked/ghost and board/layer geometry without changing mapper
coordinates, board dimensions, native snapshots, camera target state, replay
identity, setup identity, or hashes. Wide-W retains all eight layers and at
least two active-layer cues.

## 19. Camera integration

Camera sensitivity and vertical inversion remain Stage 51 preferences. Reduced
Motion controls interpolation only: target yaw, pitch, roll, focus, and fit
distance are identical, while convergence snaps or is substantially shorter.
Direct camera control remains available.

## 20. Viewport and UI-scale requirements

The supported minimum remains `634 x 660`. Small `0.90`, Standard `1.00`,
Large `1.15`, and Extra Large `1.30` must keep focus rings, scrolling,
accessibility controls, Reset Accessibility, Reset Display, Back, setup/live
actions, HUD essentials, and Wide-W navigation visible or reachable. Contrast
overrides cannot materially change layout dimensions.

## 21. Error and fallback behavior

Invalid accessibility fields fall back independently: High Contrast and Reduced
Motion to Off, hints to On. Valid display/accessibility siblings survive.
Missing contrast resources preserve the base theme and other settings. Missing
focus targets select a safe visible fallback. Consumer failures preserve
canonical settings and gameplay, produce concise diagnostics, and never create
recursive saves or per-frame logs.

## 22. Explicit exclusions

Excluded: rebinding and profiles; controllers and touch; screen readers,
speech, narration, audio cues, captions, and localisation; font selection;
colour-vision simulation or arbitrary colour/contrast controls; topology and
Topology Lab; gameplay, board/setup, pieces, RNG, scoring, progression, replay
schema/identity, state hashes, bots, packaging, and simulator/editor redesign.

## 23. Test strategy

Focused tests protect schema-3 defaults, schema-1/2 migration, hint migration,
field-level fallback, future files, guarded saves, isolated resets, policy
snapshots/signals, theme composition, static focus geometry, keyboard traversal,
modal/input isolation, semantic markers, motion isolation, hints, HUD/renderer/
camera consumers, `634 x 660`, all UI scales, all HUD/detail modes, 2D/3D/4D,
and W=8. Existing Stage 47-51, parity, native, and Python gates remain green.

## 24. Manual acceptance strategy

On macOS, exercise the real project with keyboard-only launch → setup → play →
pause → Settings → accessibility changes → return → restart/change setup/menu.
Inspect every theme with High Contrast, motion Off/On, hints Off/On, all scales,
minimum/constrained and ordinary viewports, 2D/3D/4D, and Wide-W. Do not claim
Linux, controller, touch, screen-reader, or multi-monitor acceptance.

## 25. Future controls and topology stages

Stage 53 may consume focus, contrast, motion, hints, and semantic-selection
roles but cannot be anticipated with topology UI here. Stage 54 may replace
literal control labels through its binding authority; Stage 52 continues using
existing action abstractions and does not introduce a binding system.
