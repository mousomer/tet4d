# Explosion Refactor Ownership Split

Role: authority  
Status: active  
Source of truth: this file for locked-cell explosion refactor ownership and staged extraction order  
Supersedes: none  
Last updated: 2026-04-24

## Purpose

This document defines the locked-cell explosion refactor inventory, the staged
target split for simulator/shared presentation/shared controls/shared runtime,
and the currently landed stage baseline.

This is an extraction map only.

Stages 1 through 7 are now complete.

This document remains the closeout authority for the landed ownership split,
the remaining follow-up risks, and the explicitly deferred non-goals.

Stage 1 planning and inventory establishment must **not**:
- move widgets,
- rewrite render behavior,
- change runtime semantics,
- retarget endgame,
- retarget explorer,
- or introduce new feature behavior.

The target architecture is:

1. shared board presentation,
2. shared controls,
3. shared explosion runtime,
4. thin simulator, explorer, endgame, and gameplay adapters.

The key rule is:

> The simulator must become an authoring surface, not the long-term owner of
> shared controls, shared board presentation, or shared explosion runtime
> behavior.

---

## Refactor Principles

### Shared code must not remain simulator-owned by accident

If a feature is intended to be reused by simulator, explorer, endgame, or
gameplay, it must not stay under simulator-owned UI code merely because that is
where it was first added.

### Adapters must stay thin

Simulator, explorer, and endgame may each provide their own launch-specific
inputs and chrome, but they must not own separate copies of:
- control behavior,
- board presentation logic,
- explosion runtime logic,
- or default-application logic.

### Defaults and runtime must stay separate

Persistent saved defaults are not runtime session state.

Runtime session state must never be persisted.

### Extraction order matters

Controls must be extracted before board presentation.
Board presentation must be extracted before endgame/explorer thinning.
Gameplay reuse must come last.

---

## Closeout Status

Stages completed:
- Stage 1: inventory / authority / extraction plan establishment
- Stage 2: shared controls extraction
- Stage 3: shared board-presentation extraction
- Stage 4: shared runtime-default builder and defaults/runtime boundary split
- Stage 5: explorer thinning
- Stage 6: endgame shell thinning
- Stage 7A/7B/7C: low-risk gameplay presentation reuse

Final landed architecture:
- shared controls live under `src/tet4d/ui/pygame/controls/`
- shared board presentation lives under
  `src/tet4d/ui/pygame/board_presentation/`
- shared explosion runtime/default application lives under
  `src/tet4d/ui/pygame/locked_cell_explosion/`
- simulator is the first adapter/authoring consumer of those shared layers
- explorer is a thin topology/state injection adapter
- endgame is a thin shell adapter around the shared runtime/view
- gameplay now consumes shared board-presentation seams where the reuse is
  low-risk and clearly presentation-only

---

## Current Ownership Inventory

## Simulator Surface And UI Logic

Current primary owner:

- `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`

Currently owned there:

- `StandaloneExplosionSurfaceState`
- simulator row inventory and row labels
- dynamic row visibility
- simulator state normalization
- persisted-default application into simulator state
- topology/snapshot source selection
- simulator source-cell construction
- simulator config construction
- explorer-launched simulator state construction
- controller restart
- row activation
- dropdown values, dropdown open/close state, hover state, and selection
- numeric text editing, slider drag state, clamping, and display text
- row layout, wrapped label/value text, footer/status text, and preview layout
- pointer and keyboard handling for rows, controls, dropdowns, save, restart,
  and back
- simulator preview draw routing
- simulator save action through `save_standalone_explosion_defaults`

This file remains the main closeout monolith risk by size, but not by the same
ownership boundary as before.

At closeout it primarily mixes:
- simulator adapter responsibilities,
- simulator row inventory/domain mapping,
- simulator launch/status/footer composition,
- and simulator event plumbing over shared controls/runtime/presentation.

It no longer owns the generic controls package, the shared board-presentation
authority, or the shared runtime-default builder.

---

## Dropdown, Numeric Controls, Rows, And Wrapping

Current owners:

- `src/tet4d/ui/pygame/controls/`
- `src/tet4d/ui/pygame/ui_utils.py`
- `src/tet4d/ui/pygame/render/gfx_game.py`
- `src/tet4d/ui/pygame/render/panel_utils.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`

Current split:

- Stage 2 is now landed: `controls/layout.py`, `controls/dropdown.py`, and
  `controls/numeric.py` own the extracted generic row-layout, dropdown,
  hit-testing, numeric text-entry, slider, and stepper semantics.
- `ui_utils.py` provides reusable primitives such as `compute_slider_row_layout`,
  `draw_value_slider`, text fitting, wrapping, panel frames, and gradients.
- `gfx_game.py` owns normal menu/settings row rendering and slider use for game
  menus.
- `panel_utils.py` owns gameplay side-panel grouping and presentation only, not
  interactive controls.
- `surface.py` now acts as the simulator adapter for row inventory,
  row-to-domain mapping, simulator callbacks/actions, preview composition, and
  simulator-specific status/footer text while still owning simulator state
  fields that the extracted helpers operate on.

This is the current correct ownership baseline for Stage 2. Follow-up stages
must not drift generic control behavior back into `surface.py`.

---

## Board Presentation Logic

Current owners:

- `src/tet4d/ui/pygame/board_presentation/native_board.py`
- `src/tet4d/ui/pygame/board_presentation/gameplay_board.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/render.py`
- `src/tet4d/ui/pygame/front3d_render.py`
- `src/tet4d/ui/pygame/front4d_render.py`
- `src/tet4d/ui/pygame/render/gfx_game.py`
- `src/tet4d/ui/pygame/render/grid_mode_render.py`
- `src/tet4d/ui/pygame/render/board_boundary.py`
- `src/tet4d/ui/pygame/render/active_piece_projection_guides.py`
- `src/tet4d/ui/pygame/render/projected_occlusion.py`
- `src/tet4d/ui/pygame/render/w_movement_animation.py`
- `src/tet4d/ui/pygame/topology_lab/camera_controls.py`
- `src/tet4d/ui/pygame/input/camera_mouse.py`

Current split:

- Stage 3 is now landed: `board_presentation/native_board.py` owns the shared
  simulator-first native board preview facade, reuses existing `Camera3D` /
  `LayerView3D` behavior from `front3d_render.py` and `front4d_render.py`,
  and keeps grid/shadow/boundary/edge-grid/occlusion/trace/W-movement
  application under `src/tet4d/ui/pygame/board_presentation/` rather than
  simulator-local ownership.
- Stage 7 closeout is now landed: `board_presentation/gameplay_board.py` owns
  the gameplay-facing shared presentation entrypoints for low-risk
  grid/shadow/boundary-box/edge-grid seams, 4D W-movement style dispatch, 3D
  orthographic zoom-fit application, and 4D frozen-view snapshot copying.
- Grid modes are defined in engine UI logic and rendered through a combination
  of `gfx_game.py`, `front3d_render.py`, `front4d_render.py`, and
  `grid_mode_render.py`.
- `locked_cell_explosion/board_view.py` is now only a compatibility shim that
  re-exports `board_presentation.native_board.draw_native_board_view`.
- The canonical board boundary box lives in `render/board_boundary.py`, while
  board-presentation entry owns the application/routing of box/edge/grid
  semantics for simulator and the low-risk gameplay seams.
- Edge-grid and projected line occlusion still depend on lower-level render
  helpers in `grid_mode_render.py` and `projected_occlusion.py`, but
  application ownership now routes through `board_presentation/`.
- Trace rendering for explosion particles is currently in
  `board_presentation/native_board.py` for simulator board-native previews, in
  `locked_cell_explosion/render.py` for projected explosion render state, and
  in `front3d_render.py` / `front4d_render.py` for endgame traces.
- Camera behavior is split between gameplay render camera types
  (`Camera3D`, `LayerView3D`), topology-lab camera helpers, and mouse input
  helpers.
- W-movement presentation has a small reusable scale helper in
  `render/w_movement_animation.py`, with style selection/application now
  routed through shared board-presentation helpers for simulator and gameplay.
- 2D/3D/4D board-view conventions still rely on lower-level front-render
  helpers, but the shared application seams now live under
  `board_presentation/`.

This is now the correct closeout ownership baseline. Remaining deeper camera /
projection cleanup is intentionally deferred rather than half-migrated.

---

## Explosion Runtime Logic

Current owners:

- `src/tet4d/ui/pygame/locked_cell_explosion/model.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/controller.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/simulation.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/topology.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/audio.py`
- `src/tet4d/ui/pygame/locked_cell_explosion/defaults_store.py`
- `src/tet4d/ui/pygame/endgame_animation.py`

Current split:

- `model.py` owns config/state dataclasses, particles, trail samples, render
  particles, diagnostics dataclasses, constants, and normalization helpers.
- `controller.py` owns `LockedCellExplosionController`,
  `build_locked_cell_explosion`, stepping, audio aggregation, render-state
  projection, and kinetic-energy display accessors.
- `simulation.py` owns particle initialization, masses, kinetic energy,
  diagnostics, seam contact, boundary bounce/escape, particle collisions,
  elasticity, trace sample generation, and simulation stepping.
- `topology.py` owns explosion topology adapters over edge rules and explorer
  transport.
- `audio.py` owns aggregated explosion audio event filtering.
- `defaults_store.py` owns saved explosion-default coercion, serialization,
  load, and save through `state/menu_settings.json`.
- `endgame_animation.py` still owns endgame-specific shell/relic animation and
  live-subset selection, and calls the shared explosion controller for live
  locked-cell particles. Saved shared `endgame_live_cell_fraction` is the
  authority for the persistent live subset, the escaping debris population is
  the exact complement, and the visible handoff must keep survivors on the
  shared runtime layer continuously while the shell-owned overlay is limited to
  the escaping debris path. The endgame adapter may retune only the shared
  runtime's initial survivor seed so those particles stay board-tied through
  the rupture instead of reusing the generic outward explosion launch class.
  Any survivor-transition relics retained for compatibility must stay lazy/
  derived and must not become a second stored survivor layer. It must not
  become a second explosion runtime.

The runtime/default boundary is now explicit via
`locked_cell_explosion/runtime_config.py` and remains the correct closeout
baseline.

---

## Config And Launch Paths

Current owners:

- Config/default persistence: `locked_cell_explosion/defaults_store.py` plus
  engine runtime settings persistence in
  `src/tet4d/engine/runtime/menu_settings_state.py`
- Simulator save path: `surface.py` via
  `save_standalone_explosion_defaults` -> `save_mode_explosion_defaults`
- Simulator startup defaults:
  `build_standalone_explosion_surface_state` -> `mode_explosion_defaults`
- Explorer launch path:
  `src/tet4d/ui/pygame/topology_lab/explosion.py` injects sandbox topology and
  cells into `build_explorer_explosion_surface_state`
- Endgame launch path:
  `front2d_frame.py`, `front3d_game.py`, and `front4d_game.py` capture gameplay
  locked cells and saved defaults into `endgame_animation.create_snapshot`;
  `endgame_animation.build_endgame_animation_state` applies live-subset
  selection and calls `build_locked_cell_explosion`

The shared config authority is the saved explosion defaults path.
Endgame must not grow a second default-authority path.
Explorer must not grow its own default-authority path.
Simulator must not own serialization logic beyond invoking save actions.

---

## Target Ownership Split

## A. Shared Board Presentation

Target package:

- `src/tet4d/ui/pygame/board_presentation/`

This package must become the **authoritative application point** for board
presentation behavior.

It must not be a thin wrapper that simply forwards to scattered helpers without
clarifying ownership.

It should own:

- grid-mode rendering semantics and settings application,
- shadow-mode rendering semantics and settings application,
- canonical box/boundary rendering,
- edge-grid rendering,
- projected line occlusion integration,
- explosion trace rendering primitives,
- shared camera/view adapters and input state where they are visual-only,
- W-movement style application,
- shared 2D/3D/4D board-view conventions,
- presentation-only settings application for those features.

It must **not** own:
- gameplay legality,
- topology mutation,
- explosion physics,
- simulator authoring controls,
- endgame live-subset selection,
- runtime session ownership.

Likely source files to extract from or route through this bucket:

- `locked_cell_explosion/board_view.py`
- `locked_cell_explosion/render.py`
- `render/grid_mode_render.py`
- `render/board_boundary.py`
- `render/active_piece_projection_guides.py`
- `render/projected_occlusion.py`
- `render/w_movement_animation.py`
- relevant board-presentation seams from `gfx_game.py`,
  `front3d_render.py`, and `front4d_render.py`
- visual-only camera helper seams from `topology_lab/camera_controls.py` and
  `input/camera_mouse.py`

---

## B. Shared Controls

Target package:

- `src/tet4d/ui/pygame/controls/`

This package should own:

- dropdown widget behavior,
- slider controls,
- string/numeric entry controls,
- arrow/stepper controls,
- row layout,
- label/value wrapping and spacing,
- hit testing,
- open/close state,
- control-level pointer and keyboard semantics.

It must **not** own:
- simulator row inventory,
- domain-specific row mutation,
- save/restart/back commands,
- topology-specific dropdown option generation,
- simulator-only footer or status composition.

Likely source files to extract from or route through this bucket:

- generic row/dropdown/numeric portions of `locked_cell_explosion/surface.py`
- reusable primitives currently in `ui_utils.py`
- normal menu row rendering seams in `render/gfx_game.py`

After Stage 2, `surface.py` should still own only:
- simulator row inventory,
- row-to-domain mapping,
- simulator save/restart/back actions,
- simulator-only preview composition,
- simulator-only footer/status composition.

After Stage 2, `surface.py` must no longer own:
- generic dropdown semantics,
- generic numeric-edit state machines,
- generic row layout,
- generic wrapping/spacing logic,
- generic hit-testing/open-close logic.

---

## C. Shared Explosion Runtime

Target package:

- keep under `src/tet4d/ui/pygame/locked_cell_explosion/` for now,
  and split internally before creating any broader top-level runtime package

This package should own:

- session/controller state,
- particle state,
- seam transport,
- bounce/collision,
- masses,
- elasticity,
- diagnostics,
- kinetic energy,
- trace sample generation,
- runtime defaults application,
- topology adapter inputs for explosion simulation,
- audio event aggregation tied to explosion runtime events.

It must **not** own:
- simulator row controls,
- board widget layout,
- endgame shell/relic field chrome,
- explorer sandbox state,
- gameplay board ownership.

Files already mostly in this bucket:

- `locked_cell_explosion/model.py`
- `locked_cell_explosion/controller.py`
- `locked_cell_explosion/simulation.py`
- `locked_cell_explosion/topology.py`
- `locked_cell_explosion/audio.py`
- `locked_cell_explosion/defaults_store.py`

Files with runtime-adjacent code that must remain adapter-owned or move only
after a narrower seam exists:

- `endgame_animation.py` for live-subset selection and endgame shell/relic
  animation
- `surface.py` for simulator restart/config construction until simulator
  adapter seams are split

### Short-term note on `defaults_store.py`

`defaults_store.py` is currently the correct explosion-default authority.

However, it still imports UI view-mode enums.

That is acceptable short-term and must **not** get worse.
It must be cleaned before any attempt to move defaults deeper toward a more
engine-neutral ownership layer.

Until then:
- keep it in the explosion runtime/config area,
- do not spread that dependency pattern to more files.

---

## D. Thin Adapters

Adapters should own only launch-specific behavior.

### Simulator adapter
Should own:
- save button,
- authoring row inventory,
- authoring row-to-domain mutation,
- diagnostics expansion and display choices,
- snapshot-source authoring controls,
- simulator preview composition.

### Explorer adapter
Should own:
- topology/state injection,
- sandbox cell-source handoff,
- explorer status text and launch lifecycle.

### Endgame adapter
Should own:
- gameplay locked-cell source,
- live-subset selection,
- endgame mode/chrome,
- shatter/relic timing,
- endgame-only preset/speed/chrome data.

It must **not** own any separate board-presentation config application path.

### Gameplay adapter
Should later own only:
- selective reuse of shared board-presentation features from gameplay render
  loops, without moving gameplay rules or state ownership.

Adapter files that should stay thin or become thinner:

- `locked_cell_explosion/surface.py`
- `topology_lab/explosion.py`
- `front2d_frame.py`
- `front3d_game.py`
- `front4d_game.py`
- `endgame_animation.py`
- `front3d_render.py`
- `front4d_render.py`
- `render/gfx_game.py`

Gameplay reuse must be limited to **presentation seams only**.
Gameplay must not absorb simulator controls.
Gameplay must not absorb explosion runtime unless explicitly planned later.

---

## Wrong-Layer Inventory

High-priority wrong-layer or mixed-layer files:

1. `locked_cell_explosion/surface.py`
   - currently owns simulator adapter, shared controls, row layout, dropdowns,
     numeric edit semantics, preview routing, config construction, and save path
   - shared controls must leave this file first

2. `locked_cell_explosion/board_view.py`
   - currently simulator-namespaced but owns true-board presentation concepts
     needed by simulator, explorer, endgame, and later gameplay
   - shared board presentation must leave the simulator namespace

3. `front3d_render.py` and `front4d_render.py`
   - own gameplay render loops and also contain reusable camera, board
     presentation, grid, endgame trace, and W-movement conventions
   - only presentation seams should be extracted, not gameplay loop ownership

4. `render/gfx_game.py`
   - owns normal 2D rendering and menu controls
   - shared control primitives and 2D board-presentation seams should be
     separated carefully

5. `endgame_animation.py`
   - correctly owns endgame chrome/live-subset/preset behavior, but remains a
     duplication risk because it has its own shell/relic physics and calls
     explosion runtime
   - it must not absorb shared explosion runtime or shared board-presentation
     behavior

6. `defaults_store.py`
   - correct runtime-default authority for explosion defaults
   - currently carries a short-term UI enum dependency risk
   - must not accumulate broader UI coupling

---

## Staged Extraction Order

## Stage 2: Shared Controls Extraction

Goal:
create shared control models/helpers without changing visible behavior.

Move or introduce:
- row layout and wrapped label/value measurement,
- dropdown open/close and selection state,
- numeric text edit state,
- slider/arrow hit testing,
- control-level keyboard/pointer operations.

First consumer:
- simulator rows in `locked_cell_explosion/surface.py`

Acceptance:
- simulator behavior is byte-for-byte or test-equivalent at control level,
- no board/runtime changes,
- targeted simulator control tests pass,
- `surface.py` no longer owns generic dropdown/numeric behavior.

Status:
- complete as of 2026-04-23.
- landed shared controls package:
  `src/tet4d/ui/pygame/controls/`
- landed first consumer:
  `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`
- landed shared-layer regression coverage:
  `tests/unit/engine/test_pygame_controls_shared.py`

---

## Stage 3: Shared Board Presentation Facade

Goal:
define a shared board-presentation authority and route simulator true-board
preview through it.

Move or introduce:
- board boundary/box/edge-grid authority,
- grid/shadow settings application,
- trace render primitives,
- W-movement style application,
- camera/view conventions as presentation inputs.

First consumer:
- simulator `surface.py`, routed through
  `src/tet4d/ui/pygame/board_presentation/native_board.py` with
  `locked_cell_explosion/board_view.py` reduced to a compatibility shim.

Acceptance:
- simulator true-board 2D/3D/4D behavior remains equivalent,
- no control/runtime changes,
- the new package is the authoritative application point for presentation
  behavior rather than a fake wrapper.

Status:
- complete as of 2026-04-23.
- landed shared board-presentation package:
  `src/tet4d/ui/pygame/board_presentation/`
- landed first consumer:
  `src/tet4d/ui/pygame/locked_cell_explosion/surface.py`
- existing camera/view reuse is explicit:
  `front3d_render.Camera3D`, `front4d_render.LayerView3D`,
  `topology_lab/camera_controls.py`, and `input/camera_mouse.py`
- compatibility shim retained:
  `src/tet4d/ui/pygame/locked_cell_explosion/board_view.py`

---

## Stage 4: Runtime Defaults And Session Boundary

Goal:
make runtime defaults application explicit and keep adapters from rewriting
shared runtime fields.

Move or introduce:
- helper that converts saved defaults plus runtime source/topology inputs into
  `StandaloneExplosionConfig`
- tests for simulator/explorer/endgame sharing the same runtime-default path
- clearer split between persistent defaults and runtime session state

First consumers:
- simulator restart,
- explorer launch,
- endgame launch.

Acceptance:
- `build_locked_cell_explosion` receives equivalent config for all existing
  paths,
- no visual rewrites,
- no adapter silently overrides shared defaults except documented runtime inputs.

Status:
- complete as of 2026-04-23.
- landed shared runtime-default builder:
  `src/tet4d/ui/pygame/locked_cell_explosion/runtime_config.py`
- simulator, explorer, and endgame now route runtime config assembly through
  `build_runtime_explosion_config(...)`
- persistent defaults remain in `defaults_store.py`, while runtime session
  state remains in `StandaloneExplosionSurfaceState`, `ExplosionSimulationState`,
  controller state, and endgame animation state rather than in persisted
  defaults payloads

---

## Stage 5: Explorer Adapter Thinning

Goal:
keep explorer launch ownership to topology/state injection only.

Move or introduce:
- explorer handoff object for topology, board dims, cells, and seed
- no explorer-owned copies of shared defaults, shared controls, or shared board
  presentation behavior

Acceptance:
- sandbox explosion launch remains functionally equivalent,
- explorer does not own shared board presentation or shared controls.

Status:
- complete as of 2026-04-23.
- explorer launch ownership is now limited to topology/state extraction,
  sandbox cell extraction, thin launch handoff, and explorer-only status text
- explorer handoff is explicit in
  `src/tet4d/ui/pygame/topology_lab/explosion.py` via
  `ExplorerExplosionLaunchRequest`
- explorer launch continues to route through
  `build_explorer_explosion_surface_state(...)`, which in turn uses the shared
  runtime-default builder and shared board-presentation/runtime layers

---

## Stage 6: Endgame Adapter Thinning

Goal:
keep endgame ownership to locked-cell source, live-subset selection, and
endgame chrome.

Move or introduce:
- endgame handoff object for gameplay locked cells, topology, saved defaults,
  preset/speed/chrome
- explicit runtime-only override list

Acceptance:
- endgame no longer duplicates or overrides shared explosion defaults outside
  the documented narrow adapter inputs
- endgame does not own any separate board-presentation config application path
- endgame launches shared runtime plus shared board presentation rather than a
  parallel view path
- endgame shell phases are explicit: rupture, message/noise, outward debris
  release, survivor continuity into the shared runtime/view, then persistent
  readable residue on the shared runtime/view
- the two-population split is intentional: endgame-owned debris spectacle vs
  shared-runtime live simulation subset, with saved shared
  `endgame_live_cell_fraction` controlling the surviving subset and the debris
  population defined as the complement

---

## Stage 7: Gameplay Board Presentation Reuse

Goal:
allow normal gameplay renderers to consume the shared board-presentation
authority where it reduces duplication.

Move or route:
- 2D/3D/4D grid/shadow/box/edge-grid seams,
- W-movement style helpers,
- visual-only camera conventions where appropriate.

Stage split:
- Stage 7A: route only low-risk gameplay grid/shadow/boundary-box/edge-grid
  application through shared board presentation
- Stage 7B: route gameplay W-movement presentation through shared board
  presentation
- Stage 7C: reuse presentation-only camera/view seams only where clearly
  decoupled and low-risk

Acceptance:
- gameplay render behavior remains equivalent,
- gameplay rules/state ownership does not move,
- gameplay reuses presentation seams only.

Stage 7A landed:
- `render/gfx_game.py`, `front3d_render.py`, and `front4d_render.py` now route
  low-risk grid/shadow/boundary-box/edge-grid application through
  `src/tet4d/ui/pygame/board_presentation/gameplay_board.py`
- Stage 7B now routes gameplay 4D W-movement style dispatch through that same
  shared gameplay board-presentation helper instead of keeping the style
  application branch in `front4d_render.py`
- Stage 7C now routes only the low-risk gameplay camera/view presentation
  seams through that same shared gameplay board-presentation helper:
  `front3d_render.py` now delegates orthographic zoom-fit application there,
  and `front4d_render.py` now delegates frozen-view snapshot copying there
- explicitly deferred as gameplay-local after Stage 7C:
  `front4d_render.py` basis decomposition, projection extras/raw-point
  transforms, layer-presentation orchestration, and gameplay camera/control
  semantics because those seams remain entangled and are not yet clearly
  presentation-only

---

## Deferred Work

Intentionally not solved by Stages 1 through 7:
- deep 4D camera/projection cleanup
- broader camera-system redesign
- broader projection-math redesign
- presentation unification beyond the low-risk gameplay seams already landed
- further size reduction of `surface.py`, `native_board.py`, and
  `endgame_animation.py` beyond the ownership fixes already landed

Deferred gameplay-local seams:
- `front4d_render.py` basis decomposition and layer-axis semantics
- `front4d_render.py` projection extras / raw-point transform pipeline
- gameplay camera controls and input semantics in `front3d_game.py` and
  `front4d_game.py`
- any broad front3d/front4d orchestration cleanup that would amount to camera
  or projection redesign

## Closeout Audit Notes

Documented follow-up risks after closeout:
- `locked_cell_explosion/surface.py` is still large and remains the main thin-
  adapter follow-up risk by size, even though shared controls/presentation/
  runtime ownership is now extracted
- `board_presentation/native_board.py` is now the main shared-presentation
  hotspot and may need future internal decomposition if more presentation
  seams are added there
- `board_presentation/gameplay_board.py` is currently acceptable in scope, but
  it should stay limited to shared gameplay-facing presentation entrypoints
- `endgame_animation.py` remains large, but its persistent readable simulation
  now routes through the shared runtime/view path rather than a parallel
  runtime implementation
- `front3d_render.py` and `front4d_render.py` still own lower-level gameplay
  projection/orchestration code; after Stage 7C the remaining seams there are
  explicitly deferred rather than architecturally ambiguous

No new feature work is required for this closeout baseline.

---

## Risks And Guards

### Monolith risk
`surface.py` must shrink by extracting shared controls first.
Moving it wholesale into a simulator subfolder would preserve the wrong
ownership.

### Duplicated endgame path risk
Endgame may be tempted to copy simulator view or runtime behavior.
Endgame must consume:
- shared runtime/defaults,
- shared board presentation,
with only source cells, live subset, and chrome kept local.

### Simulator-owned shared logic risk
`board_view.py` and surface controls are already useful outside the simulator.
Future edits must avoid adding new shared rendering or widget behavior under
simulator-only names.

### Config/default authority split risk
`explosion_defaults.<mode>` is the shared config authority.
Legacy endgame settings may only supply endgame-specific preset/speed/chrome
inputs. The normal pause-menu Settings -> Game `Explosion Defaults` section
must edit this same `explosion_defaults.<mode>` authority rather than
reintroducing pause-only or endgame-only defaults branches.

### Engine/UI boundary risk
Shared board presentation and shared controls remain pygame UI code.
Do not move them under `tet4d.engine`.

---

## Stage 1 Acceptance

Stage 1 is complete when:

- current ownership is mapped,
- target ownership is mapped,
- wrong-layer modules are listed,
- the Stage 2 through Stage 7 extraction order is explicit,
- runtime behavior is unchanged,
- governance/doc verification passes.
