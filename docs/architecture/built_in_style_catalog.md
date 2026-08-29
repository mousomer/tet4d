# Built-in Style Catalog

Status: active Stage 54F-4 Godot product-shell contract

## 1. Purpose and invariant

The Built-in Style Catalog owns the curated, read-only presentation styles that
ship with Tet4D. It is the third and last presentation artifact kind, and it is
deliberately not another profile library:

```text
A. runtime working presentation state   -> detached, never stored
B. user library profiles                -> mutable, stored under user://
C. built-in styles                      -> read-only, shipped in the repository
```

The product flow is one-directional:

```text
built-in style
    -> apply -> detached working B
    -> edit  -> ordinary Designer B
    -> Save As / Copy to User Library -> ordinary mutable user profile
```

A built-in style is never renamed, deleted, overwritten, or mutated. It is not a
theme engine, a style-authoring surface, a procedural generator, a marketplace,
or a second parameter registry.

## 2. Authority and boundaries

`shell_settings_registry.json` remains authoritative for parameter IDs, types,
defaults, bounds/options, semantic owners, accessibility classification,
persistence eligibility, and runtime applicability. Schema-1
`PresentationProfile` remains authoritative for complete validated value
composition. `PresentationProfileLibrary` retains mutable user-artifact
lifecycle, and `SettingsStore` retains ordinary player preferences.

`BuiltInStyleCatalog` establishes Godot product-shell authority only for:

- shipped built-in style identity and ordering;
- built-in display metadata (name, description, category, accent summary,
  recommended modes, animated flag);
- read-only resolution of a shipped style into a detached `PresentationProfile`;
- catalog load diagnostics.

It owns no parameter meaning, no applicability, no renderer application, no
persistence, and no gameplay state. It exposes no write API at all: read-only is
a structural property of the owner, not a runtime flag that code could bypass.

## 3. Stored representation

The catalog is one repository-shipped UTF-8 JSON document:

```text
godot/Tet4D.Godot/config/built_in_style_catalog.json
```

It is loaded through `res://` and never copied into, mirrored from, or written
to `user://`. Catalog schema 1 is:

```json
{
  "catalog_type": "tet4d.built_in_style_catalog",
  "catalog_schema_version": 1,
  "styles": [
    {
      "style_id": "lowercase_snake_identity",
      "display_name": "User-visible name",
      "short_description": "One-line purpose",
      "category": "baseline | heritage | vivid | animated | technical | accessibility",
      "ordering": 10,
      "animated": false,
      "accent_summary": "Short palette/treatment summary",
      "recommended_modes": ["live_2d", "live_3d", "live_4d"],
      "presentation_profile": {"schema_version": 1, "values": {}}
    }
  ]
}
```

The outer document owns shipped catalog metadata only. The embedded snapshot is
the existing authoritative profile schema, so the catalog maintains no parameter
inventory, bounds table, or migration table.

Each style declares the values it deliberately curates. Omitted values are
filled from authoritative registry defaults by the existing same-schema policy,
which keeps window, replay, diagnostics, and camera-preference parameters out of
style authorship instead of letting a style dictate them.

An entry is rejected before use when its identity is unsafe, its display name is
empty or over-long, its category is unknown, its embedded schema version is
unsupported, or its values fail `PresentationProfile` validation. Rejected
entries produce one diagnostic each and never hide healthy entries. A malformed
or unsupported catalog yields zero styles plus a diagnostic rather than a
partially trusted catalog.

## 4. Read-only semantics

`BuiltInStyleCatalog` exposes `list_styles()`, `has_style()`, `style_profile()`,
`animated_style_ids()`, `diagnostics()`, and `deterministic_snapshot()`. There
is no save, save-as, rename, duplicate, delete, import, or export operation.

`style_profile()` rebuilds a fresh `PresentationProfile` from a duplicated value
map on every call, so a caller can never reach the shipped source object. Every
listed record carries `read_only: true`.

In the Designer, built-in entries are prefixed `BUILT-IN ·`, live in their own
section, and are described as read-only in the selection description. Applying a
built-in style clears the loaded user-profile identity, which structurally
disables explicit `Save Profile`. The only ways to keep a modified built-in
style are `Save As` and `Copy to User Library`, both of which create an ordinary
mutable user profile with a fresh generated user identity.

## 5. Designer integration and A/B interaction

The catalog is a collapsed-by-default disclosure section inside the existing
full Designer, above the Profile Library section. The two sections are mutually
exclusive so their combined minimum content can never exceed the already
allocated Designer overlay; expanding either one consumes internal Designer
space and leaves the production cockpit rect and gameplay `SubViewportContainer`
rect unchanged.

Apply semantics reuse the accepted A/B contract exactly:

```text
apply built-in style
    -> detached values replace working B
    -> B is displayed through profile_preview_requested
    -> captured A is neither recaptured nor mutated
    -> the shipped catalog entry is unchanged
```

Dirty state continues to compare complete `PresentationProfile.values()` against
the applied baseline, so editing after applying a built-in style reads as
modified without implying a stored artifact exists.

## 6. Animated background surface

A genuine Tron-like style needs motion, so this stage adds one bounded
environment-layer animation surface. It is presentation-only and is controlled
entirely by three registry parameters owned by `ENVIRONMENT_PRESENTATION`:

| ID | Type and bounds | Default | Meaning |
| --- | --- | --- | --- |
| `environment.background_animation_mode` | enum `none`, `tron_grid_flow` | `none` | Selects the animated world-background treatment. |
| `environment.background_animation_intensity` | float, `0.00..1.00` | `0.55` | Scales how strongly the treatment reads. `0` falls back to the static background. |
| `environment.background_animation_speed` | float, `0.00..2.00` | `1.00` | Scales flow rate. `0` holds a still frame. |

`AnimatedBackground` renders one screen-covering quad parented to the active
camera at a fixed large negative local depth, far behind the fitted play volume
and inside the default camera far plane. Its material is unshaded and never
writes depth, and ordinary depth testing remains enabled, so gameplay wins the
depth test in either draw order. Glow post-processing stays disabled so no
background energy can bleed over pieces.

Design rules that keep the cockpit primary:

- the pattern is computed in screen space, so it never couples to gameplay zoom,
  camera orbit, board geometry, or slice layout, and cannot induce camera-motion
  competition with the play surface;
- derivative-widened lattice lines fade out where they would alias, so the
  convergence region degrades to calm field rather than shimmer;
- the frame centre is explicitly damped relative to the periphery, so the board,
  NEXT, and HOLD always read against the quietest part of the field;
- motion is low-frequency flow plus one slow luminous band; there is no strobe,
  flash, particle system, or full-screen pulse.

Colour is palette-derived, never local RGB literals. The base colour is exactly
the world background the shell already resolved from `ROLE_BACKGROUND` composed
with `environment.background_intensity`; lines use `ROLE_LIVE_BOARD_GRID` and
the travelling band uses `ROLE_ACCENT`, both for the current `theme.name`.

The flow phase is owned by the component, advanced from frame delta, and wrapped
on the lattice period. It deliberately does not consume shader `TIME`, so the
phase is resettable for A/B comparison and freezable for accessibility.

`mode = none` is the current behavior exactly: the surface is hidden, consumes
no per-frame work, and holds phase at zero.

## 7. Accessibility and motion

Motion composes with existing accessibility policy instead of adding a second
motion subsystem. `accessibility.reduced_motion` freezes the animated background
regardless of the selected mode, `environment.background_animation_speed = 0`
holds a still frame, `environment.background_animation_intensity = 0` falls back
to the static background, and the shipped accessibility style selects
`mode = none` with reduced motion enabled.

## 8. Deterministic and gameplay isolation

Style application and background animation are presentation-only. They cannot
construct or reset a native session, issue gameplay commands, mutate canonical
setup, advance queue/RNG, recompute Ghost landing truth, or change
replay/snapshot/hash identity, exact `BasisState`, active slice, canonical board
geometry, or current camera pose.

The animation phase is component-local. It is deliberately excluded from HUD,
app, and gameplay deterministic snapshots so that a time-varying value can never
enter a deterministic comparison.

## 9. Shipped styles

| Style | Category | Purpose | Notable choices |
| --- | --- | --- | --- |
| Tet4D Balanced | baseline | Restrained shipped baseline | Instrument palette, grid `0.35`, background `0.95`, static |
| Python Reference | heritage | Flat homage to the Python build | Diagnostic palette, fine grid `0.22`, hard boundary `1.00`, subdued Ghost `0.75`, background `0.55` |
| Arcade Neon | vivid | Bright cabinet look | Grid `0.55`, full board detail, Ghost `1.30`, background `1.25` |
| Tron Grid Flow | animated | The one animated style | Vector Arcade palette, `tron_grid_flow` at strength `0.55` / speed `0.85`, dark background `0.45` |
| Blueprint Technical | technical | Schematic reading | Grid `0.72`, translucent fills `0.88`/`0.78`, slice spacing `1.25`, detailed HUD |
| High Contrast | accessibility | Maximum separation, no motion | High Contrast invariant, Ghost `1.35`, background `0.30`, reduced motion |

## 10. Future relationship to comparative evaluation

This contract creates and validates candidates only. Stage 54F-5 compares them
systematically on identical deterministic states, and Stage 54F-6 selects and
polishes the product default. The existence of this catalog does not rank the
styles and does not predetermine the shipped default.

Additional animation modes, background animation scale, style thumbnails,
palette-role editing, procedural style authoring, and catalog schema migration
remain deferred.

## 11. Verification contract

Focused evidence covers registry declaration/bounds/applicability of the three
animation parameters, profile snapshot round-trip, catalog structure and
distinctness, read-only immutability under Designer usage, malformed and
rejected-entry isolation, detached apply with unchanged A, Save As and copy
paths, the absence of silent user-profile writes, `none`-mode equivalence,
animated activation, parameter propagation, phase advancement, reduced-motion
freeze, backdrop placement behind gameplay, 2D/3D/4D application through the
registry, unchanged cockpit rects across both disclosure states, and unchanged
deterministic state hash and camera pose.

Because this stage ships visible styles, structural evidence is not sufficient.
Production real-window review records every shipped style across Live 2D, 3D,
and 4D plus full and compact Designer, and records two Tron frames at different
animation phases to prove real motion with intact board readability. The
canonical, pinned, governance, settings-externalization, semantic-boundary,
sanitation, and full repository gates remain required.
