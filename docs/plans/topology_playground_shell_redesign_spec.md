# Topology Playground Visible Shell Redesign Spec

Role: spec
Status: frozen
Source of truth: this file for the current visible-shell pass
Supersedes: older shell-cleanup wording and playground shell notes
Last updated: 2026-03-22

## Purpose

Freeze the visible-shell redesign for the launcher and topology playground
without reopening settled topology-playground architecture or starting deeper
module simplification.

Architecture authority remains in
`docs/plans/topology_playground_current_authority.md`.

## Authority constraints

This spec must preserve:

- top-level playground workspaces: `Editor`, `Sandbox`, `Play`
- direct playground entry opening in `Sandbox`
- canonical runtime selectors as the only explorer-path input authority
- current Play drop-policy semantics
- deferred deeper `controls_panel.py` / `scene_state.py` simplification

## Launcher contract

The main launcher first layer must be exactly:

1. `Play`
2. `Continue`
3. `Tutorials`
4. `Topology Playground`
5. `Settings`
6. `Quit`

The `Play` submenu remains the minimal play-adjacent launch surface for:

- `Play 2D`
- `Play 3D`
- `Play 4D`
- `Play Last Custom Topology`
- leaderboard access
- bot configuration

The `Tutorials` submenu remains the learning/support surface with this split:

- `Interactive Tutorials`
- `How to Play`
- `Controls Reference`
- `Help / FAQ`

The `Settings` submenu remains the configuration surface with short labels:

- `Game`
- `Display`
- `Audio`
- `Controls`
- `Profiles`
- `Advanced`

The `Advanced` submenu is the compatibility bucket for:

- `Advanced gameplay`
- `Legacy Topology Editor Menu`

### Launcher placement rules

- `Help / FAQ` must stay reachable from the learning/support surface rather
  than only through `Settings`.
- `Controls Reference` must remain distinct from `Settings -> Controls`.
- `Settings -> Controls` means persistent input configuration, not help or
  legend/reference content.
- `Leaderboard` and `Bot` must not return to the root layer and must not live
  under `Settings`.
- `Topology Playground` is a direct modern entry and must not open a submenu
  that splits modern and legacy topology editing.
- `Legacy Topology Editor Menu` must not appear inside `Topology Playground`,
  `Explorer`, or `Path`.

## Topology-playground visible shell contract

Default visible structure:

- top bar: compact global title, workspace tabs, one short validity chip
- left sidebar: contextual controls only for the active workspace
- center area: primary working surface and largest region on screen
- right helper: small external key-hint block only
- bottom strip: compact status plus compact action shortcuts/buttons only

### Top bar

Must contain only:

- title: `Topology Playground`
- tabs: `Editor` / `Sandbox` / `Play`
- validity chip: `Valid` / `Needs Fix` / `Unsafe`

Must not contain:

- prose header copy
- default-primary diagnostic rows

### Left sidebar

`Editor` sidebar:
- `Tool`
- `Trace`
- optional `Probe Neighbors`
- edit actions only when directly relevant
- diagnostics collapsed or secondary

`Sandbox` sidebar:
- sandbox piece controls
- sandbox `Neighbors`
- sandbox actions
- diagnostics collapsed or secondary

`Play` sidebar:
- play / launch controls
- play-specific setup/status
- diagnostics collapsed or secondary

### Center workspace

- Must remain visually dominant.
- `3D` and `4D` projection working surfaces should be enlarged relative to the
  older shell.
- Nonessential chrome that compresses the scene should be removed.

### Right helper

Must contain only:

- translation keys
- rotation keys
- at most one short workspace/tool context line

Must not contain:

- prose
- duplicate controls
- diagnostics
- shadow-menu behavior

### Bottom strip

Must contain only:

- compact status chips on the left
- compact action buttons on the right

Must not contain:

- long status rows
- prose hints
- mixed cross-workspace scaffolding

## Wording contract

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
  secondary rows, or secondary surfaces.
- Workspace-owned contextual controls remain primary; read-only diagnostics do
  not.

## Probe / neighbor visible contract

- The Editor probe renders as a probe dot in `2D`, `3D`, and `4D`.
- The canonical visible probe glyph is one large circle in the active cell.
- The shared probe trace visual language is the connecting trace line itself.
  Intermediate path dots are intentionally removed.
- The Editor owns an optional `Probe Neighbors` overlay that renders canonical
  adjacent probe targets as smaller subordinate dots around the main probe.
- Toggling `Probe Neighbors` must not hide the main probe dot.
- Sandbox `Neighbors` stays separate and remains a Sandbox-owned control.
- Sandbox piece cells must continue to render as boxes.
- Sandbox neighbor markers and Editor probe-neighbor markers both render as
  dots, but with distinct visual roles.
- The same probe glyph language must be reused in `2D`, `3D`, and `4D`.
- The default `3D` / `4D` shell does not need the older per-panel movement-
  preview legends; the helper must expose full translation keys.

## Acceptance checklist

The frozen visible-shell pass is acceptable only when all of the following are
true:

- launcher root is exactly `Play`, `Continue`, `Tutorials`, `Topology
  Playground`, `Settings`, `Quit`
- `Topology Playground` is a direct modern entry
- legacy topology editor placement is only `Settings -> Advanced -> Legacy
  Topology Editor Menu`
- top bar contains only title, tabs, and one validity chip
- no default prose header is visible
- no default-primary diagnostics rows are visible
- left sidebar content is contextual to the active workspace
- center workspace is visually dominant
- right helper contains only keys plus at most one short context line
- bottom strip contains only chips/actions
- clipped or unreadable labels are absent at supported window sizes
- Editor probe renders as a large dot
- probe neighbors render as subordinate dots
- sandbox cells render as boxes
- sandbox neighbor markers render as dots only when enabled

## Deferred work

Explicitly deferred until after this visible-shell contract is stable:

- deeper `controls_panel.py` decomposition
- deeper `scene_state.py` decomposition
- runtime authority redesign
- Play semantic redesign
