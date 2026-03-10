# Topology Playground Migration

## Status
- Stage: 0
- Scope: UX architecture freeze only
- Code migration: not started in this document

## Objective
Freeze the user-facing topology UX architecture before implementation so the migration has one canonical target and clear non-goals.

This document is authoritative for the product-shape migration only. Where docs and code disagree, code remains higher trust until later migration stages update the docs.

## Current Surfaces

### 1. Play Menus and Launchers
Current play surfaces still act as launch and setup surfaces for explorer flows.

Responsibilities currently present across menu and launcher paths:
- choose dimension and mode
- launch explorer sessions
- expose coarse explorer-related setup
- route to the former Topology Lab / current Explorer Playground shell

Current code surfaces:
- `cli/front.py`
- `src/tet4d/ui/pygame/front2d_game.py`
- `src/tet4d/ui/pygame/launch/launcher_nd_runner.py`
- `config/menu/structure.json`

### 2. Explorer Playground Shell
The current unified shell exists under the historical topology-lab ownership path.

Current shell responsibilities:
- explorer scene rendering
- probe traversal
- sandbox piece movement/rotation
- preset choice
- board-size adjustment
- seam/gluing creation and editing
- play launch from current draft

Current code surfaces:
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- `src/tet4d/ui/pygame/topology_lab/app.py`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/scene2d.py`
- `src/tet4d/ui/pygame/topology_lab/scene3d.py`
- `src/tet4d/ui/pygame/topology_lab/scene4d.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/arrow_overlay.py`
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`

### 3. Line + Dots Mini Tool / Secondary Analysis Views
There are smaller list/row/panel-based analysis controls and previews inside the current shell. These help inspect presets, seams, diagnostics, and values, but they are not the primary spatial interaction surface.

Current responsibilities in this category:
- row-based parameter editing
- textual seam / transform status
- diagnostics summary
- supporting inspection views

Current code surfaces:
- left/right panel and row systems inside `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- engine-backed preview/diagnostic providers under `src/tet4d/engine/runtime/`

## Target Surfaces

### 1. Play Menus Remain Minimal Preset Launchers
Play menus must remain minimal preset launchers.

Target responsibilities for play menus:
- choose mode and dimension
- optionally choose a coarse preset or enter the Explorer Playground
- launch the playground or a normal play flow
- do not act as full topology editors

Target non-responsibilities for play menus:
- no full seam editing
- no full transform editing
- no primary topology analysis workflow
- no duplicated topology setup surface

### 2. Topology Playground Becomes the Only Full Topology Editor
The topology playground becomes the only full topology editor.

Target responsibilities for the playground:
- choose and replace presets
- adjust board size and coarse playground settings
- inspect boundaries and seams
- create, edit, and remove gluings
- move the probe
- move and rotate the sandbox piece
- inspect diagnostics and warnings
- launch play directly from the current draft state

Target ownership:
- one canonical explorer-playground shell
- one in-memory draft topology
- one direct play-launch path from that draft

### 3. Graphical Explorer Becomes the Primary Canvas
The graphical explorer becomes the primary canvas.

Target behavior:
- scene-first interaction
- boundary selection happens in the scene
- seam editing begins from scene interaction
- arrows and seam overlays live in the scene
- probe and sandbox are visible in the scene
- panels support the scene instead of replacing it

### 4. Line + Dots Mini Tool Becomes Secondary Analysis View
The line+dots mini tool becomes a secondary analysis view.

Target responsibilities:
- explain current selection
- show diagnostics and derived values
- provide supporting fine-grained controls
- expose presets and value rows as supporting controls

Target non-responsibilities:
- it is not the primary topology editor
- it is not the primary spatial interface
- it must not replace direct scene interaction for seam creation/editing

### 5. Play Launch Must Use Current Playground State Directly
Play launch must use current playground state directly.

Target rule:
- the current in-memory playground draft is the canonical source of truth for play launch
- no detached apply-confirm-refresh flow
- no mandatory save before play
- returning from play should restore the same draft shell state

## Removed or Demoted Responsibilities

### Removed from Play Menus
Play menus are demoted to minimal preset launchers.

Removed or demoted responsibilities:
- full topology editing
- seam/gluing authoring
- transform editing
- deep topology analysis
- duplicated explorer-topology setup surface

### Removed from Secondary Analysis Views
Line/row/list-based controls are demoted to supporting views.

Removed or demoted responsibilities:
- being the primary topology editor
- owning the main interaction flow
- substituting for direct scene editing

### Removed from Detached Pre-Play Setup
Detached setup flows must not remain the primary way to configure explorer topology.

Removed or demoted responsibilities:
- requiring round-tripping out of the explorer/playground shell to complete central topology tasks
- forcing the player to leave the main explorer surface to adjust presets, board size, or seam structure

## Canonical Product Rules
1. Explorer Playground is the primary user-facing shell for explorer topology work.
2. Play menus remain minimal preset launchers.
3. The graphical explorer is the primary canvas.
4. The line+dots mini tool is secondary analysis only.
5. Play launch uses current playground state directly.

## Non-Goals
This stage does not perform code migration.

Explicit non-goals:
- no runtime rewiring
- no UI event rewiring
- no engine topology semantic changes
- no deletion of old code paths
- no launcher removal
- no structural cleanup in this document-only stage

## Acceptance Criteria
This Stage 0 document is complete only if it clearly defines:
- current surfaces
- target surfaces
- removed/demoted responsibilities
- minimal role of play menus
- playground as the only full topology editor
- graphical explorer as primary canvas
- line+dots mini tool as secondary analysis view
- direct play launch from current playground state

## Next Stage Preview
The next implementation stage should migrate code toward this target incrementally:
1. add or isolate any missing playground ownership modules
2. route one explorer/playground flow through the canonical state
3. verify
4. only then demote or remove old paths