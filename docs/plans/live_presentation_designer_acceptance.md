# Stage 54F-2 Live Presentation Designer Acceptance

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Date: 2026-08-27

Branch: `codex/canonical-local-board-geometry`

Starting HEAD: `32e9d2a9e8f431693761a25ba6cd9736419ab4bf`

## Outcome

The live Godot cockpit now contains a registry-driven Presentation Designer.
It exposes all and only the current runtime-applicable entries from the
existing 26-parameter registry: 16 in Live 2D, 18 in Live 3D, and 20 in Live
4D. Boolean, numeric, and enum rows use repository-standard controls; every
numeric row pairs a bounded slider with an exact bounded value entry using the
same registry minimum, maximum, and step. Groups follow registry order and the
existing `semantic_owner` values.

Opening the surface captures the current active runtime profile as an immutable
opening baseline and detached working B. Explicit `Capture B as A` creates a
second detached immutable snapshot. Edits, A/B selection, and resets emit a
detached profile through `ReplayHud.presentation_profile_changed` and the
existing `TraceReplayApp.apply_presentation_profile()` boundary. The Designer
has no settings store, save action, native session, renderer, camera, geometry,
NEXT, or HOLD write path.

Full mode is a bounded scrollable panel inside the game area. Compact mode is a
minimal strip with explicit textual `A shown` / `B shown`, A, B, `A ↔ B`,
Expand, and Hide controls. Hidden and compact modes preserve the session and
release gameplay keyboard ownership; the remaining GUI rect still blocks
pointer pass-through into camera handling.

## Declared Reset and Exit Semantics

| Action | Result |
| --- | --- |
| Parameter `Reset` | Restore the opening-baseline value for that parameter. |
| `Reset group` | Restore all currently applicable parameters of the existing semantic owner to their opening values. |
| `Reset B to Opened` | Restore the complete opening profile. |
| `Factory Defaults` | Replace B with detached registry defaults; do not save. |
| `Keep B & Hide` | Apply B for the current runtime and hide. |
| `Revert & Hide` | Restore the opening profile as B and hide. |
| Compact / ordinary Hide | Preserve opening, A, B, displayed slot, and game state. |

## Automated Acceptance Matrix

| Criterion | Result and evidence |
| --- | --- |
| Registry/UI correspondence | PASS — each live context is recomputed from `SettingSpec.applies_at_runtime()`; tests compare every applicable spec to exactly one entry, its control class, semantic owner/spec identity, numeric min/max/step, and enum value order. A test-only applicability mutation changes the generated surface without a Designer parameter-list edit. |
| Working-copy isolation | PASS — opening, A, and B snapshots are detached; later B edits leave A and the opening baseline byte-for-byte equal. Invalid or non-applicable edits are rejected. |
| Live apply | PASS — Board grid opacity, Piece opacity, Ghost opacity, HUD density, Environment intensity, and 4D Slice Set spacing reach their established consumers through the app entry point. |
| Persistence | PASS — complete `SettingsStore.deterministic_snapshot()`, including values and save count, remains equal across open/edit/A/B/reset operations. |
| Gameplay/state | PASS — canonical setup, live snapshot/hash, exact basis slots, active-slice local orientation, canonical renderer bounds, NEXT/HOLD semantic snapshots, and camera-pose fields remain equal across presentation operations. |
| A/B | PASS — Capture A, edit B, Show A, Show B, and compact toggle apply exact frozen values without reconstructing game state. |
| Resets | PASS — parameter, Ghost owner group, opening-profile, factory-default, and revert-and-hide semantics are independently asserted against a deliberately non-default opening profile. |
| NEXT/HOLD | PASS — HOLD exists under `AE-0055`; both panels remain visible and wholly inside the right-inspector viewport in full mode. Their identity/model/geometry/availability snapshots remain stable; purely visual style revision is permitted through the shared thumbnail style owner. |
| Helper/basis/status | PASS — right-inspector scrolling remains enabled and reachable. 4D basis text and the helper's Slice guidance remain present while the full Designer is open. |
| Input/focus | PASS — full mode owns live input and suppresses a real hard-drop action; compact mode releases it and the same action reaches native gameplay. A wheel event over the compact rect does not change camera state. Hidden/compact controls release focus. |
| Responsive layout | PASS — full and compact rects remain contained by the game area at the supported constrained and large test sizes; the Designer has an internal vertical scroll and does not displace the inspector. |

Focused suite:

```text
godot --headless --path godot/Tet4D.Godot \
  --script /private/tmp/run_presentation_designer.gd
```

Result: PASS.

The canonical `res://tests/run_tests.gd` suite includes
`test_presentation_designer.gd` and reports `Godot replay tests passed`.

## Agent-Driven Non-Headless Review

Environment:

- Godot `4.7.1.stable.official.a13da4feb`;
- macOS 26.6.2 build 25G83, arm64, Apple M1 Pro;
- macOS DisplayServer with Metal Forward+;
- production scene `res://scenes/trace_replay.tscn`;
- production native fixed-seed Live 2D, 3D, and 4D sessions;
- full logical window approximately 1600 x 960 (retina capture 3456 x 2073).

The run applied registry-default A, captured it, then edited B through the
actual Designer controls/application path with Vector Arcade palette, board
grid opacity `0.75`, boundary opacity `0.50`, active-piece opacity `0.65`,
Ghost opacity `1.25`, background intensity `0.65`, 4D slice spacing `1.35`, and
W labels enabled. It paused each live session before capture.

Captured evidence:

- `01_live_2d_full_b.png` — full B editor, readable planar board/active piece,
  helper, NEXT, HOLD, and score/status;
- `02_live_3d_full_b.png` — full B editor, readable volume/transparency,
  helper, NEXT, HOLD, and status;
- `03_live_4d_full_b.png` — full B editor, readable four-slice set, active
  slice, helper, NEXT, HOLD, and basis/slice panel;
- `04_live_4d_compact_b.png` — minimally obstructive B comparison strip;
- `05_live_4d_compact_a.png` — explicit `A shown` reference over the same
  frozen 4D game;
- `06_live_4d_compact_b_same_state.png` — explicit B over that same state.

All images are under
`docs/design/screenshots/live_presentation_designer/`.

The capture driver compared the 4D live snapshot/hash, basis slots, local
orientation/active slice, camera pose, NEXT signature, and HOLD signature
before and after A/B. It reported:

```text
isolation_ok=true
state_hash=daef26d673067f1cccf82085672ed1a0747e19bf0ba178ead3421bba2a0476c2
```

The compact evidence shows the board and all four slices unobstructed except
for the small top-left strip. NEXT and HOLD are simultaneously fully visible;
the onboarding helper is visible; the basis/slice panel is visible below them
and remains inspector-scrollable.

## Mode-Specific Visual Answers

### Live 2D

**Yes.** The Designer occupies a bounded left portion while most of the flat
board, the active cells, helper, score/status, NEXT, and HOLD remain visible.
The simple board remains readily judgeable and the form scrolls independently.

### Live 3D

**Yes.** The full panel leaves a large unobstructed volume view, making grid,
boundary, environment, and opacity changes directly comparable. NEXT, HOLD,
helper, and session status remain visible. After Compact/Hide, camera and
gameplay input recover.

### Live 4D

**Yes.** All four slices and the highlighted active slice remain readable
beside the full panel. NEXT and HOLD are simultaneously visible, the upper
helper remains visible, and basis/slice information is visible or immediately
reachable in the same inspector scroll. The compact strip restores essentially
the ordinary cockpit and supports fast same-state A/B comparison.

These answers are agent-driven visual inspection, not independent human
sign-off.

## Verification

Required final-tree verification:

```text
python3 -m json.tool config/project/policy_pack.json
python3 -m json.tool godot/Tet4D.Godot/config/shell_settings_registry.json
python3 tools/governance/check_godot_settings_externalization.py
pytest -q tests/unit/governance/test_check_godot_settings_externalization.py
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/generate_maintenance_docs.py --check
python3 tools/governance/generate_configuration_reference.py --check
python3 tools/governance/validate_godot_semantic_boundary.py
./scripts/check_git_sanitation_repo.sh
git diff --check
godot --headless --path godot/Tet4D.Godot --script res://tests/run_tests.gd
GODOT_BIN=godot ./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
```

Results: PASS. Expected negative-path settings/native validation messages and
existing non-failing headless resource-teardown advisories remain diagnostic
output, not test failures.

## Authority and Deferrals

Authority effect: none. The registry and `PresentationProfile` retain
presentation-parameter authority; `SettingsStore` remains the only preference
writer; Godot retains shell presentation/input/layout authority; native C++
retains gameplay, queue/RNG, NEXT source, and HOLD authority. Viewability is an
acceptance property, not a new gameplay-semantic owner.

Deferred: named profile save/load, profile library/import/export, undo/redo,
formal randomized A/B assignment, experiment telemetry/statistics/participants,
free-form palette or colour editing, new theme packs, procedural backgrounds,
major HUD redesign, topology/challenge/physics work, independent human
acceptance, and all changes to completed Stage 54G history.

---

# Stage 54F-2R Cockpit Density Review Correction

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

This bounded correction retains the Stage 54F-2 Designer architecture and
changes only live cockpit allocation, information hierarchy, shared preview
geometry, authority-derived piece guidance, and the established bounds-driven
Live-4D fit clearance.

## Root Cause and Measured Allocation

The undersized default 4D presentation had two causes. The live top action
stack consumed 96 logical pixels and the full-width stacked NEXT/HOLD cards
consumed 452 pixels before gaps, wasting vertical board and inspector space.
After that allocation cost, the existing 1.32 bounds-derived Live-4D fit
margin left excessive recovery clearance around a height-limited collection.
Layout was corrected first; framing was refined only afterward.

At the production 1600x960 logical canvas:

| Surface | Before | After |
| --- | ---: | ---: |
| top live actions | 96 px, two rows | 46 px, one row |
| body | 1576x789 | 1576x836 |
| gameplay viewport | 1250x714 | 1207x788 |
| gameplay viewport/body area | 71.8% | 72.2% |
| right inspector | 268x789 | 311x836 |
| NEXT + HOLD | two 260-wide cards, 452 px stacked height | one 180 px paired row |
| Live-4D projected collection | about 342x541 | about 415x657 |
| collection share of viewport | 27.3% x 75.8%, 20.7% area | 34.4% x 83.3%, 28.6% area |

The authoritative collection grows about 21% in each projected dimension and
about 46% in raw projected area. The normalized viewport share grows about
38%. The 47-pixel body-height recovery contributes a 10.4% height increase
before the fit change; reducing bounds-derived clearance from 1.32 to 1.20
contributes a further 10%. Allocation is therefore the first and slightly
larger dimensional contributor, not an offset or compensating camera hack.

The project intentionally scales one fixed 1600x960 logical canvas into
requested outer windows, so 960x720, 1440x900, and normal desktop inspection
share normalized layout. In the constrained production capture, the requested
960x720 outer window yields a 960x576 rendered canvas under the project's
aspect-preserving policy; the primary hierarchy remains intact.

## Implemented Hierarchy

- NEXT and HOLD use one `PiecePreviewLayout` compact convention and remain
  separate panels backed by the existing shared `PieceThumbnailModel` and
  `PieceThumbnail`. Labels, 3D/4D recognition, empty/availability text, native
  identities, and `AE-0055` Hold authority are preserved.
- `LivePieceControlStrip` is passive (`MOUSE_FILTER_IGNORE`) and has no gameplay
  buttons. It consumes `LiveInputContract.piece_control_groups()`; role
  metadata filters the existing movement/rotation groups without copying
  action IDs, bindings, applicability, control-frame labels, or plane maps.
- Live 2D shows X translation with `A/D` and arrow bindings plus CW/CCW with
  `Up/W/X` and `Z`. Live 3D shows X/Z translation with `A/D`, `W/S` and the
  XY/XZ/YZ planes with `R/T`, `F/G`, `V/B`. Live 4D shows X/Z/W translation
  with `A/D`, `W/S`, `Q/E` and XY/XZ/YZ/XW/YW/ZW with
  `R/T`, `F/G`, `V/B`, `Y/U`, `H/J`, `N/M`.
- Directional arrows and current signed-axis suffixes compact translation;
  plane names compact multidimensional rotation; short keycaps expose the
  authoritative bindings. Detailed prose remains in the generated helper.
- Fit View stays in the single promoted top action row. Named view actions,
  Reset View, pointer gestures, and optional numeric camera status move below
  piece guidance and the 4D basis. Camera capability is retained but its
  presentation priority is secondary.
- The permanent piece surface, NEXT/HOLD, and basis fit within the initial
  inspector fold at standard density. At larger UI scales, primary content
  wraps inside the inspector while secondary help scrolls.
- Full Designer retains a judgeable board plus visible NEXT, HOLD, and piece
  controls. Compact Designer remains a small board overlay and does not alter
  normal cockpit allocation.

## Deterministic and Authority Evidence

Focused layout tests compare the production scene rects, verify the projected
authoritative collection is contained, assert the compact preview row's
substantially reduced structure, and prove the piece strip is wholly inside
the inspector viewport before scrolling at supported density/scale cases.
Contract tests assert the exact 2D/3D/4D control groups and binding labels,
that camera guidance follows piece guidance, that the strip contains no
`BaseButton`, and that its source snapshot is `LiveInputContract`.

Existing Designer integration tests continue to cover Slider, SpinBox,
scroll, pointer-camera rejection, full-mode hard-drop suppression, and
compact/hidden release. Existing live-input and deterministic tests continue
to cover Hold, translation, rotation, camera orbit/pan/zoom, A/B isolation,
store/save-count isolation, snapshots/hashes, exact basis, canonical bounds,
NEXT/HOLD signatures, and current camera pose. No native or gameplay source is
changed by 54F-2R.

## Production Godot 4.7.1 Evidence

The production scene `res://scenes/trace_replay.tscn` was captured with Godot
`4.7.1.stable.official.a13da4feb` on the macOS DisplayServer using Metal
Forward+ on an Apple M1 Pro. Evidence is under
`docs/design/screenshots/cockpit_density_control_hierarchy/`:

- `01_live_2d_normal.png` — large planar board, paired previews, compact 2D
  translation/rotation strip, secondary View, and detailed helper;
- `02_live_3d_normal.png` — large volume, X/Z vocabulary and all three 3D
  rotation planes ahead of camera gestures;
- `03_live_4d_normal.png` — principal corrected 4D cockpit with materially
  larger slices, active/Ghost cues, compact previews, full 4D piece vocabulary,
  basis actions, and subordinate View;
- `04_live_4d_designer_full.png` — bounded tuning panel with board, NEXT, HOLD,
  and primary piece strip still visible;
- `05_live_4d_designer_compact.png` — near-normal cockpit with a small A/B
  strip and substantially unobstructed board;
- `06_live_4d_constrained_960x720.png` — requested constrained outer window,
  rendered as 960x576 by the fixed-aspect policy, with primary hierarchy
  preserved and secondary detail scrollable.

## Explicit Human-Visible Questions

1. **4D size — Yes.** The default board is immediately readable without
   manual zoom: individual cells, the active piece, Ghost, active-slice frame,
   signed W labels, and four-slice relationships are visible.
2. **NEXT/HOLD density — Yes.** They are compact glanceable indicators in one
   paired row rather than dominant stacked cards, while thumbnails and state
   labels remain recognizable.
3. **Piece controls — Yes.** A first-time player can see every applicable
   translation and piece-rotation plane plus its current binding before
   scrolling.
4. **Hierarchy — Yes.** The bordered PIECE CONTROLS surface precedes the basis
   and VIEW sections; camera gestures/named actions are lower and quieter while
   Fit remains promoted.
5. **Designer coexistence — Yes.** Full and compact Designer evidence retains
   a judgeable board, NEXT, HOLD, and the primary piece-control vocabulary.

These are agent-driven visual answers, not independent human acceptance.

## Verification

Final-tree results:

- focused cockpit/authority/layout test: PASS;
- canonical Godot suite: PASS (`Godot replay tests passed`);
- pinned Godot 4.7.1 gate: PASS (`Godot 4.7.1 verification passed`);
- topology transport parity: PASS (59 shared cases);
- governance, generated maintenance/configuration, semantic-boundary,
  sanitation, and diff checks: PASS through the full repository gate;
- `CODEX_MODE=1 ./scripts/verify.sh`: PASS (`verify: OK`).

Expected negative-path settings-write and invalid-native-setup messages, plus
the existing non-failing headless teardown/resource advisories, remain
diagnostic output rather than test failures.

Authority effect: none. Deferred scope remains named/persistent profiles,
import/export, themes, new parameters/actions, remapping, touch commands,
topology/challenge work, release hardening, and independent human acceptance.
