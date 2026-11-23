# Accepted 2D / 3D / 4D gameboard visual direction

Role: visual-language reference (non-semantic)
Status: owner-accepted visual references; application to existing renderer pending
Decision date: 2026-11-22
Workstream: `docs/plans/dual_mode_godot_ui_redesign.md`
Existing authoritative implementation constraints: `docs/design/godot_visual_system.md`, `docs/plans/gameboard_visual_language_design.md`, `docs/architecture/configurable_plain_boards_and_4d_layout.md`

## Decision and scope

This document specifies **appearance only**. It records approved visual qualities
of the 2D and 3D concept images and the requirement that the 4D styling respect
the existing multi-3D-slice presentation. It rejects the earlier conceptual
mockups as *style references* only.

**It neither establishes nor replaces any gameboard semantics or geometric
presentation contract.** Every actual displayed coordinate, board extent,
slice-membership rule, signed basis, placement, cell shape, camera projection,
orientation, layout, piece geometry, movement, collision, topology and
gameplay operation is determined by its existing authoritative owner.

The approved visual qualities are:

- **Cells read first:** occupied cells are pronounced, with crisp contours and
  strong perceptual separation; active, locked and ghost states remain distinct.
- **Board first:** visually emphasize the actual rendered board and reduce the
  visual weight of menus, panels and decorative chrome.
- **Restrained palette:** dark neutral surfaces, desaturated structure, limited
  interface accent, legible typography and subdued effects.
- **Consistent dimensional styling:** 2D retains its existing flat board, 3D
  retains its existing volumetric board, and 4D retains its actual collection
  of 3D slice presentations; visually style each as rendered by the game.
- **Unified shell:** do not wrap already rendered 4D slices in separate,
  competing application cards. This is a *chrome treatment*, not a requirement
  to alter slice layout, viewport architecture or coordinate mapping.

The images in this folder are **aesthetic moodboards**, not authoritative
screenshots, test fixtures, example game states, keybinding specifications or
geometric layout diagrams. Differences between an image and the actual board
are resolved in favour of the existing runtime/gameboard contracts, never by
modifying the gameboard to make it resemble a picture.

### Unchanged owners

- The relevant `docs/rds/*`, native deterministic core, accepted topology and
  movement contracts own gameplay and board semantics.
- The existing Godot coordinate mapper, scene renderer, view-basis and camera
  contracts own visual projection and coordinate placement.
- `docs/architecture/configurable_plain_boards_and_4d_layout.md` and later
  owning contracts own 4D slice placement and adaptive fitting.
- `docs/design/godot_visual_system.md` and
  `docs/plans/gameboard_visual_language_design.md` retain current visual
  implementation rules. This document supplies the approved *style target*
  within those rules; it does not supersede them.
- `docs/plans/dual_mode_godot_ui_redesign.md` owns staging of style work,
  not new board behavior.

## 1. Visual grammar shared by all dimensions

### Priority hierarchy

1. Active piece: solid material, individual cell contours immediately visible, subtle light-facing bevel/face shading.
2. Locked stack: individually distinguishable, quieter saturation/brightness, no artificial gaps.
3. Ghost/landing projection: dashed or outlined transparent volume, weaker than active, distinguishable from lattice and locked stack.
4. Active 3D volume / active W slice frame.
5. Board bounds and outer wireframe.
6. Internal lattice / rear-face depth cues.
7. Gravity floor / environment.
8. Decorative shell.

The first three layers must remain legible without relying on hue alone. No grid or visual effect is drawn through filled cubes. Board boundaries should be substantial but not brighter than the active piece.

### Colour roles (reference direction, not a new runtime palette)

| Purpose | Suggested concept swatch | Requirement |
| --- | --- | --- |
| Main background | `#0B1119` | near-black charcoal, low texture |
| Background in gameboard | `#080E16` | deeper than shell |
| Sidebar/panel | `#17222E` | subdued; no stacked nested-card borders |
| Text | `#F1F0E9` | warm neutral white |
| Secondary text | `#A9B7C5` | readable but below primary |
| Structural grid | `#536B7E` | visible, desaturated, thinner than cells |
| Board boundary | `#97AABD` | stronger than grid, weaker than active |
| Active material | `#F0B65C` | controlled warm amber with pale edges |
| Locked material | `#6A8398` | muted steel; optional subdued piece-family colours |
| Highlight / selected | `#E5BA75` | single interaction accent, limited use |
| Ghost | outline/alpha of pale neutral | never just a dim fill indistinguishable from locked |

These are **design swatches for comparisons**, not changes to `shell_theme_palettes.json`, global style IDs or semantic color owner. The actual palettes must preserve existing role semantics, user presentation profile and High Contrast overrides. Compare candidate colours on real Godot captures before adoption.

### Geometry

- 2D squares: flat, large, filled, crisp contours; minimal corner radius; cell edges remain visible inside a multi-cell piece.
- 3D voxels: cubical body, consistent scale, top/front/side face brightness, bounded edge contrast; no excessive emissive halos or fake depth.
- 4D cells: visually match the existing 3D cell rendering grammar where corresponding 3D slice cells are visible; do not change their geometry or underlying renderer contract.
- Locked/active cells have identical geometric envelopes in 3D and 4D. Display styling changes emphasis, never occupancy or geometry.
- A grid is a board lattice, not a collection of isolated cell-edge fragments.

### Shell

The cockpit layout itself is **reopened for design** by owner decision on
2026-11-23. The old side-rail/4D-split/menu ordering is a baseline, not the
permanent target; no replacement placement is accepted yet. The concept images
illustrate visual hierarchy, **not** a required top navigation row or a
particular arrangement of NEXT/HOLD, Piece/View or settings.

Use **one shared cockpit infrastructure across 2D, 3D and 4D**, with Play and
Explorer composing the same UI modules and styling. Differences in the visible
actions, controls and arrangement are selected by *capability/configuration*
and responsive content measurement, never by separate per-dimension cockpit
implementations. Existing Play/Explorer command meaning and native semantics
remain unchanged. The board gets first claim on legible space; controls,
NEXT/HOLD and status remain accessible. Key hints derive from the input contract
rather than concept art; decorative chrome must not crowd the board.

## 2. Live 2D — accepted visual treatment

- The flat 10 × 20 example in the approved picture is not a board-size directive. Render whatever valid size the existing gameplay configuration specifies.
- Single tall, flat, centred board occupying the main viewport.
- Occupied squares have strong outer and inner contours; locked stacks read as coherent patterns of distinct squares.
- Active piece visually dominates, with landing ghost visible but not confusing.
- Use flat-looking materials and crisp flat outlines; do not add visual decoration that implies nonexistent depth or changes the existing 2D rendering model.
- NEXT, HOLD and score remain accessible outside the board.
- Use the accepted 2D screenshot as an aesthetic reference, not as evidence of exact state, scores, controls or piece selection.

Acceptance: user can resolve every occupied cell and active-piece shape immediately at normal scale; shrinking the board to fit ornamental HUD is a failure.

## 3. Live 3D — accepted visual treatment

- Style the actual 3D board and canonical camera/view presentation already provided by the renderer. Do not introduce new camera, gravity, orientation, axis, or projection behavior.
- Every voxel has a solid top/front/side reading, prominent but non-glaring edges, clear foreground/background occlusion and stable depth contrast.
- Active piece has bounded visual emphasis; settled cell stack is quieter but *each cube* stays parseable.
- Rear-face grid, bounds and floor preserve position without obscuring front voxels.
- NEXT/HOLD and controls stay away from the volumetric content.

Acceptance: the active 3D polycube's extension direction and each locked cube are identifiable without needing to orbit the camera.

## 4. Live 4D — visual language over existing semantics

The actual 4D gameboard is already represented by a set of rendered 3D slices
under the owning gameboard, projection and adaptive-layout contracts. That fact
is **context for styling**, not a new definition or replacement algorithm.

For every slice, apply the same perceptual principles used for 3D: clear
individual cubes, legible occupied structures, quiet lattice and depth cues,
and distinction between active/locked/ghost appearance. The 4D playfield
as a whole should look continuous and coherent rather than like a row of
separate app widgets. Keep the surrounding chrome visually quiet.

**No changes are authorized to:**

- the definition or number of slices, their indices, membership or ordering;
- signed view basis, projection, slice positions, spacing or adaptive
  row/column arrangement;
- camera orientation, fitted bounds, transforms, pan/zoom or axis controls;
- piece or cell geometry, visibility/occlusion truth, active-piece membership,
  state and input contracts;
- W-axis labels or other semantic indicators, except cosmetic legibility;
- internal renderer structure, viewport ownership, physics, topology,
  recording or replay.

Visual emphasis must be applied only to states the existing runtime exposes.
Never infer active-slice membership, duplicate cells, create cross-slice
connections or synthesize a single 3D substitute from a mockup.

The 4D SVG is a *visual illustration of cell prominence and shared shell
treatment*, not a prescription for four columns, a fixed W ordering, a
particular camera, a 3D projection model, fixed cell sizes or layout. The
actual screenshot produced by the running game determines what is being styled.

### Visual-only acceptance checks

1. Same state/board dimensions and same cells before and after theme change.
2. Same slice layout, camera framing and view basis, within normal rendering
   tolerance; no redesign-triggered relayout.
3. Same ability to distinguish adjacent, active, locked and ghost cells.
4. No per-slice decorative card that obscures the existing board.
5. Improved board/cell legibility at all supported window sizes, with standard
   and High Contrast options.
6. No change to game input mappings, native state, hashes, traces, rotation,
   collision, topology or study records.

## 5. UI reference artifacts

The following are original, schematic SVGs illustrating the accepted visual style. They are **design references**, not pixel-perfect copies of user-approved raster images, screenshots of Godot, or evidence that current code matches the design.

- [2D board design](mockups/accepted_2d_gameplay.svg)
- [3D board design](mockups/accepted_3d_gameplay.svg)
- [4D multi-3D-slice visual treatment (illustrative layout only)](mockups/accepted_4d_slice_matrix.svg)

The two earlier `dual_mode_plain_concept.svg` and `dual_mode_tron_concept.svg` illustrations were rejected and removed from this branch. They are not implementation references.

## 6. Engineering mapping and acceptance gate

Affected existing Godot owners to investigate, not replace uncritically:

- `godot/Tet4D.Godot/scripts/ui/replay_visuals.gd` and the active renderer/material owners for 2D and 3D cell/board appearance.
- Existing 4D slice projection, basis/view transforms, board bounds and fitted matrix layout are **read-only dependencies** to inspect and protect, not targets for redesign.
- `scripts/ui/live_cockpit.gd`, `replay_hud.gd`, `responsive_panel_policy.gd` and `scripts/ui/style/*` for HUD/component hierarchy.
- `godot/Tet4D.Godot/config/shell_theme_palettes.json`, shell settings registry and presentation profiles for semantic roles, persistent values and accessible overrides.

Do one baseline capture for each dimension, then change 2D/3D material and board legibility, apply equivalent visual styling to the existing 4D slice renderer *without changing slice geometry or layout*, and finally restyle HUD and the two theme skins. Each stage: existing automated regression tests plus real rendered snapshots; verify 680×520, 960×640, 1280×800, 1600×960, 1920×1080 and custom W counts, including 1, 4, 7 and 8 where admitted.

Human design acceptance must compare: board occupancy of the screen, legibility of individual cubes, neighbouring slices and W labels, piece orientation, ghost distinction, missing/clipped UI, style noise, high contrast and reduced motion. Existing semantics and accepted infrastructure are nonnegotiable.

This is a **design specification and implementation target**. No claim of completed Godot rendering implementation is made by publishing it.
