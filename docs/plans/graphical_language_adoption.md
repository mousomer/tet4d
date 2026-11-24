# Graphical Language Adoption

Role: spec
Status: active
Source of truth: this file for the adoption sequence; `docs/design/graphical_language/README.md` for the target look
Supersedes: none (replaces the unmerged PR #199 proposal, which was closed)
Prepared: 2026-11-24

## Owner decisions (2026-11-23 / 2026-11-24)

- The concept images in `docs/design/graphical_language/` are the target.
  Acceptance is a side-by-side comparison of real captures against them.
- Active piece a bit more luminous than the images; locked cells keep full
  hue at higher transparency; overall closer to the images than to the
  current game.
- 4D stays a W-slice matrix. The tesseract and projection views are deferred.
- Layout: concept A (right column plus controls footer) with concept B's
  status line in the footer.
- The 2026-10-25 cockpit and Main Menu layout lock is reopened for this
  redesign. `test_locked_shell_layouts.gd` is re-baselined in the same PR
  that changes the layout (P3), never earlier and never weakened.
- The work is two layers. P1 and P2 are a **skin** (data: theme, materials,
  styles). P3 is a **structural redesign** (the Control tree and layout
  policy). Layout never depends on the theme: one cockpit serves every
  theme.

## Phases

Each phase is one PR, and each changes what the player sees.

### P0 — Spec (this PR)
Commit the concept images, the graphical-language spec and this plan.
Amend the Direction section of `godot_visual_system.md`, which still
describes the older "calm instrument" look.

### P1 — Board skin
- Add a shell theme `luminous` to `config/shell_theme_palettes.json`, using
  the surface, accent, grid and frame swatches from the spec.
- Add a built-in style `tet4d_luminous` to
  `config/built_in_style_catalog.json` (theme `luminous`, a lower
  `settled_cells.opacity`, a glass-level `board.enclosure_opacity`). The
  `luminous` theme is the default.
- Cell materials in `scripts/ui/replay_visuals.gd`, gated on the `luminous`
  theme so the other themes' captures and Designer fingerprints are
  unchanged:
  - Locked cells keep their piece hue. Drop the darken-and-grey blend in
    `live_locked_cell_material` and `live_3d_locked_*`.
  - More emission on the active piece.
  - Bevel shading on 2D cells, and the existing face shading tuned to the
    concept cubes in 3D.
  - Ghost as a translucent grey outline.
- Bevel and seam geometry in `scripts/rendering/cell_renderer.gd`; bloom
  through the scene's WorldEnvironment glow, limited to the active piece.
- Glass enclosure and a bright board frame through the existing
  `board_enclosure_material` and `board_outline_material`.
- 4D slices pick all of this up through the same consumers. Slice placement
  is unchanged.
- Acceptance: captures of 2D, 3D and 4D at 1440×900 from the same seeded
  states, before and after, set next to the concept images. Gameplay and
  replay hashes unchanged. Layout lock test unchanged and green.

**P1 as built (2026-11-24):**
- The active-piece glow is a per-cell halo sprite in the piece's own hue,
  not Environment glow. Godot's glow threshold works on luminance, so it
  cannot bloom dark hues (purple, blue) without clipping them to another
  colour. The active piece is emission-only, so its hue doesn't depend on the
  light angle.
- Locked cube faces are unshaded; the per-face factors are the shading. This
  keeps them at or below full brightness and true to hue.
- 3D/4D locked cells render at 88% of `settled_cells.opacity`. 2D locked
  cells use the setting as-is, because transparency over a flat dark board
  only dims them.
- Everything is gated on the `luminous` theme. The `plain`, `tron` and
  `diagnostic` materials are unchanged.
- `luminous` is the default theme (owner decision 2026-11-24, after
  reviewing the captures). Fresh profiles, reset-to-defaults, invalid
  settings files and unknown theme IDs all resolve to it. Settings schema 4
  migrates a pre-4 saved `plain` (the old default, written for everyone) to
  `luminous`. Saved `tron` and `diagnostic` are kept, and `plain` chosen at
  schema 4 or later is kept.
- 4D's existing recession of inactive slices (Stage 58C) still applies.
- 2D bevel strips carry the same opacity as the cell body. The body is inset
  to the inner square so strips and body never overlap, and every pixel of a
  cell is one layer at the configured opacity.
- Board outer edges in 2D/3D/4D are a bright glass-edge material (thicker,
  at `board.boundary_opacity`) above the quiet face and interior lattice.
  While mostly opaque (alpha ≥ 0.5) they write depth, so a piece behind a
  3D front edge stays behind it instead of being painted over the edge.
  Pixel acceptance (windowed; the headless Godot lane draws nothing):
  `godot --path godot/Tet4D.Godot --script tests/run_board_edge_occlusion_acceptance.gd`
  renders an active slab behind the nearest 3D edge and fails if the edge
  pixels change. It fails (10% of edge pixels kept) with the depth write
  removed and passes (100%) with it.
- Captures: `docs/design/screenshots/graphical_language_p1/`, taken through
  normal startup at 1440×900 with registry defaults (no style preset). Same
  seeded game, default `luminous` versus `plain`.

### P2 — Shell skin
- `luminous` panel styling: corner radius, soft border, lift; type scale;
  keycap chips; amber selection; stat-card styling for Score, Lines and
  Level in their *current* positions.
- Files: `scripts/ui/style/shell_design_tokens.gd`,
  `shell_control_style_applier.gd` and the theme `.tres`.
- Acceptance: side-by-side captures; layout lock test unchanged and green.

**P2 as built (2026-11-24):**
- The skin lives in `ShellControlStyleApplier._flat_box`, the one place
  every StyleBox is made. Under `luminous` (and not High Contrast) corner
  radii step up (panel 4→10, control 3→6, keycap 2→5, emphasis 6→12) and
  `grid.minor`/`grid.major` borders resolve to a soft border (elevated
  surface lightened by `LUMINOUS_BORDER_LIFT`). Accent, focus and state
  borders are unchanged.
- Cockpit cards that use the `ViewportFrame` variation (NEXT, HOLD, control
  strips, 4D basis panel) take `background.panel`; `GameArea` keeps the board
  fill.
- Selected and pressed buttons use a dark amber fill (`accent.soft`), an amber
  border and `text.primary`. Section titles are white (`hint.section`
  `#E6ECF5`; NEXT/HOLD/control titles take `text.primary`).
- Content margins and font sizes are untouched. `test_locked_shell_layouts.gd`
  and `test_typography_lock.gd` pass unchanged.
- Captures: `docs/design/screenshots/graphical_language_p2/`.

### P3 — Cockpit and menu redesign
- Depends on Explorer Phase 3 (`docs/plans/explorer_cockpit_unification.md`)
  being merged first, because both edit `live_cockpit.gd`, `replay_hud.gd`
  and `practice_explorer_panel.gd`.
- Depends on the owner's main-menu decision (open item in the spec).
- Top bar (brand, Play / Explore / Settings / Help, 2D/3D/4D group); right
  column with NEXT, HOLD and stats; footer with the controls legend and the
  status line; the board as large as the window allows.
- Debug strings and the Recover / Fit View / Designer toolbar leave Play.
- One cockpit for 2D/3D/4D and Play/Explorer, implemented through the
  existing `LiveCockpit`, `CockpitLayoutPolicy` and `LiveInputContract`
  groups. Dimensions differ only in which groups and labels the descriptors
  provide.
- Re-baseline `test_locked_shell_layouts.gd` in this PR with the
  owner-accepted rectangles, keeping its reachability, no-clipping, focus and
  small-window checks.
- Retire the `plain` and `tron` themes; keep `diagnostic` and High Contrast.

### P4 — 4D views (deferred)
Tesseract overlay and projection views, after P3, as their own stage.

## Invariants for every phase

- No change to game rules, board coordinates, 4D slice membership or order,
  camera and basis, or input action semantics.
- Native and replay hashes match before and after for the same seed and
  inputs.
- High Contrast and Reduced Motion keep working in every theme.

## Programme placement

Phase III §9.1 (Professional UI review and correction) of
`professional_godot_game_programme.md`, priority P2, after Stage 57.
