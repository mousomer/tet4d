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

Availability (Stage 56H-R3.3): the Designer product
(`scenes/designer_bootstrap.tscn` and the project default scene) exposes the
live `Designer` entry. The game product (`scenes/game_bootstrap.tscn`) hides it
and refuses to open the Designer, along with the Design Laboratory menu card and
`L` shortcut.

## State and interaction map

| Object / action | State and interaction |
| --- | --- |
| BUILT-IN STYLE | Read-only appearance preset; never a save target. |
| CURRENT DESIGN | Exactly one editable detached profile: registry values, base-style provenance and cockpit panel rectangles. |
| SAVED DESIGN | Complete persisted current design, owned by PresentationProfileLibrary. |
| A/B COMPARISON | Two frozen snapshots and a shown side, separate from current design. Designer and Design Lab share the comparison-preview abstraction. |
| Save | Updates the associated saved design and complete working baseline. |
| Save As | Creates a fresh named design and association without changing the source artifact. |
| Load | `restore_design`: replaces current with the complete saved snapshot and establishes the baseline. |
| Revert | Restores the complete saved/opening working baseline. |
| Apply Style | Named appearance composition; preserves grid, geometry and independent parameters, records base style; preserves saved-design association. |
| Set A / Set B | Copies current (or a selected saved design) into the indicated comparison snapshot. |
| Toggle A/B | One HUD activation outside Designer switches frozen preview only; visible text names the side. |
| Adopt A/B as Current | Explicitly copies the candidate into current; baseline and save association remain. |

Implementation migration: `_working_profile` is current design (the internal
name remains for API compatibility), never comparison B. `show_slot` restores
the frozen candidate exactly instead of composing its style onto current.
`load_saved_profile` restores the saved snapshot instead of `with_style_of`.
`_set_applied_style` records provenance without clearing saved association or
replacing the design baseline. `capture_reference` delegates to Set A; B needs
explicit capture too. “Apply to B”, “Show A/B” as primary editing actions and
“Keep B” wording are retired. Design Lab's evidence session retains its frozen
scenario/fingerprint guard and uses the same comparison-preview owner.

Registered parameter controls use the bounded app application seam. Existing
cockpit handles remain the only panel movement/resizing implementation; profile
metadata captures/restores their rectangles through that owner. Complete design
restoration and comparison preview explicitly request geometry restoration;
ordinary value/style previews preserve it at the app boundary. Geometry changes
use the existing resolved-region fit lifecycle.
No operation writes ordinary settings or changes deterministic gameplay truth.

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

## Baselines and comparison

Parameter/group Reset uses the complete saved/opening working baseline.
Revert restores that baseline including grid, appearance, density, base-style
provenance and panel geometry. Save, Save As and Load establish a new baseline;
style application and comparison adoption do not. Internally `revert_style`
reapplies the recorded base-style appearance while preserving independent state;
the UI exposes one Revert command to avoid duplicate reset concepts.

Edits always update CURRENT DESIGN and return preview to current. Previewing A
or B never changes current or the save association. Set A/B copies complete
snapshots; later edits cannot mutate them. Adoption is explicit. Hide, Compact
and reopen preserve current and comparison state. The external HUD A/B control
is available once both snapshots exist, even with Designer hidden. Lab comparison
switching retains the deterministic fingerprint guard. Laboratory Apply Live
composes built-in appearance but fully restores a user design.

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

The Designer is a bounded panel inside the existing game-area rect, or the
cockpit surface while full Designer panel manipulation is active. Full mode uses an internal scroll container and
occupies less than a majority of ordinary board width. Compact mode becomes a
small A/B strip. Hidden mode removes the overlay while retaining the detached
session.

The board and active/Ghost pieces remain visible beside/behind the bounded
panel. NEXT and HOLD remain together in their shared module; full Designer mode
places cockpit modules in bounded scrollable frames. The 4D basis/slice indicator
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
Compact Designer mode restores the ordinary responsive cockpit. These layout
rules do not change detached current/comparison state, application, focus, persistence, or
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

## Stage 56H panel geometry and grid independence

Full Designer mode enables labelled Move and Resize handles for the board,
piece controls, view controls, and NEXT/HOLD panels. The cockpit owns detached
panel rectangles; scroll containers preserve access to controls at their minimum
sizes (300×160 logical pixels for control panels, 320×360 for the board,
including handles and board chrome; constrained by the available surface). Rectangles are constrained to the available cockpit surface, including
after window changes. The panel selector and Bring Panel Forward action recover
any overlapping panel without changing its geometry, profile, or gameplay. Compact/hidden Designer and ordinary gameplay restore the
responsive cockpit and disable all manipulation. Session rectangles survive reopening Designer and are persisted in the optional
design-state extension of the profile snapshot. Older profiles without the
extension restore default cockpit geometry.

The board panel contains the real SubViewportContainer. Moving/resizing panels
never calls Fit directly: resolved inner visibility/size signals use the same
app refit path as mode entry and window resizing. Layout geometry is independent
of profiles, style, grid mode, exact basis, view orientation, density, and native
gameplay state. Geometry edits never apply profiles or dispatch native commands.

Grid is a session presentation enum (`full`, `border`, `none`), cycling in that
order. Its cumulative roles follow the
[spatial scaffold contract](presentation_parameter_contract.md#spatial-scaffold-semantics-stage-56h):
NONE retains enclosure shading and the floor, with no lattice lines; BORDER
adds the outer box edges and boundary-face lines on camera-relative rear faces;
FULL adds the interior lines and shows all boundary faces, yielding the complete
board lattice. Lines span whole board axes rather than individual cell edges.
The 2D slab and each 3D/4D slice share this generator and topology rule. Styles
affect appearance, not topology. Pieces, Ghost and orientation labels retain
their existing roles.
Grid cycling changes only `display.grid_mode` on CURRENT DESIGN and returns
preview to current. Style composition preserves grid; loading, reverting and
previewing complete designs restores their saved grid. FULL/BORDER/NONE renderer
semantics and all-style × all-grid × dimensional renderer coverage are retained.


The three scaffold opacity controls appear only under Designer → Advanced
Settings, collapsed on opening. Registry UI context `designer_advanced` routes
Enclosure opacity, Border/surface grid opacity, and Full/internal scaffold
opacity while their semantic owner remains BOARD_PRESENTATION. Stored IDs and
values remain compatible; `board.cell_volume_opacity` is the legacy internal
edge opacity key. Named Save/Load includes all three. Each slider edits its
role material only, preserving grid, style, gameplay and panel geometry.
Border is the fresh-session grid default; complete saved designs retain grid.
