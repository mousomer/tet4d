# Camera and GUI Preset Semantics

Role: architecture
Status: human view semantics accepted; final review blockers corrected; ready for final confirmation review
Scope: Godot product-shell view lifecycle, preset actions, fit/reset, and preference boundaries across Live 2D/3D/4D and replay
Canonical owner: this file
Consumes: docs/architecture/4d_presentation_interaction_architecture.md
Stage: 54E-4a design and audit
Last updated: 2026-08-18

## 1. Purpose, authority, and stage boundary

This document owns the forward-looking product contract for transient view
state, named view actions, Fit View, Reset View, view-context lifetime, and the
boundary between current view state and persistent shell preferences. It
consumes the accepted Live-4D pipeline `C -> B -> G_D -> L -> anchor/layout ->
V/P` without merging its state owners.

The human product semantics in this revision are accepted. Stage 54E-4a
changes documentation only and does not implement them. Stage 54E-4b is not
eligible until a final confirmation review accepts this corrected
contract. No further human E4a decision gate is required unless implementation
evidence reveals a genuinely new product contradiction.

This revision clarifies and supersedes the forward-looking presentation
lifecycle chosen at Stage 54E-2d. Stage 54E-2d correctly implemented and
reviewed the then-accepted rule that Restart Game established fresh
presentation defaults. Stage 54E-4 now deliberately refines that rule:
Restart Game preserves the current view, while Reset View explicitly restores
the complete canonical view. Historical Stage 54E-2d evidence remains true.

Authority effect: clarification within existing Godot presentation authority.
There is no deterministic gameplay authority transfer, no native authority
establishment, and no change to replay, trace, snapshot, hash, RNG, or setup
identity.

## 2. Runtime audit and mismatches to be implemented later

The Stage 54E-4a audit records current implementation truth rather than
assuming the documentation is already implemented:

- `CameraRig.fit_bounds()` currently writes `_camera.projection`,
  `_target_focus`, `_fit_focus`, `_target_yaw`, `_target_pitch`,
  `_target_roll`, `_current_view_preset`, `_current_view_octant`,
  `_current_fit_state`, horizontal-reflection state/focus and the rendered
  world transform, `_base_distance`, `_zoom_multiplier`, `_target_distance`,
  `_base_orthographic_size`, and `_camera.size`. `_snap_to_targets()` then
  copies target focus/distance/yaw/pitch/roll into the corresponding current
  fields and updates camera/world/gizmo presentation. It therefore establishes
  canonical orientation and identity/diagnostic bookkeeping as well as
  fitting; it is not yet the framing-only Fit View required by this contract.
  E4b's Fit refactor and identity-state retirement are one coupled change.
- `TraceReplayApp._fit_view()` supplies canonical yaw/pitch for Live 3D and
  Live 4D and uses replay-style defaults for Live 2D and replay. Fit View must
  be split from canonical-view establishment in E4b.
- `_reset_live_2d()`, `_reset_live_3d()`, and `_reset_live_4d()` reset gameplay
  and then call `_fit_view()`. Live 4D additionally restores `B`, `L`, layout,
  and rig defaults. This violates the new restart-preserves-view rule.
- Live-mode entry and context exit currently have explicit 4D teardown/default
  seams, but equivalent canonical ownership for 2D, 3D, and replay is implicit
  in the shared camera rig. E4b must make every mode explicit.
- Live 2D currently falls through to the replay-style oblique fit defaults.
  It does not yet implement the accepted flat/front-on canonical view.
- `camera_rig.gd` owns the real selected-identity machinery:
  `_current_view_preset`, every assignment in initialization, the dead
  `frame_board()`, `fit_bounds()`, `clear_presentation_state()`, `apply_preset()`,
  `apply_framing_preset()`, and `_mark_custom_view()`; the
  `current_preset_id()` reader; and `view_status_text()`. The coupled
  `_current_view_octant` and `_current_fit_state` fields provide diagnostics
  but are currently updated through the same paths. `trace_replay_app.gd`
  reads `current_preset_id()` after action dispatch and during camera-status
  refresh, and `replay_hud.gd::set_camera_preset()` turns that identity back
  into a selected `CameraPresetSelector` item. This product model is retired
  below without discarding useful orientation/framing diagnostics.
- `CameraRig.frame_board()` has zero live callers in runtime and tests. It is
  dead combined framing/orientation/identity code, not a production path or
  compatibility surface. E4b deletes it; its responsibilities are superseded
  by the explicit arbitrary outer-orientation and framing-only seams below.
- `display.ui_scale` is declared under the registry's `display` category;
  `reset_display_settings_to_defaults()` therefore resets it, while
  `reset_accessibility_settings_to_defaults()` does not. The target ownership
  is the reverse.
- No player-facing orthographic/perspective setting exists. Every fitted view
  forces orthographic projection. `display.projection_strength` changes
  rendered cell/particle/event emphasis and is not a camera-projection choice.

These are E4b or explicitly bounded settings corrections. No runtime
correction belongs to E4a.

### 2.1 Complete current identity-value inventory

Current production paths write eight known runtime values to
`_current_view_preset`:

| Current value | Source | Public named action? | E4b disposition |
| --- | --- | --- | --- |
| `iso` | initialization, clear, fit/action paths | yes | retain as action ID only |
| `front` | `apply_preset()` / `apply_framing_preset()` | yes | retain as action ID only |
| `side` | same | yes | retain as action ID only |
| `back` | same | yes | retain as action ID only |
| `top` | same | yes | retain as action ID only |
| `opposite_iso` | same | yes | retain as action ID only |
| `custom` (`CameraPresetScript.CUSTOM`) | `_mark_custom_view()` after manual orbit/nudge/roll/pan/zoom | no; identity sentinel only | remove after all identity writers/readers and HUD selection synchronization are removed |
| `PYTHON_DIAGRAM_REPLAY_VIEW` | default `fit_bounds()` argument used by replay/2D fits; also written inside dead, zero-caller `frame_board()` | no; not present in `CameraPresetScript.PRESETS` | remove as an identity pseudo-ID; retain replay canonical numeric constants and ordinary diagnostic context; delete `frame_board()` |

`fit_bounds(view_preset=...)` does not itself validate its string parameter,
but current production callers supply only `iso` or the default replay
pseudo-ID. The table inventories actual production values rather than
speculative external misuse of that internal API.

`CameraPresetScript.label()` falls back through `definition()` to the Iso
record for an unknown ID. Consequently `view_status_text()` can render
`PYTHON_DIAGRAM_REPLAY_VIEW` as `Camera: Iso` in replay even though it is not
an Iso action. E4b removes this mislabel path by removing persistent current-
preset identity and its status/HUD consumers; it must not promote the replay
pseudo-ID into `PRESETS` or a new public action.

That unknown-ID fallback is only one defect class. Current fit and application
paths can also assign a known public ID while the rig orientation does not
match that action target. In Live 4D, `_fit_view()` passes `iso` to
`fit_bounds()` while establishing the fixed outer yaw
`3.5779249665883754` (approximately 205 degrees), so the rig can display
`Camera: Iso` for a non-Iso outer mount. `_apply_live_4d_preset()` similarly
routes yaw/pitch to `L` and then lets `apply_framing_preset(id)` label the rig
with that public ID without changing its outer orientation. Retiring
`_current_view_preset` and preset-derived status/HUD labels removes both the
unknown-ID replay fallback and known-ID false-label classes. E4b must not
replace them with continuously tracked identity.

## 3. The transient current-view model

The current navigated view belongs to the current live presentation context.
It is not gameplay-run state and is not an application preference.

Transient current-view state includes, where the mode owns it:

- exact Live-4D presentation basis `B`;
- shared Live-4D slice-local orientation `L`;
- current slice anchors/layout and other layout-derived state;
- camera/view yaw, pitch, and roll;
- focus, pan, zoom, fit reference, distance, orthographic size, and reflection;
- camera projection type when the mode has no explicit projection preference;
- interpolation and fit-derived transient state; and
- any mode-local framing or orientation state needed to reproduce the current
  presented geometry.

Each state retains the semantic owner established by Stage 54E-2. Reset View
does not become the owner of `B`, `L`, layout, or framing; it owns the composite
operation that asks those owners to restore the complete canonical view for
the current mode/context.

Transient view state must not be written to shell settings merely because the
player leaves the viewport in that state. It remains excluded from native
deterministic state, game setup, snapshots, hashes, RNG identity, replay
identity, and trace identity. A future persisted arbitrary-view feature would
be an explicit saved-view/bookmark contract, not accidental current-pose
persistence. Bookmarks are out of scope.

## 4. Mutable-presentation inventory and ownership

| Property | Semantic owner | Lifetime / persistence | Reset owner |
| --- | --- | --- | --- |
| Live-4D signed basis `B` | `EXACT_BASIS` | current 4D presentation context; never persisted | Reset View through basis owner |
| Live-4D `L.local_yaw`, `L.local_pitch` | `SLICE_LOCAL_ORIENTATION` | current 4D presentation context; never persisted | Reset View through local-orientation owner |
| slice anchors, rows, columns, spacing, fit reference | `SLICE_LAYOUT` | derived current-context state; never persisted | Reset View rebuilds canonical layout |
| focus, pan, zoom, size, distance, reflection, camera orientation | mode's `OUTER_FRAMING` / camera owner | current presentation context; never persisted | Reset View through mode owner; Fit changes framing only |
| camera projection type | `PROJECTION` presentation owner | transient canonical-view state; never persisted because no player choice exists | Reset View; Fit preserves it |
| `display.projection_strength` | persistent display presentation preference | local shell | Display Settings reset |
| `display.window_mode`, `display.windowed_size` | persistent shell/display preference | local shell | Display Settings reset |
| `display.hud_density`, `display.board_detail`, `display.show_w_labels`, `ghost.enabled`, `settled_cells.opacity` | persistent display/visibility preference | local shell | Display Settings reset |
| `theme.name` | persistent theme preference | local shell | Display Settings reset |
| `display.ui_scale` | `ACCESSIBILITY_PRESENTATION` | local shell accessibility preference | Accessibility Settings reset only |
| `accessibility.high_contrast`, `.reduced_motion`, `.show_help_hints` | `ACCESSIBILITY_PRESENTATION` | local shell | Accessibility Settings reset |
| `camera.sensitivity`, `camera.invert_y` | persistent input/presentation preference | local shell | Display/camera settings reset; never Reset View |
| `replay.playback_speed`, `replay.loop_enabled` | persistent replay-player preferences | local shell; not view pose and not deterministic replay content | replay/settings owner, not Reset View |
| `interface.show_onboarding` | persistent interface preference | local shell | interface/settings owner |
| `diagnostics.show_layout_bounds` | diagnostics visibility | session only | diagnostics/settings owner |
| setup disclosure expansion | setup-surface presentation owner | ephemeral setup-surface state | setup surface, not Reset View |

Window mode/size and replay speed/loop are explicitly included so the
persistence inventory is not inferred from a subset of camera-like state.

## 5. One composite Reset View

There is exactly one ordinary player-facing command named **Reset View**.
There are no parallel ordinary reset families named Reset Camera, Reset
Orientation, Reset Slice View, Reset Layout, Reset Basis, or Reset Framing.
Internal owner-specific helpers are required, but they are implementation
seams behind the one command.

Reset View preserves gameplay, frozen setup, deterministic identity, replay
content, and every persistent preference. It restores the complete canonical
view for the current mode/context. Projection is restored only as part of that
canonical transient view, never by changing a persistent display preference.

In Live 4D, the composite operation restores identity `B`, default `L`, the
canonical adaptive layout and anchors, canonical outer orientation/reflection,
and canonical fitted focus/pan/zoom/framing. It also restores any other
transient view state the implementation audit proves is needed for the same
canonical result. The operation changes no native gameplay state.

## 6. Fit View is framing-only

There is one separate ordinary command named **Fit View**. It frames the
currently presented board/content in the viewport.

Fit View preserves gameplay, `B`, `L`, slice layout and anchors, semantic
arrangement, current orientation, projection type, accessibility preferences,
display preferences, and replay content. It may change only the focus, pan,
zoom, distance/orthographic size, and fit reference required to frame the
already-current geometry.

E4b must provide explicit rig-side orientation and framing operations plus the
app-side composition seam:

```text
CameraRig.establish_outer_view(yaw, pitch, roll, reflection_active)
CameraRig.fit_current_bounds(bounds, margin)       # reads current orientation; writes framing only
TraceReplayApp._establish_canonical_view_and_fit(mode)
```

`camera_rig.gd` owns `establish_outer_view()`. It accepts arbitrary absolute
yaw, pitch, and roll values plus the required horizontal-reflection active
state; it is not limited to the six public action IDs. It writes the three
orientation targets and reflection-active state, then uses an orientation-only
snap to copy yaw/pitch/roll into current state and update the camera, derived
reflection transform, and orientation gizmo immediately. Reflection pivot is
derived from the current framing focus, so a later framing update recomputes
the presentation transform around that focus without changing whether
reflection is active.

`establish_outer_view()` is presentation-only. It performs no bounds
calculation or fitting and does not change focus/pan, fit reference, zoom,
distance, orthographic size, or projection. It does not assign action/preset
identity or identity-derived diagnostics. It must not mutate `B`, `L`, slice
layout/anchors, gameplay/replay content or deterministic identity, persistent
preferences, or shell settings. It must not call the current broad
`_snap_to_targets()`, because that helper also copies framing targets; E4b
provides the bounded orientation-only snap/update needed by this contract.

The existing `fit_bounds()` path is replaced by `fit_current_bounds()`; it
cannot serve both contracts while it also writes yaw/pitch/roll, reflection,
projection, and identity bookkeeping. Public `_fit_view()` calls only
`fit_current_bounds()`. Mode entry, context re-entry, application
initialization, and Reset View call
`TraceReplayApp._establish_canonical_view_and_fit(mode)`. That orchestrator
first restores the mode-specific semantic owners (`B`, `L`, layout and
canonical projection where applicable), then calls `establish_outer_view()`
with that mode's arbitrary canonical outer yaw/pitch/roll/reflection values,
and finally calls `fit_current_bounds()`.

Live 4D keeps the two orientation layers separate. Canonical Reset/re-entry
sets default `L` through `SliceLocalOrientation`, never through
`establish_outer_view()`. It calls `establish_outer_view()` only for the fixed
Live-4D outer mount and active reflection, then performs framing-only fit.

## 7. View lifetime and lifecycle matrix

The preservation boundary is the presentation context, not the individual
Tetris run.

| Operation | 2D | 3D | Live 4D | Replay | Gameplay / deterministic content | Persistent preferences |
| --- | --- | --- | --- | --- | --- | --- |
| Fit View | reframe flat current view | preserve orientation; reframe | preserve `B`, `L`, layout, orientation; reframe | preserve replay view orientation; reframe | unchanged | unchanged |
| Reset View | canonical flat view + fit | canonical 3D view + fit | identity `B`, default `L`, canonical layout/view + fit | canonical replay view + fit | unchanged | unchanged |
| Restart Game | preserve current view | preserve current view | preserve complete current `B/L/layout/V/P` | n/a | reset live gameplay | unchanged |
| new game, same mode/context | preserve current view | preserve current view | preserve complete current view | n/a | establish new live gameplay | unchanged |
| game over/loss | preserve until transition or Reset View | same | same | n/a | follows gameplay owner | unchanged |
| Change Setup / setup exit | destroy live presentation context | destroy | destroy | n/a | current live session ends per setup flow | unchanged |
| return to menu | destroy current presentation context | destroy | destroy | destroy replay presentation context | mode/session owner applies | unchanged |
| mode change | destroy old mode context | destroy | destroy | destroy | mode owner applies | unchanged |
| re-enter after exit/change | fresh canonical mode view | fresh canonical mode view | fresh canonical mode view | fresh canonical replay view | unchanged by view establishment | load/retain |
| application restart | fresh canonical mode view | fresh canonical mode view | fresh canonical mode view | fresh canonical replay view | loaded/created separately | load |

`Change Setup` is a teardown/re-entry in the current scene flow and therefore
belongs to the context-exit category. E4b must not invent hidden persistence to
recreate the old pose after that transition. A configured or random new game
started without leaving the live presentation context preserves the view.

## 8. Named view presets are actions

Named view presets are commands that move the relevant mode-owned orientation
to a named target and then establish the declared framing baseline. They do not
enter a persistent named mode.

After manual rotate, pan, or zoom, no preset needs to remain selected. The
product does not require `Top (modified)`, `Oblique (modified)`, `Custom`, or a
continuously derived current-preset identity. Consequently:

- `camera_rig.gd::_current_view_preset`, `_mark_custom_view()`, and
  `current_preset_id()` are removed;
- `view_status_text()` stops labelling the current camera from
  `_current_view_preset`, while useful orientation/framing diagnostics remain;
- the two `TraceReplayApp` reads of `current_preset_id()` and
  `ReplayHud.set_camera_preset()` are removed, and the selector becomes a true
  action surface with no selected-state synchronization;
- pan/zoom never decide named-preset membership;
- `CameraPresetScript.CUSTOM` and its special `label()` branch are removed once
  those identity consumers are gone; and
- `_current_view_octant` and `_current_fit_state` remain useful diagnostic
  concepts but are renamed/refactored as non-identity view-context and framing-
  status bookkeeping, with every current writer and test updated.

`resolve_id()` and a `0.001`-radian preset-membership tolerance were earlier
design proposals. Neither exists in runtime, neither belongs to the accepted
product model, and E4b has no runtime removal work for either. The separate
`0.001` literals currently used as ordinary numerical safety denominators or
test tolerances are not preset-membership machinery. Preset application may
assert that a target was reached using ordinary test tolerances; that is
conformance evidence, not persistent product identity.

The six current public IDs and labels remain compatibility actions with their
existing targets. In Live 4D, yaw/pitch target `L`; in Live 3D and replay they
target the legitimate outer orientation owner. They are not exposed in Live
2D. Every action preserves `B` and layout, sets zero roll where the mode owns
roll, and restores the fitted framing baseline as accepted on 2026-08-17. An
outer-view action may establish reflection only when reflection is part of the
mode/action's defined outer-view target. The current public 3D/replay action
targets use `reflection_active = false`. Live-4D named actions target `L`, have
no reflection semantics, and preserve the existing outer reflection. Fit and
all framing-only helpers always preserve reflection-active state.

| Action ID / label | Absolute yaw target | Absolute pitch target |
| --- | --- | --- |
| `iso` / Iso | `0.5585053606381855` | `0.4537856055185257` |
| `front` / Front | `0.0` | `0.0` |
| `side` / Side | `PI / 2` | `0.0` |
| `back` / Back | `PI` | `0.0` |
| `top` / Top | `0.0` | `NORMAL_GAMEPLAY_MAX_PITCH_RAD` (`PI / 3` today) |
| `opposite_iso` / Opposite Iso | `-2.5830872929516078` | `0.4537856055185257` |

The UI behaves as an action surface, not proof that one option remains
selected. Subsequent manual changes do not create a new identity.

### 8.1 Stage 54E-2c adapter disposition

`CameraRig.apply_framing_preset(id)` does not survive under that name or
signature. E4b refactors it into an ID-independent
`restore_fitted_framing()` operation because all six action definitions have
the same `zoom = 1.0` and `pan = Vector3.ZERO`; those fields are removed from
`CameraPresetScript.PRESETS` as non-information.

The framing operation may set target/current focus to `_fit_focus`, restore
the framing zoom multiplier to `1.0`, update target/current distance, and
restore the orthographic size from `_base_orthographic_size` on the currently
supported orthographic path. It may update the non-identity framing-status
diagnostic. It must not write yaw, pitch, roll, projection type, reflection-
active state, `B`, `L`, layout/anchors, action identity, or accessibility/
display preferences. When focus changes, presentation rendering may recompute
the already-selected reflection transform around that focus; this is derived
framing presentation and does not change reflection-active semantics. Its
snap/update helper must otherwise be framing-only rather than incidentally
copying orientation targets.

Live 4D action dispatch is renamed from
`TraceReplayApp._apply_live_4d_preset(id)` to
`TraceReplayApp._apply_live_4d_view_action(id)`, which sends the
definition's yaw/pitch to `_set_live_4d_local_orientation()` and therefore to
the legitimate `L` owner, then calls `restore_fitted_framing()`. The framing
helper never sees or owns Live-4D orientation.

`CameraRig.apply_preset(id)` is replaced by
`CameraRig.apply_outer_view_action(id)`, the 3D/replay view-action orientation
seam. It validates the public action ID, resolves its legitimate mode-specific
outer target, calls `establish_outer_view(yaw, pitch, 0.0, false)` for the
current public 3D/replay actions, and then composes
`restore_fitted_framing()`. A future action could pass reflection true only if
its normative outer-view target explicitly includes reflection. The action
does not create selected-preset identity. `TraceReplayApp` remains the mode-
aware dispatcher: Live 4D takes the `L` path without calling
`establish_outer_view()` or changing reflection, while 3D and replay take the
outer-rig path. Live 2D exposes no named orientation actions.

## 9. Mode-specific canonical view contracts

The common user concept is View. Internal ownership remains mode-specific.

### 9.1 Live 2D

The canonical 2D presentation is genuinely flat and simple: an orthographic,
front-on board with no gratuitous yaw, pitch, roll, perspective, or oblique
depth presentation. For the current XY board plane this means yaw `0`, pitch
`0`, roll `0`, no horizontal reflection, and orthographic projection. Reset
View restores that view and fits it. Fit View only reframes it. Orientation
presets remain absent because they cannot add a meaningful 2D choice.

E4b must replace Live 2D's current fall-through to replay-style oblique
`fit_bounds()` defaults with an explicit 2D canonical-view owner/path. This is
not authorization for a broader 2D visual redesign.

### 9.2 Live 3D

`CameraRig` is the legitimate 3D orientation and framing owner. The canonical
view is the existing accepted external diagram view (`LIVE_3D_DISPLAY_YAW_RAD`,
`LIVE_3D_DISPLAY_PITCH_RAD`, zero roll, orthographic projection, no 4D
reflection): yaw `0.5585053606381855`, pitch `0.4537856055185257` today. Reset View restores
that orientation and fits. Fit View preserves the current orientation and
projection while reframing. Live-4D `B` and `L` do not exist in this mode.

### 9.3 Live 4D

The canonical view composes identity `B`, default `L`, adaptive canonical
layout, the accepted fixed outer mount/reflection, orthographic projection,
and fitted framing. Canonical/default `L` is explicitly
`local_yaw = 0.0`, `local_pitch = 0.0`. The current accepted mount is yaw
`3.5779249665883754`, pitch `0.3490658503988659`, zero roll, with horizontal
reflection active. Reset View restores all of it through the separate owners.
Fit View preserves `B`, `L`, layout, mount/orientation, reflection, and
projection while reframing only.

### 9.4 Replay

Replay uses the replay camera/presentation owner and current replay content; it
does not receive Live-4D `B` or `L`. Reset View restores the canonical replay
diagram orientation (yaw `0.5585053606381855`, pitch
`-0.4537856055185257`, zero roll), orthographic projection, no horizontal
reflection, and fits it. Fit View preserves current replay
orientation/projection and reframes. Both operations preserve the loaded
replay document, frame index, state hashes, events, and deterministic replay
identity. Replay speed and looping are persistent replay-player preferences,
not view state.

## 10. Projection and preference reset ownership

The projection audit is resolved: Tet4D has no meaningful player-selectable
orthographic/perspective preference. Camera projection type is therefore part
of the canonical transient view for each relevant mode. Reset View restores
the canonical projection; Fit View preserves the current projection while
framing. Application restart and context re-entry establish the canonical
projection. E4b adds no projection setting.

The currently supported fitted production path is orthographic, so projection
preservation is not presently observable across multiple selectable projection
types. E4b proves that framing-only Fit does not assign projection and that the
supported orthographic state remains unchanged; it does not invent a
perspective-mode regression. If another projection mode is added later, the
same invariant becomes directly executable across those modes.

`display.projection_strength` remains a persistent renderer-emphasis setting
and is preserved by Fit View, Reset View, Restart Game, and context changes.

UI scale is an accessibility presentation preference even though its current
registry ID begins with `display.`. Target reset behaviour is:

| Operation | UI scale |
| --- | --- |
| Reset Display Settings | preserve |
| Reset Accessibility Settings | restore accessibility default |
| Reset View | preserve |
| Fit View | preserve |
| Restart Game | preserve |

E4b, or one separately routed bounded settings correction completed before its
acceptance, must reconcile the registry/reset mechanism and tests. Display
Reset is not an authorized cross-owner composite.

## 11. Exact Stage 54E-4b implementation plan

E4b is one semantic implementation objective. It may use an explicitly bounded
settings sub-commit if UI-scale ownership is clearer that way, but it must not
absorb unrelated human-review defects.

| Component / current owner | Exact current symbols and callers | Required E4b target |
| --- | --- | --- |
| `scripts/rendering/camera_rig.gd` — identity and diagnostics | `_current_view_preset`; writes in initialization, dead zero-caller `frame_board()`, `fit_bounds()`, `clear_presentation_state()`, `apply_preset()`, `apply_framing_preset()`, `_mark_custom_view()`; readers `current_preset_id()` and `view_status_text()`; coupled `_current_view_octant` / `_current_fit_state` | remove `_current_view_preset`, `_mark_custom_view()`, and `current_preset_id()`; remove every write/read; make `view_status_text()` report projection, numeric orientation/framing, non-identity context, and framing status without `CameraPresetScript.label()`; thereby remove both replay unknown-ID fallback and known-ID false labels such as Live-4D `Camera: Iso` at outer yaw 205 degrees; rename/refactor octant/fit fields as retained diagnostics; update every writer plus `test_camera_rig.gd` and direct-field/status assertions in `test_live_2d_shell.gd` |
| `scripts/rendering/camera_rig.gd` — outer orientation | no bounded arbitrary absolute outer-orientation seam; `fit_bounds()` and `apply_preset()` currently combine subsets of this responsibility with framing/identity; broad `_snap_to_targets()` copies both orientation and framing targets | add `establish_outer_view(yaw, pitch, roll, reflection_active)` exactly as section 6 specifies; write target and snapped current yaw/pitch/roll plus reflection-active presentation state only; use an orientation-only snap/update; support arbitrary mode canonical values as well as action targets; perform no fitting and change no projection, framing, identity, `B`, `L`, layout, gameplay/replay content, or preferences |
| `scripts/rendering/camera_rig.gd` — fit and action seams | `fit_bounds()`, `apply_framing_preset(id)`, `apply_preset(id)`, `_snap_to_targets()`; dead `frame_board()` has zero runtime/test callers | delete `frame_board()` with no compatibility replacement; replace `fit_bounds()` with framing-only `fit_current_bounds(bounds, margin)`, which reads current orientation for projected sizing but never writes orientation/projection/reflection-active state/identity; canonical state is established by `TraceReplayApp._establish_canonical_view_and_fit(mode)` using `establish_outer_view()` before fit; replace `apply_framing_preset(id)` with ID-independent `restore_fitted_framing()` under section 8.1; replace `apply_preset(id)` with `apply_outer_view_action(id)`, which resolves a 3D/replay action target and calls `establish_outer_view()` before that framing helper; ensure orientation and framing snaps cannot copy each other's targets |
| `scripts/presentation/camera_preset.gd` — action definitions | six `PRESETS` records with yaw/pitch/zoom/pan; `CUSTOM`; `label()` fallback/special case | retain the six IDs, labels, yaw, and pitch as action definitions; remove uniform `zoom`/`pan`; remove `CUSTOM` and its label branch after camera/HUD identity retirement; keep unknown-ID validation explicit; update `test_live_board_visual_grammar.gd`, `test_camera_rig.gd`, and preset assertions in `test_live_2d_shell.gd`. No `resolve_id()` or membership-tolerance runtime work exists |
| `scripts/app/trace_replay_app.gd` — dispatch and lifecycle | `camera_preset_requested` callback; `_apply_live_4d_preset()`; `_fit_view()`; `current_preset_id()` reads at action completion and `_refresh_camera_status()`; entry/reset/new-game/setup/menu/mode paths | remove both identity reads and HUD selection sync; replace the Live-4D seam with `_apply_live_4d_view_action(id)` routing yaw/pitch through `L`, preserving outer reflection, then calling `restore_fitted_framing()`; dispatch 3D/replay through `apply_outer_view_action(id)`; route public Fit to `fit_current_bounds()` only; add `_establish_canonical_view_and_fit(mode)`, which chooses canonical mode values, resets `B`/`L`/layout/projection through their owners, calls `establish_outer_view()` for outer mount/reflection, then fits; preserve view across live reset/same-context new game; canonicalize only at entry, Reset, re-entry, and application initialization; retain teardown on setup/menu/mode exit |
| `scripts/ui/replay_hud.gd` — View surface | `CameraPresetSelector` `OptionButton`, `set_camera_preset(id)`, `camera_preset_requested`, `fit_view_requested`, `basis_reset_requested`, and its Reset View button | replace the selected `OptionButton` model with an action menu/button surface that emits the same six IDs but displays no persistent selection; remove `set_camera_preset()`; hide named actions in 2D; rename the misleading basis signal to `reset_view_requested` and connect it to mode-aware composite reset; expose exactly one Reset View and one Fit View; retain status text without a named-current-view claim |
| `scripts/input/live_input_contract.gd`, `scripts/ui/replay_hud.gd`, `scripts/ui/onboarding/live_onboarding_model.gd` — help/input wording | Camera/Framing groups, `LIVE_4D_HELP_TEXT`, quick-help rows, and onboarding copy including the incorrect current sentence “Fit View restores orientation” | use View terminology; state Fit is framing-only, Restart preserves same-context view, and Reset restores the complete canonical view; route one composite Reset View and one framing-only Fit View; add no reset families; update `test_live_input_contract.gd` and `test_replay_viewer_layout.gd` |
| Live 2D path (`TraceReplayApp` + `CameraRig`) | `_fit_view()` falls through to default replay yaw/pitch/pseudo-ID | canonical establishment calls `establish_outer_view(0.0, 0.0, 0.0, false)` and establishes orthographic projection before fit; Fit changes framing only and exposes no named orientation actions |
| Live 3D path (`TraceReplayApp` + `CameraRig`) | `_fit_view()` supplies `LIVE_3D_DISPLAY_*`; preset callback calls `apply_preset()` | canonical Reset calls `establish_outer_view(LIVE_3D_DISPLAY_YAW_RAD, LIVE_3D_DISPLAY_PITCH_RAD, 0.0, false)` and establishes orthographic projection before fit; Fit preserves current orientation/projection/reflection; named actions resolve their target and call the same outer-orientation seam followed by framing restoration |
| Live 4D owners (`TraceReplayApp`, basis/orientation/layout owners, `CameraRig`) | `_restore_live_4d_presentation_defaults()`, `_reset_live_4d_view()`, `_apply_live_4d_preset()`, `_fit_view()` | canonical Reset composes identity `B`, `L=(0.0,0.0)`, layout, orthographic projection, `establish_outer_view(LIVE_4D_DISPLAY_YAW_RAD, LIVE_4D_DISPLAY_PITCH_RAD, 0.0, true)`, and fit; Fit preserves all but framing; named action orientation always bypasses the rig and reaches `L`, preserving outer mount/reflection |
| Replay path (`TraceReplayApp` + `CameraRig`) | default `fit_bounds()` path writes `PYTHON_DIAGRAM_REPLAY_VIEW`; `view_status_text()` falls back to Iso label | canonical Reset establishes orthographic projection, calls `establish_outer_view(PYTHON_DISPLAY_YAW_RAD, PYTHON_DISPLAY_PITCH_RAD, 0.0, false)`, then fits; Fit preserves current orientation/projection/reflection/content; remove pseudo-ID assignment and `Camera: Iso` fallback without creating a public replay preset |
| `config/shell_settings_registry.json` — UI-scale declaration | `display.ui_scale` is category `display`, persistent local-shell preference | preserve the stable setting ID and persistence, change operational category/ownership to accessibility so generated/reset routing agrees with the accepted owner |
| `scripts/ui/settings_panel.gd` — reset routing | `reset_display_settings_to_defaults()` resets `display/theme/camera`; `reset_accessibility_settings_to_defaults()` resets `accessibility` | with the registry category corrected, Display Reset preserves UI scale and Accessibility Reset restores it; update `test_shell_display_settings.gd`, `test_shell_settings_persistence.gd`, and `test_accessibility_runtime.gd` expectations |

Implementation ordering:

1. Add `establish_outer_view()`, its orientation-only snap/update, and the
   separate framing-only camera seams with snapshots that expose every affected
   property; delete zero-caller `frame_board()`.
2. Route mode entry and Reset View through canonical establishment plus fit.
3. Route Fit View through framing only.
4. Decouple live gameplay reset/new-game from presentation reset.
5. Make teardown/re-entry explicit for every mode.
6. Convert named presets to actions and remove obsolete selected identity.
7. Reconcile UI-scale reset ownership.
8. Update tests, help, RDS/architecture evidence, and real-window acceptance.

Forbidden adjacent work: the 3D arrow/control resolver defect, NEXT geometry,
slice spacing, grid/wireframe styling, 4D board-volume redesign, cockpit
consolidation, Hold, Explorer, topology, native gameplay, and replay/trace
schema changes.

## 12. Automated evidence required for E4b

Tests must capture complete presentation snapshots before and after each
operation, alongside deterministic state/hash evidence where applicable.

- **Outer-orientation seam:** call `establish_outer_view()` with arbitrary
  values that are not public action targets and with reflection both false and
  true; assert target and current yaw/pitch/roll plus reflection update
  immediately while projection, focus, fit reference, zoom, distance/size,
  identity-free diagnostics, `B`, `L`, layout, content, and preferences remain
  unchanged. Assert no production/test caller or definition of `frame_board()`
  remains.
- **Live-4D Reset View:** mutate `B`, `L`, layout-affecting transient state,
  pan, zoom, focus, and framing; invoke Reset View; assert the complete
  canonical presentation and unchanged gameplay snapshot/hash.
- **Fit View in every mode:** begin from noncanonical orientation and, in 4D,
  nonidentity `B`, nondefault `L`, and current layout; invoke Fit; assert all
  orientation/basis/layout/projection state unchanged, gameplay/replay content
  unchanged, and only required framing changed. On today's production path,
  assert orthographic projection remains orthographic and the Fit code performs
  no projection assignment; do not fabricate a supported perspective case.
- **Restart/new game:** mutate the current view, restart gameplay and start a
  new game within the same presentation context; assert gameplay reset/new-game
  semantics and exact view preservation.
- **Context re-entry:** mutate view, exit through setup/menu/mode change, and
  re-enter; assert fresh canonical view rather than the prior pose.
- **2D:** assert entry/reset yaw, pitch, roll, projection, reflection, and
  camera-space presentation are flat/front-on and simple.
- **3D:** assert Reset restores canonical 3D orientation and Fit preserves a
  manually changed orientation.
- **Replay:** assert Reset/Fit affect presentation only and preserve document,
  frame, events, and deterministic content.
- **Preset actions:** every action reaches its target; subsequent manual
  rotate/pan/zoom creates no required `Custom` or selected-preset identity.
  Assert current 3D/replay actions establish reflection false, Live-4D actions
  preserve the fixed outer reflection while changing only `L` orientation, and
  no status/HUD output derives a named current-view label.
- **Persistence:** application restart does not restore transient
  pan/zoom/yaw/pitch/roll/`B`/`L`/layout/fit state; persistent shell,
  accessibility, input, display, and replay-player preferences reload.
- **UI scale:** Display Reset preserves it; Accessibility Reset restores its
  default; Reset View, Fit View, and Restart Game preserve it.
- **Isolation:** no view operation changes setup identity, native snapshot,
  state hash, RNG identity, trace identity, or replay identity.

## 13. Focused E4b human-visible review

After automated evidence passes, record a real-window Godot 4.7.1 review with
environment and per-scenario evidence. Verify:

- 2D entry and Reset View are flat, front-on, and simple;
- Fit preserves current orientation/layout/basis while making content fit;
- Reset View restores the complete canonical view in 2D, 3D, 4D, and replay;
- Restart Game and same-context new game preserve the current view;
- setup/menu/mode exit followed by re-entry establishes a fresh canonical view;
- named presets behave as actions and no selector falsely claims a persistent
  identity after manual manipulation;
- UI-scale, Display Reset, and Accessibility Reset behave coherently; and
- 3D, 4D, and replay use their actual owners rather than simulated Live-4D
  state.

This is focused E4b acceptance, not the integrated Stage 54F human audit.
Visual plausibility does not replace deterministic-isolation tests.

## 14. Independent E4a review closure and handoff

The corrected design closes the independent review findings at contract level:

- UI scale has one accessibility owner and an exact operational reset target.
- Fit has a framing-only public path separate from canonical establishment.
- the contradictory continuous preset-identity model is removed rather than
  repaired;
- the lifecycle matrix covers 2D, 3D, 4D, replay, restart, same-context new
  game, setup/menu/mode exit, re-entry, and application restart;
- E4b is explicitly ineligible pending a green final confirmation review; and
- window mode/size plus replay speed/loop complete the mutable-presentation
  inventory.

The follow-up technical re-review findings are also closed at design level:
the real identity machinery is assigned to `camera_rig.gd`; nonexistent
`resolve_id()`/membership-tolerance removal work is eliminated; both Stage
54E-2c adapter halves have concrete dispositions; the eight-value runtime
inventory and replay pseudo-ID mislabel are explicit; canonical Live-4D
`L=(0.0,0.0)` is numeric; projection evidence matches the supported
orthographic path; and the complete `fit_bounds()` mutation/bookkeeping set is
routed with the identity retirement.

The final two blocking findings are closed at design level: arbitrary
canonical outer orientation/reflection now has the exact rig-owned
`establish_outer_view()` seam and composition order; zero-caller
`frame_board()` is deleted in E4b; both unknown-ID and known-ID false status
labels are retired; and action, canonical-reset, Live-4D `L`, reflection, and
framing routing are mutually consistent.

Final confirmation review must verify the transient/persistent split, composite
Reset View, Fit isolation, restart preservation, context re-entry, mode-specific
canonical views, flat 2D target, UI-scale ownership, projection conclusion,
removal of obsolete preset identity, E4b implementability, programme status,
and human-finding ownership. E4a must not self-certify REVIEWED GREEN.

Remaining human decisions: none. The accepted human semantics are not reopened
by this technical correction.

## 15. Scope exclusions

Stage 54E-4a implements no camera, settings, movement, NEXT, renderer, spacing,
grid, cockpit, Hold, topology, Explorer, campaign, physics, simulation, or
general GUI changes. Separate defects remain open when documented; recording
them is not a fix.
