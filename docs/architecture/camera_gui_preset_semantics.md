# Camera and GUI Preset Semantics

Role: architecture
Status: design accepted; Stage 54E-4b implements this contract
Scope: Godot product-shell view/layout/GUI preset semantics across Live 2D/3D/4D
Canonical owner: this file
Consumes: docs/architecture/4d_presentation_interaction_architecture.md
Stage: 54E-4a design and audit
Last updated: 2026-08-17

## 1. Purpose and boundary

Stage 54E-2 separated the Live-4D presentation pipeline into distinct spaces.
The preset concept predates that separation. This document audits what every
preset-like operation actually does today, assigns each mutable presentation
property exactly one semantic owner, and defines the durable preset contract
that Stage 54E-4b implements.

This document owns preset taxonomy, what each family may mutate, preset
identity, reset and lifecycle behaviour for preset-owned state, persistence
ownership, and the compatibility mapping for existing IDs.

It does not own the presentation-space separation itself, which belongs to
`4d_presentation_interaction_architecture.md` and is consumed here unchanged.

Stage 54E-4a performed no runtime change.

The two product decisions this design raised were accepted on 2026-08-17 and
are recorded in section 20. Every statement in this document is therefore
decided, either by repository evidence, by already-accepted authority, or by
that acceptance. Stage 54E-4b implements it without reopening the design.

## 2. Consumed architecture

The accepted pipeline is `C -> B -> G_D -> L -> anchor/layout -> V/P`, with
HUD/GUI composition separate from all of it. Section 14 of
`4d_presentation_interaction_architecture.md` already fixes the lifecycle
matrix, and its section 13 explicitly defers preset taxonomy, persistence,
reset, labels, and layout-preset scope to Stage 54E-4. The Stage 54E-2
decisions listed in that document are settled and are not reopened here.

Two consumed constraints do most of the work below:

- `SliceLocalOrientation.set_normal_gameplay_angles()` wraps yaw and clamps
  pitch to `[-40deg, +60deg]`. Anything a preset writes to `L` is admitted by
  construction.
- The Live-4D outer mount is fixed at yaw `205deg`, pitch `20deg` with a fixed
  horizontal presentation reflection. In Live 4D the outer rig does not rotate.

## 3. Preset inventory

### 3.1 In scope — Godot product shell

| ID / label | Entry surface | Implementation | Current mutations | Lifecycle | Persistence | Modes | Tests | Legacy coupling | Intended owner | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iso` "Iso" | `CameraPresetSelector` in live inspector VIEW | `camera_preset.gd` | yaw `+0.5585`, pitch `+0.4538`, zoom `1.0`, pan `ZERO` | reset on Reset View / mode change | none | 2D, 3D, 4D | `test_live_board_visual_grammar`, `test_camera_rig`, `test_live_2d_shell` | yes — see F1, F2 | `SLICE_LOCAL_ORIENTATION` (4D) / `OUTER_FRAMING` (3D) | REDEFINE_COMPATIBLY |
| `front` "Front" | same | same | yaw `0`, pitch `0`, zoom `1.0`, pan `ZERO` | same | none | 2D, 3D, 4D | same | yes | same | REDEFINE_COMPATIBLY |
| `side` "Side" | same | same | yaw `PI/2`, pitch `0`, zoom `1.0`, pan `ZERO` | same | none | 2D, 3D, 4D | same | yes | same | REDEFINE_COMPATIBLY |
| `back` "Back" | same | same | yaw `PI`, pitch `0`, zoom `1.0`, pan `ZERO` | same | none | 2D, 3D, 4D | same | yes | same | REDEFINE_COMPATIBLY |
| `top` "Top" | same | same | yaw `0`, pitch `+1.0472`, zoom `1.0`, pan `ZERO` | same | none | 2D, 3D, 4D | same | yes | same | REDEFINE_COMPATIBLY |
| `opposite_iso` "Opposite Iso" | same | same | yaw `-2.5831`, pitch `+0.4538`, zoom `1.0`, pan `ZERO` | same | none | 2D, 3D, 4D | same | yes | same | REDEFINE_COMPATIBLY |
| `custom` "Custom" | derived, not selectable | `_mark_custom_view()` | label only | set by any manual orbit/nudge/roll/pan/zoom | none | all | `test_camera_rig` | yes — see F3 | derived identity | REDEFINE_COMPATIBLY |
| Fit View | `fit_view_requested`, key | `_fit_view()` | focus, base distance, orthographic size, projection to orthographic, reflection, gizmo; sets label to `iso` | on demand and after every reset | none | all | `test_live_2d_shell` | yes — see F3 | `OUTER_FRAMING` | RETAIN |
| Reset View | key `0`, `Reset View` button | `_reset_live_4d_view()` | `B` to identity, `L` to `(0,0)`, `clear_presentation_state()`, then Fit | on demand | none | 4D (2D/3D reset via mode reset) | `test_live_2d_shell` | no | multi-owner by accepted contract | RETAIN |
| Adaptive layer layout | none — automatic | `adaptive_layer_layout.gd` | anchors, columns, rows from layer count and viewport aspect | recomputed on shape change | none | 4D | `test_adaptive_4d_layer_layout` | no | `SLICE_LAYOUT` | RETAIN (not a preset) |
| `theme.name` (`plain`/`tron`) | Settings | `shell_settings_registry.json` | palette/style roles | persistent | persistent | all | `test_shell_theme_palettes` | no | `GUI_LAYOUT` | RETAIN as setting |
| `display.hud_density` (`compact`/`standard`/`detailed`) | Settings | same | inspector panel visibility incl. camera panel | persistent | persistent | all | `test_replay_viewer_layout` | no | `GUI_VISIBILITY` | RETAIN as setting |
| `display.board_detail` (`minimal`/`standard`/`full`) | Settings | same | renderer detail | persistent | persistent | all | `test_shell_settings_registry` | no | `GUI_VISIBILITY` | RETAIN as setting |
| `display.ui_scale` | Settings | same | UI scale factor | persistent | persistent | all | `test_shell_display_settings` | no | `ACCESSIBILITY_PRESENTATION` | RETAIN as setting |
| `display.projection_strength` | Settings | `renderer.set_projection_strength()` | 4D slice projection strength, not camera projection | persistent | persistent | 4D | `test_shell_settings_registry` | no | `PROJECTION` | RETAIN as setting |
| `display.show_w_labels`, `ghost.enabled`, `settled_cells.opacity`, `interface.show_onboarding`, `diagnostics.show_layout_bounds` | Settings | same | HUD/renderer visibility | persistent except diagnostics | mixed | all | settings tests | no | `GUI_VISIBILITY` | RETAIN as setting |
| `camera.sensitivity`, `camera.invert_y` | Settings | `set_presentation_preferences()` | input gain and inversion | persistent | persistent | all | `test_shell_settings_store` | no | `OTHER` (input preference) | RETAIN as setting |
| `accessibility.high_contrast`, `.reduced_motion`, `.show_help_hints` | Settings | renderer/HUD | contrast, motion, hint visibility | persistent | persistent | all | `test_accessibility_runtime` | no | `ACCESSIBILITY_PRESENTATION` | RETAIN as setting |

### 3.2 Out of scope — different domain, recorded to prevent conflation

| Concept | Owner | Why out of scope |
| --- | --- | --- |
| Board presets (`compact`/`standard`/`large`/`wide_w`) in `game_setup_spec.gd` | Stage 54B / 54E-3 | Game definition, not presentation. Shares the word "preset" only. |
| `camera_preset: tutorial_3d_default` / `tutorial_4d_default` | Python pygame tutorial | Inherited Python UI. Sets `yaw_deg`, `pitch_deg`, `zoom_scale`, and `xw_deg`/`zw_deg` to zero, so in the Python model it does reset basis-like state. Godot is the product shell authority; this precedent does not bind the Godot contract. |
| `endgame_preset_id: default_orbit` | Python endgame animation | Post-game animation orbit, not a live view preset. |
| `topology_preset_id`, `speed_preset` | Python menu settings | Topology and gameplay speed, not presentation. |

## 4. Mutation-path audit

Player action to final state, as implemented today.

### 4.1 Live 4D

```text
CameraPresetSelector.item_selected
  -> ReplayHud.camera_preset_requested(id)
  -> TraceReplayApp._apply_live_4d_preset(id)
       -> _set_live_4d_local_orientation(preset.yaw, preset.pitch)
            -> SliceLocalOrientation.set_normal_gameplay_angles()   [L]
            -> _refresh_live_4d_presentation(reset_fit_reference=true)
            -> _refresh_control_frame_presentation()                [resolver refresh]
       -> CameraRig.apply_framing_preset(id)
            -> _target_focus = _fit_focus + pan                     [V/P]
            -> _zoom_multiplier = zoom; _camera.size = base * zoom  [V/P]
            -> _current_view_preset = id                            [label flag]
  -> ReplayHud.set_camera_preset(CameraRig.current_preset_id())
```

`B` is not written. Layout anchors are not written. Native gameplay is not
written. The Live-4D outer rig does not rotate.

### 4.2 Live 3D, Live 2D, replay

```text
CameraPresetSelector.item_selected
  -> ReplayHud.camera_preset_requested(id)
  -> CameraRig.apply_preset(id)
       -> _target_yaw, _target_pitch, _target_roll = 0              [outer V]
       -> _set_horizontal_reflection(false)                         [V]
       -> _zoom_multiplier, _target_distance                        [V]
       -> _current_view_preset = id                                 [label flag]
```

In 3D the outer yaw is also the control frame, through
`CameraRig.control_frame_yaw()`, which the accepted architecture retains for
the 3D resolver only.

### 4.3 Manual mutation and reset

`orbit`, `nudge_yaw`, `nudge_pitch`, `nudge_roll`, `roll`, `pan_focus`,
`pan_screen`, and `zoom` each call `_mark_custom_view()`, which sets the label
flag to `custom`. `_fit_view()` calls `fit_bounds(..., CameraPresetScript.ISO,
...)`, which sets the label flag to `iso`. `_reset_live_4d_view()` restores
`B` to identity, `L` to `(0,0)`, clears rig presentation state, then fits.

## 5. Legacy-coupling findings

**F1 — one preset ID, two semantic owners.** The same six IDs write `L` in
Live 4D and the outer rig in Live 3D and replay. This is not an accident to be
removed: in 4D the outer mount is fixed and orientation lives in `L`, while in
3D the outer rig legitimately is both the orientation and the control frame.
It is an under-documented mode-dependent binding. Stage 54E-4b must state the
binding, not erase it.

**F2 — the framing component carries no information.** All six presets declare
`zoom: 1.0` and `pan: Vector3.ZERO`. `apply_framing_preset()` therefore never
expresses a per-preset framing; it restores focus to `_fit_focus` and zoom to
the fitted baseline, discarding any manual pan or zoom. The behaviour is
useful, but it is currently an accident of uniform data rather than a declared
rule, and it makes each preset look like a combined `L + V/P` preset when it is
an orientation preset plus a fixed framing-reset step.

**F3 — the preset label can lie.** `_current_view_preset` is a mutable flag,
not a function of state. `_fit_view()` sets it to `iso` while `L` is `(0,0)`
and the outer mount is at its fixed angles, so after Fit View or Reset View the
selector reads "Iso" when nothing matches Iso. `(0,0)` is exactly the `front`
preset, so the truthful label is "Front".

**F4 — presets are exposed where they are meaningless.** The camera panel is
visible in every live mode whenever `display.hud_density` is not `compact`.
Live 2D is a flat board with a fixed orthographic front view and no `L`;
offering Top, Side, Back, and Opposite Iso there is noise.

**F5 — no preset state is persisted.** No view preset, `L` value, framing, or
projection state appears in `shell_settings_registry.json` or any store. The
selector resets every session. This is correct under the accepted contract and
should be preserved.

**F6 — no accessibility coupling exists.** `apply_preset()`,
`apply_framing_preset()`, and `clear_presentation_state()` touch only camera
state; `clear_presentation_state()` explicitly preserves sensitivity, invert-Y,
and interpolation preferences. No preset writes any `accessibility.*` value.
This is a clean result, recorded so a future change cannot silently regress it.

## 6. Semantic owner classification

| Property | Owner | Notes |
| --- | --- | --- |
| signed 4D basis `B` | `EXACT_BASIS` | gameplay-facing re-slicing; dedicated controls and indicator |
| `L.local_yaw`, `L.local_pitch` | `SLICE_LOCAL_ORIENTATION` | shared across slices; feeds resolver through `Q(local_yaw)` |
| slice anchors, columns, rows | `SLICE_LAYOUT` | algorithmic only |
| outer focus / pan | `OUTER_FRAMING` | |
| zoom multiplier, orthographic size | `OUTER_FRAMING` | |
| fit state, base distance | `OUTER_FRAMING` | |
| horizontal presentation reflection | `OUTER_FRAMING` | renderer-only, fixed for Live 4D |
| outer yaw / pitch | `OUTER_FRAMING` in 3D and replay; fixed mount in 4D | in 3D also the control frame |
| outer roll | `OUTER_FRAMING` | absent from normal gameplay; Explorer capability retained |
| camera projection type | `PROJECTION` | forced orthographic in every fitted product view |
| `display.projection_strength` | `PROJECTION` | 4D slice projection strength; independent persistent setting |
| `theme.name`, `display.ui_scale` | `GUI_LAYOUT` | |
| `display.hud_density`, `display.board_detail`, `display.show_w_labels`, `interface.show_onboarding`, `diagnostics.show_layout_bounds`, `ghost.enabled`, `settled_cells.opacity` | `GUI_VISIBILITY` | |
| `accessibility.*` | `ACCESSIBILITY_PRESENTATION` | |
| `camera.sensitivity`, `camera.invert_y` | `OTHER` | input preference, not view state |
| orientation gizmo visibility | `GUI_VISIBILITY` | driven by mode, not by preset |

No property required more than one primary owner.

## 7. Accepted taxonomy

There is exactly one preset family: **View presets**.

```text
View        named orientation of the board, plus a defined framing reset
Slice Layout   no preset family — one adaptive algorithm
Interface      no preset family — independent persistent settings
```

Rationale. A preset family is justified only when several player-useful named
states exist that cannot be expressed more clearly as independent settings.
Layout has exactly one algorithm and no player-facing alternatives, so a layout
preset family would be invented rather than discovered. GUI state is already a
set of independent persistent settings, and `display.hud_density` already
provides the one genuinely useful three-step composite; wrapping those in a
"GUI preset" would add a layer without adding a choice.

Player-facing terminology: **View**. The existing label "Camera" on the
inspector panel is retained for 3D and replay, where the camera really does
move, but the selector itself is a View selector in all modes. The word
"camera" must not be used in Live-4D help text for an operation that rotates
slice contents rather than the camera.

## 8. Policies

### 8.1 Exact basis `B`

**An ordinary View preset must never change `B`.** Re-slicing changes which
canonical axes are visible and which axis is the slice axis; it is a
gameplay-facing 4D comprehension operation with its own controls, its own
indicator, and its own help group. Burying it inside a view shortcut would
rebuild the coupling Stage 54E-2 removed.

Current behaviour already complies: `_apply_live_4d_preset()` does not touch
`_live_4d_basis`. This is retained and must become an explicit test.

If a future feature genuinely needs a named state that includes `B`, it is a
different semantic class — a re-slicing shortcut — and must be named and
surfaced as such, never as a View preset.

### 8.2 Slice-local orientation `L`

View presets set **named absolute** `L` targets, never relative
transformations, and always through `set_normal_gameplay_angles()` so the
admitted domain is enforced by construction. `Top` is defined at exactly
`NORMAL_GAMEPLAY_MAX_PITCH_RAD`; if that limit ever moves, `Top` moves with it
and a test binds the two.

Applying a preset must refresh the relative-command resolver, because the
resolver consumes `Q(L.local_yaw)`. Current code does this through
`_refresh_control_frame_presentation()`.

### 8.3 Slice layout

No layout presets. `AdaptiveLayerLayout` remains algorithmic. Layout may move
anchors and change rows, columns, and spacing; it must not rotate slice-local
coordinates, alter `B`, alter gameplay state, or reorder semantic slice
identity. Spacing and grid quality remain Stage 54F, issues #69 and #70.

### 8.4 Outer framing

A View preset restores the **fitted framing baseline**: focus returns to the
fit focus and zoom returns to `1.0`. This is stated as a rule of the View
contract rather than encoded as `pan`/`zoom` fields on each preset, because all
six presets carry identical values and the fields therefore express nothing.
Stage 54E-4b removes the per-preset `zoom` and `pan` fields and replaces the
call with a named `restore_fitted_framing()` step.

Manual pan and zoom after applying a preset are ordinary user adjustments; they
do not change `L`, and they make the view identity `Custom` under section 8.7.

### 8.5 Projection

Projection is not a preset dimension. Every fitted product view is
orthographic, `fit_bounds()` forces it, and `clear_presentation_state()`
restores it. There is no user-facing camera projection choice and Stage 54E-4b
must not add one.

`display.projection_strength` is a 4D slice projection setting, not a camera
projection mode. It remains an independent persistent display setting and no
preset may override it.

### 8.6 GUI

No GUI preset family. The existing independent settings are clearer than a
preset would be, and `display.hud_density` already covers the composite case.
Stage 54E-4b changes no GUI setting, adds no GUI preset, and renames nothing;
cockpit composition is Stage 54E-5.

A View preset must never change any GUI setting, and no GUI setting may move
the board or change any geometry transform. `display.hud_density` currently
shows and hides the camera panel, which changes only whether the control is
visible.

### 8.7 View identity under manual mutation

View identity is **derived from state equality**, not tracked by a flag.

```text
current_view_id() =
    the named preset whose orientation target equals the current orientation
    within epsilon, otherwise "custom"
```

In Live 4D the compared orientation is `(L.local_yaw, L.local_pitch)`; in Live
3D and replay it is the outer `(yaw, pitch)`. This removes the F3 class of
defect structurally: Fit View and Reset View leave `L = (0,0)`, which equals
`front`, so the selector truthfully reads "Front" instead of the current false
"Iso". A label can no longer disagree with the state that produced it.

### 8.8 Combined presets

**No combined presets.** Option A, strictly separate, is adopted. With no
layout preset family and no GUI preset family there is nothing to combine, so a
composite family would exist only to reintroduce the coupling Stage 54E-2
removed. Named composite profiles remain possible for a future Explorer or
campaign surface, but they are not ordinary Live-game presets and are out of
scope for Stage 54E-4b.

## 9. Reset and lifecycle matrix

Target behaviour. `B`, `L`, layout, and `V/P` rows match the accepted section
14 contract of `4d_presentation_interaction_architecture.md`; the View identity
column is new and follows from section 8.7.

| Operation | `B` | `L` | Layout | `V/P` | GUI | View identity |
| --- | --- | --- | --- | --- | --- | --- |
| Apply View preset | unchanged | set to named target | unchanged | restore fitted framing | unchanged | that preset |
| Manual yaw / pitch | unchanged | changed | unchanged | unchanged | unchanged | derived; `Custom` unless it lands on a named target |
| Manual pan / zoom | unchanged | unchanged | unchanged | changed | unchanged | derived from orientation only, so unchanged |
| Fit View | unchanged | unchanged | recompute | fitted default | unchanged | derived, unchanged |
| Reset View | identity | `(0,0)` | recompute | fitted default | unchanged | `Front` by derivation |
| Restart Game | identity | `(0,0)` | recompute | fitted default | unchanged | `Front` |
| New Game | identity | `(0,0)` | recompute | fitted default | unchanged | `Front` |
| Change Setup | cleared with session | cleared | cleared | cleared | unchanged | recomputed on re-entry |
| Return to menu | cleared with session | cleared | cleared | cleared | unchanged | recomputed on re-entry |
| Re-enter Live 4D | identity | `(0,0)` | rebuild | fitted default | unchanged | `Front` |
| Application restart | identity | `(0,0)` | rebuild | fitted default | loaded from settings | `Front` |

**Reset View restores the canonical product default** — option A of the three
candidates. It does not restore a persisted preferred preset and does not
restore session-entry state. Two reasons decide it. The accepted section 14
contract already defines Reset View as identity `B` plus local default `L` plus
fitted outer default, and a user-specific baseline would make one key mean a
different thing per profile, which is exactly the ambiguity this stage exists to
remove. Reset View continues to change `B`, which is explicitly defined by the
accepted architecture, the input contract help group, and the Live-4D help
text; that is not a new coupling introduced here.

**Restart Game keeps canonical defaults.** A user-configured presentation
default is deliberately not introduced; see section 10.

## 10. Persistence

| Property | Classification |
| --- | --- |
| View preset selection | never persisted — derived from `L` or outer orientation |
| `L.local_yaw`, `L.local_pitch` | session-local |
| outer focus, zoom, fit state, reflection | session-local |
| `B` | session-local |
| layout anchors | never persisted — derived |
| `camera.sensitivity`, `camera.invert_y` | application presentation preference |
| `theme.name`, `display.*`, `interface.show_onboarding` | application presentation preference |
| `accessibility.*` | accessibility preference |
| `diagnostics.show_layout_bounds` | session-local |
| board shape, piece set, randomness, seed, speed | setup state, owned by Stage 54E-3 |

**No new persistence and no schema change.** Stage 54E-4b reuses
`shell_settings_registry.json` at `schema_version 3` and adds no key, because
the accepted taxonomy persists nothing new: view identity is derived, and `L`
and framing stay session-local. The section 14 rule that persisting `L`,
anchors, or `V` would require a versioned presentation schema is therefore not
triggered.

The invariant is unchanged: no presentation state enters native deterministic
snapshots, state hashes, replay identity, trace semantics, RNG identity, or
game setup.

## 11. Compatibility and migration

| Legacy ID | Disposition | Mapping |
| --- | --- | --- |
| `iso` | REDEFINE_COMPATIBLY | same yaw/pitch target; framing fields dropped |
| `front` | REDEFINE_COMPATIBLY | same |
| `side` | REDEFINE_COMPATIBLY | same |
| `back` | REDEFINE_COMPATIBLY | same |
| `top` | REDEFINE_COMPATIBLY | same; pitch bound to `NORMAL_GAMEPLAY_MAX_PITCH_RAD` |
| `opposite_iso` | REDEFINE_COMPATIBLY | same |
| `custom` | REDEFINE_COMPATIBLY | becomes a derived result rather than a flag value |
| `CameraRig.apply_framing_preset()` | DEPRECATE | replaced by `restore_fitted_framing()`; the 54E-2c adapter has done its job |
| `CameraRig.apply_preset()` | REDEFINE_COMPATIBLY | retained as the 3D and replay orientation path, documented as such |
| per-preset `zoom` / `pan` fields | REMOVE | uniform across all six presets; carry no information |

No stored preference references a view preset, so there is no stored-value
migration and no risk of silent reinterpretation. All six public IDs and their
displayed labels survive unchanged.

## 12. Mode applicability

| Family | 2D | 3D | 4D |
| --- | --- | --- | --- |
| View presets | not exposed | exposed; targets outer orientation | exposed; targets `L` |
| Slice layout | n/a | n/a | algorithmic |
| Interface settings | shared | shared | shared |
| Fit View | yes | yes | yes |
| Reset View | mode reset | mode reset | full presentation reset |

Live 2D is a flat board on a fixed orthographic front view with no `L` and no
meaningful orientation choice, so the View selector is hidden there. This is
accepted Decision A in section 20.

## 13. Stage 54E-3 integration boundary

Presentation presets do not belong in game setup. The repository already
supports this strongly: `setup_field_spec.gd` defines a
`presentation_preference` category with `IDENTITY_PRESENTATION_PREFERENCE`,
forbids it from being session identity, and forbids it from the ordinary setup
path — and Stage 54E-3 deliberately declared no field in that category. The
category exists and is empty by design.

Destination for View controls after Stage 54E-3:

```text
live cockpit VIEW section    View selector, Fit View, Reset View   (current, retained)
settings                      camera sensitivity, invert Y, GUI, accessibility (current, retained)
pre-game setup                nothing
```

Stage 54E-4b adds no field to the setup surface and requires no Stage 54E-3
change. Stage 54E-3 is merged at `ad365627`; there is no branch integration
point to schedule.

## 14. Explorer boundary

Explorer will later permit free inspection beyond normal gameplay, including
roll and broader basis manipulation. The boundary Stage 54E-4b must respect:

- `SliceLocalOrientation.set_angles()` stays available as the unconstrained
  primitive; View presets use `set_normal_gameplay_angles()` only.
- `CameraRig.roll()` and `nudge_roll()` stay as generic primitives, absent from
  normal-gameplay action registration.
- No View preset sets or persists roll; every preset application zeroes it.
- The View preset API must remain callable by a future Explorer surface, so it
  must not assume the Live-4D fixed mount inside the preset definition.

## 15. Stage 54E-4b implementation plan

One bounded implementation PR. The audit shows no load-bearing sequential
dependency that would justify splitting it.

**Files and components**

| Component | Old behaviour | Target behaviour |
| --- | --- | --- |
| `scripts/presentation/camera_preset.gd` | six records of yaw/pitch/zoom/pan plus `custom` constant | six records of yaw/pitch only; add `resolve_id(yaw, pitch, epsilon)` returning the matching ID or `custom` |
| `scripts/rendering/camera_rig.gd` | `apply_framing_preset()` adapter; `_current_view_preset` flag set by `_mark_custom_view()` and `fit_bounds()` | `restore_fitted_framing()`; `current_preset_id()` derives from outer `(yaw, pitch)` via `resolve_id()`; delete the flag and `_mark_custom_view()` |
| `scripts/app/trace_replay_app.gd` | `_apply_live_4d_preset()` calls `apply_framing_preset()`; label read from rig in all modes | `_apply_live_4d_preset()` sets `L` then calls `restore_fitted_framing()`; in Live 4D the label derives from `L` via `resolve_id()`, not from the rig |
| `scripts/ui/replay_hud.gd` | camera panel visible in every live mode when density is not compact | hidden in Live 2D; tooltip and section wording corrected per section 7 |
| `scripts/input/live_input_contract.gd`, Live-4D help text | "camera preset" wording | View wording; no behaviour change |

**Migration**: none required; no stored preference references a preset.

**Authority impact**: none. No transfer, no establishment, no schema change.

**Forbidden adjacent work**: Stage 54E-5 cockpit consolidation, Stage 54F
spacing and grid work including issues #69 and #70, any GUI preset family, any
layout preset family, any camera projection control, any change to `B`
semantics, `SliceBasis4D`, `SliceLocalOrientation` clamps, layout algorithms,
native code, or gameplay.

## 16. Automated evidence design

New or extended Godot tests, written before the implementation.

**View ownership** — applying every preset in Live 4D proves `B` slots
unchanged, layout snapshot unchanged, native snapshot JSON and state hash
unchanged, `L` equal to the named target, and framing restored to the fitted
baseline. Applying every preset in Live 3D proves the outer orientation reaches
the target and `L` is untouched.

**Framing reset is declared, not incidental** — after a manual pan and zoom,
applying any View preset restores focus to the fit focus and zoom to `1.0`.

**Layout isolation** — recomputing the adaptive layout leaves `L`, `B`, and
canonical state unchanged, and no API exists to select a layout preset.

**GUI isolation** — changing `theme.name`, `display.hud_density`,
`display.board_detail`, and `display.ui_scale` leaves every geometry transform,
`B`, `L`, anchors, framing, and deterministic identity unchanged.

**Accessibility isolation** — applying every preset leaves every
`accessibility.*` value and `camera.sensitivity` / `camera.invert_y` unchanged.
This locks finding F6.

**View identity** — `resolve_id()` returns the named ID at each target,
`custom` after a manual yaw or pitch nudge, and is unaffected by manual pan or
zoom. After Fit View and after Reset View the identity is `front`, not `iso`,
which is the direct regression test for F3.

**Reset and lifecycle** — for each of Reset View, Restart Game, New Game,
Change Setup, return to menu, mode change, re-entry, and settings reload, assert
the row of the section 9 matrix.

**Persistence** — the persisted settings document contains no view preset, `L`,
framing, `B`, or layout key; presentation preferences reload correctly; the
deterministic session setup, snapshot, hash, and replay identity contain no
presentation state.

**Mode applicability** — the View selector is absent in Live 2D and present in
Live 3D and Live 4D at non-compact density.

## 17. Human-visible verification design

A focused real-window Godot 4.7.1 review, recorded in the format established by
`docs/plans/stage_54e3_setup_disclosure_manual_acceptance.md`, with environment,
per-scenario outcome, screenshots, and advisories. It is not Stage 54F.

Scenarios: every retained View preset has an obvious, predictable, and distinct
visual effect in 3D and 4D; applying a View preset visibly does not re-slice,
confirmed against the basis indicator; the slice layout does not rotate slice
contents when the layer count changes; changing `theme.name`,
`display.hud_density`, and `display.board_detail` does not move the board;
Reset View matches the section 9 row; the selector label is truthful after
manual rotation, after Fit View, and after Reset View; restart and re-entry are
understandable; Live 2D shows no View selector; Live 3D remains coherent.

Visual plausibility is not accepted as proof of deterministic isolation; that is
covered by section 16.

## 18. Adversarial review

1. No ordinary View preset changes more than one presentation space: it sets
   orientation and restores a defined framing baseline, and the framing step is
   a declared rule rather than hidden per-preset data.
2. Re-slicing cannot be confused with view orientation, because no View preset
   touches `B` and re-slicing keeps its own controls and indicator.
3. No GUI setting alters board geometry; section 16 locks it.
4. Reset View has exactly one meaning, inherited from the accepted section 14
   contract.
5. Restart behaviour is explicit and deliberately not user-configurable.
6. Every preset-owned property has a persistence classification in section 10.
7. Manual mutation cannot produce a false label, because identity is derived.
8. Accessibility preferences are untouched and locked by test.
9. No deterministic state is included anywhere in the contract.
10. Stage 54E-3 is not redesigned; Stage 54E-4b adds no setup field.
11. No Stage 54E-5 cockpit consolidation appears here.
12. The 54E-2c adapter is retired rather than preserved for its own sake, and
    the vacuous `zoom`/`pan` fields are removed.
13. No preset family is invented: layout and GUI families are explicitly
    rejected for lack of demonstrated player-facing choice.
14. Section 15 names the files, the old and target behaviour, the migration,
    and the forbidden scope, so another engineer can implement it without
    guessing.

## 19. Forbidden scope for Stage 54E-4

Stage 54D-3 Hold; Stage 54E-5 cockpit consolidation; Stage 54F visual work
including issues #69 and #70; board styling, cell materials, and HUD polish;
responsive-layout overhaul; Explorer; camera projection controls; any change to
gameplay, native code, topology, RNG, queue, Ghost, snapshots, hashes, or
replay and trace schemas.

## 20. Accepted product decisions

Both decisions below were accepted by the product owner on 2026-08-17. No
unresolved design question remains.

### Decision A — View selector in Live 2D — ACCEPTED

```text
ACCEPTED: hide the View selector in Live 2D; keep it in Live 3D and Live 4D
Rejected alternative: keep it visible in all three modes, as today
```

Reason. Live 2D is a flat board on a fixed orthographic front view with no
slice-local orientation. Top, Side, Back, and Opposite Iso have no meaningful
effect there, so the control offers six choices that do not answer a question
the 2D player has. The alternative keeps the inspector structurally identical
across modes, which has some consistency value, at the cost of advertising
controls that do nothing useful. The recommendation follows the same principle
Stage 54E-3 applied when it stopped presenting a one-option piece-set selector.

### Decision B — framing on preset application — ACCEPTED

```text
ACCEPTED: applying a View preset restores the fitted framing baseline,
          discarding manual pan and zoom
Rejected alternative: preserve the player's current pan and zoom across
          preset changes
```

Reason. This is today's behaviour, but only as an accident: all six presets
declare `zoom: 1.0` and `pan: ZERO`, so the framing step happens to reset
rather than to express anything per preset. The decision is whether to keep
that effect once it becomes an explicit rule. Restoring the baseline makes each
named view a clean, reproducible state, which is what a named view is for. The
alternative suits sustained close inspection, where re-zooming after every
orientation change is friction; that use case belongs to the future Explorer,
which is free to adopt the other rule. Confirming the recommendation preserves
current behaviour, so choosing it requires no migration.
