# Accepted 2D / 3D / 4D gameboard visual direction

Role: design specification
Status: owner-accepted concept; runtime implementation pending
Decision date: 2026-11-22
Workstream: `docs/plans/dual_mode_godot_ui_redesign.md`
Existing authoritative implementation constraints: `docs/design/godot_visual_system.md`, `docs/plans/gameboard_visual_language_design.md`, `docs/architecture/configurable_plain_boards_and_4d_layout.md`

## Decision and scope

This specification records the user's visual acceptance of the revised **2D** and **3D** game screens and the correction to the **4D** representation. It supersedes the initial 2026-11-22 plain/tron SVG concept mockups as design references, **not** the existing gameplay/rendering contracts.

The accepted direction is **one visual language, three geometric presentations**. Screens, component semantics, placement policy, accessibility and input ownership are shared. UI skin remains selectable with existing IDs `plain` and `tron` (plus `diagnostic`); a skin does not define a different gameplay geometry.

**Confirmed constraints:**
- The gameboard, not the HUD or decorative panels, is the clear focal object.
- Individual occupied cells are prominent, solid, sharply bounded and legible at ordinary gameplay scale.
- The palette is controlled: dark charcoal/blue-black, blue-grey structure, warm off-white labels, subdued gameplay colours and one restrained interface accent. No noisy rainbow chrome, blanket cyan neon, high bloom, or a flood of borders.
- Gameboard presentation must remain diagrammatic and geometrically truthful. A visual mockup cannot override core game semantics.
- 4D is **a set of 3D board slices**, not a single 3D box labelled 4D or a nested-cube/hypercube spectacle.
- **Do not separate 4D gameboard slices into independent app cards/panels.** Each slice is its own volumetric region but the set is rendered as one coherent playfield in one viewport, with common projection/scale and an intelligible W order.

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
- 4D cells: **the same 3D voxel primitive**, reused without shrinking/flattening into a 2D tile merely because it belongs to another W slice.
- Locked/active cells have identical geometric envelopes in 3D and 4D. Display styling changes emphasis, never occupancy or geometry.
- A grid is a board lattice, not a collection of isolated cell-edge fragments.

### Shell

Use a compact navigation/title row, a secondary score/next/hold rail and short Piece/View contextual controls. The board gets first claim on width and height. Play and Explorer use the same control language but have different permissions and context. Never draw pretend keybindings in screenshots: screen hints must come from the authoritative input contract. Decorative chrome and oversized stats must not crowd the board.

## 2. Live 2D — accepted presentation

- Default board remains **10 × 20**; all other valid configured sizes continue to work.
- Single tall, flat, centred board occupying the main viewport.
- Occupied squares have strong outer and inner contours; locked stacks read as coherent patterns of distinct squares.
- Active piece visually dominates, with landing ghost visible but not confusing.
- Spatial reference needs no 3D shadows, tilted surfaces, perspective lattice or camera widget.
- NEXT, HOLD and score remain accessible outside the board.
- Use the accepted 2D screenshot as an aesthetic reference, not as evidence of exact state, scores, controls or piece selection.

Acceptance: user can resolve every occupied cell and active-piece shape immediately at normal scale; shrinking the board to fit ornamental HUD is a failure.

## 3. Live 3D — accepted presentation

- One three-dimensional volume with a stable exterior three-quarter camera view, Y-down gravity, and an explicit axis gizmo.
- Camera projection continues to respect the existing canonical view/fit contract.
- Every voxel has a solid top/front/side reading, prominent but non-glaring edges, clear foreground/background occlusion and stable depth contrast.
- Active piece has bounded visual emphasis; settled cell stack is quieter but *each cube* stays parseable.
- Rear-face grid, bounds and floor preserve position without obscuring front voxels.
- NEXT/HOLD and controls stay away from the volumetric content.

Acceptance: the active 3D polycube's extension direction and each locked cube are identifiable without needing to orbit the camera.

## 4. Live 4D — the governing correction

Let a 4D state be `B ⊂ ℤ⁴`. For an identity W view, the displayed 3D slice at W index `w` is

`B_w = {(x,y,z) | (x,y,z,w) ∈ B}`.

In an arbitrary basis-derived view, use the current authoritative signed slice-axis coordinate rather than assume the slice axis is always canonical W. The 3D visible basis and signed labels derive from that same view state.

- Render **one 3D board per valid signed slice index**, each using the **same 3D cell renderer and visual grammar** as Live 3D.
- All visible slice volumes are placed inside **one 4D gameboard viewport**. No separate self-contained cards, unrelated dashboards, per-slice control strips or individually framed application windows.
- Each slice must have a **consistent orientation, orthographic scale, camera frame, grid style, voxel scale, perspective convention and cell material**. Changing view basis rotates/transforms all slice presentations coherently.
- Preserve the currently governed **adaptive fitted matrix** (`configurable_plain_boards_and_4d_layout.md`): the number of columns and rows depends on layer count and viewport, stable row-major slice order, complete visibility at Fit, bounded inter-volume gutters. A horizontal row in the concept example is not a hardcoded layout rule.
- 3D volumes retain their own structural outer box edges because they identify board boundaries; that is **not** permission to encase each slice in a different decorative panel.
- The whole matrix has one common visual envelope/background and optional subtle W-order connection/guide line; no artificial nested 3D boxes or blended 4D projection pretending to display a single 3D occupancy.
- A signed W/slice-axis label must be attached to each actual 3D volume and readable in ordinary and high-contrast modes.
- Every 3D slice intersected by the **active 4D piece** receives active emphasis. It is incorrect to highlight only one slice when the piece spans several slice coordinates.
- The locked stack, active cells and ghost in a slice are exactly its own projections, not copies of neighboring slices. A shape may have occupied cells on several W slices; no invented cross-slice connecting cubes.
- Semantic slice indices and axis labels are part of understanding 4D, not ornament.

For example a 4-slice board may appear as four identically oriented 3D cube volumes arranged horizontally, sharing a single playfield background and fitted camera. A taller viewport may prefer a 2×2 arrangement. Neither case implies independent panel membership or separate game modes.

### Invariants to test

1. A cell `(x,y,z,w)` is drawn exactly in the volume corresponding to its basis-derived slice coordinate.
2. Visually adjacent 3D slices may be separated by a small fitted gutter, but are not independent UI viewports or detached apps.
3. W order remains predictable during camera movement, window resizing and basis changes.
4. Each slice uses one local renderer transform; active/locked/ghost cell geometry is identical to 3D.
5. If an active 4D piece spans several W slices, all of those slices are emphasized.
6. All slices fit at Reset/Fit on supported viewports; if zoomed/panned manually, user can always restore the complete matrix.
7. The visual layer does not alter native game state, movement/rotation/transport, session hashes, study measures or accessibility semantics.

## 5. UI reference artifacts

The following are original, schematic SVGs representing the accepted geometry. They are **design references**, not pixel-perfect copies of user-approved raster images, screenshots of Godot, or evidence that current code matches the design.

- [2D board design](mockups/accepted_2d_gameplay.svg)
- [3D board design](mockups/accepted_3d_gameplay.svg)
- [4D multi-3D-slice board design](mockups/accepted_4d_slice_matrix.svg)

The two earlier `dual_mode_plain_concept.svg` and `dual_mode_tron_concept.svg` illustrations are rejected historical concepts. Do not use them for implementation acceptance.

## 6. Engineering mapping and acceptance gate

Affected existing Godot owners to investigate, not replace uncritically:

- `godot/Tet4D.Godot/scripts/ui/replay_visuals.gd` and the active renderer/material owners for 2D and 3D cell/board appearance.
- 4D slice mapper, basis/view transforms, board bounds and fitted matrix layout; preserve a shared coordinate model.
- `scripts/ui/live_cockpit.gd`, `replay_hud.gd`, `responsive_panel_policy.gd` and `scripts/ui/style/*` for HUD/component hierarchy.
- `godot/Tet4D.Godot/config/shell_theme_palettes.json`, shell settings registry and presentation profiles for semantic roles, persistent values and accessible overrides.

Do one baseline capture for each dimension, then change 2D/3D material and board legibility, then 4D rendering via reuse and matrix-fit review, finally HUD and two theme skins. Each stage: existing automated regression tests plus real rendered snapshots; verify 680×520, 960×640, 1280×800, 1600×960, 1920×1080 and custom W counts, including 1, 4, 7 and 8 where admitted.

Human design acceptance must compare: board occupancy of the screen, legibility of individual cubes, neighbouring slices and W labels, piece orientation, ghost distinction, missing/clipped UI, style noise, high contrast and reduced motion. Existing semantics and accepted infrastructure are nonnegotiable.

This is a **design specification and implementation target**. No claim of completed Godot rendering implementation is made by publishing it.
