# Topology Playground Migration

## Status
- Stage: 6
- Scope: demote the detached playground menu after canonical-state, live edit, settings, and sandbox migration
- Code migration: in progress for the migrated explorer-playground path

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

## Stage 2 Scope And Non-Goals

Stage 2 migrates the graphical explorer rendering/picking path to canonical playground state.

Explicit Stage 2 non-goals:
- do not yet merge all menus
- do not yet delete old configuration panels
- no engine topology semantic changes
- no launcher removal
- no destructive cleanup of old paths before the migrated path is verified

## Stage 2 Acceptance Criteria
Stage 2 is complete only if:
- explorer reads canonical playground state for the migrated path
- topology changes reflected in explorer come from that canonical state
- explorer is no longer driven by ad hoc local copies for the migrated path
- old configuration panels remain present for non-migrated responsibilities

## Stage 2 Status
Current implementation status:
1. canonical playground scene caches now live on `TopologyPlaygroundState` in `src/tet4d/ui/pygame/topology_lab/scene_state.py`
2. the migrated explorer rendering/picking path in `src/tet4d/ui/pygame/launch/topology_lab_menu.py` now consumes those canonical caches
3. focused tests assert canonical scene-state population, canonical scene-state refresh on topology mutation, and draw-path consumption without recomputing preview locally
4. menu consolidation and old-panel removal are still deferred to later stages

## Stage 3 Scope And Non-Goals

Stage 3 adds one fully live explorer-side topology editing path without requiring a round-trip to another menu.

Required migrated path:
- select source boundary from the explorer scene
- select target boundary from the explorer scene
- create a gluing draft in the same shell
- edit transform controls from the linked side panel
- apply the gluing without leaving explorer

Explicit Stage 3 non-goals:
- do not yet migrate every menu feature
- do not yet remove old configuration panels
- do not yet delete non-migrated topology editing paths

## Stage 3 Acceptance Criteria
Stage 3 is complete only if:
- the user can change core topology settings without leaving explorer
- at least one topology edit path is fully live from the explorer scene
- no back-and-forth is needed for that migrated path

## Stage 3 Status
Current implementation status:
1. Explorer entry can start from the scene in sandbox/probe-facing flow, right-click a boundary, and enter direct gluing creation without leaving the shell
2. a second scene boundary pick completes the source/target draft path and switches into transform editing
3. linked side-panel transform editing and apply-glue actions operate on that in-memory draft in the same shell
4. focused tests pin this direct explorer-entry scene path end to end

## Stage 4 Scope And Non-Goals

Stage 4 makes dimension, board size, and explorer preset changes live playground settings.

Required migrated settings:
- dimension selector
- axis-size editor
- current topology preset selector

Explicit Stage 4 non-goals:
- do not yet migrate every remaining menu feature
- do not yet delete old configuration panels
- do not yet consolidate every retained row/panel responsibility into new modules

## Stage 4 Acceptance Criteria
Stage 4 is complete only if:
- dimension, board-size, and explorer-preset settings are editable from the playground shell
- those settings update canonical playground state directly
- the explorer scene reflects those changes live from canonical state

## Stage 4 Status
Current implementation status:
1. explorer-entry rows now expose the dimension selector, axis-size editors, and explorer preset selector from the playground shell itself
2. changing dimension updates `TopologyPlaygroundState.dimension`, refreshes canonical scene caches, and refreshes the live explorer scene for the new dimension
3. changing board size updates `TopologyPlaygroundState.play_settings.board_dims`, refreshes canonical scene caches, and redraws the explorer against the new dimensions
4. changing explorer preset updates `TopologyPlaygroundState.explorer_profile`, rebuilds canonical scene preview state, and refreshes the scene without leaving the shell
5. focused explorer-entry tests now pin all three setting classes against canonical scene state instead of treating them as implied behavior

## Stage 5 Scope And Non-Goals

Stage 5 makes piece testing a first-class playground capability inside the explorer shell.

Required migrated sandbox responsibilities:
- spawn piece
- move piece
- rotate piece
- seam-cross preview

Explicit Stage 5 non-goals:
- do not yet migrate every remaining menu feature
- do not yet remove retained old configuration panels
- do not yet redesign Normal Game play/runtime around sandbox behavior

## Stage 5 Acceptance Criteria
Stage 5 is complete only if:
- sandbox uses canonical playground state
- piece behavior is testable without leaving playground

## Stage 5 Status
Current implementation status:
1. the unified explorer shell exposes sandbox actions directly, including spawn, move, rotate, trace, reset, and play-preview
2. sandbox state is owned on `TopologyPlaygroundState.sandbox`, not by ad hoc local shell copies
3. seam-cross preview is derived from engine-owned gluing traversal and rendered through the sandbox preview lines inside the same shell
4. focused tests pin spawn, repeated movement, rotation, and seam-cross preview without leaving the playground

## Next Stage Preview
After Stage 4, later stages may:
1. migrate additional retained menu-owned topology settings fully into the canonical playground state
2. consolidate or remove old configuration surfaces only after the new path is verified
3. continue shrinking launcher-shell orchestration until `topology_lab_menu.py` is orchestration-only

## Stage 6 Scope And Non-Goals

Stage 6 demotes the detached playground launcher entry so ordinary custom-topology flow routes through the unified explorer shell instead of treating the direct-open menu as primary.

Required work:
- keep only what has not yet been migrated on the detached path
- route the main custom-topology flow into the unified explorer playground shell
- remove duplicated launcher responsibilities for ordinary topology editing

Explicit Stage 6 non-goals:
- do not yet remove the detached direct-open shortcut entirely
- do not yet migrate every remaining retained configuration panel feature
- do not yet claim `topology_lab_menu.py` is fully decomposed

## Stage 6 Acceptance Criteria
Stage 6 is complete only if:
- the detached menu is no longer required for ordinary topology editing
- the main custom-topology flow routes into the unified explorer shell
- any remaining old-only features are listed explicitly as blockers

## Stage 6 Status
Current implementation status:
1. the detached `topology_lab` launcher action now builds the same explorer gameplay shell as ordinary explorer entry, differing only by entry context (`entry_source="lab"`) rather than by a separate normal-mode launcher flow
2. the launcher play menu now labels the detached entry as `Explorer Playground (Direct Open)` and describes it as an optional shortcut instead of the primary path
3. focused launcher/menu tests pin that ordinary explorer use no longer depends on the detached direct-open item
4. remaining old-only blockers for ordinary topology editing: none

## Stage 7 Scope And Non-Goals

Stage 7 demotes the line+dots row/panel surface so it remains available only as optional secondary analysis while the graphical explorer becomes the primary editing surface.

Required work:
- keep the line+dots row/panel controls as optional analysis/research support
- remove them from the primary editing workflow
- label them clearly as abstract/secondary analysis

Explicit Stage 7 non-goals:
- do not remove the supporting analysis pane entirely
- do not yet decompose `src/tet4d/ui/pygame/launch/topology_lab_menu.py` fully
- do not change explorer topology semantics

## Stage 7 Acceptance Criteria
Stage 7 is complete only if:
- main editing is done in the graphical explorer
- the line+dots analysis surface remains available as secondary analysis only
- helper/footer copy reflects that priority directly

## Stage 7 Status
Current implementation status:
1. the explorer pane is the primary pane label and the default active pane for the explorer-playground path
2. the former controls pane is now explicitly labeled `Analysis`
3. helper/footer copy states that the graphical explorer is the primary editor and the analysis pane is a secondary view
4. focused tests pin the explorer-first pane contract and the secondary-analysis helper text

## Stage 8 Scope And Non-Goals

Stage 8 makes play launch use the current playground state directly, with no export/import mental model and no secondary conversion menu requirement on the migrated path.

Required work:
- add a direct `Play This Topology` action from the playground shell
- launch gameplay directly from the current in-memory playground draft

Explicit Stage 8 non-goals:
- do not remove minimal preset launchers from ordinary play menus
- do not delete explicit compatibility export paths unrelated to normal playground play launch
- do not broaden this stage into a full menu rewrite

## Stage 8 Acceptance Criteria
Stage 8 is complete only if:
- current playground state launches gameplay directly
- no secondary conversion menu is required for the migrated path
- play menus can still launch minimal presets separately

## Stage 8 Status
Current implementation status:
1. the playground shell now exposes the direct action label `Play This Topology`
2. the shell play path calls `build_explorer_playground_config(...)` directly from the current `TopologyPlaygroundState` draft data
3. focused tests pin that `dimension`, `explorer_profile`, and `settings_snapshot` passed to play launch come from the live playground state itself
4. ordinary preset launchers remain outside the shell and are unchanged by this stage


## Stage 9 Scope And Non-Goals

Stage 9 freezes ordinary play menus as minimal launchers so topology complexity no longer sprawls back into play-menu flows.

Required work:
- keep only minimal safe presets in play menus
- keep an explicit action to open the Explorer Playground shell
- keep a direct action to play the last custom topology from stored explorer state

Explicit Stage 9 non-goals:
- do not remove minimal preset launchers for ordinary play
- do not move full topology editing back into play menus
- do not remove the Explorer Playground shell as the canonical topology editor

## Stage 9 Acceptance Criteria
Stage 9 is complete only if:
- play menus are no longer full topology editors
- topology complexity lives only in the playground shell
- play menus keep only minimal safe presets, open-playground, and play-last-custom actions for the migrated path

## Stage 9 Status
Current implementation status:
1. `launcher_play` now contains only `Play 2D`, `Play 3D`, `Play 4D`, `Play Last Custom Topology`, and `Open Explorer Playground`
2. `Play Last Custom Topology` launches directly through the shared playground launch/config path using the stored explorer profile and current mode settings snapshot
3. ordinary play-menu copy now describes the surface as a minimal launcher instead of a topology editor
4. focused menu/launcher tests pin the minimal action set and the direct last-custom launch path
