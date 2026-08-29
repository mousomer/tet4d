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

`DesignComparisonSession` freezes:

- session ID and creation time;
- scenario ID and deterministic non-style identity;
- exact detached A and B snapshots plus canonical hashes;
- deterministic blind display assignment; and
- the active arm.

Switching arms returns only the selected detached profile to the product's
existing presentation-application path. It cannot call gameplay commands,
advance replay, consume RNG, change the selected case/frame, reset camera pose,
or write settings/profile storage. The application verifies the scenario's
non-style fingerprint before and after a switch. Any mismatch aborts the
comparison instead of silently continuing.

The observable style contract is the complete canonical profile snapshot, so
`A -> B -> A` is exact by construction. Each arm is copied on creation and on
read; user edits cannot leak across arms. Blind mode displays deterministic
neutral labels while the stored session always retains true IDs.

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

## 9. Windows distribution

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

## 10. Verification contract

Automated evidence covers catalog ownership, candidate copy/persistence,
scenario repeatability, A/B isolation and restoration, evaluation immutability,
capture files/metadata and state isolation, export consistency, repository
validation, resource closure, and Windows package structure. Product runtime
evidence exercises every built-in across representative dimensional scenarios
and rejects script/resource/ownership errors.

Human acceptance begins only after automation is green and evaluates readability,
spatial comprehension, hierarchy, focus, comfort, UI clarity, blind labeling,
capture provenance, and proposal portability. Human preference is evidence, not
automatic authority.
