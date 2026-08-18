# Camera and GUI Preset Semantics

Role: architecture
Status: human view semantics accepted; contract corrected; ready for independent technical re-review
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
eligible until a fresh independent technical review accepts this corrected
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

- `CameraRig.fit_bounds()` currently writes projection, focus, yaw, pitch,
  roll, reflection, base distance, zoom, and orthographic size. It therefore
  establishes a canonical orientation as well as fitting; it is not yet the
  framing-only Fit View required by this contract.
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
- `_current_view_preset`, `_mark_custom_view()`, and selector synchronization
  maintain a selected preset identity that can disagree with rendered state.
  That product model is retired below.
- `display.ui_scale` is declared under the registry's `display` category;
  `reset_display_settings_to_defaults()` therefore resets it, while
  `reset_accessibility_settings_to_defaults()` does not. The target ownership
  is the reverse.
- No player-facing orthographic/perspective setting exists. Every fitted view
  forces orthographic projection. `display.projection_strength` changes
  rendered cell/particle/event emphasis and is not a camera-projection choice.

These are E4b or explicitly bounded settings corrections. No runtime
correction belongs to E4a.

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

E4b must provide two separate internal operations:

```text
fit_current_view()                 # framing only; public Fit View path
establish_canonical_view_and_fit() # owner resets followed by framing; entry/Reset View path
```

The names are illustrative, but the separation is normative. The existing
`fit_bounds()` path cannot serve both contracts while it also writes
yaw/pitch/roll, reflection, and projection.

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

- `_current_view_preset` must not remain product state;
- `_mark_custom_view()` and selector synchronization based on a tracked flag
  are retired;
- no `resolve_id()` architecture is required merely to derive a selection;
- pan/zoom never decide named-preset membership;
- target-versus-rendered equality and the former `0.001`-radian identity
  tolerance are not load-bearing product requirements; and
- generic angular comparison helpers may remain if another real operation
  needs them, but E4b must not add or retain them solely for preset identity.

No audited product operation currently needs angular target comparison after
continuous preset identity is removed. Preset application may assert that a
target was reached using ordinary test tolerances; that is conformance
evidence, not persistent product identity.

The six current public IDs and labels remain compatibility actions with their
existing targets. In Live 4D, yaw/pitch target `L`; in Live 3D and replay they
target the legitimate outer orientation owner. They are not exposed in Live
2D. Every action preserves `B` and layout, sets zero roll where the mode owns
roll, and restores the fitted framing baseline as accepted on 2026-08-17.

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
and fitted framing. The current accepted mount is yaw
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

| Component | Required change |
| --- | --- |
| `scripts/app/trace_replay_app.gd` | add mode-aware Reset View orchestration; route public Fit View to framing-only fit; preserve view across live reset and same-context new-game paths; establish canonical view only on entry, Reset View, context re-entry, and application initialization; keep setup/menu/mode transitions as teardown |
| `scripts/rendering/camera_rig.gd` | split framing calculation/application from canonical yaw/pitch/roll/projection/reflection establishment; expose owner-specific canonical reset and framing-only fit seams; preserve sensitivity, invert-Y, and reduced-motion policy |
| `scripts/presentation/camera_preset.gd` | retain useful named targets as action definitions; remove product-state `custom`, per-preset identity machinery, and vacuous identity tolerance/`resolve_id()` work; keep generic numeric helpers only if a demonstrated consumer remains |
| `scripts/ui/replay_hud.gd` and preset selector | present named views as actions without a misleading persistent selection; keep the control absent in 2D; expose one Reset View and one Fit View |
| Live input/help contracts | use View terminology and preserve one Reset View / one Fit View surface; do not add reset families |
| Live 2D camera path | establish explicit flat/front-on orthographic canonical view; Fit preserves it and changes framing only |
| Live 3D camera path | canonical reset uses the legitimate 3D rig orientation; Fit preserves current orientation |
| Live 4D presentation owners | Reset composes basis, local orientation, layout, outer-view, projection, and framing owners; Fit preserves all but framing |
| replay path | canonical replay reset and framing-only fit preserve deterministic replay document/content |
| `config/shell_settings_registry.json`, `scripts/ui/settings_panel.gd`, settings tests | make UI scale accessibility-owned operationally: Display Reset preserves it and Accessibility Reset restores it |

Implementation ordering:

1. Add separate canonical-establishment and framing-only camera seams with
   snapshots that expose every affected property.
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

- **Live-4D Reset View:** mutate `B`, `L`, layout-affecting transient state,
  pan, zoom, focus, and framing; invoke Reset View; assert the complete
  canonical presentation and unchanged gameplay snapshot/hash.
- **Fit View in every mode:** begin from noncanonical orientation and, in 4D,
  nonidentity `B`, nondefault `L`, and current layout; invoke Fit; assert all
  orientation/basis/layout/projection state unchanged, gameplay/replay content
  unchanged, and only required framing changed.
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
- E4b is explicitly ineligible pending a green independent re-review; and
- window mode/size plus replay speed/loop complete the mutable-presentation
  inventory.

Fresh independent review must verify the transient/persistent split, composite
Reset View, Fit isolation, restart preservation, context re-entry, mode-specific
canonical views, flat 2D target, UI-scale ownership, projection conclusion,
removal of obsolete preset identity, E4b implementability, programme status,
and human-finding ownership. E4a must not self-certify REVIEWED GREEN.

## 15. Scope exclusions

Stage 54E-4a implements no camera, settings, movement, NEXT, renderer, spacing,
grid, cockpit, Hold, topology, Explorer, campaign, physics, simulation, or
general GUI changes. Separate defects remain open when documented; recording
them is not a fix.
