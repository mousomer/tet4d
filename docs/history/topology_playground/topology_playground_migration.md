# Topology Playground Migration

Archived note: this is the Stage-0 architecture-freeze plan, not the current
status authority. Current topology-playground architecture authority lives in
`docs/plans/topology_playground_current_authority.md`. Newer task instructions
and the current-authority manifest take precedence over this archive.

## Stage

Stage 0 only: architecture freeze and migration design.

This document does not claim any later migration stage is implemented. It
defines the control surfaces, ownership boundaries, migration order, and
non-goals that later implementation work must follow.

## Plan

1. Name the current topology control surfaces explicitly.
2. Freeze the target control-surface architecture before later implementation.
3. Define which responsibilities are retained, moved, demoted, and removed.
4. Define the staged migration order without claiming later stages are done.

## Acceptance Criteria

This document is complete only if all are true:

- the current surfaces are named explicitly
- the target surfaces are named explicitly
- retained, moved, demoted, and removed responsibilities are defined
- the staged migration order is explicit
- explicit non-goals are included

## Problem Statement

The topology system currently exposes overlapping setup and editing surfaces.
That overlap creates round-tripping between play menus, detached playground
flows, and explorer-side editing. Partial improvements do not count as
completion if the user still has to leave the main explorer canvas to finish
core topology work, or if duplicate editor systems remain long term.

## Current Topology Control Surfaces

### 1. Play Menus

Current play-menu surfaces:

- launcher play menu in `config/menu/structure.json`
- 2D setup flow under `src/tet4d/ui/pygame/front2d_game.py`
- ND setup flow under `src/tet4d/ui/pygame/frontend_nd_setup.py`
- launcher routing under `src/tet4d/ui/pygame/launch/launcher_nd_runner.py`

Current responsibilities:

- choose dimension and gameplay mode
- launch ordinary play flows
- launch the explorer/playground flow
- hold or expose some topology-adjacent setup choices
- act as a fallback path when the playground is not yet the full editor

Current problem:

- play menus still compete with the playground for topology setup ownership
- the user can still be forced to round-trip away from the main explorer canvas

### 2. Topology Playground Menu / Shell

Current playground-menu surfaces:

- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- `src/tet4d/ui/pygame/topology_lab/app.py`
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/topology_lab/copy.py`

Current responsibilities:

- own the playground shell/orchestration
- expose topology rows and action rows
- coordinate save/export/play actions
- host tool switching, pane switching, and shell-level status

Current problem:

- this shell still mixes orchestration, analysis controls, and editing support
- a detached menu-style surface can still be perceived as a separate editor

### 3. Topology Playground Graphical Panel / Explorer-Side Topology UI

Current explorer-side surfaces:

- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/scene2d.py`
- `src/tet4d/ui/pygame/topology_lab/scene3d.py`
- `src/tet4d/ui/pygame/topology_lab/scene4d.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/arrow_overlay.py`
- `src/tet4d/ui/pygame/topology_lab/transform_editor.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`
- `src/tet4d/ui/pygame/topology_lab/preview.py`

Current responsibilities:

- render the graphical explorer
- show boundaries, seam arrows, probe state, and sandbox state
- support direct picking and explorer-side edits
- provide the live spatial context for topology work

Current problem:

- this is not yet guaranteed to be the only primary editing surface
- users can still encounter duplicate or detached editing responsibilities

### 4. Abstract Line+Dots / Graph Research View

Current abstract analysis surfaces:

- the `Analysis` pane and row-based controls inside
  `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
- the row/state helpers in
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- preview and diagnostics providers under `src/tet4d/engine/runtime/`

Current responsibilities:

- show abstract boundary/glue summaries
- show textual transform and diagnostic output
- expose row-based value changes
- support research/inspection of the current topology

Current problem:

- this surface can still overlap with the explorer as an editing path
- the architecture is not frozen unless this is explicitly demoted to analysis
  only

## Target Control Surfaces

### 1. Play Menus: Minimal Preset Launcher Only

Play menus remain, but only as minimal launch surfaces.

Target responsibilities:

- choose a dimension or play mode
- launch safe preset play paths
- launch `Play Last Custom Topology`
- launch `Open Explorer Playground`

Target non-responsibilities:

- no full topology editing
- no seam authoring or transform authoring
- no board-design workflow
- no duplicated topology editor

### 2. One Unified Topology Playground

There is one full topology editor.

Target responsibilities:

- own the canonical topology draft state
- own board settings used for topology editing
- own preset replacement and seam editing
- own piece sandbox and probe workflow
- own diagnostics and analysis support
- own play launch from the current playground state

### 3. Graphical Explorer: Primary Editing Surface

The graphical explorer is the primary live editing canvas.

Target responsibilities:

- primary boundary selection
- primary seam creation/editing entry point
- direct spatial feedback for topology changes
- direct sandbox/probe feedback in the same view

Target rule:

- if a topology task is core editing work, the explorer should be the first and
  primary place to perform it

### 4. Abstract Line+Dots / Graph Research View: Secondary Analysis Only

The abstract research view remains available, but only as a supporting analysis
tool.

Target responsibilities:

- explain current state
- show derived diagnostics and graph-style summaries
- support comparison, inspection, and debugging
- offer fine-grained supporting controls when needed

Target non-responsibilities:

- it is not the primary editor
- it is not the primary topology canvas
- it does not own the main topology workflow

## Responsibilities By Surface

### What Remains In Play Menus

- safe preset launching
- direct dimension/mode entry
- `Play Last Custom Topology`
- `Open Explorer Playground`
- shared non-topology launcher concerns that are unrelated to full topology
  editing

### What Moves Into The Topology Playground

- canonical topology draft ownership
- board settings used for topology editing
- topology preset family selection and replacement
- direct explorer-side seam authoring
- transform editing
- probe traversal and topology diagnostics
- piece sandbox spawning, movement, rotation, and seam-cross testing
- play launch from the current playground state

### What Is Demoted

- the detached playground-menu identity is demoted to an entry alias or
  shortcut, not a separate editor system
- the abstract line+dots / graph research view is demoted to secondary analysis
  only
- row/list editing remains supporting UI, not the primary editing path

### What Is Removed

- long-term duplicate topology editor systems
- any mandatory round-trip from explorer to another surface for core topology
  editing
- any separate apply/convert/export step required before playing the current
  playground draft
- topology-editor responsibilities in play menus once playground parity exists

## Canonical State Rule

The migration converges on one canonical in-memory playground state.

That state must own, directly or by stable sub-objects:

- dimension
- board settings
- current topology profile or explorer draft
- current seam-edit draft state
- current probe state
- current sandbox state
- play-launch inputs derived from the current playground draft

The explorer consumes this canonical state. Play launch consumes this canonical
state. Detached or menu-local shadow copies are migration debt, not part of the
target architecture.

## Migration Stages

### Stage 0: Architecture Freeze

Define the target architecture and migration order before broader code changes.
Do not treat partial implementation as completion.

### Stage 1: Canonical State

Create or formalize one canonical topology playground state that owns the live
draft topology and the board/playground settings required by later stages.

Exit condition:

- there is one authoritative playground state for topology editing

### Stage 2: Explorer Consumes Canonical State

Make explorer rendering, picking, overlays, and supporting analysis read from
the canonical playground state instead of local shell copies.

Exit condition:

- explorer-side UI is a consumer of canonical state, not a parallel owner

### Stage 3: Direct Explorer-Side Editing

Make the graphical explorer the first-class topology editing path.

Required migrated behaviors:

- direct boundary picking in explorer
- direct seam creation/editing from explorer context
- no mandatory round-trip to another menu for core seam work

Exit condition:

- one full edit path works from the explorer canvas itself

### Stage 4: Board Settings In Playground

Move topology-relevant board settings into the playground.

Required migrated behaviors:

- board dimensions live in playground state
- topology-relevant presets live in playground state
- changing those settings updates the same canonical draft the explorer uses

Exit condition:

- board settings are edited where topology is edited

### Stage 5: Piece Sandbox Integration

Make the playground the topology-testing surface, not just the topology-editing
surface.

Required migrated behaviors:

- spawn piece
- move piece
- rotate piece
- inspect seam-crossing behavior

Exit condition:

- topology testing happens inside the playground against the same draft being
  edited

### Stage 6: Play Launch From Playground State

Launch gameplay directly from the current playground draft.

Required migrated behaviors:

- the playground launches play from the live draft
- no export/import or convert/apply detour is required

Exit condition:

- the current playground state is sufficient to start gameplay directly

### Stage 7: Demotion Of Old Detached Surfaces

After the migrated path is proven, demote or remove old detached control
surfaces.

Required migrated behaviors:

- play menus are reduced to minimal launchers only
- the detached playground-menu identity no longer acts as a separate editor
- the abstract line+dots view is explicitly secondary analysis only

Exit condition:

- there is no long-term duplicate editor system

## Explicit Non-Goals

- no full rewrite in one pass
- no deletion before migration parity exists
- no separate long-term duplicate editor systems
- no claiming migration completion because code compiles or tests pass while the
  user still has to round-trip between surfaces
- no moving unrelated launcher, settings, or gameplay concerns into this
  migration unless they are required to make the playground the canonical
  topology editor
- no topology-semantics rewrite as part of this Stage 0 planning document

## Decision Rules For Later Stages

Later stages must not be marked complete unless all are true for the migrated
path:

- the playground state is canonical
- the explorer consumes that canonical state
- the graphical explorer is the primary editing surface
- play launch uses the current playground state directly
- play menus remain minimal launchers rather than duplicate editors
- the abstract line+dots / graph research view is secondary analysis only
