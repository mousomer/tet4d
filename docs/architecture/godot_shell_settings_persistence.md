# Stage 48 Godot Shell Settings Persistence

Status: implementation complete; interactive acceptance pending
Date: 2026-07-12

## Authority and scope

Stage 48 extends the Stage 29 registry foundation. Godot owns this user-value
layer because every included value affects shell presentation only. The
checked-in registry remains the declaration and default authority. Python
remains semantic authority for gameplay, topology, replay, parity, and
migration decisions; accepted native plain-session ownership is unchanged.

This stage adds no gameplay configuration, live-session persistence, topology
state, replay schema, Python configuration migration, native authority, or
packaging behavior.

## Bounded audit

The existing registry declares seven settings:

| Setting | Runtime owner | Stage 29 persistence | Stage 48 decision |
| --- | --- | --- | --- |
| `replay.playback_speed` | replay playback state | local shell | persist |
| `replay.loop_enabled` | replay playback state | local shell | persist |
| `display.show_w_labels` | replay renderer | local shell | persist |
| `display.projection_strength` | replay renderer | local shell | persist |
| `theme.name` | shell style manager | local shell | persist |
| `diagnostics.show_layout_bounds` | HUD diagnostics | session | exclude from disk |
| `controls_help.show_keyboard_hints` | HUD/help presentation | local shell | persist |

Stage 48 adds `interface.show_onboarding`, a persistent user preference that
enables or disables Stage 47 guidance without storing tutorial progress.

All existing settings already change through the generated Settings panel and
established replay/HUD/style owners. The Stage 29 `SettingsStore` writes an
unversioned Godot `ConfigFile`, does not validate loaded or changed values,
does not report recovery state, and is instantiated independently by the two
Settings panels. Registry defaults are authoritative, but startup state also
has adapter-local fallbacks until the registry values are applied.

Debug-only layout bounds remain visible in the UI but session-only. Camera
transforms, replay frame position, diagnostics data, and every gameplay,
topology, trace, migration, native-session, and Python-launcher value are
explicitly excluded.

Existing tests protect registry shape, generated control types, settings
scrolling, style application, replay layout, Stage 47 onboarding/navigation,
and scene integrity. Stage 48 adds store recovery/round-trip, runtime
persistence, reset, focus, and semantic whitelist coverage.

## Persistence contract

- Storage path: `user://shell_settings.json`.
- Schema: JSON object with `schema_version = 1` and a `settings` object.
- Stored keys: only registry entries explicitly marked `persist: true`.
- Stored values: validated JSON-safe booleans, strings, and numbers.
- Ordering: persistent registry order, producing deterministic canonical JSON.
- Save timing: validated save-on-change; unchanged values do not write.
- Save feedback: the Settings screen reports `Shell settings saved automatically.`
  after a successful write; no separate Save button is required.
- Replacement: write a sibling temporary file and first use Godot's
  overwrite-capable rename. If that operation fails while an existing settings
  file remains, preserve it as a sibling backup before retrying installation.
  A failed retry restores the previous file by rename or copy fallback. Clean
  temporary/backup files where safe; retain the backup and report its path only
  if restoration itself cannot complete.
- Reset: restore registry defaults, apply them immediately, and persist them.

The former Stage 29 `user://tet4d_shell_settings.cfg` path is superseded rather
than maintained as a second persistence source. No Python or repository file
is read or written for runtime preferences.

## Validation and recovery

Loading starts with registry defaults. A missing file is a normal default
state. Malformed JSON, a non-object root, missing/non-object `settings`, or an
unsupported schema version recovers entirely to defaults and records a concise
diagnostic without rewriting the source file. For a structurally valid file,
known valid values survive; unknown keys are ignored and invalid values are
replaced by defaults with diagnostics.

Schema versions must be JSON numbers with an exact supported integral value;
fractional values are never truncated, and strings, booleans, null, arrays,
and objects are rejected. Runtime changes use the same registry validation.
Save failures leave the validated in-memory value available, report the
failure, do not increment the successful-save count, do not emit a success
diagnostic, and do not crash.

## Runtime and UI flow

One registry and one store are owned by `ReplayHud` and shared by both Settings
panels. The store loads values; the panels edit them; existing signals apply
them through replay state, renderer, style manager, HUD/help, and onboarding
owners. The store never mutates those owners directly.

The Settings screen remains viewport-safe, gives initial focus to the first
setting, defines deterministic focus neighbours, and includes a reachable
`Reset Settings to Defaults` action. Esc continues to return to Main Menu.

Acceptance hardening keeps main-menu command cards compact enough that Quit is
fully visible and mouse-hit-testable at the supported viewport. Focused and
hovered cards use the palette's soft accent surface, including the light Plain
theme, rather than relying on a thin border alone. The live board retains grid
lines and its boundary outline but no longer renders an additional filled
mid-board plane. Displayed main-menu shortcuts (`2`, `3`, `4`, `H`, `A`, `S`,
and `Esc`) dispatch the same actions as their cards. Mouse and Esc Quit share
one named application-quit handler. Shortcut dispatch depends on the visible
Main Menu rather than the previously played mode, so it remains available
after returning from Live 2D, 3D, or 4D.

## Explicit non-goals

- gameplay timing, gravity, score, clears, pieces, board or live state;
- topology selection, editor state, or migration;
- replay frame position, replay assets, schema, or trace state;
- key rebinding, controller layouts, new accessibility modes, audio, or accounts;
- Python configuration, migration bundles, C++ changes, Steam, or exports.
