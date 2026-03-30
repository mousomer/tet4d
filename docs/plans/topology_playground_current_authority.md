# Topology Playground Current Authority

Role: authority
Status: active
Source of truth: this file
Supersedes: older topology-playground manifests and stage plans
Last updated: 2026-03-30

## Purpose

Use this file first for topology-playground architecture, precedence,
ownership, accepted invariants, current phase boundaries, and explicit
non-goals.

Older topology-playground manifests, stage plans, audits, and historical
summaries are background only unless a future task explicitly reactivates
them.

Visible-shell detail belongs in
`docs/plans/topology_playground_shell_redesign_spec.md`.

Transitional debt belongs in
`docs/plans/topology_playground_debt_register.md`.

## Instruction precedence

- This file and any newer user or developer instruction for the current task
  take precedence over archived topology-playground manifests.
- If an archived manifest conflicts with this file, follow this file.
- If a newer instruction severely conflicts with this file or with current code
  reality, stop and reconcile first.
- Once a mismatch is clarified, update this file and any affected lower-
  precedence docs in the same batch.

## Accepted architecture

- Visible and canonical top-level playground workspaces are `Editor`,
  `Sandbox`, and `Play`.
- `Topology Playground` is the modern current editing flow.
- Direct playground entry opens in `Sandbox` by default unless a future task
  explicitly changes that contract.
- The old menu-only topology setup/editor is legacy compatibility only.
- The legacy topology editor is not part of `Topology Playground`, `Explorer`,
  or `Path`.
- The legacy topology editor is reachable only through
  `Settings -> Advanced -> Legacy Topology Editor Menu`.
- `Inspect` is not a top-level workspace. It survives only as an
  Editor-internal non-mutating probe/selection flow.
- `Edit` is not a top-level workspace. It survives only as an Editor-internal
  explicit mutation flow.
- `Probe` is the canonical internal concept for the non-mutating Editor tool
  flow.
- Legacy `inspect_boundary` is accepted only at narrow compatibility
  boundaries, where it must normalize to canonical `probe`.
- Editor movement is always non-mutating, even when an edit-capable Editor tool
  is active.
- Probe movement, trace, and edit targeting must derive from the same canonical
  seam-aware Editor probe state.
- `Trace` is an Editor-owned contextual control.
- `Probe Neighbors` is a distinct Editor-owned overlay derived from canonical
  probe state.
- `Neighbors` is a Sandbox-owned contextual control.
- Sandbox is a separate piece-experimentation workspace. It does not implicitly
  mean neighbor-search.
- Play is a separate gameplay workspace. Translation legality and drop legality
  are distinct on non-trivial `Y`-seam topologies.
- Topology-playground-launched `Explore This Topology` uses the gameplay
  `menu` action as a direct return-to-playground transition rather than
  opening the generic independent gameplay pause menu.
- Play move classes remain explicit: deliberate translation, rotation, gravity
  tick, soft drop, and hard drop must not collapse back into one generic
  seam-transport rule.
- Play groundedness and lock are based on whether one legal drop continuation
  exists under the Play drop policy, not on generic seam adjacency or generic
  transport reachability.
- Hard drop must match repeated legal drop continuation.
- Canonical runtime selectors are the only accepted explorer-path input
  authority.
- `explorer_profile` and `explorer_draft` are canonical-runtime-owned on the
  migrated path. Any retained raw shell fields are fallback compatibility
  storage only when canonical state is absent.
- Retained shell fields, where still present, are synchronized compatibility
  projections or true shell-owned caches only. They are not truth sources.

## Accepted visible-shell invariants

- The accepted visible shell is the frozen shell defined in
  `docs/plans/topology_playground_shell_redesign_spec.md`.
- The shell keeps a compact top bar, contextual operational left sidebar,
  larger center workspace, readable minimal right helper, and compact bottom
  strip.
- The top bar contains only `Topology Playground`, `Editor` / `Sandbox` /
  `Play`, the validity chip `Valid` / `Needs Fix` / `Unsafe`, and the current
  dimension chip.
- The left sidebar inventory is the accepted per-workspace contract from the
  shell spec, including the shared `Dimension` / `Trace` /
  optional `Probe Neighbors` requirements and the explicit `Editor`,
  `Sandbox`, and `Play` row sets.
- Diagnostics remain secondary surfaces and do not replace the default
  workspace sidebar.
- The helper remains minimal in scope, not a second menu, and does not surface
  diagnostics.
- `Play Transport` and adjacent playability wording may temporarily show an
  analyzing/pending state while rigid transport analysis completes, without
  changing the accepted shell layout or chip contract.

## Accepted rendering invariants

### Editor / Probe

- The legacy Inspect dot is the Editor probe/dot.
- The Editor probe/dot and its trace must work consistently in `2D`, `3D`, and
  `4D`.
- Probe movement, trace, edit targeting, and probe-neighbor derivation must
  stay aligned to the same canonical seam-aware Editor probe state in every
  supported dimension.
- Toggling `Trace` must not disable probe movement or hide the probe/dot
  itself.
- The Editor probe must render as a large dot rather than as sandbox-style box
  geometry in `2D`, `3D`, and `4D`.
- The probe trace visual language is the connecting trace line itself.
  Intermediate path dots are intentionally removed.
- `Probe Neighbors`, when enabled, must render as smaller subordinate dots
  around the main probe and must not hide the probe/dot itself.
- Visible tool wording should prefer `Probe` for the non-mutating Editor probe
  flow.

### Sandbox

- Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and
  `4D`.
- Switching from `Sandbox` to `Editor` must not discard or silently rebuild the
  current sandbox/topology situation.
- In `3D` and `4D`, projected sandbox piece cells must render as full piece
  boxes, not as neighbor-style dots.
- Neighbor markers must appear as small dots only when the explicit sandbox
  neighbor control is enabled.
- Neighbor markers must not appear by default, must not replace or hide the
  sandbox piece, and must remain visually distinct from sandbox piece cells.
- Sandbox `Neighbors` and Editor `Probe Neighbors` are distinct overlays with
  distinct ownership and must stay documented and implemented separately.

### Shell-level readability

- Menu items and critical controls must remain fully visible; clipped, hidden,
  or unreadable items are regressions.
- The helper panel must stay visible outside the main explorer panel / viewport
  and remain readable enough to fully show movement and rotation keys plus at
  most one short workspace/tool context line.

## Current phase

The visible-shell redesign and panel-correction pass are landed.

The current topology-playground phase is shell-preserving implementation
simplification around the frozen visible shell.

This phase is intentionally limited to:

- structural simplification around the accepted shell
- compatibility cleanup that preserves the accepted shell
- doc/manifold/test drift prevention for the settled shell contract
- preserving canonical runtime-selector authority while trimming retained UI
  complexity
- deferring and caching expensive rigid playability analysis so first-frame
  readiness does not wait on the full rigid scan

Primary refactor targets in this phase:

- `src/tet4d/ui/pygame/topology_lab/controls_panel.py`
- `src/tet4d/ui/pygame/topology_lab/scene_state.py`

This phase must preserve the settled architecture rules above.
It must not reopen the accepted `Editor` / `Sandbox` / `Play` workspace model,
the accepted sandbox-first entry path, the current helper/diagnostics contract,
the canonical runtime-selector authority, the probe rendering contract, or the
settled Play drop-policy contract.

## Current active priorities

- Keep canonical runtime state as the only explorer-path input authority.
- Preserve the frozen visible shell while simplifying its implementation.
- Keep preview compile immediate, but defer and cache rigid playability
  analysis by effective preview signature so same-signature refreshes reuse the
  last full result.
- In future shell follow-up work, keep diagnostics explicitly secondary and do
  not let them drift back into default-primary sidebar content.
- Keep `Topology Playground` as a direct modern launcher entry with no
  modern-vs-legacy submenu split.
- Keep the legacy topology editor/menu out of `Topology Playground`,
  `Explorer`, and `Path`; expose it only through
  `Settings -> Advanced -> Legacy Topology Editor Menu`.
- Keep the direct playground entrypoint available via
  `python -m tet4d.ui.pygame.topology_lab` in addition to the launcher path.
- Update manifests/docs in the same pass as code changes, prevent drift, and
  keep local CI-equivalent checks green.

## Explicit non-goals

- Do not silently reopen the settled `Editor` / `Sandbox` / `Play` workspace
  split.
- Do not redesign the visible shell in this phase.
- Do not move the legacy topology editor back into the modern playground flow.
- Do not change the accepted probe rendering contract.
- Do not let retained shell projections or transitional legacy helpers drift
  back into truth ownership.
- Do not treat historical manifests as active execution authority.
- Do not silently leave this file stale after a task changes accepted
  topology-playground direction.

## Mandatory execution rules

- Update documentation and manifests in the same pass as code changes.
- Prevent drift between code, tests, manifests, generated docs, and status
  files.
- Run the repo’s governance/drift/document checks required by the project.
- Run local CI-style verification before declaring completion.
- If a full local CI command cannot run, state exactly why and run the nearest
  equivalent checks.

## Background pointer

Historical topology-playground plans, audits, and retired execution notes live
under `docs/history/topology_playground/`.
They are background only unless explicitly reactivated.
