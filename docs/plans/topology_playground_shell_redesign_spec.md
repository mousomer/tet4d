# Topology Playground Visible Shell Redesign Spec

Role: spec
Status: frozen
Source of truth: this file for the accepted visible-shell contract
Supersedes: older shell-cleanup wording and playground shell notes
Last updated: 2026-03-29

## Purpose

Define the accepted modern Topology Playground shell contract.

This file is normative for visible shell layout, helper scope, diagnostics
placement, launcher routing related to the playground, and the probe/sandbox
rendering contract.

This file does not reopen runtime authority, Play semantics, or a second shell
redesign pass.

Architecture authority remains in
`docs/plans/topology_playground_current_authority.md`.

## Authority constraints

This spec must preserve:

- top-level playground workspaces: `Editor`, `Sandbox`, `Play`
- direct playground entry opening in `Sandbox`
- canonical runtime selectors as the only explorer-path input authority
- current Play drop-policy semantics
- the legacy topology editor as a legacy-only path outside `Topology
  Playground`, `Explorer`, and `Path`
- the frozen probe/sandbox render distinction

This spec must not be used to:

- redesign the visible shell again
- move the legacy topology editor back into the modern playground flow
- reopen runtime ownership of topology-playground state
- change probe rendering from the accepted dot-based contract

## Launcher routing contract

The launcher/menu IA authority lives in `docs/rds/RDS_MENU_STRUCTURE.md`.
This spec defines the required Topology Playground routing and shell placement
constraints that the menu IA must preserve.

### Modern routing

- `Topology Playground` is the direct launcher entry to the modern
  topology-editing shell.
- `Topology Playground` must not open a submenu that splits modern and legacy
  topology editing.
- The old menu-only topology editor is legacy compatibility only.
- The old menu-only topology editor is not part of `Topology Playground`,
  `Explorer`, or `Path`.
- The old menu-only topology editor is reachable only through
  `Settings -> Advanced -> Legacy Topology Editor Menu`.

### Adjacent launcher rules

- `Help / FAQ` must stay reachable from the learning/support surface rather
  than only through `Settings`.
- `Controls Reference` must remain distinct from `Settings -> Controls`.
- `Settings -> Controls` means persistent input configuration, not help or
  legend/reference content.
- `Leaderboard` and `Bot` must not return to the launcher root and must not
  live under `Settings`.

## Workspace model

- Visible and canonical top-level workspaces are `Editor`, `Sandbox`, and
  `Play`.
- Direct playground entry opens in `Sandbox` by default.
- `Probe` is the canonical Editor concept for the non-mutating tool flow.
- `Trace` is Editor-owned.
- `Probe Neighbors` is Editor-owned.
- `Neighbors` is Sandbox-owned.
- `Inspect` and `Edit` are not peer top-level workspaces.

## Visible shell contract

Default visible structure:

- compact top bar
- contextual operational left sidebar
- larger center workspace
- readable minimal helper on the right
- compact bottom strip

### Top bar

Must contain only:

- title: `Topology Playground`
- tabs: `Editor` / `Sandbox` / `Play`
- validity chip: `Valid` / `Needs Fix` / `Unsafe`
- current dimension chip

Must not contain:

- prose header copy
- default-primary diagnostic rows

### Left sidebar

All sidebar cases include:

- `Dimension`
- `Trace`
- optional `Probe Neighbors`
- edit actions only when directly relevant
- diagnostics collapsed or secondary

`Editor` sidebar:

- `Dimension`
- `Tool`
- `Trace`
- optional `Probe Neighbors`
- `Board X`
- `Board Y`
- `Board Z` (if dim = `3D` or `4D`)
- `Board W` (if dim = `4D`)
- `Topology Preset`
- edit actions only when directly relevant
- diagnostics collapsed or secondary

`Sandbox` sidebar:

- sandbox piece controls
- sandbox `Neighbors`
- sandbox `Piece Set`
- sandbox actions
- diagnostics collapsed or secondary

`Play` sidebar:

- `Speed`
- `Play Transport`
- play / launch controls
- play-specific setup/status
- diagnostics collapsed or secondary
- temporary `analyzing` wording for rigid transport is allowed so long as it
  stays within the existing `Play Transport` / play-status shell slots

### Center workspace

- The center workspace is the dominant visual region.
- `3D` and `4D` projection work surfaces should remain larger than in the
  older shell.
- Nonessential chrome that compresses the scene should remain removed.

### Right helper

The helper is minimal in scope, not arbitrarily minimal in width.

It must fully show:

- translation or movement keys
- rotation keys
- at most one short workspace/tool context line

It must not contain:

- diagnostics
- duplicate controls
- prose blocks
- shadow-menu behavior

### Bottom strip

Must contain only:

- compact status chips
- compact action buttons

Must not contain:

- long status rows
- prose hints
- mixed cross-workspace scaffolding

## Diagnostics contract

- Diagnostics are secondary surfaces only.
- Diagnostics do not replace the default workspace sidebar.
- Default left-sidebar content remains operational and contextual by
  workspace.
- Read-only diagnostics may live behind a diagnostics pane, secondary rows, or
  other secondary surfaces.

## Rendering contract

- probe = one large circle in `2D`, `3D`, and `4D`
- probe neighbors = dots
- sandbox cells = boxes

More specifically:

- The Editor probe renders as a large dot rather than sandbox-style box
  geometry.
- The shared probe trace visual language is the connecting trace line itself.
  Intermediate path dots are intentionally removed.
- `Probe Neighbors`, when enabled, render as smaller subordinate dots around
  the main probe.
- Toggling `Probe Neighbors` must not hide the main probe.
- Sandbox `Neighbors` stays separate and remains Sandbox-owned.
- Sandbox piece cells must continue to render as boxes in `2D`, `3D`, and
  `4D`.
- Sandbox neighbor markers render as dots only when the explicit Sandbox
  control is enabled.
- The same probe glyph language must be reused in `2D`, `3D`, and `4D`.

## Helper wording and visible wording contract

- Keep `Editor`, `Sandbox`, and `Play` as the visible workspace labels.
- Prefer visible `Probe` wording over legacy `Inspect` wording.
- Keep `Tool` as the short Editor tool label where the tool choice is directly
  relevant.
- Prefer `Diagnostics` over older analysis-heavy wording on secondary surfaces.
- The right helper should stay keys-first with at most one short context line.

## Acceptance checklist

The accepted shell contract is satisfied only when all of the following remain
true:

- launcher root is `Play`, `Continue`, `Tutorials`, `Topology Playground`,
  `Settings`, `Quit`
- `Topology Playground` is a direct modern entry
- legacy topology editor placement is only `Settings -> Advanced -> Legacy
  Topology Editor Menu`
- top bar contains only title, tabs, validity chip, and dimension chip
- no default prose header is visible
- no default-primary diagnostics rows are visible
- left sidebar matches the accepted per-workspace inventory
- center workspace is visually dominant
- right helper contains only movement/rotation keys plus at most one short
  context line
- helper fully shows those key groups rather than clipping them into
  unreadability
- helper is not a second menu
- diagnostics remain secondary surfaces
- bottom strip contains only chips/actions
- clipped or unreadable labels are absent at supported window sizes
- Editor probe renders as one large dot
- probe neighbors render as subordinate dots
- sandbox cells render as boxes
- sandbox neighbor markers render as dots only when enabled

## Next phase boundary

The visible-shell redesign and panel-correction work are landed.

The next phase is implementation simplification around the frozen shell,
without changing the accepted shell contract above.

Primary refactor targets:

- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`

## Explicitly deferred work

- deeper `controls_panel.py` simplification beyond shell-preserving cleanup
- deeper `scene_state.py` simplification beyond shell-preserving cleanup
- runtime authority redesign
- Play semantic redesign
- any new visible-shell redesign pass
