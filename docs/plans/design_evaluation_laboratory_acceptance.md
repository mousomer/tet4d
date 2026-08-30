# Design Evaluation Laboratory Acceptance

Status: AUTOMATED LOCAL ACCEPTANCE GREEN / HUMAN DESIGN ACCEPTANCE PENDING ON ALL THREE PLATFORMS

Date: 2026-08-30

Authority: maintenance acceptance record for Stage 54F-5. The durable behavior
and promotion boundary are owned by
`docs/architecture/design_evaluation_laboratory.md`.

The Design Laboratory now targets three distribution platforms. Windows is the
reference platform; Android tablet and iPadOS are adapters over the identical
Design Laboratory. Nothing about a design means anything different on one
platform than another, so this record splits by *evidence*, not by behaviour.

## Platform evidence matrix

Nothing below is marked from expectation. Every filled cell names evidence that
was actually produced, and every unfilled cell is a real gap.

| Capability | Windows | Android tablet | iPad |
| --- | --- | --- | --- |
| Launch | not run (no Windows host) | not run (no APK) | not run (no Xcode/device) |
| Keyboard gameplay | automated InputMap tests | automated InputMap tests | automated InputMap tests |
| 4D/W controls | automated InputMap tests | automated InputMap tests | automated InputMap tests |
| Designer navigation | automated runtime tests | automated runtime tests | automated runtime tests |
| A/B toggle | automated runtime tests | automated runtime tests | automated runtime tests |
| Input isolation | automated runtime tests | automated runtime tests | automated runtime tests |
| Save candidate | automated runtime tests | automated runtime tests | automated runtime tests |
| Evaluation persistence | automated runtime tests | automated runtime tests | automated runtime tests |
| Screenshot pair | automated runtime tests | automated runtime tests | automated runtime tests |
| Nomination | automated + repository validator | automated + repository validator | automated + repository validator |
| External export/share | implemented; not exercised on device | implemented; not exercised on device | implemented; not exercised on device |
| Background/resume | N/A (desktop) | not run (no device/emulator) | not run (no simulator/device) |
| Physical keyboard tested | no | no | no |
| Artifact builds | yes (portable ZIP) | no (needs JDK/SDK/NDK) | configuration export only (no iPhoneOS SDK) |

The automated rows are platform independent by construction and are asserted as
such: `tests/test_cross_platform_design_boundary.gd` exports the same candidate
under Windows, Android, and iPadOS provenance and requires the preset identity,
properties, semantic owners, and snapshot hash to be identical.

## Implementation-host evidence boundary

These gaps are properties of the host this work was done on, not of the
implementation. Each is a toolchain or hardware absence, not an unfinished
feature.

- **Windows execution.** The macOS host builds and validates the Windows PE
  artifact and its resource closure. It cannot execute it. The `package-windows`
  CI job launches the packaged runtime headlessly.
- **Android APK.** Godot 4.7.2 requires a Java SDK and an Android SDK with
  `platform-tools` and `build-tools` unconditionally in `can_export()`; setting
  `package/signed=false` does not bypass it, which was verified directly. The
  arm64 GDExtension additionally needs the NDK. None are installed on this host
  and installing them was declined. The `package-android` CI job runs on
  `ubuntu-latest`, which has all three.
- **iPadOS build.** This host has Command Line Tools but not Xcode, so there is
  no iPhoneOS SDK for `xcodebuild` or for the iOS GDExtension. The Xcode project
  itself exports and validates locally. The `package-ipados` CI job runs on
  `macos-latest`, which has full Xcode, and compiles the exported project
  unsigned for the simulator.
- **Devices.** No Android tablet, emulator, `adb`, iPad, iOS Simulator, or
  external physical keyboard was available. No claim of emulator, simulator, or
  physical-keyboard acceptance is made anywhere in this record.

## Artifacts produced on the implementation host

SHA-256, `Tet4D 0.7.5`, pinned Godot `4.7.2.stable.official.ed1daf0bf`. The
export templates were verified against the SHA-512 recorded in
`config/project/policy_pack.json` before use.

| Artifact | SHA-256 |
| --- | --- |
| Windows exact generated ZIP (timestamp-bearing) — `artifacts/godot/windows/Tet4D-Designer-0.7.5-windows-x86_64.zip` | `04941cb3f6d1070521f7a4d2d306fee5478908e3cf5e51d782c96a7e973913b9` |
| Android configuration resource pack — `artifacts/godot/android/Tet4D-Designer-0.7.5-android-arm64.pck` | `a17dedd6689d931175dc7de633cbea60d498fd0b2f8a8c1418692bb0c0fa7b00` |
| iPad configuration PCK (reduced 1,298-byte descriptor) — `artifacts/godot/ipad/configuration-export/Tet4DDesigner.pck` | `6e0f54e4f44e3c66a77e273973f9519646a420078f497a329521d9c91a25b3f8` |
| iPad configuration Xcode project — `artifacts/godot/ipad/configuration-export/Tet4DDesigner.xcodeproj/project.pbxproj` | `39198a7c473cbcf053e833af296d7ff879b26ed2b075b78a549b3bef30667858` |
| iPad configuration Info.plist — `artifacts/godot/ipad/configuration-export/Tet4DDesigner/Tet4DDesigner-Info.plist` | `57fa06c3adf2e9ff6e73e0f53e87c97d33824c8b2dda02ad0157655fee349b80` |
| iPad configuration export_options.plist (`method=development`) | `2501952ce0655af361ad718ecf01d24fe77c25a5982fb086665f0fd0c86cbb24` |
| iPad configuration export aggregate (47 files; relative paths and file hashes, path-ordered) | `65cee1069d404d470dafd87858e329faed7862cc1a1e826042287c2855d01089` |

The Android entry is the resource pack, not an APK. Its staged release-signing
configuration is fixed, but no APK was produced on this host. The iPad entries
are explicitly the **configuration export**, not a compiled, signed, or release
application. The earlier record put checksum
`6e0f54e4f44e3c66a77e273973f9519646a420078f497a329521d9c91a25b3f8`
under a generic iPad path even though its descriptor was 1,298 bytes and omitted
the `ios.*` declarations. That checksum is retained and corrected here as
configuration-only evidence; it is not silently replaced or promoted to the
1,476-byte full release descriptor. No iPad release checksum exists until an
equipped build produces the complete descriptor and matching release
xcframework.

The Windows ZIP checksum identifies the exact valid generated release artifact.
Because ZIP timestamps/mtimes are not normalized, it is not a claim that a
second build is bit-for-bit reproducible; the shared PCK equivalence evidence is
separate. The configuration Xcode project also contains two inert visionOS
camera-placeholder xcframework directories emitted by Godot 4.7.2. They are
recorded inventory, not an additional target, and are not custom-filtered.

## Automated acceptance scope

Automation must be green before a person records design judgments. The accepted
matrix covers:

- the six immutable built-in styles and detached mutable user candidates;
- all ten shipped scenarios, including 2D/3D/4D, sparse/dense,
  NEXT/HOLD/Ghost, and sphere-like topology presentation;
- repeat load after camera/basis disturbance and the full preset-by-scenario
  apply/render/reset matrix;
- exact A/B snapshots, `A -> B -> A`, repeated switching, deterministic blind
  labels, and fail-closed non-style drift detection;
- replacement-safe profile and evaluation persistence, immutable historical
  preset snapshots/hashes, PNG/metadata capture, nomination, all three export
  outputs, and repository-side owner/value validation; and
- an x86_64 Windows portable ZIP containing the current Godot executable, PCK,
  release GDExtension, icon, catalog, scenarios, and replay resources without a
  Python/editor/checkout dependency.

Local macOS evidence proves the actual Windows PE artifact structure and resource
closure, not Windows execution. The Windows workflow is configured to run the
focused laboratory suite, build/validate the package, and launch the packaged
runtime. It has not run until the commits reach a Windows runner.

## Windows artifact acceptance boundary

The distributable is `Tet4D-Designer-0.7.5-windows-x86_64.zip`. Extracting it is
the install-equivalent operation. Run `Tet4D Designer/Tet4DDesigner.exe`; delete
the extracted directory to uninstall. The portable distribution intentionally
does not register a Start Menu entry, desktop shortcut, or Windows uninstall
record. Mutable profiles, evaluations, captures, and exports live under Godot's
per-user application-data root, never beside the executable.

Direct clean-machine Windows execution is not executable on the macOS
implementation host. Do not describe that step as passed until a Windows
reviewer executes the checklist below.

## Human evaluation checklist

Start only from a green automated build. The checklist below is the shared
evaluation workflow and is identical on every platform; the per-platform
sections that follow add only what differs.

### Launch and catalogue

- [ ] Extract the ZIP outside a repository checkout and launch
  `Tet4DDesigner.exe` without Python or a Godot editor installed.
- [ ] From the main menu choose **Design Laboratory**.
- [ ] Confirm all built-in presets show understandable names, descriptions,
  stable IDs, provenance/category, candidate status, and read-only identity.
- [ ] Apply and inspect each built-in; confirm the intended styles are visually
  distinct.
- [ ] Duplicate a built-in as a user candidate, edit it in the existing
  Presentation Designer, save it, close/relaunch, and confirm it reloads.

### Representative 2D / 3D / 4D review

- [ ] Review sparse and dense 2D scenarios for board scale, silhouette,
  readability, active/Ghost separation, and NEXT/HOLD balance.
- [ ] Review sparse and dense 3D scenarios for depth, occlusion, spatial
  comprehension, piece visibility, and hierarchy.
- [ ] Review sparse, dense, and sphere-like 4D scenarios for slice hierarchy,
  local depth, labels, and topology-oriented comprehension.
- [ ] Confirm piece controls stay prominent, camera/presentation controls remain
  secondary, and the 4D board retains enough viewport space.

### A/B and blind mode

- [ ] Select a scenario and two presets, then start comparison.
- [ ] Exercise **A**, **B**, **Toggle**, and **Reset scenario** repeatedly.
- [ ] Confirm switching is immediate, the gameplay state never jumps, and reset
  returns to the same board/piece/queue/HOLD/Ghost/camera/basis state.
- [ ] Enable blind mode and confirm judgment labels hide preset names while
  retaining enough orientation to choose an arm.

### Evaluation and screenshots

- [ ] Record Prefer A, Prefer B, and No preference in separate trials.
- [ ] Enter all eight optional 1–5 ratings plus free-text notes; save and reload.
- [ ] Capture A, B, and a pair; confirm `A.png`, `B.png`, and `metadata.json`
  contain the expected scenario/build/arm provenance and no names overlaid on
  blind images.

### Nomination and repository portability

- [ ] Nominate a user candidate and note the displayed absolute export path.
- [ ] Confirm `preset.json` matches the visible candidate's exact values,
  `comparison_summary.json` contains only real matching evaluations, and
  `DESIGN_PROPOSAL.md` is understandable review input.
- [ ] Copy the bundle to a source checkout and run
  `python3 tools/design_lab/validate_design_export.py <bundle-directory>`.
- [ ] Confirm validation does not alter the built-in catalog, production
  defaults, or authority documents.

### Clean exit / relaunch / removal

- [ ] Close and relaunch; confirm the user candidate and evaluations persist.
- [ ] Delete the extracted application directory and confirm no installed
  application files remain. Retain or remove per-user evidence separately as
  the reviewer intends.

## Android tablet acceptance

Configuration: a landscape Android tablet with a physical Bluetooth or USB
keyboard, optionally a mouse or trackpad. Touch is supplementary; the entire
evaluation workflow must be operable from the keyboard.

Requires `Tet4D-Designer-<version>-android-arm64.apk`, which this host cannot
build. Do not begin until that artifact exists.

- [ ] `adb install` the APK on a landscape tablet, launch it, and confirm no
  Python and no Godot editor are present on the device.
- [ ] Confirm the application opens landscape and stays landscape when the
  tablet is rotated 180 degrees.
- [ ] With the external keyboard only, exercise piece translation, every
  rotation plane, both W-axis directions, soft drop, hard drop, and hold.
- [ ] Confirm Ctrl soft drop works and that Shift+Ctrl does not trigger it.
- [ ] Open and close the Design Laboratory from the keyboard; navigate presets,
  select A and B, toggle, and reset.
- [ ] Focus the evaluation notes field and confirm typing never moves a piece.
- [ ] With the Design Laboratory visible, confirm gameplay controls are not
  consumed by the board.
- [ ] Press the system Back gesture in each of: gameplay, open Design
  Laboratory, main menu. Confirm it never terminates the application and never
  changes which arm is active or discards an in-flight comparison.
- [ ] Confirm the board keeps primary space, the 4D board stays usefully large,
  NEXT/HOLD stay compact, and piece controls stay prominent.
- [ ] Save a candidate, record an evaluation, capture a screenshot pair, and
  nominate.
- [ ] Use **Share exported bundle** and confirm the Android document picker
  appears and writes the archive somewhere reachable outside the application.
- [ ] Background the application, resume it, then force-stop and relaunch.
  Confirm built-ins, candidates, evaluations, and A/B identity are unchanged.
- [ ] Disconnect and reconnect the keyboard mid-session; confirm control
  resumes without restarting.
- [ ] Uninstall and confirm no application files remain.

## iPadOS acceptance

Configuration: an iPad in landscape with a Magic Keyboard, Bluetooth, or USB
keyboard, optionally a trackpad. Touch and trackpad are supplementary.

Requires a build installed from the exported Xcode project. Signing needs a real
Apple Developer team identifier; set `TET4D_IOS_TEAM_ID` before exporting and
configure a provisioning profile in Xcode. The exported project targets iPad
only and requires an A12 device or newer, which is an engine-level requirement
of the Godot 4.7 mobile renderer, not a project choice.

- [ ] Build, sign, and install onto a physical iPad from Xcode.
- [ ] Confirm the application opens landscape and honours both landscape
  orientations.
- [ ] Confirm the cockpit respects the safe area: nothing important sits under
  the camera housing, rounded corners, or home indicator.
- [ ] With the external keyboard only, exercise piece translation, every
  rotation plane, both W-axis directions, soft drop, hard drop, and hold.
- [ ] Confirm Ctrl soft drop works and that Shift+Ctrl does not trigger it.
- [ ] Confirm Escape cancels and closes as it does on desktop.
- [ ] Open the Design Laboratory, navigate presets, select A and B, toggle, and
  reset from the keyboard.
- [ ] Focus the evaluation notes field and confirm typing never moves a piece.
- [ ] Save a candidate, record an evaluation, capture a screenshot pair, and
  nominate.
- [ ] Open the Files app, find the **Tet4D Designer** folder under *On My iPad*,
  and confirm the nominated archive is there and can be shared out of the
  device.
- [ ] Background the application, resume it, then terminate and relaunch.
  Confirm built-ins, candidates, evaluations, and A/B identity are unchanged.
- [ ] Disconnect and reconnect the keyboard mid-session; confirm control
  resumes without restarting.

## Cross-platform equivalence check

Perform once any two platforms are available to a human.

- [ ] Create the same candidate on two platforms from the same built-in.
- [ ] Nominate both and run
  `python3 tools/design_lab/validate_design_export.py <bundle-directory>` on
  each; both must pass the same validator.
- [ ] Diff the two `preset.json` files. Only `build_identity` may differ, and
  only in its `platform` and `export_transport` provenance fields, timestamps,
  and engine build string. Any difference in `properties`, `semantic_owners`,
  or `snapshot_hash` is a defect.

## Repository promotion checklist

A successful human evaluation does not promote a design. Promotion requires a
separate reviewed repository change that:

1. validates the bundle schema;
2. resolves every property through the canonical registry and confirms exactly
   one semantic owner;
3. compares the candidate with the relevant baseline;
4. updates the appropriate authoritative design documentation;
5. updates the shipped catalog only if formally accepted;
6. updates regression fixtures/tests;
7. runs the full repository verification; and
8. keeps authority, runtime configuration, and shipped catalog consistent.

Stage 54F-6 owns default selection and any bounded polish. This acceptance
record does not predetermine that decision.
