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

The `Advanced` submenu is the compatibility bucket for:

- `Advanced gameplay`
- `Legacy Topology Editor Menu`

Placement rules for this frozen launcher contract:

- `Help / FAQ` must stay reachable from the learning/support surface rather
  than only through `Settings`.
- `Controls Reference` must remain distinct from `Settings -> Controls`.
- `Settings -> Controls` means persistent input configuration, not the help
  legend/reference surface.
- `Leaderboard` and `Bot` must not return to the root layer and must not live
  under `Settings`; they belong to play-adjacent flow instead.
- `Topology Playground` is a direct modern entry. It must not open a submenu
  that splits modern and legacy topology editing.
- `Legacy Topology Editor Menu` is a backward-compatibility surface under
  `Settings -> Advanced`; it must not appear inside `Topology Playground`,
  `Explorer`, or `Path`.

## Topology playground shell contract

Default visible structure:

- Top bar: compact global title, workspace tabs, and one short validity chip.
- Left sidebar: contextual controls only for the active workspace.
- Center area: the primary working surface and the largest region on screen.
- Right helper: a small external key-hint block only.
- Bottom strip: compact status plus compact action shortcuts/buttons only.

Frozen screen hierarchy:

- center workspace is the dominant region
- top bar is compact and global
- left sidebar is workspace-contextual only
- bottom strip is compact status/actions only
- right helper is a small external key-hint block only

Top bar:

- title: `Topology Playground`
- tabs: `Editor` / `Sandbox` / `Play`
- validity chip wording: `Valid` / `Needs Fix` / `Unsafe`
- no prose header
- no diagnostic rows

Left sidebar:

- `Editor`: `Tool`, `Trace`, optional `Probe Neighbors`, edit actions only when
  directly relevant, diagnostics collapsed
- `Sandbox`: sandbox piece controls, sandbox `Neighbors`, sandbox actions,
  diagnostics collapsed
- `Play`: play/launch controls, play-specific setup/status, diagnostics
  collapsed

Center workspace:

- larger than the side surfaces by default
- `3D` and `4D` projection working surfaces should be enlarged relative to the
  earlier shell
- remove nonessential chrome that compresses the scene

Right helper:

- translation keys
- rotation keys
- at most one short workspace/tool context line
- no prose
- no duplicate controls
- no diagnostics

Bottom strip:

- compact status chips on the left
- compact action buttons on the right
- no long status rows
- no prose

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
- The canonical visible probe glyph is one large circle in the active cell.
- The shared probe trace visual language is the connecting trace line itself;
  intermediate path dots are intentionally removed in this redesign pass.
- The Editor owns an optional `Probe Neighbors` overlay that renders canonical
  adjacent probe targets as smaller subordinate dots around the main probe.
- Toggling `Probe Neighbors` must not hide the main probe dot.
- Sandbox neighbor-search stays separate. It remains a Sandbox-owned
  `Neighbors` control and must not be reframed as an Editor feature.
- Sandbox piece cells must continue to render as boxes, while sandbox neighbor
  markers and Editor probe-neighbor markers both render as dots with distinct
  visual roles.
- The same probe glyph language must be reused in `2D`, `3D` projections, and
  `4D` projections; Editor probe or probe-neighbor markers must not regress
  into box rendering in any supported dimension.
- The `3D` / `4D` default shell does not need the older per-panel movement-
  preview legends. For this phase, the accepted probe guidance is simply: the
  probe can move, and the helper must expose the full translation keys.

## Deferred work

Explicitly deferred until after this visible-shell contract is stable:

- deeper `controls_panel.py` decomposition
- deeper `scene_state.py` decomposition
- runtime authority redesign
- Play semantic redesign
