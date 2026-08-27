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
