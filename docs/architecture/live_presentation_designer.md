# Live Presentation Designer Contract

Status: active Godot product-shell contract

Stage: 54F-2, extended by the Stage 54F-4 built-in style catalog surface

## Purpose

The Live Presentation Designer is a developer/designer instrument for changing
registered presentation values against one running deterministic live game. It
exists to shorten visual iteration without restarting a session, editing source
constants, or contaminating player settings. It is not a profile-library
storage owner, gameplay editor, scene editor, or new presentation-semantics
owner. Stage 54F-3 integrates the separate library owner through the bounded
surface and lifecycle defined by `presentation_profile_library.md`.

The production flow is:

```text
registry metadata
    -> generated Designer control
    -> detached working PresentationProfile B
    -> ReplayHud presentation_profile_changed
    -> TraceReplayApp.apply_presentation_profile
    -> existing presentation consumers
```

No control may bypass the bounded application seam to write a renderer,
material, camera, HUD node, geometry object, native session, or settings store.

## Profile identities

The following objects are distinct:

- **factory defaults** are declared by the checked-in registry;
- **persisted player preferences** are owned and written only by
  `SettingsStore`;
- **active runtime profile** is the detached profile currently applied by
  `TraceReplayApp` and retained by `ReplayHud`;
- **opening baseline** is an immutable detached copy of that active profile at
  the start of a Designer session;
- **working B** begins as a detached copy of the opening baseline and is
  replaced by validated `PresentationProfile.with_overrides()` results;
- **reference A** is created only by explicit `Capture B as A` and remains
  detached from later B edits.
- **named library profile** is an independently stored artifact owned by
  `PresentationProfileLibrary`; load copies it into B and explicit Save copies B
  back across the persistence boundary.
- **built-in style** is a read-only shipped artifact owned by
  `BuiltInStyleCatalog`; applying one copies detached values into B and can
  never be a save target.

Object aliasing between A, B, the opening baseline, active runtime state, and
the settings store is forbidden. The Designer is intentionally not given a
store or persistence callback. Applying A or B changes the current runtime
presentation only.

## Registry generation and applicability

`shell_settings_registry.json` is the sole parameter inventory. The Designer
iterates registry order, filters with `SettingSpec.applies_at_runtime()` for
the current `live_2d`, `live_3d`, or `live_4d` context, and groups the remaining
entries by the existing `semantic_owner` field. It does not use `ui_visible` as
an exclusion because this is the explicit designer surface; runtime
applicability remains the safety boundary.

Current applicable types map as follows:

| Registry type | Designer editor |
| --- | --- |
| `bool` | `CheckBox` |
| `int` / `float` | bounded `HSlider` plus exact bounded `SpinBox` |
| `enum` | `OptionButton` generated from registry options |

Minimum, maximum, step, default, option value, label, description, and owner
all come from the same spec. Stage 54F-2 adds no colour parameter or
speculative editor type. A future registered type requires a bounded contract
and factory extension rather than a parameter-specific row.

Non-applicable controls are hidden consistently. In the current registry that
yields 19 controls in Live 2D, 21 in Live 3D, and 23 in Live 4D. Shell window
transitions, replay playback/loop/projection, and shell/replay-only layout
diagnostics do not appear in the live Designer. Stage 54F-4's three
`ENVIRONMENT_PRESENTATION` background-animation parameters are ordinary
registry-generated rows; they required no new control type.

## A/B and reset semantics

The displayed profile is always announced textually as `A` or `B`; colour is
not the only indication. Full and compact surfaces both select A and B, and the
compact strip provides an explicit `A ↔ B` action. Switching slots applies a
detached copy through the same app boundary and does not rebuild the game.

Reset wording and behavior are normative:

- parameter `Reset` restores that parameter's opening-baseline value;
- `Reset group` restores every currently applicable parameter owned by that
  semantic owner to its opening-baseline value;
- `Reset B to Opened` restores the complete opening baseline;
- `Factory Defaults` replaces B with a detached registry-default profile;
- `Revert & Hide` restores the opening profile, makes it B, and hides;
- `Keep B & Hide` explicitly reapplies B and hides;
- ordinary Hide or Compact preserves A, B, and the currently displayed slot.

Named profile storage/versioning/import/export remain outside this Designer
contract and are owned by `presentation_profile_library.md`. Read-only shipped
styles are owned by `built_in_style_catalog.md`. The integrated UI may invoke
either owner, but ordinary edits, reset actions, A/B switching,
`Keep B & Hide`, collapse, and hide retain the runtime-only behavior above.

Applying a built-in style behaves exactly like any other detached B replacement:
it displays B, leaves captured A untouched, and performs no write. It also
clears the loaded user-profile identity, so explicit `Save Profile` is disabled
and the shipped style cannot be overwritten. The Designer hosts two collapsed-by-
default disclosure sections, `BUILT-IN STYLES` and `PROFILE LIBRARY`, which are
mutually exclusive so their combined minimum content cannot exceed the allocated
overlay. Expanding either consumes internal Designer space only.

Undo history, randomized assignment, telemetry, and statistical experimentation
remain outside all three contracts.

## Presentation and deterministic isolation

The existing bounded app apply method may refresh shell theme/layout, HUD,
renderer materials/visibility, environment, slice-set presentation, and camera
preferences according to the registry. It may not mutate canonical setup,
board state, pieces, locked cells, Ghost landing truth, NEXT identity, HOLD
identity/availability, score, queue/RNG, replay identity, exact `BasisState`,
active slice, canonical local-board geometry, or current interactive camera
pose. A preference such as sensitivity or inversion changes future camera
response, not the current pose.

Presentation profile application can increment purely visual style revisions
of the shared NEXT/HOLD thumbnail component. It must preserve the thumbnail
model, authoritative identity, availability, geometry signature, and shared
palette architecture.

## Cockpit viewability

The Designer is a bounded panel inside the existing game-area rect, never a
fixed opaque centre overlay. Full mode uses an internal scroll container and
occupies less than a majority of ordinary board width. Compact mode becomes a
small A/B strip. Hidden mode removes the overlay while retaining the detached
session.

The board and active/Ghost pieces remain visible beside/behind the bounded
panel. The existing right inspector is not displaced, so NEXT and HOLD remain
simultaneously visible at supported layouts. The 4D basis/slice indicator
remains visible, and helper/status content remains visible or immediately
reachable through the established inspector scroll container. Designer rows
also scroll, so constrained windows and enlarged UI scale do not make bottom
controls unreachable.

NEXT/HOLD/helper viewability is an acceptance property of this presentation
surface. It creates no new gameplay-semantic owner, visibility preference, or
parallel thumbnail/palette implementation. HOLD exists in the accepted stack
as native authority `AE-0055`; Godot continues to render it through the shared
NEXT thumbnail model and renderer.

Stage 54F-2R clarifies the priority within that coexistence contract. The full
Designer must preserve the board, active/Ghost pieces, compact NEXT/HOLD row,
and the permanent authority-derived piece-control strip. Camera guidance and
detailed helper prose are secondary and may require inspector scrolling.
Compact Designer mode does not reallocate the ordinary cockpit. These layout
rules do not change detached A/B state, application, focus, persistence, or
input-isolation semantics.

## Input and focus isolation

Opening full mode focuses a visible Designer action and causes
`ReplayHud.live_interaction_owns_input()` to suppress live gameplay keyboard,
held-repeat, hard-drop, Hold, and camera actions. All parameter controls remain
reachable through ordinary Godot focus traversal.

Compact and hidden states release Designer focus and global gameplay-key
ownership. The compact panel remains a GUI pointer hit target; the app rejects
mouse camera handling for events inside its rect before GUI dispatch, so A/B
buttons, slider drag, exact entry, and Designer scrolling do not orbit, pan, or
zoom the game behind it. Once compact/hidden or pointer interaction is outside
the strip, ordinary gameplay and camera controls resume.

## Product boundary and authority effect

The accepted shell has development/diagnostic routes but no single runtime
feature-flag or capability gate suitable for live cockpit tools. Stage 54F-2
therefore exposes a plainly labelled `Designer` action only in the existing
live View/Display action family. It is absent from replay and non-viewer
screens, uses production rendering/application paths, and is described as a
detached non-saving developer/designer capability. No hidden key, new config
mechanism, or insecure gate is introduced.

This contract formalizes orchestration within existing Godot presentation
authority. It transfers or establishes no gameplay, native, replay, profile,
registry, NEXT, HOLD, geometry, basis, camera, or persistence authority.
