# Topology Playground Current Authority

Status: active current-authority manifest  
Last updated: 2026-03-22

Use this file first for topology-playground architecture and migration-state
questions. Older topology-playground manifests, stage plans, and audits are
historical background unless a future task explicitly reactivates them.

## Instruction precedence

- This manifest and any newer user or developer instruction for the current
  task take precedence over archived topology-playground manifests.
- If an archived manifest conflicts with this file, follow this file.
- If a newer instruction severely conflicts with this file or with current code
  reality, stop and ask first before implementation.
- Once that mismatch is clarified, update this manifest and any affected
  archive-note stubs in the same batch so the repo stays coherent.

## Accepted architecture now

- Visible and canonical top-level workspaces are `Editor`, `Sandbox`, and
  `Play`.
- The current Explorer-shell pass is control-surface normalization and
  manifest/doc drift prevention, not a new semantic redesign.
- Direct explorer entry opens in `Sandbox` by default. This is the accepted
  startup contract unless a future task explicitly changes it.
- `Inspect` is no longer a top-level workspace. It survives only as an
  Editor-internal non-mutating probe/selection flow.
- `Edit` is no longer a top-level workspace. It survives only as an
  Editor-internal explicit mutation flow.
- Editor movement is always non-mutating, even when an edit-capable Editor tool
  is active.
- Probe movement, trace, and edit targeting must derive from the same canonical
  seam-aware Editor probe state.
- Sandbox is a separate piece-experimentation workspace. It does not implicitly
  mean neighbor-search.
- Play is a separate gameplay workspace. Translation legality and drop legality
  are distinct on non-trivial `Y`-seam topologies.
- Play move classes remain explicit: deliberate translation, rotation, gravity
  tick, soft drop, and hard drop must not collapse back into one generic
  seam-transport rule.
- Play groundedness and lock are based on whether one legal drop continuation
  exists under the Play drop policy, not on generic seam adjacency or generic
  transport reachability.
- Hard drop must match repeated legal drop continuation.

## Current Explorer stabilization expectations

- The legacy Inspect "dot" is the Editor probe/dot. Its movement must stay
  consistent before and after seam traversal.
- Internal cleanup should prefer `Editor` / `Probe` / workspace-owned naming in
  new shell helpers. Retained legacy inspect naming is limited to accepting the
  serialized/input token `inspect_boundary` at compatibility boundaries.
- The Editor probe/dot and its trace must work consistently in `2D`, `3D`, and
  `4D`.
- Probe movement, trace, and edit targeting must stay aligned to the same
  canonical seam-aware Editor probe state in every supported dimension.
- Editor trace visibility must be controlled by an explicit `Trace` contextual
  control owned by `Editor`, not by a floating or global Explorer exception.
  Toggling trace must not disable probe movement or hide the probe/dot itself.
- Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and
  `4D`.
- Switching from `Sandbox` to `Editor` must not discard or silently rebuild the
  current sandbox/topology situation. The same remembered topology state must
  remain available after the workspace switch.
- In `3D` and `4D`, projected sandbox piece cells must render as full piece
  boxes, not as neighbor-style dots.
- Neighbor markers must appear as small dots in `2D`, `3D`, and `4D` only when
  the Explorer `neighbor search` control is explicitly enabled. Neighbor
  markers must not appear by default, must not replace or hide the sandbox
  piece, and must remain visually distinct from sandbox piece cells. This
  current neighbor-marker behavior is canonical and replaces older sandbox
  neighbor assumptions.
- Sandbox neighbor-search visibility must be controlled by an explicit
  `Neighbors` contextual control owned by `Sandbox`, not by a floating or
  global Explorer exception.
- Menu items and critical controls must remain fully visible; clipped, hidden,
  or unreadable items are regressions.
- The helper panel must stay visible outside the main Explorer panel / viewport
  and remain minimal: translation keys, rotation keys, and at most one short
  current workspace/tool context line.
- Visible tool wording should prefer `Probe` for the non-mutating Editor probe
  flow; retaining visible `Inspect` copy is no longer the active direction.
- Explorer-facing behavior-changing controls must not be ad hoc. They belong to
  workspace selection, workspace tool selection, workspace-owned contextual
  controls, helper display options, or status-only display.

## Still transitional

- Safe internal legacy cleanup is now partially complete: workspace-shell
  copy/layout/helper routing is extracted to
  `src/tet4d/ui/pygame/topology_lab/workspace_shell.py`, and contextual
  controls-row ownership is extracted to
  `src/tet4d/ui/pygame/topology_lab/controls_panel_rows.py`. Shell-facing row
  values, playability/status formatting, and preview/context labels are now
  isolated in
  `src/tet4d/ui/pygame/topology_lab/controls_panel_values.py`, while
  probe-readiness and pane-state selectors now live in
  `src/tet4d/ui/pygame/topology_lab/scene_state.py`.
- Remaining legacy inspect compatibility is now boundary-only: runtime tool
  normalization still accepts the serialized/input token
  `inspect_boundary` and maps it onto the canonical internal `probe` tool id so
  older saved state/input callers continue to load.
- Some dimension-specific Editor probe/camera behavior still rides on older
  helper layers while the migrated shell consumes canonical runtime state.
- Retained shell projections in
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` are now limited to
  synchronized compatibility views for legacy readers, diagnostics, and
  transitional tests. Canonical runtime selectors are the only accepted
  explorer-path input authority.
- Legacy normal-mode rows and resolved-profile export are kept temporarily
  through the narrowly named transitional module
  `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py`; that seam
  is legacy-only and must not regain authority over the Explorer Playground
  flow.
- `src/tet4d/ui/pygame/launch/topology_lab_menu.py` is materially smaller after
  the shell-helper extraction, `src/tet4d/ui/pygame/topology_lab/workspace_shell.py`
  no longer depends on private helpers from
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py`, but
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` still carry follow-up
  decomposition and compatibility-alias debt.
- Helper/menu/readability cleanup is still active, but the remaining debt is
  shell/control normalization and readability rather than a semantic workspace
  redesign.
- Unsafe-topology cross-surface drift still exists in some paths, especially
  where sandbox behavior is stricter than gameplay or preview-invalid
  dimension-pairing behavior remains confusing.
- Some topology families still need focused Play drop-policy regression
  coverage beyond the currently pinned live-path cases.

## Superseded assumptions

- `Inspect` / `Edit` are not the primary visible top-level workspaces anymore.
- Sandbox is not implicitly neighbor mode and must not be documented or treated
  as such.
- Older Explorer-entry assumptions that the shell should open directly into
  `Editor` / `Edit` are superseded.
- Older Sandbox assumptions that workspace switching should restore a legacy
  editor-tool posture instead of preserving the current remembered situation
  are superseded.
- Generic explorer seam transport must not determine Play drop legality.
- Earlier Stage-1 continuation coverage did not fully fix the old spherical
  false-lock family; any wording that implies that is superseded.
- Older intermediate cleanup states, including the temporary four-mode
  `Edit` / `Inspect` / `Sandbox` / `Play` shell, are historical implementation
  steps rather than the current architecture.

## Current active priorities

- Finish workspace-first Explorer control normalization so no user-facing
  Explorer behavior still hangs off a shell exception.
- Continue focused Editor/Explorer stabilization where seam-aware probe/trace,
  helper/menu readability, or workspace isolation still regress.
- Continue removing legacy internal naming and compatibility mirrors only where
  that cleanup is grounded by tests and the current architecture contract.
- Continue deleting retained synchronized shell projections once the remaining
  legacy readers and diagnostics paths are migrated.
- Retire `legacy_normal_mode_support.py` only when the legacy Normal Game rows
  and resolved-profile export are actually deleted or deliberately rehomed.
- Continue reducing structural risk in
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` now that
  `src/tet4d/ui/pygame/launch/topology_lab_menu.py` is no longer the primary
  mixed-responsibility shell hotspot.
- Continue focused Play regression coverage for non-trivial `Y`-seam topology
  families and related launch/runtime invariants.
- Continue unsafe-topology contract cleanup where sandbox/gameplay/preview still
  disagree on valid transport behavior.
- Keep launcher/setup surfaces minimal for topology and keep custom-topology
  editing/play flowing through the Explorer Playground shell.

## Explicit non-goals for the next implementation phases

- Do not silently reopen the settled `Editor` / `Sandbox` / `Play` workspace
  split.
- Do not silently reopen the settled Play drop-policy distinction between
  deliberate translation and drop continuation unless a regression proves it
  wrong.
- Do not redesign Sandbox beyond focused visibility/framing, neighbor-toggle,
  or coupling fixes required by current regressions.
- Do not treat historical manifests as active execution authority.
- Do not silently leave the authority file stale after a task changes accepted
  topology-playground direction.

## Historical references

These files remain useful for background, but they are not the current
authority:

- `docs/history/topology_playground/tet4d_topology_playground_restructure_plan_codex.md`
- `docs/history/topology_playground/tet4d_spherical_false_lock_fix_manifest.md`
- `docs/history/topology_playground/topology_playground_migration.md`
- `docs/history/topology_playground/explorer_playground_unification.md`
- `docs/history/topology_playground/topology_playground_reality_audit.md`
- `docs/history/topology_playground/topology_playground_ownership_audit.md`
