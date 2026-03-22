# Topology Playground Current Authority

Status: active current-authority manifest  
Last updated: 2026-03-22

Use this file first for topology-playground architecture and migration-state
questions. Older topology-playground manifests, stage plans, audits, and
historical summaries are background only unless a future task explicitly
reactivates them.

## Instruction precedence

- This manifest and any newer user or developer instruction for the current
  task take precedence over archived topology-playground manifests.
- If an archived manifest conflicts with this file, follow this file.
- If a newer instruction severely conflicts with this file or with current code
  reality, stop and reconcile first.
- Once that mismatch is clarified, update this manifest and any affected
  archive-note stubs in the same batch so the repo stays coherent.

## Accepted architecture now

- Visible and canonical top-level workspaces are `Editor`, `Sandbox`, and
  `Play`.
- Direct explorer entry opens in `Sandbox` by default. This is the accepted
  startup contract unless a future task explicitly changes it.
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
- `Neighbors` is a Sandbox-owned contextual control.
- Explorer behavior-changing controls must not be ad hoc. They belong to
  workspace selection, workspace tool selection, workspace-owned contextual
  controls, helper display options, or status-only display.
- Sandbox is a separate piece-experimentation workspace. It does not
  implicitly mean neighbor-search.
- Play is a separate gameplay workspace. Translation legality and drop legality
  are distinct on non-trivial `Y`-seam topologies.
- Play move classes remain explicit: deliberate translation, rotation, gravity
  tick, soft drop, and hard drop must not collapse back into one generic
  seam-transport rule.
- Play groundedness and lock are based on whether one legal drop continuation
  exists under the Play drop policy, not on generic seam adjacency or generic
  transport reachability.
- Hard drop must match repeated legal drop continuation.
- Canonical runtime selectors are the only accepted explorer-path input
  authority.
- Retained shell fields, where still present, are synchronized compatibility
  projections only. They are not truth sources.

## Accepted invariants

### Editor / Probe invariants

- The legacy Inspect "dot" is the Editor probe/dot. Its movement must stay
  consistent before and after seam traversal.
- The Editor probe/dot and its trace must work consistently in `2D`, `3D`, and
  `4D`.
- Probe movement, trace, and edit targeting must stay aligned to the same
  canonical seam-aware Editor probe state in every supported dimension.
- Toggling `Trace` must not disable probe movement or hide the probe/dot
  itself.
- Visible tool wording should prefer `Probe` for the non-mutating Editor probe
  flow.

### Sandbox invariants

- Sandbox must show a sandbox piece by default on entry in `2D`, `3D`, and
  `4D`.
- Switching from `Sandbox` to `Editor` must not discard or silently rebuild the
  current sandbox/topology situation. The same remembered topology state must
  remain available after the workspace switch.
- In `3D` and `4D`, projected sandbox piece cells must render as full piece
  boxes, not as neighbor-style dots.
- Neighbor markers must appear as small dots in `2D`, `3D`, and `4D` only when
  the Explorer `neighbor search` control is explicitly enabled.
- Neighbor markers must not appear by default, must not replace or hide the
  sandbox piece, and must remain visually distinct from sandbox piece cells.

### Shell invariants

- Menu items and critical controls must remain fully visible; clipped, hidden,
  or unreadable items are regressions.
- The helper panel must stay visible outside the main Explorer panel / viewport
  and remain minimal: translation keys, rotation keys, and at most one short
  current workspace/tool context line.
- Helper content is not a second menu and must not become a shadow control
  surface.

## Current phase focus

The current topology-playground phase is no longer shell control-surface
normalization. The shell contract is already stabilized.

The current phase is:

- compatibility-seam retirement,
- shadow-state retirement,
- continued reduction of giant-module risk,
- and manifest/doc drift prevention under a stable Explorer shell.

This means future work should focus on:
- deleting retained synchronized shell projections once their readers are gone,
- narrowing or retiring transitional legacy seams,
- reducing compatibility mirrors and stale aliases,
- continuing structural cleanup in the remaining large topology-lab modules,
- while keeping runtime authority canonical and visible shell behavior stable.

## Still transitional

- Some dimension-specific Editor probe/camera behavior still rides on older
  helper layers while the migrated shell consumes canonical runtime state.
- Remaining synchronized shell projections in
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` are compatibility-only.
  They may still back explicit compatibility readers/tests, diagnostics, or
  retained shell consumers, but they must not regain explorer-path input
  authority. Boundary/seam selection, highlighted-glue mirrors, and the probe
  shell mirror trio (`probe_coord`, `probe_trace`, `probe_path`) are no longer
  canonical-to-shell sync outputs; canonical selectors own those seams now, and
  the probe trio survives only as fallback compatibility storage when canonical
  state is absent.
- The former transitional seam
  `src/tet4d/ui/pygame/topology_lab/legacy_normal_mode_support.py` is retired.
  Legacy Normal Game row adjustment now lives as a narrow private helper path
  inside `controls_panel.py`; it must not expand back into a generic legacy
  bucket or reclaim authority over Explorer flow, row layout, row value
  presentation, or export orchestration.
- `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and
  `src/tet4d/ui/pygame/topology_lab/scene_state.py` still carry follow-up
  decomposition and compatibility debt.
- Unsafe-topology cross-surface drift still exists in some paths, especially
  where sandbox behavior is stricter than gameplay or preview-invalid
  dimension-pairing behavior remains confusing.
- Some topology families still need focused Play drop-policy regression
  coverage beyond the currently pinned live-path cases.
- Historical docs may still mention removed legacy paths. Those references are
  documentation debt, not active authority.

## Superseded assumptions

- `Inspect` / `Edit` are not the primary visible top-level workspaces anymore.
- Sandbox is not implicitly neighbor mode and must not be documented or treated
  as such.
- Older Explorer-entry assumptions that the shell should open directly into
  `Editor` / `Edit` are superseded.
- Older Sandbox assumptions that workspace switching should restore a legacy
  editor-tool posture instead of preserving the current remembered situation are
  superseded.
- Generic explorer seam transport must not determine Play drop legality.
- Earlier Stage-1 continuation coverage did not fully fix the old spherical
  false-lock family; any wording that implies that is superseded.
- Older intermediate cleanup states, including the temporary four-mode
  `Edit` / `Inspect` / `Sandbox` / `Play` shell, are historical implementation
  steps rather than the current architecture.
- Retained shell fields are not active runtime truth, even when they are still
  synchronized for compatibility.

## Current active priorities

- Continue deleting retained synchronized shell projections once their live
  readers, compatibility tests, and diagnostics paths are migrated.
- Keep canonical runtime state as the only explorer-path input authority.
- Keep legacy Normal Game adjustment logic narrow inside `controls_panel.py`;
  do not let it become a new generic legacy bucket.
- Continue reducing structural risk in
  `src/tet4d/ui/pygame/topology_lab/controls_panel.py` and
  `src/tet4d/ui/pygame/topology_lab/scene_state.py`.
- Continue removing legacy compatibility mirrors and stale aliases only where
  cleanup is grounded by tests and the current architecture contract.
- Continue focused Play regression coverage for non-trivial `Y`-seam topology
  families and related launch/runtime invariants.
- Continue unsafe-topology contract cleanup where sandbox/gameplay/preview still
  disagree on valid transport behavior.
- Keep launcher/setup surfaces minimal for topology and keep custom-topology
  editing/play flowing through the Explorer Playground shell.
- Update manifests/docs in the same pass as code changes, prevent drift, and
  keep local CI-equivalent checks green.

## Explicit non-goals for the next implementation phases

- Do not silently reopen the settled `Editor` / `Sandbox` / `Play` workspace
  split.
- Do not silently reopen the settled Play drop-policy distinction between
  deliberate translation and drop continuation unless a regression proves it
  wrong.
- Do not redesign Sandbox beyond focused visibility/framing, neighbor-toggle,
  or coupling fixes required by current regressions.
- Do not treat historical manifests as active execution authority.
- Do not let retained shell projections or transitional legacy helpers drift
  back into truth ownership.
- Do not silently leave the authority file stale after a task changes accepted
  topology-playground direction.

## Mandatory execution rules for future passes

- Update documentation and manifests in the same pass as code changes.
- Prevent drift between code, tests, manifests, generated docs, and status
  files.
- Run the repo’s governance/drift/document checks required by the project.
- Run local CI-style verification before declaring completion.
- If a full local CI command cannot run, state exactly why and run the nearest
  equivalent checks.

## Historical references

These files remain useful for background, but they are not the current
authority:

- `docs/history/topology_playground/tet4d_topology_playground_restructure_plan_codex.md`
- `docs/history/topology_playground/tet4d_spherical_false_lock_fix_manifest.md`
- `docs/history/topology_playground/topology_playground_migration.md`
- `docs/history/topology_playground/explorer_playground_unification.md`
- `docs/history/topology_playground/topology_playground_reality_audit.md`
- `docs/history/topology_playground/topology_playground_ownership_audit.md`
