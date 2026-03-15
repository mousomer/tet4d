# Explorer Playground Unification Plan

Status date: 2026-03-09 (completed on branch codex/explorer-topology-live)
Branch baseline: `codex/explorer-topology-live`

## Objective

Finish the product/UI unification so Explorer Mode and the former Topology Lab are one user-facing shell.

Target user experience:
1. enter Explorer Playground from Explorer Mode or the Topology Lab alias
2. move the probe or the sandbox piece in the same scene
3. change presets and board size in the same shell
4. create/edit/remove seam gluings in the same shell
5. launch play from the current draft without leaving the shell

## Canonical ownership

Engine owns:
- gluing semantics
- movement graph
- preview diagnostics
- runtime topology storage
- live explorer movement runtime

UI shell owns:
- pane focus
- scene rendering and picking
- tool modes
- side-panel editors
- play-from-draft shell orchestration

Canonical shell owner:
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py`

Canonical scene/tool owners:
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`
- `src/tet4d/ui/pygame/topology_lab/explorer_tools.py`
- `src/tet4d/ui/pygame/topology_lab/boundary_picker.py`
- `src/tet4d/ui/pygame/topology_lab/scene2d.py`
- `src/tet4d/ui/pygame/topology_lab/scene3d.py`
- `src/tet4d/ui/pygame/topology_lab/scene4d.py`
- `src/tet4d/ui/pygame/topology_lab/arrow_overlay.py`
- `src/tet4d/ui/pygame/topology_lab/piece_sandbox.py`

## Product contract

### Pane model

The shell has two primary panes:
- `Controls`: left-side board/preset/transform/action rows
- `Scene`: explorer scene, picking, probe, sandbox, and play preview

Keyboard contract:
- `Tab` / `Shift+Tab`: switch pane
- `Up/Down`: move within the controls pane
- `Left/Right`: change values on adjustable controls rows
- `Enter`: activate the current row in controls, or launch play when the active tool is `Play`
- `Delete` / `Backspace`: remove the selected seam

Mouse contract:
- click `+/-` buttons on controls rows to adjust values directly
- left-click boundary or seam in the scene to inspect/select
- right-click boundary in the scene to start seam creation/editing

### Tool model

The shell exposes one active tool at a time:
- `Navigate`
- `Inspect`
- `Create Gluing`
- `Edit Transform`
- `Probe`
- `Sandbox`
- `Play`

Behavior:
- `Sandbox` captures movement/rotation for the current sandbox piece
- all other scene-facing tools use movement keys for the probe
- `Navigate` is the only tool that uses 3D/4D camera orbit/zoom controls

### Camera contract

`3D/4D` explorer scenes support camera movement in `Navigate`:
- middle-mouse drag: orbit
- mouse wheel: zoom
- existing camera keys: rotate/reset (and `xw/zw` turns in `4D`)

`2D` does not expose camera hints.

## Drift prevention

Required regression coverage:
1. Explorer entry and Topology Lab entry build the same shell launch contract except for initial tool/context.
2. Explorer entry starts in the scene pane and exposes board-size/preset controls in the same shell.
3. Mouse clicks on `+/-` controls rows adjust values, including decrement (`-`).
4. `3D/4D` explorer entry initializes a scene camera and routes navigate-tool camera actions through the shell.
5. Footer/helper lines are generated from real state and reflect:
   - active pane
   - active tool
   - available camera support
   - actual value-adjustment controls
6. Scene picking prioritizes explicit targets (`row_step`, seam, boundary) over generic row selection.

## Remaining follow-up

Core product work is complete on `codex/explorer-topology-live`.

Only optional future cleanup remains:
1. further structural decomposition of `src/tet4d/ui/pygame/launch/topology_lab_menu.py`
2. removal of explicit legacy export compatibility entirely, if that support is intentionally dropped later

## Acceptance

This plan is complete when all are true:
1. Explorer Mode and Topology Lab are the same shell in practice and copy.
2. The shell itself exposes presets, board size, seam editing, sandbox, and play.
3. `3D/4D` camera controls are available inside the shell.
4. Footer hints explain pane switching and value editing from the actual active state.
5. Mouse `+/-` adjustments work, including `-`.
6. Explorer-entry parity is pinned by tests.
