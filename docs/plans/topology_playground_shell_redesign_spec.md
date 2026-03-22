# Topology Playground Visible Shell Redesign Spec

Status: frozen visible-shell spec  
Last updated: 2026-03-22

## Purpose

Freeze the visible-shell redesign for the launcher and topology playground
without reopening settled topology-playground architecture or starting deeper
module simplification.

## Frozen authority constraints

- Preserve the settled top-level playground workspaces: `Editor`, `Sandbox`,
  and `Play`.
- Preserve direct playground entry opening in `Sandbox`.
- Preserve canonical runtime selectors as the only explorer-path input
  authority.
- Preserve current Play drop-policy semantics; they are out of scope here.
- Do not start `controls_panel.py` or `scene_state.py` simplification as a
  primary goal in this pass.
- Allow only the minimum extraction or rewiring needed to land the visible
  shell cleanly.

## Launcher shell contract

The main launcher first layer must be exactly:

1. `Play`
2. `Continue`
3. `Tutorials`
4. `Topology Playground`
5. `Settings`
6. `Quit`

Moved out of the first layer:

- `Controls`
- `Help`
- `Leaderboard`
- `Bot`

The `Play` submenu remains the minimal launch surface for `Play 2D`, `Play 3D`,
and `Play 4D`, plus `Play Last Custom Topology`, play-adjacent leaderboard
access, and bot configuration.

The `Tutorials` submenu remains a first-class learning/support surface with an
explicit internal split:

- `Interactive Tutorials`
- `How to Play`
- `Controls Reference`
- `Help / FAQ`

The `Settings` submenu remains a first-class configuration surface with short
section labels:

- `Game`
- `Display`
- `Audio`
- `Controls`
- `Profiles`
- `Advanced`

Placement rules for this frozen launcher contract:

- `Help / FAQ` must stay reachable from the learning/support surface rather
  than only through `Settings`.
- `Controls Reference` must remain distinct from `Settings -> Controls`.
- `Settings -> Controls` means persistent input configuration, not the help
  legend/reference surface.
- `Leaderboard` and `Bot` must not return to the root layer and must not live
  under `Settings`; they belong to play-adjacent flow instead.

## Topology playground shell contract

Default visible structure:

- Top bar: compact title, workspace tabs, small validity indicator.
- Left sidebar: contextual controls only for the active workspace.
- Center area: the primary working surface and the largest region on screen.
- Right helper: a small external key-hint block only.
- Bottom strip: compact status plus compact action shortcuts/buttons only.

Default view removals or demotions:

- remove the giant explanatory header line
- remove permanent verbose status rows from the default primary view
- remove mixed cross-workspace rows from one always-visible panel
- remove internal-facing labels from the default primary UI
- hide or demote always-visible diagnostics that are not needed for immediate
  interaction

## Frozen wording contract

- `Analysis View` -> `Diagnostics`
- `Explorer Workspace` -> `Workspace`
- `Workspace Path` -> `Path` or hidden behind diagnostics
- `Editor Tool` -> `Tool`
- Keep `Editor`, `Sandbox`, and `Play` as the workspace labels.
- Keep internal Probe/Edit semantics intact.
- Expose `Probe` / `Edit` only where the Editor tool choice is directly
  relevant.

## Diagnostics demotion rules

- Diagnostics and advanced state may remain available, but they must not be the
  default-primary surface.
- If retained in this pass, they should live behind the diagnostics pane,
  secondary rows, or secondary surfaces rather than as always-visible shell
  scaffolding.
- Workspace-owned contextual controls remain primary; read-only diagnostics do
  not.

## Ownership rules preserved by this redesign

- `Trace` remains Editor-owned.
- `Probe Neighbors` is a distinct Editor-owned overlay derived from canonical
  probe state.
- `Neighbors` remains Sandbox-owned.
- The helper remains external and minimal.
- The redesign must not add new shell-owned truth sources.
- The redesign must not reintroduce synchronized shell mirrors as runtime
  authority.

## Probe and neighbor overlay contract

- The Editor probe renders as a probe dot in `2D`, `3D`, and `4D`; it must not
  reuse sandbox-piece box semantics.
- The Editor owns an optional `Probe Neighbors` overlay that renders canonical
  adjacent probe targets as smaller subordinate dots around the main probe.
- Toggling `Probe Neighbors` must not hide the main probe dot.
- Sandbox neighbor-search stays separate. It remains a Sandbox-owned
  `Neighbors` control and must not be reframed as an Editor feature.
- Sandbox piece cells must continue to render as boxes, while sandbox neighbor
  markers and Editor probe-neighbor markers both render as dots with distinct
  visual roles.

## Deferred work

Explicitly deferred until after this visible-shell contract is stable:

- deeper `controls_panel.py` decomposition
- deeper `scene_state.py` decomposition
- runtime authority redesign
- Play semantic redesign
