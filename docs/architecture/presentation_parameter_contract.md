# Presentation Parameter Contract

Status: implemented durable post-Stage-54 contract

## 1. Purpose

Tet4D presentation configuration is non-gameplay state and cannot contribute
to deterministic session identity.

This contract makes tweakable Godot presentation values explicit without
replacing the accepted visual, settings, accessibility, view, or 4D
presentation architectures. Stage 54F-2 later added detached Designer tuning,
and Stage 54F-3 added explicitly persisted named artifacts under
`presentation_profile_library.md`. Controlled experiment assignment and
procedural themes remain outside this parameter contract.

## 2. Existing authorities retained

- `config/shell_settings_registry.json` is the sole declaration/default,
  type, range/options, ownership, persistence-eligibility, accessibility, and
  runtime-applicability registry.
- `config/shell_theme_palettes.json` remains the sole semantic colour-role
  source. A parameter can choose or modulate a palette; renderer code cannot
  replace palette-role colours with local RGB literals.
- `SettingsStore` remains the only preference writer and
  `user://shell_settings.json` remains the only presentation-preference
  document.
- `docs/design/godot_visual_system.md` remains the visual hierarchy and
  accessibility-composition authority.
- `docs/architecture/4d_presentation_interaction_architecture.md` and
  `docs/architecture/camera_gui_preset_semantics.md` retain ownership of exact
  basis `B`, shared slice-local orientation `L`, anchor/layout composition,
  outer view/framing, Fit, Reset, and presentation-context lifecycle.

This contract formalizes ownership inside existing Godot presentation
authority. It performs no authority transfer or new-authority establishment.

## 3. Terminology

| Term | Meaning |
| --- | --- |
| Presentation parameter | One typed, bounded registry value with exactly one semantic owner. |
| Presentation profile | A detached, versioned, complete value set validated against the registry. |
| Board preset | A gameplay/setup shortcut that selects canonical board dimensions and related setup values. |
| Runtime camera/basis state | Transient current pose, focus, zoom, projection, exact `B`, shared `L`, framing, and Fit/Reset state. It is never a presentation-profile value. |

A profile is not called a preset. Named view actions are also not profile
identity: they apply bounded transient view changes under the accepted 54E-4
contract.

## 4. Deterministic boundary

For one deterministic state `S` and two validated profiles `A` and `B`:

```text
render(S, A)
render(S, B)
```

may differ visually, but both calls describe the same game. Profile creation
or application cannot construct or reset a native session, issue gameplay
commands, mutate canonical setup, refresh queue truth, advance RNG, recompute
Ghost landing truth, or change replay/snapshot/hash identity.

The forbidden destinations are:

- `canonical_session_setup()` and `user://game_setup.json`;
- native session state and native value-copy state;
- board dimensions, topology, piece identity/coordinates, queue/RNG, gravity,
  movement/rotation legality, collision, clearing, score, Hold, and game over;
- gameplay snapshots, traces, replays, deterministic hashes, and session IDs;
- current `B`, `L`, camera pose, focus, zoom, projection, or framing.

Renderer rebuilds, material replacement, responsive anchor recomputation, and
fit-bound recomputation are presentation effects. They must consume the same
already-exported gameplay snapshot.

## 5. Registry metadata

Every registry entry must declare:

```text
id
semantic_owner
value_type
default
min / max / step for numeric values
options for enum values
persistence and persist
accessibility_classification
runtime_applicability
```

`SettingSpec` and `SettingsRegistry` reject missing fields, unknown values,
duplicate IDs, invalid defaults, invalid ranges/options, empty applicability,
or conflicting persistence declarations. A single scalar `semantic_owner`
field makes multiple owners structurally impossible.

Allowed accessibility classifications are:

- `neutral`: no accessibility-specific interpretation;
- `aesthetic`: ordinary style selection with no essential-state authority;
- `accessibility_composable`: aesthetic/legibility value over which invariant
  and High Contrast policy retains final minimum-legibility authority;
- `accessibility_preference`: a preference owned by accessibility policy.

Allowed runtime applicability values are `shell`, `replay`, `live_2d`,
`live_3d`, and `live_4d`. Applicability describes consumers; generated-panel
`ui_contexts` remains a separate row-visibility declaration.

## 6. Semantic-owner inventory

| Parameter | Owner | Runtime applicability | Accessibility classification |
| --- | --- | --- | --- |
| `display.window_mode` | `SHELL_PRESENTATION` | shell | neutral |
| `display.windowed_size` | `SHELL_PRESENTATION` | shell | neutral |
| `display.ui_scale` | `ACCESSIBILITY_PRESENTATION` | shell, replay, all live modes | accessibility_preference |
| `display.hud_density` | `HUD_PRESENTATION` | replay, all live modes | accessibility_composable |
| `display.board_detail` | `PIECE_PRESENTATION` | all live modes | accessibility_composable |
| `ghost.enabled` | `GHOST_PRESENTATION` | all live modes | accessibility_composable |
| `settled_cells.opacity` | `PIECE_PRESENTATION` | all live modes | accessibility_composable |
| `display.grid_visible` | `BOARD_PRESENTATION` | all live modes | accessibility_composable |
| `replay.playback_speed` | `REPLAY_PRESENTATION` | replay | neutral |
| `replay.loop_enabled` | `REPLAY_PRESENTATION` | replay | neutral |
| `display.show_w_labels` | `SLICE_SET_PRESENTATION` | replay, live 4D | accessibility_composable |
| `display.projection_strength` | `REPLAY_PRESENTATION` | replay | aesthetic |
| `theme.name` | `PALETTE_PRESENTATION` | shell, replay, all live modes | accessibility_composable |
| `accessibility.high_contrast` | `ACCESSIBILITY_PRESENTATION` | shell, replay, all live modes | accessibility_preference |
| `accessibility.reduced_motion` | `ACCESSIBILITY_PRESENTATION` | shell, replay, all live modes | accessibility_preference |
| `accessibility.show_help_hints` | `ACCESSIBILITY_PRESENTATION` | shell, replay, all live modes | accessibility_preference |
| `camera.sensitivity` | `CAMERA_PRESENTATION` | replay, live 3D, live 4D | neutral |
| `camera.invert_y` | `CAMERA_PRESENTATION` | replay, live 3D, live 4D | neutral |
| `diagnostics.show_layout_bounds` | `DIAGNOSTICS_PRESENTATION` | shell, replay | neutral |
| `interface.show_onboarding` | `GUIDANCE_PRESENTATION` | all live modes | accessibility_composable |
| `board.grid_opacity` | `BOARD_PRESENTATION` | all live modes | accessibility_composable |
| `board.boundary_opacity` | `BOARD_PRESENTATION` | replay, all live modes | accessibility_composable |
| `active_cells.opacity` | `PIECE_PRESENTATION` | all live modes | accessibility_composable |
| `ghost.opacity` | `GHOST_PRESENTATION` | all live modes | accessibility_composable |
| `slice_set.spacing` | `SLICE_SET_PRESENTATION` | live 4D | aesthetic |
| `environment.background_intensity` | `ENVIRONMENT_PRESENTATION` | replay, all live modes | accessibility_composable |
| `environment.background_animation_mode` | `ENVIRONMENT_PRESENTATION` | replay, all live modes | accessibility_composable |
| `environment.background_animation_intensity` | `ENVIRONMENT_PRESENTATION` | replay, all live modes | accessibility_composable |
| `environment.background_animation_speed` | `ENVIRONMENT_PRESENTATION` | replay, all live modes | accessibility_composable |

`display.board_detail` has one owner even though the shared cell-edge policy
is consumed by active, locked, and Ghost render paths: `PIECE_PRESENTATION`
owns the cross-cell outline scale; `GHOST_PRESENTATION` owns Ghost visibility
and fill opacity. High Contrast may strengthen either consumer to preserve its
independent semantic cues; that is an explicit accessibility composition, not
conflicting ownership.

## 7. Initial parameter meanings and defaults

The existing parameters retain their accepted values. The new values are:

| ID | Type and bounds | Canonical default | Meaning |
| --- | --- | --- | --- |
| `display.grid_visible` | bool | `true` | Session-only quick-control state for internal grid detail; the boundary remains visible. |
| `board.grid_opacity` | float, `0.05..0.90` | `0.31` | Normal internal/floor grid alpha before High Contrast minimum strengthening. |
| `board.boundary_opacity` | float, `0.35..1.00` | `0.90` | Ordinary board/slice wireframe alpha. |
| `active_cells.opacity` | float, `0.35..1.00` | `1.00` | Active-piece fill alpha; outlines remain independently legible. |
| `ghost.opacity` | float multiplier, `0.25..1.50` | `1.00` | Multiplies the selected palette/theme's accepted Ghost fill baseline. |
| `slice_set.spacing` | float multiplier, `0.60..1.60` | `1.00` | Multiplies the responsive 4D horizontal/vertical gutter only. It never changes slice-local geometry. |
| `environment.background_intensity` | float, `0.25..1.50` | `1.00` | Scales the selected semantic world-background role without changing the shell palette. |
| `environment.background_animation_mode` | enum `none`, `tron_grid_flow` | `none` | Selects the bounded animated world-background treatment. `none` is the static themed background. |
| `environment.background_animation_intensity` | float, `0.00..1.00` | `0.55` | Scales how strongly the animated treatment reads. `0` falls back to the static background. |
| `environment.background_animation_speed` | float, `0.00..2.00` | `1.00` | Scales the animation flow rate. `0` holds a still frame. |

Defaults reproduce the accepted local presentation. A renderer may retain
theme-specific material derivation, but it may not retain another user-control
default or range for these IDs. High Contrast may clamp grid/boundary/Ghost or
piece presentation upward where required by its accepted invariant.

## 8. Colour and palette model

The semantic palette maps roles, not game rules or fixed theme language. It
already covers backgrounds, grid/wireframe, active/locked/Ghost cells, labels,
active/inactive layers, axes, controls, and status. `theme.name` selects a
complete role mapping. High Contrast composes with that mapping and remains
semantically distinct from aesthetic theme selection.

The initial contract deliberately does not add a free-form `colour` setting.
Arbitrary role editing has no accepted product surface yet. A later Designer
Lab may add the existing setting-spec `colour` type only alongside an actual
validated role editor and serializable named-profile contract.

## 9. PresentationProfile lifecycle and A/B readiness

`PresentationProfile` schema version 1 is an in-memory value object. It:

- builds from one validated `SettingsRegistry` plus values from `SettingsStore`;
- fills omitted values from registry defaults;
- rejects unknown or invalid values;
- exposes safe copies and owner/applicability queries;
- serializes a deterministic snapshot containing only profile schema version
  and canonical values; and
- creates a new value object for overrides rather than mutating a global
  profile.

`TraceReplayApp.apply_presentation_profile(profile)` is the bounded product
entry point. The HUD applies shell-local consumers and emits the detached
profile; the app applies replay playback preferences, renderer, Ghost
visibility/style, environment, palette, and camera-preference consumers.
Applying a profile never replaces the store automatically. This separation
permits future controlled `render(S, A)` / `render(S, B)` use without
experiment assignment in this stage.

Applying presentation-profile snapshots never writes a document. Existing
settings persistence remains user/product preference state and reconstructs a
profile on load. Separately, Stage 54F-3 may write the same authoritative
snapshot only when the user explicitly saves or imports a named artifact
through `PresentationProfileLibrary`; that operation does not replace or write
the settings store.

## 10. Persistence decision

Schema 3 `user://shell_settings.json` is retained. Its contract is registry-
driven: adding recognized keys is backward-compatible because schema-1/2/3
documents already default any absent current registry entry. The setting
document contains no fixed key inventory and needs no schema bump for this
additive envelope.

Only `local_shell` plus `persist: true` entries reach the ordinary settings
document. Diagnostics and `display.grid_visible` remain session-only there.
`PresentationProfile` itself does not write. Named profile artifacts are a
separate explicit persistence boundary and may contain the complete validated
profile value set, including session-only presentation values, because loading
them still applies only detached runtime presentation and never changes
ordinary startup preferences.
No profile or setting reaches `user://game_setup.json`, native snapshots,
replay/trace files, or deterministic identity.

## 11. Runtime application

Live application may:

- rebuild materials and presentation nodes from the current exported snapshot;
- recompute responsive slice anchors and renderer bounds after spacing changes;
- refit only when accepted presentation layout bounds changed;
- switch the semantic palette/theme;
- update environment colour/intensity; and
- update camera sensitivity, inversion, and reduced-motion interpolation.

It may not call session start/reset/command APIs. Current pose and basis are
captured before profile application and must compare unchanged afterward.

## 12. Dimensional divergence and canonical-geometry follow-on

Stage 54F-1 completed the separately contracted structural follow-on recorded
in `canonical_local_board_presentation_geometry.md`. Live 2D, Live 3D, and
each local Live-4D slice now consume one explicit geometry object for cell
transforms/bounds, centred extent, face-grid segments, and boundary segments.
The 2D embedding is `[X,Y,1]` in presentation only, while 4D dimensions and
axis signs derive from exact `SliceBasis4D`.

The visible divergence is real and has four documented sources:

1. Canonical standard shapes differ by product contract: 3D is
   `6 x 10 x 6`; 4D is `5 x 10 x 4 x 4`.
2. 4D composes exact `B`, shared local `L`, a responsive multi-slice matrix,
   signed slice labels, active-slice frames, and anchor-only spacing; 3D is one
   volume with none of that slice-set composition.
3. 4D uses the accepted fitted far-side mount/reflection and whole-matrix fit;
   3D uses its external-diagram fit. The resulting projected scale and viewing
   angle differ even when one visible 4D slice has 3D-like dimensions.
4. Active 4D face materials deliberately use a darker/lower-emission
   derivative than active 3D face materials to control matrix brightness.

The shared local geometry is therefore not the cause of remaining divergence. The differences are
shape, composition, framing, and one mode-specific material derivative. This
parameter contract owns common safe roles and spacing but no geometry,
3D/4D offsets, camera compensation, or per-mode scale. Stage 54F-1 adds no
profile-specific compensation and does not require projected screenshots to
match.

## 13. Animated environment scope

Stage 54F-4 adds the three background-animation parameters above and one bounded
`AnimatedBackground` consumer under `built_in_style_catalog.md`. The animated
surface is confined to the environment/background layer: it renders behind the
play volume, never writes depth, derives every colour from existing semantic
palette roles, and owns a component-local flow phase rather than shader `TIME`.

`accessibility.reduced_motion` retains final motion authority over these
aesthetic values, which is why they are classified `accessibility_composable`
rather than as a second motion preference. The animation phase is deliberately
excluded from every deterministic snapshot.

This contract still owns no geometry, per-mode scale, camera compensation, or
shader authoring surface. Procedural themes and free-form effect graphs remain
outside it.

## 14. Verification contract

Automated evidence covers registry integrity, exact ownership, default
profile parity, copy-on-override switching, renderer consumption, schema-1/2/3
persistence, deterministic/session isolation, and 2D/3D/4D/custom/W=1 mode
coverage. Structural material, node metadata, anchor, bounds, profile, and
native snapshot/hash assertions are preferred over brittle screenshot pixels.

Real-window review records the exact Godot/platform/path and demonstrates
default coherence plus live active-piece, grid/boundary, Ghost, palette,
slice-spacing, environment, UI-scale, and accessibility changes without a game
restart. Agent-driven review is evidence, not independent human sign-off.
