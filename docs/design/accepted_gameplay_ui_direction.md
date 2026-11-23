# Accepted 2D / 3D / 4D gameboard visual direction

Role: visual-language reference (non-semantic)
Status: owner-accepted visual references; application to existing renderer pending
Decision date: 2026-11-22
Workstream: `docs/plans/unified_cockpit_visual_redesign.md`
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
- `docs/plans/unified_cockpit_visual_redesign.md` owns staging of style work,
  not new board behavior.

## Visual-language signature — Luminous Geometric Instrument (2026-11-23 clarification)

**Art-direction statement:** *A precise mathematical instrument with the visual presence of a modern puzzle game.* The board is the subject; the cockpit is the instrument panel that makes the board understandable. The aim is **diagrammatic dimensional clarity with restrained, tactile illumination**, not a sci-fi simulation console or a decorative neon arcade.

This is an owner-directed *appearance and information-hierarchy* target, not a new renderer, topology, gameplay, UI-capability, or 4D mapping authority. Apply it only through the existing semantic roles, presentation profiles, rendering owners and shared cockpit layout policy. All numerical values or named colours below are comparison targets for screenshots, not new executable constants or additional configuration settings.

### A. Image hierarchy and information architecture

At first glance the player should see, in order:

1. **The active piece and its individual constituent cells**, distinct from every other object.
2. **The occupied stack and predicted landing**, with each cell individually resolved.
3. **The containing board volumes, their depth/orientation and current layer emphasis.**
4. **The immediately necessary state**, e.g. score/clears, pause, NEXT/HOLD where supported, active dimension and mode.
5. **Piece movement, piece rotation, camera/view and W-slice controls** as separately labeled groups.
6. Optional settings, explanations and diagnostics.

The primary board claims the main visual field. The HUD supports it using compact rails/decks chosen by the *existing responsive layout engine*. The concept images' large headers, nested cards, invented scoring values or footer key legends are **not** pixel/layout targets. A single cockpit infrastructure exposes common modules using current dimension/activity capabilities and current runtime binding labels. Unavailable capabilities are absent or disabled rather than shown as decorative fake buttons. Preserve keyboard focus order, visible focus, modal reachability, current menu routes and appropriate touch targets.

### B. Palette and contrast behaviour

The reference mood is **deep charcoal / desaturated midnight slate**, warm off-white text, blue-gray board scaffolding, and a **single controlled warm accent** (amber) for primary interaction or active-element emphasis. Per-piece colour may exist to distinguish pieces and state, but it is *board information*, not license to tint every panel. Muted steel-blue locked cells are the default image mood; any piece-family colour on locked cells stays subordinate to the active object. The alternative `tron` skin may use a cooler cyan interaction accent **without changing board logic or introducing competing light sources**. `plain` remains the low-noise Instrument default; `diagnostic` and independent High Contrast overrides remain supported.

Use the current project's semantic palette mapping. The colour proposals already recorded below (`#0B1119`, `#080E16`, `#17222E`, `#F1F0E9`, `#A9B7C5`, `#536B7E`, `#97AABD`, `#F0B65C`, `#6A8398`) are *reference swatches* to compare on genuine Godot captures. A large collection of saturated hues, glowing cyan panels, intense purple frames and permanent orange borders is specifically **not** the accepted aesthetic.

A desirable luminance order is: active cell body/edge > relevant locked cell contour > active slice/boundary > external wireframe > internal grid > dark board > dark cockpit background. Text and actual affordances must still meet the existing accessibility targets. Do not achieve this order by washing out locked cells or erasing distant slices. Distinguish state through edge, opacity, label and shape in addition to hue.

### C. Materials, edges and lighting

**2D material:** flat filled square; firm uninterrupted outer silhouette and perceptible inner seams between occupied cells; very small corner radius or none; restrained internal value gradient if it does not imply false 3D depth. A multi-square piece must read as one shape *and* individually occupied cells.

**3D material:** visually solid cubical voxels with a gentle, consistent difference among top/front/side faces; controlled exterior edges; no shiny photorealistic reflection, glass, hollow cages or extremely soft rounded toy shapes. The accepted Godot camera/projection, cube envelopes and occlusion remain unchanged. The existing depth-written active/locked compositing and presentation-controlled settled opacity remain authoritative.

**4D material:** exactly the same cubical vocabulary, applied to **each actual 3D slice volume**. The entire slice matrix shares one gameplay canvas and visual grammar. Individual slice boxes and signed labels must be legible, but **never wrap each slice in a separate application card or independently designed miniature game screen**. Do not force all slices into one continuous lattice; each 3D volume retains its real spatial bounds, and the adaptive layout owns the gaps and row/column arrangement. Do not approximate 4D by one giant cube, nested cubes, a projection-fake tesseract or an always-horizontal strip of three fixed slices.

**Edge grammar:** an occupied cell's physical outline is crisp and stronger than its local internal lattice; outer board wireframe remains continuous and cleaner than the internal grid. Avoid drawing the lattice through foreground filled cells. Keep the current Godot border/full/none lattice semantics and active/locked/ghost mesh geometry.

**Emission:** reserved for the currently manipulated piece and rare action feedback; use a slight halo, if any, not enough to bleed adjacent cells together. Locked cubes are quieter, not unlit. The currently active layer is emphasized by its existing frame treatment and runtime state; do not invent extra illuminated W slices. Ghost is an intentional translucent/outlined predictive form, not a duplicate opaque piece or a generic dim cell.

### D. Typography, geometry and cockpit components

Use the established Godot font and effective-typography scale rather than introducing a separate font library: a clear display title, compact section headings, readable labels and restrained numerical emphasis. Use tabular/monospaced presentation only where it serves coordinates, scores, seeds, hashes or numeric status. A large “Tet4D” masthead in the illustrations is branding, **not a requirement to consume that much gameplay space**.

Surfaces: near-black background, subtly lifted slate cockpit panels, thin quiet borders; intentional negative space rather than repeated bright card frames. Buttons have comfortable targets and states, with selection indicated by more than colour. Bottom/side control modules share one component geometry. Visually distinct control groups correspond to Piece, View/camera and Piece State; Explorer extends them without a bespoke design language. Use the current shared responsive/sizing policy and presentation settings for density, not arbitrary screen-relative artboard coordinates.

The geometry of a panel is subordinate to the geometry of a cell. A cell may have a stronger edge than a button; that contrast is deliberate. Board edges and active frames are functional orientation aids, not decoration. Chamfers, small accent rules and angular cuts may appear rarely in the more stylized theme; they must not make the interface busier than the game.

### E. Dimensional grammar and key corrections from generated images

| Mode | Visual identity | Specific rejection |
| --- | --- | --- |
| **2D** | one flat rectangular grid with strong discrete squares, active/locked/ghost hierarchy | decorative depth effects, losing cell seams, fixed image board dimensions |
| **3D** | one exterior-view voxel volume, strong edge/face readability and quiet enclosing structure | glass cubes, internal walls masquerading as cells, perspective/camera changes for cosmetic fit |
| **4D** | an **adaptive matrix of actual 3D slice volumes**, consistent camera-relative orientation, signed slice labels and selective runtime-derived active emphasis; one unbroken **UI canvas** | one 3D box pretending to be 4D, overlapping/nested cube illustrations, three separate UI cards, or manually fixed horizontal slice layout |

**No triptych product screen.** A three-panel 2D/3D/4D collage is a comparison of design language, not a requirement that all modes appear concurrently. Normal play shows the selected dimension in the shared cockpit.

**No invented visual semantics.** Generated illustrations may have wrong piece shapes, block stacks, scores, key assignments, position of a ghost, W ordering, gravity, rotations and even geometrically impossible 3D structures. Those details must be discarded. The running Tet4D state and input contracts decide all visible game data.

### F. Design acceptance and concrete rejection tests

Capture representative *real* 2D, 3D and 4D live play, including configured small/large boards, alternate W counts, active pieces spanning multiple W slices and the currently available camera-relative views. Compare both approved skins at default/enlarged UI scale and High Contrast. The image treatment passes only if:

1. At ordinary fitted size the viewer can count the active piece's cells; each occupied cell has a clear boundary; adjacent locked cubes do not melt into one block.
2. A 3D piece's extension direction and gravity orientation are clear without compulsory orbiting. Lattice and rear faces support orientation without obscuring foreground cells.
3. 4D reads as **several real 3D slice volumes in one composition**. W labels are readable, active occupancy is accurate, no slice is lost or duplicated, and the adaptive layout/projection is unchanged.
4. Mode, status, NEXT/HOLD and actual available Piece/View controls remain reachable and legible while the *rendered* board remains dominant.
5. Real theme transitions do not alter geometry, game state, inputs, camera/basis, slice arrangement, deterministic hashes or Explorer behavior.
6. No persistent bright outlines on every panel, excessive glow, high-saturation multi-colour chrome, invented orientation arrows, fake keys or decorative controls.
7. Both Instrument and Vector Arcade are clearly related in materials, spacing, cell structure and control semantics; their differences are palette/finish, not duplicate UI implementations.

**Implementation sequence:** first preserve screenshot and code baselines (R0), then board/cell appearance in 2D/3D (R2), inherit the same appearance across the existing W-slice renderer (R3), and only then evaluate a revised common cockpit composition and final finish through the separately gated R4/R5/R6 work. The October layout lock remains the tested baseline until an explicit new layout approval and its regression update. The selected look alone does not approve a replacement layout or modification of 4D semantics.

---

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
