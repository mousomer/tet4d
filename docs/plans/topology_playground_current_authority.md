# Topology Playground Current Authority

Role: authority
Status: active
Source of truth: this file
Supersedes: older topology-playground manifests and stage plans
Last updated: 2026-05-05

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
  `Settings -> Legacy Topology Editor Menu`.
- `Inspect` is not a top-level workspace. It survives only as an
  Editor-internal non-mutating probe/selection flow.
- `Edit` is not a top-level workspace. It survives only as an Editor-internal
  explicit mutation flow.
- `Probe` is the canonical internal concept for the non-mutating Editor tool
  flow.
- Legacy `inspect_boundary` is accepted only at narrow compatibility
  boundaries, where it must normalize to canonical `probe`.
- Editor owns topology construction, boundary gluing, preset selection,
  validation, validity status, and launch eligibility.
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
- Sandbox owns free probe/piece exploration, seam visibility, and movement
  diagnostics even when that exploratory movement is broader than Play
  legality.
- Play is a separate gameplay workspace. Translation legality and drop legality
  are distinct on non-trivial `Y`-seam topologies.
- Play launch must preserve the exact canonical explorer profile and transport
  semantics selected in the lab. No silent fallback, partial reconstruction,
  or default-topology substitution is allowed on the `Play This Topology` path.
- Wrap / invert / sphere-like selections are model-level transport presets.
  They are not visual-only presets, spawn presets, or renderer hints.
- Topology-playground-launched `Explore This Topology` uses the gameplay
  `menu` action as a direct return-to-playground transition rather than
  opening the generic independent gameplay pause menu.
- Play move classes remain explicit: deliberate translation, rotation, gravity
  tick, soft drop, and hard drop must not collapse back into one generic
  seam-transport rule.
- Play groundedness and lock are based on whether one legal drop continuation
  exists under the Play drop policy, not on generic seam adjacency or generic
  transport reachability.
- Sandbox/Explorer may traverse `Y` seams cellwise for exploration, but Play
  gravity, soft drop, and hard drop must not treat a `Y`-seam traversal as an
  ordinary drop continuation.
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
- If a projected `3D` / `4D` sandbox or play surface uses board-box gridlines
  or box edges, those lines must resolve against the active piece per projected
  fragment from screen-space overlap plus projected depth; `2D` keeps the
  simpler non-projected path.
- Neighbor markers must appear as small dots only when the explicit sandbox
  neighbor control is enabled.
- Neighbor markers must not appear by default, must not replace or hide the
  sandbox piece, and must remain visually distinct from sandbox piece cells.
- Sandbox `Neighbors` and Editor `Probe Neighbors` are distinct overlays with
  distinct ownership and must stay documented and implemented separately.
- The main launcher owns the true standalone `Explosion Simulator` surface.
- Sandbox may explicitly launch the standalone locked-cell explosion simulator
  from the current sandbox cell population. That explosion path is explorer-
  owned, must consume current canonical topology/profile inputs, must open the
  same dedicated simulator surface used by the launcher rather than an
  in-scene overlay, must not inherit gameplay-only legality or lock-state
  ownership, and must keep the simulator on the true board-native explosion
  view path rather than regressing explorer launches back to projection-only
  panes.

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

Accepted implementation direction in this phase:

- keep row inventory ownership in `controls_panel_rows.py`
- keep display/value derivation in `controls_panel_values.py`
- keep explorer row mutations and seam-edit actions in focused helper modules
  such as `controls_panel_actions.py`
- keep navigation/pane/shortcut/enter routing in focused helper modules such
  as `controls_panel_routing.py`
- keep save/export/experiment command execution in focused helper modules such
  as `controls_panel_commands.py`
- keep play-preview launch preparation and runtime handoff in focused helper
  modules such as `controls_panel_launch.py`
- keep `scene_state.py` focused on the state shape plus shell-owned
  pane/tool/workspace routing
- keep canonical runtime sync/write helpers in focused modules such as
  `scene_state_canonical.py`
- keep probe selectors, probe mutations, and probe-state synchronization in
  focused modules such as `scene_state_probe.py`
- keep `controls_panel.py` as the public shell facade for shell
  input/orchestration entrypoints and compatibility seams over those focused
  helpers
- keep deferred preview/playability work in `scene_preview_state.py`

This phase must preserve the settled architecture rules above.
It must not reopen the accepted `Editor` / `Sandbox` / `Play` workspace model,
the accepted sandbox-first entry path, the current helper/diagnostics contract,
the canonical runtime-selector authority, the probe rendering contract, or the
settled Play drop-policy contract.

The current migration boundary is now explicit:

- topology semantics are frozen and are migration-blocking authority
- Pygame shell polish is not migration-blocking
- Stage 2 topology/gameplay golden trace export exists under
  `tools/migration/` with checked-in traces in `migration/golden_traces/`
- those traces are the Python-authoritative migration oracle for topology
  transport, Sandbox/Play distinction, Y-axis drop policy, gameplay state, and
  `Play This Topology` launch parity
- Unity/Godot or other engine migration work must replay exported traces
  before implementing independent transport or drop/lock logic
- endgame trace export is intentionally deferred beyond Stage 2

## Current active priorities

- Keep canonical runtime state as the only explorer-path input authority.
- Preserve the frozen visible shell while simplifying its implementation.
- Keep preview compile immediate, but defer and cache rigid playability
  analysis by effective preview signature so same-signature refreshes reuse the
  last full result.
- The effective preview/playability signature is explorer topology plus the
  resolved board dims only. Probe state, sandbox state, helper state, pane
  selection, and non-topological launch settings must not invalidate cached
  preview/playability results.
- Same-signature refresh may restore cached playability results immediately
  when they are already available in memory or persistent cache; first-frame
  readiness must still avoid waiting on a new full rigid scan.
- Deferred rigid analysis should queue only for valid states whose rigid result
  is still unknown. Invalid preview states should surface their blocked state
  without scheduling a pointless deferred rigid recompute.
- Explicit play-preview launch should force completion only when the current
  valid signature still lacks a resolved rigid result; repeat launches on the
  same signature should reuse the completed cached result.
- Keep compatibility re-exports thin when launcher/tests still read helper
  seams through `controls_panel.py`; keep routing/command/launch detail in the
  focused helper modules, prefer updating callers to the stable owner module
  when that reduces indirection, and do not let that shell facade retake
  non-shell explorer mutation ownership.
- Keep `scene_state.py` as the public state facade, but do not let canonical
  sync/write logic, probe-state normalization, or boundary/glue selection
  helpers drift back into one mixed file when focused helper modules already
  own those concerns.
- In future shell follow-up work, keep diagnostics explicitly secondary and do
  not let them drift back into default-primary sidebar content.
- Keep `Topology Playground` as a direct modern launcher entry with no
  modern-vs-legacy submenu split.
- Keep the legacy topology editor/menu out of `Topology Playground`,
  `Explorer`, and `Path`; expose it only through
  `Settings -> Legacy Topology Editor Menu`.
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
