# Display Infrastructure

Status: Stage 51 display-only architecture contract.

Current reconciliation: the post-Stage-54 presentation parameter contract
retains this display authority and routes complete validated values through a
detached schema-1 `PresentationProfile`. The checked-in settings registry is
now also authoritative for each parameter's unique semantic owner,
accessibility classification, and runtime applicability. Representative board,
piece, Ghost, slice-set, palette, and environment values apply through the
single `TraceReplayApp.apply_presentation_profile()` entry point. Applying a
profile rebuilds presentation from the current exported snapshot; it does not
restart a native session or reset current camera pose, basis, or slice-local
orientation. See `presentation_parameter_contract.md`.

## 1. Purpose and boundaries

Stage 51 establishes one Godot-owned display-settings path for the product
shell. It covers window, scale, theme, HUD density, board detail, and camera
presentation. It does not own gameplay state, game setup, topology, replay
identity, input bindings, or accessibility behavior.

Python remains the semantic oracle. Native C++ remains the accepted bounded
plain-session owner. Godot consumes their state for presentation without
changing it.

## 2. Existing baseline and focused delta

Stage 48 already established the checked-in shell-settings registry,
`user://shell_settings.json`, validated persistence, generated Settings
controls, theme choice, replay presentation controls, keyboard-hint choice, and
onboarding visibility. Stages 49 and 50 separately established board and game
setup in `user://game_setup.json`.

The focused Stage 51 delta is:

- add bounded window mode and remembered window size;
- add one semantic UI-scale choice;
- add meaningful HUD and board-detail presets;
- add camera sensitivity and vertical inversion;
- propagate those settings through one runtime presentation owner;
- preserve themes and Stage 48 presentation choices;
- migrate schema 1 without mixing display and game setup.

High contrast, reduced motion, contextual-help policy changes, focus redesign,
and other accessibility behavior are not part of this contract.

## 3. Display authority

Godot owns shell display configuration, validation, persistence, live
application, window state, viewport response, UI layout, HUD presentation,
renderer presentation, themes, and camera interaction presentation.

Godot does not derive gameplay truth. Display choices cannot affect native
construction, commands, snapshots, state hashes, effective seeds, replay
identity, or Python behavior.

## 4. Canonical display-settings model

`godot/Tet4D.Godot/config/shell_settings_registry.json` is the canonical
declaration/default model. The registry supplies identifiers, types, bounded
values, player-facing labels, defaults, persistence policy, and validation
metadata. Runtime code may interpret a validated preset but may not define a
second persisted default.

The Stage 51 model is:

| ID | Accepted values | Default |
| --- | --- | --- |
| `display.window_mode` | `windowed`, `fullscreen` | `windowed` |
| `display.windowed_size` | two validated integers | `[1280, 720]` |
| `display.ui_scale` | `small`, `standard`, `large`, `extra_large` | `standard` |
| `theme.name` | `diagnostic`, `plain`, `tron` | `plain` |
| `display.hud_density` | `compact`, `standard`, `detailed` | `standard` |
| `display.board_detail` | `minimal`, `standard`, `full` | `standard` |
| `camera.sensitivity` | `low`, `standard`, `high` | `standard` |
| `camera.invert_y` | boolean | `false` |

The existing `display.show_w_labels` and `display.projection_strength` settings
remain compatible Stage 48 presentation controls. They do not become gameplay
or board-geometry settings.

Registry validation and `SettingSpec.validated_value()` normalize values at the
persistence boundary. `SettingsStore.value()` returns safe copies for mutable
values. Raw JSON dictionaries do not leave the registry/store boundary.

## 5. Persistence ownership

`SettingsStore` is the only disk owner. It reads and writes
`user://shell_settings.json`; consumers never read that path. It serializes a
canonical schema/version envelope and only registry entries marked persistent.

`user://game_setup.json` remains a separate Stage 49/50 owner. Display reset,
load recovery, window changes, and live propagation must never read, write, or
reset game setup.

## 6. Runtime propagation flow

The coherent runtime path is:

```text
shell_settings_registry.json
            |
       SettingsStore
            |
       SettingsPanel
            |
  ReplayHud + detached PresentationProfile
      /      |       |       \
 window   theme/UI   HUD   app signals
                              |
              TraceReplayApp bounded apply
                     /       |       \
              renderer    camera   environment
```

Generated controls submit bounded values to the store. The panel emits the
canonical stored value. `ReplayHud` applies shell-local policy and forwards
renderer/camera policy through `TraceReplayApp`. Consumers never parse the JSON
file or maintain independent persisted caches.

## 7. Window-management policy

The supported modes are ordinary resizable windowed mode and fullscreen on the
current display. Before entering fullscreen, the last valid windowed size is
retained. Fullscreen dimensions never replace it. Returning to windowed mode
restores a size clamped to the current display's usable rectangle and centers
the window so it remains reachable.

The documented minimum viewport is `634 x 660`, derived from the current shell
layout contract and protected by layout tests. The persisted hard ceiling is
`16384 x 16384`; the current display provides the effective runtime ceiling.
Resize and mode changes trigger the existing responsive/container and
board-fitting paths without reconstructing a native session.

## 8. UI-scale policy

Semantic presets resolve centrally to:

| ID | Factor |
| --- | --- |
| `small` | `0.90` |
| `standard` | `1.00` |
| `large` | `1.15` |
| `extra_large` | `1.30` |

The factor is applied through the shared shell theme base scale. It affects
menus, setup, Settings, HUD, overlays, help, labels, controls, and spacing
without scaling gameplay coordinates, board geometry, camera response, or
native input. Scroll containers expose overflow at constrained viewports.

## 9. Theme policy

The persisted IDs remain `diagnostic`, `plain`, and `tron`; `plain` is the
accepted default and is presented to players as Instrument. `diagnostic`
remains the inspection theme and `tron` is the optional Vector Arcade variant.
The canonical model owns the selected ID. `ShellStyleManager`,
`ReplayVisuals`, and the runtime presentation owner apply semantic style roles
to shell and board consumers. Unknown IDs fall back through registry
validation to `plain`.

Theme changes apply live and do not reconstruct gameplay state.

## 10. HUD presentation policy

The HUD consumes already-available state and owns only layout, visibility,
grouping, labels, and formatting.

- `compact` keeps essential score/state and required 4D layer identity.
- `standard` preserves the accepted Stage 50 HUD.
- `detailed` exposes additional player-facing setup, view, and session context
  already available to the shell.

No mode requests different native state or exposes pointers, object IDs, trace
internals, migration flags, or debug-only metrics as player HUD content.

## 11. Board-detail policy

`minimal`, `standard`, and `full` are renderer-independent presentation
presets. Renderers translate them into supported boundary, grid, edge, label,
and helper visibility. Every preset retains occupied cells, active-piece
readability, gameplay-required bounds, active-layer identity, and 4D
navigation. The policy cannot alter board dimensions, coordinates, collision,
camera-fit bounds, state hashes, or replay identity.

## 12. Renderer-consumer responsibilities

The shared 2D/3D/4D renderer receives canonical presentation values through
runtime signals. It maps semantic policy to supported properties, ignores
unsupported camera/detail aspects safely, and updates live.

Renderers do not read or write settings, choose persistence fallbacks, parse
raw setting IDs from disk, or mutate native/gameplay state. The adaptive 4D
matrix continues to render every supported W layer, including all eight Wide-W
layers.

## 13. Camera-presentation policy

Camera sensitivity presets resolve centrally to `0.65`, `1.00`, and `1.45`
times the accepted response. Vertical inversion changes pitch input only.
Yaw, roll direction, piece movement/rotation, W movement, menus, scrolling,
drop timing, and game speed remain unchanged. Two-dimensional presentation
ignores camera-only preferences safely.

Stage 51 does not expose or implement reduced-motion behavior. A later
accessibility stage may extend the camera policy without changing these
settings.

## 14. Default compatibility contract

With no settings file, the shell starts windowed at a safe `1280 x 720`,
standard UI scale, Instrument (`plain`) theme, standard HUD, standard board
detail, standard camera sensitivity, and non-inverted pitch. The stable
persisted IDs and schema remain unchanged; only the visual default changes.

## 15. Error and fallback behavior

Missing files use defaults without error. Schema-1 documents retain every
valid Stage 48 value and default new fields. Structurally valid schema-2
documents validate fields independently, preserve valid siblings, ignore
unknown keys, and default invalid values.

Malformed JSON, non-object roots, missing structural fields, unsupported
versions, and future versions fall back safely in memory and emit concise
diagnostics. Loading never deletes or rewrites the source. A future-version
file is replaced only after an explicit user change or reset. Saving uses a
temporary file and guarded replace/backup/restore path so a failed replacement
preserves the previous valid file where possible.

Missing theme resources, invalid runtime presets, and invalid window sizes
fall back to their standard/default policy without restarting gameplay.

## 16. Deferred accessibility work

Stage 52 owns accessibility behavior, including high contrast, reduced motion,
colour-vision presets, accessibility-specific semantic roles, contextual-help
policy redesign, and focus-system redesign. Stage 51 supplies infrastructure
that Stage 52 may consume but exposes none of those choices.

## 17. Explicit exclusions

Excluded: topology and Topology Lab; replay/schema redesign; gameplay, scoring,
progression, RNG, pieces, speed, board setup, state hashes, bots, native/Python
semantic changes; key rebinding, profiles, controller/touch support; audio;
packaging/Steam; simulator physics; editor/sandbox redesign; arbitrary
resolutions, monitor selection, exclusive fullscreen, and window-position
persistence.

## 18. Test and acceptance strategy

Automated coverage must protect registry defaults and bounds, schema-1
migration, schema-2 round trip, malformed/future recovery, valid-sibling
preservation, display-only reset, game-setup/onboarding isolation, derived
scale/camera factors, notifications, window-size clamping, runtime theme/HUD/
detail/camera propagation, geometry/state-hash invariants, layout at minimum
and desktop viewports, all themes, and Wide-W behavior.

Manual acceptance must cover Settings navigation, persistence across restart,
windowed/fullscreen restoration, every scale/HUD/detail/camera preset, all
themes, 2D/3D/4D, pause/end-state actions, and the W=8 interaction suite.
Repository completion requires `CODEX_MODE=1 ./scripts/verify.sh`.

## 19. Future consumers

Accessibility, topology presentation, Topology Lab, tutorials, replay
presentation, editor/sandbox presentation, physics-simulator views, and future
control/input configuration may consume this infrastructure. They must extend
the canonical registry/store/runtime flow rather than introduce another
settings file, local enum family, or presentation cache.

## 20. Stage 54F applicability and truthful naming refinement

The schema-3 registry may declare optional `ui_contexts` presentation metadata
for a setting. The admitted values are `global_settings`, `replay`,
`live_2d`, `live_3d`, and `live_4d`. Omission retains the historical all-context
behavior. This metadata controls only whether a generated row is relevant in
the current Settings-panel context; it does not alter validation, defaults,
persistence, reset ownership, runtime propagation, or authority.

The full global Settings screen remains a place to configure every supported
preference. Generated Quick Settings filters context-specific controls:
replay speed/loop and replay object scale are replay-only there, while 4D slice
labels appear only in Live 4D or 4D-capable replay/global settings. Existing
IDs remain stable for persistence compatibility.

Player-facing copy names actual effects. `display.projection_strength` is
presented as replay object scale because the renderer scales replay cells,
particles, and event markers rather than camera projection. The persisted
`display.board_detail` ID is presented as cell-outline strength because its
minimal/standard/full policy changes active, locked, and Ghost outline weight,
not board geometry or grid density.

Runtime UI scale must change rendered geometry, not merely a stored factor or
Theme resource hint. `ReplayHud` owns the scale transform: it applies the
canonical factor to the HUD root and inversely adjusts the root's logical
bounds so the transformed shell continues to cover the physical viewport.
ThemeDB receives the same fallback factor for controls that consume Godot's
theme scale. This reflows menus, text, HUD controls, Settings scrolling, and
focus geometry without changing the OS window, game viewport authority,
gameplay state, camera state, or persistence schema. Returning to Standard
restores an identity transform and the full logical viewport bounds.
