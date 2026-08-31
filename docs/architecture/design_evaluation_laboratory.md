# Design Evaluation Laboratory

Status: active Stage 54F-5 Godot product-shell contract

## 1. Purpose and promotion boundary

The Design Laboratory turns the accepted presentation-profile apparatus into a
repeatable human evaluation workflow:

```text
shipped built-in or mutable user profile
    -> detached candidate
    -> deterministic scenario
    -> isolated A/B judgment
    -> durable evidence and captures
    -> nominated portable proposal
    -> human-reviewed repository promotion
```

The laboratory produces evidence. It never selects the production default,
rewrites `res://` catalog data, changes runtime settings, or edits architecture
documents. Stage 54F-6 remains the promotion and polish boundary.

## 2. Existing authorities retained

- `shell_settings_registry.json` and `SettingsRegistry` remain the sole property
  identity, validation, applicability, and semantic-owner authority.
- `PresentationProfile` remains the sole complete presentation-value object.
- `BuiltInStyleCatalog` remains the sole shipped read-only style owner.
- `PresentationProfileLibrary` remains the sole mutable user-profile store.
- Existing replay bundle cases and native snapshots remain gameplay truth.
- Canonical local-board geometry, exact 4D `BasisState`, slice-local camera
  orientation, slice-set layout, GUI layout, and accessibility composition keep
  their existing independent owners.

The laboratory adds orchestration and evidence schemas only. It creates no
parallel property mapping or gameplay fixture.

## 3. Design scenarios

`DesignScenarioCatalog` reads one shipped schema-versioned JSON document. Each
entry contains a stable ID, display metadata, dimensional/density/feature tags,
a registry-validated presentation starting snapshot, and exactly one of:

- an existing replay case plus deterministic frame index; or
- an existing canonical fixed-seed live setup plus a bounded command list.

A scenario is therefore:

```text
existing deterministic replay state at a fixed frame or fixed-seed native state
+ detached deterministic presentation starting state
```

The catalog owns selection metadata, not board data or transitions. Loading or
resetting always reconstructs the same case/frame or canonical setup/command
sequence, restores the canonical view/basis/slice-local presentation start, and
pauses the result. A missing case, invalid frame/setup/command, malformed ID,
unknown property, or invalid value is rejected diagnostically.

## 4. Preset resolution and candidate lifecycle

`DesignPresetResolver` presents built-in and user profile records through one
read-only descriptor shape while preserving source ownership. Built-ins resolve
through `BuiltInStyleCatalog`; users resolve through
`PresentationProfileLibrary`. Both produce new detached `PresentationProfile`
objects.

Candidate creation is the existing explicit copy/save-as lifecycle. Resolver
metadata may label a mutable user artifact `candidate`, but it does not store a
second profile or mutate shipped metadata.

## 5. Comparison-session invariant

`DesignComparisonSession` owns three independent session dimensions:

```text
A = frozen detached preset identity and snapshot
B = frozen detached preset identity and snapshot
shown_arm = A | B
```

The catalogue exposes separate `Apply Live`, `Set as A`, and `Set as B`
operations. Assignment copies the selected resolved preset into exactly one
slot and never chooses the shown arm. Showing or toggling an arm changes only
`shown_arm` and never infers an assignment target. When the slot currently
being shown is reassigned, the renderer refreshes that slot's new snapshot
without changing `shown_arm`; assigning the hidden slot leaves the visible
profile untouched.

The session freezes:

- session ID and creation time;
- scenario ID and deterministic non-style identity;
- exact detached A and B snapshots plus canonical hashes;
- deterministic blind display assignment; and
- the shown arm.

Switching shown arms returns only the selected detached profile to the product's
existing presentation-application path. It cannot call gameplay commands,
advance replay, consume RNG, change the selected case/frame, reset camera pose,
or write settings/profile storage. The application verifies the scenario's
non-style fingerprint before and after a switch. Any mismatch aborts the
comparison instead of silently continuing.

The observable style contract is the complete canonical profile snapshot, so
`A -> B -> A` is exact by construction. Each arm is copied on assignment and
on read; user edits and saves cannot leak across arms. Reassignment advances
the comparison evidence identity so captures made under an earlier pairing
cannot be merged into the new pairing. The serializable session snapshot
round-trips both frozen slots and `shown_arm` with hash validation.

Blind mode begins only after both slots are assigned. It displays deterministic
neutral labels while the stored session always retains true IDs. Entering or
leaving blind mode changes neither assignment nor `shown_arm`; candidate
creation, editing, saving, applying live, reset, capture, and evaluation never
silently assign either slot.

## 6. Evaluation records

`DesignEvaluationStore` owns schema-1 records under the platform user-data
directory. Writes use the shared replacement-safe file helper. A record stores:

- session/scenario IDs, preference, optional eight-dimension 1-5 ratings, notes,
  timestamp, blind state, application/build identity, and catalog/schema version;
- A and B source kind, stable ID, version/schema, display name, exact canonical
  snapshot, and canonical snapshot hash; and
- the frozen non-style fingerprint used during judgment.

Historical records never resolve mutable profile files on read, so later rename,
edit, or deletion cannot alter past provenance.

## 7. Captures

Captures live under a comparison-specific user-data directory as `A.png`,
`B.png`, and `metadata.json`. The product captures the gameplay presentation
viewport after applying the frozen arm and waiting for rendering to settle. It
restores the previously active arm after pair capture and verifies the same
non-style fingerprint throughout. PNG pixels contain no injected preset names;
metadata carries true and blind identities separately.

## 8. Nomination and portable export

Explicit nomination resolves one frozen or current candidate through the
registry and writes:

```text
<preset-id>/
    preset.json
    comparison_summary.json
    DESIGN_PROPOSAL.md
```

`preset.json` stores exact canonical values and the semantic owner resolved for
every property. `comparison_summary.json` contains only actual matching local
records; no aggregate or statistical claim is fabricated. The proposal compares
the candidate to its named reference snapshot and labels itself as review input,
not authority.

The repository validator repeats schema, value, and single-owner validation and
prints the manual promotion checklist. It never writes runtime configuration,
the built-in catalog, or design authorities.

## 9. Platform adapter boundary

The Design Laboratory is one implementation with three distribution targets.
Everything that gives a design meaning is platform independent:

```text
                    Canonical Design Laboratory
                              |
          +-------------------+-------------------+
          |                   |                   |
       Windows             Android             iPadOS
       adapter             adapter              adapter
```

`DesignPlatformProfile` is the single authority for platform identity. It
resolves the platform, its export transport, whether the platform delivers a
system Back gesture, and whether the window needs safe-area insets. Nothing else
in the shell compares `OS.get_name()`. An unknown platform resolves to the
desktop reference target rather than inventing a fourth behaviour.

Only these concerns may differ by platform:

- **Export transport.** `DesignExportTransport` moves an already generated
  bundle somewhere a human can reach: the file manager on desktop, the system
  document picker on Android, and the file-sharing enabled Documents directory
  on iPadOS. It never inspects, rewrites, or re-schemas bundle contents. Handheld
  targets additionally receive one deterministic single-file archive of the same
  bundle, because they have no desktop file manager to browse a directory with.
- **Window adaptation.** Handheld safe-area insets are expressed purely as
  additional outer margin on the shell root. The cockpit hierarchy — board
  primacy, a usefully large 4D board, compact NEXT/HOLD, prominent piece
  controls, secondary camera guidance — is identical everywhere. Tablet
  adaptation must never be satisfied by scaling the UI up and starving the
  board.
- **Lifecycle.** Android's system Back gesture follows the same deterministic
  ladder as Escape and is inert at the main menu. It cannot terminate the
  process or mutate an in-flight comparison session.
- **Input resolution.** The canonical live action contract is the only binding
  authority on every platform. External keyboards on handheld targets, and
  non-US desktop layouts, can report a logical keycode that differs from the
  physical key position a binding was designed around; `PhysicalKeyFallback`
  retries such an event by physical position, but only when the typed character
  is bound to nothing at all. One key press therefore can never dispatch two
  actions, and the fallback is inert wherever logical and physical keycodes
  agree.

Platform reaches an exported bundle only as `build_identity.platform` and
`build_identity.export_transport` provenance. It must never change what a
property means. Equivalent candidates authored on different platforms produce
`preset.json` files whose identity, properties, semantic owners, and snapshot
hash are identical, and all three pass the same repository-side validator.

`display/window/stretch/aspect` is deliberately left at the engine default.
Forcing `expand` varies the viewport aspect that fit-view derives camera
distance from, and the comparison fingerprint includes camera pose, so it
destabilises deterministic scenario reload. A fixed reference viewport also
means an A/B comparison frames the board identically on every platform.

## 9a. Windows distribution

The current Godot Windows artifact is a versioned x86_64 portable ZIP built from
the exact pinned editor/export templates and a release Windows GDExtension. It
contains the executable/PCK, DLL, shipped catalog, scenario metadata, and replay
resources, and excludes tests, editor state, user data, Python, and repository
paths. Mutable data remains in Godot's per-user application-data directory;
exports use an explicit user-selected or user-data destination.

The ZIP is the installer-equivalent distributable: extraction is installation,
launch uses `Tet4DDesigner.exe`, and deletion is uninstall. It deliberately
creates no registry keys, Start Menu entry, or desktop shortcut. The build has a
structural validator on every host. The Windows workflow runs the focused
catalog/comparison/persistence/capture/export suite with the exact Windows
editor, builds and validates the ZIP, and launches the packaged executable
headlessly. Direct clean-machine Windows human execution remains distinct
acceptance evidence. A non-Windows host may prove package structure and resource
closure but may not claim Windows execution.

## 9b. Android tablet distribution

The Android artifact is a versioned arm64 APK built from the pinned editor and
Android export templates, targeting large and extra-large screens in landscape.
Handset screen support is explicitly refused: this is a tablet build for use
with a physical keyboard, not a touch-first game. It uses the prebuilt export
template rather than a Gradle build, so no parallel Android build system enters
the repository. `--export-release` uses an ephemeral test keystore generated at
build time and injected into the release-signing fields of the disposable
staged preset. The tracked preset remains credential-free, and no signing
material is ever committed.

Mutable data stays in Godot's per-user application-data directory. Because that
directory is application private on Android, nomination additionally writes a
portable archive and offers it to the system document picker, so a nominated
design is never trapped inside the application. No broad filesystem permission
is requested.

Configuration and packaged resources are validated on any host through the
exported resource pack, which needs no Java SDK, Android SDK, emulator, or
device. The APK itself requires the full Android toolchain.

## 9c. iPadOS distribution

The iPadOS artifact is a Godot-generated Xcode project targeting the iPad device
family in landscape, built and signed through Xcode. Godot 4.7's mobile renderer
requires an A12 device or newer; that is an engine constraint, not a project
choice.

`UIFileSharingEnabled` and `LSSupportsOpeningDocumentsInPlace` expose the
application's Documents directory in the Files app, which is what makes a
nominated bundle retrievable from the device. This is the canonical Apple
mechanism and needs no native plugin, so the platform export boundary stays
where it is.

Repository-owned metadata — display name, bundle identifier, version, device
family, orientation, deployment target, and the integer release-method enum —
lives in the export preset. The design-evaluation path sets Godot 4.7.2's
`application/export_method_release` to `1` (Development). Signing identity does
not live there: the committed team identifier is a placeholder that
`TET4D_IOS_TEAM_ID` overrides, and no certificate, provisioning profile, or
credential is committed.

iPad configuration and release exports are different artifact classes. A
configuration export deliberately omits the unavailable `ios.*` GDExtension
descriptor lines and native framework, and is configuration evidence only. A
release export must retain the complete descriptor and contain the matching
release xcframework. A checksum identifies only the class actually generated;
a configuration-export checksum is never release-payload evidence.

## 10. Verification contract

Automated evidence covers catalog ownership, candidate copy/persistence,
scenario repeatability, A/B isolation and restoration, evaluation immutability,
capture files/metadata and state isolation, export consistency, repository
validation, resource closure, Windows package structure, Android export
configuration and packed resources, iPadOS Xcode project structure and
metadata, generated Development export method, explicit artifact class,
descriptor/native-payload consistency, and cross-platform semantic equivalence.
Product runtime evidence exercises every built-in across representative
dimensional scenarios and rejects script/resource/ownership errors.

Human acceptance begins only after automation is green and evaluates readability,
spatial comprehension, hierarchy, focus, comfort, UI clarity, blind labeling,
capture provenance, and proposal portability. Human preference is evidence, not
automatic authority.

Evidence must be labelled by the level at which it was actually obtained.
Automated InputMap tests, emulator or simulator testing, and real physical
keyboard testing on a real device are three different claims, and the weaker
one may never be reported as the stronger.
