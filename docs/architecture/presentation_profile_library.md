# Presentation Profile Library

Status: active Stage 54F-3 Godot product-shell contract

## 1. Purpose and invariant

The Presentation Profile Library owns explicit persistence for named,
portable `PresentationProfile` artifacts. It extends the accepted parameter
and Live Designer architecture without making ordinary editing persistent:

```text
Designer edit -> detached working B -> runtime preview only
explicit library Save -> persistent named artifact
```

It is not a theme system, settings-store replacement, gameplay/setup/replay
preset, camera-pose store, or database.

## 2. Authority and boundaries

`shell_settings_registry.json` remains authoritative for parameter IDs, types,
defaults, bounds/options, semantic owners, accessibility classification,
persistence eligibility, and runtime applicability. Schema-1
`PresentationProfile` remains authoritative for complete validated value
composition and deterministic value snapshots. `SettingsStore` remains the
only writer of ordinary player preferences.

The library establishes Godot product-shell authority only for:

- local named-profile identity and display names;
- artifact storage and listing;
- explicit save, load, duplicate, rename, delete, import, and export;
- storage diagnostics and failure transaction boundaries.

It does not transfer or duplicate presentation-parameter authority. It cannot
write ordinary settings, change startup defaults, or call gameplay/native
state APIs.

## 3. Stored representation

Each user profile is one UTF-8 JSON file under:

```text
user://presentation_profiles/<32-lowercase-hex-id>.tet4d-presentation-profile.json
```

There is no index. Listing scans the directory, validates each matching file,
and sorts by case-insensitive display name then stable ID. One corrupt file is
diagnosed and skipped without affecting other profiles.

Artifact schema 1 is:

```json
{
  "artifact_type": "tet4d.presentation_profile",
  "artifact_schema_version": 1,
  "profile_id": "generated stable local/portable identity",
  "display_name": "User-visible name",
  "presentation_profile": {
    "schema_version": 1,
    "values": {}
  }
}
```

The outer schema owns artifact lifecycle metadata only. The embedded snapshot
is the existing authoritative profile schema; the library does not maintain a
parameter inventory or migration table.

Files are written through a temporary file and replacement/restore sequence
consistent with shell-settings persistence. A generated validated ID, never a
display name or imported path fragment, selects a library filename. Display
names are trimmed, length-bounded, reject control/path separators and traversal
tokens, and are unique case-insensitively. Rename changes display name while
preserving ID and values. Duplicate and import allocate fresh local IDs.

## 4. Compatibility policy

The library accepts only artifact schema 1 and
`PresentationProfile.SCHEMA_VERSION`. Future artifact/profile versions fail
before persistence or runtime application with a useful newer-format error.
There is no implicit cross-version migration in this stage.

Current `PresentationProfile` behavior remains normative:

- unknown parameter IDs are rejected;
- known IDs with invalid types, numeric bounds, enum membership, or finite-
  number validity are rejected;
- omitted values in the current profile schema are filled from authoritative
  registry defaults;
- the resulting complete profile must conform before any mutation.

This documented same-schema missing-key behavior supports additive registry
growth; it is not permission to discard unknown newer semantics.

## 5. Lifecycle semantics

### Save As and Save

`Save As` creates a new stable identity from detached working B after name and
profile validation. Duplicate names fail; no existing artifact is overwritten.

`Save Profile` is available only for a profile loaded or saved in the current
Designer session and is a deliberate overwrite of that stable identity. Every
ordinary parameter edit remains runtime-only until that action. Successful
save replaces the semantic dirty baseline.

### Load and A/B

Load validates and deserializes the stored artifact, creates a detached
profile, replaces working B, selects/displays B, and applies it through the
existing `profile_preview_requested` boundary. Captured A is neither recaptured
nor mutated. The stored object is never exposed for mutation.

### Duplicate, rename, and delete

Duplicate copies semantic values into a new ID and distinct derived or
user-chosen name. Rename preserves ID and values and does not apply the profile.
Delete is confirmation-backed in the UI. Deleting a loaded source removes the
artifact but leaves the currently active detached B unchanged.

### Import and export

Import parses and validates the complete portable artifact before writing a
fresh local identity. It does not auto-apply. Export writes the validated named
artifact to an explicit selected destination and excludes absolute paths,
settings documents, screenshots, runtime hashes, gameplay/session state,
Designer state, and camera pose.

Failed import/export/save/rename/delete operations do not partially mutate the
library. Import failure also leaves working B, captured A, runtime presentation,
ordinary settings, and gameplay unchanged because validation/persistence
complete before the Designer receives a selectable result.

## 6. Designer and dirty state

The library is a collapsible section inside the full Designer and is collapsed
by default. Compact and hidden modes retain their accepted dimensions and
input behavior. The Designer displays the loaded/saved source and a `*` when
working B differs semantically from its stored/saved baseline.

Dirty state compares complete `PresentationProfile.values()` only. It is not
affected by selecting A/B, current camera manipulation, gameplay advancement,
Designer collapse/hide/scroll, or the library section's disclosure state. No
save prompt is introduced on hide.

## 7. Isolation and applicability

Named artifacts contain only registry-authorized profile values. They exclude
canonical setup, board/piece/queue/Hold/NEXT/Ghost semantic state, score/RNG,
topology, basis, active slice, collision, replay/trace/hash identity, current
camera yaw/pitch/pan/zoom/focus, Designer state, and shell-settings documents.

Loading continues through the accepted bounded application seam. Runtime
applicability remains registry-driven for Live 2D, 3D, and 4D; serialization
does not give an inapplicable value new semantics. Profile application may
change registered camera preferences but never restores arbitrary current pose.

## 8. Future built-in profiles

The artifact model can later distinguish read-only built-in profiles from
user-managed profiles while sharing the same authoritative payload. Stage
54F-3 creates no built-in themes, theme pack, palette editor, marketplace, or
sharing service.

## 9. Verification contract

Focused evidence covers lifecycle independence, explicit-write boundaries,
strict validation, corruption isolation, safe replacement, path safety,
round-trip fidelity, A/B detachment, settings/gameplay/camera isolation,
2D/3D/4D applicability, and cockpit structure. Production Godot 4.7.1 review
covers Save As, load restoration, A/B comparison, detached delete, and one
actual export/import path. The canonical, pinned, persistence/governance,
semantic-boundary, sanitation, and full repository gates remain required.
